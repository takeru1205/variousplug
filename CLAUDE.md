# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VariousPlug (`vp`) is a command-line tool for running code on remote Docker hosts, specifically targeting vast.ai and RunPod platforms. It's restructured from the original fireplug project and implements a Build-Sync-Run-Sync (BSRS) workflow.

## Commands

### Installation
```bash
uv tool install git+https://github.com/takeru1205/variousplug.git
```

### Development Commands
```bash
# Run the CLI tool directly with uv
uv run vp --help

# Initialize configuration
uv run vp --init

# Show current configuration
uv run vp config-show

# Set API keys
uv run vp config-set --vast-api-key YOUR_KEY
uv run vp config-set --runpod-api-key YOUR_KEY

# List instances
uv run vp list-instances
uv run vp ls  # Alias

# Simplified direct execution (NEW!)
uv run vp python script.py
uv run vp "cd /workspace && python train.py"
uv run vp python --version

# Traditional run command syntax
uv run vp run -- python script.py
uv run vp --platform vast run -- python --version
uv run vp --sync-only run -- python script.py
uv run vp --no-sync run -- python --version

# Instance management  
uv run vp create-instance --platform vast --gpu-type RTX3090
uv run vp destroy-instance INSTANCE_ID
```

### Testing Commands
```bash
# Build only (test Docker build)
uv run vp --sync-only run -- echo "test"

# Skip sync (test command execution only)
uv run vp --no-sync run -- python --version
```

## Architecture

### Core Workflow: Sync-Run-Sync (SRS)
1. **Sync**: Transfer local files to remote host using `rsync` over SSH
2. **Run**: Execute commands directly on pre-configured cloud instances
3. **Sync**: Retrieve complete workspace back to local machine (including generated models, results, etc.)

*Note: Docker build is optional and disabled by default since cloud instances come with pre-configured environments (PyTorch, CUDA, etc.). Use `--enable-docker` flag if containerization is needed.*

### Key Components
- **Remote Host Integration**: Supports vast.ai and RunPod cloud platforms with reliable rsync-based sync
- **Direct Execution**: Commands run directly on cloud instances (Docker optional)
- **Bidirectional File Sync**: Complete workspace synchronization using rsync over SSH with .vpignore support
- **Auto-Instance Selection**: Automatically selects running instances when none specified
- **Simplified CLI**: Direct command execution without explicit "run" subcommand
- **Working Directory Fix**: Commands execute in `/workspace` where files are synced
- **Complete Workspace Download**: All generated files (models, results, etc.) are synced back automatically

### Platform SDKs
The project includes documentation for integrating with:
- **RunPod Python SDK**: Endpoint management, template creation, GPU allocation
- **Vast.ai Python SDK**: Instance management, SSH keys, file operations

## Project Structure
- `src/variousplug/`: Main package directory
- `pyproject.toml`: Python project configuration with hatchling build system
- Entry point: `variousplug:main` function

## Usage Pattern
Users create project directories, write code locally, then execute on remote Docker hosts using the `vp` command. The tool supports both simplified direct execution (`vp python script.py`) and traditional explicit syntax (`vp run -- python script.py`).

### File Sync Optimization
Create a `.vpignore` file to exclude unnecessary files from sync:
```
.venv/
__pycache__/
*.pyc
.git/
node_modules/
```

### Working Directory
Files are synced to `/workspace` on remote instances. Commands automatically execute in `/workspace` directory where files are located.

### Platform Compatibility
Both vast.ai and RunPod now use the same reliable rsync-based file synchronization:
- **Upload**: Excludes patterns from .vpignore file
- **Download**: Retrieves complete workspace including all generated files
- **SSH-based**: Uses SSH for reliable file transfer on both platforms

### Common Issues and Solutions
- **GPU Types**: For RunPod, omit `--gpu-type` to auto-select available GPU, or check RunPod documentation for valid identifiers
- **Platform Specification**: Always specify `--platform vast` or `--platform runpod` when destroying instances
- **SSH Connectivity**: Both platforms require SSH keys to be properly configured in platform account settings