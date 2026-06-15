# File Name: municipal_infrastructure_balancing.py
# Location: /src/modules/
# Subsystem: Civil Defense & Municipal Infrastructure Balancer
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit
from typing import Dict, Any

@njit(cache=True, fastmath=True)
def calculate_municipal_deficits(population: int, power_supply_mw: float, water_supply_m3: float) -> tuple:
    """Calculates exact deficits for survival parameters: Power (MW), Water (m^3), and daily waste generation."""
    # Survival baselines per capita
    kw_per_person = 1.2 # Minimal civil defense power draw
    water_m3_per_person = 0.15 # Minimal survival water
    waste_kg_per_person = 1.8 # Daily solid waste generation
    
    total_power_demand_mw = (population * kw_per_person) / 1000.0
    total_water_demand_m3 = population * water_m3_per_person
    daily_waste_kg = population * waste_kg_per_person
    
    power_deficit_mw = max(0.0, total_power_demand_mw - power_supply_mw)
    water_deficit_m3 = max(0.0, total_water_demand_m3 - water_supply_m3)
    
    return power_deficit_mw, water_deficit_m3, daily_waste_kg

class MunicipalInfrastructureBalancer:
    def __init__(self):
        self.active_load_shedding = False

    def evaluate_city_infrastructure(self, population: int, grid_supply_mw: float, reservoir_m3: float, unmanaged_waste_tons: float) -> dict:
        print(f"\n[CIVIL DEFENSE] Balancing municipal survival infrastructure grids...")
        start_time = time.time()
        
        # Execute JIT Math
        p_deficit_mw, w_deficit_m3, daily_waste_kg = calculate_municipal_deficits(population, grid_supply_mw, reservoir_m3)
        
        alerts = []
        if p_deficit_mw > 0:
            self.active_load_shedding = True
            alerts.append(f"ROLLING_BLACKOUTS_REQUIRED: {-round(p_deficit_mw, 2)} MW")
            
        if w_deficit_m3 > 0:
            alerts.append("CRITICAL_WATER_RATIONING_ACTIVE")
            
        # Waste/Garbage decay and bio-hazard threshold (If more than 500 tons accumulate, epidemic risk rises)
        if unmanaged_waste_tons > 500.0:
            alerts.append("EPIDEMIC_BIOHAZARD_WARNING_WASTE_ACCUMULATION")

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "CRITICAL_INFRASTRUCTURE_FAILURE" if alerts else "MUNICIPALITY_STABLE"

        return {
            "civil_defense_status": status,
            "population_tracked": population,
            "daily_solid_waste_generation_tons": round(daily_waste_kg / 1000.0, 2),
            "power_deficit_mw": round(p_deficit_mw, 2),
            "active_alerts": alerts,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    city = MunicipalInfrastructureBalancer()
    # Mocking a crisis: 150,000 people, limited 100 MW power grid, safe water, but 600 tons of uncollected garbage.
    print("TESTING MUNICIPAL BALANCER:\n", city.evaluate_city_infrastructure(150000, 100.0, 50000.0, 650.0))
