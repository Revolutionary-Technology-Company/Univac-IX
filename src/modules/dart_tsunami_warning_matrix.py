# File Name: dart_tsunami_warning_matrix.py
# Location: /src/modules/
# Subsystem: DART Tsunami Early Warning & Wave Propagation Matrix
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_wave_kinematics(ocean_depths_m: np.ndarray, pressure_anomalies_psi: np.ndarray) -> np.ndarray:
    """Calculates tsunami wave propagation velocity (m/s) across deep ocean basins."""
    total_buoys = ocean_depths_m.shape[0]
    wave_velocities_ms = np.zeros(total_buoys, dtype=np.float64)
    gravity = 9.81
    
    for i in prange(total_buoys):
        # Only calculate if a significant pressure anomaly (seabed displacement) is detected
        if pressure_anomalies_psi[i] > 0.5:
            # Tsunami waves behave as shallow-water waves regardless of ocean depth
            # Velocity = sqrt(g * depth)
            wave_velocities_ms[i] = math.sqrt(gravity * ocean_depths_m[i])
        else:
            wave_velocities_ms[i] = 0.0
            
    return wave_velocities_ms

class DARTTsunamiWarningMatrix:
    def __init__(self):
        # Pressure anomaly threshold (PSI) that indicates massive water column displacement
        self.anomaly_threshold_psi = 0.8 

    def evaluate_ocean_grid(self, buoy_ids: List[str], depths_m: List[float], anomalies_psi: List[float], distance_to_coast_km: List[float]) -> dict:
        print(f"\n[OCEANOGRAPHY] Sweeping global DART buoy network for tectonic displacement...")
        start_time = time.time()
        
        depth_arr = np.array(depths_m, dtype=np.float64)
        anomaly_arr = np.array(anomalies_psi, dtype=np.float64)
        
        # Execute JIT Math
        velocities_ms = parallel_calculate_wave_kinematics(depth_arr, anomaly_arr)
        
        coastal_warnings = []
        for i in range(len(buoy_ids)):
            if velocities_ms[i] > 0.0 and anomalies_psi[i] >= self.anomaly_threshold_psi:
                velocity_kmh = velocities_ms[i] * 3.6
                impact_time_hours = distance_to_coast_km[i] / velocity_kmh
                
                coastal_warnings.append({
                    "buoy_id": buoy_ids[i],
                    "wave_velocity_kmh": round(velocity_kmh, 2),
                    "estimated_coastal_impact_hrs": round(impact_time_hours, 2),
                    "action": "SOUND_COASTAL_SIRENS_AND_EAS"
                })

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "TSUNAMI_GENERATION_DETECTED" if coastal_warnings else "OCEAN_BASIN_STABLE"

        return {
            "pacific_ring_status": status,
            "buoys_polled": len(buoy_ids),
            "evacuation_orders": coastal_warnings,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    tsunami = DARTTsunamiWarningMatrix()
    # Mocking a massive subduction earthquake near Buoy 2 (Deep water, fast wave)
    print("TESTING TSUNAMI WARNING MATRIX:\n", tsunami.evaluate_ocean_grid(
        ["PACIFIC-01", "JAPAN-TRENCH-02", "CASCADIA-03"], 
        [4000.0, 6000.0, 2500.0], 
        [0.1, 1.2, 0.05], 
        [1200.0, 800.0, 300.0]
    ))
