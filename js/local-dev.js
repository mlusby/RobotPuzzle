/**
 * Local Development Mock Services
 * Simulates AWS backend behavior using localStorage
 */

// Mock Auth Service for Local Development
class LocalAuthService {
    constructor() {
        this.isLocalDev = true;
        this.mockUser = {
            sub: 'local-user-123',
            email: 'mlusby@gmail.com', // Default to mlusby for testing baseline configs
            name: 'Local Development User'
        };
    }

    isAuthenticated() {
        return true; // Always authenticated in local dev
    }

    getCurrentUser() {
        return this.mockUser;
    }

    getAuthToken() {
        return 'mock-jwt-token';
    }

    async refreshSession() {
        return true;
    }

    signOut() {
        // In local dev, just reload the page
        window.location.reload();
    }
}

// Mock API Service for Local Development
class LocalApiService {
    constructor() {
        this.isLocalDev = true;
        this.initializeLocalStorage();
    }

    initializeLocalStorage() {
        // Initialize with some sample data if empty
        if (!localStorage.getItem('local-rounds')) {
            this.createSampleData();
        }
    }

    createSampleData() {
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

        localStorage.setItem('local-rounds', JSON.stringify(sampleRounds));
        localStorage.setItem('local-configurations', JSON.stringify(sampleConfigs));
        localStorage.setItem('local-scores', JSON.stringify({}));
    }

    async makeRequest(endpoint, options = {}) {
        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 100));

        const method = options.method || 'GET';
        
        // Route to appropriate local handler
        if (endpoint.startsWith('/rounds/baseline')) {
            return this.getBaselineRounds();
        } else if (endpoint.startsWith('/rounds/user-submitted')) {
            return this.getUserSubmittedRounds();
        } else if (endpoint.startsWith('/rounds/config/')) {
            const configId = endpoint.split('/').pop();
            return this.createRound(configId, JSON.parse(options.body));
        } else if (endpoint.startsWith('/scores/') && method === 'GET') {
            const roundId = endpoint.split('/').pop();
            return this.getLeaderboard(roundId);
        } else if (endpoint.startsWith('/scores/') && method === 'POST') {
            const roundId = endpoint.split('/').pop();
            return this.submitScore(roundId, JSON.parse(options.body));
        } else if (endpoint === '/scores') {
            return this.getUserScores();
        } else if (endpoint === '/configurations') {
            if (method === 'GET') {
                return this.getConfigurations();
            } else if (method === 'POST') {
                return this.createConfiguration(JSON.parse(options.body));
            }
        } else if (endpoint.startsWith('/configurations/')) {
            const configId = endpoint.split('/').pop();
            if (method === 'PUT') {
                return this.updateConfiguration(configId, JSON.parse(options.body));
            } else if (method === 'DELETE') {
                return this.deleteConfiguration(configId);
            }
        }

        throw new Error(`Unhandled local API endpoint: ${method} ${endpoint}`);
    }

    // Configuration methods
    async getConfigurations() {
        const configs = JSON.parse(localStorage.getItem('local-configurations') || '{}');
        const userConfigs = configs['local-user-123'] || {};
        return userConfigs;
    }

    async createConfiguration(configData) {
        const configs = JSON.parse(localStorage.getItem('local-configurations') || '{}');
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
        
        localStorage.setItem('local-configurations', JSON.stringify(configs));
        return { configId };
    }

    async updateConfiguration(configId, configData) {
        const configs = JSON.parse(localStorage.getItem('local-configurations') || '{}');
        if (configs['local-user-123'] && configs['local-user-123'][configId]) {
            configs['local-user-123'][configId] = {
                ...configs['local-user-123'][configId],
                ...configData
            };
            localStorage.setItem('local-configurations', JSON.stringify(configs));
        }
        return { message: 'Updated successfully' };
    }

    async deleteConfiguration(configId) {
        const configs = JSON.parse(localStorage.getItem('local-configurations') || '{}');
        if (configs['local-user-123'] && configs['local-user-123'][configId]) {
            delete configs['local-user-123'][configId];
            localStorage.setItem('local-configurations', JSON.stringify(configs));
        }
        return { message: 'Deleted successfully' };
    }

    // Round methods
    async getBaselineRounds() {
        const rounds = JSON.parse(localStorage.getItem('local-rounds') || '[]');
        return rounds.filter(round => round.authorEmail === 'mlusby@gmail.com' && round.isActive);
    }

    async getUserSubmittedRounds() {
        const configs = JSON.parse(localStorage.getItem('local-configurations') || '{}');
        const userConfigs = configs['local-user-123'] || {};
        const solvedConfigs = Object.entries(userConfigs).filter(([id, config]) => config.solved);
        
        const rounds = JSON.parse(localStorage.getItem('local-rounds') || '[]');
        return rounds.filter(round => 
            solvedConfigs.some(([configId]) => configId === round.configId)
        );
    }

    async createRound(configId, roundData) {
        const rounds = JSON.parse(localStorage.getItem('local-rounds') || '[]');
        const configs = JSON.parse(localStorage.getItem('local-configurations') || '{}');
        const config = configs['local-user-123']?.[configId];
        
        if (!config) {
            throw new Error('Configuration not found');
        }
        
        const roundId = 'round-' + Date.now();
        const newRound = {
            roundId,
            configId,
            authorEmail: 'mlusby@gmail.com',
            initialRobotPositions: roundData.initialRobotPositions,
            targetPositions: roundData.targetPositions,
            walls: config.walls,
            targets: config.targets,
            isActive: true,
            createdAt: new Date().toISOString()
        };
        
        rounds.push(newRound);
        localStorage.setItem('local-rounds', JSON.stringify(rounds));
        return { roundId };
    }

    // Score methods
    async getLeaderboard(roundId) {
        const scores = JSON.parse(localStorage.getItem('local-scores') || '{}');
        const roundScores = Object.values(scores).filter(score => score.roundId === roundId);
        return roundScores.sort((a, b) => a.moves - b.moves);
    }

    async getUserScores() {
        const scores = JSON.parse(localStorage.getItem('local-scores') || '{}');
        return Object.values(scores).filter(score => score.userId === 'local-user-123');
    }

    async submitScore(roundId, scoreData) {
        const scores = JSON.parse(localStorage.getItem('local-scores') || '{}');
        const scoreKey = `${roundId}-local-user-123`;
        const existingScore = scores[scoreKey];
        
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
            moves: scoreData.moves,
            moveSequence: scoreData.moveSequence,
            completedAt: new Date().toISOString(),
            attemptCount: existingScore ? existingScore.attemptCount + 1 : 1
        };
        
        // Mark config as solved if it's the user's own config
        const configs = JSON.parse(localStorage.getItem('local-configurations') || '{}');
        const rounds = JSON.parse(localStorage.getItem('local-rounds') || '[]');
        const round = rounds.find(r => r.roundId === roundId);
        if (round && configs['local-user-123']?.[round.configId]) {
            configs['local-user-123'][round.configId].solved = true;
            localStorage.setItem('local-configurations', JSON.stringify(configs));
        }
        
        localStorage.setItem('local-scores', JSON.stringify(scores));
        
        return {
            message: 'Score submitted successfully',
            moves: scoreData.moves,
            personalBest: isPersonalBest
        };
    }

    // Utility methods
    async getRandomConfiguration() {
        const configs = await this.getConfigurations();
        const configIds = Object.keys(configs);
        
        if (configIds.length === 0) {
            return null;
        }

        const randomId = configIds[Math.floor(Math.random() * configIds.length)];
        return {
            id: randomId,
            ...configs[randomId]
        };
    }

    async getRandomRound(boardType = 'baseline') {
        let rounds;
        if (boardType === 'baseline') {
            rounds = await this.getBaselineRounds();
        } else {
            rounds = await this.getUserSubmittedRounds();
        }
        
        if (rounds.length === 0) {
            return null;
        }

        return rounds[Math.floor(Math.random() * rounds.length)];
    }
}

// Override global services for local development
if (typeof window !== 'undefined') {
    window.authService = new LocalAuthService();
    window.apiService = new LocalApiService();
    
    console.log('🔧 Local Development Mode Active');
    console.log('📊 Mock data initialized in localStorage');
    console.log('🎮 Ready to test Robot Puzzle Game locally!');
}