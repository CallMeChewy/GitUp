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
from .core.ignore_manager import GitUpIgnoreManager
from .core.diff_interface import GitUpDiffInterface
from .core.metadata_manager import GitUpMetadataManager
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
    template_table = Table(show_header=True, header_style="bold magenta")
    template_table.add_column("Template", style="cyan", no_wrap=True)
    template_table.add_column("Description", style="white")
    template_table.add_column("Language", style="green")
    template_table.add_column("Security", style="yellow")
    
    for template in templates:
        template_table.add_row(
            template['name'],
            template['description'],
            template['language'],
            template['security_level']
        )
    
    console.print(template_table)
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

@cli.group()
def ignore():
    """Manage .gitupignore files and security patterns"""
    pass

@ignore.command('init')
@click.argument('project_path', default='.')
@click.option('--interactive', '-i', is_flag=True, help='Interactive mode')
@click.option('--security-level', '-s', default='medium', 
              type=click.Choice(['low', 'medium', 'high']), help='Security level')
@click.pass_context
def ignore_init(ctx, project_path: str, interactive: bool, security_level: str):
    """Initialize .gitupignore for existing project"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"🔍 Initializing .gitupignore for: {project_dir}")
        
        # Create diff interface
        diff_interface = GitUpDiffInterface(str(project_dir))
        
        if interactive:
            # Launch interactive review
            console.print("🚀 Launching interactive security review...")
            result = diff_interface.LaunchInteractiveReview()
            
            if result.get('success'):
                console.print("✅ .gitupignore system initialized successfully!")
                console.print(f"📝 Processed {result.get('decisions_count', 0)} security decisions")
                console.print("🔒 Your project is now more secure!")
            else:
                console.print(f"❌ Error: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            # Non-interactive mode - show overview only
            overview = diff_interface.ShowDiffOverview()
            
            if overview['diff_items']:
                console.print(f"🔍 Found {len(overview['diff_items'])} security recommendations")
                console.print("💡 Run 'gitup ignore init --interactive' to review and apply them")
            else:
                console.print("✅ No security issues found! Your .gitignore looks good.")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@ignore.command('status')
@click.argument('project_path', default='.')
@click.pass_context
def ignore_status(ctx, project_path: str):
    """Show current ignore status"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"📊 Checking ignore status for: {project_dir}")
        
        # Create ignore manager
        ignore_manager = GitUpIgnoreManager(str(project_dir))
        metadata_manager = GitUpMetadataManager(str(project_dir))
        
        # Get status
        status = ignore_manager.GetIgnoreStatus()
        statistics = metadata_manager.GetStatistics()
        
        # Show status table
        status_table = Table(show_header=True, header_style="bold magenta")
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="white")
        status_table.add_column("Details", style="green")
        
        status_table.add_row(
            ".gitignore",
            "✅ Exists" if status['gitignore_exists'] else "❌ Missing",
            "Standard ignore patterns"
        )
        
        status_table.add_row(
            ".gitupignore",
            "✅ Exists" if status['gitupignore_exists'] else "❌ Missing",
            "Security ignore patterns"
        )
        
        status_table.add_row(
            "User Decisions",
            f"{statistics['total_decisions']} decisions",
            f"{statistics['expired_decisions']} expired, {statistics['due_for_review']} due for review"
        )
        
        status_table.add_row(
            "Security Score",
            f"{statistics['security_score']:.1f}/100",
            f"Risk Level: {statistics['risk_level']}"
        )
        
        console.print(status_table)
        
        # Show recommendations if any
        if statistics['due_for_review'] > 0:
            console.print(f"⚠️  {statistics['due_for_review']} decisions are due for review")
            console.print("💡 Run 'gitup ignore review' to review them")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@ignore.command('review')
@click.argument('project_path', default='.')
@click.option('--pattern', '-p', help='Review specific pattern')
@click.pass_context
def ignore_review(ctx, project_path: str, pattern: str):
    """Review and modify ignore patterns"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"🔍 Reviewing ignore patterns for: {project_dir}")
        
        # Create diff interface
        diff_interface = GitUpDiffInterface(str(project_dir))
        
        if pattern:
            # Review specific pattern
            console.print(f"🔍 Reviewing pattern: {pattern}")
            # Implementation would review specific pattern
            console.print("🚧 Specific pattern review coming soon!")
        else:
            # Review all patterns
            console.print("🚀 Launching pattern review...")
            result = diff_interface.LaunchInteractiveReview()
            
            if result.get('success'):
                console.print("✅ Pattern review completed successfully!")
            else:
                console.print(f"❌ Error: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@ignore.command('add')
@click.argument('pattern')
@click.argument('project_path', default='.')
@click.option('--category', '-c', help='Pattern category')
@click.option('--reason', '-r', help='Reason for adding pattern')
@click.pass_context
def ignore_add(ctx, pattern: str, project_path: str, category: str, reason: str):
    """Add specific pattern to .gitupignore"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"➕ Adding pattern '{pattern}' to {project_dir}")
        
        # Create managers
        ignore_manager = GitUpIgnoreManager(str(project_dir))
        metadata_manager = GitUpMetadataManager(str(project_dir))
        
        # Add pattern
        decisions = {
            pattern: {
                'action': 'safe',
                'category': category or 'custom',
                'reason': reason or 'Manually added',
                'confidence': 1.0
            }
        }
        
        ignore_manager.ApplyUserDecisions(decisions)
        
        # Save metadata
        from .core.metadata_manager import DecisionType
        metadata_manager.AddUserDecision(
            Pattern=pattern,
            Decision=DecisionType.SAFE,
            Reason=reason or 'Manually added',
            Confidence=1.0
        )
        
        console.print(f"✅ Added pattern '{pattern}' to .gitupignore")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@ignore.command('remove')
@click.argument('pattern')
@click.argument('project_path', default='.')
@click.pass_context
def ignore_remove(ctx, pattern: str, project_path: str):
    """Remove pattern from .gitupignore"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"➖ Removing pattern '{pattern}' from {project_dir}")
        
        # Implementation would remove pattern
        console.print("🚧 Pattern removal coming soon!")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@ignore.command('audit')
@click.argument('project_path', default='.')
@click.option('--limit', '-l', default=20, help='Limit number of entries')
@click.pass_context
def ignore_audit(ctx, project_path: str, limit: int):
    """Show ignore decisions audit trail"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"📋 Showing audit trail for: {project_dir}")
        
        # Create metadata manager
        metadata_manager = GitUpMetadataManager(str(project_dir))
        
        # Get audit trail
        audit_entries = metadata_manager.GetAuditTrail(limit)
        
        if not audit_entries:
            console.print("📝 No audit entries found")
            return
        
        # Show audit table
        audit_table = Table(show_header=True, header_style="bold magenta")
        audit_table.add_column("Date", style="cyan")
        audit_table.add_column("Action", style="white")
        audit_table.add_column("User", style="green")
        audit_table.add_column("Details", style="yellow")
        
        for entry in audit_entries:
            details = entry.Details
            detail_str = f"Pattern: {details.get('pattern', 'N/A')}" if 'pattern' in details else str(details)
            
            audit_table.add_row(
                entry.Timestamp[:16],  # Show date/time without seconds
                entry.Action.value,
                entry.UserId,
                detail_str[:50] + "..." if len(detail_str) > 50 else detail_str
            )
        
        console.print(audit_table)
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

@ignore.command('update')
@click.argument('project_path', default='.')
@click.pass_context
def ignore_update(ctx, project_path: str):
    """Update security patterns"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"🔄 Updating security patterns for: {project_dir}")
        
        # Implementation would update patterns
        console.print("🚧 Pattern updates coming soon!")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)

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