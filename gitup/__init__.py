"""
GitUp - Enhanced Project Bootstrap Tool
Part of Project Himalaya - AI-Human Collaborative Development Framework

A comprehensive project setup tool that handles git, virtual environments,
dependencies, and security configuration in one command.

Key Features:
- One-command project setup
- GitGuard security integration
- Smart project templates
- Virtual environment management
- Intelligent .gitignore generation
- Git repository initialization with hooks

Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
License: MIT
Version: 0.1.0

This project demonstrates AI-human collaboration in creating developer tools
that solve real-world friction points in software development.
"""

__version__ = "2.1.0-tv955-fusion"
__author__ = "Herbert J. Bowers (Project Creator), Claude (Anthropic) - Technical Implementation"
__email__ = "HimalayaProject1@gmail.com"
__license__ = "MIT"

# Core imports for easy access
from .core.bootstrap import ProjectBootstrap
from .core.templates import TemplateManager
from .core.gitguard_integration import GitGuardIntegration

# Exception classes
from .utils.exceptions import (
    GitUpError,
    TemplateError,
    BootstrapError,
    GitGuardIntegrationError
)

# Main API classes
__all__ = [
    # Core classes
    "ProjectBootstrap",
    "TemplateManager", 
    "GitGuardIntegration",
    
    # Exceptions
    "GitUpError",
    "TemplateError",
    "BootstrapError",
    "GitGuardIntegrationError",
    
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
]

# Package metadata
PACKAGE_NAME = "gitup"
DESCRIPTION = "Enhanced project bootstrap tool with GitGuard integration"
HOMEPAGE = "https://github.com/herbbowers/gitup"
DOCUMENTATION = "https://gitup.dev"

# Supported Python versions
PYTHON_REQUIRES = ">=3.8"

def get_version():
    """Get the current GitUp version."""
    return __version__

def get_info():
    """Get comprehensive package information."""
    return {
        "name": PACKAGE_NAME,
        "version": __version__,
        "description": DESCRIPTION,
        "author": __author__,
        "email": __email__,
        "license": __license__,
        "homepage": HOMEPAGE,
        "documentation": DOCUMENTATION,
        "python_requires": PYTHON_REQUIRES,
    }