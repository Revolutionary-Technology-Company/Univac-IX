# File Name: advanced_ethernet_link_analyzer.py
# Location: /src/modules/
# Subsystem: Layer 1 Ethernet DSP, TDR & Physical Link Analyzer
# Copyright (c) 2026 Revolutionary Technology

import os
import sys
import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List
from pathlib import Path

# --- DYNAMIC PATH RESOLUTION ---
MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# SPEED OF LIGHT (Meters per second)
C_SPEED = 299792458.0 

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_tdr_length(pulse_round_trip_s: np.ndarray, nvp_factors: np.ndarray) -> np.ndarray:
    """
    Calculates physical cable length (meters) using Time-Domain Reflectometry (TDR).
    Equation: L = ((NVP * c) * t) / 2
    """
    total_ports = pulse_round_trip_s.shape[0]
    lengths_m = np.zeros(total_ports, dtype=np.float64)
    
    for i in prange(total_ports):
        # Velocity of the signal through the copper = NVP * Speed of Light
        signal_velocity = nvp_factors[i] * C_SPEED
        # Distance = Velocity * Time (Divided by 2 because the pulse must travel there and back)
        lengths_m[i] = (signal_velocity * pulse_round_trip_s[i]) / 2.0
        
    return lengths_m

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_insertion_loss(frequencies_hz: np.ndarray, k1: float, k2: float, k3: float) -> np.ndarray:
    """
    Calculates signal attenuation (dB) based on the frequency skin effect and dielectric loss.
    Equation: A(f) = k1 * sqrt(f) + k2 * f + k3 / sqrt(f)
    """
    total_ports = frequencies_hz.shape[0]
    attenuation_db = np.zeros(total_ports, dtype=np.float64)
    
    for i in prange(total_ports):
        # Ethernet attenuation formulas are typically standardized in MHz
        f_mhz = frequencies_hz[i] / 1e6 
        if f_mhz > 0:
            attenuation_db[i] = (k1 * math.sqrt(f_mhz)) + (k2 * f_mhz) + (k3 / math.sqrt(f_mhz))
            
    return attenuation_db

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_snr_and_ber(signal_power_mw: np.ndarray, noise_power_mw: np.ndarray, error_bits: np.ndarray, total_bits: np.ndarray) -> np.ndarray:
    """
    Calculates Signal-to-Noise Ratio (dB) and the Bit Error Rate (BER).
    Returns a 2D array: [SNR_dB, BER]
    """
    total_ports = signal_power_mw.shape[0]
    results = np.zeros((total_ports, 2), dtype=np.float64)
    
    for i in prange(total_ports):
        # 1. SNR = 10 * log10(Signal / Noise)
        if noise_power_mw[i] > 0:
            results[i, 0] = 10.0 * math.log10(signal_power_mw[i] / noise_power_mw[i])
            
        # 2. BER = Error Bits / Total Transmitted Bits
        if total_bits[i] > 0:
            results[i, 1] = error_bits[i] / total_bits[i]
            
    return results

class AdvancedEthernetAnalyzer:
    def __init__(self):
        self.facility_status = "L1_DSP_ACTIVE"
        self.max_ethernet_length_m = 100.0 # Standard Cat5e/Cat6 maximum distance
        self.min_acceptable_snr_db = 20.0  # Minimum SNR for reliable Gigabit link

        # Standard attenuation coefficients for Cat6 Copper
        self.cat6_k1 = 1.82
        self.cat6_k2 = 0.0169
        self.cat6_k3 = 0.25

    def execute_physical_link_scan(self, port_ids: List[str], tdr_pulse_times_s: List[float], nvp_ratings: List[float], 
                                   frequencies_hz: List[float], sig_power_mw: List[float], noise_power_mw: List[float], 
                                   error_bits: List[int], total_bits: List[int]) -> dict:
        """
        Executes the full suite: TDR Cable Length, Insertion Loss, SNR, and BER profiling.
        """
        print(f"\n[NETWORK HARDWARE] Engaging TDR pulse lasers and sweeping physical Ethernet PHY boundaries...")
        start_time = time.time()
        
        # Convert lists to NumPy arrays for JIT compilation
        tdr_arr = np.array(tdr_pulse_times_s, dtype=np.float64)
        nvp_arr = np.array(nvp_ratings, dtype=np.float64)
        freq_arr = np.array(frequencies_hz, dtype=np.float64)
        sig_arr = np.array(sig_power_mw, dtype=np.float64)
        noise_arr = np.array(noise_power_mw, dtype=np.float64)
        err_arr = np.array(error_bits, dtype=np.float64)
        tot_arr = np.array(total_bits, dtype=np.float64)
        
        # 1. TDR Length Calculation
        lengths_m = parallel_calculate_tdr_length(tdr_arr, nvp_arr)
        
        # 2. Attenuation / Insertion Loss Calculation
        insertion_loss_db = parallel_calculate_insertion_loss(freq_arr, self.cat6_k1, self.cat6_k2, self.cat6_k3)
        
        # 3. SNR and BER Calculations
        snr_ber_matrix = parallel_calculate_snr_and_ber(sig_arr, noise_arr, err_arr, tot_arr)
        
        telemetry_logs = []
        for i in range(len(port_ids)):
            port = port_ids[i]
            length = lengths_m[i]
            loss = insertion_loss_db[i]
            snr = snr_ber_matrix[i, 0]
            ber = snr_ber_matrix[i, 1]
            
            # --- FAULT DETECTION LOGIC ---
            if length > self.max_ethernet_length_m:
                action = f"TDR_FAULT: CABLE EXCEEDS 100m BOUNDARY ({round(length, 1)}m) - SIGNAL DEGRADATION IMMINENT"
            elif snr < self.min_acceptable_snr_db:
                action = f"CROSS-TALK/NOISE FAULT: SNR CRITICAL ({round(snr, 1)} dB) - RE-TERMINATE RJ45"
            elif ber > 1e-9: # 1 error per billion bits is usually the threshold for failure
                action = f"BIT_ERROR_RATE_CRITICAL: PACKET LOSS SPIKING ({ber:.2E}) - CHECK PHY HARDWARE"
            else:
                action = "PHYSICAL_LINK_PRISTINE_-_GIGABIT_FULL_DUPLEX_LOCKED"
                
            telemetry_logs.append({
                "port_id": port,
                "tdr_cable_length_meters": round(length, 2),
                "insertion_loss_db": round(loss, 2),
                "signal_to_noise_ratio_db": round(snr, 2),
                "bit_error_rate": f"{ber:.2E}",
                "diagnostic_action": action
            })

        execution_ms = (time.time() - start_time) * 1000.0

        return {
            "analyzer_status": "L1_ETHERNET_TELEMETRY_CAPTURED",
            "ports_scanned": len(port_ids),
            "tdr_pulse_status": "ACTIVE",
            "diagnostics": telemetry_logs,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    analyzer = AdvancedEthernetAnalyzer()
    
    # MOCKING TELEMETRY DATA:
    # Port 1 (eth0) - Perfect Cat6 cable, 45 meters long.
    # Port 2 (eth1) - Cable is broken/shorted at exactly 12 meters (fast TDR return).
    # Port 3 (eth2) - Cable is way too long (135m) and experiencing massive interference (high noise, low SNR).
    
    # 250 MHz base frequency (Standard for 1-Gigabit over Cat6)
    freq = 250000000.0 
    
    print("TESTING ADVANCED ETHERNET LINK ANALYZER:\n", analyzer.execute_physical_link_scan(
        port_ids=["eth0_MAIN", "eth1_DMZ", "eth2_WAREHOUSE"], 
        tdr_pulse_times_s=[4.4e-7, 1.17e-7, 1.32e-6], # Time in seconds (e.g. 0.00000044s)
        nvp_ratings=[0.68, 0.68, 0.68],               # Cat6 NVP is typically ~0.68 (68% the speed of light)
        frequencies_hz=[freq, freq, freq],
        sig_power_mw=[100.0, 100.0, 100.0],
        noise_power_mw=[0.5, 5.0, 85.0],              # Port 3 has massive noise
        error_bits=[0, 0, 15000],
        total_bits=[1000000000, 1000000000, 1000000000] # 1 Billion bits transmitted
    ))
