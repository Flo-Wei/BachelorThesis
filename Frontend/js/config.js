/**
 * Configuration file for the AI Chatbot System
 * Update these values for different environments
 */

const CONFIG = {
    // API Configuration
    API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8000'  // Development
        : window.location.origin,  // Production - same domain
    
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
