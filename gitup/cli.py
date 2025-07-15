#!/usr/bin/env python3
# File: cli.py
# Path: gitup/cli.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:05PM
"""
GitUp Command Line Interface
Main entry point for GitUp CLI commands - Enhanced project bootstrap tool.

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import sys
import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .core.bootstrap import ProjectBootstrap
from .core.templates import TemplateManager
from .utils.exceptions import GitUpError

console = Console()

@click.group()
@click.version_option(__version__)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, verbose: bool):
    """
    🚀 GitUp - Enhanced Project Bootstrap Tool
    Part of Project Himalaya - AI-Human Collaborative Development
    
    One-command project setup with GitGuard security integration.
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

@cli.command()
@click.argument('project_name')
@click.option('--template', '-t', default='auto', help='Project template to use')
@click.option('--path', '-p', default='.', help='Parent directory for project')
@click.option('--security', '-s', default='medium', 
              type=click.Choice(['low', 'medium', 'high']), help='Security level')
@click.option('--no-venv', is_flag=True, help='Skip virtual environment setup')
@click.option('--no-gitguard', is_flag=True, help='Skip GitGuard integration')
@click.option('--dry-run', is_flag=True, help='Show what would be done without doing it')
@click.pass_context
def bootstrap(ctx, project_name: str, template: str, path: str, security: str, 
              no_venv: bool, no_gitguard: bool, dry_run: bool):
    """Bootstrap a new project with complete setup"""
    try:
        if ctx.obj['verbose']:
            console.print(f"🚀 Bootstrapping project: {project_name}")
            console.print(f"📋 Template: {template}")
            console.print(f"🔒 Security level: {security}")
        
        # Create bootstrap instance
        bootstrap_config = {
            'project_name': project_name,
            'template': template,
            'parent_path': path,
            'security_level': security,
            'setup_venv': not no_venv,
            'setup_gitguard': not no_gitguard,
            'dry_run': dry_run,
            'verbose': ctx.obj['verbose']
        }
        
        bootstrapper = ProjectBootstrap(**bootstrap_config)
        
        if dry_run:
            console.print("🔍 DRY RUN - No changes will be made")
            console.print()
            
        # Run the bootstrap process
        result = bootstrapper.run()
        
        if dry_run:
            console.print("✅ Dry run completed successfully!")
            console.print("Use without --dry-run to actually create the project")
        else:
            # Show success message
            _show_bootstrap_success(result)
            
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"💥 Unexpected error: {e}", style="red")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@cli.command()
@click.option('--all', 'show_all', is_flag=True, help='Show all available templates')
@click.option('--template', '-t', help='Show details for specific template')
@click.pass_context
def templates(ctx, show_all: bool, template: Optional[str]):
    """List available project templates"""
    try:
        template_manager = TemplateManager()
        
        if template:
            # Show specific template details
            template_info = template_manager.get_template_info(template)
            _show_template_details(template_info)
        else:
            # List all templates
            available_templates = template_manager.list_templates()
            _show_template_list(available_templates, show_all)
            
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@cli.command()
@click.argument('project_path', default='.')
@click.option('--gitignore-only', is_flag=True, help='Only update .gitignore')
@click.option('--security-only', is_flag=True, help='Only update security settings')
@click.pass_context
def upgrade(ctx, project_path: str, gitignore_only: bool, security_only: bool):
    """Upgrade existing project to use GitUp enhancements"""
    try:
        if ctx.obj['verbose']:
            console.print(f"🔧 Upgrading project: {project_path}")
        
        # Implementation would go here
        console.print("🚧 Upgrade functionality coming soon!")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@cli.command()
@click.argument('project_path', default='.')
@click.pass_context
def status(ctx, project_path: str):
    """Show GitUp project status"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"📊 Checking project status: {project_dir}")
        
        # Check if it's a GitUp project
        gitup_config = project_dir / '.gitup.yaml'
        if not gitup_config.exists():
            console.print("❌ Not a GitUp project")
            console.print("💡 Run 'gitup bootstrap' to create a new project")
            console.print("💡 Run 'gitup upgrade' to upgrade existing project")
            return
        
        # Implementation would show:
        # - GitUp version used
        # - Template used
        # - Security status
        # - GitGuard integration status
        # - Virtual environment status
        
        console.print("🚧 Status functionality coming soon!")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@cli.group()
def config():
    """Configuration management commands"""
    pass

@config.command('show')
@click.argument('project_path', default='.')
@click.pass_context
def config_show(ctx, project_path: str):
    """Show current project configuration"""
    try:
        console.print("🚧 Config show functionality coming soon!")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

def _show_bootstrap_success(result):
    """Show bootstrap success message"""
    console.print()
    console.print(Panel.fit(
        "🎉 PROJECT BOOTSTRAP COMPLETE!",
        style="green bold"
    ))
    
    console.print(f"📁 Project: {result['project_name']}")
    console.print(f"🔗 Location: {result['project_path']}")
    console.print(f"📋 Template: {result['template']}")
    console.print()
    
    console.print("🚀 Next Steps:")
    console.print("1. Navigate to project: cd " + result['project_name'])
    if result.get('venv_created'):
        console.print("2. Activate environment: source .venv/bin/activate")
    console.print("3. Start coding!")
    console.print("4. Use 'gitguard commit' for secure commits")
    console.print()
    
    console.print("💡 Quick Commands:")
    console.print("   gitup status        # Check project status")
    console.print("   gitguard scan       # Security scan")
    console.print("   gitguard commit -m  # Secure commit")

def _show_template_list(templates, show_all: bool):
    """Show list of available templates"""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Template", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Language", style="green")
    table.add_column("Security", style="yellow")
    
    for template in templates:
        table.add_row(
            template['name'],
            template['description'],
            template['language'],
            template['security_level']
        )
    
    console.print(table)
    console.print()
    console.print("💡 Use 'gitup bootstrap my-project template-name' to create a project")
    console.print("💡 Use 'gitup templates --template=name' for template details")

def _show_template_details(template_info):
    """Show detailed template information"""
    console.print(Panel.fit(
        f"📋 Template: {template_info['name']}",
        style="blue bold"
    ))
    
    console.print(f"Description: {template_info['description']}")
    console.print(f"Language: {template_info['language']}")
    console.print(f"Security Level: {template_info['security_level']}")
    console.print()
    
    console.print("Dependencies:")
    for dep in template_info.get('dependencies', []):
        console.print(f"  • {dep}")
    
    console.print()
    console.print("Features:")
    for feature in template_info.get('features', []):
        console.print(f"  ✅ {feature}")

def main():
    """Main entry point for GitUp CLI"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n👋 GitUp interrupted by user")
        sys.exit(130)
    except Exception as e:
        console.print(f"💥 Unexpected error: {e}", style="red")
        sys.exit(1)

if __name__ == '__main__':
    main()