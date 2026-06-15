#!/bin/bash
# UNIVAC-IX Master Automation Loop
# Launches background telemetry workers, ASGI web bridge, and Curses TUI.

echo "=== INITIALIZING UNIVAC-IX MAIN SEQUENCE ==="

# 1. Define cleanup function for graceful shutdown
cleanup_processes() {
    echo -e "\n[!] Teardown Initiated. Terminating background Univac nodes..."
    
    # Kill the Web Bridge and any background Python workers
    kill $WEB_PID 2>/dev/null
    kill $DISCOVERY_PID 2>/dev/null
    
    echo "[!] Univac-IX Mainframe Offline."
    exit 0
}

# 2. Bind the cleanup function to the SIGINT (Ctrl+C) and EXIT signals
trap cleanup_processes SIGINT EXIT

# 3. Ignite Background Nodes
echo "[*] Spooling Network Discovery Engine in background..."
python3 src/modules/univac_discovery_engine.py &
DISCOVERY_PID=$!

echo "[*] Spooling Sperry KVM Web Bridge in background (Port 8080)..."
python3 src/modules/univac_kvm_web_bridge.py &
WEB_PID=$!

# Give the background workers 2 seconds to bind to their ports before launching the GUI
sleep 2

# 4. Launch the Primary Foreground UI
echo "[*] Handing over terminal buffer to Mainframe GUI..."
python3 src/modules/univac_mainframe_gui.py

# 5. The script waits here until the user presses [Q] in the GUI. 
# Once the Python GUI exits, the trap fires and kills the background workers.
