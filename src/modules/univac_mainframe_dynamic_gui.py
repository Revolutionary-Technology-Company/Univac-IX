#!/usr/bin/env python3
"""
UNIVAC-IX Mainframe Terminal Graphical Interface (KVM)
Location: src/modules/univac_mainframe_gui.py

FEATURES:
- Dynamic Node Detection (Scans /src/modules/ for active co-processors)
- Multi-View TUI (Main Dashboard, Subsystem Registry, Live Telemetry)
- Curses crash-protection & window-resize auto-reflow
"""

import os
import sys
import time
import curses
import random
from pathlib import Path

# --- DYNAMIC PATH RESOLUTION ---
MODULE_DIR = Path(__file__).resolve().parent
ROOT_DIR = MODULE_DIR.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# --- DYNAMIC NODE DETECTION ---
def get_installed_nodes() -> list:
    """Scans the modules folder to dynamically detect installed infrastructure nodes."""
    nodes = []
    excluded = ["__init__.py", "univac_mainframe_gui.py", "univac_kvm_launcher.py", "univac_pipeline_monitor.py", "gantry_integration_bridge.py", "univac_kvm_web_bridge.py"]
    
    if MODULE_DIR.exists():
        for file in MODULE_DIR.glob("*.py"):
            if file.name not in excluded:
                # Format name nicely (e.g., tokamak_plasma_containment_core -> Tokamak Plasma Containment Core)
                clean_name = file.stem.replace("_", " ").title()
                nodes.append(clean_name)
    return sorted(nodes)

def generate_simulated_log() -> str:
    """Generates random infrastructure telemetry for the KVM log buffer."""
    events = [
        "[AEGIS] Malicious PLC Payload Dropped - Origin: Unknown",
        "[TOKAMAK] Plasma Beta at 0.04 - Magnetic Confinement Stable",
        "[HFT_CORE] Flash Crash Detected on NASDAQ - Circuit Breakers Armed",
        "[STRATOSPHERE] Fleet 2 injecting SO2 at 22km altitude - Albedo shift nominal",
        "[BGP_DEFENSE] Detected AS Path anomaly - Null routing traffic",
        "[DART_TSUNAMI] Deep ocean pressure stable across Pacific Ring",
        "[VACTRAIN] Pod NY-LA-01 cleared for Mach 1.5 magnetic acceleration",
        "[SEED_VAULT] LN2 injection active. Permafrost delta -0.5C"
    ]
    return f"[{time.strftime('%H:%M:%S')}] {random.choice(events)}"

def draw_interface(stdscr):
    # Setup Curses Environment
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(200) # 200ms tick rate (5Hz)

    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_GREEN, -1)   # Nominal
        curses.init_pair(2, curses.COLOR_RED, -1)     # Critical
        curses.init_pair(3, curses.COLOR_CYAN, -1)    # Headers
        curses.init_pair(4, curses.COLOR_YELLOW, -1)  # Warnings
        curses.init_pair(5, curses.COLOR_MAGENTA, -1) # Titles

    # State Variables
    current_view = "MAIN"
    system_logs = []
    installed_nodes = get_installed_nodes()
    scroll_offset = 0

    while True:
        # Input Handling
        c = stdscr.getch()
        if c in [ord('q'), ord('Q')]:
            break
        elif c in [ord('m'), ord('M')]:
            current_view = "MAIN"
        elif c in [ord('n'), ord('N')]:
            current_view = "NODES"
        elif c in [ord('l'), ord('L')]:
            current_view = "LOGS"
        elif c == curses.KEY_DOWN and current_view == "NODES":
            if scroll_offset < len(installed_nodes) - 10: scroll_offset += 1
        elif c == curses.KEY_UP and current_view == "NODES":
            if scroll_offset > 0: scroll_offset -= 1

        # Simulate background activity
        if random.random() > 0.7:
            system_logs.append(generate_simulated_log())
            if len(system_logs) > 50: 
                system_logs.pop(0) # Keep log buffer trimmed

        height, width = stdscr.getmaxyx()
        stdscr.erase()

        # --- PROTECTED RENDER LOOP ---
        try:
            # HEADER
            header_text = f" UNIVAC-IX PLANETARY MAINFRAME | VIEW: {current_view} | NODES: {len(installed_nodes)} "
            stdscr.attron(curses.A_REVERSE | curses.color_pair(3))
            stdscr.addstr(0, 0, header_text.ljust(width)[:width])
            stdscr.attroff(curses.A_REVERSE | curses.color_pair(3))

            # VIEWS
            if current_view == "MAIN":
                # ASCII Art Title
                title = [
                    "█  █ █▄ █ █ █  █ ▄▀▄ ▄▀▀   █ ▀▄▀",
                    "▀▄▄▀ █ ▀█ █  ▀▄▀ █▀█ ▀▄▄   █ █ █"
                ]
                for idx, line in enumerate(title):
                    if idx + 2 < height:
                        stdscr.addstr(idx + 2, 2, line, curses.color_pair(5) | curses.A_BOLD)

                if 5 < height:
                    stdscr.addstr(5, 2, "SYSTEM STATUS:", curses.color_pair(3) | curses.A_BOLD)
                    stdscr.addstr(5, 17, "[ DEFCON 4 - GLOBAL INFRASTRUCTURE NOMINAL ]", curses.color_pair(1))

                if 7 < height:
                    stdscr.addstr(7, 2, "RECENT TELEMETRY:", curses.color_pair(3) | curses.A_BOLD)
                    log_row = 8
                    # Show last few logs
                    for log in system_logs[-min(10, height - 12):]:
                        if log_row < height - 2:
                            stdscr.addstr(log_row, 4, log[:width-6])
                            log_row += 1

            elif current_view == "NODES":
                stdscr.addstr(2, 2, "REGISTERED INFRASTRUCTURE CO-PROCESSORS:", curses.color_pair(3) | curses.A_BOLD)
                row = 4
                
                visible_nodes = installed_nodes[scroll_offset : scroll_offset + (height - 8)]
                
                for node in visible_nodes:
                    if row < height - 2:
                        # Simulate random node states for UI visual appeal
                        state = random.choice([("ONLINE", 1)] * 10 + [("STANDBY", 4), ("CALCULATING", 3)])
                        stdscr.addstr(row, 4, f"[{state[0].ljust(11)}]", curses.color_pair(state[1]) | curses.A_BOLD)
                        stdscr.addstr(row, 18, f"- {node}"[:width-20])
                        row += 1
                
                if row < height - 2 and len(installed_nodes) > height - 8:
                    stdscr.addstr(row + 1, 4, "(Use UP/DOWN arrows to scroll)", curses.color_pair(4))

            elif current_view == "LOGS":
                stdscr.addstr(2, 2, "RAW MAINFRAME TELEMETRY STREAM:", curses.color_pair(3) | curses.A_BOLD)
                row = 4
                for log in system_logs[-(height-6):]:
                    if row < height - 2:
                        stdscr.addstr(row, 4, log[:width-6])
                        row += 1

            # FOOTER
            footer_text = " [M] MAIN | [N] NODE REGISTRY | [L] LOG STREAM | [UP/DN] SCROLL | [Q] SHUTDOWN "
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(height - 1, 0, footer_text.ljust(width)[:width])
            stdscr.attroff(curses.A_REVERSE)

        except curses.error:
            # Swallow dynamic resize errors mid-frame
            pass

        stdscr.refresh()

def main(stdscr):
    draw_interface(stdscr)

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\n[UNIVAC-IX] Mainframe KVM Interface closed. Standard bash environment restored.\n")
