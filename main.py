import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import typer

import numpy as np
from numba import njit, prange

app = typer.Typer(help="UNIVAC-IX Tactical Dual-Way Radio Mesh, Live Auditing & Live Boundary Guard Fabric")

# Global register files mapping threshold boundaries read from documents
_safety_threshold_registers: Dict[str, Dict[str, int]] = {
    "0x0037": {"upper_limit": 200, "lower_limit": 10}, # Pre-cached example from Environment-Safety-Monitor
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


# --- Automated Operational Safeguard Enforcement Matrix ---

def verify_live_sensor_safety_compliance(hex_address: str, raw_payload_bytes: bytes) -> None:
    """Interceptors evaluate numerical sensor contents against compliance guidelines in real time."""
    clean_addr = hex_address.strip().lower()
    
    # 1. Guard against unmonitored channels that lack active guideline constraints
    if clean_addr not in _safety_threshold_registers:
        return
        
    # 2. Guard against empty data payloads to prevent buffer index execution crashes
    if len(raw_payload_bytes) == 0:
        return
        
    # Interpret the final byte of the incoming stream as the active numerical measurement value
    measured_integer_value = int(raw_payload_bytes[-1])
    bounds = _safety_threshold_registers[clean_addr]
    
    max_boundary = bounds.get("upper_limit", 255)
    min_boundary = bounds.get("lower_limit", 0)
    
    # 3. Check for upper limit threshold violations
    if measured_integer_value > max_boundary:
        sys.stdout.write("\a\a\a") # Fire audio terminal alarm notifications
        sys.stdout.flush()
        print("\n" + "!" * 80)
        print(f" !!! CRITICAL HARDWARE COMPLIANCE BREACH: UPPER SAFETY BOUNDS EXCEEDED !!!")
        print(f" -> SENSOR ROUTE CHANNEL: {clean_addr}")
        print(f" -> REGISTERED MAXIMUM:   {max_boundary}")
        print(f" -> REAL-TIME LIVE READ:  {measured_integer_value} !!! TRIPPED !!!")
        print("!" * 80 + "\n")
        return
        
    # 4. Check for lower limit threshold violations
    if measured_integer_value < min_boundary:
        sys.stdout.write("\a\a\a")
        sys.stdout.flush()
        print("\n" + "!" * 80)
        print(f" !!! CRITICAL HARDWARE COMPLIANCE BREACH: LOWER SAFETY BOUNDS EXCEEDED !!!")
        print(f" -> SENSOR ROUTE CHANNEL: {clean_addr}")
        print(f" -> REGISTERED MINIMUM:   {min_boundary}")
        print(f" -> REAL-TIME LIVE READ:  {measured_integer_value} !!! TRIPPED !!!")
        print("!" * 80 + "\n")
        return


# --- Core Operational Input Processing Layer ---

def process_incoming_stream(hex_address: str, raw_payload: bytes, config_data: Dict[str, Any], target_csv: Path) -> None:
    clean_addr = hex_address.strip().lower()
    hex_payload_str = raw_payload.hex().upper()
    
    # Run immediate real-time compliance tracking verification against our guideline limits
    verify_live_sensor_safety_compliance(clean_addr, raw_payload)

    # Standard routing loops for standard peripheral modules continue below
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
    """Manually routes an input frame payload to verify compliance policing engine reactions."""
    config_data = load_system_config(config)
    raw_data = bytes.fromhex(payload.strip().upper())
    process_incoming_stream(hex_address, raw_data, config_data, visio_csv)


if __name__ == "__main__":
    app()
