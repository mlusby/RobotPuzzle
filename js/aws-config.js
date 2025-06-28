// AWS Configuration - Production Environment
// Generated: Sat Jun 28 12:17:00 EST 2025
// Stack: robot-puzzle-game-prod
// Region: us-east-1

const AWS_CONFIG = {
    region: 'us-east-1',
    cognito: {
        userPoolId: 'us-east-1_vuhOQRbe8',
        userPoolWebClientId: '7huu9smgjqsmsacuclr13ek2lj'
    },
    api: {
        baseUrl: 'https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod'
    }
};

// Export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AWS_CONFIG;
}