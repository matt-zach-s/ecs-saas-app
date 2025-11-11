# Deploying to Customer AWS Accounts with Nuon

This guide explains how to deploy your Thanksgiving Meal Planner app into customer AWS accounts using Nuon's BYOC (Bring Your Own Cloud) platform.

## What is Nuon?

Nuon is a platform that enables you to deploy your SaaS application directly into your customers' AWS accounts. This gives customers:
- **Data sovereignty** - Their data stays in their AWS account
- **Security control** - They manage their own infrastructure
- **Compliance** - Easier to meet regulatory requirements
- **Cost transparency** - They pay AWS directly

## Architecture Overview

```
Your GitHub Repo
       │
       ├─ Dockerfile         → Builds Flask app container
       ├─ terraform/         → Provisions ECS infrastructure
       └─ components/        → Nuon configuration
              │
              ├─ app.toml              (Docker component)
              └─ infrastructure.toml   (Terraform component)

                    ↓

            Nuon Platform
                    │
                    ├─ Builds Docker image
                    ├─ Stores in customer's ECR
                    └─ Deploys via Terraform

                    ↓

         Customer AWS Account
                    │
                    ├─ VPC & Networking
                    ├─ Application Load Balancer
                    ├─ ECS Fargate Cluster
                    └─ Running Containers (Your App!)
```

## Project Structure

Your app is now configured for Nuon with these files:

```
ecs-saas-app/
├── metadata.toml              # App metadata (name, description)
├── components/                # Nuon component configurations
│   ├── app.toml              # Docker component (builds Flask app)
│   └── infrastructure.toml   # Terraform component (ECS infrastructure)
├── Dockerfile                 # Container definition
├── terraform/                 # ECS infrastructure code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── app/                       # Your Flask application
    ├── app.py
    ├── models.py
    └── static/
```

## Component Breakdown

### 1. Docker Component (`components/app.toml`)

This component builds your Flask application into a container:

```toml
name = "thanksgiving-app"
type = "dockerfile"

[connected_repo]
repo      = "matt-zach-s/ecs-saas-app"
directory = "."
branch    = "main"

dockerfile_path = "Dockerfile"

[[env]]
name  = "ENVIRONMENT"
value = "production"

[[env]]
name  = "PORT"
value = "5000"
```

**What it does**:
- Clones your GitHub repo
- Runs `docker build` using your Dockerfile
- Pushes the image to the customer's ECR registry
- Outputs the image URL for other components to use

### 2. Terraform Component (`components/infrastructure.toml`)

This component provisions AWS ECS infrastructure:

```toml
name         = "ecs-infrastructure"
type         = "terraform_module"
dependencies = ["thanksgiving-app"]

[connected_repo]
repo      = "matt-zach-s/ecs-saas-app"
directory = "terraform"
branch    = "main"

[[var]]
name  = "container_image_url"
value = "{{.nuon.components.thanksgiving-app.image_url}}"
```

**What it does**:
- Waits for the Docker component to complete (via `dependencies`)
- Runs your Terraform code in `terraform/` directory
- Passes the Docker image URL from the previous component
- Creates VPC, ALB, ECS cluster, and running tasks

**Key Features**:
- `dependencies = ["thanksgiving-app"]` ensures Docker builds first
- `{{.nuon.components.thanksgiving-app.image_url}}` references the Docker image URL
- All Terraform variables can be configured per-customer

### 3. Metadata File (`metadata.toml`)

Describes your app in the Nuon dashboard:

```toml
display_name = "Thanksgiving Meal Planner"
description  = "A full-stack SaaS application for planning and executing Thanksgiving meals."
readme       = "./README.md"
```

## Prerequisites

1. **Nuon Account**
   - Sign up at https://nuon.co
   - Install the Nuon CLI: https://docs.nuon.co

2. **GitHub Repository**
   - Your code must be in a GitHub repo (✅ you have this)
   - Nuon needs access to your repo

3. **AWS Account** (for each customer)
   - Customers need an AWS account
   - They'll provide Nuon with IAM credentials

## Deployment Steps

### Step 1: Install Nuon CLI

```bash
# macOS
brew install nuonco/nuon/nuon

# Or download from https://docs.nuon.co/reference/cli
```

### Step 2: Authenticate with Nuon

```bash
nuon login
```

### Step 3: Create Your App in Nuon

```bash
# From your project directory
cd ecs-saas-app

# Create the app
nuon apps create --name thanksgiving-meal-planner

# Sync your configuration
nuon apps sync
```

This will:
- Upload your component configurations
- Validate the .toml files
- Start building the Docker component

### Step 4: Create a Sandbox Install (Test Deployment)

Before deploying to customer accounts, test in your own AWS account:

```bash
# Create a sandbox install
nuon installs create-sandbox \
  --app-name thanksgiving-meal-planner \
  --sandbox-name test-install

# Monitor the installation
nuon installs status --install-id <install-id>
```

### Step 5: Deploy to Customer Account

Once tested, create production installs:

```bash
# Customer provides their AWS credentials to Nuon
# Then you can create an install in their account

nuon installs create \
  --app-name thanksgiving-meal-planner \
  --customer-name "Customer Corp" \
  --region us-east-1
```

## Component Dependencies

The components are deployed in order based on dependencies:

```
1. thanksgiving-app (Docker)
   └─ Builds Flask container
   └─ Pushes to customer's ECR
   └─ Outputs: image_url

2. ecs-infrastructure (Terraform)
   └─ Uses image_url from thanksgiving-app
   └─ Creates VPC, ALB, ECS cluster
   └─ Deploys containers
   └─ Outputs: alb_dns_name
```

## Customization Per Customer

You can customize deployments per customer by adding inputs. For example, to let customers choose instance sizes:

Create `inputs.toml`:

```toml
[[input]]
name        = "instance_size"
type        = "string"
default     = "small"
description = "Application instance size"

[[input.choices]]
value = "small"
[[input.choices]]
value = "large"
```

Then reference in `components/infrastructure.toml`:

```toml
[[var]]
name  = "task_cpu"
value = "{{.inputs.instance_size == 'large' ? '512' : '256'}}"
```

## Monitoring & Updates

### View Install Status

```bash
# List all installs
nuon installs list

# Get details of a specific install
nuon installs get --install-id <install-id>

# View logs
nuon installs logs --install-id <install-id>
```

### Update the Application

When you make changes:

1. Commit and push to GitHub
2. Run `nuon apps sync` to upload new config
3. Create a new release: `nuon apps releases create`
4. Update installs: `nuon installs update --install-id <install-id>`

## Infrastructure Costs (Per Customer)

Each customer will incur these AWS costs:

| Resource | Monthly Cost |
|----------|-------------|
| Application Load Balancer | ~$16 |
| ECS Fargate (2 tasks, 0.25 vCPU, 512 MB) | ~$30-60 |
| Data Transfer | Variable |
| CloudWatch Logs | ~$5 |
| **Total Estimate** | **$50-100/month** |

Customers pay these costs directly to AWS in their own account.

## Troubleshooting

### Build Failures

```bash
# Check component build status
nuon components builds list --component-name thanksgiving-app

# View build logs
nuon components builds logs --build-id <build-id>
```

Common issues:
- **Docker build fails**: Check Dockerfile syntax, ensure all COPY paths are correct
- **Terraform fails**: Validate terraform code locally first with `terraform validate`
- **Image not found**: Ensure Docker component completed before Terraform runs

### Install Failures

```bash
# Get detailed install status
nuon installs status --install-id <install-id>

# View Terraform outputs
nuon installs outputs --install-id <install-id>
```

### Accessing the Application

After successful deployment:

```bash
# Get the ALB URL
nuon installs outputs --install-id <install-id> | grep alb_dns_name
```

Visit the ALB DNS name in your browser to access the app.

## Security Considerations

1. **Secrets Management**
   - Use AWS Secrets Manager for sensitive values
   - Don't hardcode credentials in .toml files
   - Reference secrets in Terraform using data sources

2. **IAM Permissions**
   - Nuon needs limited IAM permissions in customer accounts
   - Customer retains full control over their infrastructure
   - Review IAM policies before granting access

3. **Network Security**
   - The Terraform creates security groups with minimal access
   - ALB is public, but ECS tasks are in private subnets
   - Consider adding WAF for additional protection

## Next Steps

1. **Test locally**: Run `docker build` and `terraform plan` to validate
2. **Create Nuon account**: Sign up at https://nuon.co
3. **Sync your app**: Run `nuon apps sync`
4. **Create sandbox install**: Test in your AWS account first
5. **Deploy to customers**: Create production installs

## Resources

- **Nuon Documentation**: https://docs.nuon.co
- **Nuon CLI Reference**: https://docs.nuon.co/reference/cli
- **Your App Architecture**: See ARCHITECTURE.md
- **Terraform Docs**: See DEPLOYMENT.md

## Support

For issues with:
- **Your application**: Check logs with `nuon installs logs`
- **Nuon platform**: Contact support@nuon.co
- **AWS infrastructure**: Check AWS Console in customer account
