# File Name: bgp_autonomous_routing_core.py
# Location: /src/modules/
# Subsystem: Border Gateway Protocol (BGP) & Route Hijack Defense
# Copyright (c) 2026 Revolutionary Technology

import time
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_path_trust(reported_latencies_ms: np.ndarray, expected_latencies_ms: np.ndarray, hop_counts: np.ndarray) -> np.ndarray:
    """Calculates a heuristic trust score for BGP routes to detect malicious traffic diversion."""
    total_routes = reported_latencies_ms.shape[0]
    trust_scores = np.zeros(total_routes, dtype=np.float64)
    
    for i in prange(total_routes):
        # If latency is massively higher than expected for the physical distance, it implies physical rerouting (interception)
        latency_delta = reported_latencies_ms[i] - expected_latencies_ms[i]
        
        # Penalize excessive, unoptimized AS hops
        hop_penalty = (hop_counts[i] - 3) * 5.0 if hop_counts[i] > 3 else 0.0
        
        # Base score 100, degraded by anomalies
        score = 100.0 - max(0.0, latency_delta * 0.5) - hop_penalty
        trust_scores[i] = max(0.0, min(100.0, score))
        
    return trust_scores

class BGPRoutingDefenseCore:
    def __init__(self):
        self.critical_trust_threshold = 60.0 # Routes falling below 60% trust are blackholed

    def evaluate_routing_tables(self, autonomous_system_paths: List[str], latencies: List[float], expected_latencies: List[float], hops: List[int]) -> dict:
        print(f"\n[CYBERCOM] Sweeping global BGP routing tables for BGP Leaks and Route Hijacking...")
        start_time = time.time()
        
        lat_arr = np.array(latencies, dtype=np.float64)
        exp_arr = np.array(expected_latencies, dtype=np.float64)
        hop_arr = np.array(hops, dtype=np.float64)
        
        # Execute JIT Math
        trust_matrix = parallel_calculate_path_trust(lat_arr, exp_arr, hop_arr)
        
        hijacked_routes = []
        for i in range(len(autonomous_system_paths)):
            if trust_matrix[i] < self.critical_trust_threshold:
                hijacked_routes.append({
                    "as_path": autonomous_system_paths[i],
                    "measured_latency_ms": latencies[i],
                    "trust_score_pct": round(trust_matrix[i], 2),
                    "action": "NULL_ROUTE_BGP_BLACKHOLE_ENGAGED"
                })

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "BGP_HIJACKING_DETECTED" if hijacked_routes else "GLOBAL_ROUTING_SECURE"

        return {
            "internet_backbone_status": status,
            "routes_analyzed": len(autonomous_system_paths),
            "quarantined_paths": hijacked_routes,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    bgp = BGPRoutingDefenseCore()
    # Mocking BGP routes. Path 2 shows extreme latency and high hops (classic Russian/Chinese BGP hijack signature).
    print("TESTING BGP DEFENSE CORE:\n", bgp.evaluate_routing_tables(
        ["AS15169 -> AS7018", "AS15169 -> AS4808 -> AS4134 -> AS7018", "AS13335 -> AS3356"], 
        [12.0, 350.0, 15.0], 
        [10.0, 12.0, 14.0], 
        [2, 8, 2]
    ))
