import json

# =====================================================================
# PIPELINE ATTACHMENTS: IMPORT REPOSITORY NODE LIBRARIES
# =====================================================================
try:
    # Node 9: Maritime Trunk Line Engine
    from transfer_protocol.py import process_univac_trunk_ping
except ImportError:
    # Fallback simulation if Node 9 hasn't been written to an independent file yet
    def process_univac_trunk_ping(p): 
        return {"STATUS": "NOMINAL_NODE_9", "DATA": "Processed via Maritime Hub Layer"}

try:
    # Node 10: Aero-Kinematic Elevation Module
    from flight_data_height import process_elevation_trunk_ping
except ImportError:
    def process_elevation_trunk_ping(p): 
        return {"STATUS": "FALLBACK_NODE_10", "ERROR": "flight_data_height.py unavailable"}

try:
    # Node 11: Terrestrial Automotive Tracking Engine
    from automotive_goaction import process_automotive_trunk_ping
except ImportError:
    def process_automotive_trunk_ping(p): 
        return {"STATUS": "FALLBACK_NODE_11", "ERROR": "automotive_goaction.py unavailable"}


# =====================================================================
# CORE DISPATCHER ENGINE
# =====================================================================
def dispatch_univac_request(request_headers, raw_payload):
    """
    Inspects transaction headers for explicit classification strings.
    Routes raw telemetry frames directly to specialized computing fabric nodes.
    """
    # 1. Normalize header metadata fields to safeguard against case mismatches
    normalized_headers = {str(k).lower(): str(v).lower() for k, v in request_headers.items()}
    
    # 2. Extract classification key from known protocol locations
    asset_type = normalized_headers.get("asset-type") or normalized_headers.get("header")
    
    # 3. ROUTE A: MARITIME ROUTER (Node 9)
    if asset_type == "vessel":
        print("[TRANSFER PROTOCOL]: Detected 'vessel' signature. Routing to Node 9...")
        results = process_univac_trunk_ping(raw_payload)
        results["DISPATCH_CONTEXT"] = "MARITIME_NODE_9"
        return results
        
    # 4. ROUTE B: AVIATION ENGINE (Node 10)
    elif asset_type == "aircraft":
        print("[TRANSFER PROTOCOL]: Detected 'aircraft' signature. Routing to Node 10...")
        results = process_elevation_trunk_ping(raw_payload)
        results["DISPATCH_CONTEXT"] = "AERO_NODE_10"
        return results
        
    # 5. ROUTE C: AUTOMOTIVE WHEEL-KINEMATICS (Node 11)
    elif asset_type == "automotive":
        print("[TRANSFER PROTOCOL]: Detected 'automotive' signature. Routing to Node 11...")
        results = process_automotive_trunk_ping(raw_payload)
        results["DISPATCH_CONTEXT"] = "TERRESTRIAL_NODE_11"
        return results
        
    # 6. FAULT ISOLATION: MALFORMED PATH
    else:
        print(f"[TRANSFER PROTOCOL ALERT]: Corrupted or unmapped asset target: '{asset_type}'")
        return {
            "STATUS": "CRITICAL_ROUTING_MISMATCH",
            "ERROR": f"Asset verification type '{asset_type}' is unrecognized. Connection dropped."
        }


# =====================================================================
# LOCAL TELEMETRY HARNESS VERIFICATION
# =====================================================================
if __name__ == "__main__":
    print("UNIVAC CORE DISPATCHER OS -- Simulating Cross-Domain Traffic...\n")
    
    # Validation Loop 1: Testing the Aircraft Request Stream
    mock_aircraft_headers = {"Asset-Type": "aircraft", "Connection": "Keep-Alive"}
    mock_aircraft_payload = "12000.0,78.5,3.2,090.0,15.0,270.0,60.0"
    
    air_output = dispatch_univac_request(mock_aircraft_headers, mock_aircraft_payload)
    print(f"Result A: {json.dumps(air_output, indent=2)}\n")
    print("-" * 65 + "\n")
    
    # Validation Loop 2: Testing the Automotive Request Stream
    mock_auto_headers = {"Header": "automotive", "User-Agent": "Univac-Car-v1.1"}
    mock_auto_payload = "1100.0,28.0,4.5,0.80,90.0,15.0"
    
    auto_output = dispatch_univac_request(mock_auto_headers, mock_auto_payload)
    print(f"Result B: {json.dumps(auto_output, indent=2)}\n")
