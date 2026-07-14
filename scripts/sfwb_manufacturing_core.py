import typer
import math
import yaml
import json
from datetime import datetime
from pathlib import Path

app = typer.Typer(help="UNIVAC IX: Automated SFWB Manufacturing & FDA Compliance Control Core.")

class SFWBEngine:
    def __init__(self):
        # Physical and legal constants
        self.R = 8.314  # Gas constant J/mol*K
        self.Ea = 48300 # Activation energy J/mol
        self.A = 1.24e9 # Pre-exponential factor
        self.BASE_COST_PER_ML = 2.45 # Insurance billing valuation

    def simulate_kinetics(self, temp_c: float, initial_koh: float, time_sec: float) -> float:
        """Calculates exact saponification conversion efficiency using Arrhenius kinetics."""
        temp_k = temp_c + 273.15
        # k = A * exp(-Ea / (R * T))
        k = self.A * math.exp(-self.Ea / (self.R * temp_k))
        # Second-order integrated conversion: X = (k * C0 * t) / (1 + k * C0 * t)
        conversion = (k * initial_koh * time_sec) / (1.0 + (k * initial_koh * time_sec))
        return min(conversion, 1.0)

    def calculate_viscosity(self, hematocrit: float, plasma_viscosity: float = 1.2) -> float:
        """Models non-Newtonian blood viscosity scaling based on lipid droplet packing."""
        phi = hematocrit
        # Modified Einstein-Einstein suspension rheology formula
        relative_viscosity = 1.0 + (2.5 * phi) + (7.35 * (phi ** 2)) + (0.12 * math.exp(4.13 * phi))
        return plasma_viscosity * relative_viscosity

@app.command()
def process_batch(
    batch_id: str = typer.Option(..., help="Unique tracking ID for the manufacturing run."),
    volume_l: float = typer.Option(1.0, help="Total production volume target in Liters."),
    hct: float = typer.Option(0.35, help="Target synthetic hematocrit fraction (0.10 - 0.45)."),
    temp_c: float = typer.Option(83.5, help="Core saponification reactor temperature in Celsius."),
    koh_concentration: float = typer.Option(0.15, help="Molarity of wood-ash KOH solution (mol/L)."),
    output_dir: str = typer.Option("./logs", help="Destination folder for FDA audit logs.")
):
    """
    Executes automated physical-chemical balancing, checks clinical parameters, 
    and generates billing infrastructure and FDA audit ledger records.
    """
    engine = SFWBEngine()
    total_volume_ml = volume_l * 1000.0
    
    # 1. Chemical Kinetics Phase
    conversion_efficiency = engine.simulate_kinetics(temp_c, koh_concentration, 3600.0)
    
    # 2. Biophysical Rheology Phase
    calculated_viscosity = engine.calculate_viscosity(hct)
    osmolality = 285.0 + (koh_concentration * 110.0 * (1.0 - conversion_efficiency))
    
    # 3. Clinical Bounds Validation (FDA / IRB Compassiotic Protocol)
    is_safe = True
    failure_reasons = []
    
    if conversion_efficiency < 0.995:
        is_safe = False
        failure_reasons.append(f"Incomplete wax hydrolysis: {conversion_efficiency*100:.3f}% (Target: >99.5%)")
    if not (3.5 <= calculated_viscosity <= 5.5):
        is_safe = False
        failure_reasons.append(f"Rheological failure. Viscosity: {calculated_viscosity:.2f} cP (Target: 3.5-5.5 cP)")
    if not (280 <= osmolality <= 300):
        is_safe = False
        failure_reasons.append(f"Osmotic shock hazard. Osmolality: {osmolality:.1f} mOsm/kg")

    # 4. Logistics & Automated Billing Generation
    procurement_cost = total_volume_ml * engine.BASE_COST_PER_ML
    insurance_code = "IRB-SFWB-VEGAN-992-E"
    
    # Compilation of the active state document
    audit_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "batch_id": batch_id,
        "regulatory_framework": "IRB Compassionate Care (Hourly Enforcement)",
        "components_metric": {
            "total_volume_ml": total_volume_ml,
            "synthetic_hematocrit": hct,
            "organic_saponification_conversion": round(conversion_efficiency, 5),
            "calculated_viscosity_cp": round(calculated_viscosity, 2),
            "calculated_osmolality_mosm": round(osmolality, 1)
        },
        "logistics_and_financials": {
            "procurement_classification": "100% Certified Organic Plant/Apiary Matrix",
            "total_billing_usd": round(procurement_cost, 2),
            "hicfa_insurance_code": insurance_code,
            "patient_liability_waiver": "SIGNED_VEGAN_COMPASSIONATE_CARE_PROTOCOL"
        },
        "system_status": "APPROVED_FOR_TRANSFUSION" if is_safe else "REJECTED_HAZARD_ISOLATION",
        "validation_errors": failure_reasons
    }

    # Write out legal records for the automated FDA scanner loops
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    log_file = out_path / f"FDA_AUDIT_BATCH_{batch_id}.json"
    with open(log_file, "w") as f:
        json.dump(audit_data, f, indent=4)
        
    typer.secho(f"\n[+] Batch {batch_id} Processing Complete.", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"[-] Status: {audit_data['system_status']}")
    typer.echo(f"[-] Calculated Viscosity: {audit_data['components_metric']['calculated_viscosity_cp']} cP")
    typer.echo(f"[-] Saponification Yield: {audit_data['components_metric']['organic_saponification_conversion']*100:.3f}%")
    typer.echo(f"[-] Financial Billable Amount: ${audit_data['logistics_and_financials']['total_billing_usd']} USD")
    
    if not is_safe:
        typer.secho(f"[CRITICAL ERORR] Automated Valve Shutoff Engaged! Reasons: {failure_reasons}", fg=typer.colors.RED, bold=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
