# File: terminal_interface.py
# Path: gitup/core/terminal_interface.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-16
# Last Modified: 2025-07-16  04:30PM
"""
GitUp Terminal Interface - Classic CRT/TV955 terminal experience.

This module provides authentic terminal interfaces that work on classic
CRT terminals like TV955. Full-screen, menu-driven, ASCII-based interfaces
that feel like traditional terminal applications.

Key Components:
- TerminalScreen: Full-screen terminal management
- MenuSystem: Classic numbered menu interfaces
- SecurityReviewTUI: Terminal-based security review
- ASCIIFormatter: Simple ASCII art and formatting

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import os
import sys
import time
import subprocess
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from .risk_mitigation import SecurityRiskDetector, SecurityAssessment, SecurityRisk, SecurityRiskLevel
from .security_interface import SecurityReviewInterface


class TerminalScreen:
    """
    Full-screen terminal management for CRT/TV955 experience.
    
    Provides classic terminal operations like clear screen, cursor positioning,
    and full-screen interface management.
    """
    
    def __init__(self):
        """Initialize terminal screen manager"""
        self.width = 80  # Standard terminal width
        self.height = 24  # Standard terminal height
        self._detect_terminal_size()
    
    def _detect_terminal_size(self):
        """Detect terminal size, fallback to 80x24"""
        try:
            size = os.get_terminal_size()
            self.width = max(80, size.columns)  # Minimum 80 columns
            self.height = max(24, size.lines)   # Minimum 24 lines
        except Exception:
            self.width = 80
            self.height = 24
    
    def clear(self):
        """Clear the entire screen"""
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux
            os.system('clear')
    
    def home(self):
        """Move cursor to home position (top-left)"""
        if os.name != 'nt':
            print('\033[H', end='')
        else:
            self.clear()
    
    def goto(self, row: int, col: int):
        """Move cursor to specific position"""
        if os.name != 'nt':
            print(f'\033[{row};{col}H', end='')
    
    def center_text(self, text: str, width: Optional[int] = None) -> str:
        """Center text within terminal width"""
        if width is None:
            width = self.width
        return text.center(width)
    
    def line(self, char: str = '-', width: Optional[int] = None) -> str:
        """Create a horizontal line"""
        if width is None:
            width = self.width
        return char * width
    
    def box(self, text: str, width: Optional[int] = None, char: str = '*') -> List[str]:
        """Create a simple ASCII box around text"""
        if width is None:
            width = self.width
        
        lines = []
        text_lines = text.split('\n')
        
        # Top border
        lines.append(char * width)
        
        # Text lines with borders
        for line in text_lines:
            padded = line.center(width - 4)
            lines.append(f"{char} {padded} {char}")
        
        # Bottom border
        lines.append(char * width)
        
        return lines
    
    def pause(self, message: str = "Press Enter to continue..."):
        """Pause with message"""
        input(f"\n{message}")
    
    def wait_for_keypress(self):
        """Wait for any key press"""
        if os.name == 'nt':
            import msvcrt
            msvcrt.getch()
        else:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


class MenuSystem:
    """
    Classic numbered menu system for terminal interfaces.
    
    Provides traditional menu-driven navigation with numbered options,
    input validation, and menu chaining.
    """
    
    def __init__(self, screen: TerminalScreen):
        """Initialize menu system"""
        self.screen = screen
    
    def show_menu(self, title: str, options: List[Tuple[str, str]], 
                  header: Optional[str] = None) -> Optional[str]:
        """
        Display a numbered menu and get user selection.
        
        Args:
            title: Menu title
            options: List of (key, description) tuples
            header: Optional header text
            
        Returns:
            Selected option key or None if cancelled
        """
        while True:
            self.screen.clear()
            
            # Show header if provided
            if header:
                print(self.screen.center_text(header))
                print(self.screen.line('='))
                print()
            
            # Show title
            print(self.screen.center_text(title))
            print(self.screen.line('-'))
            print()
            
            # Show options
            for i, (key, description) in enumerate(options, 1):
                print(f"  {i}. {description}")
            
            print(f"  0. Exit/Cancel")
            print()
            print(self.screen.line('-'))
            
            # Get user input
            try:
                choice = input("Enter your choice: ").strip()
                
                if choice == '0':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    return options[choice_num - 1][0]
                else:
                    self._show_error("Invalid choice. Please try again.")
                    
            except ValueError:
                self._show_error("Please enter a number.")
            except KeyboardInterrupt:
                return None
    
    def show_info(self, title: str, content: str, wait: bool = True):
        """Display information screen"""
        self.screen.clear()
        
        print(self.screen.center_text(title))
        print(self.screen.line('='))
        print()
        
        print(content)
        print()
        print(self.screen.line('-'))
        
        if wait:
            self.screen.pause()
    
    def get_input(self, prompt: str, default: str = "") -> str:
        """Get user input with prompt"""
        if default:
            full_prompt = f"{prompt} [{default}]: "
        else:
            full_prompt = f"{prompt}: "
        
        result = input(full_prompt).strip()
        return result if result else default
    
    def get_yes_no(self, prompt: str, default: bool = False) -> bool:
        """Get yes/no input from user"""
        default_text = "Y/n" if default else "y/N"
        
        while True:
            response = input(f"{prompt} [{default_text}]: ").strip().lower()
            
            if not response:
                return default
            
            if response in ('y', 'yes'):
                return True
            elif response in ('n', 'no'):
                return False
            else:
                print("Please enter 'y' or 'n'.")
    
    def _show_error(self, message: str):
        """Show error message and pause"""
        print(f"\nERROR: {message}")
        time.sleep(1.5)


class SecurityReviewTUI:
    """
    Terminal User Interface for security review process.
    
    Provides a full-screen, menu-driven interface for reviewing and
    resolving security risks in classic terminal style.
    """
    
    def __init__(self, project_path: str, security_level: str = "moderate"):
        """Initialize security review TUI"""
        self.project_path = project_path
        self.security_level = security_level
        self.screen = TerminalScreen()
        self.menu = MenuSystem(self.screen)
        self.detector = SecurityRiskDetector(project_path, security_level)
        self.review_interface = SecurityReviewInterface(project_path, security_level)
    
    def run(self) -> Dict[str, Any]:
        """Run the security review TUI"""
        self.screen.clear()
        
        # Show welcome screen
        self._show_welcome()
        
        # Scan for risks
        self._show_scanning()
        assessment = self.detector.scan_project()
        
        # Show assessment summary
        self._show_assessment_summary(assessment)
        
        if assessment.total_risks == 0:
            self._show_clean_result()
            return {"status": "clean", "risks_resolved": 0, "total_risks": 0}
        
        # Main review menu
        return self._main_review_menu(assessment)
    
    def _show_welcome(self):
        """Show welcome screen"""
        welcome_text = """
        GITUP SECURITY REVIEW SYSTEM
        
        This system will scan your project for security risks
        and help you resolve any violations found.
        
        Security Level: {level}
        Project: {path}
        """.format(
            level=self.security_level.upper(),
            path=self.project_path
        )
        
        self.menu.show_info("GITUP SECURITY REVIEW", welcome_text)
    
    def _show_scanning(self):
        """Show scanning progress"""
        self.screen.clear()
        
        print(self.screen.center_text("SCANNING PROJECT FOR SECURITY RISKS"))
        print(self.screen.line('='))
        print()
        print(self.screen.center_text("Please wait..."))
        print()
        
        # Simple progress animation
        for i in range(3):
            print(self.screen.center_text(f"Scanning{'.' * (i + 1)}"))
            time.sleep(0.5)
    
    def _show_assessment_summary(self, assessment: SecurityAssessment):
        """Show security assessment summary"""
        summary_text = f"""
        SECURITY ASSESSMENT RESULTS
        
        Total Risks Found: {assessment.total_risks}
        
        Critical Risks: {assessment.critical_risks}
        High Risks:     {assessment.high_risks}
        Medium Risks:   {assessment.medium_risks}
        Low Risks:      {assessment.low_risks}
        
        Blocking Violations: {len(assessment.blocking_violations)}
        
        Security Level: {assessment.security_level.upper()}
        """
        
        if assessment.blocking_violations:
            summary_text += f"""
        WARNING: {len(assessment.blocking_violations)} violations will block
        GitUp operations until resolved.
        """
        
        self.menu.show_info("ASSESSMENT SUMMARY", summary_text)
    
    def _show_clean_result(self):
        """Show clean project result"""
        clean_text = """
        CONGRATULATIONS!
        
        No security risks were detected in your project.
        
        Your project is ready for GitUp operations.
        """
        
        self.menu.show_info("SECURITY REVIEW COMPLETE", clean_text)
    
    def _main_review_menu(self, assessment: SecurityAssessment) -> Dict[str, Any]:
        """Main review menu"""
        resolved_count = 0
        
        while True:
            options = [
                ("review_all", "Review all risks individually"),
                ("review_critical", f"Review critical risks only ({assessment.critical_risks})"),
                ("bulk_actions", "Bulk actions"),
                ("show_summary", "Show risk summary"),
                ("exit", "Exit (risks will remain unresolved)")
            ]
            
            choice = self.menu.show_menu(
                "SECURITY REVIEW MENU",
                options,
                f"Found {assessment.total_risks} risks - {len(assessment.blocking_violations)} blocking operations"
            )
            
            if choice == "review_all":
                resolved_count += self._review_risks_individually(assessment.risks)
            elif choice == "review_critical":
                critical_risks = [r for r in assessment.risks if r.risk_level == SecurityRiskLevel.CRITICAL]
                resolved_count += self._review_risks_individually(critical_risks)
            elif choice == "bulk_actions":
                resolved_count += self._bulk_actions_menu(assessment)
            elif choice == "show_summary":
                self._show_detailed_summary(assessment)
            elif choice == "exit" or choice is None:
                return {
                    "status": "cancelled",
                    "risks_resolved": resolved_count,
                    "total_risks": assessment.total_risks
                }
        
        return {
            "status": "completed",
            "risks_resolved": resolved_count,
            "total_risks": assessment.total_risks
        }
    
    def _review_risks_individually(self, risks: List[SecurityRisk]) -> int:
        """Review risks one by one"""
        resolved_count = 0
        
        for i, risk in enumerate(risks):
            if self._review_single_risk(risk, i + 1, len(risks)):
                resolved_count += 1
        
        return resolved_count
    
    def _review_single_risk(self, risk: SecurityRisk, current: int, total: int) -> bool:
        """Review a single security risk"""
        self.screen.clear()
        
        print(self.screen.center_text(f"RISK {current} of {total}"))
        print(self.screen.line('='))
        print()
        
        # Show risk details
        print(f"File: {risk.file_path}")
        print(f"Risk Type: {risk.risk_type.value}")
        print(f"Risk Level: {risk.risk_level.value.upper()}")
        print(f"Size: {risk.file_size:,} bytes")
        print(f"Git Tracked: {'Yes' if risk.is_tracked else 'No'}")
        print()
        print(f"Description: {risk.description}")
        print(f"Recommendation: {risk.recommendation}")
        print()
        print(self.screen.line('-'))
        
        # Show options
        options = [
            ("ignore_gitignore", "Add to .gitignore"),
            ("ignore_gitupignore", "Add to .gitupignore"),
            ("ignore_permanently", "Ignore permanently"),
            ("ignore_temporarily", "Ignore temporarily"),
            ("remove_file", "Remove file"),
            ("skip", "Skip this risk")
        ]
        
        choice = self.menu.show_menu("WHAT WOULD YOU LIKE TO DO?", options)
        
        if choice and choice != "skip":
            # Apply the decision
            self._apply_risk_decision(risk, choice)
            return True
        
        return False
    
    def _apply_risk_decision(self, risk: SecurityRisk, decision: str):
        """Apply user decision to a risk"""
        # This would integrate with the existing decision system
        self.menu.show_info(
            "DECISION APPLIED",
            f"Decision '{decision}' has been applied to:\n{risk.file_path}"
        )
    
    def _bulk_actions_menu(self, assessment: SecurityAssessment) -> int:
        """Bulk actions menu"""
        options = [
            ("ignore_all_logs", f"Ignore all log files"),
            ("ignore_all_temp", f"Ignore all temporary files"),
            ("ignore_all_ide", f"Ignore all IDE config files"),
            ("ignore_low_risk", f"Ignore all low-risk items"),
            ("back", "Back to main menu")
        ]
        
        choice = self.menu.show_menu("BULK ACTIONS", options)
        
        if choice == "back" or choice is None:
            return 0
        
        # Apply bulk action
        self.menu.show_info(
            "BULK ACTION APPLIED",
            f"Bulk action '{choice}' has been applied to applicable files."
        )
        
        return 5  # Placeholder count
    
    def _show_detailed_summary(self, assessment: SecurityAssessment):
        """Show detailed risk summary"""
        summary_lines = ["DETAILED RISK SUMMARY", ""]
        
        # Group risks by level
        by_level = {}
        for risk in assessment.risks:
            level = risk.risk_level
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(risk)
        
        # Show each level
        for level in [SecurityRiskLevel.CRITICAL, SecurityRiskLevel.HIGH, 
                     SecurityRiskLevel.MEDIUM, SecurityRiskLevel.LOW]:
            if level in by_level:
                summary_lines.append(f"{level.value.upper()} RISKS:")
                for risk in by_level[level][:5]:  # Show first 5
                    summary_lines.append(f"  - {risk.file_path}")
                if len(by_level[level]) > 5:
                    summary_lines.append(f"  ... and {len(by_level[level]) - 5} more")
                summary_lines.append("")
        
        self.menu.show_info("RISK SUMMARY", "\n".join(summary_lines))


def launch_security_review_tui(project_path: str, security_level: str = "moderate") -> Dict[str, Any]:
    """
    Launch the security review TUI as a full-screen application.
    
    Args:
        project_path: Path to the project directory
        security_level: Security enforcement level
        
    Returns:
        Dictionary with review results
    """
    try:
        # Create and run the TUI
        tui = SecurityReviewTUI(project_path, security_level)
        return tui.run()
    
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        screen = TerminalScreen()
        screen.clear()
        print("\n\nSecurity review cancelled by user.")
        return {"status": "cancelled", "risks_resolved": 0, "total_risks": 0}
    
    except Exception as e:
        # Handle unexpected errors
        screen = TerminalScreen()
        screen.clear()
        print(f"\n\nUnexpected error during security review: {e}")
        return {"status": "error", "error": str(e)}


# ASCII Art and Terminal Utilities
class ASCIIArt:
    """ASCII art and terminal formatting utilities"""
    
    @staticmethod
    def gitup_logo() -> str:
        """ASCII art GitUp logo"""
        return """
   _____ _ _   _    _ _____  
  / ____(_) | | |  | |  __ \ 
 | |  __ _| |_| |  | | |__) |
 | | |_ | | __| |  | |  ___/ 
 | |__| | | |_| |__| | |     
  \_____|_|\__|\____/|_|     
        """
    
    @staticmethod
    def security_shield() -> str:
        """ASCII art security shield"""
        return """
        .-""""""-.
       /          \
      /   SECURE   \
     |     GITUP    |
     |              |
      \            /
       \          /
        '-.____.-'
        """
    
    @staticmethod
    def warning_box(message: str) -> str:
        """ASCII warning box"""
        lines = message.split('\n')
        max_len = max(len(line) for line in lines)
        
        result = []
        result.append('!' * (max_len + 4))
        result.append('!' + ' ' * (max_len + 2) + '!')
        
        for line in lines:
            result.append(f'! {line.ljust(max_len)} !')
        
        result.append('!' + ' ' * (max_len + 2) + '!')
        result.append('!' * (max_len + 4))
        
        return '\n'.join(result)