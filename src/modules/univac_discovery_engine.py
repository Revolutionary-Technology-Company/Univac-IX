#!/usr/bin/env python3
"""
UNIVAC-IX Network Discovery, Auto-Recovery & Ping Validation Engine
1. Scans immediate local networks and surrounding subnets for connected devices.
2. Identifies third-party industrial automation equipment (PLCs, terminal servers).
3. Auto-recovers missing connections into the master .vcf database.
4. Performs regular ping validations to audit online/offline node status.
"""

import os
import sys
import socket
import subprocess
import re
import threading
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MASTER_VCF = BASE_DIR / "master_database.vcf"

class UnivacNetworkScanner:
    def __init__(self, subnet_override=None):
        self.discovered_nodes = {}
        self.lock = threading.Lock()
        
        if subnet_override:
            self.base_subnet = subnet_override
        else:
            self.base_subnet = self.detect_local_subnet()
            
    def detect_local_subnet(self) -> str:
        """Determines the immediate local subnet layout based on active network card routing."""
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
        """Attempts connection handshakes to map specific protocol types."""
        for port in port_list:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.15)
                result = sock.connect_ex((ip_address, port))
                
                if result == 0:
                    device_type = "Generic Hardware Link"
                    if port == 502:     device_type = "Industrial Modbus PLC Node"
                    elif port == 23:    device_type = "Legacy Telnet Terminal Node"
                    elif port == 80:    device_type = "HTTP Device Configuration Page"
                    elif port == 22:    device_type = "Secure Shell Routing Controller"
                    elif port == 44818: device_type = "EtherNet/IP Automation PLC"
                    
                    with self.lock:
                        if ip_address not in self.discovered_nodes:
                            self.discovered_nodes[ip_address] = {
                                "ip": ip_address,
                                "type": device_type,
                                "port_trigger": port,
                                "detected_at": time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                    sock.close()
                    break
                sock.close()
            except Exception:
                continue

    def crawl_immediate_network(self):
        """Sweeps the immediate IP scope space across 254 active host slots."""
        print(f"[*] Sweeping local sub-network footprint: {self.base_subnet}0/24")
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
        """Parses operating system routing matrices to identify gateway neighbors."""
        print("[*] Analyzing kernel routing footprints and surrounding hardware gateways...")
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
            print(f"[-] System metrics query error: {e}")
        return gateways

    def auto_recover_lost_connections(self):
        """Compares discovered nodes against existing entries and logs lost elements."""
        if not self.discovered_nodes:
            return

        existing_records = ""
        if MASTER_VCF.exists():
            with open(MASTER_VCF, 'r', encoding='utf-8') as f:
                existing_records = f.read()

        vcf_append_buffer = []
        for ip, metadata in self.discovered_nodes.items():
            if ip in existing_records:
                continue
                
            print(f"[+] Recovered Connection! Syncing node to master directory: {ip} -> {metadata['type']}")
            vcf_card = [
                "BEGIN:VCARD",
                "VERSION:3.0",
                f"FN:NET-{metadata['type'].replace(' ', '_').upper()}-{ip.split('.')[-1]}",
                f"TEL;TYPE=IP,DIRECT:{ip}",
                f"NOTE:Auto-recovered network connection via sweep engine mapping.",
                f"X-UNIVAC-PLC-NODE:NET-{ip.split('.')[-1]}",
                f"X-UNIVAC-NET-TYPE:{metadata['type']}",
                f"X-UNIVAC-NODE-STATUS:ONLINE",
                f"X-UNIVAC-LAST-VALIDATED:{metadata['detected_at'].replace(' ', '_')}",
                "END:VCARD\n"
            ]
            vcf_append_buffer.append("\n".join(vcf_card))

        if vcf_append_buffer:
            with open(MASTER_VCF, 'a', encoding='utf-8') as f:
                f.write("\n".join(vcf_append_buffer))
            print(f"[+] Appended {len(vcf_append_buffer)} new network nodes into {MASTER_VCF.name}")

    # -------------------------------------------------------------
    # NEW CORE METHOD: PING VALIDATION LAYER
    # -------------------------------------------------------------
    
    def validate_node_ping(self, ip_address: str) -> bool:
        """Sends a standard OS ICMP echo request to verify if a node is reachable."""
        # Adjust flags for Windows vs Linux/macOS architectures
        param = "-n" if sys.platform == "win32" else "-c"
        timeout_param = "-w" if sys.platform == "win32" else "-W"
        timeout_val = "1000" if sys.platform == "win32" else "1"
        
        command = ["ping", param, "1", timeout_param, timeout_val, ip_address]
        try:
            # Execute ping command suppress terminal output loops
            response = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return response.returncode == 0
        except Exception:
            return False

    def run_database_audit_pass(self):
        """Parses the Master VCF, extracts target IP pointers, and syncs online/offline status."""
        if not MASTER_VCF.exists():
            print("[-] Audit failed: No master database .vcf file found to process.")
            return

        print(f"\n[*] Auditing database inventory: '{MASTER_VCF.name}' via ICMP ping matrix...")
        with open(MASTER_VCF, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split file cleanly into distinct component vCards
        vcards = content.split("BEGIN:VCARD")
        updated_vcards = []
        timestamp = time.strftime("%Y-%m-%d_%H:%M:%S")

        for card in vcards:
            if "END:VCARD" not in card:
                continue

            # Isolate the IP address mapping within the telephone node layers
            ip_match = re.search(r'TEL;TYPE=IP,DIRECT:(.+)$', card, re.MULTILINE)
            if ip_match:
                target_ip = ip_match.group(1).strip()
                print(f"[*] Pinging node tracking path -> [{target_ip}]... ", end="", flush=True)
                
                is_online = self.validate_node_ping(target_ip)
                status_str = "ONLINE" if is_online else "OFFLINE"
                print(status_str)

                # Strip preexisting status tracking parameters to prevent duplicates
                card = re.sub(r'^X-UNIVAC-NODE-STATUS:.*$', '', card, flags=re.MULTILINE)
                card = re.sub(r'^X-UNIVAC-LAST-VALIDATED:.*$', '', card, flags=re.MULTILINE)

                # Inject newly audited status strings right before the card boundary ends
                status_extension = f"X-UNIVAC-NODE-STATUS:{status_str}\nX-UNIVAC-LAST-VALIDATED:{timestamp}\nEND:VCARD"
                card = card.replace("END:VCARD", status_extension)

            # Rebuild clean item segments
            updated_vcards.append("BEGIN:VCARD" + card)

        # Rewrite structural database state safely back to disk assets
        with open(MASTER_VCF, 'w', encoding='utf-8') as f:
            f.write("".join(updated_vcards))
        print("[+] Network health audit complete. Database matrix updated.")

    def run_complete_discovery_cycle(self):
        """Runs an integrated loop path mapping network status arrays."""
        print("\n=== STARTING UNIVAC-IX NETWORK INTEGRITY SWEEP ===")
        
        # 1. Audit status of already registered network hardware elements
        self.run_database_audit_pass()
        
        # 2. Sweep local scopes for any newly introduced components
        self.crawl_immediate_network()
        
        # 3. Handle secondary subnets
        adjacent_nets = self.discover_surrounding_networks()
        for alternate_subnet in adjacent_nets:
            secondary_scanner = UnivacNetworkScanner(subnet_override=alternate_subnet)
secondary_scanner.crawl_immediate_network()
with self.lock:
self.discovered_nodes.update(secondary_scanner.discovered_nodes)
# 4. Bind newly discovered elements to database entries
self.auto_recover_lost_connections()
print("=== NETWORK MONITOR PASS FINISHED ===")
if name == "main":
scanner = UnivacNetworkScanner()
if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
print("[*] Monitoring system initialized in persistent telemetry state...")
try:
while True:
scanner.run_complete_discovery_cycle()
time.sleep(30) # Perform network matrix validations every 30 seconds
except KeyboardInterrupt:
print("[-] Monitor script terminated by user command.")
else:
scanner.run_complete_discovery_cycle()
