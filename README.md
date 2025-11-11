# ECS SaaS Application

A sample AWS ECS application with modern SaaS infrastructure components including containerization, Infrastructure as Code, and Kubernetes support.

## Project Structure

```
ecs-saas-app/
├── app/                    # Flask application code
│   ├── app.py             # Main application file
│   └── requirements.txt   # Python dependencies
├── terraform/             # Terraform configuration for AWS ECS
│   ├── main.tf           # Main infrastructure definitions
│   ├── variables.tf      # Input variables
│   └── outputs.tf        # Output values
├── helm/                  # Helm chart for Kubernetes deployment
│   └── ecs-saas-app/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── Dockerfile            # Container image definition
├── docker-compose.yml    # Local development setup
└── README.md            # This file
```

## Components

### 1. Flask Application
A simple Python Flask web application with:
- Hello World endpoint at `/`
- Health check endpoint at `/health`
- JSON responses with hostname and environment info

### 2. Docker
- **Dockerfile**: Multi-stage build for production-ready container
- **docker-compose.yml**: Easy local development environment

### 3. Terraform for AWS ECS
Complete infrastructure as code including:
- VPC with public subnets across multiple AZs
- Application Load Balancer (ALB)
- ECS Fargate cluster and service
- Security groups and IAM roles
- CloudWatch logging

### 4. Helm Chart
Kubernetes deployment package with:
- Deployment, Service, and ServiceAccount manifests
- Configurable resources and autoscaling
- Health checks and probes

## Quick Start

### Local Development

#### Option 1: Run with Docker Compose (Recommended)
```bash
# Build and start the application
docker-compose up --build

# Access the application at http://localhost:5000
```

#### Option 2: Run with Python directly
```bash
# Install dependencies
cd app
pip install -r requirements.txt

# Run the application
python app.py

# Access the application at http://localhost:5000
```

#### Option 3: Run with Docker
```bash
# Build the image
docker build -t ecs-saas-app:latest .

# Run the container
docker run -p 5000:5000 -e ENVIRONMENT=development ecs-saas-app:latest

# Access the application at http://localhost:5000
```

### Test the Application
```bash
# Home endpoint
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health
```

## Deploying to AWS ECS

### Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured
- Terraform installed
- Docker for building images

### Steps

#### 1. Build and Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name ecs-saas-app --region us-east-1

# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build the image
docker build -t ecs-saas-app:latest .

# Tag the image
docker tag ecs-saas-app:latest $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ecs-saas-app:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ecs-saas-app:latest
```

#### 2. Deploy with Terraform

```bash
cd terraform

# Initialize Terraform
terraform init

# Update variables (create terraform.tfvars)
cat > terraform.tfvars <<EOF
aws_region         = "us-east-1"
app_name          = "ecs-saas-app"
environment       = "production"
ecr_repository_url = "$AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/ecs-saas-app"
image_tag         = "latest"
desired_count     = 2
EOF

# Preview changes
terraform plan

# Apply configuration
terraform apply

# Get the ALB DNS name
terraform output alb_dns_name
```

#### 3. Access Your Application

After deployment completes (may take 5-10 minutes):
```bash
# Get the load balancer URL
ALB_URL=$(terraform output -raw alb_dns_name)

# Test the application
curl http://$ALB_URL/
```

## Deploying to Kubernetes (EKS or other)

### Prerequisites
- Kubernetes cluster (EKS, GKE, or local like minikube)
- kubectl configured
- Helm 3 installed
- Docker image pushed to a registry

### Steps

```bash
# Update values.yaml with your image repository
vim helm/ecs-saas-app/values.yaml

# Install the Helm chart
helm install my-saas-app helm/ecs-saas-app

# Check deployment status
kubectl get pods
kubectl get services

# Get the service URL (for LoadBalancer type)
kubectl get service my-saas-app-ecs-saas-app
```

## Configuration

### Environment Variables
- `ENVIRONMENT`: Deployment environment (development/staging/production)
- `PORT`: Port number the application listens on (default: 5000)

### Terraform Variables
See `terraform/variables.tf` for all configurable options:
- `aws_region`: AWS region for deployment
- `task_cpu`: CPU units for ECS task
- `task_memory`: Memory allocation for ECS task
- `desired_count`: Number of running tasks

### Helm Values
See `helm/ecs-saas-app/values.yaml` for all configuration options:
- `replicaCount`: Number of pod replicas
- `resources`: CPU and memory limits
- `autoscaling`: Horizontal Pod Autoscaler settings

## Cleanup

### Docker Compose
```bash
docker-compose down
```

### AWS ECS (Terraform)
```bash
cd terraform
terraform destroy
```

### Kubernetes (Helm)
```bash
helm uninstall my-saas-app
```

## Development

### Adding New Endpoints
Edit `app/app.py` to add new routes:
```python
@app.route('/new-endpoint')
def new_endpoint():
    return jsonify({'message': 'New endpoint'})
```

### Updating Dependencies
```bash
# Update requirements.txt
echo "new-package==1.0.0" >> app/requirements.txt

# Rebuild the container
docker-compose up --build
```

## Architecture

### AWS ECS Architecture
```
Internet → ALB → ECS Tasks (Fargate) → CloudWatch Logs
           ↓
      Target Group
```

### Components:
- **VPC**: Isolated network with public subnets
- **ALB**: Distributes traffic across tasks
- **ECS Cluster**: Managed container orchestration
- **Fargate**: Serverless compute for containers
- **CloudWatch**: Centralized logging and monitoring

## Best Practices Included

1. **Security**:
   - Non-root container user
   - Security groups with least privilege
   - IAM roles for service authentication

2. **Reliability**:
   - Health checks on multiple levels
   - Multi-AZ deployment
   - Auto-recovery with ECS service scheduler

3. **Observability**:
   - CloudWatch logs integration
   - Container insights enabled
   - Health check endpoints

4. **Scalability**:
   - Horizontal scaling support (increase desired_count)
   - Load balancing across tasks
   - Kubernetes HPA support in Helm chart

## Troubleshooting

### Local Development
```bash
# View logs
docker-compose logs -f

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### AWS ECS
```bash
# Check service status
aws ecs describe-services --cluster ecs-saas-app-cluster --services ecs-saas-app-service

# View logs
aws logs tail /ecs/ecs-saas-app --follow

# List running tasks
aws ecs list-tasks --cluster ecs-saas-app-cluster
```

### Kubernetes
```bash
# Check pod logs
kubectl logs -l app.kubernetes.io/name=ecs-saas-app

# Describe pod for events
kubectl describe pod <pod-name>

# Port forward for local testing
kubectl port-forward service/my-saas-app-ecs-saas-app 5000:80
```

## Next Steps

1. Add a database (RDS for ECS, or StatefulSet for Kubernetes)
2. Implement authentication and authorization
3. Add CI/CD pipeline (GitHub Actions, GitLab CI, etc.)
4. Set up monitoring and alerting (CloudWatch, Prometheus, etc.)
5. Implement HTTPS with SSL/TLS certificates
6. Add caching layer (Redis, Elasticache)
7. Implement rate limiting and API versioning

## License

MIT License - feel free to use this as a starting point for your own projects!

## Contributing

This is a sample project, but feel free to submit issues or pull requests if you find bugs or have suggestions!
