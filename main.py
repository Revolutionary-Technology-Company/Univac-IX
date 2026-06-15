import sys
import os
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import typer

app = typer.Typer(help="UNIVAC-IX Tactical Dual-Way Radio Mesh, Live Auditing & Guideline Ingestion Fabric")

# Global register files mapping threshold boundaries read from documents
_safety_threshold_registers: Dict[str, Dict[str, int]] = {
    "DEFAULT_MAX": {"upper_limit": 255, "lower_limit": 0}
}

_cached_fingerprints: Dict[str, str] = {
    "0x0011": "DRIVER_MIL_STD_1397_TACTICAL",
    "0x0012": "DRIVER_MIL_STD_1397_TACTICAL",
    "0x0013": "DRIVER_AVIATION_KNOWLEDGE",
    "0x0014": "DRIVER_AVIATION_KNOWLEDGE",
    "0x0022": "DRIVER_OTIS_GEN360",
    "0x0037": "DRIVER_SAFETY_MONITOR"
}

def load_system_config(config_path: Path) -> Dict[str, Any]:
    if config_path.exists():
        with open(config_path, "r") as stream:
            return yaml.safe_load(stream)
    print(f"Configuration Fault: Path {config_path} not found.", file=sys.stderr)
    raise typer.Exit(code=1)


# --- Automated Safety Guideline Parsing Engine ---

@app.command(name="load-safety-boundaries")
def load_safety_boundaries_command(
    guideline_path: Path = typer.Argument(..., help="Path to the Environment-Safety-Monitor markdown guideline file (e.g., README.md).")
):
    """Parses raw text guidelines to dynamically extract and store hardware sensor threshold boundaries in runtime memory registers."""
    global _safety_threshold_registers
    if not guideline_path.exists():
        print(f"[GUIDELINE FAULT] Specification doc file path not found: '{guideline_path}'", file=sys.stderr)
        raise typer.Exit(code=1)
        
    print(f"[INGESTION] Opening target environment safety guidelines: {guideline_path}")
    
    with open(guideline_path, "r", encoding="utf-8", errors="ignore") as doc:
        lines = doc.readlines()
        
    # Compile matching pattern tracking standard rule syntax: "SENSOR_ID: MAX_HEX / MIN_HEX" (e.g., "0x0037: C8 / 0A")
    rule_pattern = re.compile(r"(0x[0-9a-fA-F]{2,4})\s*:\s*([0-9a-fA-F]{2,8})\s*/\s*([0-9a-fA-F]{2,8})")
    extracted_rules_count = 0
    
    for line in lines:
        match_entry = rule_pattern.search(line.strip())
        if not match_entry:
            continue # Skip boilerplate descriptions, headers, or narrative markdown blocks
            
        sensor_addr = match_entry.group(1).lower()
        max_hex_val = match_entry.group(2)
        min_hex_val = match_entry.group(3)
        
        # Standardize hex string values into machine integers
        max_int = int(max_hex_val, 16)
        min_int = int(min_hex_val, 16)
        
        # Populate live runtime safety registers
        _safety_threshold_registers[sensor_addr] = {
            "upper_limit": max_int,
            "lower_limit": min_int
        }
        
        print(f"  -> REGISTERED ADDR [{sensor_addr}]: Upper Max Limit = {max_int} (0x{max_hex_val}) | Lower Min Limit = {min_int} (0x{min_hex_val})")
        extracted_rules_count += 1
        
    if extracted_rules_count == 0:
        print("[INGESTION WARNING] Document parsed successfully but contains no matching '0xXX: MAX/MIN' structural pattern rules.", file=sys.stderr)
        return
        
    print(f"[INGESTION COMPLETE] Successfully mapped {extracted_rules_count} dynamic boundary parameters to memory buffers.")


# --- Legacy Command Triggers for Mapping Operations ---

@app.command(name="export-visio")
def export_visio_command(
    config: Path = typer.Option(Path("config.yaml"), help="Path to the node configuration registry file."),
    output: Path = typer.Option(Path("visio_mapping.csv"), help="Target path for Visio Data Visualizer CSV output.")
):
    """Generates an enhanced Visio-compliant CSV integrating live autonomic learning and bidirectional tracking flags."""
    config_data = load_system_config(config)
    handshake_rules = config_data.get("recovery_handshakes", {})
    
    with open(output, "w", encoding="utf-8") as f:
        f.write("Process Step ID,Step Name,Description,Next Step ID,Resource,Node Type,Hardware Port,Hex Address,Assigned Driver,Bidirectional Flag,System Severity,Visio Shape Color\n")
        
        nodes = config_data.get("nodes", [])
        total_nodes = len(nodes)
        
        for index, node in enumerate(nodes):
            node_id = node.get("id", "UNKNOWN")
            hex_addr = node.get("hex_address", "").lower()
            target_mod = node.get("target_module", "GENERIC_IO")
            
            next_index = index + 1
            next_step = f"NODE_{str(next_index + 1).zfill(2)}"
            if next_index >= total_nodes:
                next_step = ""
                
            assigned_driver = _cached_fingerprints.get(hex_addr, "DRIVER_UNKNOWN_GENERIC_SERIAL")
            
            bidirectional_flag = "PASSIVE_LISTEN_ONLY"
            if assigned_driver in handshake_rules:
                bidirectional_flag = "BIDIRECTIONAL_RESPONSE_ARMED"
                
            severity = "INFORMATIONAL"
            color_code = "Blue"
            
            if assigned_driver in ["DRIVER_MIL_STD_1397_TACTICAL", "DRIVER_AVIATION_KNOWLEDGE"]:
                severity = "OPERATIONAL"
                color_code = "Green"
                
            if assigned_driver == "DRIVER_OTIS_GEN360":
                severity = "WARNING"
                color_code = "Orange"
                
            if assigned_driver == "DRIVER_SAFETY_MONITOR":
                severity = "CRITICAL_TRAP_ENGAGED"
                color_code = "Red"
                
            node_desc = f"Routes {target_mod} via driver {assigned_driver}"
            
            f.write(
                f"{node_id},"
                f"{node.get('name', 'Unnamed_Node')},"
                f"{node_desc},"
                f"{next_step},"
                f"{target_mod.upper()},"
                f"{node.get('type', 'UNKNOWN')},"
                f"{node.get('port', 'NONE')},"
                f"{hex_addr},"
                f"{assigned_driver},"
                f"{bidirectional_flag},"
                f"{severity},"
                f"{color_code}\n"
            )
            
    print(f"[VISIO COMPILER] Successfully generated layout model inside: '{output}'")


if __name__ == "__main__":
    app()
