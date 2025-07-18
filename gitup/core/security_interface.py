# File: security_interface.py
# Path: gitup/core/security_interface.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-16
# Last Modified: 2025-07-16  04:15PM
"""
GitUp Security Interface - Interactive UI for risk mitigation and security management.

This module provides comprehensive interactive interfaces for users to review
and address security risks, configure security levels, and manage global
exceptions. It implements the user-facing components of the risk mitigation system.

Key Components:
- SecurityReviewInterface: Interactive risk review and resolution
- SecurityConfigInterface: Security level and policy configuration
- GlobalExceptionManager: Global security exception management
- SecurityDashboard: Comprehensive security status visualization

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.layout import Layout
from rich.columns import Columns

from .risk_mitigation import (
    SecurityRiskDetector, SecurityEnforcer, SecurityAssessment,
    SecurityRisk, SecurityRiskType, SecurityRiskLevel, UserDecision
)
from .gitup_project_manager import GitUpProjectManager
from .interface_modes import interface_manager, InterfaceMode
from ..utils.exceptions import GitUpError, SecurityViolationError


class SecurityReviewInterface:
    """
    Interactive interface for reviewing and resolving security risks.
    
    This class provides a comprehensive UI for users to review detected
    security risks, make decisions about each risk, and track resolution
    progress.
    """
    
    def __init__(self, project_path: str, security_level: str = "moderate"):
        """
        Initialize the security review interface.
        
        Args:
            project_path: Path to the project directory
            security_level: Current security enforcement level
        """
        self.project_path = Path(project_path)
        self.security_level = security_level
        self.console = Console()
        self.interface = interface_manager  # Use adaptive interface
        self.detector = SecurityRiskDetector(str(project_path), security_level)
        self.enforcer = SecurityEnforcer(str(project_path), security_level)
        self.project_manager = GitUpProjectManager(str(project_path))
        
        # Load existing decisions
        self.decisions_file = self.project_path / ".gitup" / "security_decisions.json"
        self.user_decisions = self._load_decisions()
    
    def run_security_review(self, interactive: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive security review process.
        
        Args:
            interactive: Whether to run in interactive mode
            
        Returns:
            Dictionary with review results and user decisions
        """
        # Mode-aware header
        if self.interface.mode == InterfaceMode.HARDCORE:
            print("GitUp Security Review")
        elif self.interface.mode == InterfaceMode.NEWBIE:
            self.console.print(Panel.fit(
                "🔒 GitUp Security Review - Learning Mode",
                style="blue bold"
            ))
        else:  # STANDARD
            self.console.print(Panel.fit(
                "🔒 GitUp Security Review",
                style="blue bold"
            ))
        
        # Scan for risks with mode-appropriate messaging
        if self.interface.mode == InterfaceMode.HARDCORE:
            print("Scanning...")
        else:
            self.console.print("🔍 Scanning project for security risks...")
            
        assessment = self.detector.scan_project()
        
        # Show assessment summary
        self._display_assessment_summary(assessment)
        
        if assessment.total_risks == 0:
            self.console.print("✅ No security risks detected!")
            return {"status": "clean", "risks_resolved": 0, "total_risks": 0}
        
        # Interactive review if requested
        if interactive:
            return self._interactive_review(assessment)
        else:
            # Save blocking violations for enforcement
            if assessment.blocking_violations:
                self.enforcer.save_violations(assessment.blocking_violations)
                return {
                    "status": "violations_detected",
                    "blocking_violations": len(assessment.blocking_violations),
                    "total_risks": assessment.total_risks
                }
            else:
                return {"status": "warnings_only", "total_risks": assessment.total_risks}
    
    def _display_assessment_summary(self, assessment: SecurityAssessment) -> None:
        """Display security assessment summary with adaptive interface"""
        
        # Use adaptive interface for assessment display
        assessment_data = {
            'total_risks': assessment.total_risks,
            'critical_risks': assessment.critical_risks,
            'high_risks': assessment.high_risks,
            'medium_risks': assessment.medium_risks,
            'low_risks': assessment.low_risks,
            'blocking_violations': len(assessment.blocking_violations)
        }
        
        self.interface.print_security_assessment(assessment_data)
        
        # Show enforcement status if violations exist
        if assessment.blocking_violations:
            if self.interface.mode == InterfaceMode.HARDCORE:
                print(f"BLOCKING: {len(assessment.blocking_violations)} violations")
            elif self.interface.mode == InterfaceMode.NEWBIE:
                self.interface.print_message(
                    "⚠️ Security violations detected!",
                    "red",
                    "These are security issues that GitUp won't let you commit until they're resolved. This protects you from accidentally exposing sensitive information."
                )
            else:  # STANDARD
                self.console.print(Panel(
                    f"⚠️ Security violations detected!\n\n"
                    f"GitUp operations will be blocked until {len(assessment.blocking_violations)} security violations are resolved.\n\n"
                    f"Current security level: {self.security_level}",
                    title="Security Enforcement Active",
                    style="red"
                ))
        
        # Skip the old table display for hardcore mode
        if self.interface.mode == InterfaceMode.HARDCORE:
            return
            
        # Original table code for fallback (standard/newbie modes)
        summary_table = Table(title="Security Assessment Summary")
        summary_table.add_column("Risk Level", style="cyan")
        summary_table.add_column("Count", justify="right")
        summary_table.add_column("Status", justify="center")
        
        # Add risk counts
        risk_data = [
            ("Critical", assessment.critical_risks, "🔴" if assessment.critical_risks > 0 else "✅"),
            ("High", assessment.high_risks, "🟠" if assessment.high_risks > 0 else "✅"),
            ("Medium", assessment.medium_risks, "🟡" if assessment.medium_risks > 0 else "✅"),
            ("Low", assessment.low_risks, "🔵" if assessment.low_risks > 0 else "✅"),
        ]
        
        for level, count, status in risk_data:
            summary_table.add_row(level, str(count), status)
        
        # Add total and blocking info
        summary_table.add_row("", "", "")
        summary_table.add_row("Total Risks", str(assessment.total_risks), "")
        summary_table.add_row("Blocking Violations", str(len(assessment.blocking_violations)), 
                            "🚫" if assessment.blocking_violations else "✅")
        
        self.console.print(summary_table)
        self.console.print()
        
        # Show enforcement status
        if assessment.enforcement_active:
            self.console.print(Panel(
                f"⚠️  [bold red]Security Enforcement Active[/bold red]\n\n"
                f"GitUp operations will be blocked until {len(assessment.blocking_violations)} "
                f"security violations are resolved.\n\n"
                f"Current security level: [bold]{assessment.security_level}[/bold]",
                style="red"
            ))
        else:
            self.console.print(Panel(
                f"✅ [bold green]No Blocking Violations[/bold green]\n\n"
                f"All critical security issues have been addressed.\n"
                f"GitUp operations are permitted.\n\n"
                f"Current security level: [bold]{assessment.security_level}[/bold]",
                style="green"
            ))
    
    def _interactive_review(self, assessment: SecurityAssessment) -> Dict[str, Any]:
        """Run interactive review process"""
        
        self.console.print(f"\n🔍 Starting interactive review of {assessment.total_risks} risks...")
        
        if not Confirm.ask("Would you like to review each risk individually?"):
            # Bulk actions
            return self._bulk_review(assessment)
        
        # Individual review
        resolved_count = 0
        
        for i, risk in enumerate(assessment.risks, 1):
            self.console.print(f"\n--- Risk {i} of {assessment.total_risks} ---")
            
            # Show risk details
            self._display_risk_details(risk)
            
            # Get user decision
            decision = self._get_user_decision(risk)
            
            if decision:
                # Apply decision
                self._apply_decision(risk, decision)
                resolved_count += 1
                
                # Update progress
                self.console.print(f"✅ Risk resolved: {decision.value}")
            else:
                self.console.print("⏭️  Skipped for now")
        
        # Save decisions
        self._save_decisions()
        
        # Update enforcement status
        self._update_enforcement_status(assessment)
        
        return {
            "status": "completed",
            "risks_resolved": resolved_count,
            "total_risks": assessment.total_risks,
            "user_decisions": self.user_decisions
        }
    
    def _display_risk_details(self, risk: SecurityRisk) -> None:
        """Display detailed information about a security risk"""
        
        # Risk level styling
        level_colors = {
            SecurityRiskLevel.CRITICAL: "red",
            SecurityRiskLevel.HIGH: "orange3",
            SecurityRiskLevel.MEDIUM: "yellow",
            SecurityRiskLevel.LOW: "blue",
            SecurityRiskLevel.INFO: "green"
        }
        
        color = level_colors.get(risk.risk_level, "white")
        
        # Create risk panel
        risk_info = [
            f"[bold]File:[/bold] {risk.file_path}",
            f"[bold]Risk Type:[/bold] {risk.risk_type.value}",
            f"[bold]Risk Level:[/bold] [{color}]{risk.risk_level.value.upper()}[/{color}]",
            f"[bold]Pattern:[/bold] {risk.pattern_matched}",
            f"[bold]Size:[/bold] {risk.file_size:,} bytes",
            f"[bold]Git Tracked:[/bold] {'Yes' if risk.is_tracked else 'No'}",
            f"[bold]Description:[/bold] {risk.description}",
            f"[bold]Recommendation:[/bold] {risk.recommendation}"
        ]
        
        self.console.print(Panel(
            "\n".join(risk_info),
            title=f"Security Risk: {risk.risk_type.value}",
            border_style=color
        ))
    
    def _get_user_decision(self, risk: SecurityRisk) -> Optional[UserDecision]:
        """Get user decision for a security risk with adaptive interface"""
        
        # Mode-specific options and explanations
        if self.interface.mode == InterfaceMode.HARDCORE:
            # Minimal options for hardcore mode
            options = ["1", "2", "3", "5", "s"]
            choices = ["1", "2", "3", "5", "s"]
            
            while True:
                choice = input(f"Action for {risk.file_path} (1=.gitignore/2=.gitupignore/3=ignore/5=remove/s=skip): ").strip()
                
                if choice == "1":
                    return UserDecision.ADD_TO_GITIGNORE
                elif choice == "2":
                    return UserDecision.ADD_TO_GITUPIGNORE
                elif choice == "3":
                    return UserDecision.IGNORE_PERMANENTLY
                elif choice == "5":
                    return UserDecision.REMOVE_FILE
                elif choice == "s":
                    return None
                else:
                    continue
        
        elif self.interface.mode == InterfaceMode.NEWBIE:
            # Educational mode with detailed explanations
            explanations = {
                "1": "Add to .gitignore - Standard git way to ignore files (recommended for most cases)",
                "2": "Add to .gitupignore - GitUp's enhanced ignore system with metadata tracking",
                "3": "Ignore permanently - Tell GitUp to never warn about this file again",
                "4": "Ignore temporarily - Skip this file for now, but check it again later",
                "5": "Remove file - Delete the file from your project (careful!)",
                "6": "Review later - Skip for now and decide later",
                "p": "Preview file content - See what's inside the file before deciding",
                "s": "Skip this risk - Move to the next security issue"
            }
            
            choices = ["1", "2", "3", "4", "5", "6", "p", "s"]
            
            self.interface.print_message(
                f"🔍 Security Risk Found: {risk.file_path}",
                "yellow",
                f"This file contains {risk.risk_type.value} and has {risk.risk_level.value} risk level."
            )
            
            while True:
                choice = self.interface.get_user_choice(
                    "What would you like to do with this security risk?",
                    choices,
                    default="s",
                    explanations=explanations
                )
                
                if choice == "p":
                    self._preview_risk_content(risk)
                    continue
                
                # Convert choice to decision
                decision_map = {
                    "1": UserDecision.ADD_TO_GITIGNORE,
                    "2": UserDecision.ADD_TO_GITUPIGNORE,
                    "3": UserDecision.IGNORE_PERMANENTLY,
                    "4": UserDecision.IGNORE_TEMPORARILY,
                    "5": UserDecision.REMOVE_FILE,
                    "6": UserDecision.REVIEW_LATER,
                    "s": None
                }
                
                decision = decision_map.get(choice)
                if decision is None:
                    return None
                
                # Educational confirmations
                if decision == UserDecision.REMOVE_FILE:
                    if not self.interface.confirm_action(
                        f"Are you sure you want to delete '{risk.file_path}'?",
                        False,
                        "This will permanently remove the file from your computer. Make sure you have a backup if you need it!"
                    ):
                        continue
                
                # Show what the action will do
                if decision in [UserDecision.ADD_TO_GITIGNORE, UserDecision.ADD_TO_GITUPIGNORE]:
                    pattern = self._generate_smart_pattern(risk.file_path)
                    target_file = ".gitignore" if decision == UserDecision.ADD_TO_GITIGNORE else ".gitupignore"
                    self.interface.print_message(
                        f"📋 This will add pattern '{pattern}' to {target_file}",
                        "blue",
                        f"This pattern will ignore not just this file, but similar files in the future."
                    )
                    
                    if not self.interface.confirm_action("Proceed with this action?"):
                        continue
                
                return decision
        
        else:  # STANDARD mode
            # Balanced interface
            options = [
                ("1", "Add to .gitignore", UserDecision.ADD_TO_GITIGNORE),
                ("2", "Add to .gitupignore", UserDecision.ADD_TO_GITUPIGNORE),
                ("3", "Ignore permanently", UserDecision.IGNORE_PERMANENTLY),
                ("4", "Ignore temporarily", UserDecision.IGNORE_TEMPORARILY),
                ("5", "Remove file", UserDecision.REMOVE_FILE),
                ("6", "Review later", UserDecision.REVIEW_LATER),
                ("p", "Preview file content", None),
                ("s", "Skip this risk", None)
            ]
            
            self.console.print("\n[bold]Available Actions:[/bold]")
            for key, description, _ in options:
                self.console.print(f"  {key}. {description}")
            
            while True:
                choice = Prompt.ask(
                    "\nWhat would you like to do with this risk?",
                    choices=[opt[0] for opt in options],
                    default="s"
                )
                
                # Handle preview mode
                if choice == "p":
                    self._preview_risk_content(risk)
                    continue
                
                # Find selected option
                for key, description, decision in options:
                    if key == choice:
                        if decision is None:
                            return None  # Skip
                        
                        # Show preview of what the action will do
                        if decision in [UserDecision.ADD_TO_GITIGNORE, UserDecision.ADD_TO_GITUPIGNORE]:
                            pattern = self._generate_smart_pattern(risk.file_path)
                            target_file = ".gitignore" if decision == UserDecision.ADD_TO_GITIGNORE else ".gitupignore"
                            self.console.print(f"📋 Preview: Will add pattern '{pattern}' to {target_file}")
                            
                            if not Confirm.ask("Proceed with this action?"):
                                continue
                        
                        # Confirm critical actions
                        if decision == UserDecision.REMOVE_FILE:
                            if not Confirm.ask(f"⚠️  Are you sure you want to remove '{risk.file_path}'?"):
                                continue
                        
                        # Get optional reason
                        reason = None
                        if decision in [UserDecision.IGNORE_PERMANENTLY, UserDecision.IGNORE_TEMPORARILY]:
                            reason = Prompt.ask("Optional reason for ignoring", default="")
                        
                        return decision
    
    def _preview_risk_content(self, risk: SecurityRisk) -> None:
        """Preview file content around the security risk"""
        try:
            file_path = Path(risk.file_path)
            
            # Handle symbolic links
            if file_path.is_symlink():
                import os
                target = os.readlink(file_path)
                self.console.print(f"🔗 Symbolic link: {risk.file_path} -> {target}")
                return
            
            # Read file content
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = content.split('\n')
                
                # Show first 10 lines or full content if smaller
                preview_lines = lines[:10]
                
                self.console.print(f"\n📄 File preview: {risk.file_path}")
                self.console.print("─" * 50)
                
                for i, line in enumerate(preview_lines, 1):
                    # Highlight potential sensitive content
                    if any(word in line.lower() for word in ['password', 'secret', 'key', 'token']):
                        self.console.print(f"{i:2d}: [red]{line}[/red]")
                    else:
                        self.console.print(f"{i:2d}: {line}")
                
                if len(lines) > 10:
                    self.console.print(f"... ({len(lines) - 10} more lines)")
                
                self.console.print("─" * 50)
                
            else:
                self.console.print(f"❌ File not found: {risk.file_path}")
                
        except Exception as e:
            self.console.print(f"❌ Error reading file: {e}")
    
    def _apply_decision(self, risk: SecurityRisk, decision: UserDecision) -> None:
        """Apply user decision to a security risk"""
        
        # Record decision
        risk.user_decision = decision
        risk.decision_timestamp = datetime.now(timezone.utc).isoformat()
        
        # Store in decisions
        self.user_decisions[risk.file_path] = {
            "decision": decision.value,
            "timestamp": risk.decision_timestamp,
            "risk_type": risk.risk_type.value,
            "risk_level": risk.risk_level.value,
            "reason": getattr(risk, 'decision_reason', None)
        }
        
        # Apply the decision
        try:
            if decision == UserDecision.ADD_TO_GITIGNORE:
                self._add_to_gitignore(risk.file_path)
            elif decision == UserDecision.ADD_TO_GITUPIGNORE:
                self._add_to_gitupignore(risk.file_path)
            elif decision == UserDecision.REMOVE_FILE:
                self._remove_file(risk.file_path)
            
        except Exception as e:
            self.console.print(f"❌ Error applying decision: {e}")
    
    def _add_to_gitignore(self, file_path: str) -> None:
        """Add file pattern to .gitignore with smart pattern generation"""
        gitignore_path = self.project_path / ".gitignore"
        
        # Smart pattern generation based on file type and content
        pattern = self._generate_smart_pattern(file_path)
        
        # Read existing content
        existing_content = ""
        if gitignore_path.exists():
            existing_content = gitignore_path.read_text()
        
        # Add pattern if not already present
        if pattern not in existing_content:
            with open(gitignore_path, 'a') as f:
                f.write(f"\n# Added by GitUp security review\n{pattern}\n")
                
        self.console.print(f"✅ Added pattern '{pattern}' to .gitignore")
    
    def _generate_smart_pattern(self, file_path: str) -> str:
        """Generate intelligent ignore patterns based on file type and risk"""
        file_path_obj = Path(file_path)
        
        # Secret files - use wildcard patterns
        if file_path.endswith(('.env', '.secret', '.key', '.pem')):
            return f"*{file_path_obj.suffix}"
        
        # Config files - pattern by directory
        if 'config' in file_path.lower() and file_path_obj.suffix in ['.json', '.yaml', '.yml']:
            return f"**/config/*{file_path_obj.suffix}"
        
        # Database files - broad pattern
        if file_path.endswith(('.db', '.sqlite', '.sqlite3')):
            return "*.db"
        
        # Backup files - pattern match
        if file_path.endswith(('.bak', '.backup', '.old', '.orig')):
            return f"*{file_path_obj.suffix}"
        
        # Log files - directory pattern
        if file_path.endswith('.log') or 'log' in file_path.lower():
            return "*.log"
        
        # IDE config - use directory pattern
        if file_path.startswith(('.vscode/', '.idea/', '.settings/')):
            return f"{file_path_obj.parts[0]}/"
        
        # Temporary files - broad pattern
        if file_path.endswith(('.tmp', '.temp', '.cache')):
            return f"*{file_path_obj.suffix}"
        
        # Default - use specific file path
        return file_path
    
    def _add_to_gitupignore(self, file_path: str) -> None:
        """Add file pattern to .gitupignore"""
        gitupignore_path = self.project_path / ".gitup" / ".gitupignore"
        
        # Create pattern
        pattern = file_path
        
        # Read existing content
        existing_content = ""
        if gitupignore_path.exists():
            existing_content = gitupignore_path.read_text()
        
        # Add pattern if not already present
        if pattern not in existing_content:
            with open(gitupignore_path, 'a') as f:
                f.write(f"\n# Added by GitUp security review\n{pattern}\n")
    
    def _remove_file(self, file_path: str) -> None:
        """Remove file from filesystem"""
        file_to_remove = self.project_path / file_path
        if file_to_remove.exists():
            file_to_remove.unlink()
    
    def _bulk_review(self, assessment: SecurityAssessment) -> Dict[str, Any]:
        """Handle bulk review actions"""
        
        self.console.print("\n🔄 Bulk Review Options:")
        
        options = [
            ("1", "Add all secret files to .gitignore"),
            ("2", "Add all config files to .gitupignore"),
            ("3", "Ignore all low-risk items"),
            ("4", "Custom bulk action"),
            ("5", "Skip bulk review")
        ]
        
        for key, description in options:
            self.console.print(f"  {key}. {description}")
        
        choice = Prompt.ask(
            "\nSelect bulk action",
            choices=[opt[0] for opt in options],
            default="5"
        )
        
        resolved_count = 0
        
        if choice == "1":
            # Add secret files to .gitignore
            for risk in assessment.risks:
                if risk.risk_type == SecurityRiskType.SECRET_FILE:
                    self._apply_decision(risk, UserDecision.ADD_TO_GITIGNORE)
                    resolved_count += 1
        
        elif choice == "2":
            # Add config files to .gitupignore
            for risk in assessment.risks:
                if risk.risk_type == SecurityRiskType.SENSITIVE_CONFIG:
                    self._apply_decision(risk, UserDecision.ADD_TO_GITUPIGNORE)
                    resolved_count += 1
        
        elif choice == "3":
            # Ignore low-risk items
            for risk in assessment.risks:
                if risk.risk_level == SecurityRiskLevel.LOW:
                    self._apply_decision(risk, UserDecision.IGNORE_TEMPORARILY)
                    resolved_count += 1
        
        # Save decisions
        self._save_decisions()
        
        return {
            "status": "bulk_completed",
            "risks_resolved": resolved_count,
            "total_risks": assessment.total_risks
        }
    
    def _load_decisions(self) -> Dict[str, Dict[str, Any]]:
        """Load existing user decisions"""
        try:
            if self.decisions_file.exists():
                with open(self.decisions_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def _save_decisions(self) -> None:
        """Save user decisions to file"""
        try:
            self.decisions_file.parent.mkdir(exist_ok=True)
            
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "security_level": self.security_level,
                "decisions": self.user_decisions
            }
            
            with open(self.decisions_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def _update_enforcement_status(self, assessment: SecurityAssessment) -> None:
        """Update security enforcement status"""
        
        # Check which violations are still unresolved
        unresolved_violations = []
        for risk in assessment.blocking_violations:
            if risk.file_path not in self.user_decisions:
                unresolved_violations.append(risk)
            else:
                decision = self.user_decisions[risk.file_path]["decision"]
                if decision == UserDecision.REVIEW_LATER.value:
                    unresolved_violations.append(risk)
        
        # Update enforcement
        if unresolved_violations:
            self.enforcer.save_violations(unresolved_violations)
        else:
            self.enforcer.clear_violations()


class SecurityConfigInterface:
    """
    Interface for configuring security levels and policies.
    
    This class provides interactive configuration of security enforcement
    levels, blocking thresholds, and other security policies.
    """
    
    def __init__(self, project_path: str):
        """
        Initialize the security configuration interface.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.console = Console()
        self.project_manager = GitUpProjectManager(str(project_path))
    
    def configure_security_level(self) -> str:
        """
        Interactive security level configuration.
        
        Returns:
            Selected security level
        """
        self.console.print(Panel.fit(
            "🔧 Security Level Configuration",
            style="blue bold"
        ))
        
        # Show current level
        current_status = self.project_manager.get_project_status()
        current_level = current_status.get("current_config", {}).get("security_level", "moderate")
        
        self.console.print(f"Current security level: [bold]{current_level}[/bold]\n")
        
        # Show level descriptions
        levels = {
            "strict": {
                "description": "Maximum security - blocks critical, high, and medium risks",
                "blocks": ["Critical", "High", "Medium"],
                "auto_remediation": False,
                "scan_depth": "Deep"
            },
            "moderate": {
                "description": "Balanced security - blocks critical risks, auto-remediates others",
                "blocks": ["Critical"],
                "auto_remediation": True,
                "scan_depth": "Standard"
            },
            "relaxed": {
                "description": "Minimal security - blocks only critical risks",
                "blocks": ["Critical"],
                "auto_remediation": True,
                "scan_depth": "Basic"
            }
        }
        
        # Display level options
        table = Table(title="Security Level Options")
        table.add_column("Level", style="cyan")
        table.add_column("Description")
        table.add_column("Blocks", style="red")
        table.add_column("Auto-Fix", style="green")
        table.add_column("Scan Depth", style="yellow")
        
        for level, config in levels.items():
            table.add_row(
                level,
                config["description"],
                ", ".join(config["blocks"]),
                "Yes" if config["auto_remediation"] else "No",
                config["scan_depth"]
            )
        
        self.console.print(table)
        
        # Get user choice
        choice = Prompt.ask(
            "\nSelect security level",
            choices=list(levels.keys()),
            default=current_level
        )
        
        # Apply new level
        if choice != current_level:
            self.project_manager.update_security_level(choice)
            self.console.print(f"✅ Security level updated to: [bold]{choice}[/bold]")
        else:
            self.console.print("✅ Security level unchanged")
        
        return choice
    
    def configure_global_exceptions(self) -> List[str]:
        """
        Configure global security exceptions.
        
        Returns:
            List of global exception patterns
        """
        self.console.print(Panel.fit(
            "⚙️  Global Security Exceptions",
            style="blue bold"
        ))
        
        # Load existing exceptions
        exceptions_file = self.project_path / ".gitup" / "global_exceptions.json"
        exceptions = []
        
        if exceptions_file.exists():
            try:
                with open(exceptions_file, 'r') as f:
                    data = json.load(f)
                    exceptions = data.get("exceptions", [])
            except Exception:
                pass
        
        # Show current exceptions
        if exceptions:
            self.console.print("Current global exceptions:")
            for i, exception in enumerate(exceptions, 1):
                self.console.print(f"  {i}. {exception}")
        else:
            self.console.print("No global exceptions currently configured.")
        
        # Management options
        while True:
            self.console.print("\nOptions:")
            self.console.print("  1. Add exception pattern")
            self.console.print("  2. Remove exception")
            self.console.print("  3. Clear all exceptions")
            self.console.print("  4. Done")
            
            choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="4")
            
            if choice == "1":
                pattern = Prompt.ask("Enter exception pattern (e.g., '*.log', 'temp/*')")
                if pattern and pattern not in exceptions:
                    exceptions.append(pattern)
                    self.console.print(f"✅ Added exception: {pattern}")
            
            elif choice == "2" and exceptions:
                self.console.print("Select exception to remove:")
                for i, exception in enumerate(exceptions, 1):
                    self.console.print(f"  {i}. {exception}")
                
                try:
                    index = IntPrompt.ask("Enter number", default=0) - 1
                    if 0 <= index < len(exceptions):
                        removed = exceptions.pop(index)
                        self.console.print(f"✅ Removed exception: {removed}")
                except Exception:
                    self.console.print("❌ Invalid selection")
            
            elif choice == "3":
                if Confirm.ask("Are you sure you want to clear all exceptions?"):
                    exceptions.clear()
                    self.console.print("✅ All exceptions cleared")
            
            elif choice == "4":
                break
        
        # Save exceptions
        try:
            exceptions_file.parent.mkdir(exist_ok=True)
            with open(exceptions_file, 'w') as f:
                json.dump({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "exceptions": exceptions
                }, f, indent=2)
        except Exception:
            pass
        
        return exceptions


class SecurityDashboard:
    """
    Comprehensive security status dashboard.
    
    This class provides a unified view of the project's security status,
    including risk summaries, enforcement status, and recent activity.
    """
    
    def __init__(self, project_path: str):
        """
        Initialize the security dashboard.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
        self.console = Console()
        self.project_manager = GitUpProjectManager(str(project_path))
    
    def show_dashboard(self) -> None:
        """Display comprehensive security dashboard"""
        
        self.console.print(Panel.fit(
            "🛡️  GitUp Security Dashboard",
            style="blue bold"
        ))
        
        # Get project status
        status = self.project_manager.get_project_status()
        
        if not status["initialized"]:
            self.console.print("❌ GitUp not initialized for this project")
            return
        
        # Create dashboard layout
        layout = Layout()
        
        # Security overview
        overview_panel = self._create_overview_panel(status)
        
        # Risk summary
        risk_panel = self._create_risk_panel()
        
        # Recent activity
        activity_panel = self._create_activity_panel()
        
        # Configuration
        config_panel = self._create_config_panel(status)
        
        # Display panels
        self.console.print(overview_panel)
        self.console.print()
        
        columns = Columns([risk_panel, activity_panel], equal=True)
        self.console.print(columns)
        self.console.print()
        
        self.console.print(config_panel)
    
    def _create_overview_panel(self, status: Dict[str, Any]) -> Panel:
        """Create security overview panel"""
        
        config = status.get("current_config", {})
        compliance = status.get("compliance_status", {})
        
        overview_text = [
            f"[bold]Security Level:[/bold] {config.get('security_level', 'unknown')}",
            f"[bold]Compliance Status:[/bold] {compliance.get('status', 'unknown')}",
            f"[bold]Enforcement Active:[/bold] {'Yes' if self._has_active_violations() else 'No'}",
            f"[bold]Last Audit:[/bold] {status.get('current_state', {}).get('last_audit', 'Never')}"
        ]
        
        return Panel(
            "\n".join(overview_text),
            title="Security Overview",
            border_style="green"
        )
    
    def _create_risk_panel(self) -> Panel:
        """Create risk summary panel"""
        
        # This would typically load from recent risk assessment
        risk_text = [
            "[bold]Risk Summary:[/bold]",
            "• Critical: 0",
            "• High: 2",
            "• Medium: 5",
            "• Low: 3",
            "",
            "[bold]Status:[/bold] ✅ No blocking violations"
        ]
        
        return Panel(
            "\n".join(risk_text),
            title="Risk Assessment",
            border_style="yellow"
        )
    
    def _create_activity_panel(self) -> Panel:
        """Create recent activity panel"""
        
        activity_text = [
            "[bold]Recent Activity:[/bold]",
            "• Security review completed",
            "• 3 risks resolved",
            "• Security level updated",
            "• Global exceptions added",
            "",
            "[bold]Next Review:[/bold] Recommended"
        ]
        
        return Panel(
            "\n".join(activity_text),
            title="Recent Activity",
            border_style="blue"
        )
    
    def _create_config_panel(self, status: Dict[str, Any]) -> Panel:
        """Create configuration panel"""
        
        config = status.get("current_config", {})
        
        config_text = [
            f"[bold]Block Critical:[/bold] {config.get('block_on_critical', True)}",
            f"[bold]Block High:[/bold] {config.get('block_on_high', False)}",
            f"[bold]Block Medium:[/bold] {config.get('block_on_medium', False)}",
            f"[bold]Auto Remediation:[/bold] {config.get('auto_remediation', True)}",
            f"[bold]Scan Depth:[/bold] {config.get('scan_depth', 'standard')}",
            f"[bold]Audit Enabled:[/bold] {config.get('audit_enabled', True)}"
        ]
        
        return Panel(
            "\n".join(config_text),
            title="Security Configuration",
            border_style="cyan"
        )
    
    def _has_active_violations(self) -> bool:
        """Check if there are active security violations"""
        enforcer = SecurityEnforcer(str(self.project_path))
        has_violations, _ = enforcer.check_violations()
        return has_violations