# variousplug[vp] - A plug to various docker hosts.

**[日本語版 README](README_ja.md) | [English README](README.md)**

`vp` is a command-line interface (CLI) tool originally based on [fireplug](https://github.com/koheiw/fireplug), but restructured and repurposed to support [vast.ai](https://vast.ai) and [runPod](https://www.runpod.io/).

## Features

- 🚀 **Remote Execution** - Run code on vast.ai and RunPod GPU instances
- 🔄 **BSRS Workflow** - Build, Sync, Run, Sync automation
- 🐳 **Docker Integration** - Automatic Docker image building
- 📁 **File Synchronization** - Native SDK sync for vast.ai, rsync for RunPod
- ⚙️ **Easy Configuration** - Interactive setup and YAML config
- 🎯 **Platform Agnostic** - Support for multiple cloud platforms
- 🧪 **Comprehensive Testing** - Full test suite with CI/CD
- 🔧 **Modern Tooling** - Ruff linting, GitHub Actions, Python 3.11+

## Installation

```bash
uv tool install git+https://github.com/takeru1205/variousplug.git
```

## Quick Start

### 1. Initialize Configuration
```bash
# Initialize project configuration
vp --init

# Or for development
uv run vp --init
```

### 2. Set API Keys
```bash
# Configure your platform API keys
vp config-set --vast-api-key YOUR_VAST_API_KEY
vp config-set --runpod-api-key YOUR_RUNPOD_API_KEY
vp config-set --default-platform vast
```

### 3. Run Commands on Remote Hosts
```bash
# Run Python script on remote GPU
vp run -- python train_model.py

# Run with specific platform
vp run --platform vast -- python script.py

# Run with specific instance
vp run --instance-id 12345 -- python script.py
```

## Usage Examples

### Basic Workflow
```bash
# Create a project directory
mkdir my-ml-project && cd my-ml-project

# Initialize VariousPlug
vp --init

# Write your code
echo "print('Hello from remote GPU!')" > hello.py

# Run on remote Docker host
vp run -- python hello.py
```

### Advanced Usage
```bash
# List available instances
vp list-instances

# Create new instance
vp create-instance --platform vast --gpu-type RTX3090

# Sync files only (no execution)
vp run --sync-only -- python script.py

# Run without sync (use existing files)
vp run --no-sync -- python script.py

# Custom Dockerfile
vp run --dockerfile custom.Dockerfile -- python script.py

# Destroy instance when done
vp destroy-instance INSTANCE_ID
```

### Configuration Management
```bash
# Show current configuration
vp config-show

# Set configuration values
vp config-set --vast-api-key YOUR_KEY
vp config-set --runpod-api-key YOUR_KEY
vp config-set --default-platform runpod
```

## Platform-Specific Examples

### Vast.ai (Simplified Setup)
```bash
# 1. Configure (requires only API key)
vp config-set --vast-api-key YOUR_KEY
vp config-set --default-platform vast

# 2. Run immediately (no SSH setup needed)
vp run -- python train.py

# 3. Files sync automatically via SDK
```

### RunPod (Full Setup)
```bash
# 1. Configure
vp config-set --runpod-api-key YOUR_KEY
vp config-set --default-platform runpod

# 2. Set up SSH keys and install rsync
vp create-instance --platform runpod --gpu-type RTX4000
vp run --no-sync -- "apt update && apt install -y rsync"

# 3. Run with rsync-based sync
vp run -- python train.py
```

## Implementation Summary

VariousPlug has been completely reimplemented with modern Python tooling and enhanced functionality:

### ✅ **Core Features Implemented**
- **Full CLI Interface** - Complete command-line interface with `vp` command
- **BSRS Workflow** - Build-Sync-Run-Sync automation fully working
- **Platform Integration** - Both vast.ai and RunPod support implemented
- **Configuration Management** - YAML-based config with interactive setup
- **Docker Integration** - Automatic Docker image building and management
- **File Synchronization** - Native SDK sync for vast.ai, rsync for RunPod
- **Error Handling** - Comprehensive error handling with rich output
- **Instance Management** - Create, list, and destroy instances

### 🏗️ **Architecture**
- **`cli.py`** - Click-based command interface
- **`config.py`** - YAML configuration management
- **`executor.py`** - Core BSRS workflow implementation
- **`vast_client.py`** - Vast.ai SDK integration
- **`runpod_client.py`** - RunPod SDK integration
- **`utils.py`** - Utility functions and rich output

### 🔧 **Dependencies**
- **Click** - CLI framework
- **PyYAML** - Configuration management
- **Docker SDK** - Docker image building
- **Vast.ai SDK** - Vast.ai platform integration with native file sync
- **RunPod SDK** - RunPod platform integration
- **Rich** - Enhanced terminal output
- **Ruff** - Modern Python linting and formatting

### 📊 **Testing Status**
- ✅ CLI interface fully functional
- ✅ Configuration system working
- ✅ Docker build process tested
- ✅ BSRS workflow validated
- ✅ File sync tested (vast.ai SDK + RunPod rsync)
- ✅ Error handling comprehensive
- ✅ Unit tests with 125+ passing tests
- ✅ CI/CD with GitHub Actions

## BSRS Workflow

VariousPlug uses the sequence of following steps: **Build-Sync-Run-Sync**.

1. **🔨 Build** - Build Docker image from local Dockerfile
2. **📤 Sync** - Upload local files to remote instance
   - **vast.ai**: Native SDK `copy()` method (no SSH required)
   - **RunPod**: rsync over SSH
3. **🚀 Run** - Execute command in Docker container on remote GPU
4. **📥 Sync** - Download results back to local machine
   - **vast.ai**: Native SDK `copy()` method
   - **RunPod**: rsync over SSH

### Platform-Specific Sync Details

**Vast.ai**: Uses the native `vast_sdk.copy()` method for seamless file transfers without requiring SSH setup.

**RunPod**: Uses rsync over SSH which requires proper SSH key configuration on the pod instances.

## Documentation

- 📚 **[Platform Comparison](docs/platform-comparison.md)** - Compare Vast.ai vs RunPod (English)
- 📚 **[プラットフォーム比較](docs/platform-comparison-ja.md)** - Vast.ai vs RunPodの比較 (日本語)
- 🌟 **[Vast.ai Guide](docs/vast-ai-guide.md)** - Complete Vast.ai setup and usage
- 🚀 **[RunPod Guide](docs/runpod-guide.md)** - Complete RunPod setup and usage

## Development

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/takeru1205/variousplug.git
cd variousplug

# Install dependencies with uv
uv sync

# Run tests
uv run pytest

# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Run the CLI in development mode
uv run vp --help
```

### Project Structure
```
src/variousplug/
├── cli.py              # Main CLI interface
├── config.py           # Configuration management
├── executor.py         # BSRS workflow execution
├── factory.py          # Platform factory pattern
├── interfaces.py       # Abstract interfaces
├── vast_client.py      # Vast.ai SDK integration
├── runpod_client.py    # RunPod SDK integration
├── base.py             # Base implementations
└── utils.py            # Utility functions

tests/
├── unit/               # Unit tests
├── conftest.py         # Test configuration
└── pytest.ini         # Test settings

.github/workflows/      # CI/CD pipelines
docs/                   # Documentation
```

### CI/CD Pipeline
- **GitHub Actions** for automated testing
- **Python 3.11, 3.12, 3.13** support
- **Multi-platform testing** (Linux, macOS, Windows)
- **Ruff linting and formatting**
- **Security scanning** with bandit and safety
