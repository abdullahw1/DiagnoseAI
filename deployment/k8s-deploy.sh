#!/bin/bash

# DiagnoseAI Kubernetes Deployment Script
set -e

# Configuration
REGISTRY="your-acr-name.azurecr.io"  # Replace with your Azure Container Registry
IMAGE_NAME="diagnoseai"
TAG="latest"
NAMESPACE="diagnoseai"

echo "🏥 DiagnoseAI Kubernetes Deployment"
echo "=================================="

# Step 1: Build and push Docker image
echo "📦 Building Docker image..."
docker build -t $REGISTRY/$IMAGE_NAME:$TAG .

echo "🚀 Pushing to Azure Container Registry..."
docker push $REGISTRY/$IMAGE_NAME:$TAG

# Step 2: Update deployment with new image
echo "🔄 Updating Kubernetes deployment files..."
sed -i "s|your-registry/diagnoseai:latest|$REGISTRY/$IMAGE_NAME:$TAG|g" k8s/deployment.yaml
sed -i "s|your-registry/diagnoseai:latest|$REGISTRY/$IMAGE_NAME:$TAG|g" k8s/db-migration-job.yaml

# Step 3: Apply Kubernetes manifests
echo "🎯 Applying Kubernetes manifests..."

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Apply configuration
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy PostgreSQL
kubectl apply -f k8s/postgresql.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s

# Run database migration
kubectl apply -f k8s/db-migration-job.yaml
kubectl wait --for=condition=complete job/diagnoseai-db-migration -n $NAMESPACE --timeout=300s

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for application to be ready..."
kubectl wait --for=condition=available deployment/diagnoseai-app -n $NAMESPACE --timeout=300s

echo "✅ Deployment complete!"
echo ""
echo "📋 Useful commands:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl logs -f deployment/diagnoseai-app -n $NAMESPACE"
echo "  kubectl get ingress -n $NAMESPACE"
echo ""
echo "🌐 Your application should be available at: https://diagnoseai.yourdomain.com"