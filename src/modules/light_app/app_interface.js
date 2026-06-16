/**
 * Headless Core Broker for Univac-IX Light Engine
 * Routes raw optical arrays straight to the calculation matrix worker.
 */

const mainframeWorker = new Worker(
    new URL('./light_worker.js', import.meta.url), 
    { type: 'module' }
);

// Configuration state targets for the mathematical equations
let currentTargetState = {
    element: "Titanium",
    electrons: 22,
    charge: 0
};

// Initialize the computing stack automatically on file execution
(() => {
    console.log("[Mainframe Core] Spawning Headless Light Engine Processing Thread...");
    
    mainframeWorker.postMessage({
        action: 'INITIALIZE_MAINFRAME',
        payload: { jsonUrl: '../../assets/data/compiled_ptable_metadata.json' }
    });

    mainframeWorker.onmessage = (event) => {
        const { status, data, error } = event.data;

        if (status === 'MAINFRAME_ONLINE') {
            console.log("✅ [Mainframe Core] Processing thread ready. UI overhead bypassed.");
            startHighSpeedIngestionLoop();
        }

        if (status === 'COMPUTATION_COMPLETE') {
            // Output pure telemetry straight to system logs or your outbound WebSocket bridge
            executeStreamTelemetryOutput(data);
        }

        if (status === 'MAINFRAME_ERROR') {
            console.error(`🚨 [Mainframe Core Critical Fault] ${error}`);
        }
    };
})();

/**
 * Updates the active element configuration targeting from background script logic
 */
export function reconfigureTargetSubstance(element, electrons, charge) {
    currentTargetState = { element, electrons, charge };
}

/**
 * High-Speed Data Engine Pipeline Loop
 */
function startHighSpeedIngestionLoop() {
    // Zero-delay or high-frequency calculation loop mapping
    setInterval(() => {
        const rawTelemetryTrack = captureHardwareInstrumentationTrack();

        mainframeWorker.postMessage({
            action: 'COMPUTE_MATRIX_FRAME',
            payload: {
                liveTrack: rawTelemetryTrack,
                targetState: currentTargetState
            }
        });
    }, 10); // Runs calculation cycles continuously every 10ms
}

function executeStreamTelemetryOutput(results) {
    if (results.chemicalContext.error) {
        console.warn(`[Mainframe Telemetry Warning] ${results.chemicalContext.error}`);
        return;
    }

    // Pure system data layout print out - completely decoupled from DOM threads
    console.log(
        `[METRICS] SNR: ${results.telemetry.signalToNoiseRatioDb}dB | ` +
        `Peak: ${results.telemetry.peakIntensity}lm | ` +
        `Color Hex: ${results.chemicalContext.calculatedColorHex}`
    );
}

// Simulated High-Speed Hardware Buffer Intake Generator
function captureHardwareInstrumentationTrack(length = 128) {
    const buffer = new Float32Array(length);
    for (let i = 0; i < length; i++) {
        buffer[i] = (Math.sin(i * 0.15) * 45 + 50) + (Math.random() * 10);
    }
    return buffer;
}
