#!/usr/bin/env python3
"""
Test script for VariousPlug RunPod integration.
"""
import os
import platform
import sys
from datetime import datetime


def main():
    print("=" * 50)
    print("VariousPlug RunPod Test Script")
    print("=" * 50)

    # System information
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print(f"Current time: {datetime.now()}")
    print()

    # Working directory
    print(f"Working directory: {os.getcwd()}")
    print("Directory contents:")
    for item in sorted(os.listdir(".")):
        print(f"  - {item}")
    print()

    # Test Python imports
    print("Testing Python imports:")
    try:
        import torch
        print(f"✅ PyTorch: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"✅ CUDA available: {torch.cuda.device_count()} devices")
            for i in range(torch.cuda.device_count()):
                print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("⚠️  CUDA not available")
    except ImportError:
        print("❌ PyTorch not available")

    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError:
        print("❌ NumPy not available")

    # Create output file
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)

    output_file = f"{output_dir}/test_results.txt"
    with open(output_file, "w") as f:
        f.write("VariousPlug Test Results\n")
        f.write(f"Timestamp: {datetime.now()}\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Platform: {platform.platform()}\n")
        f.write("Test completed successfully!\n")

    print(f"✅ Created output file: {output_file}")
    print("=" * 50)
    print("Test completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
