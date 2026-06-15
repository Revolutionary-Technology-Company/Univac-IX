# File Name: particle_accelerator_synchrotron_core.py
# Location: /src/modules/
# Subsystem: High-Energy Particle Synchrotron & Quench Defense
# Copyright (c) 2026 Revolutionary Technology

import time
import math
import numpy as np
from numba import njit, prange
from typing import Dict, Any, List

C_SPEED = 299792458.0 # m/s
REST_MASS_PROTON_EV = 938.272e6 # eV

@njit(parallel=True, cache=True, fastmath=True)
def parallel_calculate_synchrotron_kinematics(beam_energies_tev: np.ndarray, ring_radius_m: float) -> np.ndarray:
    """Calculates the magnetic field (Tesla) required to bend relativistic particle beams."""
    total_sectors = beam_energies_tev.shape[0]
    required_b_fields_tesla = np.zeros(total_sectors, dtype=np.float64)
    
    for i in prange(total_sectors):
        # Convert TeV (Tera-electronvolts) to eV
        energy_ev = beam_energies_tev[i] * 1e12
        
        # At extreme relativistic speeds, Energy is approximately equal to momentum * c (E ~ pc)
        # Momentum (p) in eV/c
        momentum_ev_c = energy_ev 
        
        # Required Magnetic Field: B = p / (q * r)
        # In practical accelerator physics units: B (Tesla) ~ 3.3356 * p (GeV/c) / r (meters)
        momentum_gev_c = momentum_ev_c / 1e9
        required_b_fields_tesla[i] = (3.3356 * momentum_gev_c) / ring_radius_m
        
    return required_b_fields_tesla

class ParticleAcceleratorCore:
    def __init__(self):
        # Superconducting niobium-titanium magnets lose superconductivity ("Quench") above 2.2 Kelvin or ~8.5 Tesla
        self.critical_temp_k = 2.2 
        self.max_magnetic_field_t = 8.5
        self.accelerator_radius_m = 4300.0 # Approx LHC radius (27km circumference)

    def evaluate_beam_stability(self, sector_ids: List[str], energies_tev: List[float], magnet_temps_k: List[float]) -> dict:
        print(f"\n[QUANTUM PHYSICS] Spooling Synchrotron Superconducting Dipole Magnets...")
        start_time = time.time()
        
        e_arr = np.array(energies_tev, dtype=np.float64)
        
        # Execute JIT Math
        b_fields_t = parallel_calculate_synchrotron_kinematics(e_arr, self.accelerator_radius_m)
        
        quench_warnings = []
        for i in range(len(sector_ids)):
            temp = magnet_temps_k[i]
            b_field = b_fields_t[i]
            
            # A Quench occurs if the magnet warms up OR if the magnetic field is pushed too high
            if temp >= self.critical_temp_k or b_field >= self.max_magnetic_field_t:
                quench_warnings.append({
                    "sector": sector_ids[i],
                    "magnet_temp_k": temp,
                    "required_field_t": round(b_field, 3),
                    "action": "CRITICAL_QUENCH_DETECTED_ABORT_AND_DUMP_BEAM"
                })

        execution_ms = (time.time() - start_time) * 1000.0
        
        status = "BEAM_STABLE_COLLISIONS_ACTIVE" if not quench_warnings else "EMERGENCY_BEAM_DUMP_ENGAGED"

        return {
            "accelerator_status": status,
            "sectors_monitored": len(sector_ids),
            "peak_beam_energy_tev": max(energies_tev),
            "containment_faults": quench_warnings,
            "execution_time_ms": round(execution_ms, 5)
        }

if __name__ == "__main__":
    cern = ParticleAcceleratorCore()
    # Mocking LHC sectors. Sector 3 is pushing 7.0 TeV but its cryogenics are failing (warming to 2.3K).
    print("TESTING ACCELERATOR CORE:\n", cern.evaluate_beam_stability(
        ["SECTOR-12", "SECTOR-23", "SECTOR-34"], 
        [6.8, 6.8, 7.0], # TeV
        [1.9, 1.9, 2.3]  # Kelvin
    ))
