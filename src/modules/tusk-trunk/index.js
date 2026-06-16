// src/modules/tusk-trunk/index.js
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml'); // Standard node YAML engine

const SipStack = require('./sip-stack');
const AudioEngine = require('./audio-engine');
const LineTelemetryManager = require('./line-telemetry');

module.exports = {
  name: 'tuskTrunk',

  init(context) {
    console.log('[Module: TUSK Trunk] Loading configurations from root config.yaml...');

    let config = {};
    try {
      // Resolve path backwards out of src/modules/tusk-trunk/ up to the root /config.yaml
      const configPath = path.resolve(__dirname, '../../..', 'config.yaml');
      const fileContents = fs.readFileSync(configPath, 'utf8');
      config = yaml.load(fileContents);
    } catch (e) {
      console.error('[Module: TUSK Trunk] Failed to read root config.yaml. Falling back to defaults.', e);
      // Fallback object if file is missing or corrupted
      config = { telephony: { trunk: { ip: '127.0.0.1', port: 5060 } } };
    }

    // Extract scoped configurations from the root file
    const telecomConfig = config.telephony || {};
    const audioConfig = config.audio_engine || {};

    // 1. Instantiate Audio Engine with YAML definitions
    const targetProfile = audioConfig.acoustic_profile || 'SENNHEISER';
    const audioEngine = new AudioEngine(targetProfile);
    
    // Pass the noise suppression floor from config.yaml into the DSP core
    if (audioConfig.noise_cancellation_threshold) {
      audioEngine.noiseThreshold = audioConfig.noise_cancellation_threshold;
    }
    
    // 2. Instantiate Telemetry Manager
    const telemetry = new LineTelemetryManager({
      gatewayIp: telecomConfig.gateway?.ip || '192.168.1.200'
    });

    // 3. Launch SIP Core bound to your explicit topology
    SipStack.start({
      ip: telecomConfig.trunk?.ip || '192.168.1.100',
      port: telecomConfig.trunk?.port || 5060
    });

    // Handle incoming PTT stream hooks
    SipStack.events.on('audio_data', (rawMuLawBuffer) => {
      const linearPcmBuffer = audioEngine.muLawToPcm(rawMuLawBuffer);
      const highFidelityBuffer = audioEngine.applyNoiseCancellation(linearPcmBuffer);

      if (context.router) {
        context.router.broadcastToRawBuffers(highFidelityBuffer);
        context.router.streamToWebRTC(highFidelityBuffer);
      }
    });
  }
};
