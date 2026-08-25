# Module: athena_fire_control_computer.py
# Platform: Univac-IX Fire Control System (FCS)

import math
import logging
from datetime import datetime, timedelta

class AthenaFireControlComputer:
    def __init__(self, battery_id: str, latitude: float, longitude: float, altitude: float):
        self.battery_id = battery_id
        self.position = {'lat': latitude, 'lon': longitude, 'alt': altitude}
        self.GRAVITY = 9.80665
        self.STANDARD_MUZZLE_VELOCITY = 827.0

    def _haversine_distance_and_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> tuple:
        R = 6371000.0
        r_lat1, r_lon1 = math.radians(lat1), math.radians(lon1)
        r_lat2, r_lon2 = math.radians(lat2), math.radians(lon2)
        dlat, dlon = r_lat2 - r_lat1, r_lon2 - r_lon1
        a = math.sin(dlat / 2)**2 + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(dlon / 2)**2
        distance = R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))
        y = math.sin(dlon) * math.cos(r_lat2)
        x = math.cos(r_lat1) * math.sin(r_lat2) - math.sin(r_lat1) * math.cos(r_lat2) * math.cos(dlon)
        return distance, (math.degrees(math.atan2(y, x)) + 360) % 360

    def _project_coordinates(self, start_lat: float, start_lon: float, bearing_deg: float, distance_m: float) -> tuple:
        R = 6371000.0
        r_lat, r_lon = math.radians(start_lat), math.radians(start_lon)
        r_bearing = math.radians(bearing_deg)
        angular_dist = distance_m / R
        end_lat = math.asin(math.sin(r_lat) * math.cos(angular_dist) + math.cos(r_lat) * math.sin(angular_dist) * math.cos(r_bearing))
        end_lon = r_lon + math.atan2(math.sin(r_bearing) * math.sin(angular_dist) * math.cos(r_lat), math.cos(angular_dist) - math.sin(r_lat) * math.sin(end_lat))
        return math.degrees(end_lat), math.degrees(end_lon)

    def process_aegis_track(self, aegis_telemetry_history: list) -> dict:
        pt1 = aegis_telemetry_history[-2]
        pt2 = aegis_telemetry_history[-1]
        dt = (pt2['timestamp_utc'] - pt1['timestamp_utc']).total_seconds()
        if dt <= 0: dt = 1.0
        distance_moved, course = self._haversine_distance_and_bearing(pt1['centroid_lat'], pt1['centroid_lon'], pt2['centroid_lat'], pt2['centroid_lon'])
        speed_mps = distance_moved / dt
        length = pt2.get('observed_length_m', 150.0)
        beam = pt2.get('observed_beam_m', 20.0)
        return {
            "vessel_class": pt2['vessel_class'], "current_lat": pt2['centroid_lat'], "current_lon": pt2['centroid_lon'],
            "speed_mps": speed_mps, "speed_knots": speed_mps * 1.94384, "course_deg": course, "target_surface_area_sqm": length * beam
        }

    def compute_predictive_naval_intercept(self, target_kinetics: dict, target_alt: float, met_data: dict) -> dict:
        predicted_lat = target_kinetics['current_lat']
        predicted_lon = target_kinetics['current_lon']
        v0 = self.STANDARD_MUZZLE_VELOCITY
        density_factor = met_data.get('air_density_pct', 100.0) / 100.0
        crosswind = met_data.get('crosswind_mps', 0.0)
        headwind = met_data.get('headwind_mps', 0.0)
        
        for _ in range(10):
            distance, raw_azimuth = self._haversine_distance_and_bearing(self.position['lat'], self.position['lon'], predicted_lat, predicted_lon)
            effective_distance = distance * (1.0 + (density_factor - 1.0) * 0.05) + (headwind * 12.0)
            alt_delta = target_alt - self.position['alt']
            v_sq = v0 ** 2
            under_root = v_sq**2 - self.GRAVITY * (self.GRAVITY * (effective_distance**2) + 2 * alt_delta * v_sq)
            if under_root < 0: return {"status": "INTERCEPT_REJECTED"}
            root = math.sqrt(under_root)
            elevation_rad = math.atan((v_sq - root) / (self.GRAVITY * effective_distance))
            tof = (2 * v0 * math.sin(elevation_rad)) / self.GRAVITY
            lead_distance = target_kinetics['speed_mps'] * tof
            new_pred_lat, new_pred_lon = self._project_coordinates(target_kinetics['current_lat'], target_kinetics['current_lon'], target_kinetics['course_deg'], lead_distance)
            move_delta, _ = self._haversine_distance_and_bearing(predicted_lat, predicted_lon, new_pred_lat, new_pred_lon)
            predicted_lat, predicted_lon = new_pred_lat, new_pred_lon
            if move_delta < 0.1: break
            
        return {
            "status": "AEGIS_FIRE_SOLUTION_READY", "target_classification": target_kinetics['vessel_class'],
            "vessel_speed_knots": round(target_kinetics['speed_knots'], 1), "vessel_course_deg": round(target_kinetics['course_deg'], 1),
            "estimated_flight_time_sec": round(tof, 2), "lead_distance_ahead_m": round(lead_distance, 1),
            "firing_quadrant_elevation_deg": round(math.degrees(elevation_rad), 3), "firing_deflection_azimuth_deg": round((raw_azimuth + (crosswind * 0.08)) % 360, 3),
            "targeting_strategy": f"LOCK_LARGEST_STRUCTURAL_CENTROID ({target_kinetics['target_surface_area_sqm']:.1f} sqm profile)"
        }
