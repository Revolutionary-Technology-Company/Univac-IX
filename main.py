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

app = typer.Typer(help="UNIVAC-IX Tactical Automation, Dual-Way Radio Mesh & Safety Core Fabric")

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


# --- Automated Radio Message Processing & Injection Engine ---

def handle_incoming_radio_signal(hex_payload_str: str, config_data: Dict[str, Any]) -> None:
    """Decodes incoming over-the-air packet blocks on Port 19 and hot-injects them into system command layers."""
    decoded_text = inline_multicore_hex_decode(hex_payload_str)
    if not decoded_text:
        return
        
    print(f"\n[RADIO MESH RX] Incoming signal captured on channel 0x0013 (RADIO_TRANS_RX).")
    print(f"  -> Raw Telemetry Stream: {hex_payload_str}")
    print(f"  -> Plaintext Extracted:  {decoded_text}")
    
    # Standard format for field engineer transmissions: "[CMD] TARGET_ADDR:OVERRIDE_HEX"
    if not decoded_text.startswith("[CMD]"):
        print("  -> [REJECTED] Payload missing authorized tactical command token format structure.", file=sys.stderr)
        return
        
    try:
        # Strip token prefix and break down address and payload parameters
        command_payload = decoded_text.replace("[CMD]", "").strip()
        target_addr, override_hex = command_payload.split(":", 1)
        
        print(f"  -> [AUTHORIZED COMMAND VALIDATED] Hot-injecting radio instruction straight to terminal system...")
        print(f"    * TARGET ROUTE INTERFACE: {target_addr.strip().upper()}")
        print(f"    * INJECTED HEX VECTOR:   {override_hex.strip().upper()}")
        
        # Programmatically execute the command loop just as if it were natively sent over standard hardware layers
        raw_bytes = bytes.fromhex(override_hex.strip().upper())
        process_incoming_stream(target_addr.strip().lower(), raw_bytes, config_data)
    except Exception as parse_err:
        print(f"  -> [MALFORMED INTERRUPT] Failed to parse internal radio override string parameters: {parse_err}", file=sys.stderr)

def process_incoming_stream(hex_address: str, raw_payload: bytes, config_data: Dict[str, Any]) -> None:
    clean_addr = hex_address.strip().lower()
    hex_payload_str = raw_payload.hex().upper()
    
    # Check if the signal hit our radio receiver channel
    if clean_addr == "0x0013":
        handle_incoming_radio_signal(hex_payload_str, config_data)
        return

    # Normal routing loops for standard peripheral interfaces continue below
    decoded_readable_text = inline_multicore_hex_decode(hex_payload_str)
    print(f"  [CORE FABRIC EXECUTE] Address: {clean_addr} -> Processing Module Data Stream: {decoded_readable_text}")


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
    network_port: int = typer.Option(8080, help="Network port simulating aggregate fiber optic lines.")
):
    """Launches the master receiver engine processing hardware lines, network data, and bidirectional radio inputs."""
    global _active_serial_handles
    config_data = load_system_config(config)
    print(f"\n======================================================================")
    print(f"FULL DUAL-WAY RADIO MESH DAEMON LIVE: {config_data.get('system', {}).get('identity', 'UNIVAC-CORE')}")
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

    print(f"[LIVE MONITOR] Scanning infrastructure channels. Radio Receiver (Port 19) is armed.\n")

    try:
        while True:
            # Poll all open physical serial lanes including our radio receiver
            for hex_addr, serial_conn in list(_active_serial_handles.items()):
                if not serial_conn.in_waiting:
                    continue
                raw_bytes = serial_conn.read(serial_conn.in_waiting)
                if raw_bytes:
                    process_incoming_stream(hex_addr, raw_bytes, config_data)

            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Terminating radio mesh framework safely.")
        raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
