#!/usr/bin/env python3
"""
GitUp - Enhanced Project Bootstrap Tool
Setup configuration for Python package distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements from requirements.txt
requirements = []
if (this_directory / "requirements.txt").exists():
    with open(this_directory / "requirements.txt") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="gitup",
    version="0.1.0",
    author="Herbert J. Bowers (Project Creator), Claude (Anthropic) - Technical Implementation",
    author_email="HimalayaProject1@gmail.com",
    description="Enhanced project bootstrap tool with GitGuard integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/herbbowers/gitup",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
        "Topic :: Security",
        "Topic :: System :: Installation/Setup",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gitup=gitup.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "gitup": [
            "templates/*.yaml",
            "templates/*.json",
            "templates/gitignore/*",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/herbbowers/gitup/issues",
        "Source": "https://github.com/herbbowers/gitup",
        "Documentation": "https://gitup.dev",
    },
)