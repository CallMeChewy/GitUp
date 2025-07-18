#!/bin/bash

# GitUp TV955 Fusion - Linux Installer
# Version: 2.1.0-tv955-fusion
# Build Date: 2025-07-18T08:17:22.631547

set -e

INSTALL_DIR="/usr/local/bin"
BINARY_NAME="gitup"
DOWNLOAD_URL="https://bowersworld.com/releases/gitup/linux/gitup"

echo "🚀 GitUp TV955 Fusion Installer"
echo "=================================="
echo "Installing secure project creation tool with CRT terminal experience"
echo ""

# Check if running as root for system installation
if [ "$EUID" -eq 0 ]; then
    echo "📁 Installing to system directory: $INSTALL_DIR"
    INSTALL_PATH="$INSTALL_DIR/$BINARY_NAME"
else
    echo "📁 Installing to user directory: ~/.local/bin"
    INSTALL_DIR="$HOME/.local/bin"
    INSTALL_PATH="$INSTALL_DIR/$BINARY_NAME"
    mkdir -p "$INSTALL_DIR"
fi

# Download and install
echo "⬇️  Downloading GitUp binary..."
if command -v curl >/dev/null 2>&1; then
    curl -sSL "$DOWNLOAD_URL" -o "$INSTALL_PATH"
elif command -v wget >/dev/null 2>&1; then
    wget -q "$DOWNLOAD_URL" -O "$INSTALL_PATH"
else
    echo "❌ Error: curl or wget required for installation"
    exit 1
fi

# Make executable
chmod +x "$INSTALL_PATH"

# Verify installation
if [ -x "$INSTALL_PATH" ]; then
    echo "✅ GitUp installed successfully!"
    echo ""
    echo "🎯 Quick Start:"
    echo "   gitup --help              # Show help"
    echo "   GITUP_MODE=newbie gitup   # Launch in educational mode"
    echo ""
    echo "🎮 TV955 Experience:"
    echo "   Download TV955 terminal emulator for full CRT experience"
    echo "   Visit: https://bowersworld.com/tv955"
    echo ""
    echo "📚 Documentation: https://bowersworld.com/gitup/docs"
else
    echo "❌ Installation failed"
    exit 1
fi
