# -*- mode: python ; coding: utf-8 -*-

"""
GitUp PyInstaller Build Specification

This spec file builds GitUp into a single executable binary for distribution.
The binary includes all dependencies and can run on systems without Python installed.

Build command: pyinstaller build.spec
"""

import os
import sys
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, os.path.abspath('.'))

# Define paths
project_root = Path('.')
gitup_core = project_root / 'gitup'

block_cipher = None

# Analysis phase - discover all dependencies
a = Analysis(
    ['gitup/cli.py'],  # Main entry point
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        # Include template files
        ('gitup/templates', 'gitup/templates'),
        ('gitup/core/templates.py', 'gitup/core'),
        
        # Include configuration files
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('CHANGELOG.md', '.'),
        
        # Include documentation
        ('docs', 'docs'),
        
        # TV955 integration files
        ('gitup_tv955_wizard.js', '.'),
    ],
    hiddenimports=[
        # Core GitUp modules
        'gitup.core.bootstrap',
        'gitup.core.risk_mitigation',
        'gitup.core.security_interface',
        'gitup.core.terminal_interface',
        'gitup.core.interface_modes',
        'gitup.core.templates',
        'gitup.core.ignore_manager',
        'gitup.core.project_state_detector',
        'gitup.core.gitguard_integration',
        
        # Required dependencies
        'click',
        'rich',
        'yaml',
        'pathspec',
        'gitguard',
        'jinja2',
        'dotenv',
        
        # System modules
        'subprocess',
        'pathlib',
        'os',
        'sys',
        'json',
        'datetime',
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude development dependencies
        'pytest',
        'black',
        'flake8',
        'coverage',
        'sphinx',
        
        # Exclude GUI libraries we don't use
        'tkinter',
        'matplotlib',
        'pygame',
        'PIL',
        
        # Exclude large modules we don't need
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Post-analysis cleanup
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='gitup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress binary
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Could add GitUp icon here
)

# Build information
print("=" * 60)
print("GitUp PyInstaller Build Configuration")
print("=" * 60)
print(f"Project Root: {project_root}")
print(f"Entry Point: gitup/cli.py")
print(f"Output Binary: dist/gitup")
print(f"Console Mode: True")
print(f"Compression: UPX enabled")
print("=" * 60)