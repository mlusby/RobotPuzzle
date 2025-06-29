import json
import boto3
import os
from decimal import Decimal
import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
rounds_table = dynamodb.Table(os.environ['ROUNDS_TABLE'])

def lambda_handler(event, context):
    """
    Main Lambda handler for rounds operations
    """
    try:
        http_method = event.get('httpMethod', 'UNKNOWN')
        path = event.get('path', '')
        
        # Extract user ID from Cognito JWT token
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub')
        user_email = claims.get('email')
        
        logger.info(f"Processing {http_method} request for path: {path}")
        logger.info(f"User ID: {user_id}, Email: {user_email}")
        
        # Handle different HTTP methods and paths
        if http_method == 'GET':
            if '/config/' in path:
                # Handle /rounds/config/{id}
                return handle_get_round_config(event, user_id, user_email)
            else:
                # Handle /rounds
                return handle_get_rounds(event, user_id, user_email)
        elif http_method == 'POST':
            if '/config/' in path:
                # Handle /rounds/config/{id} - extract configId from path
                return handle_create_round_with_config_id(event, user_id, user_email)
            else:
                # Handle /rounds
                return handle_create_round(event, user_id, user_email)
        elif http_method == 'DELETE':
            return handle_delete_round(event, user_id, user_email)
        else:
            return create_response(405, {'error': 'Method not allowed'})
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return create_response(500, {'error': 'Internal server error'})

def handle_get_rounds(event, user_id, user_email):
    """Get all rounds, optionally filtered by author"""
    try:
        # Scan all rounds (in production, you might want to add pagination)
        response = rounds_table.scan()
        rounds = response.get('Items', [])
        
        # Convert Decimal objects to regular numbers for JSON serialization
        rounds = convert_decimals(rounds)
        
        logger.info(f"Retrieved {len(rounds)} rounds")
        return create_response(200, rounds)
        
    except Exception as e:
        logger.error(f"Error getting rounds: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve rounds'})

def handle_create_round(event, user_id, user_email):
    """Create a new round"""
    try:
        # Handle case where body might be None
        raw_body = event.get('body')
        if not raw_body:
            return create_response(400, {'error': 'Request body is required'})
        
        body = json.loads(raw_body)
        
        # Validate required fields
        if 'roundName' not in body or 'puzzleStates' not in body:
            return create_response(400, {'error': 'Missing required fields: roundName, puzzleStates'})
        
        # Generate round ID
        round_id = f"round_{int(datetime.datetime.now().timestamp() * 1000)}"
        
        # Create round item
        round_item = {
            'roundId': round_id,
            'roundName': body['roundName'],
            'puzzleStates': body['puzzleStates'],
            'authorEmail': user_email,
            'authorId': user_id,
            'createdAt': datetime.datetime.now().isoformat()
        }
        
        # Add optional fields if present
        if 'configId' in body:
            round_item['configId'] = body['configId']
        
        # Save to DynamoDB
        rounds_table.put_item(Item=round_item)
        
        logger.info(f"Created round: {round_id}")
        return create_response(201, round_item)
        
    except Exception as e:
        logger.error(f"Error creating round: {str(e)}")
        return create_response(500, {'error': 'Failed to create round'})

def handle_create_round_with_config_id(event, user_id, user_email):
    """Create a new round with configId from URL path"""
    try:
        # Extract configId from path /rounds/config/{id}
        path_parts = event['path'].split('/')
        if len(path_parts) < 4:
            return create_response(400, {'error': 'Config ID is required in path'})
        
        config_id = path_parts[3]  # /rounds/config/{id}
        
        # Handle case where body might be None
        raw_body = event.get('body')
        if not raw_body:
            return create_response(400, {'error': 'Request body is required'})
        
        body = json.loads(raw_body)
        
        # Validate required fields (relaxed for legacy compatibility)
        round_name = body.get('roundName') or f"Round from config {config_id}"
        
        # Create puzzle states from the request data
        puzzle_states = []
        if 'puzzleStates' in body:
            puzzle_states = body['puzzleStates']
        else:
            # Legacy format - create puzzle state from individual fields
            puzzle_state = {}
            if 'initialRobotPositions' in body:
                puzzle_state['initialRobotPositions'] = body['initialRobotPositions']
            if 'targetPositions' in body:
                puzzle_state['targetPosition'] = body['targetPositions']
            if 'walls' in body:
                puzzle_state['walls'] = body['walls']
            if 'targets' in body:
                puzzle_state['targets'] = body['targets']
            
            if puzzle_state:
                puzzle_states = [puzzle_state]
        
        if not puzzle_states:
            return create_response(400, {'error': 'puzzleStates or legacy round data is required'})
        
        # Generate round ID
        round_id = f"round_{int(datetime.datetime.now().timestamp() * 1000)}"
        
        # Create round item
        round_item = {
            'roundId': round_id,
            'roundName': round_name,
            'puzzleStates': puzzle_states,
            'configId': config_id,
            'authorEmail': user_email,
            'authorId': user_id,
            'createdAt': datetime.datetime.now().isoformat()
        }
        
        # Save to DynamoDB
        rounds_table.put_item(Item=round_item)
        
        logger.info(f"Created round with config ID: {round_id}")
        return create_response(201, round_item)
        
    except Exception as e:
        logger.error(f"Error creating round with config ID: {str(e)}")
        return create_response(500, {'error': 'Failed to create round'})

def handle_delete_round(event, user_id, user_email):
    """Delete a round (only by the author)"""
    try:
        # Extract round ID from path
        path_parts = event['path'].split('/')
        if len(path_parts) < 3:
            return create_response(400, {'error': 'Round ID is required'})
        
        round_id = path_parts[2]  # /rounds/{roundId}
        
        # Get the round to check ownership
        response = rounds_table.get_item(Key={'roundId': round_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Round not found'})
        
        round_item = response['Item']
        
        # Check if user is the author
        if round_item.get('authorEmail') != user_email:
            return create_response(403, {'error': 'You can only delete your own rounds'})
        
        # Delete the round
        rounds_table.delete_item(Key={'roundId': round_id})
        
        logger.info(f"Deleted round: {round_id}")
        return create_response(200, {'message': 'Round deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting round: {str(e)}")
        return create_response(500, {'error': 'Failed to delete round'})

def handle_get_round_config(event, user_id, user_email):
    """Get configuration for a specific round by ID"""
    try:
        # Extract round ID from path /rounds/config/{id}
        path_parts = event['path'].split('/')
        if len(path_parts) < 4:
            return create_response(400, {'error': 'Round ID is required'})
        
        round_id = path_parts[3]  # /rounds/config/{id}
        
        logger.info(f"Getting round config for ID: {round_id}")
        
        # Get the round from database
        response = rounds_table.get_item(Key={'roundId': round_id})
        
        if 'Item' not in response:
            return create_response(404, {'error': 'Round not found'})
        
        round_item = response['Item']
        round_item = convert_decimals(round_item)
        
        logger.info(f"Retrieved round config: {round_item}")
        return create_response(200, round_item)
        
    except Exception as e:
        logger.error(f"Error getting round config: {str(e)}")
        return create_response(500, {'error': 'Failed to retrieve round configuration'})

def convert_decimals(obj):
    """Convert DynamoDB Decimal objects to regular numbers for JSON serialization"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert to int if it's a whole number, otherwise to float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj

def create_response(status_code, body):
    """Create a standard HTTP response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': 'http://robot-puzzle-game-prod-website.s3-website-us-east-1.amazonaws.com',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS'
        },
        'body': json.dumps(body) if body else ''
    }