# AWS Elastic Beanstalk Deployment Guide

## Overview
This guide covers deploying the BetterMeals Agents application to AWS Elastic Beanstalk using Docker and AWS Secrets Manager for secure configuration management.

## Prerequisites

### 1. AWS CLI Setup
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
```

### 2. EB CLI Setup
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init
```

### 3. Docker Setup
```bash
# Ensure Docker is installed and running
docker --version
```

## Pre-Deployment Setup

### 1. Create AWS Secrets Manager Secret
```bash
# Create the secret in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "prod/bettermeals-backend/env" \
    --description "Secrets for BetterMeals Agents" \
    --secret-string '{
        "GROQ_API_KEY": "your_groq_api_key_here",
        "CLAUDE_API_KEY": "your_claude_api_key_here",
        "TAVILY_API_KEY": "your_tavily_api_key_here",
        "BM_API_BASE": "http://staging-bm.eba-n3mspgd3.ap-south-1.elasticbeanstalk.com"
    }'
```

### 2. Configure IAM Role
Ensure your Elastic Beanstalk EC2 instance role has the following policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:ap-south-1:*:secret:prod/bettermeals-backend/env*"
        }
    ]
}
```

## Deployment Steps

### 1. Build and Test Locally
```bash
# Build the Docker image
docker build -t bettermeals-agents .

# Test locally
docker run -p 8000:8000 \
    -e AWS_REGION=ap-south-1 \
    -e SECRETS_MANAGER_SECRET_NAME=prod/bettermeals-backend/env \
    bettermeals-agents
```

### 2. Deploy to Elastic Beanstalk
```bash
# Create environment (first time only)
eb create bettermeals-agent --platform "Docker running on 64bit Amazon Linux 2"

# Deploy updates
eb deploy
```

### 3. Configure Custom Domain (Optional)
```bash
# Option 1: Use EB CLI to configure domain
eb config

# Option 2: Configure through AWS Console
# Go to Elastic Beanstalk > Environment > Configuration > Load Balancer
# Add custom domain and SSL certificate
```

### 4. Verify Deployment
```bash
# Check application health
eb health

# View logs
eb logs

# Open application in browser
eb open
```

## URL Configuration

### Default URL
After deployment, your application will be available at:
```
http://bettermeals-agent.elasticbeanstalk.com
```

### Custom Domain Setup
To use a custom domain (e.g., `api.bettermeals.com`):

1. **Route 53 (Recommended)**:
   ```bash
   # Create hosted zone for your domain
   aws route53 create-hosted-zone --name bettermeals.com --caller-reference $(date +%s)
   
   # Get the Elastic Beanstalk environment URL
   eb status
   
   # Create CNAME record pointing to EB environment
   ```

2. **Manual DNS Configuration**:
   - Point your domain's CNAME record to: `bettermeals-agent.elasticbeanstalk.com`
   - Configure SSL certificate in Elastic Beanstalk console

3. **Update Environment Configuration**:
   ```bash
   # Edit .ebextensions/01-environment.config to add:
   option_settings:
     aws:elasticbeanstalk:environment:proxy:
       ProxyServer: nginx
     aws:elasticbeanstalk:environment:loadbalancer:ssl:
       ListenerProtocol: HTTPS
       SSLCertificateId: arn:aws:acm:ap-south-1:ACCOUNT:certificate/CERT-ID
   ```

### Environment URL Management
```bash
# List all environments
eb list

# Get environment URL
eb status

# Change environment name (if needed)
eb rename OLD_NAME NEW_NAME
```

## Configuration Files

### Key Files:
- `Dockerrun.aws.json` - Elastic Beanstalk Docker configuration
- `.ebextensions/01-environment.config` - Environment settings
- `src/bettermeals/config/secrets_manager.py` - AWS Secrets Manager integration
- `src/bettermeals/config/settings.py` - Updated to use Secrets Manager
- `Dockerfile` - Production-ready Docker configuration
- `requirements.txt` - Added AWS SDK dependencies

## Environment Variables

### Required Environment Variables:
- `AWS_REGION=ap-south-1` - AWS region
- `SECRETS_MANAGER_SECRET_NAME=prod/bettermeals-backend/env` - Secret name

### Secrets Retrieved from AWS Secrets Manager:
- `GROQ_API_KEY` - Groq API key
- `CLAUDE_API_KEY` - Claude API key  
- `TAVILY_API_KEY` - Tavily API key
- `BM_API_BASE` - BetterMeals API base URL (staging: http://staging-bm.eba-n3mspgd3.ap-south-1.elasticbeanstalk.com)

## Monitoring and Troubleshooting

### Health Checks
- Application health check endpoint: `/webhooks/whatsapp`
- Docker health check configured in Dockerfile
- Elastic Beanstalk health monitoring enabled

### Logging
- Application logs: `/var/log/eb-docker/containers/eb-current-app`
- View logs: `eb logs`
- CloudWatch integration available

### Common Issues
1. **Secrets not loading**: Check IAM permissions and secret name
2. **Health check failures**: Verify endpoint accessibility
3. **Memory issues**: Adjust instance type in EB configuration
4. **Domain not working**: Check DNS configuration and SSL certificates

## Scaling Configuration

### Auto-Scaling Settings:
- Min instances: 1
- Max instances: 4
- Desired capacity: 2
- Health check grace period: 300 seconds

## Security Considerations

1. **Secrets Management**: All sensitive data stored in AWS Secrets Manager
2. **IAM Roles**: Minimal permissions for EC2 instances
3. **Network Security**: Configure security groups as needed
4. **Container Security**: Non-root user in Docker container
5. **SSL/TLS**: Configure HTTPS for production

## Rollback Procedure

```bash
# List deployment history
eb list

# Rollback to previous version
eb deploy --version <version-label>
```

## Cost Optimization

1. **Instance Types**: Start with t3.micro for testing
2. **Auto-Scaling**: Configure appropriate scaling policies
3. **Monitoring**: Use CloudWatch for cost tracking
4. **Reserved Instances**: Consider for production workloads

## Next Steps

1. Set up monitoring and alerting
2. Configure custom domain and SSL
3. Implement CI/CD pipeline
4. Set up backup and disaster recovery
5. Performance testing and optimization
