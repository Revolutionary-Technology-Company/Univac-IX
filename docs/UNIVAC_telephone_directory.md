UNIVAC-IX Master Directory & Telemetry Ingestion Engine
-------------------------------------------------------

Welcome to the official documentation for the UNIVAC-IX Master Directory Engine. This documentation outlines the system capabilities and onboarding procedures for integrating cross-era telecommunication infrastructure.

The UNIVAC-IX directory engine acts as a bridging layer between modern unified databases and mid-century mainframe computing networks. It translates standard corporate, industrial, and government directory structures into machine-level protocols utilized by legacy hardware systems.

* * * * *

🛠️ System Overview
-------------------

The engine converts modern alphanumeric formats into 1950s-era storage footprints while generating standard mobile-compatible address records (`.vcf`).

Core Architectural Layers
-------------------------

```
  [ Modern Dropzone ] ──► ( CSV / TXT / XLS / XLSX / PDF / SQL )
                                  │
                                  ▼
                     [ UNIVAC-IX Pipeline Monitor ]
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
[ Master Database vCard ]                        [ Transmitted Outbound ]
 - Android/iOS Sync Compatible                    - 6-Bit Excess-3 Streams
 - X-UNIVAC Telemetry Tags                        - Baudot/ITA2 AFSK Audio
 - Cross-System Data Maps                         - Hardware Serial Current Loops

```

1.  The Inbound Pipeline Monitor (`univac_pipeline_monitor.py`): Automatically scans a monitored file system dropzone. It extracts structured names, routing codes, addresses, and telecom properties from standard file formats.
2.  The Hardware Transformation Engine (`univac_directory_engine.py`): Structures raw string variables into 12-character computer words and encodes them into 6-bit Excess-3 (XS-3) streams.
3.  The Signaling Core (`univac_transmitter_core.py`): Reads database entries to output 5-bit Baudot/ITA2 AFSK audio waves or toggles physical serial hardware pins for telegraph current loops.

* * * * *

💾 Core Telemetry Specifications
--------------------------------

The repository translates arbitrary string assets into a standard, fixed physical data record layout derived from the 90-column Remington Rand punch card:

Fixed 72-Character Sub-Block Allocation
---------------------------------------

Every processed record maps out down to specific character bytes to align cleanly with hardware memory banks:

| Byte Span | Field Parameter | Description / Allocation Target |
| 01 -- 24 | `NAME FIELD` | First and last entity descriptors (Padded with spaces). |
| 25 -- 36 | `PHONE FIELD` | Cleansed digits, formatted to a 12-byte constraint. |
| 37 -- 48 | `PLC NODE` | Plant Location Code, device address, or routing key. |
| 49 -- 72 | `TELEMETRY BLOCK` | Packed string containing Baud rate, WPM, and RF Frequencies. |

6-Bit Excess-3 (XS-3) Target Reference
--------------------------------------

The engine translates raw strings character-by-character into binary bitstreams. This mapping shifts standard integer indices by a factor of 3 to align with historical computing architectures:

-   `0` $\rightarrow$ `000011`
-   `5` $\rightarrow$ `001000`
-   `9` $\rightarrow$ `001100`
-   `A` $\rightarrow$ `010100`
-   `[SPACE]` $\rightarrow$ `010010`

* * * * *

🚀 Quick-Start Onboarding Guide
-------------------------------

Follow these steps to establish an active ingestion dropzone pipeline on a new server.

1\. System Requirements & Environment
-------------------------------------

The deployment requires Python 3.8+. Initialize the virtual workspace and pull environmental requirements using your system terminal:

```
# Clone the repository framework
git clone https://github.com
cd Univac-IX

# Install mandatory file processing libraries
pip install watchdog openpyxl pypdf

```

2\. Scaffold the Storage File System
------------------------------------

Run the synchronization script once or execute the shell block below to generate the managed workspace folders:

```
mkdir -p storage_pipeline/inbound_dropzone
mkdir -p storage_pipeline/processed
mkdir -p storage_pipeline/failed
mkdir -p storage_pipeline/audio_feeds

```

3\. Launch the Background Monitor Daemon
----------------------------------------

To start real-time monitoring of incoming directories, spin up the persistent pipeline monitoring script:

```
python3 univac_pipeline_monitor.py

```

* * * * *

📥 Ingestion Reference Sheets (Data Formats)
--------------------------------------------

New clients can parse records into the database by placing raw datasets directly into `storage_pipeline/inbound_dropzone/`. The subsystem automatically routes processing based on the following formatting rules:

A. CSV / Spreadsheet Template (`.csv`, `.xlsx`)
-----------------------------------------------

When generating sheets from modern applications like Microsoft Excel or Google Sheets, structure the columns using clear headers in the first row.

```
name,phone,plc_node,address,telegraph_baud,rf_frequency
"ALPHA DEPOT CENTRALE","5551234567","PLC-8812","SECTOR 4 BLOCK A","45.45","14.090 MHz"
"BRAVO TRANSCEIVER","5559876543","PLC-0411","ANTENNA FARM B","110.00","7.040 MHz"

```

B. Flat Log Files or Scrapes (`.txt`, `.pdf`)
---------------------------------------------

If importing text logs or modern PDF documents, the ingestion loop skips headers and applies recursive regular expression passes. The regex isolates standard telephone string matrices, designating adjacent strings as corporate tracking labels.

C. Legacy Binary Images (`.bin`)
--------------------------------

To process physical punch cards converted into binary images, supply raw stream collections formatted in continuous 90-byte boundaries matching original Remington Rand grid schemas.

* * * * *

📤 Integrated vCard (`.vcf`) Structural Export
----------------------------------------------

The output file generated in your root application path (`master_database.vcf`) complies with vCard 3.0 specs. This allows modern tools like Android OS, iOS, and database frameworks to parse data alongside legacy extensions.

An exported contact entry contains standard fields along with injected machine telemetry parameters:

```
BEGIN:VCARD
VERSION:3.0
FN:ALPHA DEPOT CENTRALE
TEL;TYPE=CELL,VOICE,PSTN:5551234567
ADR;TYPE=WORK:;;SECTOR 4 BLOCK A;;;;
X-UNIVAC-PLC-NODE:PLC-8812
X-UNIVAC-TELEGRAPH-BAUD:45.45
X-UNIVAC-RF-FREQUENCY:14.090 MHz
X-UNIVAC-WORD-LAYOUT:ALPHA DEPOT ,CENTRALE    ,5551234567  ,PLC-8812    ,B:45.45/W:60/F:14.090
X-UNIVAC-XS3-STREAM:0101000111110101100101110101000100100101110110001000101000111010111010010110010101011110011010011100011000010010010010010010010010010010010010010010
END:VCARD

```

* * * * *

📈 Next Steps & System Configuration
------------------------------------

Once your pipeline is active, you can adapt your ingestion paths for your specific environment:

-   To link production databases, open `univac_transmitter_core.py` and modify `ingest_from_sql()` with your local SQL Server connection strings.
-   To connect physical hardware equipment like relays, modify the COM port identifiers within `transmit_via_serial_switching()`.
-   If you have any integration questions or want to see Docker deployment examples, open an issue in the Univac-IX Repository.
