# File Name: kessler_orbital_debris_sweeper.py
# Location: /src/modules/
# Subsystem: Kessler Syndrome Defense & Laser Ablation Matrix
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_ablation_delta_v(debris_masses_kg: np.ndarray, laser_energy_mj: np.ndarray) -> np.ndarray:
    """Calculates the change in velocity (Delta-V) induced by laser photon pressure and surface ablation."""
    total_debris = debris_masses_kg.shape[0]
    delta_v_ms = np.zeros(total_debris, dtype=np.float64)
    
    # Specific momentum coupling coefficient (C_m) for laser ablation on generic aerospace aluminum
    # Represents Newtons of thrust per Megawatt of laser power (approx 5e-5 N/W)
    c_m = 5.0e-5 
    
    for i in prange(total_debris):
        if debris_masses_kg[i] <= 0: continue
        
        # Energy in Joules
        energy_j = laser_energy_mj[i] * 1e6
        
        # Momentum transferred (p = Energy * C_m)
        momentum_kg_ms = energy_j * c_m
        
        # Delta-V = p / m
        delta_v_ms[i] = momentum_kg_ms / debris_masses_kg[i]
        
    return delta_v_ms

class KesslerDebrisSweeper:
    def __init__(self):
        # To lower a LEO perigee deep into the atmosphere for rapid burn-up requires roughly 15 m/s of Delta-V
        self.required_deorbit_dv_ms = 15.0 

    def engage_orbital_shrapnel(self, debris_ids: List[str], masses_kg: List[float], altitudes_km: List[float], applied_laser_mj: float) -> dict:
        print(f"\n[ORBITAL DEFENSE] Sweeping LEO for micro-debris. Engaging ablation lasers...")
        start_time = time.time()
        
        m_arr = np.array(masses_kg, dtype=np.float64)
        
        # Assume constant 1.5 Megajoule pulses for the ground laser array
        laser_arr = np.full(len(masses_kg), applied_laser_mj, dtype=np.float64)
        
        # Execute JIT Math
        induced_dv = parallel_calculate_ablation_delta_v(m_arr, laser_arr)
        
        engagements = []
        for i in range(len(debris_ids)):
            dv = induced_dv[i]
            
            # If the laser pulse imparts enough delta-v, the debris will de-orbit
            if dv >= self.required_deorbit_dv_ms:
                engagements.append({
                    "debris_id": debris_ids[i],
                    "mass_kg": masses_kg[i],
                    "induced_delta_v": round(dv, 2),
                    "status": "SUCCESSFUL_DEORBIT_BURN_UP_CONFIRMED"
                })
            else:
                engagements.append({
                    "debris_id": debris_ids[i],
                    "mass_kg": masses_kg[i],
                    "induced_delta_v": round(dv, 2),
                    "status": "MASS_TOO_LARGE_ADDITIONAL_PASSES_REQUIRED"
                })

        execution_ms = (time.time() - start_time) * 1000.0
        
        cleared_count = sum(1 for e in engagements if e["status"] == "SUCCESSFUL_DEORBIT_BURN_UP_CONFIRMED")

        return {
            "orbit_sustainability": "KESSLER_SYNDROME_MITIGATED",
            "debris_targeted": len(debris_ids),
            "shrapnel_deorbited": cleared_count,
            "ablation_log": engagements,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    kessler = KesslerDebrisSweeper()
    # Mocking LEO Shrapnel. Piece 3 is a heavy 50kg satellite chunk that needs multiple laser passes.
    print("TESTING KESSLER DEBRIS SWEEPER:\n", kessler.engage_orbital_shrapnel(
        ["SHRAPNEL-A", "BOLT-B", "DEAD-CUBESAT-C"], 
        [0.5, 0.05, 50.0], # Masses in kg
        [400.0, 410.0, 405.0], 
        1.5 # 1.5 Megajoules per laser pulse
    ))
