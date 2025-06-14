# variousplug[vp] - A plug to various docker hosts.

**[日本語版 README](README_ja.md) | [English README](README.md)**

`vp` is a command-line interface (CLI) tool originally based on [fireplug](https://github.com/koheiw/fireplug), but restructured and repurposed to support [vast.ai](https://vast.ai) and [RunPod](https://runpod.io).

## Features

- 🚀 **Remote Execution** - Run code on vast.ai and RunPod GPU instances
- ⚡ **Simplified CLI** - Direct command execution: `vp python script.py`
- 🤖 **Auto-Instance Selection** - Automatically finds and uses running instances
- 🔄 **SRS Workflow** - Sync, Run, Sync automation with complete workspace download
- 🐳 **Docker Integration** - Optional Docker support (disabled by default)
- 📁 **File Synchronization** - Reliable rsync-based sync for both platforms with .vpignore support
- ⚙️ **Easy Configuration** - Interactive setup and YAML config
- 🎯 **Platform Agnostic** - Support for multiple cloud platforms
- 🧪 **Comprehensive Testing** - Full test suite with CI/CD
- 🔧 **Modern Tooling** - Ruff linting, GitHub Actions, Python 3.11+

## Getting Started

### 1. Create Platform Accounts

Before using VariousPlug, you'll need accounts on the platforms:

- **[Sign up for vast.ai](https://cloud.vast.ai/?ref_id=85456)** *(referral link)* - Cost-effective GPU instances with spot pricing
  - *Direct link: [vast.ai](https://vast.ai)*
- **[Sign up for RunPod](https://runpod.io?ref=jnz0wcmk)** *(referral link)* - Reliable GPU infrastructure with fixed pricing
  - *Direct link: [runpod.io](https://runpod.io)*

*Note: Using the referral links helps support the development of VariousPlug at no extra cost to you.*

### 2. Installation

```bash
uv tool install git+https://github.com/takeru1205/variousplug.git
```

### 3. Quick Start

#### Initialize Configuration
```bash
# Initialize project configuration
vp --init

# Or for development
uv run vp --init
```

#### Set API Keys
```bash
# Configure your platform API keys
vp config-set --vast-api-key YOUR_VAST_API_KEY
vp config-set --runpod-api-key YOUR_RUNPOD_API_KEY
vp config-set --default-platform vast
```

#### Run Commands on Remote Hosts
```bash
# Simplified direct execution (NEW!)
vp python train_model.py
vp "cd /workspace && python script.py"
vp python --version

# Traditional explicit syntax
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

# Run on remote Docker host (simplified syntax)
vp python hello.py
```

### Advanced Usage
```bash
# List available instances
vp list-instances
vp ls  # Alias

# Create new instance (auto-selects available GPU)
vp create-instance --platform vast
vp create-instance --platform runpod

# Sync files only (no execution)
vp run --sync-only -- python script.py

# Run without sync (use existing files)
vp run --no-sync -- python script.py

# Custom Dockerfile (Docker optional)
vp run --dockerfile custom.Dockerfile --enable-docker -- python script.py

# Enable Docker build step (disabled by default)
vp run --enable-docker -- python script.py

# Destroy instance when done (specify platform)
vp destroy-instance INSTANCE_ID --platform vast
vp destroy-instance INSTANCE_ID --platform runpod
```

### File Synchronization
Both platforms use reliable rsync-based synchronization:

**Upload**: Syncs your project files to `/workspace` on remote instance
**Download**: Retrieves complete workspace including all generated files (models, results, etc.)

Create a `.vpignore` file to exclude unnecessary files:
```bash
# .vpignore
.venv/
__pycache__/
*.pyc
.git/
node_modules/
```

**Note**: Generated files like `*.pth`, `*.pkl` are now automatically downloaded from the complete workspace.

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

### Vast.ai Setup
```bash
# 1. Configure API key
vp config-set --vast-api-key YOUR_KEY
vp config-set --default-platform vast

# 2. Add SSH key to vast.ai account (required for file sync)
# Go to https://cloud.vast.ai/account/ and add your SSH public key

# 3. Create instance and run
vp create-instance --platform vast
vp python train.py  # Files sync via rsync over SSH
```

### RunPod Setup
```bash
# 1. Configure API key
vp config-set --runpod-api-key YOUR_KEY
vp config-set --default-platform runpod

# 2. Create instance (auto-selects available GPU)
vp create-instance --platform runpod
vp run --no-sync -- "apt update && apt install -y rsync"

# 3. Run with rsync-based sync
vp run -- python train.py
```

## Implementation Summary

VariousPlug has been completely reimplemented with modern Python tooling and enhanced functionality:

### ✅ **Core Features Implemented**
- **Full CLI Interface** - Complete command-line interface with `vp` command and simplified syntax
- **SRS Workflow** - Sync-Run-Sync automation with complete workspace download
- **Platform Integration** - Both vast.ai and RunPod support with reliable rsync-based sync
- **Configuration Management** - YAML-based config with interactive setup
- **Docker Integration** - Optional Docker support (disabled by default)
- **File Synchronization** - Rsync-based sync for both platforms with .vpignore support
- **Auto-Instance Selection** - Automatically finds and uses running instances
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
- ✅ CLI interface fully functional with simplified syntax
- ✅ Configuration system working
- ✅ SRS workflow validated on both platforms
- ✅ File sync tested and fixed (rsync-based for both platforms)
- ✅ SSH connectivity issues resolved
- ✅ Complete workspace download working
- ✅ Error handling comprehensive
- ✅ Unit tests with 179 passing tests
- ✅ CI/CD with GitHub Actions

## Troubleshooting

### Common Issues

**SSH Key Setup**
- Add your SSH public key to platform account settings
- vast.ai: https://cloud.vast.ai/account/
- RunPod: Automatically configured via API

**GPU Type Errors**
```bash
# Don't specify GPU type - let it auto-select
vp create-instance --platform runpod  # ✅ Correct
vp create-instance --platform runpod --gpu-type RTX4000  # ❌ May fail
```

**Instance Destruction**
```bash
# Always specify platform when destroying
vp destroy-instance ID --platform vast    # ✅ Correct
vp destroy-instance ID --platform runpod  # ✅ Correct
vp destroy-instance ID                     # ❌ May use wrong platform
```

**File Sync Issues**
- Ensure SSH keys are properly configured
- Check `.vpignore` file excludes unnecessary files
- For RunPod: Install rsync if needed: `vp --no-sync run -- "apt update && apt install -y rsync"`

## SRS Workflow

VariousPlug uses the **Sync-Run-Sync** workflow (Docker optional):

1. **📤 Sync** - Upload local files to remote `/workspace` via rsync over SSH
2. **🚀 Run** - Execute commands directly on pre-configured instances 
3. **📥 Sync** - Download complete workspace including all generated files (models, results, etc.)

### Platform Reliability

Both **vast.ai** and **RunPod** now use the same reliable rsync-based file synchronization over SSH for consistent performance and complete workspace download.

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
