# File Name: strategic_fuel_consumption_matrix.py
# Location: /src/modules/
# Subsystem: Heavy Engine Logistics & Fuel Consumption Core
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_fuel_burn(engine_loads_pct: np.ndarray, power_ratings_kw: np.ndarray, base_bsfc_g_kwh: float) -> np.ndarray:
    """Calculates instantaneous fuel burn rates (Liters per Hour) across an array of heavy generators."""
    total_engines = engine_loads_pct.shape[0]
    burn_rates_lph = np.zeros(total_engines, dtype=np.float64)
    diesel_density_kg_l = 0.85 # Standard heavy diesel density
    
    for i in prange(total_engines):
        load_factor = engine_loads_pct[i] / 100.0
        active_power_kw = power_ratings_kw[i] * load_factor
        
        # BSFC worsens at low loads (simplified curve adjustment)
        dynamic_bsfc = base_bsfc_g_kwh
        if load_factor < 0.5:
            dynamic_bsfc = base_bsfc_g_kwh * (1.0 + (0.5 - load_factor))
            
        # Grams per hour -> Kilograms per hour -> Liters per hour
        fuel_kg_h = (active_power_kw * dynamic_bsfc) / 1000.0
        burn_rates_lph[i] = fuel_kg_h / diesel_density_kg_l
        
    return burn_rates_lph

class StrategicFuelLogistics:
    def __init__(self):
        self.bunker_capacity_liters = 500000.0 # 500,000 Liter strategic reserve

    def evaluate_fleet_consumption(self, current_reserves_liters: float, loads_pct: List[float], capacities_kw: List[float]) -> dict:
        print(f"\n[LOGISTICS] Calculating thermodynamic fuel burn across heavy generation matrix...")
        start_time = time.time()
        
        load_arr = np.array(loads_pct, dtype=np.float64)
        kw_arr = np.array(capacities_kw, dtype=np.float64)
        
        # Base BSFC of 210 g/kWh for large marine/industrial diesels
        burn_rates_lph = parallel_calculate_fuel_burn(load_arr, kw_arr, 210.0)
        
        total_burn_rate_lph = np.sum(burn_rates_lph)
        
        time_to_empty_hours = 0.0
        if total_burn_rate_lph > 0.0:
            time_to_empty_hours = current_reserves_liters / total_burn_rate_lph

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "LOGISTICS_NOMINAL"
        if time_to_empty_hours < 72.0: # Less than 3 days of fuel remaining
            status = "CRITICAL_FUEL_SHORTAGE"

        return {
            "logistics_status": status,
            "total_burn_rate_lph": round(total_burn_rate_lph, 2),
            "reserve_fuel_remaining_liters": current_reserves_liters,
            "projected_time_to_empty_hours": round(time_to_empty_hours, 2),
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    fuel = StrategicFuelLogistics()
    # Mocking 4 massive 2.5 MW municipal generators running at various loads
    print("TESTING FUEL LOGISTICS:\n", fuel.evaluate_fleet_consumption(150000.0, [95.0, 80.0, 40.0, 100.0], [2500.0, 2500.0, 2500.0, 2500.0]))
