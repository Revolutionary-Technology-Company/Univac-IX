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

app = typer.Typer(help="UNIVAC-IX Tactical Dual-Way Radio Mesh, Live Boundary Guard & Telemetry Alert Fabric")

# Global handle storage for open physical radio transmitter lines
_active_serial_handles: Dict[str, Any] = {}

# Global register files mapping threshold boundaries read from documents
_safety_threshold_registers: Dict[str, Dict[str, int]] = {
    "0x0037": {"upper_limit": 200, "lower_limit": 10},
    "0x0038": {"upper_limit": 250, "lower_limit": 18}
}

_cached_fingerprints: Dict[str, str] = {
    "0x0011": "DRIVER_MIL_STD_1397_TACTICAL",
    "0x0012": "DRIVER_MIL_STD_1397_TACTICAL",
    "0x0013": "DRIVER_AVIATION_KNOWLEDGE",
    "0x0014": "DRIVER_AVIATION_KNOWLEDGE",
    "0x0022": "DRIVER_OTIS_GEN360",
    "0x0037": "DRIVER_SAFETY_MONITOR",
    "0x0038": "DRIVER_SAFETY_MONITOR"
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


# --- Automated Over-The-Air Radio Alert Broadcasting Engine ---

def dispatch_emergency_radio_broadcast(hex_address: str, violation_type: str, threshold_val: int, current_val: int) -> None:
    """Formats a compact emergency message and transmits it over long-range radio hardware on Port 20."""
    radio_tx_addr = "0x0014" # Hardcoded route parameter matching PORT_20 RADIO_TRANS_TX allocation
    
    if radio_tx_addr not in _active_serial_handles:
        print(f"  [RADIO MESH DEFERRED] Cannot broadcast alert. Radio line {radio_tx_addr} is currently offline.", file=sys.stderr)
        return

    timestamp = time.strftime("%H:%M:%S")
    # Compact, parsing-friendly text structure for emergency field paging hardware or satellite modems
    radio_message = f"[UNIVAC-BREACH] {timestamp} | CH:{hex_address} | TYPE:{violation_type} | LIMIT:{threshold_val} | VAL:{current_val} // EVAC_ERR"
    
    # Fast encoding conversion to binary byte vector matrices
    hex_payload = radio_message.encode("utf-8").hex().upper()
    raw_packet_bytes = bytes.fromhex(hex_payload)
    
    try:
        _active_serial_handles[radio_tx_addr].write(raw_packet_bytes)
        print(f"  [RADIO MESH BROADCAST] Emergency warning dispatched across wireless network drops.")
        print(f"    -> Message Payload: {radio_message}")
    except Exception as tx_err:
        print(f"  [RADIO MESH FAULT] Signal drop on physical radio transmission array: {tx_err}", file=sys.stderr)


# --- Automated Real-time Boundary Guard Interceptor ---

def verify_live_sensor_safety_compliance(hex_address: str, raw_payload_bytes: bytes) -> None:
    """Evaluates numerical sensor inputs against compliance guidelines and triggers autonomous radio alerts on breaches."""
    clean_addr = hex_address.strip().lower()
    
    if clean_addr not in _safety_threshold_registers:
        return
    if len(raw_payload_bytes) == 0:
        return
        
    measured_integer_value = int(raw_payload_bytes[-1])
    bounds = _safety_threshold_registers[clean_addr]
    
    max_boundary = bounds.get("upper_limit", 255)
    min_boundary = bounds.get("lower_limit", 0)
    
    # 1. Process Upper Limit Violation
    if measured_integer_value > max_boundary:
        sys.stdout.write("\a\a\a")
        sys.stdout.flush()
        print("\n" + "!" * 80)
        print(f" !!! CRITICAL HARDWARE COMPLIANCE BREACH: UPPER SAFETY BOUNDS EXCEEDED !!!")
        print(f" -> SENSOR ROUTE CHANNEL: {clean_addr} | Real-Time Live Read: {measured_integer_value} (MAX: {max_boundary})")
        print("!" * 80)
        
        # Deploy immediate autonomic over-the-air radio warning message
        dispatch_emergency_radio_broadcast(clean_addr, "MAX_EXCEEDED", max_boundary, measured_integer_value)
        print()
        return
        
    # 2. Process Lower Limit Violation
    if measured_integer_value < min_boundary:
        sys.stdout.write("\a\a\a")
        sys.stdout.flush()
        print("\n" + "!" * 80)
        print(f" !!! CRITICAL HARDWARE COMPLIANCE BREACH: LOWER SAFETY BOUNDS EXCEEDED !!!")
        print(f" -> SENSOR ROUTE CHANNEL: {clean_addr} | Real-Time Live Read: {measured_integer_value} (MIN: {min_boundary})")
        print("!" * 80)
        
        # Deploy immediate autonomic over-the-air radio warning message
        dispatch_emergency_radio_broadcast(clean_addr, "MIN_EXCEEDED", min_boundary, measured_integer_value)
        print()
        return


# --- Core Operational Signal Router ---

def process_incoming_stream(hex_address: str, raw_payload: bytes, config_data: Dict[str, Any], target_csv: Path) -> None:
    clean_addr = hex_address.strip().lower()
    hex_payload_str = raw_payload.hex().upper()
    
    verify_live_sensor_safety_compliance(clean_addr, raw_payload)
    decoded_readable_text = inline_multicore_hex_decode(hex_payload_str)
    print(f"  [CORE PROCESSING] Address: {clean_addr} | Stream: {hex_payload_str} | Ascii: {decoded_readable_text}")


# --- Daemon Engine Baseline Configuration Commands ---

def load_system_config(config_path: Path) -> Dict[str, Any]:
    if config_path.exists():
        with open(config_path, "r") as stream:
            return yaml.safe_load(stream)
    print(f"Configuration Fault: Path {config_path} not found.", file=sys.stderr)
    raise typer.Exit(code=1)

@app.command(name="route-signal")
def route_signal_command(
    hex_address: str = typer.Argument(..., help="Target device hexadecimal address."),
    payload: str = typer.Argument(..., help="The hexadecimal input or output signal payload data."),
    config: Path = typer.Option(Path("config.yaml"), help="Path to the node configuration registry file."),
    visio_csv: Path = typer.Option(Path("visio_mapping.csv"), help="The target data visualizer spreadsheet to write audits to.")
):
    """Manually routes an input frame payload to verify compliance and radio alerting capabilities."""
    global _active_serial_handles
    config_data = load_system_config(config)
    
    # Stub: Mount a virtual dummy handle to represent the physical radio hardware interface for testing if missing
    if "0x0014" not in _active_serial_handles:
        class DummySerial:
            def write(self, data): pass
        _active_serial_handles["0x0014"] = DummySerial()
        
    raw_data = bytes.fromhex(payload.strip().upper())
    process_incoming_stream(hex_address, raw_data, config_data, visio_csv)


if __name__ == "__main__":
    app()
