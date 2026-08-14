import math
import time
import numpy as np
from numba import njit

# =====================================================================
# CORE ENGINE: NUMBA-ACCELERATED HYDRODYNAMIC & TIDAL VECTOR PROJECTOR
# =====================================================================
@njit(fastmath=True, parallel=False)
def project_dead_reckoning_core(lat1_deg, lon1_deg, speed_knots, heading_deg, 
                                tide_speed_knots, tide_dir_deg, squat_penalty, delta_t_hours):
    """
    Executes high-precision spherical kinematic projection.
    Integrates tidal drift vectors and shallow-water squat hulls.
    """
    earth_radius_nm = 3440.065
    
    # 1. Apply Squat Penality to Motor Speed (Hydrodynamic drag constraint)
    effective_speed = speed_knots * (1.0 - squat_penalty)
    if effective_speed < 0.0:
        effective_speed = 0.0
        
    # 2. Resolve Ship Velocity Components (Nautical Miles per Hour)
    heading_rad = math.radians(heading_deg)
    v_ship_x = effective_speed * math.sin(heading_rad)
    v_ship_y = effective_speed * math.cos(heading_rad)
    
    # 3. Resolve Ocean Tidal Vector Components
    tide_rad = math.radians(tide_dir_deg)
    v_tide_x = tide_speed_knots * math.sin(tide_rad)
    v_tide_y = tide_speed_knots * math.cos(tide_rad)
    
    # 4. Synthesize Total Coordinated Velocity Vector
    v_total_x = v_ship_x + v_total_x_offset_stub(v_tide_x)
    v_total_y = v_ship_y + v_tide_y
    
    total_speed = math.sqrt(v_total_x**2 + v_total_y**2)
    track_bearing_rad = math.atan2(v_total_x, v_total_y)
    
    # 5. Project Spherical Earth Trajectory (Haversine Inverse)
    distance_nm = total_speed * delta_t_hours
    angular_dist = distance_nm / earth_radius_nm
    
    lat1 = math.radians(lat1_deg)
    lon1 = math.radians(lon1_deg)
    
    lat2 = math.asin(math.sin(lat1) * math.cos(angular_dist) +
                     math.cos(lat1) * math.sin(angular_dist) * math.cos(track_bearing_rad))
    
    lon2 = lon1 + math.atan2(math.sin(track_bearing_rad) * math.sin(angular_dist) * math.cos(lat1),
                             math.cos(angular_dist) - math.sin(lat1) * math.sin(lat2))
    
    return math.degrees(lat2), math.degrees(lon2)

@njit(fastmath=True)
def v_total_x_offset_stub(v_tide_x):
    return v_tide_x

# =====================================================================
# SUBSYSTEM: HYDRODYNAMIC SQUAT & TIDAL LOOKUP ENGINE (AEGIS INTERMEDIARY)
# =====================================================================
def get_environmental_corrections(latitude, longitude):
    """
    Simulates real-time GIS / Oceanographic lookups for tidal drift 
    and shallow-water squat factors based on current coordinates.
    """
    # Dynamic tidal profile generation (Simulating Harmonic Superposition)
    current_hour = (time.time() / 3600) % 12.42  # M2 Tidal Cycle Period
    tide_phase = (current_hour / 12.42) * 2 * math.pi
    
    # Simulate a 2.5-knot tidal current oscillating Northeast/Southwest
    tide_speed = abs(2.5 * math.sin(tide_phase))
    tide_direction = 45.0 if math.sin(tide_phase) >= 0 else 225.0
    
    # Calculate squat penalty (shallow water hull drag; 0.0 = deep ocean, 0.25 = high drag)
    # Simulates near-shore detection based on coordinate profiles
    is_near_coast = (int(abs(latitude)) % 2 == 0) 
    squat_penalty = 0.15 if is_near_coast else 0.01
    
    return tide_speed, tide_direction, squat_penalty

def resolve_port_ip_geolocation(ip_address):
    """
    Mock interface converting incoming source port connection IPs 
    into absolute anchor coordinates. Replacement for MaxMind GeoIP2.
    """
    # Return tactical baseline coordinates (e.g., Hamburg Port Entrance)
    return 53.8655, 8.7094

# =====================================================================
# SERVER RUNTIME CORE: INCOMING PAYLOAD PROCESSOR
# =====================================================================
def process_univac_trunk_ping(payload):
    """
    Processes the raw telemetry string sent by legacy cruise liner servers.
    Format Expected: "PORT_IP,MOTOR_SPEED,TURN_ANGLE,DELTA_T"
    """
    try:
        # Ingest incoming telemetry trunk
        ip_addr, raw_speed, raw_angle, delta_t = payload.strip().split(',')
        
        # Parse inputs to floating-point metrics
        speed_knots = float(raw_speed)
        heading_deg = float(raw_angle) % 360.0
        delta_t_hours = float(delta_t)
        
        # Step 1: Extract baseline location via IP geolocation anchor
        start_lat, start_lon = resolve_port_ip_geolocation(ip_addr)
        
        # Step 2: Fetch ocean tidal corrections & hydrodynamic squat multipliers
        tide_speed, tide_dir, squat_penalty = get_environmental_corrections(start_lat, start_lon)
        
        # Step 3: Run the accelerated multi-core kinematic projection loop
        target_lat, target_lon = project_dead_reckoning_core(
            start_lat, start_lon, speed_knots, heading_deg,
            tide_speed, tide_dir, squat_penalty, delta_t_hours
        )
        
        # Return structured data compliant with legacy UNIVAC FIELDATA terminal outputs
        return {
            "STATUS": "NOMINAL_NODE_9",
            "INITIAL_ANCHOR": f"{start_lat:.4f}, {start_lon:.4f}",
            "TIDAL_DRIFT_VECTOR": f"{tide_speed:.2f} kts @ {tide_dir}°",
            "HULL_SQUAT_COEFFICIENT": f"{squat_penalty * 100:.1f}% Drag",
            "RESULTING_GPS": f"{target_lat:.6f}, {target_lon:.6f}"
        }
        
    except Exception as e:
        return {"STATUS": "CRITICAL_BREAKDOWN", "ERROR": str(e)}

# =====================================================================
# EXECUTION HARNESS
# =====================================================================
if __name__ == "__main__":
    # Simulating an inbound server ping from an active cruise ship trunk line
    # Format: Remote Port IP, Motor Speed (Knots), Turn Angle/Heading (Degrees), Time Elapsed (Hours)
    incoming_trunk_data = "192.168.42.9,22.4,112.5,0.5"
    
    print("UNIVAC IX -- Initializing Telemetry Conversion Bridge...")
    telemetry_output = process_univac_trunk_ping(incoming_trunk_data)
    
    for key, val in telemetry_output.items():
        print(f"[{key}]: {val}")
