/**
 * Unified API Service
 * Works with both localStorage (local dev) and AWS (production)
 */
class ApiService {
    constructor() {
        this.isLocalDev = ENV.isDevelopment();
        
        if (this.isLocalDev) {
            this.baseUrl = ENV.config.api.baseUrl;
            this.initializeLocalStorage();
        } else {
            // For production, get the base URL dynamically
            this.baseUrl = this.getProductionBaseUrl();
        }
    }

    getProductionBaseUrl() {
        // Try to get from AWS_CONFIG, with fallback handling
        if (typeof AWS_CONFIG !== 'undefined' && AWS_CONFIG.api && AWS_CONFIG.api.baseUrl) {
            return AWS_CONFIG.api.baseUrl;
        }
        
        // If AWS_CONFIG not loaded yet, return null and we'll handle it in makeRequest
        return null;
    }

    initializeLocalStorage() {
        // Initialize with sample data if empty
        if (!localStorage.getItem('robot-puzzle-rounds')) {
            this.createSampleData();
        }
    }

    createSampleData() {
        console.log('📊 Initializing sample data for local development');
        
        // Sample baseline rounds (authored by mlusby@gmail.com)
        const sampleRounds = [
            {
                roundId: 'round-1',
                configId: '1',
                authorEmail: 'mlusby@gmail.com',
                initialRobotPositions: {
                    silver: { x: 2, y: 3 },
                    green: { x: 5, y: 7 },
                    red: { x: 10, y: 12 },
                    yellow: { x: 13, y: 8 },
                    blue: { x: 8, y: 2 }
                },
                targetPositions: { color: 'red', x: 8, y: 8 },
                walls: [
                    '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                    '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right',
                    '2,3,bottom', '5,7,right', '10,12,left', '13,8,top'
                ],
                targets: ['8,8'],
                isActive: true,
                createdAt: new Date().toISOString()
            },
            {
                roundId: 'round-2',
                configId: '2',
                authorEmail: 'mlusby@gmail.com',
                initialRobotPositions: {
                    silver: { x: 1, y: 1 },
                    green: { x: 14, y: 14 },
                    red: { x: 6, y: 9 },
                    yellow: { x: 11, y: 4 },
                    blue: { x: 3, y: 12 }
                },
                targetPositions: { color: 'green', x: 8, y: 8 },
                walls: [
                    '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                    '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right',
                    '1,1,right', '14,14,left', '6,9,bottom', '11,4,top'
                ],
                targets: ['8,8'],
                isActive: true,
                createdAt: new Date().toISOString()
            }
        ];

        // Sample configurations
        const sampleConfigs = {
            'local-user-123': {
                '1': {
                    walls: [
                        '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                        '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right',
                        '2,3,bottom', '5,7,right', '10,12,left', '13,8,top'
                    ],
                    targets: ['8,8'],
                    authorEmail: 'mlusby@gmail.com',
                    isBaseline: true,
                    solved: true,
                    createdAt: new Date().toISOString()
                },
                '2': {
                    walls: [
                        '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                        '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right',
                        '1,1,right', '14,14,left', '6,9,bottom', '11,4,top'
                    ],
                    targets: ['8,8'],
                    authorEmail: 'mlusby@gmail.com',
                    isBaseline: true,
                    solved: true,
                    createdAt: new Date().toISOString()
                }
            }
        };

        localStorage.setItem('robot-puzzle-rounds', JSON.stringify(sampleRounds));
        localStorage.setItem('robot-puzzle-configurations', JSON.stringify(sampleConfigs));
        localStorage.setItem('robot-puzzle-scores', JSON.stringify({}));
    }

    async makeRequest(endpoint, options = {}) {
        // Route to localStorage methods in local development
        if (this.isLocalDev) {
            return await this.handleLocalRequest(endpoint, options);
        }

        // Production AWS API calls
        const token = authService.getAuthToken();
        
        if (!token) {
            throw new Error('No authentication token available');
        }

        // If baseUrl is null, try to get it again (AWS_CONFIG might be loaded now)
        if (!this.baseUrl) {
            this.baseUrl = this.getProductionBaseUrl();
            if (!this.baseUrl) {
                throw new Error('API base URL not available. AWS configuration may not be loaded yet.');
            }
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
                console.log('Error response data:', errorData);
                const errorMessage = (errorData && errorData.error) ? errorData.error : `HTTP error! status: ${response.status}`;
                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            console.error('Error details:', error.message, error.stack);
            throw error;
        }
    }

    async handleLocalRequest(endpoint, options = {}) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 100));

        const method = options.method || 'GET';
        
        // Route to appropriate local handler
        if (endpoint.startsWith('/rounds/baseline')) {
            return this.getBaselineRoundsLocal();
        } else if (endpoint.startsWith('/rounds/user-submitted')) {
            return this.getUserSubmittedRoundsLocal();
        } else if (endpoint.startsWith('/rounds/solved')) {
            return this.getSolvedRoundsLocal();
        } else if (endpoint.startsWith('/rounds/config/')) {
            const configId = endpoint.split('/').pop();
            return this.createRoundLocal(configId, JSON.parse(options.body));
        } else if (endpoint.startsWith('/scores/') && method === 'GET') {
            const roundId = endpoint.split('/').pop();
            return this.getLeaderboardLocal(roundId);
        } else if (endpoint.startsWith('/scores/') && method === 'POST') {
            const roundId = endpoint.split('/').pop();
            return this.submitScoreLocal(roundId, JSON.parse(options.body));
        } else if (endpoint === '/scores') {
            return this.getUserScoresLocal();
        } else if (endpoint === '/configurations') {
            if (method === 'GET') {
                return this.getConfigurationsLocal();
            } else if (method === 'POST') {
                return this.createConfigurationLocal(JSON.parse(options.body));
            }
        } else if (endpoint.startsWith('/configurations/')) {
            const configId = endpoint.split('/').pop();
            if (method === 'PUT') {
                return this.updateConfigurationLocal(configId, JSON.parse(options.body));
            } else if (method === 'DELETE') {
                return this.deleteConfigurationLocal(configId);
            }
        } else if (endpoint === '/user/profile') {
            if (method === 'GET') {
                return this.getUserProfileLocal();
            } else if (method === 'PUT') {
                return this.updateUserProfileLocal(JSON.parse(options.body));
            }
        } else if (endpoint === '/rounds/user-completed') {
            return this.getUserCompletedRoundsLocal();
        } else if (endpoint.startsWith('/rounds/') && !endpoint.includes('/config/')) {
            const roundId = endpoint.split('/').pop();
            if (method === 'GET') {
                return this.getRoundLocal(roundId);
            } else if (method === 'DELETE') {
                return this.deleteRoundLocal(roundId);
            }
        }

        throw new Error(`Unhandled local API endpoint: ${method} ${endpoint}`);
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

    // Rounds API methods
    async getBaselineRounds() {
        return await this.makeRequest('/rounds/baseline');
    }

    async getUserSubmittedRounds() {
        return await this.makeRequest('/rounds/user-submitted');
    }

    async createRound(configId, roundData) {
        // Add configId to the round data if not already present
        const enrichedRoundData = {
            ...roundData,
            configId: configId
        };
        
        return await this.makeRequest('/rounds', {
            method: 'POST',
            body: JSON.stringify(enrichedRoundData)
        });
    }

    // Scores API methods
    async getLeaderboard(roundId) {
        return await this.makeRequest(`/scores/${roundId}`);
    }

    async getUserScores() {
        return await this.makeRequest('/scores');
    }

    async submitScore(roundId, scoreData) {
        return await this.makeRequest(`/scores/${roundId}`, {
            method: 'POST',
            body: JSON.stringify(scoreData)
        });
    }

    // Get rounds that have been solved (have associated scores)
    async getSolvedRounds() {
        return await this.makeRequest('/rounds/solved');
    }

    // Utility method to get a random round for gameplay
    async getRandomRound(boardType = 'baseline') {
        try {
            let rounds;
            if (boardType === 'baseline') {
                rounds = await this.getBaselineRounds();
            } else {
                rounds = await this.getUserSubmittedRounds();
            }
            
            if (rounds.length === 0) {
                return null; // No rounds available
            }

            const randomRound = rounds[Math.floor(Math.random() * rounds.length)];
            return randomRound;
        } catch (error) {
            console.error('Failed to get random round:', error);
            return null;
        }
    }

    // Get a random solved round (preserves original puzzle state)
    async getRandomSolvedRound() {
        try {
            const solvedRounds = await this.getSolvedRounds();
            
            if (!solvedRounds || solvedRounds.length === 0) {
                return null;
            }

            // Pick a random round from the list
            const randomRound = solvedRounds[Math.floor(Math.random() * solvedRounds.length)];
            
            // Get the specific round by ID to ensure we get complete data
            if (randomRound.roundId) {
                console.log('🔍 Getting specific round:', randomRound.roundId);
                return await this.getRound(randomRound.roundId);
            }
            
            return randomRound;
        } catch (error) {
            console.error('Failed to get random solved round:', error);
            return null;
        }
    }

    // Local Storage Methods (for development)
    async getConfigurationsLocal() {
        const configs = JSON.parse(localStorage.getItem('robot-puzzle-configurations') || '{}');
        const userConfigs = configs['local-user-123'] || {};
        return userConfigs;
    }

    async createConfigurationLocal(configData) {
        const configs = JSON.parse(localStorage.getItem('robot-puzzle-configurations') || '{}');
        if (!configs['local-user-123']) configs['local-user-123'] = {};
        
        const userConfigs = configs['local-user-123'];
        const existingIds = Object.keys(userConfigs).map(id => parseInt(id)).filter(id => !isNaN(id));
        const configId = String(Math.max(...existingIds, 0) + 1);
        
        userConfigs[configId] = {
            ...configData,
            authorEmail: 'mlusby@gmail.com',
            isBaseline: true, // Since we're testing as mlusby
            solved: false,
            createdAt: new Date().toISOString()
        };
        
        localStorage.setItem('robot-puzzle-configurations', JSON.stringify(configs));
        return { configId };
    }

    async updateConfigurationLocal(configId, configData) {
        const configs = JSON.parse(localStorage.getItem('robot-puzzle-configurations') || '{}');
        if (configs['local-user-123'] && configs['local-user-123'][configId]) {
            configs['local-user-123'][configId] = {
                ...configs['local-user-123'][configId],
                ...configData
            };
            localStorage.setItem('robot-puzzle-configurations', JSON.stringify(configs));
        }
        return { message: 'Updated successfully' };
    }

    async deleteConfigurationLocal(configId) {
        const configs = JSON.parse(localStorage.getItem('robot-puzzle-configurations') || '{}');
        if (configs['local-user-123'] && configs['local-user-123'][configId]) {
            delete configs['local-user-123'][configId];
            localStorage.setItem('robot-puzzle-configurations', JSON.stringify(configs));
        }
        return { message: 'Deleted successfully' };
    }

    async getBaselineRoundsLocal() {
        const rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        return rounds.filter(round => round.authorEmail === 'mlusby@gmail.com' && round.isActive);
    }

    async getUserSubmittedRoundsLocal() {
        const configs = JSON.parse(localStorage.getItem('robot-puzzle-configurations') || '{}');
        const userConfigs = configs['local-user-123'] || {};
        const solvedConfigs = Object.entries(userConfigs).filter(([id, config]) => config.solved);
        
        const rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        return rounds.filter(round => 
            solvedConfigs.some(([configId]) => configId === round.configId)
        );
    }

    async getSolvedRoundsLocal() {
        // Get all rounds that have associated scores (i.e., have been solved)
        const scores = JSON.parse(localStorage.getItem('robot-puzzle-scores') || '{}');
        const rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        
        // Find rounds that have been solved (have scores)
        const solvedRoundIds = new Set();
        Object.values(scores).forEach(score => {
            solvedRoundIds.add(score.roundId);
        });
        
        // Return rounds that have been solved, preserving their original state
        return rounds.filter(round => solvedRoundIds.has(round.roundId));
    }

    async createRoundLocal(configId, roundData) {
        const rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        const configs = JSON.parse(localStorage.getItem('robot-puzzle-configurations') || '{}');
        const config = configs['local-user-123']?.[configId];
        
        if (!config) {
            throw new Error('Configuration not found');
        }
        
        const roundId = 'round-' + Date.now();
        const newRound = {
            roundId,
            configId,
            authorEmail: 'mlusby@gmail.com',
            initialRobotPositions: JSON.parse(JSON.stringify(roundData.initialRobotPositions)),
            targetPositions: JSON.parse(JSON.stringify(roundData.targetPositions)),
            walls: config.walls,
            targets: config.targets,
            isActive: true,
            createdAt: new Date().toISOString()
        };
        
        rounds.push(newRound);
        localStorage.setItem('robot-puzzle-rounds', JSON.stringify(rounds));
        return { roundId };
    }

    async getLeaderboardLocal(roundId) {
        const scores = JSON.parse(localStorage.getItem('robot-puzzle-scores') || '{}');
        const roundScores = Object.values(scores).filter(score => score.roundId === roundId);
        return roundScores.sort((a, b) => a.moves - b.moves);
    }

    async getUserScoresLocal() {
        const scores = JSON.parse(localStorage.getItem('robot-puzzle-scores') || '{}');
        return Object.values(scores).filter(score => score.userId === 'local-user-123');
    }

    async submitScoreLocal(roundId, scoreData) {
        const scores = JSON.parse(localStorage.getItem('robot-puzzle-scores') || '{}');
        const scoreKey = `${roundId}-local-user-123`;
        const existingScore = scores[scoreKey];
        
        // Get user profile for username
        const userProfile = await this.getUserProfileLocal();
        
        let isPersonalBest = false;
        let currentBest = null;
        
        if (existingScore) {
            currentBest = existingScore.moves;
            if (scoreData.moves >= existingScore.moves) {
                return {
                    message: 'Score not improved',
                    currentBest: existingScore.moves,
                    submitted: scoreData.moves
                };
            }
            isPersonalBest = true;
        } else {
            isPersonalBest = true;
        }
        
        scores[scoreKey] = {
            roundId,
            userId: 'local-user-123',
            username: userProfile?.username || null,
            moves: scoreData.moves,
            moveSequence: scoreData.moveSequence,
            completedAt: new Date().toISOString(),
            attemptCount: existingScore ? existingScore.attemptCount + 1 : 1
        };
        
        // Mark config as solved if it's the user's own config
        const configs = JSON.parse(localStorage.getItem('robot-puzzle-configurations') || '{}');
        const rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        const round = rounds.find(r => r.roundId === roundId);
        if (round && configs['local-user-123']?.[round.configId]) {
            configs['local-user-123'][round.configId].solved = true;
            localStorage.setItem('robot-puzzle-configurations', JSON.stringify(configs));
        }
        
        localStorage.setItem('robot-puzzle-scores', JSON.stringify(scores));
        
        return {
            message: 'Score submitted successfully',
            moves: scoreData.moves,
            personalBest: isPersonalBest
        };
    }

    // User Profile API methods
    async getUserProfile() {
        if (this.isLocalDev) {
            return this.getUserProfileLocal();
        }
        return await this.makeRequest('/user/profile');
    }

    async updateUserProfile(profileData) {
        if (this.isLocalDev) {
            return this.updateUserProfileLocal(profileData);
        }
        return await this.makeRequest('/user/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    async getUserProfileLocal() {
        const profiles = JSON.parse(localStorage.getItem('robot-puzzle-profiles') || '{}');
        return profiles['local-user-123'] || null;
    }

    async updateUserProfileLocal(profileData) {
        try {
            console.log('updateUserProfileLocal called with:', profileData);
            const profiles = JSON.parse(localStorage.getItem('robot-puzzle-profiles') || '{}');
            console.log('Current profiles:', profiles);
            
            profiles['local-user-123'] = {
                ...profiles['local-user-123'],
                ...profileData,
                updatedAt: new Date().toISOString()
            };
            
            localStorage.setItem('robot-puzzle-profiles', JSON.stringify(profiles));
            console.log('Profile updated successfully:', profiles['local-user-123']);
            return profiles['local-user-123'];
        } catch (error) {
            console.error('Error in updateUserProfileLocal:', error);
            throw error;
        }
    }

    // Additional round management methods
    async getUserCompletedRounds() {
        if (this.isLocalDev) {
            return this.getUserCompletedRoundsLocal();
        }
        return await this.makeRequest('/rounds/user-completed');
    }

    async getRound(roundId) {
        if (this.isLocalDev) {
            return this.getRoundLocal(roundId);
        }
        return await this.makeRequest(`/rounds/${roundId}`);
    }

    async deleteRound(roundId) {
        if (this.isLocalDev) {
            return this.deleteRoundLocal(roundId);
        }
        return await this.makeRequest(`/rounds/${roundId}`, {
            method: 'DELETE'
        });
    }

    async getUserCompletedRoundsLocal() {
        const rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        const scores = JSON.parse(localStorage.getItem('robot-puzzle-scores') || '{}');
        
        const userScores = Object.values(scores).filter(score => score.userId === 'local-user-123');
        
        return userScores.map(score => {
            const round = rounds.find(r => r.roundId === score.roundId);
            return {
                roundId: score.roundId,
                moves: score.moves,
                completedAt: score.completedAt,
                round: round
            };
        });
    }

    async getRoundLocal(roundId) {
        const rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        return rounds.find(r => r.roundId === roundId) || null;
    }

    async deleteRoundLocal(roundId) {
        let rounds = JSON.parse(localStorage.getItem('robot-puzzle-rounds') || '[]');
        const scores = JSON.parse(localStorage.getItem('robot-puzzle-scores') || '{}');
        
        // Remove the round
        rounds = rounds.filter(r => r.roundId !== roundId);
        localStorage.setItem('robot-puzzle-rounds', JSON.stringify(rounds));
        
        // Remove associated scores
        const updatedScores = {};
        Object.keys(scores).forEach(key => {
            if (!key.startsWith(`${roundId}-`)) {
                updatedScores[key] = scores[key];
            }
        });
        localStorage.setItem('robot-puzzle-scores', JSON.stringify(updatedScores));
        
        return { success: true };
    }
}

// Create global API service instance
const apiService = new ApiService();