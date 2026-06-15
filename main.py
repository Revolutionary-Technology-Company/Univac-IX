import sys
import os
import time
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

app = typer.Typer(help="UNIVAC-IX Tactical Dual-Way Radio Mesh & Live Visio Auditing Fabric")

_active_serial_handles: Dict[str, Any] = {}

_cached_fingerprints: Dict[str, str] = {
    "0x0011": "DRIVER_MIL_STD_1397_TACTICAL",
    "0x0012": "DRIVER_MIL_STD_1397_TACTICAL",
    "0x0013": "DRIVER_AVIATION_KNOWLEDGE",
    "0x0014": "DRIVER_AVIATION_KNOWLEDGE",
    "0x0022": "DRIVER_OTIS_GEN360",
    "0x0037": "DRIVER_SAFETY_MONITOR"
}

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


# --- Automated Live Visio Auditing Script Component ---

def append_radio_injection_to_visio_map(target_addr: str, override_payload_hex: str, target_csv: Path) -> None:
    """Appends live over-the-air modifications straight into the Visio diagram ledger file."""
    if not target_csv.exists():
        print(f"  [VISIO LOG FAULT] Target ledger template missing at path '{target_csv}'. Run export-visio command first.", file=sys.stderr)
        return
        
    # Generate discrete timestamped event ID constraints
    epoch_stamp = int(time.time())
    node_id = f"RADIO_INJECT_{epoch_stamp}"
    timestamp = time.strftime("%H:%M:%S")
    
    assigned_driver = _cached_fingerprints.get(target_addr.lower(), "DRIVER_UNKNOWN_GENERIC_SERIAL")
    node_name = f"Radio_Override_{timestamp}"
    node_desc = f"OTA Injection payload {override_payload_hex} intercepted via Port 19"
    
    # Structure layout elements tailored precisely for Microsoft Visio Data Visualizer tools
    log_line = f"{node_id},{node_name},{node_desc},,,RADIO_MESH_INJECT,VIRTUAL_AIR_LINK,{target_addr.lower()},{assigned_driver},RADIO_MUTATED_STATE,WARNING,Orange\n"
    
    try:
        with open(target_csv, "a", encoding="utf-8") as ledger:
            ledger.write(log_line)
        print(f"  -> [VISIO LEDGER UPDATE] Appended tracking node {node_id} directly to target database sheet file.")
    except Exception as io_err:
        print(f"  [VISIO LOG FAULT] Could not write to system mapping sheets: {io_err}", file=sys.stderr)


# --- Automated Radio Message Processing & Injection Engine ---

def handle_incoming_radio_signal(hex_payload_str: str, config_data: Dict[str, Any], target_csv: Path) -> None:
    """Decodes incoming over-the-air packet blocks on Port 19 and maps execution states straight to Visio charts."""
    decoded_text = inline_multicore_hex_decode(hex_payload_str)
    if not decoded_text:
        return
        
    print(f"\n[RADIO MESH RX] Incoming signal captured on channel 0x0013 (RADIO_TRANS_RX).")
    print(f"  -> Plaintext Extracted:  {decoded_text}")
    
    if not decoded_text.startswith("[CMD]"):
        print("  -> [REJECTED] Payload missing authorized tactical command token format structure.", file=sys.stderr)
        return
        
    try:
        command_payload = decoded_text.replace("[CMD]", "").strip()
        target_addr, override_hex = command_payload.split(":", 1)
        target_addr = target_addr.strip().lower()
        override_hex = override_hex.strip().upper()
        
        print(f"  -> [AUTHORIZED INTERRUPT VALIDATED] Executing radio instruction update loops...")
        
        # 1. Fire the real-time visual mapping script engine append function before routing state payloads
        append_radio_injection_to_visio_map(target_addr, override_hex, target_csv)
        
        # 2. Programmatically execute the inner core hardware engine command loop paths
        raw_bytes = bytes.fromhex(override_hex)
        process_incoming_stream(target_addr, raw_bytes, config_data, target_csv)
    except Exception as parse_err:
        print(f"  -> [MALFORMED INTERRUPT] Failed to parse internal radio override string parameters: {parse_err}", file=sys.stderr)

def process_incoming_stream(hex_address: str, raw_payload: bytes, config_data: Dict[str, Any], target_csv: Path) -> None:
    clean_addr = hex_address.strip().lower()
    hex_payload_str = raw_payload.hex().upper()
    
    if clean_addr == "0x0013":
        handle_incoming_radio_signal(hex_payload_str, config_data, target_csv)
        return

    decoded_readable_text = inline_multicore_hex_decode(hex_payload_str)
    print(f"  [CORE FABRIC EXECUTE] Address: {clean_addr} -> Dispatched to target module driver pipeline: {decoded_readable_text}")


# --- Daemon Engine Startup Commands ---

def load_system_config(config_path: Path) -> Dict[str, Any]:
    if config_path.exists():
        with open(config_path, "r") as stream:
            return yaml.safe_load(stream)
    print(f"Configuration Fault: Path {config_path} not found.", file=sys.stderr)
    raise typer.Exit(code=1)

@app.command(name="listen-ports")
def listen_ports_command(
    config: Path = typer.Option(Path("config.yaml"), help="Path to the system topology file."),
    visio_csv: Path = typer.Option(Path("visio_mapping.csv"), help="The target data visualizer spreadsheet to write audits to."),
    network_port: int = typer.Option(8080, help="Network port simulating aggregate fiber optic lines.")
):
    """Launches the master multi-channel communication server matrix with dynamic visual ledger logging hooks."""
    global _active_serial_handles
    config_data = load_system_config(config)
    print(f"\n======================================================================")
    print(f"VISIO AUDITING RADIO DAEMON LIVE: {config_data.get('system', {}).get('identity', 'UNIVAC-CORE')}")
    print(f"======================================================================")
    inline_multicore_hex_decode("414243") # Warm up cache arrays
    
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

    print(f"[LIVE MONITOR] Scanning infrastructure channels. Target Visio audit file loaded: '{visio_csv}'\n")

    try:
        while True:
            for hex_addr, serial_conn in list(_active_serial_handles.items()):
                if not serial_conn.in_waiting:
                    continue
                raw_bytes = serial_conn.read(serial_conn.in_waiting)
                if raw_bytes:
                    process_incoming_stream(hex_addr, raw_bytes, config_data, visio_csv)

            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Terminating auditing tracking mesh frameworks safely.")
        raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
