/**
 * Authentication Service using AWS Cognito
 */
class AuthService {
    constructor() {
        this.userPool = null;
        this.currentUser = null;
        this.cognitoUser = null;
        this.init();
    }

    init() {
        // Initialize Cognito User Pool
        this.userPool = new AmazonCognitoIdentity.CognitoUserPool({
            UserPoolId: AWS_CONFIG.cognito.userPoolId,
            ClientId: AWS_CONFIG.cognito.userPoolWebClientId
        });

        // Check if user is already authenticated
        this.cognitoUser = this.userPool.getCurrentUser();
        if (this.cognitoUser) {
            this.cognitoUser.getSession((err, session) => {
                if (err) {
                    console.log('Session error:', err);
                    this.signOut();
                } else if (session.isValid()) {
                    this.currentUser = {
                        username: this.cognitoUser.getUsername(),
                        email: session.getIdToken().payload.email,
                        token: session.getIdToken().getJwtToken()
                    };
                    this.onAuthStateChange('signedIn');
                } else {
                    this.signOut();
                }
            });
        } else {
            this.onAuthStateChange('signedOut');
        }
    }

    signUp(email, password, confirmPassword) {
        return new Promise((resolve, reject) => {
            if (password !== confirmPassword) {
                reject(new Error('Passwords do not match'));
                return;
            }

            const attributeList = [
                new AmazonCognitoIdentity.CognitoUserAttribute({
                    Name: 'email',
                    Value: email
                })
            ];

            this.userPool.signUp(email, password, attributeList, null, (err, result) => {
                if (err) {
                    reject(err);
                } else {
                    resolve({
                        user: result.user,
                        userConfirmed: result.userConfirmed,
                        userSub: result.userSub
                    });
                }
            });
        });
    }

    confirmSignUp(username, confirmationCode) {
        return new Promise((resolve, reject) => {
            const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
                Username: username,
                Pool: this.userPool
            });

            cognitoUser.confirmRegistration(confirmationCode, true, (err, result) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(result);
                }
            });
        });
    }

    signIn(email, password) {
        return new Promise((resolve, reject) => {
            const authenticationData = {
                Username: email,
                Password: password
            };

            const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);

            const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
                Username: email,
                Pool: this.userPool
            });

            cognitoUser.authenticateUser(authenticationDetails, {
                onSuccess: (session) => {
                    this.cognitoUser = cognitoUser;
                    this.currentUser = {
                        username: cognitoUser.getUsername(),
                        email: session.getIdToken().payload.email,
                        token: session.getIdToken().getJwtToken()
                    };
                    this.onAuthStateChange('signedIn');
                    resolve(this.currentUser);
                },
                onFailure: (err) => {
                    reject(err);
                },
                newPasswordRequired: (userAttributes, requiredAttributes) => {
                    // Handle new password required case
                    reject(new Error('New password required'));
                }
            });
        });
    }

    signOut() {
        if (this.cognitoUser) {
            this.cognitoUser.signOut();
        }
        this.currentUser = null;
        this.cognitoUser = null;
        this.onAuthStateChange('signedOut');
    }

    getCurrentUser() {
        return this.currentUser;
    }

    getAuthToken() {
        return this.currentUser ? this.currentUser.token : null;
    }

    isAuthenticated() {
        return this.currentUser !== null;
    }

    refreshSession() {
        return new Promise((resolve, reject) => {
            if (!this.cognitoUser) {
                reject(new Error('No user session'));
                return;
            }

            this.cognitoUser.getSession((err, session) => {
                if (err) {
                    reject(err);
                } else if (session.isValid()) {
                    this.currentUser.token = session.getIdToken().getJwtToken();
                    resolve(session);
                } else {
                    reject(new Error('Invalid session'));
                }
            });
        });
    }

    forgotPassword(email) {
        return new Promise((resolve, reject) => {
            const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
                Username: email,
                Pool: this.userPool
            });

            cognitoUser.forgotPassword({
                onSuccess: (data) => {
                    resolve(data);
                },
                onFailure: (err) => {
                    reject(err);
                }
            });
        });
    }

    confirmPassword(email, confirmationCode, newPassword) {
        return new Promise((resolve, reject) => {
            const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
                Username: email,
                Pool: this.userPool
            });

            cognitoUser.confirmPassword(confirmationCode, newPassword, {
                onSuccess: () => {
                    resolve('Password confirmed successfully');
                },
                onFailure: (err) => {
                    reject(err);
                }
            });
        });
    }

    // Override this method to handle auth state changes
    onAuthStateChange(state) {
        console.log('Auth state changed:', state);
        
        // Dispatch custom event for components to listen to
        window.dispatchEvent(new CustomEvent('authStateChange', {
            detail: { state, user: this.currentUser }
        }));
    }
}

// Create global auth service instance
const authService = new AuthService();