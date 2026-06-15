#!/usr/bin/env python3
"""
UNIVAC-IX Network Discovery, Deep Hardware Profiling & Integrity Core
Location: src/modules/univac_discovery_engine.py
"""

import os
import sys
import socket
import json
import re
import threading
import time
import subprocess
from pathlib import Path

# --- LOCKED RELATIVE WORKSPACE PATHS ---
# Resolves from src/modules/ up two levels to the Repository Root Folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent  
MASTER_VCF = BASE_DIR / "master_database.vcf"
LIBRARY_DIR = BASE_DIR / "storage_pipeline" / "hardware_node_library"
TEMPLATES_ROOT = BASE_DIR / "storage_pipeline" / "gantry_site_templates"

# Ensure all system pipeline target folders exist cleanly
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)


class DeepHardwareProfiler:
    @staticmethod
    def interrogate_device(ip: str, port: int) -> dict:
        """Connects safely to open channels to extract banners and classify computing appliances."""
        profile = {
            "ip_address": ip,
            "primary_interface_port": port,
            "architecture_class": "Unknown Appliance",
            "capabilities": [],
            "inferred_protocol": "RAW_STREAM",
            "last_interrogated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "firmware_hint": "No standard hardware banner response recorded."
        }

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((ip, port))
            
            probe = b"GET / HTTP/1.0\r\n\r\n" if port == 80 else b"\r\n"
            s.sendall(probe)
            banner = s.recv(512).decode('utf-8', errors='ignore').strip()
            s.close()
        except Exception:
            banner = ""

        # Device Heuristics Matrix
        if port == 502:
            profile["architecture_class"] = "Programmable Logic Controller (PLC)"
            profile["inferred_protocol"] = "Modbus/TCP"
            profile["capabilities"] = ["Coil_Control", "Register_Telemetry", "Industrial_Automation"]
            profile["firmware_hint"] = "Standard Fieldbus Register Map Active"
        elif port == 44818:
            profile["architecture_class"] = "Rockwell/Allen-Bradley Automation Unit"
            profile["inferred_protocol"] = "EtherNet/IP"
            profile["capabilities"] = ["Tag_Data_Sync", "CIP_Routing", "Industrial_Automation"]
            profile["firmware_hint"] = "Logix-Class Core Engine Interfaced"
        elif port == 23:
            profile["architecture_class"] = "Serial Terminal Server Gateway"
            profile["inferred_protocol"] = "Telnet"
            profile["capabilities"] = ["Serial_Bridge", "TTY_Relay", "Telegraphic_Intermediary"]
            if banner:
                profile["firmware_hint"] = banner[:80].replace("\n", " ").replace("\r", "")
        elif port == 22:
            profile["architecture_class"] = "Secure Shell Routing Controller"
            profile["inferred_protocol"] = "SSH"
            profile["capabilities"] = ["Encrypted_Console", "Remote_Configuration_Terminal"]
            if banner:
                profile["firmware_hint"] = banner[:60]
        elif port == 80:
            profile["architecture_class"] = "Embedded Network Management Interface"
            profile["inferred_protocol"] = "HTTP"
            profile["capabilities"] = ["Web_Administration", "REST_Configuration_Access"]
            if "Server:" in banner:
                server_type = re.search(r'Server:\s*(.+)$', banner, re.MULTILINE | re.IGNORECASE)
                profile["firmware_hint"] = server_type.group(1).strip() if server_type else "Embedded Web Server"
            elif banner:
                profile["firmware_hint"] = banner[:60].replace("\n", " ")

        return profile

    @staticmethod
    def register_profile_to_library(profile: dict):
        """Saves or updates a JSON hardware manifest file in the local Node Library folder."""
        safe_ip = profile["ip_address"].replace(".", "_")
        filename = f"node_profile_{safe_ip}.json"
        target_path = LIBRARY_DIR / filename

        if target_path.exists():
            try:
                with open(target_path, 'r', encoding='utf-8') as f:
                    old_profile = json.load(f)
                    old_profile.update(profile)
                    profile = old_profile
            except Exception:
                pass

        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=4)
        print(f"[💾] NODE LIBRARY ACCESS: Compiled hardware profile saved -> {filename}")


class UnivacNetworkMonitor:
    def __init__(self, subnet_override=None):
        self.discovered_nodes = {}
        self.lock = threading.Lock()
        self.base_subnet = subnet_override if subnet_override else self.detect_local_subnet()

    def detect_local_subnet(self) -> str:
        """Determines the local subnet routing path based on active network interfaces."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            ip_parts = local_ip.split('.')
            return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}."
        except Exception:
            return "192.168.1."

    def scan_port_target(self, ip_address: str, port_list: list):
        """Sweeps a target IP across vital system ports, spinning up the profiler on discovery."""
        for port in port_list:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.15)
                result = sock.connect_ex((ip_address, port))
                
                if result == 0:
                    sock.close()
                    print(f"\n[🔬] HARDWARE HIT: Detected device response at {ip_address}:{port}. Fingerprinting...")
                    profile = DeepHardwareProfiler.interrogate_device(ip_address, port)
                    DeepHardwareProfiler.register_profile_to_library(profile)
                    
                    with self.lock:
                        if ip_address not in self.discovered_nodes:
                            self.discovered_nodes[ip_address] = profile
                    break
                sock.close()
            except Exception:
                continue

    def crawl_immediate_network(self):
        """Sweeps all 254 active host slots on the current subnet using multi-threading."""
        print(f"[*] Commencing discovery sweep on subnet range: {self.base_subnet}0/24")
        common_ports = [22, 23, 80, 502, 44818]
        
        threads = []
        for host in range(1, 255):
            target_ip = f"{self.base_subnet}{host}"
            t = threading.Thread(target=self.scan_port_target, args=(target_ip, common_ports))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()

    def discover_surrounding_networks(self) -> list:
        """Parses local system OS routing maps and ARP structures to discover neighboring network paths."""
        print("[*] Interrogating kernel ARP cache matrices for alternative routing footprints...")
        gateways = []
        try:
            command = ["arp", "-a"] if sys.platform != "win32" else ["arp", "-g"]
            output = subprocess.check_output(command, stderr=subprocess.DEVNULL).decode('utf-8', errors='ignore')
            found_ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', output)
            
            for ip in found_ips:
                if ip.endswith('.1') or ip.endswith('.254') or ip.endswith('.2'):
                    if not ip.startswith(self.base_subnet) and ip != "255.255.255.255":
                        ip_prefix = ".".join(ip.split('.')[:3]) + "."
                        if ip_prefix not in gateways:
                            gateways.append(ip_prefix)
        except Exception as e:
            print(f"[-] Infrastructure diagnostic error: {e}")
            
        if gateways:
            print(f"[+] Located {len(gateways)} surrounding network subnets: {gateways}")
        return gateways

    def validate_node_ping(self, ip_address: str) -> bool:
        """Dispatches an OS-agnostic ICMP echo request to verify device availability."""
        param = "-n" if sys.platform == "win32" else "-c"
        timeout_param = "-w" if sys.platform == "win32" else "-W"
        timeout_val = "1000" if sys.platform == "win32" else "1"
        
        command = ["ping", param, "1", timeout_param, timeout_val, ip_address]
        try:
            response = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return response.returncode == 0
        except Exception:
            return False

    def run_database_audit_pass(self):
        """Combs the Master VCF, pings mapped network hosts, and rewrites online/offline statuses."""
        if not MASTER_VCF.exists():
            print("[-] Keep-alive audit bypassed: Master database file does not exist yet.")
            return

        print(f"[*] Auditing connection status logs in '{MASTER_VCF.name}' via ICMP matrix...")
        with open(MASTER_VCF, 'r', encoding='utf-8') as f:
            content = f.read()

        vcards = content.split("BEGIN:VCARD")
        updated_vcards = []
        timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")

        for card in vcards:
            if "END:VCARD" not in card:
                continue

            ip_match = re.search(r'TEL;TYPE=IP,DIRECT:(.+)$', card, re.MULTILINE)
            if ip_match:
                target_ip = ip_match.group(1).strip()
                print(f"    -> Auditing Node [{target_ip}]: ", end="", flush=True)
                
                is_online = self.validate_node_ping(target_ip)
                status_str = "ONLINE" if is_online else "OFFLINE"
                print(status_str)
card = re.sub(r'^X-UNIVAC-NODE-STATUS:.$', '', card, flags=re.MULTILINE)
card = re.sub(r'^X-UNIVAC-LAST-VALIDATED:.$', '', card, flags=re.MULTILINE)
status_extension = f"X-UNIVAC-NODE-STATUS:{status_str}\nX-UNIVAC-LAST-VALIDATED:{timestamp}\nEND:VCARD"
card = card.replace("END:VCARD", status_extension)
updated_vcards.append("BEGIN:VCARD" + card)
with open(MASTER_VCF, 'w', encoding='utf-8') as f:
f.write("".join(updated_vcards))
print("[+] Keep-alive status values synced to disk database.")
def reconcile_with_master_vcf(self):
"""Converts discovered node profiles into complete vCards and syncs them to the database."""
if not self.discovered_nodes:
return
existing_data = ""
if MASTER_VCF.exists():
with open(MASTER_VCF, 'r', encoding='utf-8') as f:
existing_data = f.read()
vcf_appends = []
for ip, prof in self.discovered_nodes.items():
if ip in existing_data:
continue
print(f"[+] Auto-Recovery Triggered! Injecting network node entry to database: {ip}")
clean_class = prof['architecture_class'].replace(' ', '_').upper()
vcf_card = [
"BEGIN:VCARD",
"VERSION:3.0",
f"FN:NODE-{clean_class}-{ip.split('.')[-1]}",
f"TEL;TYPE=IP,DIRECT:{ip}",
f"NOTE:Auto-profiled hardware link: {prof['firmware_hint']}",
f"X-UNIVAC-PLC-NODE:NET-{ip.split('.')[-1]}",
f"X-UNIVAC-NET-TYPE:{prof['inferred_protocol']}",
f"X-UNIVAC-NODE-STATUS:ONLINE",
f"X-UNIVAC-CAPABILITIES:{','.join(prof['capabilities'])}",
f"X-UNIVAC-LAST-VALIDATED:{prof['last_interrogated'].replace(' ', '_')}",
"END:VCARD\n"
]
vcf_appends.append("\n".join(vcf_card))
if vcf_appends:
with open(MASTER_VCF, 'a', encoding='utf-8') as f:
f.write("\n".join(vcf_appends))
print(f"[+] Successfully appended {len(vcf_appends)} newly recovered nodes to {MASTER_VCF.name}")
def run_complete_discovery_cycle(self):
print("\n=========================================================")
print(" UNIVAC-IX NETWORK INTEGRITY & DISCOVERY SWEEP")
print("=========================================================")
self.run_database_audit_pass()
self.crawl_immediate_network()
adjacent_subnets = self.discover_surrounding_networks()
for alt_net in adjacent_subnets:
secondary_scanner = UnivacNetworkMonitor(subnet_override=alt_net)
secondary_scanner.crawl_immediate_network()
with self.lock:
self.discovered_nodes.update(secondary_scanner.discovered_nodes)
self.reconcile_with_master_vcf()
print("=========================================================\n")
if name == "main":
scanner = UnivacNetworkMonitor()
if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
print("[*] Running in persistent network monitor mode (60-second intervals)...")
try:
while True:
scanner.run_complete_discovery_cycle()
time.sleep(60)
except KeyboardInterrupt:
print("\n[-] Background network monitor loop terminated gracefully.")
else:
scanner.run_complete_discovery_cycle()
