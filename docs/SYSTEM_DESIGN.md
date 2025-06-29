# Robot Puzzle Game - System Design Documentation

## Table of Contents
1. [Game Overview](#game-overview)
2. [Core Game Mechanics](#core-game-mechanics)
3. [User Roles and Permissions](#user-roles-and-permissions)
4. [Content Management System](#content-management-system)
5. [Scoring and Competition System](#scoring-and-competition-system)
6. [User Interface Requirements](#user-interface-requirements)
7. [Technical Architecture](#technical-architecture)
8. [Data Models](#data-models)
9. [API Specifications](#api-specifications)
10. [Acceptance Criteria](#acceptance-criteria)

## Game Overview

The Robot Puzzle Game is a competitive puzzle-solving game where players move colored robots on a grid-based board to reach target squares in the minimum number of moves possible.

### Core Concept
- **Board**: 16x16 grid with walls and robots
- **Objective**: Move the designated robot to its matching colored target square
- **Competition**: Achieve the solution in the fewest moves to rank on leaderboards
- **Content Creation**: Users can create their own board configurations for others to play

## Core Game Mechanics

### Board Setup
- **Grid Size**: 16x16 squares
- **Robots**: Exactly 5 robots (silver, yellow, green, blue, red)
- **Walls**: Placed only on grid edges between squares, never within squares
- **Fixed Walls**: 
  - Center 2x2 square is always completely walled
  - Outer perimeter is always walled
- **Initial Robot Positions**: Always randomized when a round is created
- **Robot Placement Rules**: Robots cannot be placed in the center 2x2 square

### Movement Rules
- **Direction**: Robots move only in straight lines (up, down, left, right)
- **Movement Behavior**: Robots slide until they hit an obstacle
- **Stopping Conditions**:
  - **Against another robot**: Stop in the square just before the other robot
  - **Against a wall**: Stop in the square that has the wall on the opposite side from where the robot entered
- **Turn Structure**: One robot movement per turn/move

### Victory Conditions
- **Objective**: Get the designated robot to the target square of matching color
- **Target System**: Each round has exactly one target square with one designated color
- **Completion**: Round is solved when the matching colored robot occupies the target square
- **Auto-Save**: Solved rounds are automatically saved when completed

### Scoring System
- **Score Calculation**: Simple count of moves (robot movements) required to solve
- **Move Limit**: Maximum 98 moves can be saved (99th move prevents saving)
- **Move Tracking**: Each move stored as robot color + direction for validation
- **Reset Functionality**: Players can return to initial state at any time

## User Roles and Permissions

### User Categories

#### Standard Users
- **Authentication**: Required in production, bypassed in development
- **Content Creation**: Can create board configurations
- **Content Usage**: Can play rounds from their own configurations and baseline configurations
- **Content Deletion**: Can delete their own configurations
- **Competitive Play**: Can play solved rounds created by any user

#### Baseline Content Creator (mlusby@gmail.com)
- **Special Status**: Configurations created by this user are "baseline"
- **Global Availability**: Baseline configurations available to all users for round generation
- **Enhanced Permissions**: May have additional functionality in production

#### Development Mode User
- **Identity**: Hardcoded as "Admin" (admin@robotgame.dev)
- **Username**: Can be changed from "Admin", email remains fixed
- **Functionality**: All features available (equivalent to production mlusby@gmail.com)

### Permission Matrix

| Action | Standard User | Baseline Creator | Dev Mode |
|--------|---------------|------------------|----------|
| Create Configurations | ✓ | ✓ | ✓ |
| Delete Own Configurations | ✓ | ✓ | ✓ |
| Generate Rounds from Own Configs | ✓ | ✓ | ✓ |
| Generate Rounds from Baseline | ✓ | ✓ | ✓ |
| Play Solved Rounds | ✓ | ✓ | ✓ |
| Special Features | ✗ | May have additional | ✓ |

## Content Management System

### Board Configurations

#### Creation Requirements
- **Minimum Targets**: At least one target must be placed
- **Target Placement**: Targets cannot be placed in center 2x2 square
- **Wall Placement**: No restrictions beyond fixed walls (center + perimeter)
- **Target Colors**: Assigned randomly at round creation, not during configuration
- **Validation**: Currently no automatic validation for solvability

#### Configuration Lifecycle
- **Creation**: Available to any authenticated user
- **Usage**: 
  - Own configurations: Always available for round generation
  - Baseline configurations: Available to all users
- **Deletion**: 
  - Users can delete own configurations
  - Existing solved rounds remain playable
  - No new rounds generated from deleted configurations
- **Status**: All saved configurations remain active until deleted

### Round Generation

#### Round Creation Process
1. **Configuration Selection**: From baseline or user's own configurations
2. **Target Selection**: Random selection from available targets in configuration
3. **Color Assignment**: Random assignment of color to selected target
4. **Robot Placement**: Random placement of 5 robots (avoiding center 2x2 and target)
5. **Collision Handling**: Re-randomize if robot placed on target square

#### Round Types
- **Practice Rounds**: Newly generated, not preserved if unsolved
- **Competitive Rounds**: Previously solved rounds, preserved for competitive play
- **Availability**: Rounds become competitive immediately upon first solution

#### Round Lifecycle
- **Generation**: On-demand when user selects "New Round"
- **Preservation**: Only solved rounds are saved permanently
- **Abandonment**: No penalty for leaving unsolved rounds
- **Competitive Access**: Solved rounds immediately available to all users

## Scoring and Competition System

### Individual Round Scoring
- **Metric**: Number of moves to complete the round
- **Validation**: Move sequence verified to ensure legitimate solution
- **Multiple Attempts**: Only best (lowest) score per user per round counts
- **Leaderboard Display**: Per-round rankings showing username, moves, date, medal

### Medal System
- **Gold Medal**: Tied for lowest number of moves on a round
- **Silver Medal**: Tied for second-lowest number of moves on a round  
- **Bronze Medal**: Tied for third-lowest number of moves on a round
- **Tie Handling**: Earlier solutions rank higher in display order
- **Multiple Winners**: Unlimited number of users can achieve same medal level

### Global Scoring
- **Point System**: 3 points per gold, 2 points per silver, 1 point per bronze
- **Global Leaderboard**: Ranked by total points, then by tie-breaking rules
- **Tie Breaking**: Users with same points ranked by order of achievement
- **Statistics Tracking**: Medal counts and solve percentages per user

### Move Validation
- **Storage Format**: Sequence of "color-direction" commands
- **Validation Process**: Replay moves from initial state to verify end state
- **Security**: Prevents score manipulation by validating complete solve path
- **Privacy**: Move sequences stored but not visible to other players

## User Interface Requirements

### Round Selection Interface
- **Mode Selection**: Clear distinction between "New Round" and "Solved Rounds"
- **New Round Flow**: 
  - Select from available configurations (baseline + own)
  - Immediate round generation and play
- **Solved Round Flow**:
  - Browse available competitive rounds
  - View existing leaderboard before playing
  - Select specific round to attempt

### Gameplay Interface
- **Board Display**: 16x16 grid with clear robot and wall visualization
- **Robot Movement**: Click/tap interface for robot selection and movement
- **Move Counter**: Real-time display of current move count
- **Reset Function**: One-click return to initial round state
- **Progress Indicator**: Clear indication when target is reached
- **Move Limit Warning**: Notification approaching 99-move limit

### Leaderboard Displays
- **Round Leaderboard**: 
  - Shown during round selection and after completion
  - Username, move count, completion date, medal indicator
  - Sorted by moves (ascending), then by date (ascending for ties)
- **Global Leaderboard**:
  - Separate page/view for overall rankings
  - Username, total points, medal counts
  - Sorted by points (descending), then by achievement order

### Configuration Creation Interface
- **Grid Editor**: Visual interface for placing walls and targets
- **Wall Tool**: Click grid edges to add/remove walls
- **Target Tool**: Click squares to place/remove targets
- **Validation**: Minimum one target before saving
- **Preview**: Ability to test configuration before saving

### User Statistics Interface
- **Personal Dashboard**: 
  - Total rounds solved
  - Medal distribution (counts and percentages)
  - Personal solve statistics
- **Progress Tracking**: Visual indicators of achievement levels

## Technical Architecture

### Environment Configuration
- **Production**: Full authentication, real data, mlusby@gmail.com baseline privileges
- **Development**: Mock authentication, separate data, all features available
- **Visual Distinction**: Clear indicators of current environment
- **Feature Parity**: Identical functionality across environments

### Authentication System
- **Production**: Cognito-based user authentication
- **Development**: Bypassed authentication with mock user
- **Session Management**: Secure token handling and refresh
- **User Profile**: Email, username, authentication state

### Data Storage
- **User Data**: Profiles, authentication tokens, preferences
- **Configuration Data**: Board layouts, target positions, metadata
- **Round Data**: Initial states, target assignments, completion status
- **Score Data**: Move sequences, completion times, validation state
- **Leaderboard Data**: Computed rankings, medal assignments, points

### API Architecture
- **RESTful Design**: Standard HTTP methods and status codes
- **Authentication**: Bearer token validation on protected endpoints
- **CORS Configuration**: Proper cross-origin resource sharing
- **Error Handling**: Consistent error response format
- **Rate Limiting**: Protection against abuse

### Performance Requirements
- **Scale**: Support for <100 users, <1000 configurations, <10000 rounds, <100000 scores
- **Response Time**: <2 seconds for round generation, <1 second for move validation
- **Availability**: 99% uptime during active hours
- **Data Integrity**: ACID compliance for score submissions

## Data Models

### User Profile
```json
{
  "userId": "string (unique identifier)",
  "email": "string (authentication key)",
  "username": "string (display name, changeable)",
  "createdAt": "timestamp",
  "lastLoginAt": "timestamp"
}
```

### Board Configuration
```json
{
  "configId": "string (unique identifier)",
  "authorEmail": "string (creator identification)",
  "authorId": "string (creator user ID)",
  "walls": ["array of strings (grid edge identifiers)"],
  "targets": ["array of strings (grid square identifiers)"],
  "isBaseline": "boolean (mlusby@gmail.com created)",
  "createdAt": "timestamp",
  "isActive": "boolean (available for round generation)"
}
```

### Round
```json
{
  "roundId": "string (unique identifier)",
  "configId": "string (source configuration)",
  "authorEmail": "string (creator of round)",
  "authorId": "string (creator user ID)",
  "initialRobotPositions": {"color": {"x": "number", "y": "number"}},
  "targetPosition": {"color": "string", "x": "number", "y": "number"},
  "walls": ["array of strings (inherited from config)"],
  "targets": ["array of strings (inherited from config)"],
  "isSolved": "boolean (has been completed)",
  "createdAt": "timestamp",
  "firstSolvedAt": "timestamp",
  "firstSolvedBy": "string (user ID)"
}
```

### Score/Solution
```json
{
  "scoreId": "string (unique identifier)",
  "roundId": "string (associated round)",
  "userId": "string (solving user)",
  "username": "string (display name at time of solve)",
  "moves": "number (move count)",
  "moveSequence": ["array of strings (color-direction pairs)"],
  "completedAt": "timestamp",
  "validationStatus": "string (validated/pending/invalid)",
  "medalType": "string (gold/silver/bronze)"
}
```

### Leaderboard Entry
```json
{
  "userId": "string",
  "username": "string",
  "totalPoints": "number",
  "goldMedals": "number",
  "silverMedals": "number",
  "bronzeMedals": "number",
  "roundsSolved": "number",
  "lastActivityAt": "timestamp"
}
```

## API Specifications

### Authentication Endpoints
- `POST /auth/login` - User authentication
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - Session termination
- `GET /user/profile` - Get user profile
- `PUT /user/profile` - Update user profile

### Configuration Management
- `GET /configurations` - List user's configurations + baseline
- `POST /configurations` - Create new configuration
- `PUT /configurations/{id}` - Update configuration (own only)
- `DELETE /configurations/{id}` - Delete configuration (own only)
- `GET /configurations/{id}` - Get specific configuration

### Round Management
- `GET /rounds` - List available rounds (baseline + own configs for new, all solved for competitive)
- `POST /rounds` - Create new round from configuration
- `GET /rounds/{id}` - Get specific round details
- `DELETE /rounds/{id}` - Delete round (own only, if no scores)

### Score Management
- `GET /scores/{roundId}` - Get leaderboard for specific round
- `POST /scores/{roundId}` - Submit solution for round
- `GET /scores/user/{userId}` - Get user's solve history
- `GET /leaderboard/global` - Get global leaderboard

### Game State Management
- `GET /rounds/{id}/state` - Get current round state
- `POST /rounds/{id}/moves` - Submit move sequence
- `POST /rounds/{id}/reset` - Reset to initial state

## Acceptance Criteria

### Core Gameplay
- [ ] Users can move robots in four directions until they hit obstacles
- [ ] Robots stop correctly (before other robots, against walls)
- [ ] Rounds complete automatically when target robot reaches target square
- [ ] Move counter accurately tracks robot movements
- [ ] Reset functionality returns to exact initial state
- [ ] Move limit (99) prevents score saving but allows continued play

### Content Management
- [ ] Users can create board configurations with wall and target placement
- [ ] Configurations require minimum one target before saving
- [ ] Targets cannot be placed in center 2x2 square
- [ ] Robots are never placed in center 2x2 square during round generation
- [ ] Robot placement collision detection prevents initial target occupation
- [ ] Users can delete own configurations without affecting existing solved rounds

### Round Generation
- [ ] New rounds generate with random robot positions and target selection
- [ ] Baseline configurations available to all users
- [ ] User configurations available only to creator until solved
- [ ] Solved rounds immediately become available for competitive play
- [ ] Unsolved rounds are not preserved or shared

### Scoring System
- [ ] Only lowest score per user per round is tracked
- [ ] Move sequences are stored and validated
- [ ] Medals assigned correctly (gold/silver/bronze for 1st/2nd/3rd place move counts)
- [ ] Ties handled by chronological order (earlier solutions rank higher)
- [ ] Global leaderboard calculates points correctly (3/2/1 for gold/silver/bronze)

### User Interface
- [ ] Clear distinction between "New Round" and "Solved Round" modes
- [ ] Round selection shows existing leaderboards for solved rounds
- [ ] Individual round leaderboards display correctly
- [ ] Global leaderboard accessible and accurate
- [ ] Configuration creation interface validates minimum requirements
- [ ] Move counter displays in real-time during gameplay

### Authentication and Permissions
- [ ] Production requires authentication, development bypasses
- [ ] mlusby@gmail.com configurations treated as baseline
- [ ] Users can only delete own configurations
- [ ] Solved rounds visible to all users regardless of creator
- [ ] Development mode provides all functionality without restrictions

### Technical Requirements
- [ ] API endpoints respond within performance requirements
- [ ] CORS headers configured correctly for frontend access
- [ ] Authentication tokens validated on protected endpoints
- [ ] Error handling provides meaningful feedback
- [ ] Data validation prevents invalid configurations/rounds/scores

### Environment Consistency
- [ ] Development and production exhibit identical behavior
- [ ] Visual indicators clearly distinguish environments
- [ ] Data separation maintained between environments
- [ ] Feature parity maintained across environments

---

*This documentation serves as the authoritative specification for the Robot Puzzle Game system. All development and modifications should be validated against these requirements to ensure consistent functionality and user experience.*