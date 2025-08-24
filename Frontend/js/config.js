/**
 * Configuration file for AI Chatbot System
 * Update these values for different environments
 * Version: 1.0.0
 */

const CONFIG = {
    // Version for cache busting
    VERSION: '1.0.0',
    
    // API Configuration
    API_BASE_URL: (() => {
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        console.log('Config: Determining API_BASE_URL for hostname:', hostname);
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            console.log('Config: Using localhost development URL');
            return 'http://localhost:8000';
        } else if (hostname === '10.1.70.4' || hostname.startsWith('10.1.')) {
            console.log('Config: Using local network URL');
            return `http://${hostname}:8000`;
        } else {
            console.log('Config: Using production URL with /api prefix');
            return window.location.origin + '/api';
        }
    })(),
    
    // Feature flags
    ENABLE_DEBUG_LOGGING: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1',
    
    // UI Configuration
    REFRESH_INTERVAL: 5000, // 5 seconds
    MAX_MESSAGE_LENGTH: 1000,
    
    // Session Configuration
    SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes in milliseconds
};

// Debug logging
console.log('Config loaded:', CONFIG);
console.log('Config.API_BASE_URL:', CONFIG.API_BASE_URL);

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
