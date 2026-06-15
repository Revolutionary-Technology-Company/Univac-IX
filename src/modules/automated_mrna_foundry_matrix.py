# File Name: automated_mrna_foundry_matrix.py
# Location: /src/modules/
# Subsystem: Automated mRNA Pharmaceutical Foundry & Folding Matrix
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_folding_stability(gc_content_pct: np.ndarray, strand_length_bases: np.ndarray) -> np.ndarray:
    """
    Calculates a heuristic proxy for Minimum Free Energy (MFE) in RNA folding.
    Lower (more negative) MFE means a more stable structure that resists thermal degradation.
    """
    total_strands = gc_content_pct.shape[0]
    mfe_kcal_mol = np.zeros(total_strands, dtype=np.float64)
    
    for i in prange(total_strands):
        # Guanine-Cytosine (GC) pairs have 3 hydrogen bonds, making them highly stable.
        # Higher GC content generally leads to more stable RNA secondary structures (lower MFE).
        gc_fraction = gc_content_pct[i] / 100.0
        
        # Heuristic MFE calculation (simplified for real-time simulation)
        # Stability scales with length and exponentially with GC content
        base_stability = -(strand_length_bases[i] * 0.3)
        gc_bonus = base_stability * (gc_fraction * 1.5)
        
        mfe_kcal_mol[i] = base_stability + gc_bonus
        
    return mfe_kcal_mol

class AutomatedmRNAFoundry:
    def __init__(self):
        # MFE must be below -300 kcal/mol to survive standard refrigeration without degrading
        self.target_stability_mfe = -300.0 

    def execute_bioreactor_batch(self, batch_ids: List[str], gc_contents: List[float], strand_lengths: List[int], reactor_temps_c: List[float]) -> dict:
        print(f"\n[BIO-MANUFACTURING] Spooling mRNA foundry. Calculating thermal folding stability...")
        start_time = time.time()
        
        gc_arr = np.array(gc_contents, dtype=np.float64)
        len_arr = np.array(strand_lengths, dtype=np.float64)
        
        # Execute JIT Math
        mfe_scores = parallel_calculate_folding_stability(gc_arr, len_arr)
        
        production_orders = []
        total_vials_produced = 0
        
        for i in range(len(batch_ids)):
            mfe = mfe_scores[i]
            reactor_temp = reactor_temps_c[i]
            
            # If the reactor gets too hot (above 37C), the lipid nanoparticles and mRNA denature
            if reactor_temp > 37.0:
                production_orders.append({
                    "batch": batch_ids[i],
                    "issue": "BIOREACTOR_THERMAL_DENATURATION",
                    "action": "FLUSH_BATCH_AND_STERILIZE_VAT"
                })
            elif mfe > self.target_stability_mfe: # e.g. -200 is warmer/less stable than -300
                production_orders.append({
                    "batch": batch_ids[i],
                    "mfe_kcal_mol": round(mfe, 2),
                    "action": "REJECT_BATCH_FRAGILE_COLD_CHAIN_REQUIRED"
                })
            else:
                # Assuming 1 batch generates 500,000 viable doses
                total_vials_produced += 500000
                production_orders.append({
                    "batch": batch_ids[i],
                    "mfe_kcal_mol": round(mfe, 2),
                    "action": "BATCH_APPROVED_COMMENCE_LIPID_ENCAPSULATION"
                })

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "FOUNDRY_OPERATIONS_OPTIMAL" if total_vials_produced > 0 else "ALL_BATCHES_REJECTED"

        return {
            "foundry_status": status,
            "batches_sequenced": len(batch_ids),
            "total_viable_doses_synthesized": total_vials_produced,
            "quality_control_log": production_orders,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    foundry = AutomatedmRNAFoundry()
    # Mocking mRNA vaccine production. Batch 3 has low GC content (fragile). Batch 2 reactor overheated.
    print("TESTING MRNA FOUNDRY MATRIX:\n", foundry.execute_bioreactor_batch(
        ["VAX-BATCH-ALPHA", "VAX-BATCH-BRAVO", "VAX-BATCH-CHARLIE"], 
        [55.0, 60.0, 35.0], # GC Content %
        [4000, 4200, 3800], # Base pairs length
        [34.0, 39.5, 35.0]  # Bioreactor temp C
    ))
