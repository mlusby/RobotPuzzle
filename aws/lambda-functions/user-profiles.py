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
profiles_table = dynamodb.Table(os.environ['PROFILES_TABLE'])

def lambda_handler(event, context):
    """
    Main Lambda handler for user profile operations
    Handles GET and PUT operations for user profiles
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
            # Check if this is a username lookup request: /user/username/{userId}
            if '/user/username/' in path:
                # Extract target userId from path
                path_parts = path.split('/')
                target_user_id = path_parts[-1]  # Last part is the userId
                logger.info(f"Username lookup request for userId: {target_user_id}")
                return get_username_by_user_id(target_user_id)
            else:
                # Regular profile request: /user/profile
                return get_user_profile(user_id, user_email)
        elif http_method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            return update_user_profile(user_id, user_email, body)
        else:
            logger.error(f"Unsupported HTTP method: {http_method}")
            return error_response(405, f'Method {http_method} not allowed')
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return error_response(500, f'Internal server error: {str(e)}')

def get_user_profile(user_id, user_email):
    """
    Retrieve user profile from DynamoDB
    """
    logger.info(f"Getting profile for user: {user_id}")
    
    try:
        response = profiles_table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            profile = response['Item']
            # Convert Decimal to regular types for JSON serialization
            profile = json.loads(json.dumps(profile, default=decimal_default))
            logger.info(f"Found existing profile for user {user_id}")
        else:
            # Return minimal profile if none exists
            profile = {
                'userId': user_id,
                'email': user_email,
                'username': None,
                'createdAt': datetime.datetime.utcnow().isoformat()
            }
            logger.info(f"No existing profile found for user {user_id}, returning default")
        
        return success_response(profile)
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return error_response(500, f'Failed to retrieve user profile: {str(e)}')

def update_user_profile(user_id, user_email, profile_data):
    """
    Update user profile in DynamoDB
    """
    logger.info(f"Updating profile for user: {user_id} with data: {profile_data}")
    
    try:
        # Validate input data
        if not isinstance(profile_data, dict):
            return error_response(400, 'Profile data must be an object')
        
        # Extract and validate username if provided
        username = profile_data.get('username')
        if username is not None:
            if not isinstance(username, str):
                return error_response(400, 'Username must be a string')
            
            username = username.strip()
            if len(username) < 3:
                return error_response(400, 'Username must be at least 3 characters long')
            
            if len(username) > 20:
                return error_response(400, 'Username must be no more than 20 characters long')
            
            # Basic validation for allowed characters
            if not username.replace('_', '').replace('-', '').isalnum():
                return error_response(400, 'Username can only contain letters, numbers, hyphens, and underscores')
        
        # Get existing profile or create new one
        existing_response = profiles_table.get_item(Key={'userId': user_id})
        
        if 'Item' in existing_response:
            # Update existing profile
            profile = existing_response['Item']
            profile['updatedAt'] = datetime.datetime.utcnow().isoformat()
        else:
            # Create new profile
            profile = {
                'userId': user_id,
                'email': user_email,
                'createdAt': datetime.datetime.utcnow().isoformat(),
                'updatedAt': datetime.datetime.utcnow().isoformat()
            }
        
        # Update fields from request
        if username is not None:
            profile['username'] = username
            
        # Add any other profile fields that might be provided
        for key, value in profile_data.items():
            if key not in ['userId', 'email', 'createdAt', 'updatedAt'] and value is not None:
                profile[key] = value
        
        # Save to DynamoDB
        profiles_table.put_item(Item=profile)
        
        # Convert Decimal to regular types for JSON response
        response_profile = json.loads(json.dumps(profile, default=decimal_default))
        
        logger.info(f"Successfully updated profile for user {user_id}")
        return success_response(response_profile)
        
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        return error_response(500, f'Failed to update user profile: {str(e)}')

def get_username_by_user_id(target_user_id):
    """
    Get username for a specific userId (public endpoint for leaderboards)
    Returns only the username and email (public info), not full profile
    """
    logger.info(f"Getting username for userId: {target_user_id}")
    
    try:
        response = profiles_table.get_item(Key={'userId': target_user_id})
        
        if 'Item' in response:
            profile = response['Item']
            # Return only public information
            public_info = {
                'userId': target_user_id,
                'username': profile.get('username'),
                'email': profile.get('email')  # Include email as fallback
            }
            logger.info(f"Found profile for user {target_user_id}, username: {profile.get('username')}")
        else:
            # User has no profile, return minimal info
            public_info = {
                'userId': target_user_id,
                'username': None,
                'email': None
            }
            logger.info(f"No profile found for user {target_user_id}")
        
        return success_response(public_info)
        
    except Exception as e:
        logger.error(f"Error getting username for user {target_user_id}: {str(e)}")
        return error_response(500, f'Failed to retrieve username: {str(e)}')

def success_response(data):
    """Return a successful API response"""
    return {
        'statusCode': 200,
        'headers': cors_headers(),
        'body': json.dumps(data, default=decimal_default)
    }

def error_response(status_code, message):
    """Return an error API response"""
    return {
        'statusCode': status_code,
        'headers': cors_headers(),
        'body': json.dumps({'error': message})
    }

def cors_response():
    """Return a CORS preflight response"""
    return {
        'statusCode': 200,
        'headers': cors_headers(),
        'body': ''
    }

def cors_headers():
    """Return standard CORS headers"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,OPTIONS'
    }

def decimal_default(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, Decimal):
        # Convert decimal to int if it's a whole number, otherwise float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    raise TypeError