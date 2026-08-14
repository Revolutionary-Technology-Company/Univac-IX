import math
import numpy as np
from numba import njit

# =====================================================================
# CORE ENGINE: JIT-ACCELERATED CLIMB/DESCENT AND WIND PERFORMANCE CORE
# =====================================================================
@njit(fastmath=True, parallel=False)
def calculate_elevation_delta_core(initial_alt_ft, motor_power_pct, pitch_angle_deg, 
                                   heading_deg, wind_speed_kts, wind_dir_deg, delta_t_sec):
    """
    Calculates altitude progression using aerodynamic flight control dynamics,
    engine power-to-climb performance coefficients, and vertical wind vectors.
    """
    # 1. Standard Atmospheric Density Approximation (Troposphere lapse rate)
    # Used to calculate true airspeed and engine efficiency falloff at altitude
    if initial_alt_ft < 36089.0:
        temp_k = 288.15 - (0.0019812 * initial_alt_ft)
        pressure_pa = 101325.0 * (temp_k / 288.15) ** 5.25588
    else:
        # Lower Stratosphere boundary clamp
        temp_k = 216.65
        pressure_pa = 22632.1 * math.exp(-0.000048063 * (initial_alt_ft - 36089.0))
    
    air_density = pressure_pa / (287.05 * temp_k)
    standard_sea_level_density = 1.225
    density_ratio = air_density / standard_sea_level_density
    
    # 2. Resolve True Airspeed (TAS) from Engine Power and Density
    # Engine efficiency decays at higher altitudes due to lower air density
    base_thrust_kts = 120.0 * (motor_power_pct / 100.0)
    true_airspeed_kts = base_thrust_kts / math.sqrt(max(density_ratio, 0.1))
    true_airspeed_fps = true_airspeed_kts * 1.68781
    
    # 3. Resolve Wind Vectors (Headwind/Tailwind Component)
    heading_rad = math.radians(heading_deg)
    wind_rad = math.radians(wind_dir_deg)
    angle_diff = heading_rad - wind_rad
    
    headwind_kts = wind_speed_kts * math.cos(angle_diff)
    ground_speed_fps = (true_airspeed_kts - headwind_kts) * 1.68781
    
    # 4. Compute Vertical Kinematics via Flight Control Surface Data
    # Pitch angle determines vertical vs horizontal breakdown of velocity
    pitch_rad = math.radians(pitch_angle_deg)
    climb_rate_fps = true_airspeed_fps * math.sin(pitch_rad)
    
    # Simulate atmospheric vertical updraft/downdraft relative to wind shear
    # Higher wind speeds over rough typography induce localized vertical waves
    vertical_wind_fps = (wind_speed_kts * 0.05) * math.sin(angle_diff)
    
    # 5. Integrate Delta Change over Time Session
    total_climb_rate = climb_rate_fps + vertical_wind_fps
    altitude_delta = total_climb_rate * delta_t_sec
    final_elevation = initial_alt_ft + altitude_delta
    
    return final_elevation, total_climb_rate, ground_speed_fps

# =====================================================================
# SERVER RUNTIME CORE: INCOMING TELEMETRY PROCESSOR
# =====================================================================
def process_elevation_trunk_ping(payload):
    """
    Parses incoming high-throughput aero-telemetry payloads.
    Format Expected: "INITIAL_ALT,MOTOR_POWER,PITCH_ANGLE,HEADING,WIND_SPEED,WIND_DIR,DURATION"
    """
    try:
        # Unpack raw pipeline string fields
        raw_fields = payload.strip().split(',')
        initial_alt = float(raw_fields[0])
        motor_power = float(raw_fields[1])
        pitch_angle = float(raw_fields[2])
        heading = float(raw_fields[3]) % 360.0
        wind_speed = float(raw_fields[4])
        wind_dir = float(raw_fields[5]) % 360.0
        duration_sec = float(raw_fields[6])
        
        # Calculate kinematics using high-performance physics pipeline
        final_alt, vertical_rate_fps, ground_speed_fps = calculate_elevation_delta_core(
            initial_alt, motor_power, pitch_angle, heading, wind_speed, wind_dir, duration_sec
        )
        
        return {
            "STATUS": "NOMINAL_NODE_10",
            "ATMOSPHERIC_FRAME": "TROPOSPHERIC_LAPSE_LAPSER",
            "COMPUTED_GROUND_SPEED": f"{ground_speed_fps / 1.68781:.2f} kts",
            "VERTICAL_VELOCITY": f"{vertical_rate_fps * 60:.1f} feet/minute",
            "TARGET_ELEVATION": f"{final_alt:.4f} ft"
        }
        
    except Exception as e:
        return {"STATUS": "CRITICAL_AERO_BREAKDOWN", "ERROR": str(e)}

# =====================================================================
# RUNTIME VERIFICATION HARNESS
# =====================================================================
if __name__ == "__main__":
    # Payload format: Initial Alt (ft), Engine Power (%), Pitch Angle (°), Heading (°), Wind Speed (kts), Wind Dir (°), Time (s)
    incoming_payload = "5000.0,85.0,6.5,180.0,25.0,210.0,10.0"
    
    print("UNIVAC IX -- Initializing Node 10 Aero-Kinematic Router...")
    elevation_matrix = process_elevation_trunk_ping(incoming_payload)
    
    for metric, value in elevation_matrix.items():
        print(f"[{metric}]: {value}")
