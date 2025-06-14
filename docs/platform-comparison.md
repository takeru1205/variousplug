# Platform Comparison: Vast.ai vs RunPod

This guide compares the two supported platforms in VariousPlug to help you choose the best option for your needs.

## Quick Comparison

| Feature | Vast.ai | RunPod |
|---------|---------|---------|
| **File Sync** | Native SDK (no SSH) | rsync over SSH |
| **Setup Complexity** | Simple (API key only) | Moderate (SSH keys) |
| **Pricing** | Spot market pricing | Fixed pricing tiers |
| **GPU Variety** | Wide variety | Curated selection |
| **Instance Types** | Bare metal | Containerized pods |
| **Reliability** | Variable (spot market) | High (dedicated) |

## File Synchronization

### Vast.ai - Native SDK
```bash
# No SSH setup required
vp config-set --vast-api-key YOUR_KEY
vp run -- python script.py  # Files sync automatically
```

**Advantages:**
- ✅ No SSH configuration needed
- ✅ Works out-of-the-box with API key
- ✅ Cross-platform compatibility
- ✅ Built-in error handling and retries
- ✅ Automatic authentication

**Limitations:**
- ⚠️ Depends on Vast.ai SDK reliability
- ⚠️ Less control over transfer parameters

### RunPod - rsync over SSH
```bash
# Requires SSH key setup
vp config-set --runpod-api-key YOUR_KEY
# + SSH key configuration on pods
vp run -- "apt update && apt install -y rsync"  # First time
vp run -- python script.py  # Files sync via rsync
```

**Advantages:**
- ✅ Battle-tested rsync technology
- ✅ Fine-grained control over transfers
- ✅ Standard SSH infrastructure
- ✅ Works with any SSH-enabled host

**Limitations:**
- ⚠️ Requires SSH key setup
- ⚠️ Manual rsync installation on pods
- ⚠️ More complex initial configuration

## Pricing Models

### Vast.ai - Spot Market
- **Dynamic pricing** based on demand
- **Lower costs** during off-peak times
- **Bidding system** for better prices
- **Cost optimization** built into VariousPlug

```bash
# VariousPlug uses cost-optimized defaults
vp create-instance --platform vast --gpu-type GTX_1070
# Automatic $0.50/hour price limit
```

### RunPod - Fixed Pricing
- **Predictable costs** with fixed rates
- **Premium hardware** with guaranteed availability
- **Multiple tiers** (Secure Cloud, Community Cloud)
- **Reserved instances** for long-term workloads

```bash
# Standard RunPod pod creation
vp create-instance --platform runpod --gpu-type RTX4000
```

## Use Case Recommendations

### Choose Vast.ai When:
- 🎯 **Simplicity matters** - Minimal setup required
- 💰 **Cost optimization** - Need lowest possible prices
- ⚡ **Quick prototyping** - Fast iteration cycles
- 🔄 **Batch processing** - Intermittent workloads
- 🏠 **Local development** - Working from various environments

### Choose RunPod When:
- 🏢 **Production workloads** - Need guaranteed availability
- 🔒 **Security requirements** - Enterprise-grade infrastructure
- 📊 **Predictable costs** - Fixed budget planning
- 🚀 **Performance critical** - Need premium hardware
- 🔧 **Advanced networking** - Custom SSH configurations

## Setup Comparison

### Vast.ai Setup (5 minutes)
1. Get API key from Vast.ai console
2. Configure VariousPlug: `vp config-set --vast-api-key YOUR_KEY`
3. Start using: `vp run -- python script.py`

### RunPod Setup (15-30 minutes)
1. Get API key from RunPod console
2. Configure VariousPlug: `vp config-set --runpod-api-key YOUR_KEY`
3. Create pod with SSH keys configured
4. Install rsync on pod: `vp run --no-sync -- "apt update && apt install -y rsync"`
5. Start using: `vp run -- python script.py`

## Performance Characteristics

### Vast.ai
- **File Transfer**: Fast (native SDK)
- **Instance Startup**: Variable (5-60 seconds)
- **Availability**: Spot-based (may be preempted)
- **Network**: Variable quality

### RunPod
- **File Transfer**: Fast (rsync over dedicated network)
- **Instance Startup**: Consistent (10-30 seconds)
- **Availability**: High (dedicated resources)
- **Network**: Premium quality

## Migration Between Platforms

VariousPlug makes it easy to switch between platforms:

```bash
# Switch to Vast.ai
vp config-set --default-platform vast
vp run -- python script.py

# Switch to RunPod
vp config-set --default-platform runpod
vp run -- python script.py
```

Configuration and code remain the same - only the underlying infrastructure changes.

## Troubleshooting Platform-Specific Issues

### Vast.ai Common Issues
- **SDK errors**: Check API key validity
- **Transfer failures**: Verify instance is running
- **Permission issues**: Ensure API key has proper permissions

### RunPod Common Issues
- **SSH connection failed**: Verify SSH keys are configured
- **rsync not found**: Install rsync on the pod first
- **Permission denied**: Check SSH key permissions

## Best Practices

### For Vast.ai:
1. Always destroy instances when done (cost optimization)
2. Use GPU comparison tool to find best value
3. Monitor spot prices for optimal timing
4. Set up billing alerts

### For RunPod:
1. Configure SSH keys during pod creation
2. Install common tools (rsync, git) in custom images
3. Use templates for consistent environments
4. Consider reserved instances for long-term use

## Conclusion

Both platforms work excellent with VariousPlug:

- **Vast.ai** excels in simplicity and cost optimization
- **RunPod** provides enterprise-grade reliability and performance

Choose based on your specific needs, or use both platforms depending on the workload type.