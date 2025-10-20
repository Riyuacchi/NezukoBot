#!/bin/bash
# Pelican Panel startup script with automatic dependency installation

echo "=== NezukoBot Pelican Startup Script ==="

# Update from git if enabled
if [[ -d .git ]] && [[ ${AUTO_UPDATE} == "1" ]]; then
    echo "Updating from git..."
    git pull
fi

# Try to install dependencies if not already installed
if ! command -v cmake &> /dev/null; then
    echo "CMake not found. Attempting to install dependencies..."

    # Make install script executable
    chmod +x install-deps.sh 2>/dev/null

    # Try to run installer (may fail if no sudo)
    if ./install-deps.sh 2>/dev/null; then
        echo "Dependencies installed successfully!"
    else
        echo "WARNING: Could not install dependencies automatically."
        echo "Voice support requires: cmake, build-essential, libopus-dev, pkg-config"
        echo "Building without voice support..."
        cargo run --release
        exit $?
    fi
fi

# Check if we have the necessary tools for voice support
if command -v cmake &> /dev/null && command -v pkg-config &> /dev/null; then
    echo "Build tools detected. Compiling with voice support..."
    cargo run --release --features voice
else
    echo "Build tools not available. Compiling without voice support..."
    cargo run --release
fi
