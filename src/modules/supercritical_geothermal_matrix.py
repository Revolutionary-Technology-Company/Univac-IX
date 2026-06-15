# File Name: supercritical_geothermal_matrix.py
# Location: /src/modules/
# Subsystem: Supercritical Magma Borehole Thermodynamic Matrix
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_supercritical_yield(temps_c: np.ndarray, pressures_mpa: np.ndarray, flow_rates_kg_s: np.ndarray) -> np.ndarray:
    """Calculates the thermal Megawatt yield of supercritical geothermal fluid."""
    total_wells = temps_c.shape[0]
    yields_mw = np.zeros(total_wells, dtype=np.float64)
    
    # Critical point of water: 374 Celsius, 22.1 MPa
    crit_temp = 374.0
    crit_pressure = 22.1
    
    for i in prange(total_wells):
        t = temps_c[i]
        p = pressures_mpa[i]
        
        if t >= crit_temp and p >= crit_pressure:
            # Enthalpy of supercritical water is massive (~3000+ kJ/kg)
            # Proxy calculation for specific enthalpy (kJ/kg) based on temp
            enthalpy_kj_kg = 2000.0 + (t - crit_temp) * 5.0 
            
            # Power (MW) = Flow rate (kg/s) * Enthalpy (kJ/kg) / 1000
            yields_mw[i] = (flow_rates_kg_s[i] * enthalpy_kj_kg) / 1000.0
        else:
            # Sub-critical conventional geothermal yield (much lower efficiency)
            yields_mw[i] = (flow_rates_kg_s[i] * 800.0) / 1000.0
            
    return yields_mw

class SupercriticalGeothermalMatrix:
    def __init__(self):
        self.casing_melt_limit_c = 600.0 # Temperature at which standard titanium/steel alloy casings fail

    def evaluate_deep_boreholes(self, well_ids: List[str], depths_km: List[float], bottom_temps_c: List[float], pressures_mpa: List[float], flow_rates_kg_s: List[float]) -> dict:
        print(f"\n[ENERGY INFRASTRUCTURE] Evaluating deep-mantle supercritical thermodynamics...")
        start_time = time.time()
        
        t_arr = np.array(bottom_temps_c, dtype=np.float64)
        p_arr = np.array(pressures_mpa, dtype=np.float64)
        flow_arr = np.array(flow_rates_kg_s, dtype=np.float64)
        
        # Execute JIT Math
        power_yields_mw = parallel_calculate_supercritical_yield(t_arr, p_arr, flow_arr)
        
        total_grid_yield_mw = 0.0
        critical_faults = []
        
        for i in range(len(well_ids)):
            if bottom_temps_c[i] >= self.casing_melt_limit_c:
                critical_faults.append({
                    "well_id": well_ids[i],
                    "temperature_c": bottom_temps_c[i],
                    "action": "INITIATE_EMERGENCY_QUENCH_PREVENT_CASING_MELTDOWN"
                })
            else:
                total_grid_yield_mw += power_yields_mw[i]

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "GRID_POWER_NOMINAL" if not critical_faults else "GEOTHERMAL_CASING_FAILURE_IMMINENT"

        return {
            "facility_status": status,
            "wells_monitored": len(well_ids),
            "total_supercritical_yield_mw": round(total_grid_yield_mw, 2),
            "structural_faults": critical_faults,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    geo = SupercriticalGeothermalMatrix()
    # Mocking 3 deep boreholes. Well 1 is standard. Well 2 is Supercritical (Massive Power). Well 3 is melting.
    print("TESTING SUPERCRITICAL GEOTHERMAL MATRIX:\n", geo.evaluate_deep_boreholes(
        ["KRAFLA-01", "ICELAND-DEEP-02", "YELLOWSTONE-03"], 
        [2.5, 4.8, 5.5], 
        [250.0, 450.0, 650.0], # Temps (C)
        [15.0, 25.0, 30.0],    # Pressures (MPa)
        [50.0, 50.0, 50.0]     # Flow Rates (kg/s)
    ))
