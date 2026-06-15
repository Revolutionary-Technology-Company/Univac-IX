# File Name: emp_geomagnetic_storm_interlock.py
# Location: /src/modules/
# Subsystem: EMP & Geomagnetically Induced Current (GIC) Governor
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_gic_amperes(db_dt_nt_min: np.ndarray, line_lengths_km: np.ndarray, resistance_ohms: float) -> np.ndarray:
    """Calculates Geomagnetically Induced Currents (GIC) in Amperes across multiple long-haul transmission lines."""
    total_lines = db_dt_nt_min.shape[0]
    induced_currents_amp = np.zeros(total_lines, dtype=np.float64)
    
    for i in prange(total_lines):
        # Simplified Faraday induction calculation for long power lines
        # E-field (V/km) approximated from magnetic field rate of change (nT/min)
        e_field_v_km = db_dt_nt_min[i] * 0.05 
        induced_voltage = e_field_v_km * line_lengths_km[i]
        
        induced_currents_amp[i] = induced_voltage / resistance_ohms
        
    return induced_currents_amp

class ElectromagneticPulseGovernor:
    def __init__(self):
        self.grid_islanded = False
        self.safe_current_threshold_amp = 50.0 # Standard transformer saturation limit

    def evaluate_magnetometer_telemetry(self, db_dt_array: List[float], line_lengths: List[float]) -> dict:
        print(f"\n[SPACE WEATHER] Scanning for High-Altitude EMP and Coronal Mass Ejections...")
        start_time = time.time()
        
        db_arr = np.array(db_dt_array, dtype=np.float64)
        len_arr = np.array(line_lengths, dtype=np.float64)
        
        # Execute JIT math (Assuming average grid resistance of 0.5 ohms per phase)
        gic_amperes = parallel_calculate_gic_amperes(db_arr, len_arr, 0.5)
        
        peak_current = np.max(gic_amperes)
        
        status = "MAGNETOSPHERE_STABLE"
        action = "MAINTAIN_GRID_TIE"
        
        if peak_current > self.safe_current_threshold_amp:
            self.grid_islanded = True
            status = "CRITICAL_EMP_OR_CME_DETECTED"
            action = "ISOLATE_MAINFRAME_TO_BATTERY_BACKUP"

        execution_ms = (time.time() - start_time) * 1000.0

        return {
            "geomagnetic_status": status,
            "peak_induced_current_amp": round(peak_current, 2),
            "autonomic_action": action,
            "grid_islanded": self.grid_islanded,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    emp_gov = ElectromagneticPulseGovernor()
    # Mocking a massive solar storm: 2000 nT/min change over 300km power lines
    print("TESTING EMP/GIC GOVERNOR:\n", emp_gov.evaluate_magnetometer_telemetry([50.0, 100.0, 2500.0], [50.0, 150.0, 300.0]))
