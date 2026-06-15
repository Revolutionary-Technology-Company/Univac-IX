# File Name: cryogenic_lng_carrier_matrix.py
# Location: /src/modules/
# Subsystem: Seaborne Cryogenic Logistics & Boil-Off Gas (BOG) Core
# Copyright (c) 2026 Revolutionary Technology

import time
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_lng_boil_off(ambient_temps_k: np.ndarray, tank_areas_m2: np.ndarray, u_value_w_m2k: float) -> np.ndarray:
    """Calculates Boil-Off Gas generation rates (kg/h) for cryogenic LNG supertankers."""
    total_ships = ambient_temps_k.shape[0]
    bog_kg_h = np.zeros(total_ships, dtype=np.float64)
    
    lng_temp_k = 111.15 # -162 Celsius (boiling point of Methane)
    latent_heat_vap_j_kg = 510000.0 # Approx Latent Heat of Vaporization for LNG (J/kg)
    
    for i in prange(total_ships):
        # Calculate temperature differential driving heat into the tank
        delta_t = max(0.0, ambient_temps_k[i] - lng_temp_k)
        
        # Heat Ingress (Watts) = U-Value * Area * Delta_T
        heat_ingress_w = u_value_w_m2k * tank_areas_m2[i] * delta_t
        
        # Boil-off rate (kg/s) = Heat (J/s) / Latent Heat (J/kg)
        boil_off_kg_s = heat_ingress_w / latent_heat_vap_j_kg
        
        # Convert to kg per hour
        bog_kg_h[i] = boil_off_kg_s * 3600.0
        
    return bog_kg_h

class CryogenicLNGLogisticsMatrix:
    def __init__(self):
        # Standard GTT NO96 membrane containment U-value
        self.insulation_u_value = 0.13 
        # Max BOG the ship's dual-fuel diesel engines can consume for propulsion
        self.max_engine_consumption_kg_h = 3500.0 

    def evaluate_fleet_thermodynamics(self, vessel_ids: List[str], ambient_temps_c: List[float], tank_surface_areas_m2: List[float]) -> dict:
        print(f"\n[CRYOGENICS] Calculating global fleet Boil-Off Gas (BOG) thermodynamics...")
        start_time = time.time()
        
        # Convert Celsius to Kelvin
        temps_k_arr = np.array(ambient_temps_c, dtype=np.float64) + 273.15
        area_arr = np.array(tank_surface_areas_m2, dtype=np.float64)
        
        # Execute JIT Math
        boil_off_rates = parallel_calculate_lng_boil_off(temps_k_arr, area_arr, self.insulation_u_value)
        
        venting_alerts = []
        for i in range(len(vessel_ids)):
            bog = boil_off_rates[i]
            
            # If expanding gas exceeds what the ship's engines can burn, tank pressure rises dangerously
            if bog > self.max_engine_consumption_kg_h:
                venting_alerts.append({
                    "vessel_id": vessel_ids[i],
                    "excess_bog_kg_h": round(bog - self.max_engine_consumption_kg_h, 2),
                    "action": "OPEN_GAS_COMBUSTION_UNIT_VENT_TO_FLARE"
                })

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "EXCESS_BOG_FLARING_REQUIRED" if venting_alerts else "FLEET_THERMODYNAMICS_STABLE"

        return {
            "fleet_status": status,
            "vessels_monitored": len(vessel_ids),
            "total_fleet_bog_generation_kg_h": round(np.sum(boil_off_rates), 2),
            "critical_pressure_interventions": venting_alerts,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    lng = CryogenicLNGLogisticsMatrix()
    # Mocking massive Q-Max LNG carriers crossing the equator. Ship 3 hits extreme 45C ambient heat.
    print("TESTING CRYOGENIC LOGISTICS:\n", lng.evaluate_fleet_thermodynamics(
        ["ARCTIC-DISCOVERER", "Q-MAX-PIONEER", "EQUATORIAL-STAR"], 
        [15.0, 25.0, 45.0], 
        [18000.0, 22000.0, 22000.0]
    ))
