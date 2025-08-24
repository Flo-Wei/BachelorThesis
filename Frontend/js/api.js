/**
 * API Utilities for AI Chatbot System
 * Handles JWT authentication and API calls
 */

class APIClient {
    constructor() {
        // Use configuration for base URL
        this.baseURL = typeof CONFIG !== 'undefined' ? CONFIG.API_BASE_URL : 
            (() => {
                const hostname = window.location.hostname;
                if (hostname === 'localhost' || hostname === '127.0.0.1') {
                    return 'http://localhost:8000';
                } else if (hostname === '10.1.70.4' || hostname.startsWith('10.1.')) {
                    // Local network - use port 8000
                    return `http://${hostname}:8000`;
                } else {
                    return window.location.origin;
                }
            })();
        
        // Debug logging
        console.log('APIClient initialized with:', {
            hostname: window.location.hostname,
            origin: window.location.origin,
            baseURL: this.baseURL,
            configExists: typeof CONFIG !== 'undefined',
            configURL: typeof CONFIG !== 'undefined' ? CONFIG.API_BASE_URL : 'undefined'
        });
        
        this.token = localStorage.getItem('auth_token');
        this.user = JSON.parse(localStorage.getItem('user_data') || 'null');
    }

    // Set authentication token
    setAuth(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('auth_token', token);
        localStorage.setItem('user_data', JSON.stringify(user));
    }

    // Clear authentication
    clearAuth() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
    }

    // Check if user is authenticated
    isAuthenticated() {
        return this.token !== null;
    }

    // Get current user
    getCurrentUser() {
        return this.user;
    }

    // Make authenticated request
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        // Add authentication header if token exists
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            
            // Handle authentication errors
            if (response.status === 401) {
                this.clearAuth();
                throw new Error('Authentication required');
            }

            if (!response.ok) {
                let errorMessage = `HTTP ${response.status}`;
                
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.message || errorMessage;
                } catch (parseError) {
                    // If we can't parse JSON, try to get text content
                    try {
                        const errorText = await response.text();
                        if (errorText) {
                            errorMessage = errorText;
                        }
                    } catch (textError) {
                        // If all else fails, use status text
                        errorMessage = response.statusText || errorMessage;
                    }
                }
                
                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            console.error(`Request URL: ${url}`);
            console.error(`Request config:`, config);
            throw error;
        }
    }

    // ===== USER MANAGEMENT =====

    async registerUser(username, email) {
        return await this.request('/users/register', {
            method: 'POST',
            body: JSON.stringify({ username, email })
        });
    }

    async loginUser(username) {
        const response = await this.request('/users/login', {
            method: 'POST',
            body: JSON.stringify({ username })
        });
        
        // Store authentication data
        this.setAuth(response.access_token, response.user);
        return response;
    }

    async getUser(userId) {
        return await this.request(`/users/${userId}`);
    }

    // ===== CHAT SESSIONS =====

    async getUserSessions(userId) {
        return await this.request(`/users/${userId}/sessions`);
    }

    async createSession(userId, sessionName = null) {
        return await this.request(`/users/${userId}/sessions`, {
            method: 'POST',
            body: JSON.stringify({ session_name: sessionName })
        });
    }

    async getSession(sessionId) {
        return await this.request(`/sessions/${sessionId}`);
    }

    async getSessionMessages(sessionId) {
        return await this.request(`/sessions/${sessionId}/messages`);
    }

    async updateSession(sessionId, sessionName) {
        return await this.request(`/sessions/${sessionId}`, {
            method: 'PUT',
            body: JSON.stringify({ session_name: sessionName })
        });
    }

    // ===== CHAT =====

    async sendMessage(userId, message, sessionId = null) {
        return await this.request(`/users/${userId}/chat`, {
            method: 'POST',
            body: JSON.stringify({ 
                message, 
                session_id: sessionId 
            })
        });
    }

    // ===== SKILLS =====

    async getSkillSystems() {
        return await this.request('/skills/systems');
    }

    async getSessionSkills(sessionId, skillSystem) {
        return await this.request(`/sessions/${sessionId}/skills/${skillSystem}`);
    }

    async getAllSessionSkills(sessionId) {
        return await this.request(`/sessions/${sessionId}/skills`);
    }

    // ===== UTILITY =====

    async healthCheck() {
        return await this.request('/health');
    }
}

// Create global API client instance
const api = new APIClient();

// Utility functions for common operations
const AuthUtils = {
    requireAuth() {
        if (!api.isAuthenticated()) {
            window.location.href = 'user.html';
            return false;
        }
        return true;
    },

    getCurrentUserId() {
        const user = api.getCurrentUser();
        return user ? user.user_id : null;
    },

    logout() {
        api.clearAuth();
        window.location.href = 'user.html';
    }
};

// UI utility functions
const UIUtils = {
    showLoading(element) {
        if (element) {
            element.innerHTML = '<div class="loading">Loading...</div>';
        }
    },

    showError(element, message) {
        if (element) {
            element.innerHTML = `
                <div class="error-message">
                    <strong>Error:</strong> ${message}
                </div>
            `;
        }
    },

    showSuccess(element, message) {
        if (element) {
            element.innerHTML = `
                <div class="success-message">
                    <strong>Success:</strong> ${message}
                </div>
            `;
        }
    },

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    formatTimeAgo(dateString) {
        const now = new Date();
        const date = new Date(dateString);
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return UIUtils.formatDate(dateString);
    }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, api, AuthUtils, UIUtils };
}
