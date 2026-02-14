#!/bin/bash
# Build Test Script for HA Governance Add-on
# Tests if Dockerfile builds successfully

set -e

echo "======================================"
echo "HA Governance Build Test"
echo "======================================"

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

echo "✅ Docker found"

# Check if we're in the right directory
if [ ! -f "Dockerfile" ]; then
    echo "❌ Dockerfile not found. Run this script from the ha_governance directory"
    exit 1
fi

echo "✅ Dockerfile found"

# Check critical files exist
critical_files=(
    "config.yaml"
    "requirements.txt"
    "app/main.py"
    "rootfs/etc/s6-overlay/s6-rc.d/ha_governance/run"
    "rootfs/etc/s6-overlay/s6-rc.d/ha_governance/type"
)

for file in "${critical_files[@]}"; do
    if [ ! -f "$file" ] && [ ! -d "$file" ]; then
        echo "❌ Missing critical file: $file"
        exit 1
    fi
done

echo "✅ All critical files present"

# Test build
echo ""
echo "Building Docker image (this may take a few minutes)..."
echo "--------------------------------------"

if docker build \
    --build-arg BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest \
    --build-arg BUILD_VERSION=0.1.45 \
    --build-arg BUILD_ARCH=amd64 \
    -t ha-governance-test:latest \
    .; then
    
    echo ""
    echo "======================================"
    echo "✅ BUILD SUCCESSFUL!"
    echo "======================================"
    echo ""
    echo "Image: ha-governance-test:latest"
    echo ""
    echo "Next steps:"
    echo "1. Commit and push to your repository"
    echo "2. Reload repository in HA Add-on Store"
    echo "3. Update to version 0.1.45"
    echo ""
    
    # Cleanup
    read -p "Remove test image? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rmi ha-governance-test:latest
        echo "✅ Test image removed"
    fi
    
else
    echo ""
    echo "======================================"
    echo "❌ BUILD FAILED"
    echo "======================================"
    echo ""
    echo "Check the error messages above."
    echo "Common issues:"
    echo "  - Missing rootfs/ directory"
    echo "  - Scripts not executable"
    echo "  - Syntax errors in Dockerfile"
    echo ""
    exit 1
fi
