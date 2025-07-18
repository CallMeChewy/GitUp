#!/usr/bin/env python3

"""
GitUp Build System

Automated build script for creating GitUp distribution binaries.
Supports multiple platforms and build configurations.

Usage:
    python build.py --platform linux
    python build.py --platform windows
    python build.py --platform macos
    python build.py --all
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path
import json
from datetime import datetime

class GitUpBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / 'dist'
        self.build_dir = self.project_root / 'build'
        self.platform_name = platform.system().lower()
        self.arch = platform.machine().lower()
        
        # Build configuration
        self.config = {
            'version': '2.1.0-tv955-fusion',
            'author': 'Herbert J. Bowers & Claude (Anthropic)',
            'description': 'GitUp TV955 Fusion - Secure Project Creation with CRT Experience',
            'build_date': datetime.now().isoformat(),
            'build_platform': f"{self.platform_name}-{self.arch}",
        }
        
    def ensure_dependencies(self):
        """Ensure PyInstaller and build dependencies are available."""
        print("🔧 Checking build dependencies...")
        
        required_packages = [
            'pyinstaller>=5.0.0',
            'setuptools>=60.0.0',
            'wheel>=0.37.0'
        ]
        
        for package in required_packages:
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True, check=True)
                print(f"   ✅ {package} installed/updated")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Failed to install {package}: {e}")
                return False
                
        return True
    
    def clean_build(self):
        """Clean previous build artifacts."""
        print("🧹 Cleaning previous build artifacts...")
        
        dirs_to_clean = [self.dist_dir, self.build_dir]
        for dir_path in dirs_to_clean:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"   🗑️  Removed {dir_path}")
        
        # Remove spec file artifacts
        spec_files = list(self.project_root.glob('*.spec'))
        for spec_file in spec_files:
            if spec_file.name != 'build.spec':  # Keep our main spec
                spec_file.unlink()
                print(f"   🗑️  Removed {spec_file}")
    
    def build_binary(self, target_platform=None):
        """Build GitUp binary using PyInstaller."""
        target = target_platform or self.platform_name
        print(f"🏗️  Building GitUp binary for {target}...")
        
        # Create target-specific dist directory
        if target == 'windows':
            dist_path = 'dist/windows'
        elif target == 'macos':
            dist_path = 'dist/macos'
        else:  # linux
            dist_path = 'dist/linux'
        
        # Ensure dist directory exists
        os.makedirs(dist_path, exist_ok=True)
        
        # Use the spec file directly with PyInstaller
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--distpath', dist_path,
            'build.spec'
        ]
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True)
            
            # Rename the binary to include platform
            original_binary = Path(dist_path) / 'gitup'
            if target == 'windows':
                target_binary = Path(dist_path) / 'gitup-windows.exe'
                if original_binary.exists():
                    original_binary.rename(target_binary)
            else:
                target_binary = Path(dist_path) / f'gitup-{target}'
                if original_binary.exists():
                    original_binary.rename(target_binary)
            
            print(f"   ✅ Binary built successfully for {target}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Build failed for {target}: {e}")
            return False
    
    def create_installer_script(self, target_platform):
        """Create platform-specific installer script."""
        if target_platform == 'linux':
            self.create_linux_installer()
        elif target_platform == 'windows':
            self.create_windows_installer()
        elif target_platform == 'macos':
            self.create_macos_installer()
    
    def create_linux_installer(self):
        """Create Linux installation script."""
        installer_content = f'''#!/bin/bash

# GitUp TV955 Fusion - Linux Installer
# Version: {self.config['version']}
# Build Date: {self.config['build_date']}

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
'''
        
        installer_path = self.dist_dir / 'linux' / 'install.sh'
        installer_path.parent.mkdir(parents=True, exist_ok=True)
        installer_path.write_text(installer_content)
        installer_path.chmod(0o755)
        print(f"   📝 Created Linux installer: {installer_path}")
    
    def create_build_info(self):
        """Create build information file."""
        build_info = {
            **self.config,
            'files': {
                'binary': f'gitup-{self.platform_name}',
                'installer': f'install-{self.platform_name}.sh',
                'checksum': 'sha256.txt'
            },
            'system_requirements': {
                'os': f'{self.platform_name}',
                'arch': self.arch,
                'min_version': 'Ubuntu 18.04+ / CentOS 7+ / Similar'
            },
            'features': [
                'Multi-level interface system (Hardcore/Standard/Newbie)',
                'TV955 terminal integration',
                'Template-based secure project creation',
                'Real-time security risk detection',
                'Smart .gitignore management',
                'Authentic CRT terminal experience'
            ]
        }
        
        info_path = self.dist_dir / 'build-info.json'
        with open(info_path, 'w') as f:
            json.dump(build_info, f, indent=2)
        print(f"   📋 Created build info: {info_path}")
    
    def calculate_checksums(self):
        """Calculate checksums for distribution files."""
        print("🔐 Calculating checksums...")
        
        import hashlib
        
        checksum_file = self.dist_dir / 'sha256.txt'
        
        with open(checksum_file, 'w') as f:
            for file_path in self.dist_dir.rglob('*'):
                if file_path.is_file() and file_path.name != 'sha256.txt':
                    sha256_hash = hashlib.sha256()
                    with open(file_path, 'rb') as binary_file:
                        for chunk in iter(lambda: binary_file.read(4096), b""):
                            sha256_hash.update(chunk)
                    
                    relative_path = file_path.relative_to(self.dist_dir)
                    f.write(f"{sha256_hash.hexdigest()}  {relative_path}\\n")
                    print(f"   🔑 {relative_path}: {sha256_hash.hexdigest()[:16]}...")
        
        print(f"   ✅ Checksums saved to {checksum_file}")
    
    def build_all_platforms(self):
        """Build for all supported platforms."""
        platforms = ['linux', 'windows', 'macos']
        success_count = 0
        
        for platform_name in platforms:
            print(f"\\n{'='*60}")
            print(f"Building for {platform_name.upper()}")
            print('='*60)
            
            if self.build_binary(platform_name):
                self.create_installer_script(platform_name)
                success_count += 1
            else:
                print(f"❌ Failed to build for {platform_name}")
        
        print(f"\\n🎯 Build Summary: {success_count}/{len(platforms)} platforms successful")
        return success_count == len(platforms)
    
    def run_build(self, target_platform=None, clean=True):
        """Run the complete build process."""
        print("🚀 GitUp TV955 Fusion Build System")
        print("=" * 50)
        print(f"Version: {self.config['version']}")
        print(f"Platform: {self.platform_name}-{self.arch}")
        print(f"Target: {target_platform or 'current platform'}")
        print("=" * 50)
        
        try:
            # Preparation
            if not self.ensure_dependencies():
                return False
            
            if clean:
                self.clean_build()
            
            # Build process
            if target_platform == 'all':
                success = self.build_all_platforms()
            else:
                success = self.build_binary(target_platform)
                if success:
                    self.create_installer_script(target_platform or self.platform_name)
            
            if success:
                self.create_build_info()
                self.calculate_checksums()
                
                print("\\n🎊 BUILD COMPLETED SUCCESSFULLY!")
                print(f"📁 Distribution files: {self.dist_dir}")
                print("\\n🎯 Next Steps:")
                print("   1. Test the binary on target systems")
                print("   2. Upload to BowersWorld.com distribution")
                print("   3. Update download links and documentation")
                
                return True
            else:
                print("\\n❌ BUILD FAILED")
                return False
                
        except Exception as e:
            print(f"\\n💥 Unexpected error: {e}")
            return False

def main():
    """Main entry point for build script."""
    parser = argparse.ArgumentParser(description='GitUp Build System')
    parser.add_argument('--platform', choices=['linux', 'windows', 'macos', 'all'], 
                       help='Target platform for build')
    parser.add_argument('--no-clean', action='store_true', 
                       help='Skip cleaning previous build artifacts')
    parser.add_argument('--version', action='version', version='GitUp Build System 2.1.0')
    
    args = parser.parse_args()
    
    builder = GitUpBuilder()
    success = builder.run_build(
        target_platform=args.platform,
        clean=not args.no_clean
    )
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()