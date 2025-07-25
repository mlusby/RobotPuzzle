/**
 * Environment Detection and Configuration
 * Automatically detects local vs production environment
 */

class Environment {
    constructor() {
        this.isLocal = this.detectLocalEnvironment();
        this.config = this.getConfig();
    }

    detectLocalEnvironment() {
        // Detect local development environment
        return (
            window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1' ||
            window.location.hostname === '' ||
            window.location.protocol === 'file:' ||
            (window.location.hostname.includes('localhost') || 
             window.location.hostname.includes('127.0.0.1') ||
             (window.location.port && ['3000', '8000', '8080', '5000'].includes(window.location.port)))
        );
    }

    getConfig() {
        if (this.isLocal) {
            return this.getLocalConfig();
        } else {
            return this.getProductionConfig();
        }
    }

    getLocalConfig() {
        return {
            environment: 'local',
            auth: {
                required: false,
                mockUser: {
                    sub: 'local-user-123',
                    email: 'mlusby@gmail.com',
                    name: 'Local Development User'
                }
            },
            api: {
                baseUrl: null, // Will be mocked
                mock: true
            },
            storage: {
                type: 'localStorage',
                prefix: 'robot-puzzle-'
            },
            ui: {
                showDevBanner: true,
                signOutText: 'Refresh (Mock Sign Out)'
            }
        };
    }

    getProductionConfig() {
        return {
            environment: 'production',
            auth: {
                required: true,
                mockUser: null
            },
            api: {
                baseUrl: this.getProductionBaseUrl(),
                mock: false
            },
            storage: {
                type: 'aws',
                prefix: null
            },
            ui: {
                showDevBanner: false,
                signOutText: 'Sign Out'
            }
        };
    }

    getProductionBaseUrl() {
        // Try to get from AWS_CONFIG if available
        if (typeof AWS_CONFIG !== 'undefined' && AWS_CONFIG.api && AWS_CONFIG.api.baseUrl) {
            return AWS_CONFIG.api.baseUrl;
        }
        
        // Fallback: wait for AWS_CONFIG to be loaded and return a getter
        return null;
    }

    isDevelopment() {
        return this.isLocal;
    }

    isProduction() {
        return !this.isLocal;
    }
}

// Global environment instance
const ENV = new Environment();

// Console logging
if (ENV.isDevelopment()) {
    console.log('🔧 Local Development Mode Active');
    console.log('📊 Environment Config:', ENV.config);
} else {
    console.log('🚀 Production Mode Active');
}