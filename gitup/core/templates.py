# File: templates.py
# Path: gitup/core/templates.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:08PM
"""
GitUp Template Management System
Manages project templates with smart .gitignore generation and context-aware setup.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml
import json

from ..utils.exceptions import TemplateError

class TemplateManager:
    """Manages project templates and smart configuration"""
    
    def __init__(self):
        self.templates = self._load_built_in_templates()
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        return [
            {
                'name': name,
                'description': info['description'],
                'language': info['language'],
                'security_level': info['security_level']
            }
            for name, info in self.templates.items()
        ]
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get detailed information about a template"""
        if template_name not in self.templates:
            raise TemplateError(f"Template '{template_name}' not found")
        
        return self.templates[template_name].copy()
    
    def detect_template(self) -> Dict[str, Any]:
        """Auto-detect appropriate template based on context"""
        # For now, default to python-web
        # In a real implementation, this would analyze the environment
        return self.get_template_info('python-web')
    
    def _load_built_in_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in project templates"""
        return {
            'python-web': {
                'name': 'python-web',
                'description': 'Python web application (Flask/Django)',
                'language': 'Python',
                'languages': ['python'],
                'security_level': 'high',
                'dependencies': [
                    'flask>=2.0.0',
                    'requests>=2.28.0',
                    'python-dotenv>=0.19.0'
                ],
                'directories': ['src', 'tests', 'docs', 'static', 'templates'],
                'gitignore': self._get_python_web_gitignore(),
                'features': [
                    'Flask web framework',
                    'Virtual environment setup',
                    'GitGuard security integration',
                    'Pre-commit hooks',
                    'Development server configuration'
                ]
            },
            'python-data': {
                'name': 'python-data',
                'description': 'Python data science project',
                'language': 'Python',
                'languages': ['python'],
                'security_level': 'medium',
                'dependencies': [
                    'pandas>=1.5.0',
                    'numpy>=1.24.0',
                    'jupyter>=1.0.0',
                    'matplotlib>=3.6.0',
                    'seaborn>=0.12.0'
                ],
                'directories': ['src', 'data', 'notebooks', 'tests', 'docs'],
                'gitignore': self._get_python_data_gitignore(),
                'features': [
                    'Data science libraries',
                    'Jupyter notebook support',
                    'Data directory structure',
                    'Model versioning',
                    'Visualization tools'
                ]
            },
            'python-cli': {
                'name': 'python-cli',
                'description': 'Python command-line tool',
                'language': 'Python',
                'languages': ['python'],
                'security_level': 'medium',
                'dependencies': [
                    'click>=8.0.0',
                    'rich>=12.0.0',
                    'typer>=0.7.0'
                ],
                'directories': ['src', 'tests', 'docs'],
                'gitignore': self._get_python_cli_gitignore(),
                'features': [
                    'Click CLI framework',
                    'Rich terminal output',
                    'Command-line argument parsing',
                    'Packaging for distribution'
                ]
            },
            'node-web': {
                'name': 'node-web',
                'description': 'Node.js web application',
                'language': 'JavaScript',
                'languages': ['javascript'],
                'security_level': 'high',
                'dependencies': [
                    'express',
                    'dotenv',
                    'cors',
                    'helmet'
                ],
                'directories': ['src', 'tests', 'docs', 'public'],
                'gitignore': self._get_node_gitignore(),
                'features': [
                    'Express.js framework',
                    'Security middleware',
                    'Environment configuration',
                    'Static file serving'
                ]
            },
            'react-app': {
                'name': 'react-app',
                'description': 'React application',
                'language': 'JavaScript',
                'languages': ['javascript'],
                'security_level': 'medium',
                'dependencies': [
                    'react',
                    'react-dom',
                    'react-scripts'
                ],
                'directories': ['src', 'public', 'tests', 'docs'],
                'gitignore': self._get_react_gitignore(),
                'features': [
                    'React framework',
                    'Component-based architecture',
                    'Hot reloading',
                    'Build optimization'
                ]
            },
            'docs': {
                'name': 'docs',
                'description': 'Documentation project',
                'language': 'Markdown',
                'languages': ['markdown'],
                'security_level': 'low',
                'dependencies': [],
                'directories': ['docs', 'assets', 'examples'],
                'gitignore': self._get_docs_gitignore(),
                'features': [
                    'Documentation structure',
                    'Markdown support',
                    'Asset management',
                    'Example code organization'
                ]
            }
        }
    
    def _get_python_web_gitignore(self) -> str:
        """Python web application .gitignore with GitGuard integration"""
        return '''# GitUp Generated .gitignore - Python Web Application
# Template: python-web
# Generated: 2025-07-15

# ========================================
# PYTHON
# ========================================
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# ========================================
# VIRTUAL ENVIRONMENTS
# ========================================
.venv/
venv/
ENV/
env/
.env/

# ========================================
# WEB APPLICATION SPECIFIC
# ========================================
# Flask instance folder
instance/

# Database files
*.db
*.sqlite
*.sqlite3

# Session files
flask_session/

# Uploaded files
uploads/
static/uploads/
media/

# Cache files
.cache/
.flask_cache/

# ========================================
# ENVIRONMENT & CONFIGURATION
# ========================================
.env
.env.local
.env.development
.env.production
.env.staging

# Configuration files with secrets
config/secrets.py
config/production.py
config/local_settings.py

# SSL certificates
*.pem
*.key
*.crt
*.cer
*.p12
*.pfx

# ========================================
# LOGS & DEBUGGING
# ========================================
*.log
logs/
debug.log
error.log
access.log

# ========================================
# TESTING & COVERAGE
# ========================================
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
coverage.xml
*.cover
.hypothesis/

# ========================================
# DEVELOPMENT TOOLS
# ========================================
.vscode/
.idea/
*.swp
*.swo
*~

# ========================================
# OS GENERATED
# ========================================
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# ========================================
# GITGUARD INTEGRATION
# ========================================
.gitguard/logs/
.gitguard/backups/
.gitguard/cache/

# ========================================
# GITUP SPECIFIC
# ========================================
.gitup/
bootstrap_logs/
'''

    def _get_python_data_gitignore(self) -> str:
        """Python data science .gitignore"""
        return '''# GitUp Generated .gitignore - Python Data Science
# Template: python-data
# Generated: 2025-07-15

# ========================================
# PYTHON
# ========================================
__pycache__/
*.py[cod]
*$py.class
.Python
.venv/
venv/

# ========================================
# JUPYTER NOTEBOOK
# ========================================
.ipynb_checkpoints
*/.ipynb_checkpoints/*

# ========================================
# DATA FILES
# ========================================
# Raw data (usually large and sensitive)
data/raw/
data/external/
data/private/

# Processed data (may contain sensitive info)
data/processed/confidential/
data/processed/personal/

# Keep these data files (safe for version control)
# data/processed/public/
# data/reference/
# data/examples/

# Database files
*.db
*.sqlite
*.sqlite3

# Data formats
*.csv
*.xlsx
*.json
*.parquet
*.h5
*.hdf5

# Pickled files
*.pkl
*.pickle

# ========================================
# MACHINE LEARNING
# ========================================
# Model files
models/
*.model
*.h5
*.joblib
*.pkl

# Training logs
logs/
tensorboard_logs/
wandb/

# Checkpoints
checkpoints/
*.ckpt

# ========================================
# ENVIRONMENT & CONFIGURATION
# ========================================
.env
.env.local
config/secrets.py

# ========================================
# GITGUARD INTEGRATION
# ========================================
.gitguard/logs/
.gitguard/backups/
.gitguard/cache/

# ========================================
# DEVELOPMENT
# ========================================
.vscode/
.idea/
*.swp
*.swo

# ========================================
# OS GENERATED
# ========================================
.DS_Store
Thumbs.db
'''

    def _get_python_cli_gitignore(self) -> str:
        """Python CLI tool .gitignore"""
        return '''# GitUp Generated .gitignore - Python CLI Tool
# Template: python-cli
# Generated: 2025-07-15

# ========================================
# PYTHON
# ========================================
__pycache__/
*.py[cod]
*$py.class
.Python
.venv/
venv/
build/
dist/
*.egg-info/

# ========================================
# CLI TOOL SPECIFIC
# ========================================
# User configuration
config/user_config.json
config/user_settings.yaml
~/.config/*/

# CLI logs
cli.log
*.log
logs/

# Cache files
cache/
.cache/
*.cache

# Temporary files
tmp/
temp/
*.tmp

# ========================================
# ENVIRONMENT
# ========================================
.env
.env.local

# ========================================
# GITGUARD INTEGRATION
# ========================================
.gitguard/logs/
.gitguard/backups/
.gitguard/cache/

# ========================================
# DEVELOPMENT
# ========================================
.vscode/
.idea/
*.swp
*.swo

# ========================================
# TESTING
# ========================================
.pytest_cache/
.coverage
htmlcov/

# ========================================
# OS GENERATED
# ========================================
.DS_Store
Thumbs.db
'''

    def _get_node_gitignore(self) -> str:
        """Node.js .gitignore"""
        return '''# GitUp Generated .gitignore - Node.js Web Application
# Template: node-web
# Generated: 2025-07-15

# ========================================
# NODE.JS
# ========================================
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# ========================================
# DEPENDENCY DIRECTORIES
# ========================================
jspm_packages/
bower_components/

# ========================================
# ENVIRONMENT & CONFIGURATION
# ========================================
.env
.env.local
.env.development
.env.production
.env.staging

# ========================================
# BUILD & DISTRIBUTION
# ========================================
dist/
build/
.next/
.nuxt/
.vuepress/dist/

# ========================================
# LOGS
# ========================================
*.log
logs/

# ========================================
# CACHE
# ========================================
.npm
.eslintcache
.cache/

# ========================================
# GITGUARD INTEGRATION
# ========================================
.gitguard/logs/
.gitguard/backups/
.gitguard/cache/

# ========================================
# DEVELOPMENT
# ========================================
.vscode/
.idea/
*.swp
*.swo

# ========================================
# OS GENERATED
# ========================================
.DS_Store
Thumbs.db
'''

    def _get_react_gitignore(self) -> str:
        """React application .gitignore"""
        return '''# GitUp Generated .gitignore - React Application
# Template: react-app
# Generated: 2025-07-15

# ========================================
# NODE.JS
# ========================================
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# ========================================
# REACT BUILD
# ========================================
build/
dist/
.next/

# ========================================
# ENVIRONMENT
# ========================================
.env
.env.local
.env.development
.env.production

# ========================================
# CACHE
# ========================================
.eslintcache
.cache/

# ========================================
# GITGUARD INTEGRATION
# ========================================
.gitguard/logs/
.gitguard/backups/
.gitguard/cache/

# ========================================
# DEVELOPMENT
# ========================================
.vscode/
.idea/

# ========================================
# OS GENERATED
# ========================================
.DS_Store
Thumbs.db
'''

    def _get_docs_gitignore(self) -> str:
        """Documentation project .gitignore"""
        return '''# GitUp Generated .gitignore - Documentation Project
# Template: docs
# Generated: 2025-07-15

# ========================================
# DOCUMENTATION BUILD
# ========================================
_build/
build/
dist/
site/

# ========================================
# TEMPORARY FILES
# ========================================
*.tmp
*.temp
~*

# ========================================
# GITGUARD INTEGRATION
# ========================================
.gitguard/logs/
.gitguard/backups/
.gitguard/cache/

# ========================================
# DEVELOPMENT
# ========================================
.vscode/
.idea/

# ========================================
# OS GENERATED
# ========================================
.DS_Store
Thumbs.db
'''