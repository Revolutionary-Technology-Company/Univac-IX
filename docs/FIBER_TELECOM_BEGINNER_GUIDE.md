# 🌌 Mastering the UNIVAC-IX Headless Fiber Optic Mainframe
## Quick-Start Integration Guide for Next-Gen Optical Telemetry Processing

Welcome to **UNIVAC-IX**—the world’s most powerful, headless, mathematical light calculation mainframe. Built natively for zero-GUI high-speed execution environments, UNIVAC-IX processes raw optical telemetry arrays (such as OTDR traces and spectrometer data matrices) in real time. 

By offloading complex physics algorithms directly onto isolated worker threads and compiling dynamic material indexes from an underlying Excel-based abstract syntax tree (AST), UNIVAC-IX achieves maximal computation speeds.

This guide will teach you how to initialize the mainframe, stream raw fiber instrumentation data, and read the real-time standardized JSON telemetry output.

---

## 🚀 1. Architectural Setup

UNIVAC-IX operates purely via standard inputs and outputs (`stdin` / `stdout`). This keeps your computational layer lightweight and completely independent of frontend rendering latency.

Ensure your module repository contains the following architecture:
```text
Univac-IX/
├── assets/
│   └── data/
│       ├── elements_period_table_index.xlsx   # Master materials/chemical index
│       └── compiled_ptable_metadata.json      # Pre-compiled formula graph
└── src/
    └── modules/
        └── light_app/
            ├── light_worker.js                # High-speed math worker thread
            └── app_interface.js               # Mainframe engine orchestrator
```

---

## ⚡ 2. Launching Your First Headless Session

To spin up the mainframe engine without any interface bottlenecks, initialize the orchestrator from your system terminal root:

```bash
node src/modules/light_app/app_interface.js
```

### Capturing the Output Stream
Because the mainframe outputs pure JSON strings straight to the system console, you can pipe the live calculation matrix into a persistent storage file for logging and external processing:

```bash
node src/modules/light_app/app_interface.js > assets/data/telecom_output_stream.json
```

---

## 📊 3. Understanding the Standardized Output Schema

Every 15 milliseconds, the mainframe completes an entire sweep of your fiber optics link. It runs real-time wave equations to calculate exact distance profiles, localized attenuation anomalies, and fault event vectors.

Here is a breakdown of the standard JSON telemetry data your integration bridges will read from `stdout`:

```json
{
  "timestamp": 1781559322000,
  "telemetry": {
    "totalMonitoredDistanceMeters": 32005.45,
    "anomalyEventCount": 1,
    "coreMaterialActive": "Glass_Silica",
    "spectralHexSignature": "#38bdf8"
  },
  "traceMatrix": [
    {
      "index": 20,
      "distanceMeters": 1000.15,
      "amplitudeDb": 48.50,
      "status": "Mechanical or Fusion Splice Detected"
    }
  ]
}
```

### Key Metrics Decoded:
*   **`distanceMeters`**: Computed via high-fidelity Time of Flight (ToF) equations divided by the core material's dynamic index of refraction.
*   **`status`**: Rayleigh backscatter drops are cross-analyzed instantly. Drop steps between `0.5 dB` and `3.0 dB` automatically trigger localized splice alerts.

---

## 🛠️ 4. Basic Automation Wiring Pattern

To harness the true performance of this mainframe, use this simple script pattern to intercept the live data output and execute automated network routing logic when anomalies occur:

```javascript
import { spawn } from 'child_process';

// Launch the headless mainframe subprocess
const mainframe = spawn('node', ['./src/modules/light_app/app_interface.js']);

mainframe.stdout.on('data', (data) => {
    const lines = data.toString().split('\n');
    for (const line of lines) {
        if (!line.trim()) continue;
        
        try {
            const telemetry = JSON.parse(line);
            
            // Log real-time telemetry straight to your custom interface
            console.log(`[LINK MONITOR] Core: ${telemetry.telemetry.coreMaterialActive} | Anomalies: ${telemetry.telemetry.anomalyEventCount}`);
            
        } catch (e) {
            // Handle fragmented stream allocations gracefully
        }
    }
});
```

---

## 🎯 Next Steps
Ready to unleash advanced wave-optics algorithms? Advance to the **[Advanced Commands & Physics Configurations Guide](FIBER_TELECOM_ADVANCED_GUIDE.md)** to learn how to inject runtime material alterations via `stdin` and monitor deep chromatic dispersion and micro-void fractures.
