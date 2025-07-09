# Custom Domain Setup with HTTPS

This guide explains how to set up your Robot Puzzle Game with a custom domain and HTTPS using CloudFront.

## Prerequisites

1. **Domain Name**: You need to own a domain name (e.g., `yourdomain.com`)
2. **AWS Account**: With appropriate permissions to create CloudFront distributions and ACM certificates

## Step 1: Request SSL Certificate

1. Go to AWS Certificate Manager (ACM) in the **us-east-1 (N. Virginia)** region
   - **Important**: CloudFront requires certificates to be in us-east-1
2. Click "Request a certificate"
3. Choose "Request a public certificate"
4. Enter your domain name (e.g., `puzzle.yourdomain.com`)
5. Choose DNS validation
6. Complete the DNS validation by adding the CNAME record to your domain's DNS

Wait for the certificate status to become "Issued" before proceeding.

## Step 2: Configure the Deployment Script

Edit the `deploy.sh` file and update these variables:

```bash
# Custom Domain Configuration (Optional)
CUSTOM_DOMAIN="puzzle.yourdomain.com"  # Your subdomain
CERTIFICATE_ARN="arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"  # Your certificate ARN
```

To get your Certificate ARN:
1. Go to AWS Certificate Manager in us-east-1
2. Find your certificate
3. Copy the ARN (it starts with `arn:aws:acm:us-east-1:`)

## Step 3: Deploy with Custom Domain

Run the deployment:

```bash
./deploy.sh
```

The script will:
1. Create a CloudFront distribution
2. Configure HTTPS with your certificate
3. Set up caching and compression
4. Provide you with the CloudFront URL

## Step 4: Update DNS

After deployment, you'll get a CloudFront distribution URL like:
`https://d1234567890.cloudfront.net`

Create a CNAME record in your domain's DNS:
- **Name**: `puzzle` (or whatever subdomain you chose)
- **Type**: `CNAME`
- **Value**: `d1234567890.cloudfront.net` (your CloudFront domain)

## Step 5: Wait for Propagation

- DNS changes can take up to 48 hours to propagate globally
- CloudFront distribution deployment takes 15-20 minutes
- You can check status in the AWS CloudFront console

## Benefits of This Setup

✅ **HTTPS by default** - All traffic is encrypted  
✅ **Global CDN** - Fast loading worldwide via CloudFront edge locations  
✅ **Custom Domain** - Professional URL for your game  
✅ **Caching** - Improved performance and reduced costs  
✅ **Automatic redirects** - HTTP traffic redirects to HTTPS  

## Troubleshooting

### Certificate Issues
- Ensure certificate is in us-east-1 region
- Verify DNS validation is complete
- Check certificate status is "Issued"

### DNS Issues
- Verify CNAME record points to CloudFront domain
- Use `dig` or `nslookup` to test DNS resolution
- Wait for DNS propagation (up to 48 hours)

### CloudFront Issues
- Check distribution status in AWS console
- Ensure origin is pointing to S3 bucket
- Verify cache behaviors are configured correctly

## Example Configuration

For domain `example.com`, to set up `puzzle.example.com`:

1. **Certificate**: Request for `puzzle.example.com` in us-east-1
2. **Deploy script**: Set `CUSTOM_DOMAIN="puzzle.example.com"`
3. **DNS**: Add CNAME record: `puzzle.example.com` → `d1234567890.cloudfront.net`

Your game will be available at: `https://puzzle.example.com`