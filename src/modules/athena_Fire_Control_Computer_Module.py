python

"""
Module: athena_fire_control_computer.py
Platform: Univac-IX Fire Control System (FCS)
Implementation: American Ballistic Kernel / Aegis Integration Engine
Description: Parsers Aegis tracking telemetry, estimates target lead vectors,
             and applies a high-fidelity sea-state clutter filter to reject
             surface noise, wave reflections, and storm anomalies.
"""

import math
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ATHENA-SEA-FILTER] - %(levelname)s - %(message)s')

class AthenaFireControlComputer:
    def __init__(self, battery_id: str, latitude: float, longitude: float, altitude: float):
        """
        Initializes the Tactical Naval Gunfire Control Subsystem with integrated Clutter Filtering.
        """
        self.battery_id = battery_id
        self.position = {'lat': latitude, 'lon': longitude, 'alt': altitude}
        
        # Ballistic Kinematics Constants
        self.GRAVITY = 9.80665
        self.STANDARD_MUZZLE_VELOCITY = 827.0  # Hypervelocity Extended Range Standard (m/s)
        
        # Kalman Filter State Variables for Sea-State Clutter Rejection
        self.kalman_state = None  # [lat, lon, v_lat, v_lon]
        self.kalman_covariance = None
        self.process_noise = 0.05  # Operational plant variance
        self.measurement_noise_base = 0.1  # Dynamic floor scaled by Sea State
        
        logging.info(f"Athena FCS initialized on battery {battery_id}. Sea-State Clutter Optimization Engine Online.")

    def _haversine_distance_and_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> tuple:
        """
        Computes accurate range (meters) and bearing (degrees) between two geodetic pairs.
        """
        R = 6371000.0
        r_lat1, r_lon1 = math.radians(lat1), math.radians(lon1)
        r_lat2, r_lon2 = math.radians(lat2), math.radians(lon2)
        
        dlat = r_lat2 - r_lat1
        dlon = r_lon2 - r_lon1
        
        a = math.sin(dlat / 2)**2 + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(dlon / 2)**2
        distance = R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
        
        y = math.sin(dlon) * math.cos(r_lat2)
        x = math.cos(r_lat1) * math.sin(r_lat2) - math.sin(r_lat1) * math.cos(r_lat2) * math.cos(dlon)
        bearing = (math.degrees(math.atan2(y, x)) + 360) % 360
        
        return distance, bearing

    def apply_sea_state_clutter_filter(self, raw_radar_returns: list, sea_state: int) -> list:
        """
        Digital Sea-State Radar Clutter Filter.
        Accepts raw, noisy spatial returns from AN/SPY array feed.
        Applies a rolling statistical anomaly threshold based on Douglas Sea Scale heights.
        Filters out wave crests and spray spikes to isolate genuine metallic hull structures.
        """
        if not raw_radar_returns:
            return []
            
        # Define maximum expected structural variance (wave height thresholds in meters per Sea State)
        # Sea State 3 = Slight waves (1.25m), Sea State 5 = Rough waves (4m), Sea State 6 = Very Rough (6m)
        clutter_wave_thresholds = {
            0: 0.1, 1: 0.5, 2: 1.0, 3: 1.5, 4: 2.5, 5: 4.0, 6: 6.0, 7: 9.0
        }
        max_wave_height = clutter_wave_thresholds.get(sea_state, 4.0)
        
        # Dynamic Doppler Speed Floor: Waves rarely match sustained velocity vectors over time
        # Filter out radar components whose micro-Doppler signals match common wave velocities (under 5.5 m/s)
        doppler_speed_floor_mps = 5.5 if sea_state >= 4 else 2.0
        
        valid_structural_points = []
        
        # Calculate spatial average center mass (centroid tracking baseline)
        avg_lat = sum(p['lat'] for p in raw_radar_returns) / len(raw_radar_returns)
        avg_lon = sum(p['lon'] for p in raw_radar_returns) / len(raw_radar_returns)
        
        # Standard deviation pass: Filter raw returns to reject sea spray reflections
        lat_variance = sum((p['lat'] - avg_lat)**2 for p in raw_radar_returns) / len(raw_radar_returns)
        lon_variance = sum((p['lon'] - avg_lon)**2 for p in raw_radar_returns) / len(raw_radar_returns)
        
        lat_std = math.sqrt(lat_variance) if lat_variance > 0 else 0.0001
        lon_std = math.sqrt(lon_variance) if lon_variance > 0 else 0.0001

        for node in raw_radar_returns:
            # 1. Z-Score Clutter Trim: Reject extreme outliers (transient spray spikes)
            z_lat = abs(node['lat'] - avg_lat) / lat_std
            z_lon = abs(node['lon'] - avg_lon) / lon_std
            if z_lat > 2.5 or z_lon > 2.5:
                continue  # Drops point as localized sea spray clutter
                
            # 2. Check height signatures against max wave clutter floor
            observed_height = node.get('height_above_water_m', 0.0)
            if observed_height <= max_wave_height and node.get('instant_velocity_mps', 0.0) < doppler_speed_floor_mps:
                continue  # Points match characteristics of an active wave crest
                
            valid_structural_points.append(node)
            
        logging.info(f"Clutter Filter Executed [Sea State {sea_state}]: Reduced {len(raw_radar_returns)} returns to {len(valid_structural_points)} verified hull points.")
        return valid_structural_points

    def process_aegis_track(self, filtered_points: list, delta_t: float, sea_state: int) -> dict:
        """
        Aegis Track Fusion Engine. Processes the output of the sea filter.
        Initializes and steps a linear Kalman tracking filter to lock onto true target speed, 
        course heading, and structural dimensions.
        """
        if not filtered_points:
            raise ValueError("Zero target telemetry inputs passed to Aegis tracking system.")
            
        # Compute tracking centroid out of verified hull structures
        c_lat = sum(p['lat'] for p in filtered_points) / len(filtered_points)
        c_lon = sum(p['lon'] for p in filtered_points) / len(filtered_points)
        
        # Extract boundary sizing arrays (Largest structural dimensions of target ship)
        lats = [p['lat'] for p in filtered_points]
        lons = [p['lon'] for p in filtered_points]
        
        # Convert bounding coordinate delta grids to physical meters
        ship_length_m, _ = self._haversine_distance_and_bearing(min(lats), c_lon, max(lats), c_lon)
        ship_beam_m, _ = self._haversine_distance_and_bearing(c_lat, min(lons), c_lat, max(lons))
        
        # Ensure dimensions fallback to standard baseline profiles if returns are tight
        ship_length_m = max(ship_length_m, 120.0)
        ship_beam_m = max(ship_beam_m, 18.0)
        
        # Step Linear Tracking Kalman Filter to lock spatial velocity vectors
        r_noise = self.measurement_noise_base * (1.0 + (sea_state * 0.5))
        
        if self.kalman_state is None:
            # Initialization Frame
            self.kalman_state = [c_lat, c_lon, 0.0, 0.0]
            self.kalman_covariance = [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 1.0]]
        else:
            # Prediction updates
            self.kalman_state[0] += self.kalman_state[2] * delta_t
            self.kalman_state[1] += self.kalman_state[3] * delta_t
            
            # Measurement correction step calculations
            k_gain = self.process_noise / (self.process_noise + r_noise)
            
            v_lat_measured = (c_lat - self.kalman_state[0]) / delta_t
            v_lon_measured = (c_lon - self.kalman_state[1]) / delta_t
            
            self.kalman_state[0] += k_gain * (c_lat - self.kalman_state[0])
            self.kalman_state[1] += k_gain * (c_lon - self.kalman_state[1])
            self.kalman_state[2] += k_gain * (v_lat_measured - self.kalman_state[2])
            self.kalman_state[3] += k_gain * (v_lon_measured - self.kalman_state[3])

        # Resolve filtered kinematic movement profiles
        future_lat_step = self.kalman_state[0] + self.kalman_state[2]
        future_lon_step = self.kalman_state[1] + self.kalman_state[3]
        speed_mps, course_deg = self._haversine_distance_and_bearing(self.kalman_state[0], self.kalman_state[1], future_lat_step, future_lon_step)
        
        return {
            "centroid_lat": self.kalman_state[0],
            "centroid_lon": self.kalman_state[1],
            "speed_mps": speed_mps,
            "speed_knots": speed_mps * 1.94384,
            "course_heading_deg": course_deg,
            "hull_length_m": ship_length_m,
            "hull_beam_m": ship_beam_m,
            "target_volume_cross_section_sqm": ship_length_m * ship_beam_m
        }

    def compute_predictive_intercept_solution(self, track_data: dict) -> dict:
        """
        Iterative Intercept Lead Vector Engine.
        Calculates shell flight time to predict exactly where a moving target vessel will be, 
        aiming square at the largest geometric part of the hull (structural center mass centroid).
        """
        target_lat = track_data["centroid_lat"]
        target_lon = track_data["centroid_lon"]
        speed = track_data["speed_mps"]
        heading_rad = math.radians(track_data["course_heading_deg"])
        
        # Calculate movement vector offsets in degrees per second
        lat_degree_offset_per_sec = (speed * math.cos(heading_rad)) / 111132.0
        lon_degree_offset_per_sec = (speed * math.sin(heading_rad)) / (111320.0 * math.cos(math.radians(target_lat)))
        
        predicted_lat = target_lat
        predicted_lon = target_lon
        flight_time_seconds = 0.0
        
        # Iterate to converge flight time with down-track vessel advancement (Iterative Lead Tracking)
        for _ in range(5):

range_meters, azimuth_deg = self._haversine_distance_and_bearing(self.position['lat'], self.position['lon'], predicted_lat, predicted_lon)
# Simple parabolic flight time mapping calculation
v_sq = self.STANDARD_MUZZLE_VELOCITY ** 2
under_root = v_sq2 - self.GRAVITY * (self.GRAVITY * (range_meters2))
if under_root < 0:
return {"status": "KINETIC_ENGAGEMENT_REJECTED", "reason": "Target lead position out of maximum ballistic range bounds."}
elevation_rad = math.atan((v_sq - math.sqrt(under_root)) / (self.GRAVITY * range_meters))
flight_time_seconds = (2 * self.STANDARD_MUZZLE_VELOCITY * math.sin(elevation_rad)) / self.GRAVITY
# Reposition target coordinates ahead matching flight path timings
predicted_lat = target_lat + (lat_degree_offset_per_sec * flight_time_seconds)
predicted_lon = target_lon + (lon_degree_offset_per_sec * flight_time_seconds)
final_range, final_azimuth = self._haversine_distance_and_bearing(self.position['lat'], self.position['lon'], predicted_lat, predicted_lon)
final_elevation_deg = math.degrees(math.atan((v_sq - math.sqrt(v_sq2 - self.GRAVITY * (self.GRAVITY * (final_range2)))) / (self.GRAVITY * final_range)))
return {
"status": "INTERCEPT_SOLUTION_LOCKED",
"intercept_range_m": round(final_range, 1),
"firing_azimuth_deg": round(final_azimuth, 3),
"firing_elevation_deg": round(final_elevation_deg, 3),
"projectile_time_of_flight_sec": round(flight_time_seconds, 2),
"lead_displacement_m": round(speed * flight_time_seconds, 1),
"target_lock_zone": f"Hull Center Profile ({int(track_data['hull_length_m'])}m x {int(track_data['hull_beam_m'])}m Centroid Point)"
}
Testing Simulation
if name == "main":
# Position tracking array: Coastal Artillery Base Battery
fcs = AthenaFireControlComputer(battery_id="COAST-DEF-01", latitude=32.665, longitude=-117.240, altitude=25.0)
# Raw Aegis AN/SPY Returns corrupted with heavy sea spray and active wave-crest reflections
# The actual vessel centroid is progressing near Lat: 32.721, Lon: -117.012 moving east
noisy_radar_feed = [
{"lat": 32.7211, "lon": -117.0122, "height_above_water_m": 12.0, "instant_velocity_mps": 11.2}, # Ship Structure
{"lat": 32.7215, "lon": -117.0119, "height_above_water_m": 14.5, "instant_velocity_mps": 11.0}, # Ship Structure
{"lat": 32.7208, "lon": -117.0125, "height_above_water_m": 8.0, "instant_velocity_mps": 11.5}, # Ship Structure
{"lat": 32.7225, "lon": -117.0150, "height_above_water_m": 2.1, "instant_velocity_mps": 3.4}, # Wave Clutter Peak
{"lat": 32.7190, "lon": -117.0102, "height_above_water_m": 1.5, "instant_velocity_mps": 4.1}, # Wave Clutter Peak
{"lat": 32.7550, "lon": -117.0420, "height_above_water_m": 0.5, "instant_velocity_mps": 1.2} # Distant Sea Spray Anomaly
]
# 1. Strip out wave crests and sea clutter under Rough Sea State 5 conditions
clean_points = fcs.apply_sea_state_clutter_filter(noisy_radar_feed, sea_state=5)
# 2. Track target vessel properties using Kalman smoothing across a 2.0 second update step
vessel_track = fcs.process_aegis_track(clean_points, delta_t=2.0, sea_state=5)
# 3. Compute predictive layout adjustments to shoot ahead of the moving ship target profile
firing_command = fcs.compute_predictive_intercept_solution(vessel_track)
print("\n--- AN/SPY CRUISE TRACK FUSION & RADAR CLUTTER RUNNER ---")
print(f"Target Classification Status: Ship Centroid Identified.")
print(f"Locked Speed: {vessel_track['speed_knots']:.2f} knots | Heading: {vessel_track['course_heading_deg']:.1f}°")
print(f"Total Structural Target Footprint Area: {vessel_track['target_volume_cross_section_sqm']:.1f} sq-meters")
print("\n--- BALLISTIC ENGAGEMENT SOLUTION ---")
for key, val in firing_command.items():
print(f" {key.replace('_', ' ').title()}: {val}")

