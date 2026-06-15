import sys
import os
import time
import socket
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import typer

import numpy as np
from numba import njit, prange

try:
    import serial
except ImportError:
    serial = None

app = typer.Typer(help="UNIVAC-IX Emergency Bidirectional Control & Handshake Core Fabric")

_active_serial_handles: Dict[str, Any] = {}
_cached_fingerprints: Dict[str, str] = {}
_last_client_socket: Optional[socket.socket] = None # Hold last fiber client for reverse network response injection

# --- Numba High-Performance Accelerated Computing Core ---

@njit(parallel=True, cache=True, fastmath=True)
def parallel_cpu_hex_to_text_matrix(hex_array: np.ndarray, hex_lengths: np.ndarray) -> np.ndarray:
    total_lines = hex_array.shape
    max_hex_len = hex_array.shape
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

def inline_multicore_hex_decode(raw_hex_string: str) -> str:
    clean_hex = raw_hex_string.strip().upper()
    hex_len = len(clean_hex)
    if hex_len == 0:
        return ""
    if hex_len % 2 != 0:
        return "[ERROR: ASYMMETRIC STREAM]"

    hex_matrix = np.zeros((1, hex_len), dtype=np.uint8)
    line_lengths = np.array([hex_len], dtype=np.int32)
    hex_matrix[0, :hex_len] = list(clean_hex.encode("ascii"))
    
    raw_text_matrix = parallel_cpu_hex_to_text_matrix(hex_matrix, line_lengths)
    return bytes(raw_text_matrix[0, :hex_len // 2]).decode("utf-8", errors="ignore")


# --- Automated Handshake Reply Dispatcher Engine ---

def execute_hardware_reverse_injection(hex_addr: str, reply_hex: str) -> None:
    """Dispatches corrective recovery strings straight back into physical serial links or fiber networks."""
    raw_reply_bytes = bytes.fromhex(reply_hex.strip().upper())
    
    # 1. Check if destination target is an active hardware serial port interface channel
    if hex_addr in _active_serial_handles:
        try:
            _active_serial_handles[hex_addr].write(raw_reply_bytes)
            print(f"  [RECOVERY INJECTED -> SERIAL] Dispatched payload {reply_hex} back into channel {hex_addr}.")
            return
        except Exception as e:
            print(f"  [RECOVERY FAULT] Failed to write back to serial port {hex_addr}: {e}", file=sys.stderr)
            return

    # 2. Check if destination target passed through the High-Speed Fiber Pipe interface
    if _last_client_socket:
        try:
            # Format return frame as ADDR:PAYLOAD_HEX for clear bidirectional protocol loops
            network_return_frame = f"{hex_addr}:{reply_hex}\n".encode('utf-8')
            _last_client_socket.sendall(network_return_frame)
            print(f"  [RECOVERY INJECTED -> FIBER] Echoed return instruction network payload frame back down core trunk pipeline.")
            return
        except Exception as net_err:
            print(f"  [RECOVERY FAULT] Fiber line return injection dropped: {net_err}", file=sys.stderr)
            return

    print(f"  [RECOVERY WARNING] Handshake aborted. Interface medium destination pathway '{hex_addr}' is unmounted.", file=sys.stderr)

def evaluate_handshake_reply_rules(driver_name: str, hex_addr: str, decoded_text: str, config_data: Dict[str, Any]) -> None:
    """Scans the config matrix layout to catch faults and execute immediate corrective handshakes."""
    handshake_rules = config_data.get("recovery_handshakes", {}).get(driver_name, {})
    if not handshake_rules:
        return # No automated counter-measure rules configured for this driver type
        
    trigger = handshake_rules.get("trigger_keyword", "")
    if trigger not in decoded_text.upper():
        return # Data stream did not reach structural warning parameters
        
    print(f"\n  [ALERT MATCHED] Rule Trigger: '{trigger}' located inside payload stream for {driver_name}.")
    print(f"  [POLICING ENGINE] Deploying automated emergency counter-measure: {handshake_rules.get('label')}")
    
    execute_hardware_reverse_injection(hex_addr, handshake_rules.get("reply_hex", ""))


# --- Driver Routing Hierarchy Matrix ---

def execute_heuristic_fingerprint(hex_payload: str) -> str:
    upper_payload = hex_payload.upper()
    if upper_payload.startswith("AA55") or "NTDS" in inline_multicore_hex_decode(upper_payload):
        return "DRIVER_MIL_STD_1397_TACTICAL"
    if upper_payload.startswith("7E") or "ALTITUDE" in inline_multicore_hex_decode(upper_payload):
        return "DRIVER_AVIATION_KNOWLEDGE"
    if upper_payload.startswith("0F0F") or "BREAKDOWN" in inline_multicore_hex_decode(upper_payload):
        return "DRIVER_OTIS_GEN360"
    if upper_payload.startswith("DEAD") or "CRITICAL" in inline_multicore_hex_decode(upper_payload):
        return "DRIVER_SAFETY_MONITOR"
    return "DRIVER_UNKNOWN_GENERIC_SERIAL"

def load_system_config(config_path: Path) -> Dict[str, Any]:
    if config_path.exists():
        with open(config_path, "r") as stream:
            return yaml.safe_load(stream)
    print(f"Configuration Fault: Path {config_path} not found.", file=sys.stderr)
    raise typer.Exit(code=1)

def execute_matrix_mirror_routing(source_addr: str, raw_payload: bytes, config_data: Dict[str, Any]) -> None:
    routing_rule = config_data.get("routing_matrix", {})
    if routing_rule.get("source_node", "").lower() != source_addr.lower():
        return
    targets = routing_rule.get("mirror_targets", [])
    for target in targets:
        target_addr = target.get("address", "").lower()
        if target_addr not in _active_serial_handles:
            continue
        try:
            _active_serial_handles[target_addr].write(raw_payload)
        except Exception:
            pass

def route_to_active_driver(driver_name: str, hex_addr: str, decoded_text: str, hex_str: str, config_data: Dict[str, Any]) -> None:
    match driver_name:
        case "DRIVER_MIL_STD_1397_TACTICAL":
            print(f"  [DRIVER] Tactical Aegis Core Frame active on channel {hex_addr} | Msg: {decoded_text}")
            evaluate_handshake_reply_rules(driver_name, hex_addr, decoded_text, config_data)
            return
        case "DRIVER_AVIATION_KNOWLEDGE":
            print(f"  [DRIVER] Aviation Telemetry Node active on channel {hex_addr} | Msg: {decoded_text}")
            evaluate_handshake_reply_rules(driver_name, hex_addr, decoded_text, config_data)
            return
        case "DRIVER_OTIS_GEN360":
            print(f"  [DRIVER] Otis Mechanical Interface Link tracking line {hex_addr} | Msg: {decoded_text}")
            evaluate_handshake_reply_rules(driver_name, hex_addr, decoded_text, config_data)
            return
        case "DRIVER_SAFETY_MONITOR":
            print(f"  [CRITICAL PRIORITY TRAP] Facility sensory threat verified on channel {hex_addr}! | Msg: {decoded_text}")
            evaluate_handshake_reply_rules(driver_name, hex_addr, decoded_text, config_data)
            return
        case _:
            print(f"  [DRIVER] Custom physical profile active on channel {hex_addr} | Raw: {hex_str}")
            return

def process_incoming_stream(hex_address: str, raw_payload: bytes, config_data: Dict[str, Any]) -> None:
    clean_addr = hex_address.strip().lower()
    hex_payload_str = raw_payload.hex().upper()
    
    execute_matrix_mirror_routing(clean_addr, raw_payload, config_data)
    decoded_readable_text = inline_multicore_hex_decode(hex_payload_str)
    
    if clean_addr not in _cached_fingerprints:
        detected_driver = execute_heuristic_fingerprint(hex_payload_str)
        _cached_fingerprints[clean_addr] = detected_driver
        print(f"\n[LEARNED INTERFACE] Identified hardware element on port address {clean_addr} -> Assigned: {detected_driver}")

    assigned_driver = _cached_fingerprints[clean_addr]
    route_to_active_driver(assigned_driver, clean_addr, decoded_readable_text, hex_payload_str, config_data)


# --- Daemon Engine Startup Commands Menu ---

@app.command(name="listen-ports")
def listen_ports_command(
    config: Path = typer.Option(Path("config.yaml"), help="Path to the system topology file."),
    network_port: int = typer.Option(8080, help="Network port tracking aggregate fiber optic lines.")
):
    """Launches the core listening loop equipped with automatic bidirectional hardware recovery injectors."""
    global _active_serial_handles, _last_client_socket
    config_data = load_system_config(config)
    print(f"\n======================================================================")
    print(f"BIDIRECTIONAL TACOPS FABRIC RUNNING: {config_data.get('system', {}).get('identity', 'UNIVAC-CORE')}")
    print(f"======================================================================")
    inline_multicore_hex_decode("414243") # Warm up cache arrays
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", network_port))
    server_socket.listen(10)
    server_socket.setblocking(False)
    
    for node in config_data.get("nodes", []):
        port_path = node.get("port", "")
        if not port_path.startswith("/dev/"):
            continue
        if not serial:
            continue
        try:
            ser = serial.Serial(port_path, baudrate=115200, timeout=0.01)
_active_serial_handles[node.get("hex_address").lower()] = ser
except Exception:
pass
print(f"[LIVE MONITOR] Listening... Fault detection systems online and handshakes loaded.\n")
try:
while True:
# Poll fiber socket interface parameters
try:
client_sock, _ = server_socket.accept()
client_sock.settimeout(0.2)
_last_client_socket = client_sock # Dynamic bind for network-driven reverse response paths
raw_buffer = client_sock.recv(4096)
if raw_buffer:
payload_str = raw_buffer.decode('utf-8').strip()
if ":" in payload_str:
addr, data_hex = payload_str.split(":", 1)
process_incoming_stream(addr, bytes.fromhex(data_hex.strip()), config_data)
client_sock.close()
_last_client_socket = None
except BlockingIOError:
pass
except Exception:
pass
# Scan physical serial adapter lanes
for hex_addr, serial_conn in list(_active_serial_handles.items()):
if not serial_conn.in_waiting:
continue
raw_bytes = serial_conn.read(serial_conn.in_waiting)
if raw_bytes:
process_incoming_stream(hex_addr, raw_bytes, config_data)
time.sleep(0.005)
except KeyboardInterrupt:
print("\n[SHUTDOWN] Exiting tactical diagnostic framework safely.")
server_socket.close()
raise typer.Exit(code=0)
if name == "main":
app()
