# File Name: legacy_dreadnought_synchro_resolver.py
# Location: /src/modules/
# Subsystem: Pre-UNIVAC Analog Battleship Fire-Control Conversion
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any

@njit(parallel=True, cache=True, fastmath=True)
def parallel_resolve_synchro_angles(s1_s3_volts: np.ndarray, s3_s2_volts: np.ndarray, v_ref: float) -> np.ndarray:
    """Converts 3-phase analog synchro transmitter voltages into highly precise digital azimuth angles."""
    total_turrets = s1_s3_volts.shape[0]
    resolved_angles_deg = np.zeros(total_turrets, dtype=np.float64)
    
    for i in prange(total_turrets):
        # Prevent division by zero on dead lines
        if v_ref <= 0.0:
            continue
            
        # Standard Synchro formula utilizing arctan2 for full 360-degree resolution
        sin_theta = s1_s3_volts[i] / v_ref
        sin_theta_plus_120 = s3_s2_volts[i] / v_ref
        
        # Isolate cos(theta) using the 120-degree phase shift
        cos_theta = (sin_theta * -0.5 - sin_theta_plus_120) / (math.sqrt(3.0) / 2.0)
        
        angle_rad = math.atan2(sin_theta, cos_theta)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360.0
            
        resolved_angles_deg[i] = angle_deg
        
    return resolved_angles_deg

class LegacyDreadnoughtResolver:
    def __init__(self):
        self.reference_voltage = 115.0 # Standard WWII Naval AC Reference

    def process_analog_fire_control(self, turret_s1_s3: list, turret_s3_s2: list) -> dict:
        print(f"\n[DREADNOUGHT] Resolving pre-UNIVAC analog synchro voltages...")
        start_time = time.time()
        
        s1_arr = np.array(turret_s1_s3, dtype=np.float64)
        s3_arr = np.array(turret_s3_s2, dtype=np.float64)
        
        # Execute JIT Math
        digital_angles = parallel_resolve_synchro_angles(s1_arr, s3_arr, self.reference_voltage)
        
        execution_ms = (time.time() - start_time) * 1000.0

        return {
            "status": "ANALOG_CONVERTED_TO_DIGITAL",
            "turrets_tracked": len(turret_s1_s3),
            "digital_azimuths_deg": [round(a, 2) for a in digital_angles],
            "execution_time_ms": round(execution_ms, 5)
        }
