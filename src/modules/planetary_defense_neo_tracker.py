# File Name: planetary_defense_neo_tracker.py
# Location: /src/modules/
# Subsystem: Near Earth Object (NEO) Planetary Defense Core
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_impact_energy(masses_kg: np.ndarray, velocities_kms: np.ndarray) -> np.ndarray:
    """Calculates the kinetic energy of incoming asteroids in Megatons of TNT equivalent."""
    total_objects = masses_kg.shape[0]
    yields_megatons = np.zeros(total_objects, dtype=np.float64)
    
    # 1 Megaton of TNT = 4.184 x 10^15 Joules
    joules_per_megaton = 4.184e15
    
    for i in prange(total_objects):
        # Convert km/s to m/s
        v_meters_per_sec = velocities_kms[i] * 1000.0
        
        # KE = 1/2 * m * v^2
        kinetic_energy_joules = 0.5 * masses_kg[i] * (v_meters_per_sec**2)
        
        yields_megatons[i] = kinetic_energy_joules / joules_per_megaton
        
    return yields_megatons

class PlanetaryDefenseNEOTracker:
    def __init__(self):
        self.city_killer_threshold_mt = 10.0 # 10 Megatons (Tunguska class)
        self.extinction_threshold_mt = 100000.0 # 100,000 Megatons (Chicxulub/Dinosaur class)

    def evaluate_orbital_threats(self, object_ids: List[str], masses_kg: List[float], velocities_kms: List[float], impact_probabilities: List[float]) -> dict:
        print(f"\n[PLANETARY DEFENSE] Sweeping deep-space radar telemetry for NEO impact trajectories...")
        start_time = time.time()
        
        m_arr = np.array(masses_kg, dtype=np.float64)
        v_arr = np.array(velocities_kms, dtype=np.float64)
        
        # Execute JIT Math
        impact_yields_mt = parallel_calculate_impact_energy(m_arr, v_arr)
        
        critical_threats = []
        for i in range(len(object_ids)):
            if impact_probabilities[i] > 0.1: # Greater than 10% chance of Earth intersection
                yield_mt = impact_yields_mt[i]
                
                classification = "MINOR_ATMOSPHERIC_BURNUP"
                if yield_mt >= self.extinction_threshold_mt:
                    classification = "GLOBAL_EXTINCTION_EVENT"
                elif yield_mt >= self.city_killer_threshold_mt:
                    classification = "CITY_KILLER_CATASTROPHIC"
                    
                if yield_mt >= self.city_killer_threshold_mt:
                    critical_threats.append({
                        "neo_designation": object_ids[i],
                        "impact_probability_pct": round(impact_probabilities[i] * 100.0, 2),
                        "kinetic_yield_megatons": round(yield_mt, 2),
                        "threat_class": classification,
                        "action": "INITIATE_KINETIC_DEFLECTION_PROTOCOL"
                    })

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "PLANETARY_ORBIT_SECURE" if not critical_threats else "DEFCON_1_KINETIC_THREAT_INBOUND"

        return {
            "defense_status": status,
            "neos_tracked": len(object_ids),
            "identified_threats": critical_threats,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    neo = PlanetaryDefenseNEOTracker()
    # Mocking 3 asteroids. Apophis-X is massive (5x10^10 kg) moving at 30km/s with a 95% impact chance.
    print("TESTING PLANETARY DEFENSE CORE:\n", neo.evaluate_orbital_threats(
        ["AST-2026-A", "AST-2026-B", "APOPHIS-X"], 
        [5000.0, 1.5e8, 5.0e10], 
        [15.0, 22.0, 30.0], 
        [0.001, 0.05, 0.95]
    ))
