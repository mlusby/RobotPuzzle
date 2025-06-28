#!/bin/bash

# Robot Puzzle Game - Deployment Status Checker
# Enhanced monitoring and troubleshooting tool

set -e

# Configuration
STACK_NAME="robot-puzzle-game-prod"
REGION="us-east-1"
CHECK_INTERVAL=10  # Check every 10 seconds for interactive use

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper function to log with timestamp
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') | $1"
}

# Function to show stack overview
show_stack_overview() {
    echo -e "${BLUE}📊 Stack Overview${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local stack_info=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].[StackName,StackStatus,CreationTime,LastUpdatedTime]' \
        --output table 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo "$stack_info"
    else
        echo -e "${RED}❌ Stack not found or error retrieving information${NC}"
        return 1
    fi
}

# Function to show stack parameters
show_stack_parameters() {
    echo -e "\n${PURPLE}⚙️  Stack Parameters${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local parameters=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Parameters[*].[ParameterKey,ParameterValue]' \
        --output table 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$parameters" ]]; then
        echo "$parameters"
    else
        echo -e "${YELLOW}⚠️  No parameters found or unable to retrieve${NC}"
    fi
}

# Function to show stack outputs
show_stack_outputs() {
    echo -e "\n${GREEN}📤 Stack Outputs${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$outputs" ]]; then
        echo "$outputs"
        
        # Extract website URL for quick access
        local website_url=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
            --output text 2>/dev/null)
        
        if [[ -n "$website_url" && "$website_url" != "None" ]]; then
            echo -e "\n${CYAN}🌐 Quick Access: $website_url${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  No outputs found or unable to retrieve${NC}"
    fi
}

# Function to show recent stack events
show_recent_events() {
    local count=${1:-10}
    
    echo -e "\n${PURPLE}📋 Recent Stack Events (Last $count)${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local events=$(aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --max-items $count \
        --query 'StackEvents[*].[Timestamp,LogicalResourceId,ResourceType,ResourceStatus,ResourceStatusReason]' \
        --output table 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo "$events"
    else
        echo -e "${RED}❌ Unable to retrieve stack events${NC}"
    fi
}

# Function to show failed resources
show_failed_resources() {
    echo -e "\n${RED}💥 Failed Resources${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local failed_resources=$(aws cloudformation describe-stack-events \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackEvents[?contains(ResourceStatus, `FAILED`)].[LogicalResourceId,ResourceType,ResourceStatus,ResourceStatusReason]' \
        --output table 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$failed_resources" ]]; then
        echo "$failed_resources"
    else
        echo -e "${GREEN}✅ No failed resources found${NC}"
    fi
}

# Function to show stack resources
show_stack_resources() {
    echo -e "\n${CYAN}🏗️  Stack Resources${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local resources=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackResources[*].[LogicalResourceId,ResourceType,ResourceStatus,PhysicalResourceId]' \
        --output table 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo "$resources"
    else
        echo -e "${RED}❌ Unable to retrieve stack resources${NC}"
    fi
}

# Function to check resource health
check_resource_health() {
    echo -e "\n${BLUE}🏥 Resource Health Check${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Check S3 bucket
    local bucket_name=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId' \
        --output text 2>/dev/null)
    
    if [[ -n "$bucket_name" && "$bucket_name" != "None" ]]; then
        echo -n "   S3 Bucket ($bucket_name): "
        if aws s3 ls "s3://$bucket_name" &>/dev/null; then
            echo -e "${GREEN}✓ Accessible${NC}"
        else
            echo -e "${RED}✗ Inaccessible${NC}"
        fi
    fi
    
    # Check API Gateway
    local api_id=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackResources[?ResourceType==`AWS::ApiGateway::RestApi`].PhysicalResourceId' \
        --output text 2>/dev/null)
    
    if [[ -n "$api_id" && "$api_id" != "None" ]]; then
        echo -n "   API Gateway ($api_id): "
        if aws apigateway get-rest-api --rest-api-id "$api_id" --region "$REGION" &>/dev/null; then
            echo -e "${GREEN}✓ Available${NC}"
        else
            echo -e "${RED}✗ Unavailable${NC}"
        fi
    fi
    
    # Check Lambda function
    local lambda_name=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackResources[?ResourceType==`AWS::Lambda::Function`].PhysicalResourceId' \
        --output text 2>/dev/null)
    
    if [[ -n "$lambda_name" && "$lambda_name" != "None" ]]; then
        echo -n "   Lambda Function ($lambda_name): "
        if aws lambda get-function --function-name "$lambda_name" --region "$REGION" &>/dev/null; then
            echo -e "${GREEN}✓ Active${NC}"
        else
            echo -e "${RED}✗ Inactive${NC}"
        fi
    fi
    
    # Check DynamoDB table
    local table_name=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackResources[?ResourceType==`AWS::DynamoDB::Table`].PhysicalResourceId' \
        --output text 2>/dev/null)
    
    if [[ -n "$table_name" && "$table_name" != "None" ]]; then
        echo -n "   DynamoDB Table ($table_name): "
        if aws dynamodb describe-table --table-name "$table_name" --region "$REGION" &>/dev/null; then
            echo -e "${GREEN}✓ Available${NC}"
        else
            echo -e "${RED}✗ Unavailable${NC}"
        fi
    fi
    
    # Check Cognito User Pool
    local user_pool_id=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
        --output text 2>/dev/null)
    
    if [[ -n "$user_pool_id" && "$user_pool_id" != "None" ]]; then
        echo -n "   Cognito User Pool ($user_pool_id): "
        if aws cognito-idp describe-user-pool --user-pool-id "$user_pool_id" --region "$REGION" &>/dev/null; then
            echo -e "${GREEN}✓ Active${NC}"
        else
            echo -e "${RED}✗ Inactive${NC}"
        fi
    fi
}

# Function to test website functionality
test_website() {
    echo -e "\n${PURPLE}🧪 Website Functionality Test${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    local website_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
        --output text 2>/dev/null)
    
    if [[ -n "$website_url" && "$website_url" != "None" ]]; then
        echo -n "   Website accessibility: "
        if curl -s --head "$website_url" | head -n 1 | grep -q "200"; then
            echo -e "${GREEN}✓ Accessible${NC}"
            
            echo -n "   Content delivery: "
            if curl -s "$website_url" | grep -q "Robot Puzzle"; then
                echo -e "${GREEN}✓ Content loading${NC}"
            else
                echo -e "${YELLOW}⚠ Content may be incomplete${NC}"
            fi
        else
            echo -e "${RED}✗ Inaccessible${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Website URL not found${NC}"
    fi
    
    # Test API Gateway
    local api_url=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
        --output text 2>/dev/null)
    
    if [[ -n "$api_url" && "$api_url" != "None" ]]; then
        echo -n "   API Gateway CORS: "
        local cors_response=$(curl -s -X OPTIONS "${api_url}/configurations" -H "Origin: $website_url" -w "%{http_code}")
        if [[ "$cors_response" =~ 200$ ]]; then
            echo -e "${GREEN}✓ CORS configured${NC}"
        else
            echo -e "${YELLOW}⚠ CORS may need configuration${NC}"
        fi
    fi
}

# Function to show troubleshooting information
show_troubleshooting() {
    echo -e "\n${YELLOW}🔧 Troubleshooting Information${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    echo -e "\n${CYAN}📍 Common Issues and Solutions:${NC}"
    echo -e "   ${YELLOW}1. Stack Creation Failed:${NC}"
    echo -e "      • Check IAM permissions for CloudFormation"
    echo -e "      • Verify resource limits and quotas"
    echo -e "      • Review template syntax errors"
    
    echo -e "\n   ${YELLOW}2. Website Not Loading:${NC}"
    echo -e "      • S3 bucket policy may need adjustment"
    echo -e "      • Check S3 static website hosting configuration"
    echo -e "      • Verify DNS propagation (can take time)"
    
    echo -e "\n   ${YELLOW}3. API Errors:${NC}"
    echo -e "      • Verify Cognito User Pool configuration"
    echo -e "      • Check Lambda function logs in CloudWatch"
    echo -e "      • Ensure DynamoDB table permissions"
    
    echo -e "\n   ${YELLOW}4. Authentication Issues:${NC}"
    echo -e "      • Check Cognito User Pool and App Client settings"
    echo -e "      • Verify CORS configuration in API Gateway"
    echo -e "      • Ensure frontend AWS configuration is correct"
    
    echo -e "\n${CYAN}🔗 Useful Commands:${NC}"
    echo -e "   View CloudFormation events:"
    echo -e "   ${GREEN}aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $REGION${NC}"
    
    echo -e "\n   Delete failed stack:"
    echo -e "   ${GREEN}aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION${NC}"
    
    echo -e "\n   Check Lambda logs:"
    echo -e "   ${GREEN}aws logs describe-log-groups --log-group-name-prefix /aws/lambda/robot-puzzle-game --region $REGION${NC}"
    
    echo -e "\n   Re-deploy after fixes:"
    echo -e "   ${GREEN}./deploy.sh${NC}"
    
    echo -e "\n${CYAN}🌐 AWS Console Links:${NC}"
    echo -e "   • CloudFormation: https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks"
    echo -e "   • S3: https://console.aws.amazon.com/s3/"
    echo -e "   • API Gateway: https://console.aws.amazon.com/apigateway/"
    echo -e "   • Lambda: https://console.aws.amazon.com/lambda/"
    echo -e "   • Cognito: https://console.aws.amazon.com/cognito/"
    echo -e "   • DynamoDB: https://console.aws.amazon.com/dynamodb/"
}

# Function to monitor stack in real-time
monitor_stack() {
    echo -e "${BLUE}👁️  Real-time Stack Monitoring${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop monitoring${NC}\n"
    
    local last_event_time=""
    
    while true; do
        # Get current status
        local status=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].StackStatus' \
            --output text 2>/dev/null || echo "STACK_NOT_FOUND")
        
        # Get latest event
        local latest_event=$(aws cloudformation describe-stack-events \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --max-items 1 \
            --query 'StackEvents[0].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
            --output text 2>/dev/null)
        
        # Display status
        echo -e "\r$(date '+%H:%M:%S') | Status: ${YELLOW}$status${NC}                    "
        
        # Show new events
        if [[ -n "$latest_event" && "$latest_event" != "$last_event_time" ]]; then
            echo -e "${CYAN}New Event:${NC} $latest_event"
            last_event_time="$latest_event"
        fi
        
        # Check if monitoring should stop
        case $status in
            "*_COMPLETE"|"*_FAILED"|"ROLLBACK_COMPLETE"|"STACK_NOT_FOUND")
                echo -e "\n${GREEN}✅ Stack reached final state: $status${NC}"
                break
                ;;
        esac
        
        sleep $CHECK_INTERVAL
    done
}

# Function to show usage information
show_usage() {
    echo -e "${BLUE}📖 Robot Puzzle Game - Deployment Checker${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\nUsage: $0 [option]"
    echo -e "\nOptions:"
    echo -e "  ${GREEN}status${NC}        Show complete deployment status"
    echo -e "  ${GREEN}monitor${NC}       Monitor stack changes in real-time"
    echo -e "  ${GREEN}events${NC}        Show recent stack events"
    echo -e "  ${GREEN}outputs${NC}       Show stack outputs"
    echo -e "  ${GREEN}resources${NC}     Show stack resources"
    echo -e "  ${GREEN}health${NC}        Check resource health"
    echo -e "  ${GREEN}test${NC}          Test website functionality"
    echo -e "  ${GREEN}troubleshoot${NC}  Show troubleshooting information"
    echo -e "  ${GREEN}help${NC}          Show this help message"
    echo -e "\nDefault (no option): Show complete status overview"
}

# Main function
main() {
    local action=${1:-status}
    
    case $action in
        "status")
            show_stack_overview
            show_stack_outputs
            show_recent_events 5
            show_failed_resources
            ;;
        "monitor")
            monitor_stack
            ;;
        "events")
            show_recent_events 20
            ;;
        "outputs")
            show_stack_outputs
            ;;
        "resources")
            show_stack_resources
            ;;
        "health")
            check_resource_health
            ;;
        "test")
            test_website
            ;;
        "troubleshoot")
            show_troubleshooting
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $action${NC}"
            show_usage
            exit 1
            ;;
    esac
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi