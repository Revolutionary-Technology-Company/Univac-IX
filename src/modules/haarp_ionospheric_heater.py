# File Name: haarp_ionospheric_heater.py
# Location: /src/modules/
# Subsystem: Phased Array Ionospheric Heater & ERP Matrix
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_phased_array_erp(transmitter_power_w: np.ndarray, antenna_gains_dbi: np.ndarray) -> np.ndarray:
    """Calculates Effective Radiated Power (ERP) for a massive grid of dipole antennas."""
    total_antennas = transmitter_power_w.shape[0]
    erp_watts = np.zeros(total_antennas, dtype=np.float64)
    
    for i in prange(total_antennas):
        # Convert dB to linear gain: Gain = 10^(dBi / 10)
        linear_gain = 10.0 ** (antenna_gains_dbi[i] / 10.0)
        erp_watts[i] = transmitter_power_w[i] * linear_gain
        
    return erp_watts

class HAARPIonosphericHeater:
    def __init__(self):
        # The Gakona, Alaska HAARP array max ERP is roughly 3.6 Gigawatts
        self.max_safe_erp_gw = 4.0 

    def fire_ionospheric_array(self, frequency_mhz: float, powers_w: List[float], gains_dbi: List[float]) -> dict:
        print(f"\n[ATMOSPHERIC RF] Spooling phased array for ionospheric excitation...")
        start_time = time.time()
        
        p_arr = np.array(powers_w, dtype=np.float64)
        g_arr = np.array(gains_dbi, dtype=np.float64)
        
        # Execute JIT Math
        erp_array = parallel_calculate_phased_array_erp(p_arr, g_arr)
        total_erp_watts = np.sum(erp_array)
        total_erp_gw = total_erp_watts / 1e9
        
        # Calculate theoretical electron density shift in the F-layer (simplified physics proxy)
        excitation_factor = (total_erp_gw / self.max_safe_erp_gw) * 100.0
        
        status = "TRANSMITTING"
        if total_erp_gw > self.max_safe_erp_gw:
            status = "CRITICAL_ERP_OVERLOAD_SHUTDOWN"

        execution_ms = (time.time() - start_time) * 1000.0

        return {
            "array_status": status,
            "target_frequency_mhz": frequency_mhz,
            "active_dipoles": len(powers_w),
            "total_effective_radiated_power_gw": round(total_erp_gw, 3),
            "ionospheric_excitation_pct": round(excitation_factor, 2),
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    haarp = HAARPIonosphericHeater()
    # Mocking 180 crossed dipole antennas, each pushing 20kW at 15 dBi gain.
    mock_powers = [20000.0] * 180
    mock_gains = [15.0] * 180
    print("TESTING HAARP ARRAY:\n", haarp.fire_ionospheric_array(4.5, mock_powers, mock_gains))
