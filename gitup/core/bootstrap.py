# File: bootstrap.py
# Path: gitup/core/bootstrap.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:07PM
"""
GitUp Project Bootstrap Core
Main bootstrap engine for creating new projects with complete setup.

This module handles:
- Project directory creation
- Git repository initialization
- Virtual environment setup
- Dependencies installation
- GitGuard integration
- Template processing
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .templates import TemplateManager
from .gitguard_integration import GitGuardIntegration
from ..utils.exceptions import BootstrapError, VirtualEnvironmentError, GitRepositoryError

console = Console()

class ProjectBootstrap:
    """Main project bootstrap engine"""
    
    def __init__(self, project_name: str, template: str = 'auto', 
                 parent_path: str = '.', security_level: str = 'medium',
                 setup_venv: bool = True, setup_gitguard: bool = True,
                 dry_run: bool = False, verbose: bool = False):
        self.project_name = project_name
        self.template = template
        self.parent_path = Path(parent_path).resolve()
        self.security_level = security_level
        self.setup_venv = setup_venv
        self.setup_gitguard = setup_gitguard
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Calculated paths
        self.project_path = self.parent_path / project_name
        
        # Components
        self.template_manager = TemplateManager()
        self.gitguard_integration = GitGuardIntegration()
        
        # State tracking
        self.bootstrap_state = {
            'project_created': False,
            'git_initialized': False,
            'venv_created': False,
            'dependencies_installed': False,
            'gitguard_configured': False,
            'initial_commit_made': False
        }
    
    def run(self) -> Dict[str, Any]:
        """Main bootstrap process"""
        console.print(f"🚀 GitUp Bootstrap: Setting up '{self.project_name}'")
        console.print("=" * 50)
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                
                # Step 1: Validate and prepare
                task = progress.add_task("🔍 Validating setup...", total=None)
                self._validate_setup()
                progress.update(task, description="✅ Setup validated")
                
                # Step 2: Create project directory
                task = progress.add_task("📁 Creating project directory...", total=None)
                self._create_project_directory()
                progress.update(task, description="✅ Project directory created")
                
                # Step 3: Process template
                task = progress.add_task("📋 Processing template...", total=None)
                template_info = self._process_template()
                progress.update(task, description=f"✅ Template '{template_info['name']}' processed")
                
                # Step 4: Initialize git repository
                task = progress.add_task("🔧 Initializing git repository...", total=None)
                self._setup_git_repository()
                progress.update(task, description="✅ Git repository initialized")
                
                # Step 5: Set up virtual environment
                if self.setup_venv and 'python' in template_info.get('languages', []):
                    task = progress.add_task("🐍 Setting up virtual environment...", total=None)
                    self._setup_virtual_environment()
                    progress.update(task, description="✅ Virtual environment created")
                
                # Step 6: Create project files
                task = progress.add_task("📝 Creating project files...", total=None)
                self._create_project_files(template_info)
                progress.update(task, description="✅ Project files created")
                
                # Step 7: Install dependencies
                task = progress.add_task("📦 Installing dependencies...", total=None)
                self._install_dependencies(template_info)
                progress.update(task, description="✅ Dependencies installed")
                
                # Step 8: Set up GitGuard
                if self.setup_gitguard:
                    task = progress.add_task("🛡️ Setting up GitGuard...", total=None)
                    self._setup_gitguard_integration(template_info)
                    progress.update(task, description="✅ GitGuard configured")
                
                # Step 9: Initial commit
                task = progress.add_task("📝 Creating initial commit...", total=None)
                self._create_initial_commit()
                progress.update(task, description="✅ Initial commit created")
            
            return {
                'success': True,
                'project_name': self.project_name,
                'project_path': str(self.project_path),
                'template': template_info['name'],
                'venv_created': self.bootstrap_state['venv_created'],
                'gitguard_enabled': self.bootstrap_state['gitguard_configured'],
                'security_level': self.security_level
            }
            
        except Exception as e:
            console.print(f"❌ Bootstrap failed: {e}", style="red")
            if self.verbose:
                import traceback
                traceback.print_exc()
            raise BootstrapError(f"Project bootstrap failed: {e}")
    
    def _validate_setup(self):
        """Validate bootstrap setup"""
        if self.dry_run:
            console.print("🔍 DRY RUN - Validation only")
            return
        
        # Check if project directory already exists
        if self.project_path.exists():
            raise BootstrapError(f"Project directory already exists: {self.project_path}")
        
        # Check if parent directory exists and is writable
        if not self.parent_path.exists():
            raise BootstrapError(f"Parent directory does not exist: {self.parent_path}")
        
        if not os.access(self.parent_path, os.W_OK):
            raise BootstrapError(f"Parent directory is not writable: {self.parent_path}")
        
        # Check if git is available
        try:
            subprocess.run(['git', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise BootstrapError("Git is not installed or not available in PATH")
        
        # Check if python is available (for venv)
        if self.setup_venv:
            try:
                subprocess.run([sys.executable, '--version'], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                raise BootstrapError("Python is not available for virtual environment setup")
    
    def _create_project_directory(self):
        """Create project directory"""
        if self.dry_run:
            console.print(f"Would create directory: {self.project_path}")
            return
        
        self.project_path.mkdir(parents=True, exist_ok=False)
        os.chdir(self.project_path)
        self.bootstrap_state['project_created'] = True
        
        if self.verbose:
            console.print(f"📁 Created project directory: {self.project_path}")
    
    def _process_template(self) -> Dict[str, Any]:
        """Process and prepare template"""
        if self.template == 'auto':
            # Auto-detect template based on context
            template_info = self.template_manager.detect_template()
        else:
            template_info = self.template_manager.get_template_info(self.template)
        
        if self.verbose:
            console.print(f"📋 Using template: {template_info['name']}")
            console.print(f"   Description: {template_info['description']}")
        
        return template_info
    
    def _setup_git_repository(self):
        """Initialize git repository"""
        if self.dry_run:
            console.print("Would initialize git repository")
            return
        
        try:
            # Initialize git repository
            subprocess.run(['git', 'init'], check=True, capture_output=True)
            
            # Set up git config if not already set
            self._setup_git_config()
            
            # Set up git hooks for GitGuard
            if self.setup_gitguard:
                self._setup_git_hooks()
            
            self.bootstrap_state['git_initialized'] = True
            
            if self.verbose:
                console.print("🔧 Git repository initialized")
                
        except subprocess.CalledProcessError as e:
            raise GitRepositoryError(f"Failed to initialize git repository: {e}")
    
    def _setup_git_config(self):
        """Set up git configuration"""
        try:
            # Check if user.name is set
            result = subprocess.run(
                ['git', 'config', 'user.name'], 
                capture_output=True, text=True
            )
            if result.returncode != 0:
                # Git config not set, would need user input in non-dry-run mode
                if self.verbose:
                    console.print("⚠️  Git user.name not set - would prompt for setup")
        except subprocess.CalledProcessError:
            pass
    
    def _setup_git_hooks(self):
        """Set up git hooks for GitGuard integration"""
        hooks_dir = Path('.git/hooks')
        hooks_dir.mkdir(exist_ok=True)
        
        # Pre-commit hook
        pre_commit_hook = hooks_dir / 'pre-commit'
        pre_commit_content = '''#!/bin/bash
# GitGuard pre-commit hook (installed by GitUp)
echo "🛡️  Running GitGuard security scan..."
gitguard scan --format text
if [ $? -ne 0 ]; then
    echo "❌ GitGuard found security issues. Fix them or use 'gitguard commit --auto-fix'"
    exit 1
fi
'''
        pre_commit_hook.write_text(pre_commit_content)
        pre_commit_hook.chmod(0o755)
        
        if self.verbose:
            console.print("🔗 Git hooks configured for GitGuard")
    
    def _setup_virtual_environment(self):
        """Set up Python virtual environment"""
        if self.dry_run:
            console.print("Would create Python virtual environment")
            return
        
        try:
            # Create virtual environment
            subprocess.run([sys.executable, '-m', 'venv', '.venv'], check=True)
            
            # Create activation helpers
            self._create_activation_helpers()
            
            self.bootstrap_state['venv_created'] = True
            
            if self.verbose:
                console.print("🐍 Virtual environment created")
                
        except subprocess.CalledProcessError as e:
            raise VirtualEnvironmentError(f"Failed to create virtual environment: {e}")
    
    def _create_activation_helpers(self):
        """Create environment activation helper scripts"""
        # Unix/Linux/macOS activation script
        activate_script = Path('activate_env.sh')
        activate_content = '''#!/bin/bash
# GitUp-generated environment activation script
source .venv/bin/activate
echo "✅ Virtual environment activated"
echo "💡 Use 'deactivate' to exit"
echo "🚀 Use 'gitup status' to check project status"
'''
        activate_script.write_text(activate_content)
        activate_script.chmod(0o755)
        
        # Windows activation script
        activate_bat = Path('activate_env.bat')
        activate_bat_content = '''@echo off
REM GitUp-generated environment activation script
call .venv\\Scripts\\activate.bat
echo ✅ Virtual environment activated
echo 💡 Use 'deactivate' to exit
echo 🚀 Use 'gitup status' to check project status
'''
        activate_bat.write_text(activate_bat_content)
    
    def _create_project_files(self, template_info: Dict[str, Any]):
        """Create project files from template"""
        if self.dry_run:
            console.print("Would create project files from template")
            return
        
        # Create .gitignore
        gitignore_content = template_info.get('gitignore', '')
        if gitignore_content:
            Path('.gitignore').write_text(gitignore_content)
        
        # Create requirements.txt for Python projects
        if 'python' in template_info.get('languages', []):
            dependencies = template_info.get('dependencies', [])
            if self.setup_gitguard:
                dependencies.append('gitguard>=1.0.2')
            
            requirements_content = '\\n'.join(dependencies)
            Path('requirements.txt').write_text(requirements_content)
        
        # Create basic project structure
        self._create_basic_structure(template_info)
        
        if self.verbose:
            console.print("📝 Project files created")
    
    def _create_basic_structure(self, template_info: Dict[str, Any]):
        """Create basic project structure"""
        # Create common directories
        directories = template_info.get('directories', ['src', 'tests', 'docs'])
        for dir_name in directories:
            Path(dir_name).mkdir(exist_ok=True)
        
        # Create main module file for Python projects
        if 'python' in template_info.get('languages', []):
            main_file = Path('src') / 'main.py'
            main_content = f'''#!/usr/bin/env python3
"""
{self.project_name} - Main Module
Generated by GitUp Bootstrap
"""

def main():
    """Main entry point"""
    print("Hello from {self.project_name}!")
    print("🚀 Project bootstrapped with GitUp")
    print("🛡️  Security provided by GitGuard")

if __name__ == "__main__":
    main()
'''
            main_file.write_text(main_content)
    
    def _install_dependencies(self, template_info: Dict[str, Any]):
        """Install project dependencies"""
        if self.dry_run:
            console.print("Would install dependencies")
            return
        
        if 'python' in template_info.get('languages', []):
            self._install_python_dependencies()
        
        self.bootstrap_state['dependencies_installed'] = True
        
        if self.verbose:
            console.print("📦 Dependencies installed")
    
    def _install_python_dependencies(self):
        """Install Python dependencies"""
        if not Path('requirements.txt').exists():
            return
        
        try:
            pip_executable = Path('.venv/bin/pip')
            if not pip_executable.exists():
                pip_executable = Path('.venv/Scripts/pip.exe')  # Windows
            
            subprocess.run([
                str(pip_executable), 
                'install', 
                '-r', 
                'requirements.txt'
            ], check=True)
            
        except subprocess.CalledProcessError as e:
            if self.verbose:
                console.print(f"⚠️  Failed to install dependencies: {e}")
    
    def _setup_gitguard_integration(self, template_info: Dict[str, Any]):
        """Set up GitGuard integration"""
        if self.dry_run:
            console.print("Would set up GitGuard integration")
            return
        
        try:
            self.gitguard_integration.setup_for_project(
                project_path=self.project_path,
                template_info=template_info,
                security_level=self.security_level
            )
            
            self.bootstrap_state['gitguard_configured'] = True
            
            if self.verbose:
                console.print("🛡️  GitGuard integration configured")
                
        except Exception as e:
            if self.verbose:
                console.print(f"⚠️  GitGuard setup failed: {e}")
    
    def _create_initial_commit(self):
        """Create initial git commit"""
        if self.dry_run:
            console.print("Would create initial commit")
            return
        
        try:
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run([
                'git', 'commit', '-m', 
                f'Initial commit - {self.project_name} (GitUp Bootstrap)'
            ], check=True)
            
            self.bootstrap_state['initial_commit_made'] = True
            
            if self.verbose:
                console.print("📝 Initial commit created")
                
        except subprocess.CalledProcessError as e:
            if self.verbose:
                console.print(f"⚠️  Failed to create initial commit: {e}")