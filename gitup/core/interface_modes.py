# File: interface_modes.py
# Path: gitup/core/interface_modes.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-17
# Last Modified: 2025-07-17  10:00PM
"""
GitUp Interface Modes - Multi-level user experience system.

This module provides adaptive interfaces for different user types:
- Hardcore Mode: Minimal output, maximum speed for experienced users
- Newbie Mode: Detailed guidance and educational content for beginners
- Standard Mode: Balanced approach for most users

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import os
from enum import Enum
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm


class InterfaceMode(Enum):
    """Interface mode enumeration"""
    HARDCORE = "hardcore"
    NEWBIE = "newbie"
    STANDARD = "standard"


class InterfaceModeManager:
    """
    Manages interface modes and provides adaptive UI components.
    
    This class detects the user's preferred interface mode and provides
    appropriate UI components, messaging, and interaction patterns.
    """
    
    def __init__(self):
        """Initialize interface mode manager"""
        self.mode = self._detect_mode()
        self.console = Console()
        
        # Mode-specific configurations
        self.configs = {
            InterfaceMode.HARDCORE: {
                "verbose": False,
                "colors": False,
                "explanations": False,
                "confirmations": False,
                "progress_bars": False,
                "tips": False,
                "emoji": False,
                "panels": False
            },
            InterfaceMode.NEWBIE: {
                "verbose": True,
                "colors": True,
                "explanations": True,
                "confirmations": True,
                "progress_bars": True,
                "tips": True,
                "emoji": True,
                "panels": True
            },
            InterfaceMode.STANDARD: {
                "verbose": True,
                "colors": True,
                "explanations": False,
                "confirmations": True,
                "progress_bars": True,
                "tips": False,
                "emoji": False,
                "panels": True
            }
        }
    
    def _detect_mode(self) -> InterfaceMode:
        """Detect interface mode from environment or configuration"""
        # Check environment variable first
        env_mode = os.getenv('GITUP_MODE', '').lower()
        
        if env_mode == 'hardcore':
            return InterfaceMode.HARDCORE
        elif env_mode == 'newbie':
            return InterfaceMode.NEWBIE
        else:
            return InterfaceMode.STANDARD
    
    def get_config(self, key: str) -> Any:
        """Get configuration value for current mode"""
        return self.configs[self.mode].get(key, False)
    
    def print_message(self, message: str, style: str = "", explanation: str = "") -> None:
        """Print message with mode-appropriate formatting"""
        if self.mode == InterfaceMode.HARDCORE:
            # Minimal output
            print(message.replace("🔍", "").replace("✅", "").replace("❌", "").strip())
        
        elif self.mode == InterfaceMode.NEWBIE:
            # Rich output with explanations
            if self.get_config("panels"):
                if explanation:
                    panel_content = f"{message}\n\n💡 {explanation}"
                else:
                    panel_content = message
                self.console.print(Panel(panel_content, style=style))
            else:
                self.console.print(message, style=style)
                if explanation:
                    self.console.print(f"💡 {explanation}", style="dim")
        
        else:  # STANDARD
            # Balanced output
            if self.get_config("panels") and style:
                self.console.print(Panel(message, style=style))
            else:
                self.console.print(message, style=style)
    
    def print_security_assessment(self, assessment: Dict[str, Any]) -> None:
        """Print security assessment with mode-appropriate formatting"""
        
        if self.mode == InterfaceMode.HARDCORE:
            # Minimal table
            print(f"RISKS: {assessment['total_risks']} | BLOCKING: {assessment['blocking_violations']}")
        
        elif self.mode == InterfaceMode.NEWBIE:
            # Educational detailed table
            table = Table(title="🔒 Security Assessment Results")
            table.add_column("Risk Level", style="bold")
            table.add_column("Count", justify="right")
            table.add_column("Status", justify="center")
            table.add_column("What This Means", style="dim")
            
            table.add_row("Critical", str(assessment.get('critical_risks', 0)), "🔴", "Must fix immediately")
            table.add_row("High", str(assessment.get('high_risks', 0)), "🟠", "Should fix soon")
            table.add_row("Medium", str(assessment.get('medium_risks', 0)), "🟡", "Consider fixing")
            table.add_row("Low", str(assessment.get('low_risks', 0)), "🔵", "Optional improvement")
            
            self.console.print(table)
            
            if assessment.get('blocking_violations', 0) > 0:
                self.console.print(Panel(
                    f"⚠️ GitUp found {assessment['blocking_violations']} security issues that need attention.\n\n"
                    "💡 Don't worry! GitUp will help you fix these safely. Most can be resolved by adding "
                    "files to .gitignore so they won't be committed to your repository.",
                    title="Security Issues Found",
                    style="red"
                ))
        
        else:  # STANDARD
            # Professional table
            table = Table(title="Security Assessment Summary")
            table.add_column("Risk Level", style="bold")
            table.add_column("Count", justify="right")
            table.add_column("Status", justify="center")
            
            table.add_row("Critical", str(assessment.get('critical_risks', 0)), "🔴")
            table.add_row("High", str(assessment.get('high_risks', 0)), "🟠")
            table.add_row("Medium", str(assessment.get('medium_risks', 0)), "🟡")
            table.add_row("Low", str(assessment.get('low_risks', 0)), "🔵")
            
            self.console.print(table)
    
    def get_user_choice(self, question: str, choices: List[str], default: str = None, 
                       explanations: Dict[str, str] = None) -> str:
        """Get user choice with mode-appropriate prompting"""
        
        if self.mode == InterfaceMode.HARDCORE:
            # Minimal prompt
            choice_str = "/".join(choices)
            if default:
                choice_str += f" [{default}]"
            return input(f"{question} ({choice_str}): ").strip() or default
        
        elif self.mode == InterfaceMode.NEWBIE:
            # Educational prompt with explanations
            self.console.print(f"\n[bold]{question}[/bold]")
            
            if explanations:
                for choice in choices:
                    explanation = explanations.get(choice, "")
                    self.console.print(f"  {choice}: {explanation}")
            else:
                for choice in choices:
                    self.console.print(f"  {choice}")
            
            if default:
                self.console.print(f"\n💡 Tip: Press Enter to select the default option: {default}")
            
            return Prompt.ask("Your choice", choices=choices, default=default)
        
        else:  # STANDARD
            # Standard prompt
            self.console.print(f"\n[bold]{question}[/bold]")
            for choice in choices:
                self.console.print(f"  {choice}")
            
            return Prompt.ask("Your choice", choices=choices, default=default)
    
    def confirm_action(self, message: str, default: bool = False, 
                      explanation: str = "") -> bool:
        """Get user confirmation with mode-appropriate messaging"""
        
        if self.mode == InterfaceMode.HARDCORE:
            # Skip confirmations unless critical
            if "remove" in message.lower() or "delete" in message.lower():
                return input(f"{message} (y/N): ").lower().startswith('y')
            return True
        
        elif self.mode == InterfaceMode.NEWBIE:
            # Educational confirmation
            if explanation:
                self.console.print(f"💡 {explanation}")
            return Confirm.ask(message, default=default)
        
        else:  # STANDARD
            # Standard confirmation
            return Confirm.ask(message, default=default)
    
    def show_tip(self, tip: str) -> None:
        """Show tip if appropriate for current mode"""
        if self.get_config("tips"):
            self.console.print(f"💡 [dim]Tip: {tip}[/dim]")
    
    def show_progress(self, description: str):
        """Show progress indicator if appropriate for current mode"""
        if self.get_config("progress_bars"):
            # Return progress context for Rich progress bars
            from rich.progress import Progress, SpinnerColumn, TextColumn
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            )
        else:
            # Simple text for hardcore mode
            if self.mode == InterfaceMode.HARDCORE:
                print(f"{description}...")
            return None


# Global instance
interface_manager = InterfaceModeManager()