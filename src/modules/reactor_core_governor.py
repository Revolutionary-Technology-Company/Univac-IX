# File Name: reactor_core_governor.py
# Location: /src/modules/
# Subsystem: Thermal Yield & SCRAM Autonomic Governor UPDATED
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit
from typing import Dict, Any

@njit(cache=True, fastmath=True)
def calculate_thermal_yield_mw(neutron_flux: float, coolant_flow_rate: float, core_temp_c: float) -> float:
    """Calculates instantaneous Megawatt thermal yield based on flux and coolant flow."""
    # Base thermal coefficient
    thermal_base = neutron_flux * 3.14159
    # Coolant suppression factor
    cooling_factor = 1.0 - math.exp(-coolant_flow_rate / 5000.0)
    
    yield_mw = (thermal_base * cooling_factor) + (core_temp_c * 0.05)
    return yield_mw

class ReactorCoreGovernor:
    def __init__(self, max_safe_temp_c: float = 850.0, scram_flux_threshold: float = 1.5e14):
        self.max_safe_temp = max_safe_temp_c
        self.scram_flux_threshold = scram_flux_threshold
        self.control_rod_insertion_pct = 0.0
        self.reactor_scrammed = False

    def evaluate_core_state(self, telemetry: dict) -> dict:
        if self.reactor_scrammed:
            return {"status": "SCRAM_LOCKED", "yield_mw": 0.0, "rod_insertion": 100.0}

        flux = telemetry.get("neutron_flux_hz", 0.0)
        temp_c = telemetry.get("core_temperature_c", 25.0)
        flow_rate = telemetry.get("coolant_flow_liters_sec", 100.0)

        # Execute JIT compiled physics
        current_yield = calculate_thermal_yield_mw(flux, flow_rate, temp_c)

        # Autonomic SCRAM Check
        if temp_c >= self.max_safe_temp or flux >= self.scram_flux_threshold:
            self.reactor_scrammed = True
            self.control_rod_insertion_pct = 100.0
            return {
                "status": "CRITICAL_SCRAM_ENGAGED",
                "yield_mw": current_yield,
                "rod_insertion": self.control_rod_insertion_pct,
                "message": f"Threshold breached. Temp: {temp_c}C | Flux: {flux:.2e}"
            }

        # Dynamic Rod Modulation
        if temp_c > (self.max_safe_temp * 0.85):
            self.control_rod_insertion_pct = min(100.0, self.control_rod_insertion_pct + 5.0)
        elif temp_c < (self.max_safe_temp * 0.60):
            self.control_rod_insertion_pct = max(0.0, self.control_rod_insertion_pct - 2.0)

        return {
            "status": "NOMINAL",
            "yield_mw": round(current_yield, 2),
            "rod_insertion": round(self.control_rod_insertion_pct, 2),
            "message": "Thermal output stable."
        }

if __name__ == "__main__":
    governor = ReactorCoreGovernor()
    test_telemetry = {"neutron_flux_hz": 1.2e13, "core_temperature_c": 740.0, "coolant_flow_liters_sec": 8500.0}
    print("TESTING REACTOR GOVERNOR:\n", governor.evaluate_core_state(test_telemetry))
