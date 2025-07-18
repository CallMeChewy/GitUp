#!/bin/bash

# GitUp TV955 Fusion - Universal Installer
# 
# This script installs GitUp on Linux/macOS systems
# Usage: curl -sSL bowersworld.com/gitup/install | bash

set -e

# Configuration
GITUP_VERSION="2.1.0-tv955-fusion"
BASE_URL="https://github.com/herbbowers/gitup/releases/latest/download"
INSTALL_DIR_SYSTEM="/usr/local/bin"
INSTALL_DIR_USER="$HOME/.local/bin"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Logo and header
show_header() {
    echo ""
    echo -e "${BLUE}${BOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}${BOLD}║                     🚀 GitUp TV955 Fusion                     ║${NC}"
    echo -e "${BLUE}${BOLD}║            Secure Project Creation + CRT Experience           ║${NC}"
    echo -e "${BLUE}${BOLD}║                        Version $GITUP_VERSION                        ║${NC}"
    echo -e "${BLUE}${BOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Revolutionary secure development tool with authentic terminal experience${NC}"
    echo ""
}

# Detect system
detect_system() {
    echo -e "${BLUE}🔍 Detecting system...${NC}"
    
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    
    case "$OS" in
        linux*)
            PLATFORM="linux"
            BINARY_NAME="gitup-linux-x64"
            ;;
        darwin*)
            PLATFORM="macos"
            BINARY_NAME="gitup-macos-x64"
            ;;
        *)
            echo -e "${RED}❌ Unsupported operating system: $OS${NC}"
            echo "   Supported: Linux, macOS"
            exit 1
            ;;
    esac
    
    case "$ARCH" in
        x86_64|amd64)
            ARCH_SUFFIX="x64"
            ;;
        arm64|aarch64)
            # For now, use x64 binary with Rosetta on macOS
            if [ "$PLATFORM" = "macos" ]; then
                ARCH_SUFFIX="x64"
                echo -e "${YELLOW}⚠️  Using x64 binary with Rosetta on ARM Mac${NC}"
            else
                echo -e "${RED}❌ ARM Linux not yet supported${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}❌ Unsupported architecture: $ARCH${NC}"
            echo "   Supported: x86_64/amd64"
            exit 1
            ;;
    esac
    
    echo -e "   ✅ Platform: ${GREEN}$PLATFORM-$ARCH_SUFFIX${NC}"
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔧 Checking prerequisites...${NC}"
    
    # Check for download tools
    if command -v curl >/dev/null 2>&1; then
        DOWNLOAD_CMD="curl -sSL"
        echo -e "   ✅ curl found"
    elif command -v wget >/dev/null 2>&1; then
        DOWNLOAD_CMD="wget -qO-"
        echo -e "   ✅ wget found"
    else
        echo -e "${RED}❌ Neither curl nor wget found${NC}"
        echo "   Please install curl or wget and try again"
        exit 1
    fi
    
    # Check for git (optional but recommended)
    if command -v git >/dev/null 2>&1; then
        echo -e "   ✅ git found"
    else
        echo -e "   ${YELLOW}⚠️  git not found (recommended for GitUp functionality)${NC}"
    fi
}

# Determine install location
choose_install_location() {
    echo -e "${BLUE}📁 Determining installation location...${NC}"
    
    if [ "$EUID" -eq 0 ] || [ "$(id -u)" -eq 0 ]; then
        # Running as root - install system-wide
        INSTALL_DIR="$INSTALL_DIR_SYSTEM"
        echo -e "   ✅ Installing system-wide: ${GREEN}$INSTALL_DIR${NC}"
    else
        # Check if user can write to system directory
        if [ -w "$INSTALL_DIR_SYSTEM" ]; then
            INSTALL_DIR="$INSTALL_DIR_SYSTEM"
            echo -e "   ✅ Installing system-wide: ${GREEN}$INSTALL_DIR${NC}"
        else
            # Install to user directory
            INSTALL_DIR="$INSTALL_DIR_USER"
            mkdir -p "$INSTALL_DIR"
            echo -e "   ✅ Installing to user directory: ${GREEN}$INSTALL_DIR${NC}"
            
            # Check if user bin directory is in PATH
            if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
                echo -e "   ${YELLOW}⚠️  $INSTALL_DIR not in PATH${NC}"
                echo "   Add this to your shell profile (.bashrc, .zshrc, etc.):"
                echo -e "   ${BOLD}export PATH=\"$INSTALL_DIR:\$PATH\"${NC}"
            fi
        fi
    fi
    
    INSTALL_PATH="$INSTALL_DIR/gitup"
}

# Download and install
install_gitup() {
    echo -e "${BLUE}⬇️  Downloading GitUp...${NC}"
    
    DOWNLOAD_URL="$BASE_URL/$BINARY_NAME"
    TEMP_FILE=$(mktemp)
    
    echo -e "   📡 Source: $DOWNLOAD_URL"
    
    if [ "$DOWNLOAD_CMD" = "curl -sSL" ]; then
        if ! curl -sSL "$DOWNLOAD_URL" -o "$TEMP_FILE"; then
            echo -e "${RED}❌ Download failed${NC}"
            rm -f "$TEMP_FILE"
            exit 1
        fi
    else
        if ! wget -qO "$TEMP_FILE" "$DOWNLOAD_URL"; then
            echo -e "${RED}❌ Download failed${NC}"
            rm -f "$TEMP_FILE"
            exit 1
        fi
    fi
    
    # Verify download
    if [ ! -s "$TEMP_FILE" ]; then
        echo -e "${RED}❌ Downloaded file is empty${NC}"
        rm -f "$TEMP_FILE"
        exit 1
    fi
    
    # Install binary
    echo -e "${BLUE}📦 Installing binary...${NC}"
    mv "$TEMP_FILE" "$INSTALL_PATH"
    chmod +x "$INSTALL_PATH"
    
    # Verify installation
    if [ -x "$INSTALL_PATH" ]; then
        echo -e "   ✅ Binary installed: ${GREEN}$INSTALL_PATH${NC}"
    else
        echo -e "${RED}❌ Installation failed${NC}"
        exit 1
    fi
}

# Test installation
test_installation() {
    echo -e "${BLUE}🧪 Testing installation...${NC}"
    
    if "$INSTALL_PATH" --version >/dev/null 2>&1; then
        VERSION_OUTPUT=$("$INSTALL_PATH" --version 2>/dev/null || echo "GitUp $GITUP_VERSION")
        echo -e "   ✅ Installation successful: ${GREEN}$VERSION_OUTPUT${NC}"
    else
        echo -e "${RED}❌ Installation test failed${NC}"
        echo "   Binary exists but won't execute"
        exit 1
    fi
}

# Show completion message
show_completion() {
    echo ""
    echo -e "${GREEN}${BOLD}🎊 GitUp TV955 Fusion installed successfully!${NC}"
    echo ""
    echo -e "${BOLD}🚀 Quick Start:${NC}"
    echo -e "   ${BLUE}gitup --help${NC}                    # Show help"
    echo -e "   ${BLUE}gitup init${NC}                      # Initialize secure project"
    echo -e "   ${BLUE}GITUP_MODE=newbie gitup${NC}         # Educational mode"
    echo ""
    echo -e "${BOLD}🎮 Interface Modes:${NC}"
    echo -e "   ${BLUE}GITUP_MODE=hardcore${NC}             # Minimal, fast interface"
    echo -e "   ${BLUE}GITUP_MODE=standard${NC}             # Professional interface (default)"
    echo -e "   ${BLUE}GITUP_MODE=newbie${NC}               # Educational, guided interface"
    echo ""
    echo -e "${BOLD}📺 TV955 CRT Experience:${NC}"
    echo -e "   For the full authentic terminal experience:"
    echo -e "   ${YELLOW}https://bowersworld.com/tv955${NC}"
    echo ""
    echo -e "${BOLD}📚 Documentation:${NC}"
    echo -e "   User Guide: ${YELLOW}https://bowersworld.com/gitup/docs${NC}"
    echo -e "   Examples:   ${YELLOW}https://github.com/herbbowers/gitup/tree/main/examples${NC}"
    echo ""
    echo -e "${BOLD}🛡️  Security Features:${NC}"
    echo -e "   • Real-time security risk detection"
    echo -e "   • Smart .gitignore management"
    echo -e "   • Template-based secure project creation"
    echo -e "   • Comprehensive audit trails"
    echo ""
    echo -e "${BOLD}🏔️  Project Himalaya - AI-Human Collaboration${NC}"
    echo -e "   Created by Herbert J. Bowers & Claude (Anthropic)"
    echo ""
}

# Error handler
handle_error() {
    echo ""
    echo -e "${RED}❌ Installation failed${NC}"
    echo ""
    echo -e "${BOLD}💡 Troubleshooting:${NC}"
    echo -e "   1. Check internet connection"
    echo -e "   2. Verify system compatibility (Linux/macOS x64)"
    echo -e "   3. Ensure sufficient disk space"
    echo -e "   4. Try manual installation:"
    echo -e "      ${BLUE}wget $BASE_URL/$BINARY_NAME${NC}"
    echo -e "      ${BLUE}chmod +x $BINARY_NAME${NC}"
    echo -e "      ${BLUE}sudo mv $BINARY_NAME /usr/local/bin/gitup${NC}"
    echo ""
    echo -e "${BOLD}🆘 Support:${NC}"
    echo -e "   GitHub Issues: ${YELLOW}https://github.com/herbbowers/gitup/issues${NC}"
    echo -e "   Documentation: ${YELLOW}https://bowersworld.com/gitup/docs${NC}"
    echo ""
    exit 1
}

# Set error handler
trap handle_error ERR

# Main installation flow
main() {
    show_header
    detect_system
    check_prerequisites
    choose_install_location
    install_gitup
    test_installation
    show_completion
}

# Run installer
main "$@"