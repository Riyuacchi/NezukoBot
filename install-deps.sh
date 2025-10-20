#!/bin/bash
# Script to install build dependencies for voice support on Linux

echo "Installing build dependencies for voice support..."

# Detect package manager and install dependencies
if command -v apt-get &> /dev/null; then
    # Debian/Ubuntu
    echo "Detected apt (Debian/Ubuntu)"
    apt-get update
    apt-get install -y cmake build-essential libopus-dev pkg-config
elif command -v apk &> /dev/null; then
    # Alpine Linux
    echo "Detected apk (Alpine)"
    apk add --no-cache cmake make gcc g++ musl-dev opus-dev pkgconfig
elif command -v yum &> /dev/null; then
    # RHEL/CentOS
    echo "Detected yum (RHEL/CentOS)"
    yum install -y cmake gcc gcc-c++ opus-devel pkgconfig
else
    echo "ERROR: No supported package manager found"
    exit 1
fi

echo "Dependencies installed successfully!"
echo "You can now run: cargo build --release --features voice"
