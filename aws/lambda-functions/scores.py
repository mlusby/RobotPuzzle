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
scores_table = dynamodb.Table(os.environ['SCORES_TABLE'])
configs_table = dynamodb.Table(os.environ['CONFIGS_TABLE'])

def lambda_handler(event, context):
    """
    Main Lambda handler for scores and leaderboard operations
    Handles both leaderboard retrieval and score submission
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        # Extract basic request information
        http_method = event.get('httpMethod', 'UNKNOWN')
        path = event.get('path', '')
        
        logger.info(f"HTTP Method: {http_method}, Path: {path}")
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            logger.info("Handling CORS preflight request")
            return cors_response()
        
        # Extract user information from JWT token
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        user_id = claims.get('sub')
        user_email = claims.get('email')
        
        logger.info(f"User ID: {user_id}, User Email: {user_email}")
        
        if not user_id:
            logger.error("No user ID found in JWT claims")
            return error_response(401, 'Unauthorized: No user ID found')
        
        # Route to appropriate handler based on method and path
        if http_method == 'GET':
            path_params = event.get('pathParameters') or {}
            round_id = path_params.get('roundId')
            
            logger.info(f"GET request - Round ID: {round_id}")
            
            if round_id:
                # GET /scores/{roundId} - Get leaderboard for specific round
                return get_leaderboard(round_id)
            else:
                # GET /scores - Get user's personal scores
                return get_user_scores(user_id)
                
        elif http_method == 'POST':
            path_params = event.get('pathParameters') or {}
            round_id = path_params.get('roundId')
            
            # Parse request body first to potentially get roundId from body
            try:
                body = event.get('body', '{}')
                if isinstance(body, str):
                    score_data = json.loads(body)
                else:
                    score_data = body
                    
                logger.info(f"Score data received: {score_data}")
                
                # If no roundId in path, try to get it from request body
                if not round_id:
                    round_id = score_data.get('roundId')
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in request body: {e}")
                return error_response(400, 'Invalid JSON in request body')
            
            logger.info(f"POST request - Round ID: {round_id}")
            
            if not round_id:
                logger.error("No roundId provided in path or body for score submission")
                return error_response(400, 'roundId is required for score submission (in path or body)')
            
            # POST /scores or /scores/{roundId} - Submit score for specific round
            return submit_score(user_id, round_id, score_data, user_email)
            
        else:
            logger.error(f"Unsupported HTTP method: {http_method}")
            return error_response(405, 'Method not allowed')
        
    except KeyError as e:
        logger.error(f"Missing required parameter: {e}")
        return error_response(400, f'Missing required parameter: {str(e)}')
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return error_response(500, f'Internal server error: {str(e)}')

def get_leaderboard(round_id):
    """
    Get leaderboard for a specific round
    """
    logger.info(f"Getting leaderboard for round: {round_id}")
    
    try:
        response = scores_table.query(
            IndexName='LeaderboardIndex',
            KeyConditionExpression='roundId = :roundId',
            ExpressionAttributeValues={':roundId': round_id},
            ScanIndexForward=True  # Sort by moves ascending (best scores first)
        )
        
        logger.info(f"Found {len(response['Items'])} scores for round {round_id}")
        
        return success_response(response['Items'])
        
    except Exception as e:
        logger.error(f"Failed to get leaderboard for round {round_id}: {e}")
        return error_response(500, f'Failed to get leaderboard: {str(e)}')

def get_user_scores(user_id):
    """
    Get all scores for a specific user
    """
    logger.info(f"Getting scores for user: {user_id}")
    
    try:
        response = scores_table.scan(
            FilterExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        logger.info(f"Found {len(response['Items'])} scores for user {user_id}")
        
        return success_response(response['Items'])
        
    except Exception as e:
        logger.error(f"Failed to get user scores for {user_id}: {e}")
        return error_response(500, f'Failed to get user scores: {str(e)}')

def submit_score(user_id, round_id, score_data, user_email):
    """
    Submit a score for a specific round
    """
    logger.info(f"Submitting score for user {user_id}, round {round_id}")
    logger.info(f"Score data: {score_data}")
    
    try:
        # Validate score data
        if 'moves' not in score_data:
            logger.error("No 'moves' field in score data")
            return error_response(400, 'moves field is required')
        
        if 'moveSequence' not in score_data:
            logger.error("No 'moveSequence' field in score data")
            return error_response(400, 'moveSequence field is required')
        
        moves = score_data['moves']
        move_sequence = score_data['moveSequence']
        
        logger.info(f"Moves: {moves}, Move sequence length: {len(move_sequence) if move_sequence else 'None'}")
        
        # Check if user already has a score for this round
        existing_response = scores_table.get_item(
            Key={'roundId': round_id, 'userId': user_id}
        )
        
        attempt_count = 1
        is_personal_best = True
        
        if 'Item' in existing_response:
            existing_score = existing_response['Item']
            attempt_count = existing_score.get('attemptCount', 0) + 1
            
            logger.info(f"Existing score: {existing_score['moves']}, New score: {moves}")
            
            # Only update if new score is better (fewer moves)
            if moves >= existing_score['moves']:
                logger.info("Score not improved, returning existing best")
                return success_response({
                    'message': 'Score not improved',
                    'currentBest': int(existing_score['moves']),
                    'submitted': moves,
                    'personalBest': False
                })
        
        # Create new score record
        score_item = {
            'roundId': round_id,
            'userId': user_id,
            'moves': moves,
            'moveSequence': move_sequence,
            'completedAt': datetime.datetime.utcnow().isoformat(),
            'attemptCount': attempt_count,
            'userEmail': user_email
        }
        
        logger.info(f"Saving score item: {score_item}")
        
        scores_table.put_item(Item=score_item)
        
        logger.info("Score submitted successfully")
        
        return success_response({
            'message': 'Score submitted successfully',
            'moves': moves,
            'personalBest': is_personal_best,
            'attemptCount': attempt_count
        }, 201)
        
    except Exception as e:
        logger.error(f"Failed to submit score: {e}", exc_info=True)
        return error_response(500, f'Failed to submit score: {str(e)}')

def success_response(data, status_code=200):
    """
    Return a successful response with CORS headers
    """
    # Clean data to prevent undefined values in JSON
    cleaned_data = clean_data_for_json(data)
    
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': 'https://robots.mlusby.dev',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(cleaned_data, default=decimal_default)
    }

def error_response(status_code, message):
    """
    Return an error response with CORS headers
    """
    logger.error(f"Error response: {status_code} - {message}")
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': 'https://robots.mlusby.dev',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({'error': message})
    }

def cors_response():
    """
    Return CORS preflight response
    """
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': 'https://robots.mlusby.dev',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': ''
    }

def decimal_default(obj):
    """
    JSON encoder for Decimal objects and other problematic types
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif obj is None:
        return None
    elif isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f'Object of type {type(obj)} is not JSON serializable')

def clean_data_for_json(data):
    """
    Clean data to ensure JSON serialization doesn't create 'undefined' values
    """
    if isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if value is None:
                cleaned[key] = None
            else:
                cleaned[key] = clean_data_for_json(value)
        return cleaned
    elif isinstance(data, Decimal):
        return float(data)
    else:
        return data