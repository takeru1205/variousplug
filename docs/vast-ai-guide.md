# VariousPlug Vast.ai Integration Guide

This guide explains how to use VariousPlug (`vp`) with Vast.ai GPU instances for running code on cost-effective remote machines.

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

### 1. Vast.ai Account Setup

1. **Create Account**: Sign up at [Vast.ai](https://vast.ai/)
2. **Add Payment Method**: Add a credit card or payment method
3. **Get API Key**: 
   - Go to [Vast.ai Account Settings](https://vast.ai/console/account/)
   - Navigate to "API Key" section
   - Copy your API key (starts with long alphanumeric string)

### 2. System Requirements

- **Python 3.11+** installed
- **uv** package manager (recommended) or pip
- **Docker** (for building images)
- **SSH client** (for manual access, optional - not required for file sync)

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
- **Vast.ai API key**: Enter your Vast.ai API key
- **RunPod API key**: Leave blank or press Enter
- **Default platform**: Choose `vast`
- **Data directory**: `data` (default)
- **Base Docker image**: `pytorch/pytorch` (default for Vast.ai)

### 2. Manual Configuration

Alternatively, configure manually:

```bash
# Set Vast.ai API key
vp config-set --vast-api-key "your_vast_api_key_here"

# Set Vast.ai as default platform
vp config-set --default-platform vast

# Verify configuration
vp config-show
```

### 3. Configuration File

VariousPlug creates a `.vp/config.yaml` file:

```yaml
project:
  name: my-ml-project
  data_dir: data
  base_image: pytorch/pytorch
  working_dir: /workspace

platforms:
  default: vast
  vast:
    api_key: your_vast_api_key_here
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

# List available instances (all platforms)
vp ls

# List only Vast.ai instances
vp ls --platform vast
```

### 2. Create Your First Instance

```bash
# Create a cost-effective GPU instance
vp create-instance --platform vast --gpu-type "GTX_1070"

# Create with specific image
vp create-instance --platform vast \
  --gpu-type "GTX_1080" \
  --image "pytorch/pytorch"
```

### 3. Run Your First Command

```bash
# Run a simple command (auto-selects instance)
vp run -- python --version

# Run with specific instance
vp --instance-id your_instance_id run -- python --version
```

## Instance Management

### Creating Instances

#### Cost-Effective GPU Options

```bash
# Ultra-budget: GTX 1070 (lowest cost)
vp create-instance --platform vast --gpu-type "GTX_1070"

# Budget: GTX 1080 (good price/performance)
vp create-instance --platform vast --gpu-type "GTX_1080"

# Mid-range: RTX 3070 (modern features)
vp create-instance --platform vast --gpu-type "RTX_3070"

# High-end: RTX 4090 (maximum performance)
vp create-instance --platform vast --gpu-type "RTX_4090"
```

#### Custom Images

```bash
# PyTorch with CUDA
vp create-instance --platform vast \
  --gpu-type "GTX_1080" \
  --image "pytorch/pytorch"

# TensorFlow
vp create-instance --platform vast \
  --gpu-type "GTX_1080" \
  --image "tensorflow/tensorflow:latest-gpu"

# Basic Python
vp create-instance --platform vast \
  --gpu-type "GTX_1070" \
  --image "python:3.11-slim"

# Custom image with specific tag
vp create-instance --platform vast \
  --gpu-type "GTX_1080" \
  --image "pytorch/pytorch:2.1.0-cuda11.8-devel"
```

### Listing Instances

```bash
# List all instances across platforms
vp ls

# List only Vast.ai instances
vp ls --platform vast
vp list-instances --platform vast

# Short form
vp ls -p vast
```

### Destroying Instances

```bash
# Destroy specific instance
vp destroy-instance your_instance_id --platform vast

# Auto-detect platform (works if instance ID is unique)
vp destroy-instance your_instance_id
```

## Running Code

### 1. BSRS Workflow (Build-Sync-Run-Sync)

VariousPlug follows a **Build-Sync-Run-Sync** workflow:

1. **Build**: Creates Docker image from your Dockerfile
2. **Sync**: Uploads your code to the remote instance using Vast.ai SDK
3. **Run**: Executes your command in the container
4. **Sync**: Downloads results back to your local machine using Vast.ai SDK

#### File Synchronization with Vast.ai

VariousPlug uses the **native Vast.ai SDK** for file transfers, which provides:

- ✅ **No SSH setup required** - Works with API key authentication only
- ✅ **Automatic file transfers** - Seamless upload/download
- ✅ **Reliable transfers** - Built-in error handling and retries
- ✅ **Cross-platform support** - Works on Windows, macOS, and Linux

### 2. Basic Commands

```bash
# Complete workflow (recommended)
vp run -- python train.py

# Skip sync (if files already uploaded)
vp --no-sync run -- python train.py

# Sync only (upload files without running)
vp --sync-only run -- python train.py

# Specify instance and platform
vp --platform vast --instance-id your_instance_id run -- python train.py
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
import os

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    device = torch.device("cuda")
    print(f"Using GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    device = torch.device("cpu")
    print("Using CPU")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

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
    if torch.cuda.is_available():
        f.write(f"GPU: {torch.cuda.get_device_name(0)}\n")
EOF

# Create data directory
mkdir -p data

# Run training on Vast.ai
vp run -- python train.py
```

#### Data Processing

```bash
# Process data with specific GPU
# Create instance with specific GPU first
vp create-instance --platform vast --gpu-type "GTX_1080"
vp run -- python process_data.py

# Run Jupyter notebook (if image supports it)
vp run -- jupyter notebook --ip=0.0.0.0 --allow-root --no-browser
```

#### Custom Docker Environment

```bash
# Create custom Dockerfile
cat > Dockerfile << 'EOF'
FROM pytorch/pytorch:latest

# Install additional packages
RUN pip install transformers datasets wandb scikit-learn

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
vp run --dockerfile Dockerfile --enable-docker -- python train.py
```

## Cost Optimization

### 1. Choose Cost-Effective GPUs

```bash
# Most cost-effective options (in order of price)
vp create-instance --platform vast --gpu-type "GTX_1070"     # Ultra budget
vp create-instance --platform vast --gpu-type "GTX_1080"     # Budget
vp create-instance --platform vast --gpu-type "GTX_1080_Ti"  # Good value
vp create-instance --platform vast --gpu-type "RTX_3070"     # Modern budget
```

### 2. Automatic Cost Optimizations

VariousPlug automatically applies cost optimizations for Vast.ai:

```bash
# Automatically configured cost settings:
# - price: Maximum $0.50/hour
# - disk_gb: 10GB (reduced from default)
# - direct_port_count: 1 (minimal network ports)
# - auto_destroy: True (auto-cleanup if connection lost)
# - use_jupyter_lab: False (reduced overhead)
```

### 3. Instance Lifecycle Management

```bash
# Create instance only when needed
vp create-instance --platform vast --gpu-type "GTX_1080"

# Check cost before starting
echo "Expected cost: ~$0.10-0.30/hour for GTX 1080"

# Run your workload
vp run -- python long_training.py

# Destroy immediately after use (IMPORTANT!)
vp destroy-instance your_instance_id
```

### 4. Monitor Usage

```bash
# Check running instances regularly
vp ls

# Verify instance destruction
vp ls --platform vast
```

### 5. Cost Comparison by GPU Type

| GPU Type | Typical Cost/Hour | Memory | Use Case |
|----------|------------------|---------|----------|
| GTX 1070 | $0.05 - $0.15 | 8GB | Testing, small models |
| GTX 1080 | $0.10 - $0.25 | 8GB | Development, medium models |
| GTX 1080 Ti | $0.15 - $0.30 | 11GB | Training, larger models |
| RTX 3070 | $0.20 - $0.40 | 8GB | Modern training, inference |
| RTX 4090 | $0.50 - $1.50 | 24GB | Large models, research |

## Troubleshooting

### Common Issues

#### 1. API Key Issues

```bash
# Error: "API key not configured"
# Solution: Set your Vast.ai API key
vp config-set --vast-api-key "your_vast_api_key_here"
```

#### 2. No Instances Available

```bash
# Error: "No instances available with the specified requirements"
# Solution: Try different GPU types
vp create-instance --platform vast --gpu-type "GTX_1080"
vp create-instance --platform vast --gpu-type "GTX_1070"
```

#### 3. SSH Connection Issues

```bash
# Info: SSH not required for Vast.ai
# VariousPlug uses native SDK for file transfers
# Commands execute normally on remote instances
```

#### 4. Instance Not Starting

```bash
# Check instance status
vp ls --platform vast

# Wait for instance to be ready (startup time: 1-5 minutes)
# Status will show "running" when ready
```

#### 5. High Costs

```bash
# Always destroy instances when done
vp destroy-instance your_instance_id

# Check for running instances regularly
vp ls

# Monitor costs in Vast.ai dashboard
# URL: https://vast.ai/console/instance/
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
vp ls --help
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
vp create-instance --platform vast --gpu-type "GTX_1080"
vp run -- python train.py

# 4. Download results (if SSH configured)
# (automatically done by BSRS workflow)

# 5. Clean up (CRITICAL!)
vp destroy-instance your_instance_id
```

### 3. Cost Management

1. **Always destroy instances** when finished - this is critical!
2. **Use cheaper GPU types** for development and testing
3. **Monitor usage** in Vast.ai console regularly
4. **Set price limits** for cost control
5. **Use `vp ls`** frequently to check for running instances

### 4. Security

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Add `.vp/` to `.gitignore`**
4. **Regularly rotate API keys**

### 5. Performance Tips

1. **Choose appropriate GPU** for your workload
2. **Use smaller Docker images** when possible
3. **Optimize data loading** for remote execution
4. **Test locally first** before running on remote

## Example: Complete ML Project

Here's a complete example of setting up and running a machine learning project:

```bash
# 1. Setup
mkdir gpu-training && cd gpu-training
vp --init  # Configure with Vast.ai API key

# 2. Create training script
cat > train.py << 'EOF'
import torch
import torch.nn as nn
import torch.optim as optim
import os
import time

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Check GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")

# Simple model
model = nn.Sequential(
    nn.Linear(784, 128),
    nn.ReLU(),
    nn.Linear(128, 10)
).to(device)

optimizer = optim.Adam(model.parameters())

# Simulate training
print("Starting training...")
for epoch in range(5):
    # Simulate batch processing
    fake_data = torch.randn(32, 784).to(device)
    fake_labels = torch.randint(0, 10, (32,)).to(device)
    
    optimizer.zero_grad()
    outputs = model(fake_data)
    loss = nn.CrossEntropyLoss()(outputs, fake_labels)
    loss.backward()
    optimizer.step()
    
    print(f"Epoch {epoch + 1}/5, Loss: {loss.item():.4f}")
    time.sleep(1)

# Save model
torch.save(model.state_dict(), "data/model.pth")
print("Model saved to data/model.pth")

# Save training log
with open("data/training_log.txt", "w") as f:
    f.write("Training completed successfully!\n")
    f.write(f"Device: {device}\n")
    if torch.cuda.is_available():
        f.write(f"GPU: {torch.cuda.get_device_name(0)}\n")
    f.write("Model saved to data/model.pth\n")

print("Training completed!")
EOF

# 3. Create requirements
cat > requirements.txt << 'EOF'
torch>=2.0.0
torchvision
numpy
matplotlib
EOF

# 4. Run on Vast.ai
vp create-instance --platform vast --gpu-type "GTX_1080"

# Wait for instance to be ready
vp ls --platform vast

# Run training
vp run -- python train.py

# 5. Check results
ls data/  # Should show model.pth and training_log.txt

# 6. Cleanup (CRITICAL!)
vp ls --platform vast  # Get instance ID
vp destroy-instance your_instance_id
```

## Advanced Usage

### Custom Price Limits

You can override the default $0.50/hour price limit:

```bash
# Note: This requires modifying the CreateInstanceRequest
# Current implementation has $0.50/hour hard limit for safety
```

### SSH Setup (Optional)

**Note**: SSH setup is **not required** for file synchronization with VariousPlug, as it uses the native Vast.ai SDK for transfers.

SSH access can be useful for:
- Manual debugging and inspection
- Interactive development
- Custom file operations outside of VariousPlug

To set up SSH access:

1. Generate SSH key pair
2. Add public key to Vast.ai account
3. Connect manually with `ssh -p <port> root@<host>`

*Note: SSH setup is optional - VariousPlug uses the native Vast.ai SDK for file transfers.*

### Multiple Instances

```bash
# Create multiple instances for parallel processing
vp create-instance --platform vast --gpu-type "GTX_1080"
vp create-instance --platform vast --gpu-type "GTX_1080"

# List all instances
vp ls

# Run on specific instances
vp --instance-id instance1 run -- python task1.py
vp --instance-id instance2 run -- python task2.py

# Clean up all instances
vp destroy-instance instance1
vp destroy-instance instance2
```

This guide covers the essential aspects of using VariousPlug with Vast.ai. The platform offers excellent cost-effectiveness for GPU computing, making it ideal for development, training, and experimentation.

**Remember: Always destroy instances when finished to avoid unexpected charges!**