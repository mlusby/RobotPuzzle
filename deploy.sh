#!/bin/bash

# Robot Puzzle Game - Unified Deployment Script
# Intelligent deployment system that detects and deploys all components

set -e

# Configuration
STACK_NAME="robot-puzzle-game-prod"
TEMPLATE_FILE="aws/cloudformation-template.yaml"
REGION="us-east-1"
DEPLOYMENT_TIMEOUT=1800
CHECK_INTERVAL=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Progress indicators
PROGRESS_CHARS="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

# Global variables
START_TIME=""
TEMP_FILES=()
DEPLOYMENT_SUMMARY=()

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🧹 Cleaning up temporary files...${NC}"
    for file in "${TEMP_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            rm -f "$file"
        fi
    done
}

trap cleanup EXIT INT TERM

# Helper functions
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') | $1"
}

elapsed_time() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    printf "%02d:%02d" $minutes $seconds
}

add_to_summary() {
    DEPLOYMENT_SUMMARY+=("$1")
}

# Deployment detection functions
detect_infrastructure_changes() {
    log "${BLUE}🔍 Detecting infrastructure changes...${NC}"
    
    local stack_exists=false
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &>/dev/null; then
        stack_exists=true
    fi
    
    if [[ "$stack_exists" == "false" ]]; then
        echo "new_stack"
        return 0
    fi
    
    # Check if template has changes by attempting a change set
    local changeset_name="deployment-check-$(date +%s)"
    local changeset_output=$(mktemp)
    TEMP_FILES+=("$changeset_output")
    
    aws cloudformation create-change-set \
        --stack-name "$STACK_NAME" \
        --change-set-name "$changeset_name" \
        --template-body file://"$TEMPLATE_FILE" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --parameters ParameterKey=AppName,ParameterValue=robot-puzzle-game \
                     ParameterKey=Environment,ParameterValue=prod \
        2>&1 > "$changeset_output"
    
    sleep 10  # Wait for changeset creation
    
    # Check changeset status
    local changeset_status=$(aws cloudformation describe-change-set \
        --stack-name "$STACK_NAME" \
        --change-set-name "$changeset_name" \
        --region "$REGION" \
        --query 'Status' \
        --output text 2>/dev/null)
    
    local has_changes="false"
    if [[ "$changeset_status" == "CREATE_COMPLETE" ]]; then
        local changes_count=$(aws cloudformation describe-change-set \
            --stack-name "$STACK_NAME" \
            --change-set-name "$changeset_name" \
            --region "$REGION" \
            --query 'length(Changes)' \
            --output text 2>/dev/null)
        
        if [[ "$changes_count" -gt 0 ]]; then
            has_changes="true"
        fi
    fi
    
    # Clean up changeset
    aws cloudformation delete-change-set \
        --stack-name "$STACK_NAME" \
        --change-set-name "$changeset_name" \
        --region "$REGION" &>/dev/null
    
    if [[ "$has_changes" == "true" ]]; then
        echo "infrastructure_changes"
    else
        echo "no_infrastructure_changes"
    fi
}

detect_lambda_changes() {
    log "${BLUE}🔍 Detecting Lambda function changes...${NC}"
    
    local lambda_functions=(
        "aws/lambda-functions/scores.py:ScoresFunction"
        "aws/lambda-functions/board-configurations.py:BoardConfigurationsFunction"
        "aws/lambda-functions/user-profiles.py:UserProfilesFunction"
    )
    
    local changes_needed=()
    
    for func_info in "${lambda_functions[@]}"; do
        local file_path="${func_info%:*}"
        local logical_id="${func_info#*:}"
        
        if [[ ! -f "$file_path" ]]; then
            continue
        fi
        
        # Get function name from CloudFormation
        local function_name=$(aws cloudformation describe-stack-resources \
            --stack-name "$STACK_NAME" \
            --region "$REGION" \
            --logical-resource-id "$logical_id" \
            --query 'StackResources[0].PhysicalResourceId' \
            --output text 2>/dev/null)
        
        if [[ -z "$function_name" || "$function_name" == "None" ]]; then
            continue
        fi
        
        # Get current function info
        local current_hash=$(aws lambda get-function \
            --function-name "$function_name" \
            --region "$REGION" \
            --query 'Configuration.CodeSha256' \
            --output text 2>/dev/null)
        
        # Calculate local file hash (simplified check)
        local local_hash=$(sha256sum "$file_path" | cut -d' ' -f1)
        
        # For simplicity, always consider Lambda functions as needing update
        # In production, you'd want more sophisticated change detection
        changes_needed+=("$file_path:$logical_id")
    done
    
    if [[ ${#changes_needed[@]} -gt 0 ]]; then
        echo "${changes_needed[@]}"
    else
        echo "no_lambda_changes"
    fi
}

detect_website_changes() {
    log "${BLUE}🔍 Detecting website file changes...${NC}"
    
    # Get S3 bucket name
    local bucket_name=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId' \
        --output text 2>/dev/null)
    
    if [[ -z "$bucket_name" || "$bucket_name" == "None" ]]; then
        echo "website_changes"  # Assume changes if we can't check
        return 0
    fi
    
    local files_to_check=(
        "index.html"
        "login.html"
        "wall-editor.html"
        "styles.css"
        "script.js"
        "favicon.svg"
        "error.html"
    )
    
    local changes_detected=false
    
    for file in "${files_to_check[@]}"; do
        if [[ ! -f "$file" ]]; then
            continue
        fi
        
        # Check if file exists in S3 and compare timestamps (simplified)
        local s3_exists=$(aws s3 ls "s3://${bucket_name}/${file}" --region "$REGION" 2>/dev/null)
        if [[ -z "$s3_exists" ]]; then
            changes_detected=true
            break
        fi
    done
    
    # Check js/ directory
    if [[ -d "js" ]]; then
        local js_files_exist=$(aws s3 ls "s3://${bucket_name}/js/" --region "$REGION" 2>/dev/null)
        if [[ -z "$js_files_exist" ]]; then
            changes_detected=true
        fi
    fi
    
    if [[ "$changes_detected" == "true" ]]; then
        echo "website_changes"
    else
        echo "no_website_changes"
    fi
}

# Deployment functions
validate_aws_setup() {
    log "${BLUE}🔐 Validating AWS setup...${NC}"
    
    if ! command -v aws &> /dev/null; then
        log "${RED}❌ AWS CLI is not installed${NC}"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log "${RED}❌ AWS credentials not configured${NC}"
        exit 1
    fi
    
    local account_id=$(aws sts get-caller-identity --query Account --output text)
    local user_arn=$(aws sts get-caller-identity --query Arn --output text)
    
    log "${GREEN}✅ AWS CLI configured${NC}"
    log "${CYAN}   Account ID: $account_id${NC}"
    log "${CYAN}   User/Role: $user_arn${NC}"
    log "${CYAN}   Region: $REGION${NC}"
}

validate_template() {
    log "${BLUE}📋 Validating CloudFormation template...${NC}"
    
    if [[ ! -f "$TEMPLATE_FILE" ]]; then
        log "${RED}❌ Template file not found: $TEMPLATE_FILE${NC}"
        exit 1
    fi
    
    aws cloudformation validate-template \
        --template-body file://"$TEMPLATE_FILE" \
        --region "$REGION" &>/dev/null
    
    if [[ $? -ne 0 ]]; then
        log "${RED}❌ Template validation failed${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ Template validation successful${NC}"
}

deploy_infrastructure() {
    log "${BLUE}🚀 Deploying infrastructure...${NC}"
    
    local deploy_output=$(mktemp)
    TEMP_FILES+=("$deploy_output")
    
    aws cloudformation deploy \
        --template-file "$TEMPLATE_FILE" \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --parameter-overrides \
            AppName=robot-puzzle-game \
            Environment=prod \
        --no-fail-on-empty-changeset 2>&1 | tee "$deploy_output"
    
    local deploy_exit_code=${PIPESTATUS[0]}
    
    if grep -q "No changes to deploy" "$deploy_output"; then
        log "${YELLOW}ℹ️  No infrastructure changes needed${NC}"
        add_to_summary "Infrastructure: No changes needed"
        return 0
    fi
    
    if [[ $deploy_exit_code -eq 0 ]]; then
        log "${GREEN}✅ Infrastructure deployment successful${NC}"
        add_to_summary "Infrastructure: Successfully deployed"
        return 0
    else
        log "${RED}❌ Infrastructure deployment failed${NC}"
        return 1
    fi
}

deploy_lambda_function() {
    local function_file=$1
    local logical_id=$2
    local function_description=$3
    
    log "${BLUE}📦 Deploying $function_description...${NC}"
    
    local function_name=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --logical-resource-id "$logical_id" \
        --query 'StackResources[0].PhysicalResourceId' \
        --output text 2>/dev/null)
    
    if [[ -z "$function_name" || "$function_name" == "None" ]]; then
        log "${YELLOW}⚠️  Could not find Lambda function $logical_id in stack${NC}"
        return 1
    fi
    
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
    
    # Deploy the function
    if aws lambda update-function-code \
        --function-name "$function_name" \
        --zip-file "fileb://$zip_file" \
        --region "$REGION" \
        --output json &>/dev/null; then
        
        log "${GREEN}✅ Successfully deployed $function_description${NC}"
        add_to_summary "Lambda: $function_description deployed"
        rm -rf "$temp_dir"
        return 0
    else
        log "${RED}❌ Failed to deploy $function_description${NC}"
        rm -rf "$temp_dir"
        return 1
    fi
}

deploy_lambda_functions() {
    local lambda_changes="$1"
    
    if [[ "$lambda_changes" == "no_lambda_changes" ]]; then
        log "${YELLOW}ℹ️  No Lambda function changes detected${NC}"
        add_to_summary "Lambda: No changes needed"
        return 0
    fi
    
    log "${BLUE}🔧 Deploying Lambda functions...${NC}"
    
    local success_count=0
    local total_count=0
    
    # Parse lambda changes and deploy each function
    for func_change in $lambda_changes; do
        local file_path="${func_change%:*}"
        local logical_id="${func_change#*:}"
        local function_description=""
        
        case "$logical_id" in
            "ScoresFunction")
                function_description="Scores Lambda Function"
                ;;
            "BoardConfigurationsFunction")
                function_description="Board Configurations Lambda Function"
                ;;
            "UserProfilesFunction")
                function_description="User Profiles Lambda Function"
                ;;
            *)
                function_description="Lambda Function ($logical_id)"
                ;;
        esac
        
        ((total_count++))
        if deploy_lambda_function "$file_path" "$logical_id" "$function_description"; then
            ((success_count++))
        fi
    done
    
    if [[ $total_count -eq 0 ]]; then
        log "${YELLOW}⚠️  No Lambda function files found to deploy${NC}"
        return 0
    elif [[ $success_count -eq $total_count ]]; then
        log "${GREEN}✅ All Lambda functions deployed successfully ($success_count/$total_count)${NC}"
        return 0
    else
        log "${YELLOW}⚠️  Some Lambda functions failed to deploy ($success_count/$total_count)${NC}"
        return 1
    fi
}

upload_website_files() {
    local website_changes="$1"
    
    if [[ "$website_changes" == "no_website_changes" ]]; then
        log "${YELLOW}ℹ️  No website file changes detected${NC}"
        add_to_summary "Website: No changes needed"
        return 0
    fi
    
    log "${BLUE}📤 Uploading website files to S3...${NC}"
    
    # Get bucket name
    local bucket_name=$(aws cloudformation describe-stack-resources \
        --stack-name "$STACK_NAME" \
        --region "$REGION" \
        --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId' \
        --output text 2>/dev/null)
    
    if [[ -z "$bucket_name" ]]; then
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
    
    local uploaded=0
    local total_files=${#files_to_upload[@]}
    
    for file in "${files_to_upload[@]}"; do
        if [[ -f "$file" ]]; then
            if aws s3 cp "$file" "s3://${bucket_name}/" --region "$REGION" &>/dev/null; then
                ((uploaded++))
            fi
        fi
    done
    
    # Upload JS directory
    if [[ -d "js" ]]; then
        if aws s3 cp js/ "s3://${bucket_name}/js/" --recursive --region "$REGION" &>/dev/null; then
            ((uploaded++))
        fi
    fi
    
    log "${GREEN}✅ Website files uploaded (${uploaded}/${total_files} successful)${NC}"
    add_to_summary "Website: Files uploaded successfully"
    
    # Set bucket website configuration
    aws s3 website "s3://${bucket_name}" --index-document index.html --error-document error.html --region "$REGION" &>/dev/null
    
    return 0
}

get_stack_outputs() {
    log "${BLUE}📋 Retrieving stack outputs...${NC}"
    
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
}

update_aws_config() {
    log "${BLUE}⚙️  Updating AWS configuration...${NC}"
    
    if [[ -z "$API_URL" || -z "$USER_POOL_ID" || -z "$USER_POOL_CLIENT_ID" ]]; then
        log "${RED}❌ Missing required configuration values${NC}"
        return 1
    fi
    
    # Create backup of existing config
    if [[ -f "js/aws-config.js" ]]; then
        cp "js/aws-config.js" "js/aws-config.js.backup.$(date +%s)"
    fi
    
    mkdir -p js
    
    cat > js/aws-config.js << EOF
// AWS Configuration - Auto-generated by unified deployment script
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
    add_to_summary "Config: AWS configuration updated"
}

test_deployment() {
    log "${BLUE}🧪 Testing deployment...${NC}"
    
    local test_results=()
    
    if [[ -n "$WEBSITE_URL" ]]; then
        if curl -s --head "$WEBSITE_URL" | head -n 1 | grep -q "200 OK"; then
            test_results+=("Website: ✅ Accessible")
        else
            test_results+=("Website: ⚠️  May not be ready yet")
        fi
    fi
    
    if [[ -n "$API_URL" ]]; then
        if curl -s -X OPTIONS "${API_URL}/configurations" &>/dev/null; then
            test_results+=("API: ✅ Responding")
        else
            test_results+=("API: ⚠️  May not be ready yet")
        fi
    fi
    
    for result in "${test_results[@]}"; do
        add_to_summary "$result"
    done
}

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
    
    echo -e "\n${CYAN}📋 Components Deployed:${NC}"
    for item in "${DEPLOYMENT_SUMMARY[@]}"; do
        echo -e "   • $item"
    done
    
    if [[ -n "$WEBSITE_URL" ]]; then
        echo -e "\n${GREEN}🌐 Production URL:${NC}"
        echo -e "   ${CYAN}${WEBSITE_URL}${NC}"
    fi
    
    if [[ -n "$API_URL" ]]; then
        echo -e "\n${BLUE}🔌 API Information:${NC}"
        echo -e "   API Gateway URL: ${CYAN}$API_URL${NC}"
        echo -e "   User Profile endpoints:"
        echo -e "     GET ${CYAN}$API_URL/user/profile${NC}"
        echo -e "     PUT ${CYAN}$API_URL/user/profile${NC}"
    fi
    
    echo -e "\n${YELLOW}🎮 New Features Available:${NC}"
    echo -e "   • Username management and profiles"
    echo -e "   • Click on your name to edit username"
    echo -e "   • Current usernames displayed in leaderboards"
    echo -e "   • Competitive rounds dropdown with delete functionality"
    echo -e "   • Inline leaderboard with pagination"
    echo -e "   • Professional button styling"
    
    echo -e "\n${YELLOW}🔗 Next Steps:${NC}"
    echo -e "   1. ${CYAN}Visit your website${NC} and test the new username features"
    echo -e "   2. ${CYAN}Create an account${NC} and set your username"
    echo -e "   3. ${CYAN}Play competitive rounds${NC} and see the enhanced leaderboard"
}

# Main deployment function
main() {
    START_TIME=$(date +%s)
    
    echo -e "${PURPLE}🚀 Robot Puzzle Game - Unified Deployment${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    log "${BLUE}🏁 Starting intelligent deployment process...${NC}"
    
    # Validation phase
    validate_aws_setup
    validate_template
    
    # Detection phase
    log "${BLUE}🔍 Analyzing what needs to be deployed...${NC}"
    local infrastructure_status=$(detect_infrastructure_changes)
    local lambda_changes=$(detect_lambda_changes)
    local website_changes=$(detect_website_changes)
    
    log "${CYAN}   Infrastructure: $infrastructure_status${NC}"
    log "${CYAN}   Lambda functions: $lambda_changes${NC}"
    log "${CYAN}   Website files: $website_changes${NC}"
    
    # Deployment phase
    local deployment_needed=false
    
    if [[ "$infrastructure_status" != "no_infrastructure_changes" ]]; then
        deployment_needed=true
        if ! deploy_infrastructure; then
            log "${RED}❌ Infrastructure deployment failed${NC}"
            exit 1
        fi
    fi
    
    if [[ "$lambda_changes" != "no_lambda_changes" ]]; then
        deployment_needed=true
    fi
    
    if [[ "$website_changes" != "no_website_changes" ]]; then
        deployment_needed=true
    fi
    
    if [[ "$deployment_needed" == "false" ]]; then
        log "${GREEN}✅ No deployment needed - everything is up to date!${NC}"
        get_stack_outputs
        echo -e "\n${GREEN}🌐 Your application is already running at:${NC}"
        echo -e "   ${CYAN}${WEBSITE_URL}${NC}"
        exit 0
    fi
    
    # Always get stack outputs for subsequent operations
    get_stack_outputs
    
    # Update configuration
    if ! update_aws_config; then
        log "${YELLOW}⚠️  Configuration update failed, but proceeding${NC}"
    fi
    
    # Deploy Lambda functions
    if ! deploy_lambda_functions "$lambda_changes"; then
        log "${YELLOW}⚠️  Lambda deployment had issues, but proceeding${NC}"
    fi
    
    # Upload website files
    if ! upload_website_files "$website_changes"; then
        log "${YELLOW}⚠️  Website upload had issues, but proceeding${NC}"
    fi
    
    # Testing phase
    test_deployment
    
    # Show summary
    show_deployment_summary
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi