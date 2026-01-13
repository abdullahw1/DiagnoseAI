# 🚂 Railway Deployment Guide

Railway is the easiest and most cost-effective way to deploy DiagnoseAI.

## Cost: ~$5-10/month (includes database)

## Step-by-Step Deployment

### 1. Prepare Your Repository
```bash
# Make sure your code is in a Git repository
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Deploy to Railway

#### Option A: One-Click Deploy
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

#### Option B: Manual Deploy
1. Go to [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your DiagnoseAI repository
6. Railway will automatically detect the Dockerfile

### 3. Add PostgreSQL Database
1. In your Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Railway will automatically create a database and set DATABASE_URL

### 4. Configure Environment Variables
In Railway dashboard, go to your app → Variables:

```bash
# Required Variables
SECRET_KEY=your-super-secret-key-here-change-this
OPENAI_API_KEY=sk-your-openai-api-key
FLASK_ENV=production

# Optional Variables
HOSPITAL_NAME=Your Hospital Name
MAX_CONTENT_LENGTH=52428800
```

### 5. Deploy
1. Railway will automatically deploy when you push to main branch
2. Get your app URL from Railway dashboard
3. Access your app at: `https://your-app-name.railway.app`

### 6. Initialize Database
The migration script runs automatically on deployment, but you can also run it manually:

```bash
# In Railway dashboard → your app → Deploy logs
# You should see: "Database setup completed successfully!"
```

## Railway Features
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Auto-scaling
- ✅ Built-in PostgreSQL
- ✅ GitHub integration
- ✅ Zero-config deployment
- ✅ $5 free credits monthly

## Monitoring
- View logs in Railway dashboard
- Monitor resource usage
- Set up alerts for downtime

## Custom Domain (Optional)
1. In Railway dashboard → Settings → Domains
2. Add your custom domain
3. Update DNS records as shown
4. Railway handles SSL automatically

## Scaling
Railway automatically scales based on usage. For high traffic:
- Upgrade to Pro plan ($20/month)
- Increase memory/CPU limits
- Add multiple replicas