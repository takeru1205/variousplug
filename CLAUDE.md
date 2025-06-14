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

# Run commands on remote hosts
uv run vp run -- python script.py
uv run vp run --platform vast -- python --version
uv run vp run --sync-only -- python script.py
uv run vp run --no-sync -- python --version

# Instance management  
uv run vp create-instance --platform vast --gpu-type RTX3090
uv run vp destroy-instance INSTANCE_ID
```

### Testing Commands
```bash
# Build only (test Docker build)
uv run vp run --sync-only -- echo "test"

# Skip sync (test command execution only)
uv run vp run --no-sync -- python --version
```

## Architecture

### Core Workflow: Build-Sync-Run-Sync (BSRS)
1. **Build**: Create Docker images for the remote environment
2. **Sync**: Transfer local files to remote host using `rsync` or AWS S3
3. **Run**: Execute commands in Docker containers on remote hosts
4. **Sync**: Retrieve results back to local machine

### Key Components
- **Remote Host Integration**: Supports vast.ai and RunPod cloud platforms
- **Docker Context Management**: Works with multiple remote Docker hosts
- **File Synchronization**: Handles bidirectional file sync between local and remote
- **Cloud Storage Support**: AWS S3 integration for sync operations

### Platform SDKs
The project includes documentation for integrating with:
- **RunPod Python SDK**: Endpoint management, template creation, GPU allocation
- **Vast.ai Python SDK**: Instance management, SSH keys, file operations

## Project Structure
- `src/variousplug/`: Main package directory
- `pyproject.toml`: Python project configuration with hatchling build system
- Entry point: `variousplug:main` function

## Usage Pattern
Users create project directories, write code locally, then execute on remote Docker hosts using the `fp` command (fireplug compatibility) or `vp` command.