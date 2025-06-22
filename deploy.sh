#!/bin/bash

# Robot Puzzle Game - Advanced AWS Deployment Script
# Based on sophisticated deployment patterns from temperature-monitor

set -e

# Configuration
STACK_NAME="robot-puzzle-game-dev"
TEMPLATE_FILE="aws/cloudformation-template.yaml"
REGION="us-east-1"  # Change to your preferred region
DEPLOYMENT_TIMEOUT=1800  # 30 minutes
CHECK_INTERVAL=30  # Check every 30 seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Progress indicators
PROGRESS_CHARS="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Global variables
START_TIME=""
TEMP_FILES=()

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up temporary files...${NC}"
    for file in "${TEMP_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            rm -f "$file"
            echo "   Removed: $file"
        fi
    done
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Helper function to log with timestamp
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') | $1"
}

# Helper function to show elapsed time
elapsed_time() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    printf "%02d:%02d" $minutes $seconds
}

# Function to monitor stack progress with real-time updates
monitor_stack_progress() {
    local stack_name=$1
    local operation=$2  # CREATE or UPDATE
    local progress_index=0
    
    echo -e "${BLUE}📊 Monitoring ${operation} progress for stack: ${stack_name}${NC}"
    echo -e "${YELLOW}⏱️  Started at: $(date)${NC}"
    
    while true; do
        # Get current status
        local status=$(aws cloudformation describe-stacks \
            --stack-name "$stack_name" \
            --region "$REGION" \
            --query 'Stacks[0].StackStatus' \
            --output text 2>/dev/null || echo "STACK_NOT_FOUND")
        
        # Progress indicator
        local char=${PROGRESS_CHARS:$progress_index:1}
        progress_index=$(( (progress_index + 1) % ${#PROGRESS_CHARS} ))
        
        # Display status with elapsed time
        printf "\r${char} Status: ${YELLOW}%-20s${NC} | Elapsed: ${CYAN}%s${NC}" "$status" "$(elapsed_time)"
        
        # Check if deployment is complete
        case $status in
            "${operation}_COMPLETE")
                echo -e "\n${GREEN}✅ ${operation} completed successfully!${NC}"
                return 0
                ;;
            "${operation}_FAILED"|"ROLLBACK_COMPLETE"|"ROLLBACK_FAILED")
                echo -e "\n${RED}❌ ${operation} failed with status: $status${NC}"
                show_failure_details "$stack_name"
                return 1
                ;;
            "STACK_NOT_FOUND")
                echo -e "\n${RED}❌ Stack not found${NC}"
                return 1
                ;;
            *"_IN_PROGRESS"|"REVIEW_IN_PROGRESS")
                # Continue monitoring
                ;;
            *)
                echo -e "\n${YELLOW}⚠️  Unexpected status: $status${NC}"
                ;;
        esac
        
        # Show recent events every few iterations
        if [ $((progress_index % 4)) -eq 0 ]; then
            show_recent_events "$stack_name" 3
        fi
        
        sleep $CHECK_INTERVAL
    done
}

# Function to show recent stack events
show_recent_events() {
    local stack_name=$1
    local count=${2:-5}
    
    echo -e "\n${PURPLE}📋 Recent events:${NC}"
    aws cloudformation describe-stack-events \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --max-items $count \
        --query 'StackEvents[*].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
        --output table 2>/dev/null || echo "   Unable to fetch events"
}

# Function to show detailed failure information
show_failure_details() {
    local stack_name=$1
    
    echo -e "\n${RED}💥 Deployment Failure Details:${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Show failed resources
    echo -e "\n${PURPLE}🔍 Failed Resources:${NC}"
    aws cloudformation describe-stack-events \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'StackEvents[?contains(ResourceStatus, `FAILED`)].[LogicalResourceId,ResourceStatus,ResourceStatusReason]' \
        --output table 2>/dev/null || echo "   Unable to fetch failure details"
    
    # Show recent events for context
    echo -e "\n${PURPLE}📊 Recent Events (Last 10):${NC}"
    show_recent_events "$stack_name" 10
    
    echo -e "\n${YELLOW}💡 Troubleshooting Tips:${NC}"
    echo -e "   1. Check the AWS Console for detailed error messages"
    echo -e "   2. Verify IAM permissions for CloudFormation and related services"
    echo -e "   3. Check resource limits and quotas in your AWS account"
    echo -e "   4. Review template syntax and resource dependencies"
    echo -e "\n${YELLOW}🔧 To retry deployment:${NC}"
    echo -e "   ./deploy.sh"
    echo -e "\n${YELLOW}🗑️  To clean up failed resources:${NC}"
    echo -e "   aws cloudformation delete-stack --stack-name $stack_name --region $REGION"
}

# Function to handle existing stack states
handle_existing_stack() {
    local stack_name=$1
    
    local status=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].StackStatus' \
        --output text 2>/dev/null || echo "STACK_NOT_FOUND")
    
    case $status in
        "STACK_NOT_FOUND")
            log "${GREEN}✅ No existing stack found, proceeding with deployment${NC}"
            return 0
            ;;
        "CREATE_COMPLETE"|"UPDATE_COMPLETE")
            log "${YELLOW}⚠️  Stack already exists with status: $status${NC}"
            echo -e "${BLUE}📝 This will update the existing stack${NC}"
            read -p "Continue with stack update? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo -e "${YELLOW}❌ Deployment cancelled by user${NC}"
                exit 0
            fi
            return 0
            ;;
        "ROLLBACK_COMPLETE"|"CREATE_FAILED"|"UPDATE_FAILED")
            log "${RED}❌ Stack in failed state: $status${NC}"
            echo -e "${YELLOW}🔧 Automatically cleaning up failed stack...${NC}"
            aws cloudformation delete-stack --stack-name "$stack_name" --region "$REGION"
            
            echo -e "${BLUE}⏳ Waiting for stack deletion...${NC}"
            aws cloudformation wait stack-delete-complete --stack-name "$stack_name" --region "$REGION"
            log "${GREEN}✅ Failed stack cleaned up successfully${NC}"
            return 0
            ;;
        *"_IN_PROGRESS")
            log "${YELLOW}⚠️  Stack operation in progress: $status${NC}"
            echo -e "${BLUE}⏳ Waiting for current operation to complete...${NC}"
            monitor_stack_progress "$stack_name" "${status%_IN_PROGRESS}"
            return $?
            ;;
        *)
            log "${RED}❌ Unexpected stack status: $status${NC}"
            echo -e "${YELLOW}💡 Please check the AWS Console for more details${NC}"
            exit 1
            ;;
    esac
}

# Function to validate AWS credentials and permissions
validate_aws_setup() {
    log "${BLUE}🔐 Validating AWS setup...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log "${RED}❌ AWS CLI is not installed${NC}"
        echo -e "${YELLOW}💡 Install AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log "${RED}❌ AWS credentials not configured${NC}"
        echo -e "${YELLOW}💡 Configure AWS CLI: aws configure${NC}"
        exit 1
    fi
    
    # Get account info
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local user_arn=$(aws sts get-caller-identity --query Arn --output text)
    
    log "${GREEN}✅ AWS CLI configured${NC}"
    log "${CYAN}   Account ID: $account_id${NC}"
    log "${CYAN}   User/Role: $user_arn${NC}"
    log "${CYAN}   Region: $REGION${NC}"
    
    # Validate CloudFormation permissions
    if ! aws cloudformation list-stacks --region "$REGION" &> /dev/null; then
        log "${RED}❌ Insufficient CloudFormation permissions${NC}"
        echo -e "${YELLOW}💡 Ensure your user/role has CloudFormation permissions${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ AWS permissions validated${NC}"
}

# Function to validate template
validate_template() {
    log "${BLUE}📋 Validating CloudFormation template...${NC}"
    
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log "${RED}❌ Template file not found: $TEMPLATE_FILE${NC}"
        exit 1
    fi
    
    # Validate template syntax
    local validation_result=$(aws cloudformation validate-template \
        --template-body file://"$TEMPLATE_FILE" \
        --region "$REGION" 2>&1)
    
    if [[ $? -ne 0 ]]; then
        log "${RED}❌ Template validation failed${NC}"
        echo -e "${YELLOW}Error details:${NC}"
        echo "$validation_result"
        exit 1
    fi
    
    log "${GREEN}✅ Template validation successful${NC}"
    
    # Show template summary
    local description=$(aws cloudformation validate-template \
        --template-body file://"$TEMPLATE_FILE" \
        --region "$REGION" \
        --query 'Description' \
        --output text 2>/dev/null || echo "No description")
    
    log "${CYAN}   Description: $description${NC}"
}

# Function to execute pending changesets
execute_pending_changeset() {
    local stack_name=$1
    
    log "${BLUE}🔄 Checking for pending changesets...${NC}"
    
    # List all changesets for the stack
    local changesets_output=$(aws cloudformation list-change-sets \
        --stack-name "$stack_name" \
        --region "$REGION" 2>/dev/null)
    
    if [[ $? -ne 0 ]]; then
        log "${YELLOW}⚠️  Unable to list changesets${NC}"
        return 1
    fi
    
    # Check for changesets that failed due to no changes
    local failed_no_changes=$(echo "$changesets_output" | jq -r '.Summaries[] | select(.Status == "FAILED" and (.StatusReason | contains("no changes") or contains("didn'\''t contain changes"))) | .ChangeSetName' 2>/dev/null | head -n1)
    
    if [[ -n "$failed_no_changes" ]]; then
        log "${YELLOW}ℹ️  No infrastructure changes needed (changeset: $failed_no_changes)${NC}"
        return 2  # Special return code for "no changes"
    fi
    
    # Check for pending changesets ready to execute
    local ready_changesets=$(echo "$changesets_output" | jq -r '.Summaries[] | select(.Status == "CREATE_COMPLETE") | .ChangeSetName' 2>/dev/null | head -n1)
    
    if [[ -n "$ready_changesets" ]]; then
        log "${YELLOW}📋 Found pending changeset: $ready_changesets${NC}"
        log "${BLUE}⚡ Executing changeset...${NC}"
        
        if aws cloudformation execute-change-set \
            --change-set-name "$ready_changesets" \
            --stack-name "$stack_name" \
            --region "$REGION" &>/dev/null; then
            log "${GREEN}✅ Changeset execution initiated${NC}"
            return 0
        else
            log "${RED}❌ Failed to execute changeset${NC}"
            return 1
        fi
    else
        log "${YELLOW}⚠️  No pending changesets found${NC}"
        return 1
    fi
}

# Function to deploy CloudFormation stack
deploy_stack() {
    log "${BLUE}🚀 Deploying CloudFormation stack...${NC}"
    
    # Check for existing stack
    handle_existing_stack "$STACK_NAME"
    
    # Deploy stack
    local deploy_output=$(mktemp)
    TEMP_FILES+=("$deploy_output")
    
    aws cloudformation deploy \
        --template-file "$TEMPLATE_FILE" \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --parameter-overrides \
            AppName=robot-puzzle-game \
            Environment=dev \
        --no-fail-on-empty-changeset 2>&1 | tee "$deploy_output"
    
    local deploy_exit_code=${PIPESTATUS[0]}
    
    # Check for "No changes" scenario
    if grep -q "No changes to deploy" "$deploy_output"; then
        log "${YELLOW}ℹ️  No infrastructure changes needed${NC}"
        return 0
    fi
    
    # Check if deployment failed due to changeset creation
    if [[ $deploy_exit_code -ne 0 ]] || grep -q "Waiting for changeset to be created" "$deploy_output"; then
        log "${YELLOW}🔄 Deployment created changeset, attempting automatic execution...${NC}"
        
        # Wait a moment for changeset to be ready
        sleep 10
        
        # Try to execute the changeset
        execute_pending_changeset "$STACK_NAME"
        local changeset_result=$?
        
        if [[ $changeset_result -eq 0 ]]; then
            # Monitor the deployment progress after executing changeset
            monitor_stack_progress "$STACK_NAME" "UPDATE"
            return $?
        elif [[ $changeset_result -eq 2 ]]; then
            # No changes needed - this is success, not failure
            log "${GREEN}✅ Infrastructure is already up to date${NC}"
            return 0
        else
            log "${RED}❌ Failed to execute changeset automatically${NC}"
            log "${YELLOW}💡 Please execute the changeset manually in the AWS Console${NC}"
            return 1
        fi
    fi
    
    if [[ $deploy_exit_code -ne 0 ]]; then
        log "${RED}❌ CloudFormation deploy command failed${NC}"
        return 1
    fi
    
    # Determine operation type based on stack existence
    local operation="CREATE"
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &>/dev/null; then
        operation="UPDATE"
    fi
    
    # Monitor the deployment progress
    monitor_stack_progress "$STACK_NAME" "$operation"
    return $?
}

# Function to get and display stack outputs
get_stack_outputs() {
    log "${BLUE}📋 Retrieving stack outputs...${NC}"
    
    local outputs=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table 2>/dev/null)
    
    if [[ $? -eq 0 && -n "$outputs" ]]; then
        echo -e "\n${GREEN}📊 Stack Outputs:${NC}"
        echo "$outputs"
        
        # Extract key values for further processing
        WEBSITE_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
            --output text 2>/dev/null)
        
        API_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
            --output text 2>/dev/null)
        
        USER_POOL_ID=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
            --output text 2>/dev/null)
        
        USER_POOL_CLIENT_ID=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'Stacks[0].Outputs[?OutputKey==`UserPoolClientId`].OutputValue' \
            --output text 2>/dev/null)
        
        BUCKET_NAME=$(aws cloudformation describe-stack-resources \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId' \
            --output text 2>/dev/null)
    else
        log "${YELLOW}⚠️  Unable to retrieve stack outputs${NC}"
        return 1
    fi
}

# Function to update AWS configuration
update_aws_config() {
    log "${BLUE}⚙️  Updating AWS configuration...${NC}"
    
    if [[ -z "$API_URL" || -z "$USER_POOL_ID" || -z "$USER_POOL_CLIENT_ID" ]]; then
        log "${RED}❌ Missing required configuration values${NC}"
        return 1
    fi
    
    # Create backup of existing config
    if [[ -f "js/aws-config.js" ]]; then
        cp "js/aws-config.js" "js/aws-config.js.backup.$(date +%s)"
        TEMP_FILES+=("js/aws-config.js.backup.*")
    fi
    
    # Ensure js directory exists
    mkdir -p js
    
    cat > js/aws-config.js << EOF
// AWS Configuration - Auto-generated by deploy script
// Generated: $(date)
// Stack: $STACK_NAME
// Region: $REGION

const AWS_CONFIG = {
    region: '${REGION}',
    cognito: {
        userPoolId: '${USER_POOL_ID}',
        userPoolWebClientId: '${USER_POOL_CLIENT_ID}'
    },
    api: {
        baseUrl: '${API_URL}'
    }
};

// Export for Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AWS_CONFIG;
}
EOF
    
    log "${GREEN}✅ AWS configuration updated${NC}"
    log "${CYAN}   Config file: js/aws-config.js${NC}"
}

# Function to upload website files with progress
upload_website_files() {
    log "${BLUE}📤 Uploading website files to S3...${NC}"
    
    if [[ -z "$BUCKET_NAME" ]]; then
        log "${RED}❌ S3 bucket name not found${NC}"
        return 1
    fi
    
    local files_to_upload=(
        "index.html"
        "wall-editor.html"
        "login.html"
        "styles.css"
        "script.js"
        "favicon.svg"
        "error.html"
    )
    
    # Upload individual files
    local total_files=${#files_to_upload[@]}
    local uploaded=0
    
    for file in "${files_to_upload[@]}"; do
        if [[ -f "$file" ]]; then
            echo -n "   Uploading $file... "
            if aws s3 cp "$file" "s3://${BUCKET_NAME}/" --region "$REGION" &>/dev/null; then
                echo -e "${GREEN}✓${NC}"
                ((uploaded++))
            else
                echo -e "${RED}✗${NC}"
            fi
        else
            echo -e "   ${YELLOW}⚠️  File not found: $file${NC}"
        fi
    done
    
    # Upload JS directory
    if [[ -d "js" ]]; then
        echo -n "   Uploading js/ directory... "
        if aws s3 cp js/ "s3://${BUCKET_NAME}/js/" --recursive --region "$REGION" &>/dev/null; then
            echo -e "${GREEN}✓${NC}"
            ((uploaded++))
        else
            echo -e "${RED}✗${NC}"
        fi
    fi
    
    log "${GREEN}✅ Website files uploaded (${uploaded}/${total_files} successful)${NC}"
    
    # Set bucket website configuration
    if aws s3 website "s3://${BUCKET_NAME}" --index-document index.html --error-document error.html --region "$REGION" &>/dev/null; then
        log "${GREEN}✅ S3 website configuration set${NC}"
    else
        log "${YELLOW}⚠️  Unable to set S3 website configuration${NC}"
    fi
}

# Function to test deployment
test_deployment() {
    log "${BLUE}🧪 Testing deployment...${NC}"
    
    if [[ -n "$WEBSITE_URL" ]]; then
        echo -e "\n${PURPLE}🌐 Testing website accessibility...${NC}"
        if curl -s --head "$WEBSITE_URL" | head -n 1 | grep -q "200 OK"; then
            log "${GREEN}✅ Website is accessible${NC}"
        else
            log "${YELLOW}⚠️  Website may not be ready yet (this is normal for new deployments)${NC}"
        fi
    fi
    
    if [[ -n "$API_URL" ]]; then
        echo -e "\n${PURPLE}🔌 Testing API Gateway...${NC}"
        # Test OPTIONS request (should work without auth)
        if curl -s -X OPTIONS "${API_URL}/configurations" &>/dev/null; then
            log "${GREEN}✅ API Gateway is responding${NC}"
        else
            log "${YELLOW}⚠️  API Gateway may not be ready yet${NC}"
        fi
    fi
}

# Function to display deployment summary
show_deployment_summary() {
    local end_time=$(date +%s)
    local total_time=$((end_time - START_TIME))
    local minutes=$((total_time / 60))
    local seconds=$((total_time % 60))
    
    echo -e "\n${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    echo -e "\n${CYAN}📊 Deployment Summary:${NC}"
    echo -e "   Total time: ${minutes}m ${seconds}s"
    echo -e "   Stack name: $STACK_NAME"
    echo -e "   Region: $REGION"
    echo -e "   Timestamp: $(date)"
    
    # Always show the production URL prominently
    if [[ -n "$WEBSITE_URL" ]]; then
        echo -e "\n${GREEN}🌐 Production URL:${NC}"
        echo -e "   ${CYAN}${WEBSITE_URL}${NC}"
        echo -e "\n${GREEN}🚀 Your Robot Puzzle Game is live at:${NC}"
        echo -e "   ${CYAN}$WEBSITE_URL${NC}"
    fi
    
    if [[ -n "$API_URL" ]]; then
        echo -e "\n${BLUE}🔌 API Information:${NC}"
        echo -e "   API Gateway URL: ${CYAN}$API_URL${NC}"
    fi
    
    if [[ -n "$USER_POOL_ID" ]]; then
        echo -e "\n${PURPLE}🔐 Authentication:${NC}"
        echo -e "   User Pool ID: ${CYAN}$USER_POOL_ID${NC}"
        echo -e "   User Pool Client ID: ${CYAN}$USER_POOL_CLIENT_ID${NC}"
    fi
    
    echo -e "\n${YELLOW}🔗 Next Steps:${NC}"
    echo -e "   1. ${CYAN}Visit your website${NC} and create an account"
    echo -e "   2. ${CYAN}Test the board configuration tool${NC} to create custom puzzles"
    echo -e "   3. ${CYAN}Play the game${NC} and enjoy your creation!"
    
    echo -e "\n${YELLOW}📚 Resources:${NC}"
    echo -e "   • CloudFormation Console: https://console.aws.amazon.com/cloudformation/"
    echo -e "   • S3 Bucket: https://console.aws.amazon.com/s3/buckets/${BUCKET_NAME}"
    echo -e "   • API Gateway: https://console.aws.amazon.com/apigateway/"
    echo -e "   • Cognito User Pool: https://console.aws.amazon.com/cognito/"
    
    echo -e "\n${YELLOW}🧹 Cleanup:${NC}"
    echo -e "   To delete all resources: ${CYAN}aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION${NC}"
    
    echo -e "\n${YELLOW}🆘 Troubleshooting:${NC}"
    echo -e "   • Check logs: ${CYAN}./check-deployment.sh${NC}"
    echo -e "   • Monitor stack: ${CYAN}aws cloudformation describe-stack-events --stack-name $STACK_NAME${NC}"
    echo -e "   • View in console: https://console.aws.amazon.com/cloudformation/home?region=$REGION#/stacks"
}

# Main deployment function
main() {
    START_TIME=$(date +%s)
    
    echo -e "${PURPLE}🚀 Robot Puzzle Game - AWS Deployment${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log "${BLUE}🏁 Starting deployment process...${NC}"
    
    # Validation phase
    validate_aws_setup
    validate_template
    
    # Deployment phase
    if deploy_stack; then
        log "${GREEN}✅ Infrastructure deployment successful${NC}"
    else
        log "${RED}❌ Infrastructure deployment failed${NC}"
        exit 1
    fi
    
    # Always try to get stack outputs and show the production URL
    # This ensures we show the URL even when there are no infrastructure changes
    if get_stack_outputs; then
        log "${GREEN}✅ Stack outputs retrieved${NC}"
        
        # Update configuration if outputs are available
        if update_aws_config; then
            log "${GREEN}✅ Configuration update successful${NC}"
        else
            log "${YELLOW}⚠️  Configuration update failed, but proceeding${NC}"
        fi
        
        # Upload phase
        if upload_website_files; then
            log "${GREEN}✅ Website upload successful${NC}"
        else
            log "${YELLOW}⚠️  Website upload failed, but proceeding${NC}"
        fi
        
        # Testing phase
        test_deployment
        
        # Always show summary with production URL
        show_deployment_summary
        exit 0
    else
        log "${RED}❌ Unable to retrieve stack outputs${NC}"
        exit 1
    fi
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi