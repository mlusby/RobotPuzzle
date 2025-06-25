class RobotPuzzleGame {
    constructor() {
        this.boardSize = 16;
        this.baseQuadrants = this.defineBaseQuadrants();
        this.moveCount = 0;
        this.targetColor = 'red';
        this.targetPosition = { x: 8, y: 8 };
        this.currentRound = null;
        this.moveHistory = [];
        this.personalBest = null;
        
        this.dragState = {
            isDragging: false,
            robot: null,
            startPos: null,
            currentPath: []
        };
        
        this.init();
    }
    
    defineBaseQuadrants() {
        // Define the 4 base 8x8 quadrants with corner cutouts
        // Each quadrant defined as array of wall strings in format "x,y,direction"
        // Coordinates are within each 8x8 quadrant (0-7, 0-7)
        return {
            quadrant1: [ // Top-left image analysis
                // Green robot at (1,2), yellow target at (6,1)
                '1,2,left', '2,2,bottom', '2,3,top',
                '6,4,right', '7,4,left',
                '0,5,bottom', '0,6,top',
                '2,5,bottom', '2,6,top',
                '6,6,bottom', '6,7,top'
            ],
            quadrant2: [ // Top-right image analysis  
                // Green target at (1,1), yellow robot at (6,2)
                '1,1,right', '2,1,left',
                '6,2,right', '7,2,left',
                '2,4,bottom', '2,5,top',
                '7,4,bottom', '7,5,top',
                '5,6,bottom', '5,7,top'
            ],
            quadrant3: [ // Bottom-left image analysis
                // Yellow target at (4,1), blue target at (6,2), blue robot at (4,6), red robot at (2,7)
                '4,1,bottom', '4,2,top',
                '2,2,left',
                '6,3,bottom', '6,4,top',
                '0,4,bottom', '0,5,top',
                '7,4,bottom', '7,5,top',
                '5,6,right', '6,6,left'
            ],
            quadrant4: [ // Bottom-right image analysis
                // Yellow target at (0,2), blue target at (5,3), green target at (3,6), silver robot at (6,5)
                '0,2,left',
                '3,1,bottom', '3,2,top',
                '5,3,right', '6,3,left',
                '0,5,right', '1,5,left',
                '6,6,bottom', '6,7,top',
                '3,7,bottom'
            ]
        };
    }

    rotateQuadrant(walls, rotation) {
        // Rotate wall positions and directions
        // rotation: 0, 1, 2, 3 (0°, 90°, 180°, 270°)
        return walls.map(wall => {
            const [x, y, dir] = wall.split(',');
            let newX = parseInt(x), newY = parseInt(y), newDir = dir;
            
            for (let i = 0; i < rotation; i++) {
                // Rotate 90° clockwise
                const tempX = newX;
                newX = 7 - newY;
                newY = tempX;
                
                // Rotate direction
                const dirMap = { 'top': 'right', 'right': 'bottom', 'bottom': 'left', 'left': 'top' };
                newDir = dirMap[newDir];
            }
            
            return `${newX},${newY},${newDir}`;
        });
    }

    async generateBoard() {
        const walls = new Set();
        
        // Check for custom board from board configurator
        const customBoard = localStorage.getItem('customBoard');
        if (customBoard) {
            const configData = JSON.parse(customBoard);
            if (configData.walls) {
                configData.walls.forEach(wall => walls.add(wall));
                this.availableTargets = configData.targets || [];
            } else {
                // Legacy format - just walls array
                configData.forEach(wall => walls.add(wall));
                this.availableTargets = [];
            }
            return walls;
        }
        
        // Check for saved configurations from API
        try {
            const config = await apiService.getRandomConfiguration();
            if (config) {
                config.walls.forEach(wall => walls.add(wall));
                this.availableTargets = config.targets || [];
                return walls;
            }
        } catch (error) {
            console.error('Failed to load configuration from API:', error);
        }
        
        // Default: Add walls around the center 2x2 cutout area only
        for (let x = 7; x <= 8; x++) {
            for (let y = 7; y <= 8; y++) {
                if (x === 7) walls.add(`${x},${y},left`);
                if (x === 8) walls.add(`${x},${y},right`);
                if (y === 7) walls.add(`${x},${y},top`);
                if (y === 8) walls.add(`${x},${y},bottom`);
            }
        }
        
        this.availableTargets = [];
        return walls;
    }
    
    isInCutoutArea(x, y, cutoutType) {
        // Check if position is in the corner cutout (positions 7,7 within each 8x8 quadrant)
        switch(cutoutType) {
            case 'topLeft': return x === 0 && y === 0;
            case 'topRight': return x === 7 && y === 0;
            case 'bottomLeft': return x === 0 && y === 7;
            case 'bottomRight': return x === 7 && y === 7;
            default: return false;
        }
    }

    generateRandomRobotPositions() {
        // Generate random starting positions for all robots
        const availablePositions = [];
        
        // Generate all valid positions (avoiding center 2x2 formed by cutouts)
        for (let x = 0; x < this.boardSize; x++) {
            for (let y = 0; y < this.boardSize; y++) {
                if (!((x === 7 || x === 8) && (y === 7 || y === 8))) {
                    availablePositions.push({ x, y });
                }
            }
        }
        
        // Shuffle and select 5 positions
        const shuffled = availablePositions.sort(() => Math.random() - 0.5);
        const colors = ['silver', 'green', 'red', 'yellow', 'blue'];
        const robots = {};
        
        colors.forEach((color, index) => {
            robots[color] = {
                x: shuffled[index].x,
                y: shuffled[index].y,
                color: color
            };
        });
        
        return robots;
    }

    selectRandomTarget(configuration) {
        const colors = ['silver', 'green', 'red', 'yellow', 'blue'];
        const randomColor = colors[Math.floor(Math.random() * colors.length)];
        
        // If configuration has defined targets, use one of them
        if (configuration.targets && configuration.targets.length > 0) {
            const randomTargetKey = configuration.targets[Math.floor(Math.random() * configuration.targets.length)];
            const [x, y] = randomTargetKey.split(',').map(n => parseInt(n));
            
            return {
                color: randomColor,
                x: x,
                y: y
            };
        } else {
            // Generate a random target position (avoiding center walls and invalid positions)
            let targetX, targetY;
            do {
                targetX = Math.floor(Math.random() * this.boardSize);
                targetY = Math.floor(Math.random() * this.boardSize);
            } while (
                // Avoid center walls
                ((targetX === 7 || targetX === 8) && (targetY === 7 || targetY === 8))
            );
            
            return {
                color: randomColor,
                x: targetX,
                y: targetY
            };
        }
    }

    initializeRobots() {
        const availablePositions = [];
        
        // Generate all valid positions (avoiding center 2x2 formed by cutouts)
        for (let x = 0; x < this.boardSize; x++) {
            for (let y = 0; y < this.boardSize; y++) {
                if (!((x === 7 || x === 8) && (y === 7 || y === 8))) {
                    availablePositions.push({ x, y });
                }
            }
        }
        
        // Shuffle and select 5 positions
        const shuffled = availablePositions.sort(() => Math.random() - 0.5);
        const colors = ['silver', 'green', 'red', 'yellow', 'blue'];
        const robots = {};
        
        colors.forEach((color, index) => {
            robots[color] = {
                x: shuffled[index].x,
                y: shuffled[index].y,
                color: color
            };
        });
        
        return robots;
    }
    
    async init() {
        this.walls = await this.generateBoard();
        this.robots = this.initializeRobots();
        this.initialRobots = JSON.parse(JSON.stringify(this.robots));
        this.createBoard();
        this.placeRobots();
        this.updateTarget();
        this.setupEventListeners();
        this.updateMoveCounter();
    }
    
    createBoard() {
        const board = document.getElementById('game-board');
        board.innerHTML = '';
        
        for (let y = 0; y < this.boardSize; y++) {
            for (let x = 0; x < this.boardSize; x++) {
                const square = document.createElement('div');
                square.className = 'square';
                square.dataset.x = x;
                square.dataset.y = y;
                
                // Add center wall styling
                if ((x === 7 || x === 8) && (y === 7 || y === 8)) {
                    square.classList.add('center-wall');
                }
                
                // Add wall borders
                if (this.walls.has(`${x},${y},top`)) square.classList.add('wall-top');
                if (this.walls.has(`${x},${y},bottom`)) square.classList.add('wall-bottom');
                if (this.walls.has(`${x},${y},left`)) square.classList.add('wall-left');
                if (this.walls.has(`${x},${y},right`)) square.classList.add('wall-right');
                
                board.appendChild(square);
            }
        }
    }
    
    placeRobots() {
        // Clear existing robots first
        document.querySelectorAll('.robot').forEach(robot => robot.remove());
        
        // Safety check for robots object
        if (!this.robots) {
            console.error('Robots object is not initialized');
            return;
        }
        
        Object.values(this.robots).forEach(robot => {
            if (!robot || typeof robot.x === 'undefined' || typeof robot.y === 'undefined') {
                console.error('Invalid robot data:', robot);
                return;
            }
            
            const robotEl = document.createElement('div');
            robotEl.className = `robot ${robot.color}`;
            robotEl.dataset.color = robot.color;
            
            const square = this.getSquareElement(robot.x, robot.y);
            if (square) {
                square.appendChild(robotEl);
            } else {
                console.error('Square not found for robot at position:', robot.x, robot.y);
            }
        });
    }
    
    getSquareElement(x, y) {
        return document.querySelector(`[data-x="${x}"][data-y="${y}"]`);
    }
    
    updateTarget() {
        // Check if we have configured target positions
        if (this.availableTargets && this.availableTargets.length > 0) {
            // Use a configured target position
            const randomTargetKey = this.availableTargets[Math.floor(Math.random() * this.availableTargets.length)];
            const [x, y] = randomTargetKey.split(',').map(n => parseInt(n));
            
            this.targetPosition.x = x;
            this.targetPosition.y = y;
            
            // Randomly assign a color
            const colors = Object.keys(this.robots);
            this.targetColor = colors[Math.floor(Math.random() * colors.length)];
        } else {
            // Generate random target (fallback behavior)
            const colors = Object.keys(this.robots);
            this.targetColor = colors[Math.floor(Math.random() * colors.length)];
            
            // Generate random target position (avoiding center walls and robot positions)
            do {
                this.targetPosition.x = Math.floor(Math.random() * this.boardSize);
                this.targetPosition.y = Math.floor(Math.random() * this.boardSize);
            } while (
                this.isOccupied(this.targetPosition.x, this.targetPosition.y) ||
                ((this.targetPosition.x === 7 || this.targetPosition.x === 8) && 
                 (this.targetPosition.y === 7 || this.targetPosition.y === 8))
            );
        }
        
        this.updateTargetUI();
    }
    
    updateTargetUI() {
        // Update the target UI without changing the target data
        document.getElementById('target-color').textContent = this.targetColor;
        document.getElementById('target-color').style.color = this.getColorHex(this.targetColor);
        
        const targetSquare = document.getElementById('target-square');
        const targetGridSquare = this.getSquareElement(this.targetPosition.x, this.targetPosition.y);
        const gameBoard = document.getElementById('game-board');
        const gameBoardContainer = document.querySelector('.game-board-container');
        
        // Get actual positions relative to the container
        const squareRect = targetGridSquare.getBoundingClientRect();
        const containerRect = gameBoardContainer.getBoundingClientRect();
        
        // Position target square relative to game board container
        targetSquare.style.left = `${squareRect.left - containerRect.left}px`;
        targetSquare.style.top = `${squareRect.top - containerRect.top}px`;
        targetSquare.style.width = `${squareRect.width}px`;
        targetSquare.style.height = `${squareRect.height}px`;
        targetSquare.style.backgroundColor = this.getColorHex(this.targetColor);
        targetSquare.style.opacity = '0.6';
    }
    
    getColorHex(color) {
        const colors = {
            silver: '#c0c0c0',
            green: '#4CAF50',
            red: '#f44336',
            yellow: '#FFEB3B',
            blue: '#2196F3'
        };
        return colors[color];
    }
    
    isOccupied(x, y) {
        return Object.values(this.robots).some(robot => robot.x === x && robot.y === y);
    }
    
    hasWall(x, y, direction) {
        const wallKey = `${x},${y},${direction}`;
        return this.walls.has(wallKey);
    }
    
    canMoveTo(fromX, fromY, toX, toY, direction) {
        // Check bounds
        if (toX < 0 || toX >= this.boardSize || toY < 0 || toY >= this.boardSize) {
            return false;
        }
        
        // Check walls
        if (this.hasWall(fromX, fromY, direction)) {
            return false;
        }
        
        // Check opposite wall on destination
        const oppositeDir = {
            'right': 'left',
            'left': 'right',
            'top': 'bottom',
            'bottom': 'top'
        };
        
        if (this.hasWall(toX, toY, oppositeDir[direction])) {
            return false;
        }
        
        return true;
    }
    
    calculatePath(robot, direction) {
        const path = [];
        let x = robot.x;
        let y = robot.y;
        
        const dx = direction === 'right' ? 1 : direction === 'left' ? -1 : 0;
        const dy = direction === 'bottom' ? 1 : direction === 'top' ? -1 : 0;
        
        while (true) {
            const nextX = x + dx;
            const nextY = y + dy;
            
            // Check if we can move to next position
            if (!this.canMoveTo(x, y, nextX, nextY, direction)) {
                break;
            }
            
            // Check if there's another robot blocking
            if (this.isOccupied(nextX, nextY)) {
                break;
            }
            
            x = nextX;
            y = nextY;
            path.push({ x, y });
        }
        
        return path;
    }
    
    getDirection(startX, startY, endX, endY) {
        const dx = endX - startX;
        const dy = endY - startY;
        
        if (Math.abs(dx) > Math.abs(dy)) {
            return dx > 0 ? 'right' : 'left';
        } else {
            return dy > 0 ? 'bottom' : 'top';
        }
    }
    
    moveRobot(robotColor, newX, newY) {
        const robot = this.robots[robotColor];
        const robotEl = document.querySelector(`.robot.${robotColor}`);
        
        // Remove from current position
        robotEl.remove();
        
        // Update robot position
        robot.x = newX;
        robot.y = newY;
        
        // Place at new position with animation
        const newSquare = this.getSquareElement(newX, newY);
        newSquare.appendChild(robotEl);
        
        // Trigger animation
        robotEl.style.transform = 'scale(1.2)';
        setTimeout(() => {
            robotEl.style.transform = 'scale(1)';
        }, 200);
        
        // Record the move
        this.moveHistory.push({
            robot: robotColor,
            fromX: this.dragState.startPos.x,
            fromY: this.dragState.startPos.y,
            toX: newX,
            toY: newY,
            moveNumber: this.moveCount + 1
        });
        
        this.moveCount++;
        this.updateMoveCounter();
        this.checkWin();
    }
    
    checkWin() {
        const targetRobot = this.robots[this.targetColor];
        if (targetRobot.x === this.targetPosition.x && targetRobot.y === this.targetPosition.y) {
            setTimeout(async () => {
                await this.onGameComplete();
            }, 500);
        }
    }
    
    updateMoveCounter() {
        document.getElementById('move-count').textContent = this.moveCount;
    }
    
    clearPathPreview() {
        document.querySelectorAll('.path-preview, .path-end').forEach(square => {
            square.classList.remove('path-preview', 'path-end');
        });
    }
    
    showPathPreview(path) {
        this.clearPathPreview();
        
        path.forEach((pos, index) => {
            const square = this.getSquareElement(pos.x, pos.y);
            if (index === path.length - 1) {
                square.classList.add('path-end');
            } else {
                square.classList.add('path-preview');
            }
        });
    }
    
    setupEventListeners() {
        const board = document.getElementById('game-board');
        
        // Mouse events
        board.addEventListener('mousedown', this.handleStart.bind(this));
        document.addEventListener('mousemove', this.handleMove.bind(this));
        document.addEventListener('mouseup', this.handleEnd.bind(this));
        
        // Touch events
        board.addEventListener('touchstart', this.handleStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleEnd.bind(this));
        
        // Reset button
        document.getElementById('reset-btn').addEventListener('click', this.reset.bind(this));
        
        // New Round button
        document.getElementById('new-round-btn').addEventListener('click', this.loadNewRound.bind(this));
        
        // Round type selector
        const roundTypeSelector = document.getElementById('round-type-selector');
        if (roundTypeSelector) {
            roundTypeSelector.addEventListener('change', this.loadNewRound.bind(this));
        } else {
            console.error('Round type selector not found in DOM');
        }
        
        // Leaderboard button
        document.getElementById('leaderboard-btn').addEventListener('click', this.showLeaderboard.bind(this));
        
        // Sign out button
        document.getElementById('sign-out-btn').addEventListener('click', () => {
            authService.signOut();
            window.location.href = 'login.html';
        });
        
        // Wall editor button
        document.getElementById('editor-btn').addEventListener('click', () => {
            window.open('wall-editor.html', '_blank');
        });

        // Add debug handler for creating initial data if needed
        if (window.location.search.includes('debug=init')) {
            setTimeout(() => this.initializeBaselineData(), 3000);
        }

        // Modal close handlers
        document.querySelector('#leaderboard-modal .close').addEventListener('click', () => {
            document.getElementById('leaderboard-modal').style.display = 'none';
        });

        // Completion modal handlers
        document.getElementById('view-leaderboard-btn').addEventListener('click', this.showLeaderboard.bind(this));
        document.getElementById('new-round-completion-btn').addEventListener('click', this.loadNewRound.bind(this));
        document.getElementById('close-completion-btn').addEventListener('click', () => {
            document.getElementById('completion-modal').style.display = 'none';
        });

        // Close modals when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                e.target.style.display = 'none';
            }
        });
    }
    
    handleStart(e) {
        e.preventDefault();
        const target = e.target;
        
        if (!target.classList.contains('robot')) return;
        
        const robotColor = target.dataset.color;
        const robot = this.robots[robotColor];
        
        // Safety check for robot existence
        if (!robot) {
            console.error('Robot not found for color:', robotColor);
            return;
        }
        
        this.dragState = {
            isDragging: true,
            robot: robotColor,
            startPos: { x: robot.x, y: robot.y },
            currentPath: []
        };
    }
    
    handleMove(e) {
        if (!this.dragState.isDragging) return;
        
        e.preventDefault();
        const clientX = e.clientX || (e.touches && e.touches[0].clientX);
        const clientY = e.clientY || (e.touches && e.touches[0].clientY);
        
        const board = document.getElementById('game-board');
        const rect = board.getBoundingClientRect();
        const squareSize = rect.width / this.boardSize;
        
        const x = Math.floor((clientX - rect.left) / squareSize);
        const y = Math.floor((clientY - rect.top) / squareSize);
        
        if (x < 0 || x >= this.boardSize || y < 0 || y >= this.boardSize) {
            this.clearPathPreview();
            return;
        }
        
        const robot = this.robots[this.dragState.robot];
        const direction = this.getDirection(robot.x, robot.y, x, y);
        const path = this.calculatePath(robot, direction);
        
        this.dragState.currentPath = path;
        this.showPathPreview(path);
    }
    
    handleEnd(e) {
        if (!this.dragState.isDragging) return;
        
        const robot = this.robots[this.dragState.robot];
        const path = this.dragState.currentPath;
        
        // Only move if there's a valid path and we're not on the starting square
        if (path.length > 0) {
            const endPos = path[path.length - 1];
            this.moveRobot(this.dragState.robot, endPos.x, endPos.y);
        }
        
        this.clearPathPreview();
        this.dragState = {
            isDragging: false,
            robot: null,
            startPos: null,
            currentPath: []
        };
    }
    
    reset() {
        // Reset robots to initial positions only
        this.robots = JSON.parse(JSON.stringify(this.initialRobots));
        this.moveCount = 0;
        this.moveHistory = [];
        
        // Clear board and rebuild with same layout
        document.querySelectorAll('.robot').forEach(robot => robot.remove());
        this.placeRobots();
        this.updateMoveCounter();
        this.clearPathPreview();
    }
    
    async nextPuzzle() {
        // Generate new random board and setup
        this.walls = await this.generateBoard();
        this.robots = this.initializeRobots();
        this.initialRobots = JSON.parse(JSON.stringify(this.robots));
        this.moveCount = 0;
        
        // Rebuild everything for new puzzle
        this.createBoard();
        this.placeRobots();
        this.updateTarget();
        this.updateMoveCounter();
        this.clearPathPreview();
    }

    async loadNewRound() {
        try {
            const roundTypeSelector = document.getElementById('round-type-selector');
            if (!roundTypeSelector) {
                console.error('Round type selector not found, falling back to new round generation');
                await this.generateNewRound();
                return;
            }
            const roundType = roundTypeSelector.value;
            
            if (roundType === 'new') {
                // Generate a new round from available configurations
                await this.generateNewRound();
            } else {
                // Load a previously solved round
                await this.loadSolvedRound();
            }
        } catch (error) {
            console.error('Failed to load new round:', error);
            // Only show alert if this is a user-initiated action
            if (this.currentRound) {
                alert('Failed to load new round. Please try again.');
            }
            throw error; // Re-throw for caller to handle
        }
    }

    async generateNewRound() {
        try {
            // Get available board configurations
            const configurations = await apiService.getConfigurations();
            const configIds = Object.keys(configurations);
            
            if (configIds.length === 0) {
                console.log('No board configurations available. Please create some configurations first.');
                if (this.currentRound) {
                    alert('No board configurations available. Please create some configurations first.');
                }
                return;
            }
            
            // Select a random configuration
            const randomConfigId = configIds[Math.floor(Math.random() * configIds.length)];
            const selectedConfig = configurations[randomConfigId];
            
            // Generate random robot starting positions
            const robotPositions = this.generateRandomRobotPositions();
            
            // Select a random target from the configuration's targets, or generate one
            const targetPosition = this.selectRandomTarget(selectedConfig);
            
            // Create a new round object (not saved to database yet)
            const newRound = {
                roundId: `temp-${Date.now()}`, // Temporary ID until solved
                configId: randomConfigId,
                configuration: selectedConfig,
                initialRobotPositions: robotPositions,
                targetPositions: targetPosition,
                walls: selectedConfig.walls,
                targets: selectedConfig.targets || [],
                isTemporary: true // Flag to indicate this hasn't been saved yet
            };
            
            await this.loadRound(newRound);
            console.log('🎲 Generated new round from configuration', randomConfigId);
        } catch (error) {
            console.error('Failed to generate new round:', error);
            throw error;
        }
    }

    async loadSolvedRound() {
        try {
            console.log('🔍 Loading competitive rounds...');
            
            // Get a random round that has been solved (preserves original state)
            const round = await apiService.getRandomSolvedRound();
            
            console.log('🔍 Solved rounds API response:', round);
            
            if (!round) {
                console.log('❌ No solved rounds found in database');
                if (this.currentRound) {
                    alert('No competitive rounds available yet.\n\nComplete some puzzles in "Practice" mode first to create competitive rounds!\n\nThen switch back to "Competitive Rounds" to play those exact same puzzles.');
                }
                // Fall back to generating a new round for now
                console.log('🔄 Falling back to practice mode');
                await this.generateNewRound();
                return;
            }

            // Mark as not temporary since this is an existing solved round
            round.isTemporary = false;
            
            await this.loadRound(round);
            
            // Show notification that this is a competitive round
            if (round.roundId) {
                console.log('🏆 Competitive Round Loaded:', round.roundId);
                console.log('🎯 This round preserves the exact puzzle state from when it was first solved');
                console.log('🎮 Robot positions:', round.initialRobotPositions);
                console.log('🎯 Target:', round.targetPositions);
            }
        } catch (error) {
            console.error('❌ Failed to load competitive round:', error);
            // Fall back to generating a new round
            console.log('🔄 Falling back to practice mode due to error');
            await this.generateNewRound();
        }
    }

    async loadRound(round) {
        this.currentRound = round;
        this.moveCount = 0;
        this.moveHistory = [];
        
        // Set up the board from round data
        this.walls = new Set(round.walls || []);
        
        // Set robot positions from round
        this.robots = round.initialRobotPositions;
        this.initialRobots = JSON.parse(JSON.stringify(this.robots));
        
        // Set target from round (preserved state)
        const targetData = round.targetPositions;
        this.targetColor = targetData.color;
        this.targetPosition = { x: targetData.x, y: targetData.y };
        
        // Load personal best for this round
        await this.loadPersonalBest();
        
        // Rebuild the UI
        this.createBoard();
        this.placeRobots();
        this.updateTargetUI(); // Use updateTargetUI to preserve target data
        this.updateMoveCounter();
        this.clearPathPreview();
        
        // Store round ID for score submission
        document.getElementById('round-id').textContent = round.roundId;
    }

    async loadPersonalBest() {
        if (!this.currentRound) return;
        
        try {
            const userScores = await apiService.getUserScores();
            const roundScore = userScores.find(score => score.roundId === this.currentRound.roundId);
            
            if (roundScore) {
                this.personalBest = roundScore.moves;
                document.getElementById('personal-best').textContent = `Personal Best: ${roundScore.moves} moves`;
            } else {
                this.personalBest = null;
                document.getElementById('personal-best').textContent = '';
            }
        } catch (error) {
            console.error('Failed to load personal best:', error);
            this.personalBest = null;
            document.getElementById('personal-best').textContent = '';
        }
    }

    async onGameComplete() {
        if (!this.currentRound) {
            // Fallback to old behavior if no round is loaded
            return;
        }

        try {
            let roundIdToSubmit = this.currentRound.roundId;

            // If this is a temporary round, save it to the database first
            if (this.currentRound.isTemporary) {
                console.log('💾 Saving temporary round to database...');
                
                const roundData = {
                    initialRobotPositions: this.initialRobots,
                    targetPositions: this.currentRound.targetPositions
                };

                try {
                    const roundResult = await apiService.createRound(this.currentRound.configId, roundData);
                    roundIdToSubmit = roundResult.roundId;
                    
                    // Update current round to no longer be temporary
                    this.currentRound.roundId = roundIdToSubmit;
                    this.currentRound.isTemporary = false;
                    
                    console.log('✅ Round saved with ID:', roundIdToSubmit);
                } catch (roundError) {
                    console.error('Failed to save round to database:', roundError);
                    // Continue with temporary ID for local storage in development
                    if (!ENV.isDevelopment()) {
                        throw roundError;
                    }
                }
            }

            // Submit the score
            const scoreData = {
                moves: this.moveCount,
                moveSequence: this.moveHistory
            };

            const result = await apiService.submitScore(roundIdToSubmit, scoreData);
            
            // Show completion modal
            this.showCompletionModal(result);
            
            // Update personal best display
            await this.loadPersonalBest();
            
        } catch (error) {
            console.error('Failed to submit score:', error);
            alert('Congratulations on completing the puzzle! However, there was an error saving your score.');
        }
    }

    showCompletionModal(scoreResult) {
        const modal = document.getElementById('completion-modal');
        const content = document.getElementById('completion-content');
        
        let statusMessage = '';
        let isPersonalBest = false;
        
        if (scoreResult.personalBest) {
            statusMessage = 'New Personal Best!';
            isPersonalBest = true;
        } else if (scoreResult.message.includes('not improved')) {
            statusMessage = `Current best: ${scoreResult.currentBest} moves`;
        } else {
            statusMessage = 'Score submitted successfully!';
        }
        
        content.innerHTML = `
            <div class="completion-stats">
                <div class="stat ${isPersonalBest ? 'personal-best-indicator' : ''}">
                    <span class="stat-value">${this.moveCount}</span>
                    <span class="stat-label">Moves</span>
                </div>
                <div class="stat">
                    <span class="stat-value">${this.personalBest || 'N/A'}</span>
                    <span class="stat-label">Personal Best</span>
                </div>
            </div>
            <p style="text-align: center; font-weight: bold; color: ${isPersonalBest ? '#4CAF50' : '#666'};">
                ${statusMessage}
            </p>
        `;
        
        modal.style.display = 'block';
    }

    async showLeaderboard() {
        if (!this.currentRound) {
            alert('Load a round first to view the leaderboard!');
            return;
        }

        try {
            console.log('📊 Loading leaderboard for round:', this.currentRound.roundId);
            const leaderboard = await apiService.getLeaderboard(this.currentRound.roundId);
            console.log('📊 Leaderboard data:', leaderboard);
            this.displayLeaderboard(leaderboard);
        } catch (error) {
            console.error('Failed to load leaderboard:', error);
            alert('Failed to load leaderboard. Please try again.');
        }
    }

    displayLeaderboard(scores) {
        const modal = document.getElementById('leaderboard-modal');
        const content = document.getElementById('leaderboard-content');
        
        const roundInfo = this.currentRound.isTemporary ? 
            `<p><strong>Round:</strong> Practice Round (not competitive)</p>` :
            `<p><strong>Round:</strong> ${this.currentRound.roundId} (Competitive)</p>`;
        
        if (scores.length === 0) {
            content.innerHTML = roundInfo + '<p>No scores recorded for this round yet. Be the first to compete!</p>';
        } else {
            const currentUserId = authService.getCurrentUser().sub;
            
            let tableHTML = roundInfo + `
                <table class="leaderboard-table">
                    <thead>
                        <tr>
                            <th class="leaderboard-rank">Rank</th>
                            <th>Player</th>
                            <th class="leaderboard-moves">Moves</th>
                            <th>Completed</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            scores.forEach((score, index) => {
                const isCurrentUser = score.userId === currentUserId;
                const completedDate = new Date(score.completedAt).toLocaleDateString();
                
                tableHTML += `
                    <tr class="${isCurrentUser ? 'current-user' : ''}">
                        <td class="leaderboard-rank">${index + 1}</td>
                        <td>${isCurrentUser ? 'You' : 'Player'}</td>
                        <td class="leaderboard-moves">${score.moves}</td>
                        <td>${completedDate}</td>
                    </tr>
                `;
            });
            
            tableHTML += '</tbody></table>';
            content.innerHTML = tableHTML;
        }
        
        modal.style.display = 'block';
    }

    // Debug method to initialize baseline data
    async initializeBaselineData() {
        try {
            console.log('🔧 Initializing baseline data...');
            
            // Create a few baseline configurations first
            const baselineConfigs = [
                {
                    walls: [
                        '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                        '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right',
                        '2,3,bottom', '5,7,right', '10,12,left', '13,8,top'
                    ],
                    targets: ['8,8']
                },
                {
                    walls: [
                        '7,7,left', '7,7,top', '8,7,top', '8,7,right',
                        '7,8,left', '7,8,bottom', '8,8,bottom', '8,8,right',
                        '1,1,right', '14,14,left', '6,9,bottom', '11,4,top'
                    ],
                    targets: ['8,8']
                }
            ];

            // Create configurations
            for (let i = 0; i < baselineConfigs.length; i++) {
                try {
                    const result = await apiService.createConfiguration(baselineConfigs[i]);
                    console.log(`✅ Created baseline configuration #${result.configId}`);
                    
                    // Create a round for this configuration
                    const roundData = {
                        initialRobotPositions: {
                            silver: { x: 2, y: 3 },
                            green: { x: 5, y: 7 },
                            red: { x: 10, y: 12 },
                            yellow: { x: 13, y: 8 },
                            blue: { x: 8, y: 2 }
                        },
                        targetPositions: { color: 'red', x: 8, y: 8 }
                    };
                    
                    const roundResult = await apiService.createRound(result.configId, roundData);
                    console.log(`✅ Created baseline round ${roundResult.roundId}`);
                    
                } catch (error) {
                    console.error(`❌ Failed to create baseline data ${i + 1}:`, error);
                }
            }
            
            console.log('🎉 Baseline data initialization complete!');
            alert('Baseline data initialized! Refresh the page to see new rounds.');
            
        } catch (error) {
            console.error('Failed to initialize baseline data:', error);
        }
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication first
    if (!authService.isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }
    
    const game = new RobotPuzzleGame();
    
    // Try to load initial round after authentication is stable
    setTimeout(async () => {
        try {
            // Wait for auth service to be fully ready
            await new Promise(resolve => setTimeout(resolve, 2000));
            await game.loadNewRound();
        } catch (error) {
            console.error('Failed to load initial round, using fallback:', error);
            // Fallback to original behavior - just show the game without rounds
            console.log('Game loaded with default configuration');
        }
    }, 1000);
});