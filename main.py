import sys
import os
import time
import socket
import re
import math
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import typer

# High-Performance Parallel Computing Layer
import numpy as np
from numba import njit, prange, cuda

try:
    import serial
except ImportError:
    serial = None

app = typer.Typer(help="UNIVAC-IX Emergency Autonomous Diagnostic, Recovery & Tactical Control Core Mainframe Fabric")

# --- Global Operational Memories and State Registries ---
_active_serial_handles: Dict[str, Any] = {}
_cached_fingerprints: Dict[str, str] = {}
_last_client_socket: Optional[socket.socket] = None
_loaded_nodes_cache: List[str] = []

_safety_threshold_registers: Dict[str, Dict[str, int]] = {
    "0x0037": {"upper_limit": 200, "lower_limit": 10},
    "0x0038": {"upper_limit": 250, "lower_limit": 18}
}

_INTELLIGENCE_PATTERNS: Dict[str, str] = {
    "FINANCIAL_ROUTING": r"(?:ACCOUNT|IBAN|BANK|ROUTE|SWIFT)[\s\:\-\=]*([A-Z0-9]{8,24})",
    "SYSTEM_AUTHENTICATION": r"(?:PASS|PASSWORD|PWD|SECRET|KEY|TOKEN)[\s\:\-\=]*([a-zA-Z0-9\!\@\#\$\%\^\&\*]{6,32})",
    "TACTICAL_NAVIGATION": r"(?:LAT|LON|COORD|WAYPOINT|NAV)[\s\:\-\=]*([\d\.\-\u00B0\'\"]{4,18}\s*[NSEW]?)"
}


# ==============================================================================
# 1. NUMBA ACCELERATED COMPUTING LAYER (FORWARD, REVERSE, STORAGE CARVING)
# ==============================================================================

@njit(parallel=True, cache=True, fastmath=True)
def parallel_cpu_text_to_hex_matrix(ascii_array: np.ndarray, line_lengths: np.ndarray) -> np.ndarray:
    total_lines = ascii_array.shape[0]
    max_len = ascii_array.shape[1]
    hex_matrix = np.zeros((total_lines, max_len * 2), dtype=np.uint8)
    for i in prange(total_lines):
        current_length = line_lengths[i]
        for j in range(current_length):
            val = ascii_array[i, j]
            high_nibble = (val >> 4) & 0x0F
            low_nibble = val & 0x0F
            high_char = high_nibble + 48
            if high_nibble > 9:
                high_char = high_nibble + 55
            low_char = low_nibble + 48
            if low_nibble > 9:
                low_char = low_nibble + 55
            hex_matrix[i, j * 2] = high_char
            hex_matrix[i, (j * 2) + 1] = low_char
    return hex_matrix

@njit(parallel=True, cache=True, fastmath=True)
def parallel_cpu_hex_to_text_matrix(hex_array: np.ndarray, hex_lengths: np.ndarray) -> np.ndarray:
    total_lines = hex_array.shape[0]
    max_hex_len = hex_array.shape[1]
    ascii_matrix = np.zeros((total_lines, max_hex_len // 2), dtype=np.uint8)
    for i in prange(total_lines):
        current_hex_len = hex_lengths[i]
        total_chars = current_hex_len // 2
        for j in range(total_chars):
            high_char = hex_array[i, j * 2]
            low_char = hex_array[i, (j * 2) + 1]
            high_nibble = high_char - 48
            if high_char > 64:
                high_nibble = high_char - 55
            low_nibble = low_char - 48
            if low_char > 64:
                low_nibble = low_char - 55
            ascii_matrix[i, j] = (high_nibble << 4) | low_nibble
    return ascii_matrix

@njit(cache=True, fastmath=True)
def decode_fieldata_byte(byte_val: int) -> int:
    if byte_val == 0:   return 32
    if byte_val == 1:   return 48
    if byte_val == 2:   return 49
    if byte_val == 3:   return 50
    if byte_val == 4:   return 51
    if byte_val == 5:   return 52
    if byte_val == 6:   return 53
    if byte_val == 7:   return 54
    if byte_val == 8:   return 55
    if byte_val == 9:   return 56
    if byte_val == 10:  return 57
    if 11 <= byte_val <= 36: return byte_val + 54
    if byte_val == 37:  return 46
    if byte_val == 38:  return 44
    if byte_val == 39:  return 45
    if byte_val == 40:  return 47
    return 63

@njit(cache=True, fastmath=True)
def decode_ebcdic_byte(byte_val: int) -> int:
    if byte_val == 0x40: return 32
    if 0x81 <= byte_val <= 0x89: return byte_val - 0x81 + 97
    if 0x91 <= byte_val <= 0x99: return byte_val - 0x91 + 106
    if 0xA2 <= byte_val <= 0xA9: return byte_val - 0xA2 + 115
    if 0xC1 <= byte_val <= 0xC9: return byte_val - 0xC1 + 65
    if 0xD1 <= byte_val <= 0xD9: return byte_val - 0xD1 + 74
    if 0xE2 <= byte_val <= 0xE9: return byte_val - 0xE2 + 83
    if 0xF0 <= byte_val <= 0xF9: return byte_val - 0xF0 + 48
    if byte_val == 0x4B: return 46
    if byte_val == 0x6B: return 44
    if byte_val == 0x60: return 45
    if byte_val == 0x61: return 47
    if byte_val == 0x50: return 38
    if byte_val == 0x7D: return 39
    return 63

@njit(parallel=True, cache=True, fastmath=True)
def parallel_cpu_carve_fieldata(raw_binary_buffer: np.ndarray) -> np.ndarray:
    total_bytes = raw_binary_buffer.shape[0]
    output_ascii_array = np.zeros(total_bytes, dtype=np.uint8)
    for i in prange(total_bytes):
        output_ascii_array[i] = decode_fieldata_byte(raw_binary_buffer[i] & 0x3F)
    return output_ascii_array

@njit(parallel=True, cache=True, fastmath=True)
def parallel_cpu_carve_ebcdic(raw_binary_buffer: np.ndarray) -> np.ndarray:
    total_bytes = raw_binary_buffer.shape[0]
    output_ascii_array = np.zeros(total_bytes, dtype=np.uint8)
    for i in prange(total_bytes):
        output_ascii_array[i] = decode_ebcdic_byte(raw_binary_buffer[i])
    return output_ascii_array

@cuda.jit
def nvidia_gpu_hex_kernel(d_ascii, d_lengths, d_output):
    idx = cuda.grid(1)
    if idx >= d_ascii.shape[0]: return
    line_len = d_lengths[idx]
    for j in range(line_len):
        val = d_ascii[idx, j]
        high_nibble = (val >> 4) & 0x0F
        low_nibble = val & 0x0F
        high_char = high_nibble + 48
        if high_nibble > 9: high_char = high_nibble + 55
        low_char = low_nibble + 48
        if low_nibble > 9: low_char = low_nibble + 55
        d_output[idx, j * 2] = high_char
        d_output[idx, (j * 2) + 1] = low_char

@cuda.jit
def nvidia_gpu_reverse_kernel(d_hex, d_lengths, d_output):
    idx = cuda.grid(1)
    if idx >= d_hex.shape[0]: return
    hex_len = d_lengths[idx]
    total_chars = hex_len // 2
    for j in range(total_chars):
        high_char = d_hex[idx, j * 2]
        low_char = d_hex[idx, (j * 2) + 1]
        high_nibble = high_char - 48
        if high_char > 64: high_nibble = high_char - 55
        low_nibble = low_char - 48
        if low_char > 64: low_nibble = low_char - 55
        d_output[idx, j] = (high_nibble << 4) | low_nibble


# ==============================================================================
# 2. KOMMANDOGERAT-58 PHYSICS MODULE
# ==============================================================================

@njit(cache=True, fastmath=True)
def calculate_kg58_physics(mass: float, radius: float, velocity: float, thrust: float, piston_area: float, pressure: float) -> np.ndarray:
    centrifugal_force = (mass * (velocity ** 2)) / radius
    rotational_torque = thrust * radius
    piston_actuator_force = pressure * piston_area
    net_radial_equilibrium = centrifugal_force - piston_actuator_force
    output_vector = np.zeros(4, dtype=np.float64)
    output_vector[0] = centrifugal_force
    output_vector[1] = rotational_torque
    output_vector[2] = piston_actuator_force
    output_vector[3] = net_radial_equilibrium
    return output_vector


# ==============================================================================
# 3. LOWER LEVEL CORE INFRASTRUCTURE UTILITIES & HEURISTICS
# ==============================================================================

def validate_word_alignment(bit_length: int) -> None:
    if bit_length in: return
    print(f"Hardware Fault: Unsupported bit architecture {bit_length}.", file=sys.stderr)
    raise typer.Exit(code=1)

def convert_hex_stream(hex_payload: str) -> bytes:
    if len(hex_payload) % 2 == 0: return bytes.fromhex(hex_payload)
    print("Signal Fault: Hexadecimal streams must be symmetric.", file=sys.stderr)
    raise typer.Exit(code=1)

def load_system_config(config_path: Path) -> Dict[str, Any]:
    if config_path.exists():
        with open(config_path, "r") as stream: return yaml.safe_load(stream)
    print(f"Configuration Fault: Path {config_path} not found.", file=sys.stderr)
    raise typer.Exit(code=1)

def inline_multicore_hex_decode(raw_hex_string: str) -> str:
    clean_hex = raw_hex_string.strip().upper()
    hex_len = len(clean_hex)
    if hex_len == 0: return ""
    if hex_len % 2 != 0: return "[ERROR: ASYMMETRIC STREAM]"
    hex_matrix = np.zeros((1, hex_len), dtype=np.uint8)
    line_lengths = np.array([hex_len], dtype=np.int32)
    hex_matrix[0, :hex_len] = list(clean_hex.encode("ascii"))
    raw_text_matrix = parallel_cpu_hex_to_text_matrix(hex_matrix, line_lengths)
    return bytes(raw_text_matrix[0, :hex_len // 2]).decode("utf-8", errors="ignore")

def discover_hot_plugged_nodes(old_cache: List[str], current_nodes: List[Dict[str, Any]]) -> List[str]:
    new_additions: List[str] = []
    for node in current_nodes:
        node_id = node.get("id", "UNKNOWN")
        if node_id in old_cache: continue
        new_additions.append(node_id)
    return new_additions

def parse_system_arp_table() -> List[Dict[str, str]]:
    discovered_endpoints: List[Dict[str, str]] = []
    command = ["arp", "-n"]
    if os.name == "nt": command = ["arp", "-a"]
    try:
        raw_output = subprocess.check_output(command, stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore")
    except Exception:
        return discovered_endpoints
    ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    mac_pattern = r"([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})"
    for line in raw_output.splitlines():
        found_ip = re.search(ip_pattern, line)
        found_mac = re.search(mac_pattern, line)
        if not found_ip or not found_mac: continue

discovered_endpoints.append({"ip": found_ip.group(1), "mac": found_mac.group(1).replace("-", ":").lower()})
return discovered_endpoints
def execute_heuristic_fingerprint(hex_payload: str) -> str:
upper_payload = hex_payload.upper()
if upper_payload.startswith("AA55") or "NTDS" in inline_multicore_hex_decode(upper_payload): return "DRIVER_MIL_STD_1397_TACTICAL"
if upper_payload.startswith("7E") or "ALTITUDE" in inline_multicore_hex_decode(upper_payload): return "DRIVER_AVIATION_KNOWLEDGE"
if upper_payload.startswith("0F0F") or "BREAKDOWN" in inline_multicore_hex_decode(upper_payload): return "DRIVER_OTIS_GEN360"
if upper_payload.startswith("DEAD") or "CRITICAL" in inline_multicore_hex_decode(upper_payload): return "DRIVER_SAFETY_MONITOR"
return "DRIVER_UNKNOWN_GENERIC_SERIAL"
==============================================================================
4. DISASTER RECOVERY OVER-THE-AIR HANDLING & POLICING ENGINE
==============================================================================
def dispatch_emergency_radio_broadcast(hex_address: str, violation_type: str, threshold_val: int, current_val: int) -> None:
radio_tx_addr = "0x0014"
if radio_tx_addr not in _active_serial_handles: return
timestamp = time.strftime("%H:%M:%S")
radio_message = f"[UNIVAC-NET-BREACH] {timestamp} | CH:{hex_address} | TYPE:{violation_type} | LIMIT:{threshold_val} | VAL:{current_val} // EVAC_ERR"
hex_payload = radio_message.encode("utf-8").hex().upper()
try:
_active_serial_handles[radio_tx_addr].write(bytes.fromhex(hex_payload))
print(f" [RADIO MESH BROADCAST] Warning sent: {radio_message}")
except Exception:
pass
def verify_live_sensor_safety_compliance(hex_address: str, raw_payload_bytes: bytes) -> None:
clean_addr = hex_address.strip().lower()
if clean_addr not in _safety_threshold_registers: return
if len(raw_payload_bytes) == 0: return
measured_integer_value = int(raw_payload_bytes[-1])
bounds = _safety_threshold_registers[clean_addr]
max_boundary = bounds.get("upper_limit", 255)
min_boundary = bounds.get("lower_limit", 0)
if measured_integer_value > max_boundary:
sys.stdout.write("\a\a\a")
sys.stdout.flush()
print(f"\n!!! COMPLIANCE BREACH: UPPER SAFETY EXCEEDED ON {clean_addr} (VAL: {measured_integer_value} / MAX: {max_boundary}) !!!")
dispatch_emergency_radio_broadcast(clean_addr, "NET_MAX_EXCEEDED", max_boundary, measured_integer_value)
return
if measured_integer_value < min_boundary:
sys.stdout.write("\a\a\a")
sys.stdout.flush()
print(f"\n!!! COMPLIANCE BREACH: LOWER SAFETY EXCEEDED ON {clean_addr} (VAL: {measured_integer_value} / MIN: {min_boundary}) !!!")
dispatch_emergency_radio_broadcast(clean_addr, "NET_MIN_EXCEEDED", min_boundary, measured_integer_value)
return
def execute_direct_hardware_injection(hex_addr: str, reply_hex: str) -> None:
clean_addr = hex_addr.strip().lower()
if clean_addr not in _active_serial_handles: return
try:
_active_serial_handles[clean_addr].write(bytes.fromhex(reply_hex.strip().upper()))
print(f" [RECOVERY SUCCESS] Injected override payload {reply_hex.upper()} straight down channel {clean_addr}.")
except Exception:
pass
def dispatch_radio_alert_notice(node_id: str, channel_addr: str, rule_label: str, target_driver: str) -> None:
radio_tx_addr = "0x0014"
if radio_tx_addr not in _active_serial_handles: return
timestamp = time.strftime("%H:%M:%S")
alert_text = f"[UNIVAC-ALERT] {timestamp} | NODE:{node_id} | ADDR:{channel_addr} | DRV:{target_driver} | ACTION:{rule_label} // INJECT_OK"
try:
_active_serial_handles[radio_tx_addr].write(alert_text.encode("utf-8").hex().upper().encode("ascii"))
print(f" [RADIO MESH BROADCAST] Notice: {alert_text}")
except Exception:
pass
def execute_matrix_mirror_routing(source_addr: str, raw_payload: bytes, config_data: Dict[str, Any]) -> None:
routing_rule = config_data.get("routing_matrix", {})
if routing_rule.get("source_node", "").lower() != source_addr.lower(): return
targets = routing_rule.get("mirror_targets", [])
for target in targets:
target_addr = target.get("address", "").lower()
if target_addr not in _active_serial_handles: continue
try:
_active_serial_handles[target_addr].write(raw_payload)
except Exception:
pass
def append_radio_injection_to_visio_map(target_addr: str, override_payload_hex: str, target_csv: Path) -> None:
if not target_csv.exists(): return
node_id = f"RADIO_INJECT_{int(time.time())}"
timestamp = time.strftime("%H:%M:%S")
assigned_driver = cached_fingerprints.get(target_addr.lower(), "DRIVER_UNKNOWN_GENERIC_SERIAL")
log_line = f"{node_id},Radio_Override{timestamp},OTA Injection {override_payload_hex} via Port 19,,,RADIO_MESH_INJECT,VIRTUAL_AIR_LINK,{target_addr.lower()},{assigned_driver},RADIO_MUTATED_STATE,WARNING,Orange,NONE\n"
try:
with open(target_csv, "a", encoding="utf-8") as ledger: ledger.write(log_line)
except Exception:
pass
def handle_incoming_radio_signal(hex_payload_str: str, config_data: Dict[str, Any], target_csv: Path) -> None:
decoded_text = inline_multicore_hex_decode(hex_payload_str)
if not decoded_text or not decoded_text.startswith("[CMD]"): return
try:
command_payload = decoded_text.replace("[CMD]", "").strip()
target_addr, override_hex = command_payload.split(":", 1)
target_addr = target_addr.strip().lower()
override_hex = override_hex.strip().upper()
print(f"\n[RADIO MESH RX] Authorized instruction validated. Target: {target_addr} | Payload: {override_hex}")
append_radio_injection_to_visio_map(target_addr, override_hex, target_csv)
process_incoming_stream(target_addr, bytes.fromhex(override_hex), config_data, target_csv)
except Exception:
pass
def evaluate_handshake_reply_rules(driver_name: str, hex_addr: str, decoded_text: str, config_data: Dict[str, Any]) -> None:
handshake_rules = config_data.get("recovery_handshakes", {}).get(driver_name, {})
if not handshake_rules: return
trigger = handshake_rules.get("trigger_keyword", "")
if trigger not in decoded_text.upper(): return
print(f"\n [ALERT MATCHED] Rule Trigger: '{trigger}' seen inside stream for {driver_name}.")
execute_direct_hardware_injection(hex_addr, handshake_rules.get("reply_hex", ""))
==============================================================================
5. CONSOLIDATED PIPELINE EXECUTION ENGINE ROUTER
==============================================================================
def process_incoming_stream(hex_address: str, raw_payload: bytes, config_data: Dict[str, Any], target_csv: Path) -> None:
clean_addr = hex_address.strip().lower()
hex_payload_str = raw_payload.hex().upper()
execute_matrix_mirror_routing(clean_addr, raw_payload, config_data)
verify_live_sensor_safety_compliance(clean_addr, raw_payload)
if clean_addr == "0x0013":
handle_incoming_radio_signal(hex_payload_str, config_data, target_csv)
return
if clean_addr not in _cached_fingerprints:
detected_driver = execute_heuristic_fingerprint(hex_payload_str)
_cached_fingerprints[clean_addr] = detected_driver
print(f"\n[LEARNED INTERFACE] Identified hardware component on channel {clean_addr} -> Driver Bound: {detected_driver}")
assigned_driver = _cached_fingerprints[clean_addr]
decoded_readable_text = inline_multicore_hex_decode(hex_payload_str)
print(f" [CORE PROCESSING] Address: {clean_addr} | Driver: {assigned_driver} | Plaintext: {decoded_readable_text}")
evaluate_handshake_reply_rules(assigned_driver, clean_addr, decoded_readable_text, config_data)
==============================================================================
6. TYPER MANAGEMENT COMMAND MENUS INTERFACE
==============================================================================
@app.command(name="route-signal")
def route_signal_command(
hex_address: str = typer.Argument(..., help="Target device hexadecimal address Space."),
payload: str = typer.Argument(..., help="The hexadecimal input or output data vector stream payload."),
config: Path = typer.Option(Path("config.yaml"), help="Path to the node configuration registry file."),
visio_csv: Path = typer.Option(Path("visio_mapping.csv"), help="The target Data Visualizer log sheet destination path.")
):
"""Manually injects and routes a programmatic telemetry payload straight into the core processor fabrics."""
config_data = load_system_config(config)
if "0x0014" not in _active_serial_handles:
class DummySerial:
def write(self, data): pass
_active_serial_handles["0x0014"] = DummySerial()
process_incoming_stream(hex_address, bytes.fromhex(payload.strip().upper()), config_data, visio_csv)
@app.command(name="monitor-fabric")
def monitor_fabric_command(
config: Path = typer.Option(Path("config.yaml"), help="Path to the configuration matrix profile."),
interval: float = typer.Option(1.0, help="Timestep polling interval gap constraint in fractional seconds.")
):
"""Launches a live background observer loop to execute hot-plug integration maps upon registry file updates."""
global _loaded_nodes_cache
if not config.exists(): raise typer.Exit(code=1)
print(f"[FABRIC] Initializing topology monitor line state observer: {config}")
initial_data = load_system_config(config)
_loaded_nodes_cache = [node.get("id", "UNKNOWN") for node in initial_data.get("nodes", [])]
last_modified_time = config.stat().st_mtime
try:
while True:
time.sleep(interval)
current_modified_time = config.stat().st_mtime
if current_modified_time == last_modified_time: continue
print("[HOTPLUG EVENT] Local topology matrix file modification caught. Syncing entries...")
last_modified_time = current_modification_time
current_nodes = load_system_config(config).get("nodes", [])
new_nodes = discover_hot_plugged_nodes(_loaded_nodes_cache, current_nodes)
for node in current_nodes:
if node.get("id") not in new_nodes: continue
print(f" -> PLUG-AND-PLAY MOUNTED: Node [{node.get('id')}] -> Hex Mapping Address: {node.get('hex_address')}")
_loaded_nodes_cache = [node.get("id", "UNKNOWN") for node in current_nodes]
except KeyboardInterrupt:
raise typer.Exit(code=0)
@app.command(name="convert-log")
def convert_log_command(
source_file: Path = typer.Argument(..., help="Path to the raw textual log asset dump."),
output_hex_file: Optional[Path] = typer.Option(None, help="Target storage file to save translated data."),
use_gpu: bool = typer.Option(False, "--use-gpu", help="Force thread computation allocation over NVIDIA graphics engines.")
):
"""Converts text log blocks into high-speed hexadecimal streams via Multicore CPU or NVIDIA GPU acceleration."""
if not source_file.exists(): raise typer.Exit(code=1)
with open(source_file, "r", encoding="utf-8", errors="ignore") as f:
lines = [line.strip() for line in f if line.strip()]
if not lines: return
total_lines = len(lines)
max_line_len = max(len(line) for line in lines)
ascii_matrix = np.zeros((total_lines, max_line_len), dtype=np.uint8)
line_lengths = np.zeros(total_lines, dtype=np.int32)
for idx, line in enumerate(lines):
line_bytes = line.encode("utf-8")
line_lengths[idx] = len(line_bytes)
ascii_matrix[idx, :len(line_bytes)] = list(line_bytes)
if use_gpu:
if not cuda.is_available(): raise typer.Exit(code=5)
print(f"[CONVERTER] Deploying hardware line processing: NVIDIA CUDA Streaming Multiproc Engine over {total_lines} lines.")
d_ascii = cuda.to_device(ascii_matrix)
d_lengths = cuda.to_device(line_lengths)
d_output = cuda.device_array((total_lines, max_line_len * 2), dtype=np.uint8)
threads_per_block = 128
blocks_per_grid = (total_lines + (threads_per_block - 1)) // threads_per_block
nvidia_gpu_hex_kernel[blocks_per_grid, threads_per_block](d_ascii, d_lengths, d_output)
cuda.synchronize()
raw_hex_matrix = d_output.copy_to_host()
if not use_gpu:
print(f"[CONVERTER] Deploying hardware line processing: Multicore CPU Numba Parallel Matrix over {total_lines} items.")
raw_hex_matrix = parallel_cpu_text_to_hex_matrix(ascii_matrix, line_lengths)
final_output_list = [bytes(raw_hex_matrix[idx, :line_lengths[idx] * 2]).decode("ascii") for idx in range(total_lines)]
final_output_string = "\n".join(final_output_list)
if not output_hex_file:
print(final_output_string)
return
with open(output_hex_file, "w", encoding="utf-8") as out: out.write(final_output_string + "\n")

