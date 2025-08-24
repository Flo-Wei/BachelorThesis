/**
 * Configuration file for the AI Chatbot System
 * Update these values for different environments
 */

const CONFIG = {
    // API Configuration
    API_BASE_URL: (() => {
        const hostname = window.location.hostname;
        const port = window.location.port;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            // Development environment
            return 'http://localhost:8000';
        } else if (hostname === '10.1.70.4' || hostname.startsWith('10.1.')) {
            // Local network - use port 8000
            return `http://${hostname}:8000`;
        } else {
            // Production environment - same domain (works with reverse proxy)
            // Option 1: No prefix (current setup)
            // return window.location.origin;
            
            // Option 2: With /api prefix (enabled)
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

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}
