import sys
from typing import Optional
import typer

app = typer.Typer(help="Universal Legacy System Hardware Interface Node")

# --- Helper Logic and Guard Clauses ---

def validate_word_alignment(bit_length: int) -> None:
    if bit_length == 36:
        return
    if bit_length == 18:
        return
    if bit_length == 16:
        return
    print(f"Error: Non-standard word width {bit_length} detected.", file=sys.stderr)
    raise typer.Exit(code=1)

def convert_hex_stream(hex_payload: str) -> bytes:
    if len(hex_payload) % 2 == 0:
        return bytes.fromhex(hex_payload)
    print("Error: Hexadecimal data stream must contain even-length segments.", file=sys.stderr)
    raise typer.Exit(code=1)


# --- Module Sub-Commands ---

@app.command(name="aegis-bridge")
def aegis_bridge_command(
    payload: str = typer.Argument(..., help="Hexadecimal signal data stream."),
    target_node: str = typer.Option("NTDS_A", help="Target hardware node designation."),
    word_size: int = typer.Option(36, help="Target system bit width architecture.")
):
    """Interfaces directly with the Univac-Aegis-bridge hardware streams."""
    validate_word_alignment(word_size)
    
    clean_hex = payload.strip().upper()
    raw_data = convert_hex_stream(clean_hex)
    
    match target_node:
        case "NTDS_A":
            print(f"[AEGIS] Routing to AN/UYK-7 Parallel Channel A: {raw_data.hex()}")
            return
        case "NTDS_B":
            print(f"[AEGIS] Routing to AN/UYK-7 Serial Channel B: {raw_data.hex()}")
            return
        case "AN/UYK-20":
            print(f"[AEGIS] Routing to AN/UYK-20 Controller: {raw_data.hex()}")
            return
            
    print(f"Warning: Node '{target_node}' matches no hardware pipeline.", file=sys.stderr)
    raise typer.Exit(code=2)


@app.command(name="safety-monitor")
def safety_monitor_command(
    sensor_id: str = typer.Argument(..., help="Hex identifier for the target environment sensor."),
    threshold_hex: str = typer.Option("FF", help="Hexadecimal maximum threshold value.")
):
    """Executes thresholds against the Environment-Safety-Monitor specifications."""
    clean_sensor = sensor_id.strip().upper()
    clean_threshold = threshold_hex.strip().upper()
    
    sensor_bytes = convert_hex_stream(clean_sensor)
    threshold_bytes = convert_hex_stream(clean_threshold)
    
    print(f"[SAFETY] Monitoring Sensor: {sensor_bytes.hex()} | Limit: {threshold_bytes.hex()}")


@app.command(name="kvm-gui")
def kvm_gui_command(
    display_mode: str = typer.Option("HEX_MATRIX", help="Interface layout style for the KVM console.")
):
    """Initializes the operator control console state from the Univac_Sperry_KVM_GUI layer."""
    match display_mode:
        case "HEX_MATRIX":
            print("[KVM] Launching Raw Hexadecimal Grid Matrix Display Console.")
            return
        case "LEGACY_TTY":
            print("[KVM] Launching Teletype TTY Terminal Emulator Stream.")
            return
            
    print(f"Error: Display mode '{display_mode}' is unsupported.", file=sys.stderr)
    raise typer.Exit(code=3)


if __name__ == "__main__":
    app()
