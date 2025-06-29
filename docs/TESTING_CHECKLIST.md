# Robot Puzzle Game - Testing Checklist

This document provides specific testing procedures to validate the system against the acceptance criteria defined in [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md).

## Core Gameplay Testing

### AC: Robot Movement Mechanics
- **Test ID**: CG-001
- **Requirement**: Users can move robots in four directions until they hit obstacles
- **Test Procedure**:
  1. Load any round with robots not against walls
  2. Click on a robot to select it
  3. Click in each direction (up, down, left, right) from the robot
  4. Verify robot slides until hitting wall or other robot
- **Expected Result**: Robot moves in straight line until obstacle, stops in correct square
- **Manual Verification**: Visual confirmation of robot position after movement

### AC: Obstacle Collision Detection  
- **Test ID**: CG-002
- **Requirement**: Robots stop correctly (before other robots, against walls)
- **Test Procedure**:
  1. Move robot toward another robot
  2. Move robot toward wall
  3. Verify stopping positions in both cases
- **Expected Result**: 
  - Robot stops in square just before other robot
  - Robot stops in square with wall on opposite side from entry direction
- **Manual Verification**: Check robot positions match collision rules

### AC: Victory Detection
- **Test ID**: CG-003  
- **Requirement**: Rounds complete automatically when target robot reaches target square
- **Test Procedure**:
  1. Identify target color and position for current round
  2. Move the matching colored robot to target square
  3. Verify automatic completion
- **Expected Result**: Round immediately marked as solved, score saved
- **Manual Verification**: Success message displayed, leaderboard updated

### AC: Move Counter Accuracy
- **Test ID**: CG-004
- **Requirement**: Move counter accurately tracks robot movements
- **Test Procedure**:
  1. Start new round, verify counter starts at 0
  2. Make 5 robot movements
  3. Reset round, verify counter returns to 0
  4. Make 10 more movements
- **Expected Result**: Counter shows 5 after first sequence, 0 after reset, 10 after second sequence
- **Manual Verification**: Visual counter display matches actual moves made

### AC: Reset Functionality
- **Test ID**: CG-005
- **Requirement**: Reset functionality returns to exact initial state
- **Test Procedure**:
  1. Note initial robot positions and target
  2. Make several moves
  3. Click reset button
  4. Compare current state to initial state
- **Expected Result**: All robots return to exact starting positions, move counter resets to 0
- **Manual Verification**: Visual comparison of robot positions

### AC: Move Limit Prevention
- **Test ID**: CG-006
- **Requirement**: Move limit (99) prevents score saving but allows continued play
- **Test Procedure**:
  1. Create test scenario with 98 moves made
  2. Make 99th move without solving
  3. Attempt to solve on 99th move
  4. Verify score is not saved
  5. Verify game continues to allow moves
- **Expected Result**: No score saved at 99 moves, game remains playable
- **Manual Verification**: Score submission returns appropriate error, UI remains functional

## Content Management Testing

### AC: Configuration Creation
- **Test ID**: CM-001
- **Requirement**: Users can create board configurations with wall and target placement
- **Test Procedure**:
  1. Access configuration creation interface
  2. Place walls on grid edges
  3. Place targets on grid squares
  4. Save configuration
- **Expected Result**: Configuration saved successfully with placed elements
- **Manual Verification**: Saved configuration displays correctly when loaded

### AC: Minimum Target Validation
- **Test ID**: CM-002
- **Requirement**: Configurations require minimum one target before saving
- **Test Procedure**:
  1. Create configuration with only walls, no targets
  2. Attempt to save
  3. Add one target
  4. Attempt to save again
- **Expected Result**: First save fails with validation error, second save succeeds
- **Manual Verification**: Error message displayed for first attempt, success for second

### AC: Target Placement Restrictions
- **Test ID**: CM-003
- **Requirement**: Targets cannot be placed in center 2x2 square
- **Test Procedure**:
  1. Attempt to place target in center 2x2 area (squares 7,7 7,8 8,7 8,8)
  2. Verify placement is prevented or target is automatically moved
- **Expected Result**: Target placement rejected or moved outside center area
- **Manual Verification**: No targets visible in center 2x2 squares

### AC: Robot Placement Rules
- **Test ID**: CM-004
- **Requirement**: Robots are never placed in center 2x2 square during round generation
- **Test Procedure**:
  1. Generate 10 new rounds from various configurations
  2. Check robot positions in each round
  3. Verify no robots in center 2x2 area
- **Expected Result**: No robots appear in squares 7,7 7,8 8,7 8,8 in any round
- **Manual Verification**: Visual inspection of robot positions

### AC: Robot-Target Collision Prevention
- **Test ID**: CM-005
- **Requirement**: Robot placement collision detection prevents initial target occupation
- **Test Procedure**:
  1. Generate rounds from configuration with limited available squares
  2. Verify no robot starts on target square
  3. If collision occurs, verify re-randomization happens
- **Expected Result**: Target square always empty at round start
- **Manual Verification**: Visual confirmation target square unoccupied initially

### AC: Configuration Deletion Impact
- **Test ID**: CM-006
- **Requirement**: Users can delete own configurations without affecting existing solved rounds
- **Test Procedure**:
  1. Create configuration, generate round, solve it
  2. Delete the configuration
  3. Verify solved round remains playable
  4. Verify no new rounds can be generated from deleted configuration
- **Expected Result**: Existing round accessible, new round generation unavailable
- **Manual Verification**: Solved round still in competitive list, configuration not in creation list

## Round Generation Testing

### AC: Random Robot Placement
- **Test ID**: RG-001
- **Requirement**: New rounds generate with random robot positions and target selection
- **Test Procedure**:
  1. Generate 5 rounds from same configuration
  2. Compare robot starting positions across rounds
  3. Compare target selections across rounds
- **Expected Result**: Different robot positions and/or target selections in each round
- **Manual Verification**: Visual comparison shows randomization occurring

### AC: Baseline Configuration Access
- **Test ID**: RG-002
- **Requirement**: Baseline configurations available to all users
- **Test Procedure**:
  1. Log in as non-mlusby@gmail.com user
  2. Access round generation interface
  3. Verify baseline configurations appear in available list
- **Expected Result**: Baseline configurations visible to all users
- **Manual Verification**: Configuration list includes baseline items

### AC: User Configuration Availability
- **Test ID**: RG-003
- **Requirement**: User configurations available only to creator until solved
- **Test Procedure**:
  1. User A creates configuration
  2. User B attempts to generate round from User A's configuration
  3. User A solves round from their configuration
  4. User B attempts to access solved round
- **Expected Result**: User B cannot access until solved, can access after solving
- **Manual Verification**: Configuration availability changes based on solve status

### AC: Immediate Competitive Availability
- **Test ID**: RG-004
- **Requirement**: Solved rounds immediately become available for competitive play
- **Test Procedure**:
  1. Solve a newly generated round
  2. Immediately check competitive round list
  3. Verify solved round appears in list
- **Expected Result**: Round appears in competitive list immediately after solving
- **Manual Verification**: Round visible in "Solved Rounds" section

### AC: Unsolved Round Preservation
- **Test ID**: RG-005
- **Requirement**: Unsolved rounds are not preserved or shared
- **Test Procedure**:
  1. Generate round, make some moves but don't solve
  2. Abandon round (navigate away or start new round)
  3. Verify abandoned round is not accessible to self or others
- **Expected Result**: Abandoned round disappears, not visible to any user
- **Manual Verification**: Round not in any accessible lists

## Scoring System Testing

### AC: Best Score Tracking
- **Test ID**: SS-001
- **Requirement**: Only lowest score per user per round is tracked
- **Test Procedure**:
  1. Solve same round multiple times with different move counts
  2. Check leaderboard entry for user
  3. Verify only best (lowest) score is displayed
- **Expected Result**: Leaderboard shows only the lowest move count achieved
- **Manual Verification**: Single entry per user showing best score

### AC: Move Sequence Validation
- **Test ID**: SS-002
- **Requirement**: Move sequences are stored and validated
- **Test Procedure**:
  1. Solve round with specific sequence of moves
  2. Verify score is accepted and saved
  3. Attempt to submit invalid move sequence (if possible through API)
- **Expected Result**: Valid sequences accepted, invalid sequences rejected
- **Manual Verification**: Score appears on leaderboard for valid solutions

### AC: Medal Assignment
- **Test ID**: SS-003
- **Requirement**: Medals assigned correctly (gold/silver/bronze for 1st/2nd/3rd place move counts)
- **Test Procedure**:
  1. Have multiple users solve same round with different move counts
  2. Check leaderboard medal assignments
  3. Verify gold for lowest, silver for second lowest, bronze for third lowest
- **Expected Result**: Correct medal types displayed for each ranking tier
- **Manual Verification**: Medal indicators match actual ranking positions

### AC: Tie Handling
- **Test ID**: SS-004
- **Requirement**: Ties handled by chronological order (earlier solutions rank higher)
- **Test Procedure**:
  1. Have User A solve round in X moves
  2. Have User B solve same round in X moves later
  3. Check leaderboard ordering
- **Expected Result**: User A appears before User B in leaderboard display
- **Manual Verification**: Earlier solution listed higher in tied group

### AC: Global Leaderboard Calculation
- **Test ID**: SS-005
- **Requirement**: Global leaderboard calculates points correctly (3/2/1 for gold/silver/bronze)
- **Test Procedure**:
  1. Track user's medal achievements across multiple rounds
  2. Calculate expected points (3×gold + 2×silver + 1×bronze)
  3. Compare with displayed global leaderboard points
- **Expected Result**: Displayed points match calculated points
- **Manual Verification**: Manual calculation matches system calculation

## User Interface Testing

### AC: Round Mode Distinction
- **Test ID**: UI-001
- **Requirement**: Clear distinction between "New Round" and "Solved Round" modes
- **Test Procedure**:
  1. Access round selection interface
  2. Verify clear visual/textual distinction between options
  3. Test navigation between modes
- **Expected Result**: Obvious difference in UI elements and labeling
- **Manual Verification**: User can easily distinguish between modes

### AC: Leaderboard Display in Selection
- **Test ID**: UI-002
- **Requirement**: Round selection shows existing leaderboards for solved rounds
- **Test Procedure**:
  1. Access solved rounds list
  2. Select round with existing scores
  3. Verify leaderboard is visible before starting round
- **Expected Result**: Leaderboard displayed during round selection
- **Manual Verification**: Score information visible in selection interface

### AC: Individual Round Leaderboards
- **Test ID**: UI-003
- **Requirement**: Individual round leaderboards display correctly
- **Test Procedure**:
  1. Access round with multiple scores
  2. Verify username, move count, date, medal are all displayed
  3. Verify sorting by moves (ascending), then date (ascending)
- **Expected Result**: Complete information displayed in correct order
- **Manual Verification**: All required fields visible and properly sorted

### AC: Global Leaderboard Access
- **Test ID**: UI-004
- **Requirement**: Global leaderboard accessible and accurate
- **Test Procedure**:
  1. Navigate to global leaderboard
  2. Verify username, points, medal counts displayed
  3. Verify sorting by points (descending)
- **Expected Result**: Global rankings visible with complete information
- **Manual Verification**: Comprehensive leaderboard with correct sorting

### AC: Configuration Creation Validation
- **Test ID**: UI-005
- **Requirement**: Configuration creation interface validates minimum requirements
- **Test Procedure**:
  1. Access configuration creation
  2. Attempt to save without minimum targets
  3. Verify validation feedback provided
- **Expected Result**: Clear error message preventing invalid save
- **Manual Verification**: User receives helpful validation feedback

### AC: Real-time Move Counter
- **Test ID**: UI-006
- **Requirement**: Move counter displays in real-time during gameplay
- **Test Procedure**:
  1. Start round, observe move counter at 0
  2. Make moves and observe counter updates
  3. Verify immediate updates after each move
- **Expected Result**: Counter updates immediately after each robot movement
- **Manual Verification**: Visual confirmation of immediate counter updates

## Authentication and Permissions Testing

### AC: Production Authentication Requirement
- **Test ID**: AP-001
- **Requirement**: Production requires authentication, development bypasses
- **Test Procedure**:
  1. Access production environment without authentication
  2. Verify authentication required
  3. Access development environment
  4. Verify authentication bypassed with mock user
- **Expected Result**: Production blocks unauthenticated access, development allows it
- **Manual Verification**: Different behavior in different environments

### AC: Baseline Configuration Treatment
- **Test ID**: AP-002
- **Requirement**: mlusby@gmail.com configurations treated as baseline
- **Test Procedure**:
  1. Create configuration as mlusby@gmail.com
  2. Log in as different user
  3. Verify configuration appears in available list
- **Expected Result**: mlusby@gmail.com configurations available to all users
- **Manual Verification**: Cross-user configuration accessibility

### AC: Own Configuration Deletion Rights
- **Test ID**: AP-003
- **Requirement**: Users can only delete own configurations
- **Test Procedure**:
  1. User A creates configuration
  2. User B attempts to delete User A's configuration
  3. User A attempts to delete their own configuration
- **Expected Result**: User B cannot delete, User A can delete
- **Manual Verification**: Delete option only available for own configurations

### AC: Solved Round Visibility
- **Test ID**: AP-004
- **Requirement**: Solved rounds visible to all users regardless of creator
- **Test Procedure**:
  1. User A solves round from their configuration
  2. User B accesses competitive rounds list
  3. Verify User A's solved round is visible to User B
- **Expected Result**: All solved rounds visible to all users
- **Manual Verification**: Cross-user solved round accessibility

### AC: Development Mode Functionality
- **Test ID**: AP-005
- **Requirement**: Development mode provides all functionality without restrictions
- **Test Procedure**:
  1. Test all features in development mode
  2. Compare with production feature set for mlusby@gmail.com
  3. Verify equivalent functionality available
- **Expected Result**: Development mode has complete feature access
- **Manual Verification**: Feature parity between dev mode and production baseline user

## Technical Requirements Testing

### AC: API Response Performance
- **Test ID**: TR-001
- **Requirement**: API endpoints respond within performance requirements
- **Test Procedure**:
  1. Measure response times for round generation (<2 seconds)
  2. Measure response times for move validation (<1 second)
  3. Test under normal load conditions
- **Expected Result**: Response times meet specified requirements
- **Manual Verification**: Timing measurements within acceptable ranges

### AC: CORS Configuration
- **Test ID**: TR-002
- **Requirement**: CORS headers configured correctly for frontend access
- **Test Procedure**:
  1. Make API requests from frontend application
  2. Verify no CORS-related errors in browser console
  3. Test all endpoint types (GET, POST, PUT, DELETE, OPTIONS)
- **Expected Result**: All API requests succeed without CORS errors
- **Manual Verification**: Browser console shows no CORS-related errors

### AC: Authentication Token Validation
- **Test ID**: TR-003
- **Requirement**: Authentication tokens validated on protected endpoints
- **Test Procedure**:
  1. Make API request with valid token
  2. Make API request with invalid/expired token
  3. Make API request with no token
- **Expected Result**: Valid tokens accepted, invalid tokens rejected
- **Manual Verification**: Appropriate HTTP status codes returned

### AC: Error Handling Feedback
- **Test ID**: TR-004
- **Requirement**: Error handling provides meaningful feedback
- **Test Procedure**:
  1. Trigger various error conditions (invalid data, missing fields, etc.)
  2. Verify error messages are descriptive and helpful
  3. Check error message consistency across similar conditions
- **Expected Result**: Clear, actionable error messages provided
- **Manual Verification**: Error messages help user understand and resolve issues

### AC: Data Validation Prevention
- **Test ID**: TR-005
- **Requirement**: Data validation prevents invalid configurations/rounds/scores
- **Test Procedure**:
  1. Attempt to create invalid configurations (no targets, etc.)
  2. Attempt to submit invalid scores/moves
  3. Verify system rejects invalid data
- **Expected Result**: Invalid data rejected with appropriate errors
- **Manual Verification**: System prevents corruption from invalid inputs

## Environment Consistency Testing

### AC: Behavior Consistency
- **Test ID**: EC-001
- **Requirement**: Development and production exhibit identical behavior
- **Test Procedure**:
  1. Test same workflows in both environments
  2. Compare user interface behavior
  3. Compare API response formats and content
- **Expected Result**: Identical behavior across environments (except auth)
- **Manual Verification**: Side-by-side comparison shows consistent behavior

### AC: Environment Visual Distinction
- **Test ID**: EC-002
- **Requirement**: Visual indicators clearly distinguish environments
- **Test Procedure**:
  1. Access development environment
  2. Access production environment
  3. Verify clear visual indicators of current environment
- **Expected Result**: Obvious visual cues distinguish environments
- **Manual Verification**: User can immediately identify current environment

### AC: Data Separation
- **Test ID**: EC-003
- **Requirement**: Data separation maintained between environments
- **Test Procedure**:
  1. Create data in development environment
  2. Check that data does not appear in production
  3. Create data in production
  4. Check that data does not appear in development
- **Expected Result**: Complete data isolation between environments
- **Manual Verification**: No cross-environment data contamination

### AC: Feature Parity
- **Test ID**: EC-004
- **Requirement**: Feature parity maintained across environments
- **Test Procedure**:
  1. Test all features in development
  2. Test all features in production (as appropriate user)
  3. Compare available functionality
- **Expected Result**: Same features available in both environments
- **Manual Verification**: Feature comparison shows equivalent capabilities

---

## Testing Notes

### Automation Opportunities
- Move counter accuracy testing could be automated
- API response time testing should be automated
- CORS configuration testing could be automated
- Data validation testing could be automated

### Manual Testing Priority
- User interface behavior and visual confirmation
- Cross-user permission and visibility testing
- Environment distinction and consistency
- Complex game flow scenarios

### Test Data Requirements
- Multiple user accounts for cross-user testing
- Various board configurations for comprehensive testing
- Solved rounds with different score distributions
- Invalid data samples for validation testing

---

*This checklist should be executed before any major release and after significant changes to ensure system compliance with acceptance criteria.*