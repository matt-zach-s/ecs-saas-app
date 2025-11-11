# Deployment Technologies Explained

## Overview

Your app currently runs locally on your laptop. To make it accessible to others or run in production, you need deployment tools. You have three different deployment options set up:

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR APPLICATION                         │
│              (Flask + SQLite + HTML/CSS/JS)                 │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Can be deployed using:
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐       ┌──────────┐      ┌──────────┐
   │ DOCKER  │       │ TERRAFORM│      │   HELM   │
   │         │       │          │      │          │
   │ Package │       │ AWS ECS  │      │Kubernetes│
   │   App   │       │Deploy    │      │ Deploy   │
   └─────────┘       └──────────┘      └──────────┘
```

## 1. Docker (Containerization)

### What It Does
Docker packages your app into a "container" - a standardized unit that includes:
- Your Python code
- All dependencies (Flask, SQLAlchemy, etc.)
- The exact Python version
- System libraries

Think of it like a shipping container: it works the same way whether it's on a truck, ship, or train.

### Your Dockerfile Explained

```dockerfile
# Start with Python 3.11 (the "base image")
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy requirements file
COPY app/requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY app/ .

# Tell Docker the app listens on port 5000
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Command to run when container starts
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
```

### What This Means

**Layer by Layer**:
1. `FROM python:3.11-slim` - Start with a minimal Linux system that has Python 3.11
2. `WORKDIR /app` - Create and use `/app` as the working directory
3. `COPY app/requirements.txt .` - Copy just the requirements first (for caching)
4. `RUN pip install...` - Install dependencies
5. `COPY app/ .` - Copy all your application code
6. `EXPOSE 5000` - Document that the app uses port 5000
7. `CMD [...]` - Use Gunicorn (production web server) to run the app

**Why Gunicorn?**
- Flask's built-in server is for development only
- Gunicorn is production-ready and can handle multiple requests

### Why Use Docker?

**Problem**: "It works on my machine" syndrome
```
Your Laptop (works)          Server (broken)
- Python 3.14                - Python 3.8
- macOS                      - Linux
- Different libraries        - Missing dependencies
```

**Solution**: Docker ensures identical environment everywhere
```
Your Laptop → Docker Image → Any Server
All have EXACTLY the same environment
```

### Docker Commands

```bash
# Build an image from your Dockerfile
docker build -t thanksgiving-app:latest .

# Run the container locally
docker run -p 5000:5000 thanksgiving-app:latest

# See running containers
docker ps

# Stop a container
docker stop <container-id>
```

### Docker Compose

Your `docker-compose.yml` makes it even easier:

```yaml
services:
  web:
    build: .                    # Build from Dockerfile in current directory
    ports:
      - "5000:5000"            # Map port 5000 outside to 5000 inside
    environment:
      - ENVIRONMENT=development # Set environment variables
    volumes:
      - ./app:/app             # Mount local code for live editing
```

**Run with one command**:
```bash
docker-compose up
```

This is great for local development because the `volumes` line means changes to your code are reflected immediately without rebuilding.

## 2. Terraform (AWS ECS Infrastructure)

### What It Does
Terraform creates all the cloud infrastructure (servers, networks, databases) you need on AWS using code. It's "Infrastructure as Code" (IaC).

### What AWS ECS Is

**ECS** = Elastic Container Service - AWS's service for running Docker containers

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS CLOUD                            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                VPC (Your Private Network)           │   │
│  │                                                     │   │
│  │  ┌──────────────┐    ┌─────────────────────────┐   │   │
│  │  │              │    │   ECS Cluster           │   │   │
│  │  │   Internet   │    │   ┌──────┐  ┌──────┐   │   │   │
│  │  │   Gateway    │───▶│   │Task 1│  │Task 2│   │   │   │
│  │  │              │    │   │(App) │  │(App) │   │   │   │
│  │  └──────────────┘    │   └──────┘  └──────┘   │   │   │
│  │         ▲            └─────────────────────────┘   │   │
│  │         │                                          │   │
│  │  ┌──────┴────────┐                                 │   │
│  │  │ Load Balancer │◀──── Users access here          │   │
│  │  │     (ALB)     │                                 │   │
│  │  └───────────────┘                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Your Terraform Configuration

Your `terraform/` folder creates:

#### 1. **VPC & Networking** (`main.tf` lines 15-70)
```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  # Creates a private network in AWS
}
```
- **VPC** = Virtual Private Cloud (your own isolated network)
- **Subnets** = Smaller network segments in different availability zones
- **Internet Gateway** = Allows communication with the internet

#### 2. **Security Groups** (lines 72-120)
```hcl
resource "aws_security_group" "alb" {
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Allow HTTP from anywhere
  }
}
```
- Firewalls that control what traffic can reach your app
- ALB security group: Allows port 80 (HTTP) from internet
- ECS security group: Allows port 5000 only from ALB

#### 3. **Load Balancer** (lines 122-165)
```hcl
resource "aws_lb" "main" {
  name               = "ecs-saas-app-alb"
  load_balancer_type = "application"
  # Distributes traffic across multiple containers
}
```
- Spreads traffic across multiple instances of your app
- Performs health checks
- Automatically routes to healthy instances

#### 4. **ECS Cluster** (lines 167-179)
```hcl
resource "aws_ecs_cluster" "main" {
  name = "ecs-saas-app-cluster"
  # The cluster that manages your containers
}
```
- Logical grouping of tasks/services
- Manages container orchestration

#### 5. **Task Definition** (lines 215-250)
```hcl
resource "aws_ecs_task_definition" "app" {
  family                   = "ecs-saas-app"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"      # 0.25 vCPU
  memory                   = "512"      # 512 MB RAM

  container_definitions = jsonencode([{
    name  = "ecs-saas-app"
    image = "${var.ecr_repository_url}:latest"  # Your Docker image
    portMappings = [{
      containerPort = 5000
    }]
  }])
}
```
- Defines how to run your container
- Specifies CPU/memory requirements
- Points to your Docker image in ECR

#### 6. **ECS Service** (lines 252-280)
```hcl
resource "aws_ecs_service" "app" {
  name            = "ecs-saas-app-service"
  desired_count   = 2  # Run 2 copies of your app
  launch_type     = "FARGATE"
  # Ensures 2 containers are always running
}
```
- Maintains desired number of tasks (containers)
- Registers tasks with load balancer
- Auto-restarts failed tasks

### Variables (`variables.tf`)

```hcl
variable "aws_region" {
  default = "us-east-1"
}

variable "desired_count" {
  default = 2  # Number of containers to run
}
```

Makes your infrastructure configurable without editing main files.

### Outputs (`outputs.tf`)

```hcl
output "alb_dns_name" {
  value = aws_lb.main.dns_name
  # Shows you the URL to access your app
}
```

After `terraform apply`, you get useful information like your app's URL.

### Terraform Commands

```bash
# Initialize (download AWS provider)
terraform init

# Preview what will be created
terraform plan

# Create the infrastructure
terraform apply

# Get output values
terraform output alb_dns_name

# Destroy everything
terraform destroy
```

### Cost Warning

Running this Terraform will create AWS resources that **cost money**:
- ALB: ~$16/month
- Fargate tasks: ~$0.04/hour per task × 2 = ~$60/month
- Data transfer: Variable

**Estimate: ~$80-100/month**

## 3. Helm (Kubernetes Deployment)

### What It Does
Helm is the "package manager" for Kubernetes. It bundles all Kubernetes configuration files together so you can install/upgrade your app with one command.

### What Kubernetes Is

**Kubernetes** (K8s) = Container orchestration platform (similar to ECS but open-source and cloud-agnostic)

```
┌─────────────────────────────────────────────────────┐
│              Kubernetes Cluster                     │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │           Namespace                          │  │
│  │                                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │  │  │
│  │  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │  │  │
│  │  │ │ App  │ │  │ │ App  │ │  │ │ App  │ │  │  │
│  │  │ │ Container│  │ │ Container│  │ │ Container│  │  │
│  │  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  │  │
│  │        ▲             ▲             ▲        │  │
│  │        └─────────────┴─────────────┘        │  │
│  │                     │                       │  │
│  │            ┌────────┴────────┐              │  │
│  │            │    Service      │              │  │
│  │            │  (Load Balancer)│              │  │
│  │            └─────────────────┘              │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Your Helm Chart Structure

```
helm/ecs-saas-app/
├── Chart.yaml              # Metadata about your chart
├── values.yaml             # Default configuration values
└── templates/
    ├── deployment.yaml     # How to run your app
    ├── service.yaml        # How to expose your app
    ├── serviceaccount.yaml # Identity for your app
    └── _helpers.tpl        # Reusable template functions
```

### Chart.yaml

```yaml
name: ecs-saas-app
version: 0.1.0
description: A Helm chart for ECS SaaS Application
```

Metadata about your chart (like package.json for npm).

### values.yaml (Configuration)

```yaml
replicaCount: 2  # Run 2 copies of your app

image:
  repository: your-account.dkr.ecr.us-east-1.amazonaws.com/ecs-saas-app
  tag: "latest"

service:
  type: LoadBalancer  # Creates a cloud load balancer
  port: 80           # External port
  targetPort: 5000   # Port your app listens on

resources:
  limits:
    cpu: 500m        # Max 0.5 CPU cores
    memory: 512Mi    # Max 512 MB RAM
  requests:
    cpu: 250m        # Guaranteed 0.25 CPU
    memory: 256Mi    # Guaranteed 256 MB RAM

env:
  - name: ENVIRONMENT
    value: "production"
  - name: PORT
    value: "5000"
```

### templates/deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecs-saas-app
spec:
  replicas: {{ .Values.replicaCount }}  # Uses value from values.yaml
  template:
    spec:
      containers:
      - name: ecs-saas-app
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        ports:
        - containerPort: {{ .Values.service.targetPort }}
        env:
          {{- toYaml .Values.env | nindent 12 }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
```

**What it does**:
- Creates a Deployment (manages Pods)
- Runs specified number of replicas
- Uses values from `values.yaml`
- `{{ .Values.replicaCount }}` is replaced with actual value

### templates/service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: ecs-saas-app
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
  selector:
    app: ecs-saas-app  # Routes to pods with this label
```

**What it does**:
- Creates a Service (networking for pods)
- Type LoadBalancer = Gets a public IP/DNS
- Routes port 80 → port 5000 on containers

### Helm Commands

```bash
# Install your chart
helm install my-thanksgiving-app helm/ecs-saas-app

# Upgrade with new values
helm upgrade my-thanksgiving-app helm/ecs-saas-app \
  --set replicaCount=5

# See what's deployed
helm list

# Uninstall
helm uninstall my-thanksgiving-app

# Override values
helm install my-app helm/ecs-saas-app \
  --values custom-values.yaml
```

### Kubernetes vs ECS

| Feature | ECS | Kubernetes |
|---------|-----|------------|
| **Vendor** | AWS only | Any cloud or on-prem |
| **Complexity** | Simpler | More complex |
| **Flexibility** | Limited to AWS features | Highly flexible |
| **Learning Curve** | Easier | Steeper |
| **Ecosystem** | AWS-specific tools | Huge open-source ecosystem |
| **Cost** | Pay for Fargate/EC2 | Pay for nodes/managed service |

## When to Use Each

### Docker (Always)
- ✅ **Development**: Use `docker-compose up` for local testing
- ✅ **CI/CD**: Build images for deployment
- ✅ **Consistency**: Ensure same environment everywhere

### Terraform + ECS (Good for AWS-focused teams)
- ✅ Want to deploy on AWS
- ✅ Need managed infrastructure
- ✅ Don't want Kubernetes complexity
- ✅ AWS-specific features (RDS, S3 integration)
- ❌ Locked into AWS

### Helm + Kubernetes (Good for cloud flexibility)
- ✅ Want multi-cloud or on-prem options
- ✅ Need advanced orchestration features
- ✅ Large scale applications
- ✅ Already using Kubernetes
- ❌ Steeper learning curve
- ❌ More complex to manage

## Comparison Chart

```
                    Local Dev        AWS ECS         Kubernetes
                    ─────────        ───────         ──────────
Tool Used:          Docker Compose   Terraform       Helm
Complexity:         ⭐ Simple        ⭐⭐ Medium     ⭐⭐⭐ Complex
Cost:               Free             $80-100/month   Varies
Setup Time:         5 minutes        30 minutes      1-2 hours
Best For:           Development      AWS production  Enterprise/Multi-cloud
Lock-in:            None             AWS             None
Scalability:        1 machine        High            Very High
Learning Curve:     Easy             Medium          Steep
```

## Your Current Setup

Right now, you're using **Docker Compose** for local development:
- Fast iteration
- See changes immediately
- No cloud costs
- Perfect for development!

To deploy to production, you'd:

### Option 1: AWS ECS (Recommended for you)
1. Build Docker image
2. Push to Amazon ECR
3. Run `terraform apply`
4. Access via load balancer URL

### Option 2: Kubernetes (If you need flexibility)
1. Set up Kubernetes cluster (EKS, GKE, etc.)
2. Build and push Docker image
3. Run `helm install`
4. Access via service external IP

## Next Steps

Want to try deploying? I can help you:
1. Build a Docker image locally
2. Test it with Docker
3. (If desired) Deploy to AWS with Terraform
4. (If desired) Deploy to Kubernetes with Helm

Just let me know which path you want to explore!
