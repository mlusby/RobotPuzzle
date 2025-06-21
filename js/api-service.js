/**
 * API Service for Board Configurations
 */
class ApiService {
    constructor() {
        this.baseUrl = AWS_CONFIG.api.baseUrl;
    }

    async makeRequest(endpoint, options = {}) {
        const token = authService.getAuthToken();
        
        if (!token) {
            throw new Error('No authentication token available');
        }

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        };

        const config = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, config);
            
            if (response.status === 401) {
                // Token might be expired, try to refresh
                try {
                    await authService.refreshSession();
                    config.headers.Authorization = `Bearer ${authService.getAuthToken()}`;
                    const retryResponse = await fetch(`${this.baseUrl}${endpoint}`, config);
                    
                    if (!retryResponse.ok) {
                        throw new Error(`HTTP error! status: ${retryResponse.status}`);
                    }
                    
                    return await retryResponse.json();
                } catch (refreshError) {
                    // Refresh failed, redirect to login
                    authService.signOut();
                    throw new Error('Authentication failed. Please log in again.');
                }
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Board Configuration API methods
    async getConfigurations() {
        return await this.makeRequest('/configurations');
    }

    async getConfiguration(configId) {
        return await this.makeRequest(`/configurations/${configId}`);
    }

    async createConfiguration(configData) {
        return await this.makeRequest('/configurations', {
            method: 'POST',
            body: JSON.stringify(configData)
        });
    }

    async updateConfiguration(configId, configData) {
        return await this.makeRequest(`/configurations/${configId}`, {
            method: 'PUT',
            body: JSON.stringify(configData)
        });
    }

    async deleteConfiguration(configId) {
        return await this.makeRequest(`/configurations/${configId}`, {
            method: 'DELETE'
        });
    }

    // Utility method to get a random configuration for gameplay
    async getRandomConfiguration() {
        try {
            const configurations = await this.getConfigurations();
            const configIds = Object.keys(configurations);
            
            if (configIds.length === 0) {
                return null; // No configurations available
            }

            const randomId = configIds[Math.floor(Math.random() * configIds.length)];
            return {
                id: randomId,
                ...configurations[randomId]
            };
        } catch (error) {
            console.error('Failed to get random configuration:', error);
            return null;
        }
    }
}

// Create global API service instance
const apiService = new ApiService();