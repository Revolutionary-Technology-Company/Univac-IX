// validate-config.js
const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

function validateConfig() {
  const configPath = path.resolve(__dirname, 'config.yaml');

  console.log(`[Validator] Checking formatting for: ${configPath}`);

  // 1. Check if file exists
  if (!fs.existsSync(configPath)) {
    console.error('❌ Error: config.yaml file is missing from the root directory!');
    process.exit(1);
  }

  try {
    const fileContents = fs.readFileSync(configPath, 'utf8');
    
    // 2. Attempt to parse the YAML structure
    const parsedData = yaml.load(fileContents);
    
    if (!parsedData || typeof parsedData !== 'object') {
      throw new Error('File parsed completely empty or is not a valid YAML object structure.');
    }

    console.log('✅ YAML Syntax Check: Passed cleanly.');

    // 3. Structural Validation: Ensure critical telephony nodes exist
    const requiredKeys = ['telephony', 'audio_engine', 'hardware_thresholds'];
    const missingKeys = [];

    requiredKeys.forEach(key => {
      if (!parsedData[key]) {
        missingKeys.push(key);
      }
    });

    if (missingKeys.length > 0) {
      console.warn(`⚠️ Warning: The file is valid YAML, but is missing standard schema segments: [${missingKeys.join(', ')}]`);
    } else {
      console.log('✅ Schema validation: All trunk blocks found successfully.');
    }

    process.exit(0); // Clean exit

  } catch (error) {
    console.error('❌ Formatting Error: Failed to parse config.yaml safely.');
    console.error(`Reason: ${error.message}`);
    process.exit(1); // Crash out to stop the server from launching blindly
  }
}

validateConfig();
