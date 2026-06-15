#!/usr/bin/env python3
"""
UNIVAC-IX Master Directory Engine
Converts modern and legacy data sources (CSV, TXT, 720-char Blocks) into an 
Android-compatible .vcf file embedded with UNIVAC 6-bit XS-3 telemetry metadata.
"""

import csv
import json
import os
import re

# Authentic 6-bit Excess-3 (XS-3) Character Mapping Table
# Maps characters to their exact 1950s UNIVAC binary string representations.
XS3_TABLE = {
    '0': '000011', '1': '000100', '2': '000101', '3': '000110', '4': '000111',
    '5': '001000', '6': '001001', '7': '001010', '8': '001011', '9': '001100',
    'A': '010100', 'B': '010101', 'C': '010110', 'D': '010111', 'E': '011000',
    'F': '011001', 'G': '011010', 'H': '011011', 'I': '011100', 'J': '011101',
    'K': '011110', 'L': '011111', 'M': '100000', 'N': '100001', 'O': '100010',
    'P': '100011', 'Q': '100100', 'R': '100101', 'S': '101010', 'T': '101011',
    'U': '101100', 'V': '101101', 'W': '101110', 'X': '101111', 'Y': '110000',
    'Z': '110001', ' ': '010010', '-': '001101', ',': '111010', '.': '111100'
}

def to_xs3_stream(text: str) -> str:
    """Converts a standard text string into a contiguous 6-bit XS-3 binary stream."""
    binary_stream = []
    for char in text.upper():
        if char in XS3_TABLE:
            binary_stream.append(XS3_TABLE[char])
        else:
            binary_stream.append(XS3_TABLE[' ']) # Fallback to space if character unknown
    return "".join(binary_stream)

def build_fixed_word_layout(name: str, plc: str, address: str, phone: str) -> dict:
    """
    Structures raw fields into a traditional 90-character/72-character layout
    and generates the matching UNIVAC word architecture metadata.
    """
    # Pad and format fields according to 1950s record parameters
    clean_name = name.strip().upper()[:35].ljust(35)
    clean_plc = plc.strip().upper()[:5].ljust(5)
    clean_address = address.strip().upper()[:35].ljust(35)
    clean_phone = re.sub(r'\D', '', phone)[:15].ljust(15)
    
    raw_record = f"{clean_name}{clean_plc}{clean_address}{clean_phone}"
    
    # Split the raw string stream into standard UNIVAC 12-character words
    words = [raw_record[i:i+12] for i in range(0, len(raw_record), 12)]
    
    return {
        "raw_record": raw_record,
        "words": words,
        "xs3_stream": to_xs3_stream(raw_record)
    }

def parse_720_block(block_data: str) -> list:
    """
    Parses a raw 720-character UNISERVO tape block dump.
    Assumes an 8-record layout per block (90 characters per personnel entry).
    """
    records = []
    if len(block_data) < 720:
        block_data = block_data.ljust(720)
        
    for i in range(0, 720, 90):
        chunk = block_data[i:i+90]
        if chunk.strip() == "" or chunk.count(' ') == 90:
            continue
            
        name = chunk[0:35].strip()
        plc = chunk[35:40].strip()
        address = chunk[40:75].strip()
        phone = chunk[75:90].strip()
        
        if name or phone:
            records.append({
                "name": name,
                "plc": plc,
                "address": address,
                "phone": phone
            })
    return records

def generate_vcard_entry(record: dict) -> str:
    """
    Generates an Android/iOS compatible vCard string injected with custom 
    X-UNIVAC extensions for integration with legacy systems like CRAY and PLCs.
    """
    meta = build_fixed_word_layout(
        record.get("name", "UNKNOWN"),
        record.get("plc", "000"),
        record.get("address", ""),
        record.get("phone", "")
    )
    
    vcf = []
    vcf.append("BEGIN:VCARD")
    vcf.append("VERSION:3.0")
    vcf.append(f"FN:{record.get('name', 'UNKNOWN').strip()}")
    vcf.append(f"TEL;TYPE=CELL,VOICE:{record.get('phone', '').strip()}")
    vcf.append(f"ADR;TYPE=WORK:;;{record.get('address', '').strip()};;;;")
    vcf.append(f"ORG:UNIVAC Plant;PLC-{record.get('plc', '000').strip()}")
    
    # Custom X-UNIVAC headers for legacy hardware and machine-language parsing
    vcf.append(f"X-UNIVAC-PLC:{record.get('plc', '000').strip()}")
    vcf.append(f"X-UNIVAC-WORD-LAYOUT:{','.join(meta['words'])}")
    vcf.append(f"X-UNIVAC-XS3-STREAM:{meta['xs3_stream']}")
    vcf.append(f"X-UNIVAC-RECORD-RAW:{meta['raw_record']}")
    
    vcf.append("END:VCARD")
    return "\n".join(vcf)

def scan_and_convert(input_file: str, output_vcf: str):
    """
    Detects the file type based on content structure, parses directory items, 
    and appends them directly into the target master .vcf database file.
    """
    found_records = []
    
    if not os.path.exists(input_file):
        print(f"Error: Input path {input_file} does not exist.")
        return

    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Strategy 1: Detect 720-character tape block formatting
    if len(content) >= 720 and not ',' in content and not '\t' in content:
        print(f"[*] Processing {input_file} as a legacy UNIVAC 720-Character Block File...")
        # Break content into individual 720-character blocks
        blocks = [content[i:i+720] for i in range(0, len(content), 720)]
        for b in blocks:
            found_records.extend(parse_720_block(b))
            
    # Strategy 2: Process as a structured CSV/Text layout
    else:
        print(f"[*] Scanning {input_file} as flat text/CSV layout...")
        f.seek(0)
        try:
            reader = csv.DictReader(f)
            # Check for common header naming schemas
            headers = [h.lower() for h in reader.fieldnames] if reader.fieldnames else []
            if 'name' in headers or 'phone' in headers:
                for row in reader:
                    found_records.append({
                        "name": row.get('name', row.get('NAME', 'UNKNOWN')),
                        "plc": row.get('plc', row.get('PLC', '000')),
                        "address": row.get('address', row.get('ADDRESS', '')),
                        "phone": row.get('phone', row.get('PHONE', ''))
                    })
            else:
                # Fallback Regex scanning for unformatted text logs
                f.seek(0)
                for line in f:
                    # Regex searching for basic phone patterns: e.g., 555-1234 or (555) 123-4567
                    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', line)
                    if phone_match:
                        phone = phone_match.group(0)
                        # Extract string segments around the number as name candidates
                        name_candidate = line.replace(phone, "").strip(",;\t\n\r ")
                        found_records.append({
                            "name": name_candidate if name_candidate else "Auto Detected",
                            "plc": "000",
                            "address": "Extracted from text logs",
                            "phone": phone
                        })
        except Exception as e:
            print(f"[-] Parsing error encountered: {e}")

    # Write out the structural entries to the VCF database file
    if found_records:
        with open(output_vcf, 'a', encoding='utf-8') as out_f:
            for rec in found_records:
                out_f.write(generate_vcard_entry(rec) + "\n")
        print(f"[+] Successfully converted {len(found_records)} records into {output_vcf}")
    else:
        print("[-] No valid directory records detected in this file sample.")

if __name__ == "__main__":
    # Example execution scaffolding for emulator environments
    import sys
    if len(sys.argv) < 3:
        print("Usage: python univac_directory_engine.py <input_source_file> <output_database.vcf>")
    else:
        scan_and_convert(sys.argv[1], sys.argv[2])
