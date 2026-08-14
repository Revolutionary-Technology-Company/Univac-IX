import math
import numpy as np
from numba import njit

# =====================================================================
# CORE ENGINE: JIT-ACCELERATED TIME-SERIES FUEL BURN LOOP
# =====================================================================
@njit(fastmath=True, parallel=False)
def calculate_fuel_depletion_core(initial_fuel_gallons, efficiency_ratio_base, 
                                  speeds_array, durations_sec_array, total_intervals):
    # Calculates remaining fuel volumes, accounting for idle burn and non-linear scaling.
    remaining_fuel = initial_fuel_gallons
    total_consumed = 0.0
    
    for i in range(total_intervals):
        if remaining_fuel <= 0.0:
            remaining_fuel = 0.0
            break
            
        speed = speeds_array[i]
        duration_hours = durations_sec_array[i] / 3600.0
        
        if speed <= 0.0:
            interval_burn = 0.8 * duration_hours
        else:
            speed_modifier = 1.0 + (0.00015 * (speed ** 2.2))
            gallons_per_hour = (efficiency_ratio_base * speed) * speed_modifier
            interval_burn = gallons_per_hour * duration_hours
            
        total_consumed += interval_burn
        remaining_fuel -= interval_burn
        
    if remaining_fuel < 0.0:
        remaining_fuel = 0.0
        
    return remaining_fuel, total_consumed

# =====================================================================
# SERVER RUNTIME CORE: DIAGNOSTIC PAYLOAD PROCESSOR
# =====================================================================
def process_fuel_telemetry_ping(payload):
    # Parses and calculates multi-interval engine log payloads.
    try:
        config_block, log_block = payload.strip().split('|')
        config_fields = config_block.split(',')
        initial_fuel = float(config_fields[0])
        efficiency_base = float(config_fields[1])
        
        intervals = log_block.split(',')
        total_intervals = len(intervals)
        
        speeds = np.zeros(total_intervals, dtype=np.float64)
        durations = np.zeros(total_intervals, dtype=np.float64)
        
        for idx, entry in enumerate(intervals):
            speed_str, duration_str = entry.split(':')
            speeds[idx] = float(speed_str)
            durations[idx] = float(duration_str)
            
        fuel_left, fuel_burned = calculate_fuel_depletion_core(
            initial_fuel, efficiency_base, speeds, durations, total_intervals
        )
        
        burn_percentage = (fuel_burned / initial_fuel) * 100.0 if initial_fuel > 0 else 100.0
        reserve_flag = "CRITICAL_LOW_RESERVE" if (fuel_left / initial_fuel) < 0.15 else "NOMINAL"
        
        return {
            "STATUS": "NOMINAL_NODE_12",
            "INITIAL_CAPACITY": f"{initial_fuel:.2f} GAL",
            "TOTAL_VOLUME_BURNED": f"{fuel_burned:.4f} GAL",
            "REMAINING_VOLUME": f"{fuel_left:.4f} GAL",
            "BURN_RATIO_METRIC": f"{burn_percentage:.1f}%",
            "RESERVE_THROTTLE_STATUS": reserve_flag
        }
    except Exception as e:
        return {"STATUS": "CRITICAL_FUEL_ANALYTICS_BREAKDOWN", "ERROR": str(e)}

if __name__ == "__main__":
    mock_payload = "150.0,0.015|35.0:1200,0.0:300,70.0:2700"
    analytics_matrix = process_fuel_telemetry_ping(mock_payload)
