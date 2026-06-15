import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import typer

app = typer.Typer(help="Dynamic Plug-and-Play UNIVAC Mainframe Hardware Emulator Fabric")

# Global reference state to check for dynamic hot-swap additions
_loaded_nodes_cache: List[str] = []

def validate_word_alignment(bit_length: int) -> None:
    if bit_length == 36:
        return
    if bit_length == 18:
        return
    if bit_length == 16:
        return
    print(f"Hardware Fault: Unsupported bit architecture {bit_length}.", file=sys.stderr)
    raise typer.Exit(code=1)

def convert_hex_stream(hex_payload: str) -> bytes:
    if len(hex_payload) % 2 == 0:
        return bytes.fromhex(hex_payload)
    print("Signal Fault: Hexadecimal streams must be symmetric (even length).", file=sys.stderr)
    raise typer.Exit(code=1)

def load_system_config(config_path: Path) -> Dict[str, Any]:
    if config_path.exists():
        with open(config_path, "r") as stream:
            return yaml.safe_load(stream)
    print(f"Configuration Fault: Path {config_path} not found.", file=sys.stderr)
    raise typer.Exit(code=1)

def discover_hot_plugged_nodes(old_cache: List[str], current_nodes: List[Dict[str, Any]]) -> List[str]:
    """Identifies newly appended physical or virtual nodes during runtime modifications."""
    new_additions: List[str] = []
    for node in current_nodes:
        node_id = node.get("id", "UNKNOWN")
        if node_id in old_cache:
            continue
        new_additions.append(node_id)
    return new_additions


@app.command(name="route-signal")
def route_signal_command(
    hex_address: str = typer.Argument(..., help="Target device hexadecimal address (e.g., 0x00A1)."),
    payload: str = typer.Argument(..., help="The hexadecimal input or output signal payload data."),
    config: Path = typer.Option(Path("config.yaml"), help="Path to the node configuration registry file.")
):
    """Dynamically interfaces and maps I/O signals to attached repository software layers."""
    config_data = load_system_config(config)
    clean_addr = hex_address.strip().lower()
    clean_payload = payload.strip().upper()
    
    raw_data = convert_hex_stream(clean_payload)
    system_word_size = config_data.get("system", {}).get("default_word_size", 36)
    validate_word_alignment(system_word_size)

    for node in config_data.get("nodes", []):
        if node.get("hex_address", "").lower() != clean_addr:
            continue
        
        if node.get("status") != "ACTIVE":
            print(f"Pipeline Deferred: Node {node.get('id')} is on STANDBY or OFFLINE.", file=sys.stderr)
            raise typer.Exit(code=0)
            
        match node.get("target_module"):
            case "aegis-bridge":
                print(f"[MODULE: AEGIS] Routing to {node['name']} ({node['type']}) -> Payload: {raw_data.hex()}")
                return
            case "aviation-knowledge":
                print(f"[MODULE: AVIATION] Parsing flight telemetry payload stream -> {raw_data.hex()}")
                return
            case "safety-monitor":
                print(f"[MODULE: SAFETY] Injecting hardware sensory data -> {raw_data.hex()}")
                return
            case "otis-gen360":
                print(f"[MODULE: OTIS] Processing vertical transit system matrix data -> {raw_data.hex()}")
                return
            case _:
                print(f"Module Fault: Target routine '{node.get('target_module')}' missing implementation.", file=sys.stderr)
                raise typer.Exit(code=4)

    print(f"Routing Fault: Address {hex_address} matches no mapped hardware node.", file=sys.stderr)
    raise typer.Exit(code=2)


@app.command(name="monitor-fabric")
def monitor_fabric_command(
    config: Path = typer.Option(Path("config.yaml"), help="Path to the node configuration file to poll for hot-plugs."),
    interval: float = typer.Option(1.0, help="Polling interval gap delay in fractional seconds.")
):
    """Launches a live background listener loop detecting on-the-fly hardware attachments."""
    global _loaded_nodes_cache
    if not config.exists():
        print(f"Initialization Fault: Cannot monitor non-existent target '{config}'", file=sys.stderr)
        raise typer.Exit(code=1)
        
    print(f"[FABRIC] Initializing hardware framework mapping observer for: {config}")
    initial_data = load_system_config(config)
    _loaded_nodes_cache = [node.get("id", "UNKNOWN") for node in initial_data.get("nodes", [])]
    print(f"[FABRIC] Monitoring {_loaded_nodes_cache} active baseline interface pathways...")

    last_modified_time = config.stat().st_mtime

    try:
        while True:
            time.sleep(interval)
            current_modified_time = config.stat().st_mtime
            
            if current_modified_time == last_modified_time:
                continue
                
            # Document mutation state event
            print("[HOTPLUG EVENT] Change flagged on hardware registry map. Parsing additions...")
            last_modified_time = current_modified_time
            
            updated_data = load_system_config(config)
            current_nodes = updated_data.get("nodes", [])
            
            new_nodes = discover_hot_plugged_nodes(_loaded_nodes_cache, current_nodes)
            
            if not new_nodes:
                print("[HOTPLUG WARNING] Registry update contains no completely new Node IDs.")
                # Refresh cache layout regardless to parse non-structural data mutations
                _loaded_nodes_cache = [node.get("id", "UNKNOWN") for node in current_nodes]
                continue

            for node in current_nodes:
                if node.get("id") not in new_nodes:
                    continue
                print(f" -> PLUG-AND-PLAY MOUNTED: Node [{node.get('id')}] -> Name: {node.get('name')} Address: {node.get('hex_address')} Module target: {node.get('target_module')}")
                
            # Append completely synchronized entities back to running session state mapping
            _loaded_nodes_cache = [node.get("id", "UNKNOWN") for node in current_nodes]
            
    except KeyboardInterrupt:
        print("\n[FABRIC] Terminating active hardware mapping watch process cleanly.")
        raise typer.Exit(code=0)


@app.command(name="export-visio")
def export_visio_command(
    config: Path = typer.Option(Path("config.yaml"), help="Path to the node configuration registry file."),
    output: Path = typer.Option(Path("visio_mapping.csv"), help="Target path for Visio Data Visualizer CSV output.")
):
    """Generates a Visio-compliant Data Visualizer CSV mapping file from the active framework."""
    config_data = load_system_config(config)
    
    with open(output, "w") as f:
        f.write("Process Step ID,Step Name,Description,Next Step ID,Resource,Node Type,Hardware Port,Hex Address\n")
        nodes = config_data.get("nodes", [])
        total_nodes = len(nodes)
        
        for index, node in enumerate(nodes):
            next_index = index + 1
            next_step = f"NODE_0{next_index + 1}"
            if next_index >= total_nodes:
                next_step = ""
                
            f.write(
                f"{node['id']},"
                f"{node['name']},"
                f"Routes signals to {node['target_module']},"
                f"{next_step},"
                f"{node['target_module'].upper()},"
                f"{node['type']},"
                f"{node['port']},"
                f"{node['hex_address']}\n"
            )
            
    print(f"Success: Visio structural file compiled at '{output}'.")


if __name__ == "__main__":
    app()
