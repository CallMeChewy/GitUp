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
import time
import click
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

try:
    from . import __version__
    from .core.bootstrap import ProjectBootstrap
    from .core.templates import TemplateManager
    from .core.ignore_manager import GitUpIgnoreManager
    from .core.diff_interface import GitUpDiffInterface
    from .core.metadata_manager import GitUpMetadataManager
    from .core.project_state_detector import ProjectStateDetector
    from .core.gitup_project_manager import GitUpProjectManager
    from .core.security_interface import SecurityReviewInterface, SecurityConfigInterface, SecurityDashboard
    from .core.terminal_interface import launch_security_review_tui
    from .utils.exceptions import GitUpError, SecurityViolationError
except ImportError:
    # Handle case when running as compiled binary
    __version__ = "2.1.0-tv955-fusion"
    from gitup.core.bootstrap import ProjectBootstrap
    from gitup.core.templates import TemplateManager
    from gitup.core.ignore_manager import GitUpIgnoreManager
    from gitup.core.diff_interface import GitUpDiffInterface
    from gitup.core.metadata_manager import GitUpMetadataManager
    from gitup.core.project_state_detector import ProjectStateDetector
    from gitup.core.gitup_project_manager import GitUpProjectManager
    from gitup.core.security_interface import SecurityReviewInterface, SecurityConfigInterface, SecurityDashboard
    from gitup.core.terminal_interface import launch_security_review_tui
    from gitup.utils.exceptions import GitUpError, SecurityViolationError

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
        
        # Create project manager
        manager = GitUpProjectManager(str(project_dir), verbose=ctx.obj['verbose'])
        
        # Get project status
        status_info = manager.get_project_status()
        
        if not status_info["initialized"]:
            console.print("❌ Not a GitUp project")
            console.print("💡 Run 'gitup init' to initialize GitUp for this project")
            console.print("💡 Run 'gitup bootstrap' to create a new project")
            return
        
        # Show project status
        console.print("🚀 GitUp Project Status")
        console.print(f"   → GitUp directory: {status_info['gitup_dir']}")
        
        # Show analysis summary
        analysis = status_info.get("project_analysis", {})
        if analysis:
            console.print(f"   → Project state: {analysis.get('state', 'unknown')}")
            console.print(f"   → Risk level: {analysis.get('risk_level', 'unknown')}")
            console.print(f"   → Setup complexity: {analysis.get('setup_complexity', 'unknown')}")
        
        # Show current configuration
        config = status_info.get("current_config", {})
        if config:
            console.print(f"   → Security level: {config.get('security_level', 'unknown')}")
            console.print(f"   → Template type: {config.get('template_type', 'none')}")
        
        # Show compliance status
        compliance = status_info.get("compliance_status", {})
        if compliance:
            console.print(f"   → Compliance: {compliance.get('status', 'unknown')}")
        
        # Show file status
        files = status_info.get("files_status", {})
        if files:
            console.print("\n📁 GitUp Files:")
            for file_type, exists in files.items():
                status_icon = "✅" if exists else "❌"
                console.print(f"   → {file_type}: {status_icon}")
        
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
@click.argument('project_path', default='.')
@click.option('--existing', is_flag=True, help='Initialize for existing project')
@click.option('--scan-history', is_flag=True, help='Scan git history for security issues')
@click.option('--minimal', is_flag=True, help='Minimal setup with basic protection')
@click.option('--force', is_flag=True, help='Force initialization even if .gitup exists')
@click.pass_context
def init(ctx, project_path: str, existing: bool, scan_history: bool, minimal: bool, force: bool):
    """Initialize GitUp for a project"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"🔧 Initializing GitUp for project: {project_dir}")
        
        # Create project manager
        manager = GitUpProjectManager(str(project_dir), verbose=ctx.obj['verbose'])
        
        # Check if already initialized
        if not force and (project_dir / ".gitup").exists():
            console.print("⚠️  GitUp already initialized for this project")
            console.print("💡 Use --force to reinitialize")
            return
        
        # Migrate legacy files if they exist
        legacy_gitupignore = project_dir / ".gitupignore"
        legacy_meta = project_dir / ".gitupignore.meta"
        
        if legacy_gitupignore.exists() or legacy_meta.exists():
            console.print("🔄 Found legacy GitUp files, migrating...")
            migration_result = manager.migrate_legacy_files()
            if migration_result["status"] == "success":
                console.print("✅ Legacy files migrated successfully")
                for file_path in migration_result["files_migrated"]:
                    console.print(f"   → {file_path}")
            else:
                console.print("❌ Migration failed:")
                for error in migration_result["errors"]:
                    console.print(f"   → {error}")
        
        # Initialize project
        result = manager.initialize_project(force=force)
        
        if result["status"] == "already_initialized":
            console.print("✅ Project already initialized")
        elif result["status"] == "initialized":
            console.print("🎉 GitUp initialized successfully!")
            console.print(f"   → .gitup directory: {result['gitup_dir']}")
            
            # Show analysis summary
            analysis = result.get("analysis", {})
            if analysis:
                console.print(f"   → Project state: {analysis.get('state', 'unknown')}")
                console.print(f"   → Risk level: {analysis.get('risk_level', 'unknown')}")
                console.print(f"   → Security level: {analysis.get('recommended_security_level', 'moderate')}")
        
        # Run security review if initialized
        if result["status"] == "initialized":
            console.print("\n🔍 Running security review...")
            try:
                # Get security level from result
                analysis = result.get("analysis", {})
                security_level = analysis.get("recommended_security_level", "moderate")
                
                # Create security review interface
                review_interface = SecurityReviewInterface(str(project_dir), security_level)
                
                # Run non-interactive security review
                review_result = review_interface.run_security_review(interactive=False)
                
                if review_result["status"] == "violations_detected":
                    console.print(f"⚠️  Security violations detected!")
                    console.print(f"   → Blocking violations: {review_result['blocking_violations']}")
                    console.print(f"   → Total risks: {review_result['total_risks']}")
                    console.print("\n🚫 GitUp operations will be blocked until violations are resolved!")
                    console.print("   → Run 'gitup security review' to launch full-screen security review")
                    
                    # Ask if user wants to launch security review now
                    from rich.prompt import Confirm
                    if Confirm.ask("\nWould you like to launch the security review now?"):
                        console.print("\n🚀 Launching full-screen security review...")
                        time.sleep(1)
                        tui_result = launch_security_review_tui(str(project_dir), security_level)
                        
                        if tui_result["status"] == "completed":
                            console.print(f"\n✅ Security review completed!")
                            console.print(f"   → Resolved: {tui_result['risks_resolved']}/{tui_result['total_risks']} risks")
                        elif tui_result["status"] == "cancelled":
                            console.print(f"\n⚠️  Security review cancelled - violations remain active")
                elif review_result["status"] == "clean":
                    console.print("✅ No security risks detected!")
                else:
                    console.print(f"ℹ️  {review_result['total_risks']} security risks found (warnings only)")
                
            except Exception as e:
                console.print(f"⚠️  Security review failed: {e}")
        
        # Show next steps
        console.print("\n💡 Next steps:")
        console.print("   → Run 'gitup status' to check project status")
        console.print("   → Run 'gitup security dashboard' to view security overview")
        console.print("   → Run 'gitup compliance-check' to verify security compliance")
        
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
@click.argument('project_path', default='.')
@click.option('--detailed', '-d', is_flag=True, help='Show detailed analysis')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
@click.pass_context
def analyze(ctx, project_path: str, detailed: bool, output_json: bool):
    """Analyze project state and provide setup recommendations"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"🔍 Analyzing project: {project_dir}")
        
        # Create detector and analyze
        detector = ProjectStateDetector(str(project_dir), verbose=ctx.obj['verbose'])
        analysis = detector.analyze_project()
        
        if output_json:
            # Output JSON format
            import json
            from dataclasses import asdict
            
            # Convert enums to strings for JSON serialization
            analysis_dict = asdict(analysis)
            analysis_dict['state'] = analysis.state.value
            analysis_dict['risk_level'] = analysis.risk_level.value
            analysis_dict['setup_complexity'] = analysis.setup_complexity.value
            
            console.print(json.dumps(analysis_dict, indent=2))
            return
        
        # Show analysis results
        _show_project_analysis(analysis, detailed)
        
        # Show recommendations
        recommendations = detector.get_recommendations(analysis)
        _show_project_recommendations(recommendations)
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"💥 Unexpected error: {e}", style="red")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
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

@cli.command()
@click.argument('project_path', default='.')
@click.pass_context
def compliance_check(ctx, project_path: str):
    """Run comprehensive compliance check"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"🔍 Running compliance check: {project_dir}")
        
        # Create project manager
        manager = GitUpProjectManager(str(project_dir), verbose=ctx.obj['verbose'])
        
        # Check if GitUp is initialized
        if not (project_dir / ".gitup").exists():
            console.print("❌ GitUp not initialized for this project")
            console.print("💡 Run 'gitup init' to initialize GitUp")
            return
        
        console.print("🔍 Running compliance check...")
        
        # Run compliance check
        compliance_results = manager.run_compliance_check()
        
        # Show results
        console.print(f"\n📊 Compliance Check Results")
        console.print(f"   → Overall Status: {compliance_results['overall_status']}")
        console.print(f"   → Timestamp: {compliance_results['timestamp']}")
        
        # Show security analysis
        security = compliance_results.get("security_analysis", {})
        if security:
            console.print(f"\n🔒 Security Analysis:")
            console.print(f"   → Risk Level: {security.get('risk_level', 'unknown')}")
            console.print(f"   → Potential Secrets: {security.get('potential_secrets', 0)}")
            console.print(f"   → Sensitive Files: {security.get('sensitive_files', 0)}")
            console.print(f"   → Large Files: {security.get('large_files', 0)}")
        
        # Show file compliance
        file_compliance = compliance_results.get("file_compliance", {})
        if file_compliance:
            console.print(f"\n📁 File Compliance:")
            for check, status in file_compliance.items():
                status_icon = "✅" if status else "❌"
                console.print(f"   → {check}: {status_icon}")
        
        # Show git compliance
        git_compliance = compliance_results.get("git_compliance", {})
        if git_compliance:
            console.print(f"\n📦 Git Compliance:")
            for check, status in git_compliance.items():
                status_icon = "✅" if status else "❌"
                console.print(f"   → {check}: {status_icon}")
        
        # Show recent audit entries
        audit_entries = compliance_results.get("audit_trail", [])
        if audit_entries:
            console.print(f"\n📜 Recent Audit Entries:")
            for entry in audit_entries[-3:]:  # Show last 3 entries
                console.print(f"   → {entry.get('timestamp', 'unknown')}: {entry.get('operation', 'unknown')}")
        
        # Show recommendations based on status
        if compliance_results['overall_status'] == "RISK_DETECTED":
            console.print("\n⚠️  Recommendations:")
            console.print("   → Review and secure potential secret files")
            console.print("   → Run 'gitup ignore init --interactive' to update ignore patterns")
        elif compliance_results['overall_status'] == "PARTIAL_COMPLIANCE":
            console.print("\n💡 Recommendations:")
            console.print("   → Run 'gitup ignore init' to complete setup")
            console.print("   → Consider updating security level if needed")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"💥 Unexpected error: {e}", style="red")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
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

def _show_project_analysis(analysis, detailed: bool):
    """Show project analysis results"""
    from .core.project_state_detector import ProjectStateDetector
    
    detector = ProjectStateDetector()
    state_summary = detector.get_state_summary(analysis)
    
    # Main analysis panel
    console.print()
    console.print(Panel.fit(
        f"📊 Project Analysis: {Path(analysis.path).name}",
        style="blue bold"
    ))
    
    # Basic info table
    info_table = Table(show_header=True, header_style="bold magenta")
    info_table.add_column("Attribute", style="cyan")
    info_table.add_column("Value", style="white")
    info_table.add_column("Status", style="green")
    
    # Project state
    info_table.add_row("Project State", state_summary, "✅" if analysis.has_git else "⚠️")
    
    # Risk level with color coding
    risk_color = "red" if analysis.risk_level.value == "high_risk" else \
                 "yellow" if analysis.risk_level.value == "medium_risk" else "green"
    info_table.add_row("Risk Level", analysis.risk_level.value.replace("_", " ").title(), f"[{risk_color}]●[/]")
    
    # Setup complexity
    info_table.add_row("Setup Complexity", analysis.setup_complexity.value.replace("_", " ").title(), "")
    
    # Security recommendation
    info_table.add_row("Recommended Security", analysis.recommended_security_level.title(), "")
    
    console.print(info_table)
    
    # Show file counts
    console.print(f"\n📁 Files: {analysis.file_count} total")
    if analysis.has_git:
        console.print(f"📝 Commits: {analysis.commit_count}")
        if analysis.days_since_creation > 0:
            console.print(f"📅 Age: {analysis.days_since_creation} days")
    
    # Show detailed analysis if requested
    if detailed:
        console.print("\n🔍 Detailed Analysis:")
        
        # Git information
        git_table = Table(show_header=True, header_style="bold magenta")
        git_table.add_column("Git Feature", style="cyan")
        git_table.add_column("Status", style="white")
        
        git_table.add_row("Repository", "✅ Yes" if analysis.has_git else "❌ No")
        git_table.add_row("GitIgnore", "✅ Yes" if analysis.has_gitignore else "❌ No")
        git_table.add_row("GitHub Remote", "✅ Yes" if analysis.has_github_remote else "❌ No")
        git_table.add_row("GitHub Actions", "✅ Yes" if analysis.has_github_actions else "❌ No")
        
        console.print(git_table)
        
        # Security findings
        if analysis.potential_secrets or analysis.sensitive_files or analysis.large_files:
            console.print("\n🔒 Security Findings:")
            
            if analysis.potential_secrets:
                console.print(f"⚠️  Potential Secrets ({len(analysis.potential_secrets)}):")
                for secret in analysis.potential_secrets[:5]:  # Show first 5
                    console.print(f"   • {secret}")
                if len(analysis.potential_secrets) > 5:
                    console.print(f"   ... and {len(analysis.potential_secrets) - 5} more")
            
            if analysis.sensitive_files:
                console.print(f"🔐 Sensitive Files ({len(analysis.sensitive_files)}):")
                for sensitive in analysis.sensitive_files[:3]:  # Show first 3
                    console.print(f"   • {sensitive}")
                if len(analysis.sensitive_files) > 3:
                    console.print(f"   ... and {len(analysis.sensitive_files) - 3} more")
            
            if analysis.large_files:
                console.print(f"📦 Large Files ({len(analysis.large_files)}):")
                for large in analysis.large_files[:3]:  # Show first 3
                    console.print(f"   • {large}")
                if len(analysis.large_files) > 3:
                    console.print(f"   ... and {len(analysis.large_files) - 3} more")
    
    # Show warnings
    if analysis.setup_warnings:
        console.print("\n⚠️  Setup Warnings:")
        for warning in analysis.setup_warnings:
            console.print(f"   {warning}")
    
    console.print(f"\n⏱️  Analysis completed in {analysis.analysis_duration_ms}ms")

def _show_project_recommendations(recommendations):
    """Show project recommendations"""
    console.print()
    console.print(Panel.fit(
        "🎯 Recommendations",
        style="green bold"
    ))
    
    # Templates
    if recommendations["templates"]:
        console.print("📋 Recommended Templates:")
        for template in recommendations["templates"]:
            console.print(f"   • {template}")
    
    # Security
    console.print(f"\n🔒 Security Level: {recommendations['security_level']}")
    console.print(f"🔧 Setup Complexity: {recommendations['setup_complexity'].replace('_', ' ').title()}")
    
    # Immediate actions
    if recommendations["immediate_actions"]:
        console.print("\n⚡ Immediate Actions:")
        for action in recommendations["immediate_actions"]:
            console.print(f"   1. {action}")
    
    # Long-term actions
    if recommendations["long_term_actions"]:
        console.print("\n🚀 Long-term Actions:")
        for action in recommendations["long_term_actions"]:
            console.print(f"   • {action}")
    
    console.print("\n💡 Next Steps:")
    console.print("   • Run 'gitup bootstrap <project-name>' to create new project")
    console.print("   • Run 'gitup upgrade' to enhance existing project")
    console.print("   • Run 'gitup ignore init --interactive' for security review")

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

@cli.group()
def security():
    """Security management commands"""
    pass

@security.command('review')
@click.argument('project_path', default='.')
@click.option('--interactive/--no-interactive', '-i', default=True, help='Interactive review mode')
@click.option('--auto-fix', is_flag=True, help='Automatically fix common issues')
@click.pass_context
def security_review(ctx, project_path: str, interactive: bool, auto_fix: bool):
    """Run comprehensive security review"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"🔍 Running security review: {project_dir}")
        
        # Check if GitUp is initialized
        if not (project_dir / ".gitup").exists():
            console.print("❌ GitUp not initialized for this project")
            console.print("💡 Run 'gitup init' to initialize GitUp")
            return
        
        # Get current security level
        manager = GitUpProjectManager(str(project_dir))
        status = manager.get_project_status()
        security_level = status.get("current_config", {}).get("security_level", "moderate")
        
        # Run security review
        if interactive:
            # Launch full-screen terminal interface
            result = launch_security_review_tui(str(project_dir), security_level)
        else:
            # Use Rich console interface for non-interactive
            review_interface = SecurityReviewInterface(str(project_dir), security_level)
            result = review_interface.run_security_review(interactive=False)
        
        # Show results
        if result["status"] == "clean":
            console.print("✅ Security review completed - no risks detected!")
        elif result["status"] == "completed":
            console.print(f"✅ Security review completed!")
            console.print(f"   → Resolved: {result['risks_resolved']}/{result['total_risks']} risks")
        elif result["status"] == "violations_detected":
            console.print(f"⚠️  Security violations detected!")
            console.print(f"   → Blocking violations: {result['blocking_violations']}")
            console.print(f"   → Total risks: {result['total_risks']}")
            console.print("   → Run 'gitup security review --interactive' to resolve")
        
    except SecurityViolationError as e:
        console.print(f"🚫 Security violation: {e}", style="red")
        console.print("Run 'gitup security review' to address violations")
        sys.exit(1)
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"💥 Unexpected error: {e}", style="red")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@security.command('config')
@click.argument('project_path', default='.')
@click.pass_context
def security_config(ctx, project_path: str):
    """Configure security settings"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"⚙️  Configuring security: {project_dir}")
        
        # Check if GitUp is initialized
        if not (project_dir / ".gitup").exists():
            console.print("❌ GitUp not initialized for this project")
            console.print("💡 Run 'gitup init' to initialize GitUp")
            return
        
        # Create security config interface
        config_interface = SecurityConfigInterface(str(project_dir))
        
        # Configure security level
        new_level = config_interface.configure_security_level()
        
        # Configure global exceptions
        from rich.prompt import Confirm
        if Confirm.ask("Would you like to configure global exceptions?"):
            exceptions = config_interface.configure_global_exceptions()
            console.print(f"✅ Configured {len(exceptions)} global exceptions")
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"💥 Unexpected error: {e}", style="red")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)

@security.command('dashboard')
@click.argument('project_path', default='.')
@click.pass_context
def security_dashboard(ctx, project_path: str):
    """Show security dashboard"""
    try:
        project_dir = Path(project_path).resolve()
        
        if ctx.obj['verbose']:
            console.print(f"📊 Security dashboard: {project_dir}")
        
        # Check if GitUp is initialized
        if not (project_dir / ".gitup").exists():
            console.print("❌ GitUp not initialized for this project")
            console.print("💡 Run 'gitup init' to initialize GitUp")
            return
        
        # Create and show dashboard
        dashboard = SecurityDashboard(str(project_dir))
        dashboard.show_dashboard()
        
    except GitUpError as e:
        console.print(f"❌ Error: {e}", style="red")
        sys.exit(1)
    except Exception as e:
        console.print(f"💥 Unexpected error: {e}", style="red")
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()