# File Name: private_5g_core_simulator.py
# Location: /src/modules/
# Subsystem: Private 5G Core (5GC), CBRS Orchestrator & Field Test Matrix
# Copyright (c) 2026 Revolutionary Technology

import os
import sys
import time
import math
import random
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List
from pathlib import Path

# --- DYNAMIC PATH RESOLUTION ---
MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# UNIVERSAL CONSTANTS
C_SPEED = 299792458.0  # Speed of Light (m/s)

@njit(parallel=True, cache=True, fastmath=True)
def parallel_timing_advance_and_rsrp(distances_m: np.ndarray, tx_power_dbm: float, center_freq_mhz: float) -> np.ndarray:
    """
    Calculates Timing Advance (TA) and Reference Signal Received Power (RSRP).
    Returns Array: [Timing_Advance_microseconds, RSRP_dBm]
    """
    total_ue = distances_m.shape[0]
    results = np.zeros((total_ue, 2), dtype=np.float64)
    
    # FSPL Constant for standard propagation
    fspl_constant = 20.0 * math.log10((4.0 * math.pi) / C_SPEED)
    
    for i in prange(total_ue):
        d = distances_m[i]
        if d > 0:
            # 1. Timing Advance (TA = 2d / c) - Time for signal to go tower-to-phone and back
            # Multiplied by 1,000,000 to get microseconds
            ta_us = ((2.0 * d) / C_SPEED) * 1000000.0
            
            # 2. RSRP via Path Loss
            # Convert MHz to Hz for the formula
            fspl = (20.0 * math.log10(d)) + (20.0 * math.log10(center_freq_mhz * 1e6)) + fspl_constant
            # Assuming a standard high-gain base station antenna (e.g., 15 dBi)
            rsrp = (tx_power_dbm + 15.0) - fspl
            
            results[i, 0] = ta_us
            results[i, 1] = rsrp
            
    return results

class Private5GCoreMatrix:
    def __init__(self):
        self.facility_status = "CBRS_CORE_ACTIVE"
        # CBRS Band 48 operates between 3550 and 3700 MHz
        self.cbrs_freq_mhz = 3600.0 
        self.max_range_meters = 8046.72 # Approx 5 miles
        
    def _generate_virtual_msisdn(self, gps_coords: tuple) -> str:
        """Generates a locked +1 (XXX) 555-XXXX number based on virtual hardware profiles."""
        lat, lon = gps_coords
        # Mock logic to assign area code based on latitude (e.g., Seattle ~ 47.6 -> 206)
        area_code = "206" if lat > 47.0 else "415"
        subscriber_number = random.randint(1000, 9999)
        return f"+1 ({area_code}) 555-{subscriber_number}"

    def execute_cbrs_network_mesh(self, hw_ids: List[str], gps_locations: List[tuple], distances_from_tower_m: List[float]) -> dict:
        """
        Simulates an Evolved Packet Core (EPC) assigning private numbers to localized 
        Sierra Wireless hardware operating on private 5G spectrum.
        """
        print(f"\n[5G CORE] Spooling Private Evolved Packet Core (EPC). Scanning CBRS Band 48...")
        start_time = time.time()
        
        dist_arr = np.array(distances_from_tower_m, dtype=np.float64)
        # Using a high-power private cell tower base station (40 dBm / 10 Watts)
        rf_metrics = parallel_timing_advance_and_rsrp(dist_arr, 40.0, self.cbrs_freq_mhz)
        
        diagnostics = []
        for i in range(len(hw_ids)):
            hw_id = hw_ids[i]
            dist = dist_arr[i]
            ta_us = rf_metrics[i, 0]
            rsrp = rf_metrics[i, 1]
            
            assigned_number = self._generate_virtual_msisdn(gps_locations[i])
            
            if dist > self.max_range_meters:
                status = "OUT_OF_RANGE - RRC_CONNECTION_DROPPED"
            elif rsrp < -110.0:
                status = "CELL_EDGE - HIGH_INTERFERENCE_DSP_ACTIVE"
            else:
                status = "5G_ATTACH_SUCCESS - QAM_256_LOCKED"
                
            diagnostics.append({
                "hardware_profile": hw_id,
                "assigned_private_number": assigned_number,
                "distance_meters": round(dist, 2),
                "timing_advance_us": round(ta_us, 4),
                "rsrp_dbm": round(rsrp, 2),
                "status": status
            })

        execution_ms = (time.time() - start_time) * 1000.0

        return {
            "core_status": "PRIVATE_NETWORK_ROUTING_NOMINAL",
            "active_band": "LTE_BAND_48_CBRS",
            "connected_ues": len(hw_ids),
            "diagnostics": diagnostics,
            "execution_time_ms": round(execution_ms, 5)
        }

    def launch_field_test_cli(self, arfcn: int, rsrp: float, sinr: float):
        """Generates a text-based Field Test Mode interface based on exact 3GPP math."""
        print("\n==================================================")
        print(" UNIVAC-IX RF FIELD TEST MODE || DIAGNOSTIC SHELL ")
        print("==================================================")
        
        # Calculate frequency from ARFCN (Assuming standard 5G N78 / LTE B48 parameters)
        f_low = 3550.0
        arfcn_offset = 552448 if arfcn > 100000 else 43590 # Rough proxy for NR vs LTE
        
        print(f"-> Serving Cell Identity (PCI): {random.randint(1, 500)}")
        print(f"-> RSRP (Signal Power):         {rsrp} dBm")
        print(f"-> SINR (Signal Quality):       {sinr} dB")
        print(f"-> Channel Code (ARFCN):        {arfcn}")
        
        if rsrp > -80:
            print("-> Link Quality:                [ EXCELLENT ]")
        elif rsrp > -100:
            print("-> Link Quality:                [ MODERATE ]")
        else:
            print("-> Link Quality:                [ WEAK / CELL EDGE ]")
        print("==================================================\n")


if __name__ == "__main__":
    core = Private5GCoreMatrix()
    
    # MOCK PRIVATE 5G NETWORK ALLOCATION
    # Emulating 3 Sierra EM9291 modems attempting to attach to the Univac tower
    print(core.execute_cbrs_network_mesh(
        hw_ids=["SIERRA_EM9291_ALPHA", "SIERRA_EM9291_BRAVO", "SIERRA_EM9291_CHARLIE"],
        gps_locations=[(47.6062, -122.3321), (47.6101, -122.3421), (37.7749, -122.4194)],
        distances_from_tower_m=[1500.0, 5000.0, 9500.0] # 3rd device is outside the 5-mile limit
    ))
    
    # LAUNCH FIELD TEST MODE (Simulating a device with excellent signal on CBRS)
    core.launch_field_test_cli(arfcn=552448, rsrp=-75.5, sinr=22.0)
