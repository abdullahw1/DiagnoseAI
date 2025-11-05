#!/bin/bash

# AWS Deployment Script for DiagnoseAI
# Ultra-budget deployment using EC2 t3.micro

set -e

echo "☁️  DiagnoseAI AWS Deployment (Budget Mode)"
echo "==========================================="

# Configuration
REGION="us-east-1"
INSTANCE_TYPE="t3.micro"
KEY_NAME="diagnoseai-key"
SECURITY_GROUP_NAME="diagnoseai-sg"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   pip install awscli"
    exit 1
fi

# Check if configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS CLI configured"

# Get account ID and default VPC
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text)
SUBNET_ID=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[0].SubnetId" --output text)

echo "📋 Using Account: $ACCOUNT_ID"
echo "📋 Using VPC: $VPC_ID"
echo "📋 Using Subnet: $SUBNET_ID"

# Create key pair if it doesn't exist
if ! aws ec2 describe-key-pairs --key-names $KEY_NAME &> /dev/null; then
    echo "🔑 Creating key pair..."
    aws ec2 create-key-pair --key-name $KEY_NAME --query 'KeyMaterial' --output text > ${KEY_NAME}.pem
    chmod 400 ${KEY_NAME}.pem
    echo "✅ Key pair created: ${KEY_NAME}.pem"
else
    echo "✅ Key pair already exists"
fi

# Create security group if it doesn't exist
SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SECURITY_GROUP_NAME" --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ]; then
    echo "🔒 Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name $SECURITY_GROUP_NAME \
        --description "DiagnoseAI Security Group" \
        --vpc-id $VPC_ID \
        --query 'GroupId' --output text)
    
    # Add rules
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 80 --cidr 0.0.0.0/0
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 443 --cidr 0.0.0.0/0
    aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 5003 --cidr 0.0.0.0/0
    
    echo "✅ Security group created: $SG_ID"
else
    echo "✅ Security group already exists: $SG_ID"
fi

# Get latest Amazon Linux 2 AMI
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" "Name=state,Values=available" \
    --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" \
    --output text)

echo "📦 Using AMI: $AMI_ID"

# Create user data script
cat > user-data.sh << 'EOF'
#!/bin/bash
yum update -y
yum install -y docker git

# Start Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Wait for Docker to be ready
sleep 10

# Clone repository (replace with your repo URL)
cd /home/ec2-user
git clone https://github.com/your-username/DiagnoseAI.git || {
    echo "Failed to clone repository. Creating minimal setup..."
    mkdir -p DiagnoseAI
    cd DiagnoseAI
    
    # Create minimal docker-compose for SQLite version
    cat > docker-compose.yml << 'COMPOSE_EOF'
version: '3.8'
services:
  web:
    image: python:3.11-slim
    ports:
      - "5003:5003"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///instance/diagnoseai.db
      - SECRET_KEY=change-this-secret-key-in-production
      - OPENAI_API_KEY=your-openai-key-here
    volumes:
      - ./:/app
    working_dir: /app
    command: bash -c "pip install -r requirements.txt && python migrate_db.py && gunicorn --bind 0.0.0.0:5003 --workers 2 start:app"
COMPOSE_EOF
}

cd DiagnoseAI

# Create environment file
cat > .env << 'ENV_EOF'
SECRET_KEY=your-secret-key-change-this-in-production
OPENAI_API_KEY=your-openai-key-here
DATABASE_URL=sqlite:///instance/diagnoseai.db
FLASK_ENV=production
HOSPITAL_NAME=Demo Hospital
ENV_EOF

# Create instance directory
mkdir -p instance

# Start the application
docker-compose up -d

# Create a simple status page
cat > /var/www/html/status.html << 'STATUS_EOF'
<!DOCTYPE html>
<html>
<head><title>DiagnoseAI Status</title></head>
<body>
<h1>DiagnoseAI Deployment Status</h1>
<p>Application should be running on port 5003</p>
<p><a href="http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5003">Access DiagnoseAI</a></p>
</body>
</html>
STATUS_EOF

echo "Deployment completed!" > /var/log/deployment.log
EOF

# Launch EC2 instance
echo "🚀 Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --count 1 \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --subnet-id $SUBNET_ID \
    --user-data file://user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=DiagnoseAI-Server}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo "🎉 Deployment completed!"
echo "================================"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "SSH Command: ssh -i ${KEY_NAME}.pem ec2-user@$PUBLIC_IP"
echo ""
echo "⏳ Application is starting up (may take 5-10 minutes)..."
echo "🌐 Access your app at: http://$PUBLIC_IP:5003"
echo ""
echo "💰 Monthly cost estimate: ~$8-12"
echo "📊 Monitor usage in AWS Console"
echo ""
echo "🔧 Next steps:"
echo "1. Wait 5-10 minutes for deployment to complete"
echo "2. Access the application and change default passwords"
echo "3. Configure your OpenAI API key in .env file"
echo "4. Set up a domain name (optional)"
echo ""
echo "🛑 To stop/terminate:"
echo "   aws ec2 terminate-instances --instance-ids $INSTANCE_ID"

# Clean up
rm -f user-data.sh