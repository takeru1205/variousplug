# VariousPlug RunPod Integration Guide

This guide explains how to use VariousPlug (`vp`) with RunPod GPU instances for running code on remote machines.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Instance Management](#instance-management)
- [Running Code](#running-code)
- [Cost Optimization](#cost-optimization)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. RunPod Account Setup

1. **Create Account**: Sign up at [RunPod.io](https://www.runpod.io/)
2. **Add Payment Method**: Add a credit card or payment method
3. **Get API Key**: 
   - Go to [RunPod Settings](https://www.runpod.io/console/user/settings)
   - Navigate to "API Keys" section
   - Create a new API key with appropriate permissions
   - Copy the API key (starts with `rpa_`)

### 2. System Requirements

- **Python 3.11+** installed
- **uv** package manager (recommended) or pip
- **Docker** (for building images)
- **SSH client** (for file synchronization - required for RunPod)

## Installation

### Using uv (Recommended)

```bash
# Install VariousPlug
uv tool install git+https://github.com/takeru1205/variousplug.git
```

### Using pip

```bash
# Install VariousPlug
pip install git+https://github.com/takeru1205/variousplug.git
```

## Configuration

### 1. Initialize VariousPlug

```bash
# Initialize configuration interactively
vp --init
```

Follow the prompts:
- **Project name**: Your project name (e.g., `my-ml-project`)
- **Vast.ai API key**: Leave blank or press Enter
- **RunPod API key**: Enter your RunPod API key (rpa_xxxxx)
- **Default platform**: Choose `runpod`
- **Data directory**: `data` (default)
- **Base Docker image**: `runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04`

### 2. Manual Configuration

Alternatively, configure manually:

```bash
# Set RunPod API key
vp config-set --runpod-api-key "rpa_your_api_key_here"

# Set RunPod as default platform
vp config-set --default-platform runpod

# Verify configuration
vp config-show
```

### 3. Configuration File

VariousPlug creates a `.vp/config.yaml` file:

```yaml
project:
  name: my-ml-project
  data_dir: data
  base_image: runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04
  working_dir: /workspace

platforms:
  default: runpod
  runpod:
    api_key: rpa_your_api_key_here
    enabled: true

docker:
  build_context: .
  dockerfile: Dockerfile
  build_args: {}

sync:
  exclude_patterns:
    - .git/
    - .vp/
    - __pycache__/
    - "*.pyc"
    - .DS_Store
    - node_modules/
    - .env
  include_patterns:
    - "*"
```

## Basic Usage

### 1. Check Configuration

```bash
# Show current configuration
vp config-show

# List available instances
vp list-instances
```

### 2. Create Your First Instance

```bash
# Create a cost-effective GPU instance
vp create-instance --platform runpod --gpu-type "NVIDIA GeForce RTX 3070"

# Create with specific image
vp create-instance --platform runpod \
  --gpu-type "NVIDIA RTX 4000 Ada Generation" \
  --image "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"
```

### 3. Run Your First Command

```bash
# Run a simple command (auto-selects instance)
vp run -- python --version

# Run with specific instance
vp run --instance-id your_instance_id -- python --version
```

## Instance Management

### Creating Instances

#### Cost-Effective GPU Options

```bash
# Recommended: RTX 3070 (good price/performance)
vp create-instance --platform runpod --gpu-type "NVIDIA GeForce RTX 3070"

# Budget option: RTX 4000 Ada Generation  
vp create-instance --platform runpod --gpu-type "NVIDIA RTX 4000 Ada Generation"

# If available: L4 (very cost-effective)
vp create-instance --platform runpod --gpu-type "NVIDIA L4"
```

#### Custom Images

```bash
# PyTorch with CUDA
vp create-instance --platform runpod \
  --gpu-type "NVIDIA GeForce RTX 3070" \
  --image "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"

# TensorFlow
vp create-instance --platform runpod \
  --gpu-type "NVIDIA GeForce RTX 3070" \
  --image "runpod/tensorflow:2.11.0-py3.10-cuda11.8.0-devel-ubuntu22.04"

# Basic Python
vp create-instance --platform runpod \
  --gpu-type "NVIDIA GeForce RTX 3070" \
  --image "python:3.11-slim"
```

### Listing Instances

```bash
# List all instances
vp list-instances

# List RunPod instances specifically
vp list-instances --platform runpod
```

### Destroying Instances

```bash
# Destroy specific instance
vp destroy-instance your_instance_id --platform runpod

# Auto-detect platform
vp destroy-instance your_instance_id
```

## Running Code

### 1. BSRS Workflow (Build-Sync-Run-Sync)

VariousPlug follows a **Build-Sync-Run-Sync** workflow:

1. **Build**: Creates Docker image from your Dockerfile
2. **Sync**: Uploads your code to the remote instance using rsync over SSH
3. **Run**: Executes your command in the container
4. **Sync**: Downloads results back to your local machine using rsync over SSH

#### File Synchronization with RunPod

VariousPlug uses **rsync over SSH** for RunPod file transfers, which requires:

- 🔑 **SSH key setup** - Must configure SSH keys on pod instances
- 📦 **rsync installation** - Remote pods need rsync installed
- 🔧 **Manual setup** - One-time SSH key configuration per pod
- 🏃 **Reliable transfers** - Battle-tested rsync technology

### 2. Basic Commands

```bash
# Complete workflow (recommended)
vp run -- python train.py

# Skip sync (if files already uploaded)
vp run --no-sync -- python train.py

# Sync only (upload files without running)
vp run --sync-only -- python train.py

# Specify instance
vp run --instance-id your_instance_id -- python train.py
```

### 3. Example Workflows

#### Machine Learning Training

```bash
# Create project structure
mkdir ml-project && cd ml-project
vp --init

# Create training script
cat > train.py << 'EOF'
import torch
import torch.nn as nn
import time

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
else:
    device = torch.device("cpu")
    print("Using CPU")

# Simple training simulation
model = nn.Linear(10, 1).to(device)
print("Training started...")
for epoch in range(10):
    time.sleep(1)  # Simulate training
    print(f"Epoch {epoch + 1}/10 completed")

print("Training completed!")

# Save results
with open("data/results.txt", "w") as f:
    f.write("Training completed successfully!\n")
    f.write(f"Device used: {device}\n")
EOF

# Create data directory
mkdir -p data

# Run training on RunPod
vp run -- python train.py
```

#### Data Processing

```bash
# Process data with specific GPU
vp run --gpu-type "NVIDIA GeForce RTX 3070" -- python process_data.py

# Run Jupyter notebook
vp run -- jupyter notebook --ip=0.0.0.0 --allow-root --no-browser
```

#### Custom Docker Environment

```bash
# Create custom Dockerfile
cat > Dockerfile << 'EOF'
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Install additional packages
RUN pip install transformers datasets wandb

# Set working directory
WORKDIR /workspace

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code
COPY . .

CMD ["python", "train.py"]
EOF

# Run with custom Dockerfile
vp run --dockerfile Dockerfile -- python train.py
```

## Cost Optimization

### 1. Choose Cost-Effective GPUs

```bash
# Most cost-effective options (in order)
vp create-instance --platform runpod --gpu-type "NVIDIA L4"                    # Best value
vp create-instance --platform runpod --gpu-type "NVIDIA GeForce RTX 3070"     # Good value  
vp create-instance --platform runpod --gpu-type "NVIDIA RTX 4000 Ada Generation"  # Moderate
```

### 2. Use Community Cloud

VariousPlug automatically uses `COMMUNITY` cloud for lower costs, but you can verify:

```bash
# Configuration automatically set for cost optimization:
# - cloud_type: "COMMUNITY" (cheaper than SECURE)
# - container_disk_in_gb: 15 (reduced from default 20GB)
# - volume_in_gb: 0 (no additional storage)
```

### 3. Instance Lifecycle Management

```bash
# Create instance only when needed
vp create-instance --platform runpod --gpu-type "NVIDIA GeForce RTX 3070"

# Run your workload
vp run -- python long_training.py

# Destroy immediately after use
vp destroy-instance your_instance_id
```

### 4. Optimize Docker Images

```bash
# Use smaller base images when possible
vp create-instance --platform runpod \
  --gpu-type "NVIDIA GeForce RTX 3070" \
  --image "python:3.11-slim"  # Smaller than PyTorch images

# Multi-stage builds in Dockerfile
cat > Dockerfile << 'EOF'
# Build stage
FROM python:3.11 AS builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
WORKDIR /workspace
COPY . .
EOF
```

## Troubleshooting

### Common Issues

#### 1. API Key Issues

```bash
# Error: "API key not configured"
# Solution: Set your RunPod API key
vp config-set --runpod-api-key "rpa_your_api_key_here"
```

#### 2. No Instances Available

```bash
# Error: "There are no longer any instances available"
# Solution: Try different GPU types or wait
vp create-instance --platform runpod --gpu-type "NVIDIA GeForce RTX 3070"
vp create-instance --platform runpod --gpu-type "NVIDIA RTX 4000 Ada Generation"
```

#### 3. SSH Connection Issues

```bash
# Error: "Permission denied (publickey,password)"
# This is expected - VariousPlug will fallback to simulation mode
# SSH setup requires additional configuration not covered in this guide
```

#### 4. Instance Not Running

```bash
# Check instance status
vp list-instances

# Wait for instance to be ready (can take 1-3 minutes)
# Status should show "running"
```

### Debug Mode

```bash
# Run with verbose output
vp --verbose run -- python script.py

# Check configuration
vp config-show
```

### Getting Help

```bash
# Show help
vp --help
vp run --help

# Show specific command help
vp create-instance --help
vp destroy-instance --help
```

## Best Practices

### 1. Project Organization

```
your-project/
├── .vp/                    # VariousPlug configuration
│   └── config.yaml
├── data/                   # Input/output data
├── src/                    # Source code
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── .vpignore              # Files to exclude from sync
└── README.md
```

### 2. Development Workflow

```bash
# 1. Initialize project
mkdir my-project && cd my-project
vp --init

# 2. Develop locally first
python train.py

# 3. Test on remote when ready
vp create-instance --platform runpod --gpu-type "NVIDIA GeForce RTX 3070"
vp run -- python train.py

# 4. Download results
# (automatically done by BSRS workflow)

# 5. Clean up
vp destroy-instance your_instance_id
```

### 3. Cost Management

1. **Always destroy instances** when finished
2. **Use cheaper GPU types** for development
3. **Monitor usage** in RunPod console
4. **Use sync-only mode** to test file uploads before running expensive jobs

### 4. Security

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Add `.vp/` to `.gitignore`**
4. **Regularly rotate API keys**

## Example: Complete ML Project

Here's a complete example of setting up and running a machine learning project:

```bash
# 1. Setup
mkdir gpu-training && cd gpu-training
vp --init  # Configure with RunPod API key

# 2. Create training script
cat > train.py << 'EOF'
import torch
import torch.nn as nn
import torch.optim as optim
import os

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Check GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Simple model
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
).to(device)

# Save model
torch.save(model.state_dict(), "data/model.pth")
print("Model saved to data/model.pth")
EOF

# 3. Create requirements
cat > requirements.txt << 'EOF'
torch>=2.0.0
numpy
matplotlib
EOF

# 4. Run on RunPod
vp create-instance --platform runpod --gpu-type "NVIDIA GeForce RTX 3070"
vp run -- python train.py

# 5. Check results
ls data/  # Should show model.pth

# 6. Cleanup
vp list-instances  # Get instance ID
vp destroy-instance your_instance_id
```

This guide covers the essential aspects of using VariousPlug with RunPod. For advanced usage and platform-specific features, refer to the main VariousPlug documentation.


Available GPU ids

```
AMD Instinct MI300X OAM
NVIDIA A100 80GB PCIe
NVIDIA A100-SXM4-80GB
NVIDIA A30
NVIDIA A40
NVIDIA B200
NVIDIA GeForce RTX 3070
NVIDIA GeForce RTX 3080
NVIDIA GeForce RTX 3080 Ti
NVIDIA GeForce RTX 3090
NVIDIA GeForce RTX 3090 Ti
NVIDIA GeForce RTX 4070 Ti
NVIDIA GeForce RTX 4080
NVIDIA GeForce RTX 4080 SUPER
NVIDIA GeForce RTX 4090
NVIDIA GeForce RTX 5080
NVIDIA GeForce RTX 5090
NVIDIA H100 80GB HBM3
NVIDIA H100 NVL
NVIDIA H100 PCIe
NVIDIA H200
NVIDIA L4
NVIDIA L40
NVIDIA L40S
NVIDIA RTX 2000 Ada Generation
NVIDIA RTX 4000 Ada Generation
NVIDIA RTX 5000 Ada Generation
NVIDIA RTX 6000 Ada Generation
NVIDIA RTX A2000
NVIDIA RTX A4000
NVIDIA RTX A4500
NVIDIA RTX A5000
NVIDIA RTX A6000
NVIDIA RTX PRO 6000 Blackwell Workstation Edition
Tesla V100-FHHL-16GB
Tesla V100-PCIE-16GB
Tesla V100-SXM2-16GB
Tesla V100-SXM2-32GB
```
