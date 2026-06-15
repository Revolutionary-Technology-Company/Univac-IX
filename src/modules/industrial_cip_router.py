# File Name: industrial_cip_router.py
# Location: /src/modules/
# Subsystem: Allen-Bradley / GE / GM CIP Packet Constructor
# Copyright (c) 2026 Revolutionary Technology

import time
import numpy as np
from numba import njit, prange
from typing import Dict, Any

@njit(cache=True, fastmath=True)
def calculate_crc32_industrial(data_array: np.ndarray) -> int:
    """Calculates a hard deterministic CRC-32 checksum for validating EtherNet/IP CIP packets."""
    crc = 0xFFFFFFFF
    for i in range(data_array.shape[0]):
        crc ^= data_array[i]
        for _ in range(8):
            mask = -(crc & 1)
            crc = (crc >> 1) ^ (0xEDB88320 & mask)
    return ~crc & 0xFFFFFFFF

class IndustrialCIPRouter:
    def __init__(self):
        self.supported_vendors = ["ALLEN_BRADLEY", "GENERAL_ELECTRIC", "GENERAL_MOTORS_LAN"]

    def construct_override_packet(self, vendor: str, register_hex: str, payload_value: int) -> dict:
        target_vendor = vendor.strip().upper()
        if target_vendor not in self.supported_vendors:
            return {"status": "FAULT", "error": f"Vendor {target_vendor} not supported by CIP core."}

        # 1. Build the mock packet header (Command, Length, Session Handle, Status)
        # 0x6F = SendRRData (Unconnected Message)
        header = [0x6F, 0x00, 0x14, 0x00, 0x01, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00, 0x00]
        
        # 2. Append Target Register and Payload (Simulated byte stream)
        reg_int = int(register_hex, 16)
        register_bytes = [reg_int >> 8 & 0xFF, reg_int & 0xFF]
        payload_bytes = [payload_value >> 24 & 0xFF, payload_value >> 16 & 0xFF, payload_value >> 8 & 0xFF, payload_value & 0xFF]
        
        full_packet = np.array(header + register_bytes + payload_bytes, dtype=np.uint8)
        
        # 3. Numba JIT CRC-32 Checksum
        checksum = calculate_crc32_industrial(full_packet)
        packet_hex = "".join([f"{b:02X}" for b in full_packet])

        return {
            "status": "CIP_PACKET_READY",
            "vendor_target": target_vendor,
            "target_register": register_hex,
            "packet_hex_stream": packet_hex,
            "crc32_checksum": hex(checksum),
            "timestamp": time.time()
        }

if __name__ == "__main__":
    router = IndustrialCIPRouter()
    print("TESTING INDUSTRIAL CIP ROUTER:\n", router.construct_override_packet("ALLEN_BRADLEY", "0x4A2C", 9999))
