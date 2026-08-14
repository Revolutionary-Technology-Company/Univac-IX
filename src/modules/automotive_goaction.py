import math
import time
import numpy as np
from numba import njit

# =====================================================================
# CORE ENGINE: JIT-ACCELERATED TERRESTRIAL WHEEL-KINEMATICS CORE (NODE 11)
# =====================================================================
@njit(fastmath=True, parallel=False)
def project_automotive_core(wheel_rpm, wheel_diameter_inches, road_grade_pct, 
                            surface_friction_mu, drive_efficiency_pct, delta_t_sec):
    """
    Calculates terrestrial velocity, wheel slip losses, true ground speed,
    and vertical elevation change caused by hill climbs or declines.
    """
    # 1. Calculate Theoretical Speed (Inches per Minute)
    circumference_inches = math.pi * wheel_diameter_inches
    theoretical_inches_per_min = wheel_rpm * circumference_inches
    
    # Convert to standard feet per second (fps)
    theoretical_fps = (theoretical_inches_per_min / 12.0) / 60.0
    
    # 2. Account for Wheel Slip and Drivetrain Mechanical Loss
    # High grade percentage or slick roads (low friction mu) scales down power delivery
    normalized_friction = min(surface_friction_mu, 1.0)
    grade_drag_factor = min(abs(road_grade_pct) / 100.0, 0.5)
    
    # Slip equation modeling surface adhesion loss
    slip_coefficient = max(0.02, grade_drag_factor * (1.1 - normalized_friction))
    effective_efficiency = (drive_efficiency_pct / 100.0) * (1.0 - slip_coefficient)
    
    # 3. Resolve True Ground Speed (FPS and MPH)
    true_ground_speed_fps = theoretical_fps * effective_efficiency
    true_ground_speed_mph = true_ground_speed_fps * 0.681818
    
    # 4. Extract Vector Components based on Road Grade Angle
    # Grade % = tan(theta) * 100 -> find actual angle
    grade_angle_rad = math.atan(road_grade_pct / 100.0)
    
    linear_distance_feet = true_ground_speed_fps * delta_t_sec
    
    # Separate forward ground travel vs vertical elevation climb/descent
    forward_travel_feet = linear_distance_feet * math.cos(grade_angle_rad)
    elevation_change_feet = linear_distance_feet * math.sin(grade_angle_rad)
    
    return true_ground_speed_mph, forward_travel_feet, elevation_change_feet


# =====================================================================
# SERVER RUNTIME CORE: TERRESTRIAL PAYLOAD PROCESSOR
# =====================================================================
def process_automotive_trunk_ping(payload):
    """
    Parses incoming high-throughput terrestrial automotive payloads.
    Format Expected: "WHEEL_RPM,WHEEL_DIAMETER,ROAD_GRADE,FRICTION_MU,EFFICIENCY,DURATION"
    """
    try:
        raw_fields = payload.strip().split(',')
        wheel_rpm = float(raw_fields[0])
        wheel_diameter = float(raw_fields[1])
        road_grade = float(raw_fields[2])
        friction_mu = float(raw_fields[3])
        efficiency = float(raw_fields[4])
        duration_sec = float(raw_fields[5])
        
        # Execute JIT physics matrix
        mph, forward_ft, elevation_ft = project_automotive_core(
            wheel_rpm, wheel_diameter, road_grade, friction_mu, efficiency, duration_sec
        )
        
        return {
            "STATUS": "NOMINAL_NODE_11",
            "GROUND_SPEED": f"{mph:.2f} mph",
            "FORWARD_PROGRESSION": f"{forward_ft:.2f} ft",
            "VERTICAL_ELEVATION_DELTA": f"{elevation_ft:.2f} ft"
        }
    except Exception as e:
        return {"STATUS": "CRITICAL_AUTO_BREAKDOWN", "ERROR": str(e)}


# =====================================================================
# CORE GATEWAY: THREE-WAY PROTOCOL DISPATCHER
# =====================================================================
# Mock imports of prior systems for local orchestration testing
try:
    from univac_node9 import process_univac_trunk_ping
    from univac_node10 import process_elevation_trunk_ping
except ImportError:
    def process_univac_trunk_ping(p): return {"STATUS": "NOMINAL_NODE_9", "DATA": "Maritime Success"}
    def process_elevation_trunk_ping(p): return {"STATUS": "NOMINAL_NODE_10", "DATA": "Aviation Success"}

def dispatch_univac_request(request_headers, raw_payload):
    """
    Inspects incoming tactical headers. Handles 'vessel', 'aircraft', 
    and 'automotive' asset parameters to branch traffic routes.
    """
    normalized_headers = {k.lower(): v.lower() for k, v in request_headers.items()}
    asset_type = normalized_headers.get("asset-type") or normalized_headers.get("header")
    
    # 1. Route Node 9: Maritime Platforms
    if asset_type == "vessel":
        print("[GATEWAY]: Dispatched to Node 9 (Maritime Kinematics)...")
        results = process_univac_trunk_ping(raw_payload)
        results["DISPATCH_CONTEXT"] = "MARITIME_NODE_9"
        return results
        
    # 2. Route Node 10: Aero-Kinematic Platforms
    elif asset_type == "aircraft":
        print("[GATEWAY]: Dispatched to Node 10 (Aero-Kinematics)...")
        results = process_elevation_trunk_ping(raw_payload)
        results["DISPATCH_CONTEXT"] = "AERO_NODE_10"
        return results
        
    # 3. Route Node 11: Terrestrial Wheeled Platforms
    elif asset_type == "automotive":
        print("[GATEWAY]: Dispatched to Node 11 (Terrestrial Kinematics)...")
        # Expects: "WHEEL_RPM,WHEEL_DIAMETER,ROAD_GRADE,FRICTION_MU,EFFICIENCY,DURATION"
        results = process_automotive_trunk_ping(raw_payload)
        results["DISPATCH_CONTEXT"] = "TERRESTRIAL_NODE_11"
        return results
        
    # 4. Error Catchment
    else:
        print(f"[GATEWAY ALERT]: Unmapped asset categorization header: '{asset_type}'")
        return {
            "STATUS": "CRITICAL_ROUTING_MISMATCH",
            "ERROR": "Invalid classification layer. Inbound line connection dropped."
        }


# =====================================================================
# RUNTIME INTEGRATION TEST
# =====================================================================
if __name__ == "__main__":
    print("UNIVAC CENTRAL ROUTER V2 -- Processing Asset Protocols...\n")
    
    # Test Inbound Automotive Trunk
    car_headers = {"Asset-Type": "automotive"}
    # Payload: 900 RPM, 26-inch Tires, 6.0% Road Grade, 0.85 Friction (dry asphalt), 92% Drivetrain, 30 Seconds
    car_payload = "900.0,26.0,6.0,0.85,92.0,30.0"
    
    car_response = dispatch_univac_request(car_headers, car_payload)
    import json
    print(f"Automotive Output: {json.dumps(car_response, indent=2)}")
