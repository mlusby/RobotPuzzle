import json
import boto3
import os
from decimal import Decimal
import uuid
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    """
    Main Lambda handler for board configuration CRUD operations
    """
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # Extract user ID from Cognito JWT token
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return cors_response()
        
        # Route to appropriate handler
        if path == '/configurations':
            if http_method == 'GET':
                return get_configurations(user_id)
            elif http_method == 'POST':
                return create_configuration(user_id, json.loads(event['body']))
        elif path.startswith('/configurations/'):
            config_id = event['pathParameters']['configId']
            if http_method == 'GET':
                return get_configuration(user_id, config_id)
            elif http_method == 'PUT':
                return update_configuration(user_id, config_id, json.loads(event['body']))
            elif http_method == 'DELETE':
                return delete_configuration(user_id, config_id)
        
        return error_response(405, 'Method not allowed')
        
    except KeyError as e:
        return error_response(400, f'Missing required parameter: {str(e)}')
    except json.JSONDecodeError:
        return error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        print(f"Error: {str(e)}")
        return error_response(500, 'Internal server error')

def get_configurations(user_id):
    """
    Get all board configurations for a user
    """
    try:
        response = table.query(
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        configurations = {}
        for item in response['Items']:
            configurations[item['configId']] = {
                'walls': item.get('walls', []),
                'targets': item.get('targets', []),
                'createdAt': item.get('createdAt'),
                'updatedAt': item.get('updatedAt')
            }
        
        return success_response(configurations)
    except Exception as e:
        return error_response(500, f'Failed to get configurations: {str(e)}')

def get_configuration(user_id, config_id):
    """
    Get a specific board configuration
    """
    try:
        response = table.get_item(
            Key={'userId': user_id, 'configId': config_id}
        )
        
        if 'Item' not in response:
            return error_response(404, 'Configuration not found')
        
        item = response['Item']
        configuration = {
            'walls': item.get('walls', []),
            'targets': item.get('targets', []),
            'createdAt': item.get('createdAt'),
            'updatedAt': item.get('updatedAt')
        }
        
        return success_response(configuration)
    except Exception as e:
        return error_response(500, f'Failed to get configuration: {str(e)}')

def create_configuration(user_id, data):
    """
    Create a new board configuration
    """
    try:
        # Validate input data
        if 'walls' not in data or 'targets' not in data:
            return error_response(400, 'Missing walls or targets data')
        
        # Find next available config ID
        response = table.query(
            KeyConditionExpression='userId = :userId',
            ExpressionAttributeValues={':userId': user_id}
        )
        
        existing_ids = []
        for item in response['Items']:
            try:
                existing_ids.append(int(item['configId']))
            except ValueError:
                continue  # Skip non-numeric config IDs
        
        config_id = str(max(existing_ids) + 1 if existing_ids else 1)
        
        # Create the item
        now = datetime.utcnow().isoformat()
        item = {
            'userId': user_id,
            'configId': config_id,
            'walls': data['walls'],
            'targets': data['targets'],
            'createdAt': now,
            'updatedAt': now
        }
        
        table.put_item(Item=item)
        
        return success_response({'configId': config_id}, 201)
    except Exception as e:
        return error_response(500, f'Failed to create configuration: {str(e)}')

def update_configuration(user_id, config_id, data):
    """
    Update an existing board configuration
    """
    try:
        # Check if configuration exists and belongs to user
        response = table.get_item(
            Key={'userId': user_id, 'configId': config_id}
        )
        
        if 'Item' not in response:
            return error_response(404, 'Configuration not found')
        
        # Validate input data
        if 'walls' not in data or 'targets' not in data:
            return error_response(400, 'Missing walls or targets data')
        
        # Update the item
        now = datetime.utcnow().isoformat()
        table.put_item(Item={
            'userId': user_id,
            'configId': config_id,
            'walls': data['walls'],
            'targets': data['targets'],
            'createdAt': response['Item'].get('createdAt', now),
            'updatedAt': now
        })
        
        return success_response({'message': 'Configuration updated successfully'})
    except Exception as e:
        return error_response(500, f'Failed to update configuration: {str(e)}')

def delete_configuration(user_id, config_id):
    """
    Delete a board configuration
    """
    try:
        # Check if configuration exists and belongs to user
        response = table.get_item(
            Key={'userId': user_id, 'configId': config_id}
        )
        
        if 'Item' not in response:
            return error_response(404, 'Configuration not found')
        
        # Delete the item
        table.delete_item(
            Key={'userId': user_id, 'configId': config_id}
        )
        
        return success_response({'message': 'Configuration deleted successfully'})
    except Exception as e:
        return error_response(500, f'Failed to delete configuration: {str(e)}')

def success_response(data, status_code=200):
    """
    Return a successful response with CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(data, default=decimal_default)
    }

def error_response(status_code, message):
    """
    Return an error response with CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
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
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': ''
    }

def decimal_default(obj):
    """
    JSON encoder for Decimal objects
    """
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f'Object of type {type(obj)} is not JSON serializable')