# Robot Puzzle Game

A web-based puzzle game where players slide colored robots across a board to reach target positions. Built with serverless AWS architecture.

## 🎮 Game Features

- **16x16 Grid Board**: Navigate robots through walls and obstacles
- **5 Colored Robots**: Silver, green, red, yellow, and blue robots
- **Sliding Mechanics**: Robots slide until they hit a wall or another robot
- **Custom Board Designer**: Create and save your own puzzle configurations
- **User Authentication**: Personal board configurations saved to the cloud
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## 🏗️ Architecture

The game uses a fully serverless AWS architecture:

- **Frontend**: Static website hosted on S3
- **Authentication**: AWS Cognito User Pools
- **API**: API Gateway with Lambda functions
- **Database**: DynamoDB for user board configurations
- **Infrastructure**: CloudFormation for repeatable deployments

## 🚀 Quick Deployment

### Prerequisites

1. **AWS Account**: Active AWS account with appropriate permissions
2. **AWS CLI**: Installed and configured
   ```bash
   aws configure
   ```
3. **Git**: To clone the repository

### Deploy to AWS

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd robots
   ```

2. **Run the deployment script**:
   ```bash
   ./deploy.sh
   ```

3. **Wait for deployment** (typically 5-10 minutes)

4. **Visit your game**: The script will output the website URL

### Manual Deployment

If you prefer manual deployment:

1. **Deploy CloudFormation stack**:
   ```bash
   aws cloudformation deploy \
     --template-file aws/cloudformation-template.yaml \
     --stack-name robot-puzzle-game-dev \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides AppName=robot-puzzle-game Environment=dev
   ```

2. **Get stack outputs**:
   ```bash
   aws cloudformation describe-stacks --stack-name robot-puzzle-game-dev
   ```

3. **Update `js/aws-config.js`** with the outputs

4. **Upload files to S3 bucket**

## 🎯 How to Play

1. **Sign Up**: Create an account or sign in
2. **Select a Robot**: Click and drag a robot to move it
3. **Slide to Target**: Robots slide until they hit an obstacle
4. **Reach the Goal**: Get the target-colored robot to the highlighted square
5. **Track Moves**: Try to solve puzzles in the fewest moves possible

## 🛠️ Board Configuration

1. **Access the Editor**: Click "Board Configuration" in the main game
2. **Design Mode**: Switch between "Walls" and "Targets" modes
3. **Place Walls**: Click lines between squares to add/remove walls
4. **Set Targets**: Click squares to place potential target positions
5. **Save Configuration**: Give your configuration a number and save
6. **Test**: Use "Test in Game" to try your creation

## 📁 Project Structure

```
robot-puzzle-game/
├── index.html              # Main game interface
├── wall-editor.html        # Board configuration tool
├── login.html             # Authentication interface
├── styles.css             # Game styling
├── script.js              # Game logic
├── favicon.svg            # Game icon
├── error.html             # Error page
├── js/
│   ├── aws-config.js      # AWS configuration
│   ├── auth-service.js    # Authentication service
│   └── api-service.js     # API service
├── aws/
│   └── cloudformation-template.yaml  # Infrastructure definition
├── deploy.sh              # Deployment script
└── README.md              # This file
```

## 🔧 Configuration

### AWS Configuration (`js/aws-config.js`)

```javascript
const AWS_CONFIG = {
    region: 'us-east-1',
    cognito: {
        userPoolId: 'YOUR_USER_POOL_ID',
        userPoolWebClientId: 'YOUR_CLIENT_ID'
    },
    api: {
        baseUrl: 'YOUR_API_GATEWAY_URL'
    }
};
```

### CloudFormation Parameters

- `AppName`: Application name (default: robot-puzzle-game)
- `Environment`: Environment name (dev/staging/prod)

## 🔐 Security Features

- **User Authentication**: AWS Cognito with email verification
- **API Authorization**: JWT token-based API access
- **User Isolation**: Board configurations are user-scoped
- **CORS Configuration**: Proper cross-origin resource sharing
- **Input Validation**: Server-side data validation

## 💰 AWS Costs

The serverless architecture is cost-effective:

- **S3**: ~$0.02/month for website hosting
- **Cognito**: Free tier covers up to 50,000 MAUs
- **Lambda**: Free tier includes 1M requests/month
- **DynamoDB**: Free tier includes 25GB storage
- **API Gateway**: Free tier includes 1M requests/month

Total estimated cost for small usage: **$0-5/month**

## 🧹 Cleanup

To remove all AWS resources:

```bash
aws cloudformation delete-stack --stack-name robot-puzzle-game-dev
```

## 🐛 Troubleshooting

### Common Issues

1. **Deployment Fails**: Check AWS credentials and permissions
2. **CORS Errors**: Ensure API Gateway CORS is configured correctly
3. **Authentication Issues**: Verify Cognito configuration
4. **API Not Working**: Check Lambda function logs in CloudWatch

### Debug Commands

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name robot-puzzle-game-dev

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name robot-puzzle-game-dev

# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/robot-puzzle-game
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🎉 Acknowledgments

- Inspired by classic sliding puzzle games
- Built with modern web technologies and AWS serverless architecture
- Designed for educational purposes and fun!