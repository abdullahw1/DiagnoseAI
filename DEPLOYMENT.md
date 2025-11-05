# DiagnoseAI Deployment Guide

This guide covers deploying DiagnoseAI to production environments.

## Quick Start (Local/Development)

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd DiagnoseAI
   ```

2. **Configure Environment**
   ```bash
   cp .env.production .env
   # Edit .env with your configuration
   ```

3. **Deploy with Docker**
   ```bash
   ./deploy.sh
   ```

4. **Access Application**
   - Open http://localhost:5003
   - Register your first user account

## Production Deployment Options

### Option 1: Docker Compose (Recommended)

**Prerequisites:**
- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ RAM
- 10GB+ disk space

**Steps:**
1. Configure environment variables in `.env`
2. Run deployment script: `./deploy.sh`
3. Configure reverse proxy (nginx included)

### Option 2: Cloud Deployment

#### AWS ECS/Fargate
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker build -t diagnoseai .
docker tag diagnoseai:latest <account>.dkr.ecr.us-east-1.amazonaws.com/diagnoseai:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/diagnoseai:latest
```

#### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/diagnoseai
gcloud run deploy --image gcr.io/PROJECT-ID/diagnoseai --platform managed
```

#### Azure Container Instances
```bash
# Build and push to ACR
az acr build --registry myregistry --image diagnoseai .
az container create --resource-group myResourceGroup --name diagnoseai --image myregistry.azurecr.io/diagnoseai:latest
```

## Environment Configuration

### Required Variables
```bash
SECRET_KEY=your-very-secure-secret-key-here
OPENAI_API_KEY=sk-your-openai-api-key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Optional Variables
```bash
FLASK_ENV=production
UPLOAD_FOLDER=/app/uploads
MAX_CONTENT_LENGTH=52428800
LOG_LEVEL=INFO
HOSPITAL_NAME="Your Hospital Name"
```

## Database Setup

### PostgreSQL (Recommended for Production)
```bash
# Using Docker Compose (included)
docker-compose up -d db

# Or external PostgreSQL
DATABASE_URL=postgresql://user:pass@your-db-host:5432/diagnoseai
```

### SQLite (Development Only)
```bash
# Automatically created in instance/diagnoseai.db
# Not recommended for production
```

## SSL/HTTPS Configuration

### Using Let's Encrypt (Recommended)
```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ./ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ./ssl/key.pem

# Update nginx.conf with your domain
# Uncomment HTTPS server block

# Deploy with nginx
docker-compose --profile production up -d
```

### Using Custom Certificates
```bash
# Place your certificates in ./ssl/
cp your-cert.pem ./ssl/cert.pem
cp your-key.pem ./ssl/key.pem

# Update nginx.conf
# Deploy with nginx
docker-compose --profile production up -d
```

## Monitoring and Maintenance

### Health Checks
- Application: `http://your-domain/health`
- Database: Built-in PostgreSQL health checks
- Container: Docker health checks included

### Logs
```bash
# View application logs
docker-compose logs -f web

# View database logs
docker-compose logs -f db

# View nginx logs
docker-compose logs -f nginx
```

### Backups
```bash
# Database backup
docker-compose exec db pg_dump -U diagnoseai_user diagnoseai > backup.sql

# Restore database
docker-compose exec -T db psql -U diagnoseai_user diagnoseai < backup.sql

# Backup uploaded files
docker run --rm -v diagnoseai_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

### Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations if needed
docker-compose exec web flask db upgrade
```

## Security Considerations

### Network Security
- Use HTTPS in production
- Configure firewall rules
- Use VPN for admin access
- Enable rate limiting (included in nginx config)

### Application Security
- Change default SECRET_KEY
- Use strong database passwords
- Enable CSRF protection
- Regular security updates

### Data Security
- Encrypt data at rest
- Use secure file permissions
- Regular backups
- HIPAA compliance considerations

## Performance Optimization

### Scaling
```bash
# Scale web workers
docker-compose up -d --scale web=3

# Use load balancer
# Configure nginx upstream with multiple backends
```

### Database Optimization
- Use connection pooling
- Regular VACUUM and ANALYZE
- Monitor query performance
- Consider read replicas for high load

### File Storage
- Use cloud storage (S3, GCS, Azure Blob) for uploaded images
- Configure CDN for static assets
- Implement file compression

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check database status
docker-compose ps db
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d db
```

**File Upload Issues**
```bash
# Check upload directory permissions
docker-compose exec web ls -la /app/uploads

# Check disk space
docker-compose exec web df -h
```

**Memory Issues**
```bash
# Check container memory usage
docker stats

# Increase memory limits in docker-compose.yml
```

### Support
- Check logs: `docker-compose logs -f`
- Verify environment variables: `docker-compose config`
- Test database connection: `docker-compose exec web flask shell`

## Production Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups scheduled
- [ ] Monitoring configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Log rotation setup
- [ ] Health checks working
- [ ] Firewall rules configured
- [ ] DNS records updated