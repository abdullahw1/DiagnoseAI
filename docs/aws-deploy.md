# ☁️ AWS Deployment Guide (Budget-Friendly)

Deploy DiagnoseAI on AWS using your $100 credits efficiently.

## 💰 Cost Breakdown (Monthly)
- **ECS Fargate**: ~$15-25/month
- **RDS PostgreSQL (t3.micro)**: ~$15/month  
- **Application Load Balancer**: ~$16/month
- **Total**: ~$46-56/month (your $100 covers ~2 months)

## 🚀 Deployment Options

### Option 1: ECS Fargate (Recommended)
Serverless containers, pay only for what you use.

### Option 2: EC2 + Docker (Cheapest)
Single t3.micro instance (~$8/month)

---

## 🎯 Option 1: ECS Fargate Deployment

### Prerequisites
```bash
# Install AWS CLI
pip install awscli
aws configure
# Enter your AWS credentials

# Install ECS CLI
curl -Lo ecs-cli https://amazon-ecs-cli.s3.amazonaws.com/ecs-cli-darwin-amd64-latest
chmod +x ecs-cli && sudo mv ecs-cli /usr/local/bin
```

### Step 1: Create ECR Repository
```bash
# Create container registry
aws ecr create-repository --repository-name diagnoseai --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### Step 2: Build and Push Image
```bash
# Build image
docker build -t diagnoseai .

# Tag for ECR
docker tag diagnoseai:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/diagnoseai:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/diagnoseai:latest
```

### Step 3: Create RDS Database
```bash
# Create DB subnet group
aws rds create-db-subnet-group \
    --db-subnet-group-name diagnoseai-subnet-group \
    --db-subnet-group-description "DiagnoseAI DB Subnet Group" \
    --subnet-ids subnet-12345 subnet-67890

# Create PostgreSQL database
aws rds create-db-instance \
    --db-instance-identifier diagnoseai-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username diagnoseai \
    --master-user-password YourSecurePassword123 \
    --allocated-storage 20 \
    --db-name diagnoseai \
    --vpc-security-group-ids sg-12345 \
    --db-subnet-group-name diagnoseai-subnet-group \
    --backup-retention-period 7 \
    --storage-encrypted
```

### Step 4: Create ECS Task Definition
Create `task-definition.json`:
```json
{
  "family": "diagnoseai",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "diagnoseai",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/diagnoseai:latest",
      "portMappings": [
        {
          "containerPort": 5003,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://diagnoseai:YourSecurePassword123@your-rds-endpoint:5432/diagnoseai"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:diagnoseai/secret-key"
        },
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:diagnoseai/openai-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/diagnoseai",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Step 5: Deploy with ECS
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create ECS cluster
aws ecs create-cluster --cluster-name diagnoseai-cluster

# Create service
aws ecs create-service \
    --cluster diagnoseai-cluster \
    --service-name diagnoseai-service \
    --task-definition diagnoseai:1 \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

---

## 💡 Option 2: EC2 Single Instance (Ultra Budget)

### Cost: ~$8-12/month

### Step 1: Launch EC2 Instance
```bash
# Launch t3.micro instance (free tier eligible)
aws ec2 run-instances \
    --image-id ami-0abcdef1234567890 \
    --count 1 \
    --instance-type t3.micro \
    --key-name your-key-pair \
    --security-group-ids sg-12345 \
    --subnet-id subnet-12345 \
    --user-data file://user-data.sh
```

### Step 2: User Data Script
Create `user-data.sh`:
```bash
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

# Clone and deploy
cd /home/ec2-user
git clone https://github.com/your-username/DiagnoseAI.git
cd DiagnoseAI

# Create environment file
cat > .env << EOF
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key-here
DATABASE_URL=sqlite:///instance/diagnoseai.db
FLASK_ENV=production
EOF

# Deploy with Docker Compose
docker-compose up -d
```

### Step 3: Configure Security Group
```bash
# Allow HTTP/HTTPS traffic
aws ec2 authorize-security-group-ingress \
    --group-id sg-12345 \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-12345 \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
    --group-id sg-12345 \
    --protocol tcp \
    --port 5003 \
    --cidr 0.0.0.0/0
```

---

## 🔧 AWS Automation Script

Let me create an automated deployment script: