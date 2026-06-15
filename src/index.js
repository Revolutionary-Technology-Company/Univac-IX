// Example addition to your main application loader
const tuskTrunkModule = require('./modules/tusk-trunk');

// Inside your server startup sequence:
const appContext = { /* your existing system nodes/config */ };
tuskTrunkModule.init(appContext);
