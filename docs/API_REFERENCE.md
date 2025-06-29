# Robot Puzzle Game - API Reference

This document provides detailed API specifications for the Robot Puzzle Game backend services.

## Base URL
- **Production**: `https://tdrzqioye7.execute-api.us-east-1.amazonaws.com/prod`
- **Development**: Local development server (auth bypassed)

## Authentication
- **Type**: Bearer Token (JWT)
- **Header**: `Authorization: Bearer <token>`
- **Development**: Authentication bypassed, mock user used

## Common Response Formats

### Success Response
```json
{
  "statusCode": 200,
  "data": {...}
}
```

### Error Response
```json
{
  "statusCode": 400,
  "error": "Error message description"
}
```

## Authentication Endpoints

### POST /auth/login
Authenticate user and obtain JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "userpassword"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "token": "jwt-token-string",
  "user": {
    "userId": "user-id",
    "email": "user@example.com",
    "username": "display-name"
  }
}
```

### POST /auth/refresh
Refresh JWT token.

**Headers:** `Authorization: Bearer <current-token>`

**Response:**
```json
{
  "statusCode": 200,
  "token": "new-jwt-token-string"
}
```

### POST /auth/logout
Terminate user session.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "message": "Logged out successfully"
}
```

## User Profile Endpoints

### GET /user/profile
Get current user profile information.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "user": {
    "userId": "user-id",
    "email": "user@example.com", 
    "username": "display-name",
    "createdAt": "2025-01-01T00:00:00Z",
    "lastLoginAt": "2025-01-01T12:00:00Z"
  }
}
```

### PUT /user/profile
Update user profile information.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "username": "new-display-name"
}
```

**Response:**
```json
{
  "statusCode": 200,
  "user": {
    "userId": "user-id",
    "email": "user@example.com",
    "username": "new-display-name",
    "updatedAt": "2025-01-01T12:00:00Z"
  }
}
```

## Configuration Management Endpoints

### GET /configurations
Get list of available board configurations.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "configurations": {
    "config-id-1": {
      "configId": "config-id-1",
      "authorEmail": "author@example.com",
      "walls": ["7,7,left", "8,8,top"],
      "targets": ["5,5", "10,10"],
      "isBaseline": true,
      "createdAt": "2025-01-01T00:00:00Z"
    }
  }
}
```

### POST /configurations
Create new board configuration.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "walls": ["7,7,left", "8,8,top", "5,5,right"],
  "targets": ["5,5", "10,10", "12,3"]
}
```

**Response:**
```json
{
  "statusCode": 201,
  "configuration": {
    "configId": "new-config-id",
    "authorEmail": "user@example.com",
    "authorId": "user-id",
    "walls": ["7,7,left", "8,8,top", "5,5,right"],
    "targets": ["5,5", "10,10", "12,3"],
    "isBaseline": false,
    "createdAt": "2025-01-01T12:00:00Z"
  }
}
```

### PUT /configurations/{configId}
Update existing configuration (own configurations only).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "walls": ["7,7,left", "8,8,top"],
  "targets": ["5,5", "10,10"]
}
```

**Response:**
```json
{
  "statusCode": 200,
  "configuration": {
    "configId": "config-id",
    "walls": ["7,7,left", "8,8,top"],
    "targets": ["5,5", "10,10"],
    "updatedAt": "2025-01-01T12:00:00Z"
  }
}
```

### DELETE /configurations/{configId}
Delete configuration (own configurations only).

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "message": "Configuration deleted successfully"
}
```

### GET /configurations/{configId}
Get specific configuration details.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "configuration": {
    "configId": "config-id",
    "authorEmail": "author@example.com",
    "walls": ["7,7,left", "8,8,top"],
    "targets": ["5,5", "10,10"],
    "isBaseline": true,
    "createdAt": "2025-01-01T00:00:00Z"
  }
}
```

## Round Management Endpoints

### GET /rounds
Get list of available rounds.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `type` (optional): `new` for practice rounds, `solved` for competitive rounds

**Response:**
```json
{
  "statusCode": 200,
  "rounds": [
    {
      "roundId": "round-id",
      "configId": "config-id",
      "authorEmail": "author@example.com",
      "targetPosition": {"color": "red", "x": 8, "y": 8},
      "isSolved": true,
      "createdAt": "2025-01-01T00:00:00Z",
      "firstSolvedAt": "2025-01-01T01:00:00Z",
      "firstSolvedBy": "solver-user-id"
    }
  ]
}
```

### POST /rounds
Create new round from configuration.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "configId": "config-id",
  "roundName": "Practice Round",
  "puzzleStates": [
    {
      "walls": ["7,7,left", "8,8,top"],
      "targets": ["8,8", "5,5"],
      "initialRobotPositions": {
        "red": {"x": 2, "y": 3},
        "blue": {"x": 5, "y": 7},
        "green": {"x": 10, "y": 12},
        "yellow": {"x": 14, "y": 1},
        "silver": {"x": 1, "y": 15}
      },
      "targetPosition": {"color": "red", "x": 8, "y": 8}
    }
  ]
}
```

**Response:**
```json
{
  "statusCode": 201,
  "round": {
    "roundId": "new-round-id",
    "configId": "config-id",
    "roundName": "Practice Round",
    "puzzleStates": [...],
    "authorEmail": "user@example.com",
    "createdAt": "2025-01-01T12:00:00Z"
  }
}
```

### POST /rounds/config/{configId}
Create new round from configuration (legacy endpoint).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "initialRobotPositions": {
    "red": {"x": 2, "y": 3},
    "blue": {"x": 5, "y": 7},
    "green": {"x": 10, "y": 12},
    "yellow": {"x": 14, "y": 1},
    "silver": {"x": 1, "y": 15}
  },
  "targetPositions": {"color": "red", "x": 8, "y": 8},
  "walls": ["7,7,left", "8,8,top"],
  "targets": ["8,8", "5,5"]
}
```

**Response:**
```json
{
  "statusCode": 201,
  "round": {
    "roundId": "new-round-id",
    "configId": "config-id",
    "authorEmail": "user@example.com",
    "createdAt": "2025-01-01T12:00:00Z"
  }
}
```

### GET /rounds/{roundId}
Get specific round details.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "round": {
    "roundId": "round-id",
    "configId": "config-id",
    "puzzleStates": [...],
    "targetPosition": {"color": "red", "x": 8, "y": 8},
    "initialRobotPositions": {...},
    "walls": [...],
    "targets": [...],
    "isSolved": true,
    "createdAt": "2025-01-01T00:00:00Z"
  }
}
```

### GET /rounds/config/{configId}
Get round configuration by config ID.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "round": {
    "roundId": "round-id",
    "configId": "config-id",
    "puzzleStates": [...],
    "createdAt": "2025-01-01T00:00:00Z"
  }
}
```

### DELETE /rounds/{roundId}
Delete round (own rounds only, no existing scores).

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "message": "Round deleted successfully"
}
```

## Score Management Endpoints

### GET /scores/{roundId}
Get leaderboard for specific round.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "leaderboard": [
    {
      "scoreId": "score-id",
      "userId": "user-id",
      "username": "player-name",
      "moves": 15,
      "completedAt": "2025-01-01T12:00:00Z",
      "medalType": "gold"
    }
  ]
}
```

### POST /scores/{roundId}
Submit solution for round.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "moves": 15,
  "moveSequence": ["red-up", "blue-left", "red-right", "green-down"],
  "completedAt": "2025-01-01T12:00:00Z"
}
```

**Response:**
```json
{
  "statusCode": 201,
  "score": {
    "scoreId": "new-score-id",
    "roundId": "round-id",
    "userId": "user-id",
    "moves": 15,
    "medalType": "silver",
    "personalBest": true,
    "completedAt": "2025-01-01T12:00:00Z"
  }
}
```

### GET /scores/user/{userId}
Get user's solve history.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "scores": [
    {
      "scoreId": "score-id",
      "roundId": "round-id",
      "moves": 15,
      "medalType": "gold",
      "completedAt": "2025-01-01T12:00:00Z"
    }
  ]
}
```

### GET /leaderboard/global
Get global leaderboard.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "leaderboard": [
    {
      "userId": "user-id",
      "username": "player-name",
      "totalPoints": 45,
      "goldMedals": 12,
      "silverMedals": 8,
      "bronzeMedals": 5,
      "roundsSolved": 25,
      "lastActivityAt": "2025-01-01T12:00:00Z"
    }
  ]
}
```

## Game State Management Endpoints

### GET /rounds/{roundId}/state
Get current round state for user.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "state": {
    "roundId": "round-id",
    "currentRobotPositions": {
      "red": {"x": 8, "y": 8},
      "blue": {"x": 5, "y": 7}
    },
    "moveCount": 15,
    "isComplete": true,
    "targetReached": true
  }
}
```

### POST /rounds/{roundId}/moves
Submit move sequence.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "moves": ["red-up", "blue-left"]
}
```

**Response:**
```json
{
  "statusCode": 200,
  "state": {
    "moveCount": 17,
    "isValid": true,
    "isComplete": false
  }
}
```

### POST /rounds/{roundId}/reset
Reset round to initial state.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "statusCode": 200,
  "state": {
    "roundId": "round-id",
    "moveCount": 0,
    "robotPositions": {...},
    "isComplete": false
  }
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created successfully |
| 400 | Bad request (invalid data) |
| 401 | Unauthorized (authentication required) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Not found |
| 409 | Conflict (duplicate data) |
| 429 | Too many requests (rate limited) |
| 500 | Internal server error |

## Rate Limiting
- **Limit**: 100 requests per minute per user
- **Headers**: Rate limit information included in response headers
- **Exceeded**: Returns 429 status with retry information

## Data Formats

### Grid Coordinates
- **Format**: "x,y" where x and y are 0-based integers
- **Range**: 0-15 for both x and y coordinates
- **Example**: "8,8" represents center-right of center 2x2 area

### Wall Specifications
- **Format**: "x,y,side" where side is "top", "bottom", "left", or "right"
- **Example**: "7,7,left" represents left wall of square at (7,7)

### Move Specifications
- **Format**: "color-direction" where color is robot color and direction is movement
- **Colors**: "red", "blue", "green", "yellow", "silver"
- **Directions**: "up", "down", "left", "right"
- **Example**: "red-up" means move red robot upward

### Timestamp Format
- **Format**: ISO 8601 format in UTC
- **Example**: "2025-01-01T12:00:00Z"

---

*This API reference should be kept in sync with actual implementation. All endpoints require proper CORS headers and authentication validation.*