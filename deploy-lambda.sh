#!/bin/bash

# Deploy Lambda Functions for Robot Puzzle Game
# This script packages and deploys the separate Lambda function files

set -e

# Configuration
STACK_NAME="robot-puzzle-game-dev"
REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper function to log with timestamp
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') | $1"
}

# Function to get Lambda function name from CloudFormation stack
get_lambda_function_name() {
    local logical_id=$1
    
    aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --logical-resource-id "$logical_id" \
        --query 'StackResources[0].PhysicalResourceId' \
        --output text 2>/dev/null
}

# Function to package and deploy a Lambda function
deploy_lambda_function() {
    local function_file=$1
    local logical_id=$2
    local function_description=$3
    
    log "${BLUE}📦 Deploying $function_description...${NC}"
    
    # Get the actual function name from CloudFormation
    local function_name=$(get_lambda_function_name "$logical_id")
    
    if [[ -z "$function_name" || "$function_name" == "None" ]]; then
        log "${RED}❌ Could not find Lambda function $logical_id in stack${NC}"
        return 1
    fi
    
    log "${CYAN}   Function name: $function_name${NC}"
    
    # Create temporary directory for packaging
    local temp_dir=$(mktemp -d)
    local zip_file="${temp_dir}/function.zip"
    
    # Copy function file and create zip
    cp "$function_file" "${temp_dir}/index.py"
    
    # Package the function
    (cd "$temp_dir" && zip -q "$zip_file" index.py)
    
    if [[ ! -f "$zip_file" ]]; then
        log "${RED}❌ Failed to create deployment package${NC}"
        rm -rf "$temp_dir"
        return 1
    fi
    
    log "${CYAN}   Package created: $(du -h "$zip_file" | cut -f1)${NC}"
    
    # Deploy the function
    log "${CYAN}   Updating Lambda function code...${NC}"
    
    local update_result=$(aws lambda update-function-code \
        --function-name "$function_name" \
        --zip-file "fileb://$zip_file" \
        --region "$REGION" \
        --output json 2>&1)
    
    if [[ $? -eq 0 ]]; then
        log "${GREEN}✅ Successfully deployed $function_description${NC}"
        
        # Extract key info from the result
        local last_modified=$(echo "$update_result" | jq -r '.LastModified // "Unknown"')
        local code_size=$(echo "$update_result" | jq -r '.CodeSize // "Unknown"')
        
        log "${CYAN}   Last modified: $last_modified${NC}"
        log "${CYAN}   Code size: $code_size bytes${NC}"
    else
        log "${RED}❌ Failed to deploy $function_description${NC}"
        log "${RED}Error: $update_result${NC}"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Clean up
    rm -rf "$temp_dir"
    
    # Wait a moment for the function to be ready
    log "${CYAN}   Waiting for function to be ready...${NC}"
    sleep 5
    
    return 0
}

# Function to validate AWS setup
validate_aws_setup() {
    log "${BLUE}🔐 Validating AWS setup...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log "${RED}❌ AWS CLI is not installed${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log "${RED}❌ AWS credentials not configured${NC}"
        exit 1
    fi
    
    # Check if stack exists
    if ! aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        log "${RED}❌ CloudFormation stack '$STACK_NAME' not found${NC}"
        log "${YELLOW}💡 Run ./deploy.sh first to create the infrastructure${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ AWS setup validated${NC}"
}

# Function to test Lambda function
test_lambda_function() {
    local logical_id=$1
    local function_description=$2
    
    log "${BLUE}🧪 Testing $function_description...${NC}"
    
    local function_name=$(get_lambda_function_name "$logical_id")
    
    if [[ -z "$function_name" || "$function_name" == "None" ]]; then
        log "${YELLOW}⚠️  Could not test function - name not found${NC}"
        return 1
    fi
    
    # Create a test event (basic OPTIONS request for CORS)
    local test_event='{
        "httpMethod": "OPTIONS",
        "path": "/scores",
        "headers": {},
        "requestContext": {},
        "body": null
    }'
    
    # Invoke the function
    local test_result=$(aws lambda invoke \
        --function-name "$function_name" \
        --payload "$test_event" \
        --region "$REGION" \
        --output json \
        /tmp/lambda-test-output.json 2>&1)
    
    if [[ $? -eq 0 ]]; then
        local status_code=$(cat /tmp/lambda-test-output.json 2>/dev/null | jq -r '.statusCode // "Unknown"')
        
        if [[ "$status_code" == "200" ]]; then
            log "${GREEN}✅ $function_description test passed (status: $status_code)${NC}"
        else
            log "${YELLOW}⚠️  $function_description test completed with status: $status_code${NC}"
            log "${CYAN}   This may be expected for the test payload${NC}"
        fi
    else
        log "${YELLOW}⚠️  Could not test $function_description${NC}"
        log "${CYAN}   Error: $test_result${NC}"
    fi
    
    # Clean up test file
    rm -f /tmp/lambda-test-output.json
}

# Main deployment function
main() {
    log "${PURPLE}🚀 Lambda Function Deployment${NC}"
    log "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Validation
    validate_aws_setup
    
    # Check if Lambda function files exist
    if [[ ! -f "aws/lambda-functions/scores.py" ]]; then
        log "${RED}❌ Scores Lambda function file not found: aws/lambda-functions/scores.py${NC}"
        exit 1
    fi
    
    # Deploy scores function
    if deploy_lambda_function "aws/lambda-functions/scores.py" "ScoresFunction" "Scores Lambda Function"; then
        log "${GREEN}✅ Scores function deployment successful${NC}"
        
        # Test the function
        test_lambda_function "ScoresFunction" "Scores Lambda Function"
    else
        log "${RED}❌ Scores function deployment failed${NC}"
        exit 1
    fi
    
    # Optionally deploy board configurations function if it exists
    if [[ -f "aws/lambda-functions/board-configurations.py" ]]; then
        log "${BLUE}🔄 Also updating Board Configurations function...${NC}"
        
        if deploy_lambda_function "aws/lambda-functions/board-configurations.py" "BoardConfigurationsFunction" "Board Configurations Lambda Function"; then
            log "${GREEN}✅ Board configurations function deployment successful${NC}"
            test_lambda_function "BoardConfigurationsFunction" "Board Configurations Lambda Function"
        else
            log "${YELLOW}⚠️  Board configurations function deployment failed${NC}"
        fi
    fi
    
    log "${GREEN}🎉 Lambda function deployment completed!${NC}"
    log "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    log "${CYAN}📋 Next Steps:${NC}"
    log "${CYAN}   1. Test the score submission functionality in your game${NC}"
    log "${CYAN}   2. Check CloudWatch logs for detailed debugging information${NC}"
    log "${CYAN}   3. Monitor the application for any remaining issues${NC}"
    
    log "${YELLOW}🔍 Monitoring Commands:${NC}"
    log "${YELLOW}   View logs: aws logs tail /aws/lambda/robot-puzzle-game-dev-scores --follow --region $REGION${NC}"
    log "${YELLOW}   Check deployment: ./check-deployment.sh${NC}"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi