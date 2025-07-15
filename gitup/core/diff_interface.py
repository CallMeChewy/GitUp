# File: diff_interface.py
# Path: /home/herb/Desktop/GitUp/gitup/core/diff_interface.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:37PM
"""
Interactive diff interface for GitUp .gitupignore system.
Provides user-friendly interface for reviewing .gitignore conflicts and making
security decisions through terminal-based interactive prompts.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import textwrap

# Rich imports for enhanced terminal output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.text import Text
    from rich.columns import Columns
    from rich.layout import Layout
    from rich.live import Live
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .ignore_manager import GitUpIgnoreManager
from .pattern_analyzer import GitUpPatternAnalyzer
from .metadata_manager import GitUpMetadataManager, DecisionType


class DiffAction(Enum):
    """Available diff actions."""
    ACCEPT_ALL = "accept_all"
    REJECT_ALL = "reject_all"
    MERGE_FILES = "merge_files"
    CREATE_GITUPIGNORE = "create_gitupignore"
    REVIEW_INDIVIDUAL = "review_individual"
    HELP = "help"
    QUIT = "quit"


class ReviewAction(Enum):
    """Available review actions for individual items."""
    SAFE = "safe"
    IGNORE = "ignore"
    RENAME = "rename"
    EDIT = "edit"
    SKIP = "skip"
    HELP = "help"
    BACK = "back"


@dataclass
class DiffItem:
    """Single diff item for review."""
    Pattern: str
    Category: str
    SecurityLevel: str
    CurrentStatus: str  # 'missing', 'conflict', 'exists'
    Recommendation: str
    RiskScore: float
    FileMatches: List[str]
    Description: str


class GitUpDiffInterface:
    """
    Interactive diff interface for .gitupignore system.
    
    Provides terminal-based interface for reviewing conflicts between existing
    .gitignore files and GitUp security recommendations.
    """
    
    def __init__(self, ProjectPath: str):
        """
        Initialize the diff interface.
        
        Args:
            ProjectPath: Path to the project directory
        """
        self.ProjectPath = Path(ProjectPath)
        self.IgnoreManager = GitUpIgnoreManager(str(ProjectPath))
        self.PatternAnalyzer = GitUpPatternAnalyzer(str(ProjectPath))
        self.MetadataManager = GitUpMetadataManager(str(ProjectPath))
        
        # Initialize console
        if RICH_AVAILABLE:
            self.Console = Console()
        else:
            self.Console = None
        
        # Track user decisions
        self.UserDecisions = {}
        self.ReviewedItems = set()
        
        # Interface state
        self.ShowHelp = False
        self.CurrentPage = 0
        self.ItemsPerPage = 10
    
    def ShowDiffOverview(self) -> Dict[str, Any]:
        """
        Show overview of differences between .gitignore and GitUp recommendations.
        
        Returns:
            Dictionary with diff overview results
        """
        if self.Console:
            self.Console.print("\n[bold blue]GitUp Security Review[/bold blue]")
            self.Console.print("=" * 60)
        else:
            print("\nGitUp Security Review")
            print("=" * 60)
        
        # Analyze existing patterns
        Analysis = self.IgnoreManager.AnalyzeExistingGitIgnore()
        Suggestions = self.IgnoreManager.CreateSuggestions()
        
        # Build diff items
        DiffItems = self._BuildDiffItems(Analysis, Suggestions)
        
        # Show summary
        self._ShowSummary(DiffItems)
        
        # Show side-by-side comparison
        self._ShowSideBySideComparison(Analysis, Suggestions)
        
        return {
            'diff_items': DiffItems,
            'analysis': Analysis,
            'suggestions': Suggestions
        }
    
    def LaunchInteractiveReview(self) -> Dict[str, Any]:
        """
        Launch interactive review process.
        
        Returns:
            Dictionary with review results
        """
        if self.Console:
            self.Console.print("\n[bold green]Interactive Security Review[/bold green]")
        else:
            print("\nInteractive Security Review")
        
        # Get diff overview
        DiffData = self.ShowDiffOverview()
        DiffItems = DiffData['diff_items']
        
        if not DiffItems:
            if self.Console:
                self.Console.print("[green]✓ No security issues found! Your .gitignore looks good.[/green]")
            else:
                print("✓ No security issues found! Your .gitignore looks good.")
            return {'action': 'no_issues', 'decisions': {}}
        
        # Show main menu
        while True:
            Action = self._ShowMainMenu()
            
            if Action == DiffAction.ACCEPT_ALL:
                return self._AcceptAllSuggestions(DiffItems)
            elif Action == DiffAction.REJECT_ALL:
                return self._RejectAllSuggestions(DiffItems)
            elif Action == DiffAction.MERGE_FILES:
                return self._MergeWithGitIgnore(DiffItems)
            elif Action == DiffAction.CREATE_GITUPIGNORE:
                return self._CreateGitUpIgnoreOnly(DiffItems)
            elif Action == DiffAction.REVIEW_INDIVIDUAL:
                self._ReviewIndividualItems(DiffItems)
            elif Action == DiffAction.HELP:
                self._ShowHelp()
            elif Action == DiffAction.QUIT:
                return {'action': 'quit', 'decisions': self.UserDecisions}
    
    def ReviewSingleItem(self, Item: DiffItem) -> Dict[str, Any]:
        """
        Review a single diff item.
        
        Args:
            Item: DiffItem to review
            
        Returns:
            Dictionary with review result
        """
        if self.Console:
            self.Console.print(f"\n[bold]Reviewing: {Item.Pattern}[/bold]")
        else:
            print(f"\nReviewing: {Item.Pattern}")
        
        # Show item details
        self._ShowItemDetails(Item)
        
        # Get user decision
        while True:
            if self.Console:
                Action = Prompt.ask(
                    "What would you like to do?",
                    choices=["safe", "ignore", "rename", "edit", "skip", "help", "back"],
                    default="safe"
                )
            else:
                Action = input("Action [safe/ignore/rename/edit/skip/help/back]: ").strip().lower()
            
            try:
                ReviewActionEnum = ReviewAction(Action)
                
                if ReviewActionEnum == ReviewAction.SAFE:
                    return self._HandleSafeDecision(Item)
                elif ReviewActionEnum == ReviewAction.IGNORE:
                    return self._HandleIgnoreDecision(Item)
                elif ReviewActionEnum == ReviewAction.RENAME:
                    return self._HandleRenameDecision(Item)
                elif ReviewActionEnum == ReviewAction.EDIT:
                    return self._HandleEditDecision(Item)
                elif ReviewActionEnum == ReviewAction.SKIP:
                    return {'action': 'skip', 'pattern': Item.Pattern}
                elif ReviewActionEnum == ReviewAction.HELP:
                    self._ShowItemHelp(Item)
                    continue
                elif ReviewActionEnum == ReviewAction.BACK:
                    return {'action': 'back', 'pattern': Item.Pattern}
                
            except ValueError:
                if self.Console:
                    self.Console.print("[red]Invalid choice. Please try again.[/red]")
                else:
                    print("Invalid choice. Please try again.")
    
    def GenerateFinalConfiguration(self) -> Dict[str, Any]:
        """
        Generate final .gitupignore configuration based on user decisions.
        
        Returns:
            Dictionary with final configuration
        """
        if not self.UserDecisions:
            return {'success': False, 'message': 'No decisions to process'}
        
        # Apply user decisions
        try:
            self.IgnoreManager.ApplyUserDecisions(self.UserDecisions)
            
            # Save metadata
            for Pattern, Decision in self.UserDecisions.items():
                self.MetadataManager.AddUserDecision(
                    Pattern=Pattern,
                    Decision=DecisionType(Decision['action']),
                    Reason=Decision.get('reason', 'User decision'),
                    Confidence=Decision.get('confidence', 1.0)
                )
            
            return {
                'success': True,
                'gitupignore_created': True,
                'decisions_count': len(self.UserDecisions),
                'metadata_saved': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Private helper methods
    
    def _BuildDiffItems(self, Analysis: Dict[str, Any], Suggestions: Dict[str, Any]) -> List[DiffItem]:
        """Build list of diff items from analysis and suggestions."""
        DiffItems = []
        
        # Add missing patterns
        for Missing in Analysis['missing_patterns']:
            DiffItems.append(DiffItem(
                Pattern=Missing['pattern'],
                Category=Missing['category'],
                SecurityLevel=Missing['risk_level'],
                CurrentStatus='missing',
                Recommendation='add_to_gitupignore',
                RiskScore=self._GetRiskScore(Missing['risk_level']),
                FileMatches=self._FindFileMatches(Missing['pattern']),
                Description=f"Missing security pattern for {Missing['category']}"
            ))
        
        # Add conflicts
        for Conflict in Analysis['conflicts']:
            DiffItems.append(DiffItem(
                Pattern=Conflict['pattern'],
                Category='conflict',
                SecurityLevel='medium',
                CurrentStatus='conflict',
                Recommendation='review_and_decide',
                RiskScore=2.0,
                FileMatches=self._FindFileMatches(Conflict['pattern']),
                Description=Conflict['reason']
            ))
        
        # Sort by risk score
        DiffItems.sort(key=lambda x: x.RiskScore, reverse=True)
        
        return DiffItems
    
    def _ShowSummary(self, DiffItems: List[DiffItem]) -> None:
        """Show summary of diff items."""
        if not DiffItems:
            return
        
        MissingCount = len([item for item in DiffItems if item.CurrentStatus == 'missing'])
        ConflictCount = len([item for item in DiffItems if item.CurrentStatus == 'conflict'])
        
        if self.Console:
            SummaryTable = Table(title="Security Review Summary")
            SummaryTable.add_column("Issue Type", style="cyan")
            SummaryTable.add_column("Count", style="magenta")
            SummaryTable.add_column("Risk Level", style="red")
            
            if MissingCount > 0:
                SummaryTable.add_row("Missing Security Patterns", str(MissingCount), "High")
            if ConflictCount > 0:
                SummaryTable.add_row("Pattern Conflicts", str(ConflictCount), "Medium")
            
            self.Console.print(SummaryTable)
        else:
            print(f"\nSummary:")
            print(f"  Missing Security Patterns: {MissingCount}")
            print(f"  Pattern Conflicts: {ConflictCount}")
    
    def _ShowSideBySideComparison(self, Analysis: Dict[str, Any], Suggestions: Dict[str, Any]) -> None:
        """Show side-by-side comparison of current vs recommended."""
        if self.Console:
            DiffLayout = Layout()
            DiffLayout.split_row(
                Layout(name="current", ratio=1),
                Layout(name="recommended", ratio=1)
            )
            
            # Current .gitignore
            CurrentPatterns = Analysis.get('existing_patterns', [])
            CurrentText = "\n".join(CurrentPatterns) if CurrentPatterns else "# No .gitignore file"
            DiffLayout["current"].update(Panel(
                Syntax(CurrentText, "gitignore", theme="monokai"),
                title="Current .gitignore",
                border_style="blue"
            ))
            
            # Recommended additions
            RecommendedPatterns = []
            for Addition in Suggestions.get('security_additions', []):
                RecommendedPatterns.append(f"{Addition['pattern']}  # {Addition['category']}")
            
            RecommendedText = "\n".join(RecommendedPatterns) if RecommendedPatterns else "# No recommendations"
            DiffLayout["recommended"].update(Panel(
                Syntax(RecommendedText, "gitignore", theme="monokai"),
                title="Recommended .gitupignore",
                border_style="green"
            ))
            
            self.Console.print(DiffLayout)
        else:
            print("\nCurrent .gitignore vs Recommended .gitupignore:")
            print("-" * 60)
            
            CurrentPatterns = Analysis.get('existing_patterns', [])
            RecommendedPatterns = [addition['pattern'] for addition in Suggestions.get('security_additions', [])]
            
            MaxLen = max(len(CurrentPatterns), len(RecommendedPatterns))
            
            for i in range(MaxLen):
                Current = CurrentPatterns[i] if i < len(CurrentPatterns) else ""
                Recommended = RecommendedPatterns[i] if i < len(RecommendedPatterns) else ""
                print(f"{Current:<30} | {Recommended}")
    
    def _ShowMainMenu(self) -> DiffAction:
        """Show main menu and get user choice."""
        if self.Console:
            self.Console.print("\n[bold]Actions:[/bold]")
            MenuOptions = [
                "[A] Accept all GitUp suggestions",
                "[R] Reject all suggestions",
                "[M] Merge with existing .gitignore",
                "[C] Create .gitupignore only",
                "[I] Review each item individually",
                "[H] Help & Documentation",
                "[Q] Quit"
            ]
            
            for Option in MenuOptions:
                self.Console.print(f"  {Option}")
            
            Choice = Prompt.ask(
                "\nWhat would you like to do?",
                choices=["A", "R", "M", "C", "I", "H", "Q"],
                default="I"
            ).upper()
        else:
            print("\nActions:")
            print("  [A] Accept all GitUp suggestions")
            print("  [R] Reject all suggestions")
            print("  [M] Merge with existing .gitignore")
            print("  [C] Create .gitupignore only")
            print("  [I] Review each item individually")
            print("  [H] Help & Documentation")
            print("  [Q] Quit")
            
            Choice = input("\nWhat would you like to do? [A/R/M/C/I/H/Q]: ").strip().upper()
        
        ActionMap = {
            'A': DiffAction.ACCEPT_ALL,
            'R': DiffAction.REJECT_ALL,
            'M': DiffAction.MERGE_FILES,
            'C': DiffAction.CREATE_GITUPIGNORE,
            'I': DiffAction.REVIEW_INDIVIDUAL,
            'H': DiffAction.HELP,
            'Q': DiffAction.QUIT
        }
        
        return ActionMap.get(Choice, DiffAction.HELP)
    
    def _ShowItemDetails(self, Item: DiffItem) -> None:
        """Show detailed information about a diff item."""
        if self.Console:
            # Create details panel
            Details = f"""
[bold]Pattern:[/bold] {Item.Pattern}
[bold]Category:[/bold] {Item.Category}
[bold]Security Level:[/bold] {Item.SecurityLevel}
[bold]Status:[/bold] {Item.CurrentStatus}
[bold]Risk Score:[/bold] {Item.RiskScore}

[bold]Description:[/bold]
{Item.Description}

[bold]File Matches:[/bold]
{chr(10).join(Item.FileMatches[:5])}
{f"... and {len(Item.FileMatches) - 5} more" if len(Item.FileMatches) > 5 else ""}
"""
            
            self.Console.print(Panel(Details, title=f"Review: {Item.Pattern}", border_style="yellow"))
            
            # Show file preview if available
            if Item.FileMatches:
                self._ShowFilePreview(Item.FileMatches[0])
        else:
            print(f"\nPattern: {Item.Pattern}")
            print(f"Category: {Item.Category}")
            print(f"Security Level: {Item.SecurityLevel}")
            print(f"Status: {Item.CurrentStatus}")
            print(f"Risk Score: {Item.RiskScore}")
            print(f"Description: {Item.Description}")
            print(f"File Matches: {', '.join(Item.FileMatches[:3])}")
            if len(Item.FileMatches) > 3:
                print(f"... and {len(Item.FileMatches) - 3} more")
    
    def _ShowFilePreview(self, FilePath: str) -> None:
        """Show preview of a file."""
        FullPath = self.ProjectPath / FilePath
        
        if not FullPath.exists():
            return
        
        try:
            with open(FullPath, 'r', encoding='utf-8') as f:
                Content = f.read(500)  # First 500 characters
            
            if self.Console:
                self.Console.print(Panel(
                    Syntax(Content, lexer_name="text", theme="monokai"),
                    title=f"Preview: {FilePath}",
                    border_style="dim"
                ))
            else:
                print(f"\nPreview of {FilePath}:")
                print("-" * 40)
                print(Content[:200] + "..." if len(Content) > 200 else Content)
                print("-" * 40)
        
        except Exception:
            if self.Console:
                self.Console.print(f"[dim]Could not preview {FilePath}[/dim]")
            else:
                print(f"Could not preview {FilePath}")
    
    def _ReviewIndividualItems(self, DiffItems: List[DiffItem]) -> None:
        """Review items individually."""
        for i, Item in enumerate(DiffItems):
            if self.Console:
                self.Console.print(f"\n[bold]Item {i+1} of {len(DiffItems)}[/bold]")
            else:
                print(f"\nItem {i+1} of {len(DiffItems)}")
            
            Result = self.ReviewSingleItem(Item)
            
            if Result['action'] == 'back':
                if i > 0:
                    i -= 2  # Go back one (will be incremented by loop)
                    continue
            elif Result['action'] == 'skip':
                continue
            else:
                self.UserDecisions[Item.Pattern] = Result
                self.ReviewedItems.add(Item.Pattern)
    
    def _AcceptAllSuggestions(self, DiffItems: List[DiffItem]) -> Dict[str, Any]:
        """Accept all GitUp suggestions."""
        for Item in DiffItems:
            self.UserDecisions[Item.Pattern] = {
                'action': 'safe',
                'reason': 'Accepted all suggestions',
                'confidence': 1.0
            }
        
        return self.GenerateFinalConfiguration()
    
    def _RejectAllSuggestions(self, DiffItems: List[DiffItem]) -> Dict[str, Any]:
        """Reject all GitUp suggestions."""
        return {'action': 'reject_all', 'decisions': {}}
    
    def _MergeWithGitIgnore(self, DiffItems: List[DiffItem]) -> Dict[str, Any]:
        """Merge recommendations with existing .gitignore."""
        if self.Console:
            Confirmed = Confirm.ask("This will modify your existing .gitignore file. Continue?")
        else:
            Confirmed = input("This will modify your existing .gitignore file. Continue? [y/N]: ").strip().lower() == 'y'
        
        if not Confirmed:
            return {'action': 'cancelled', 'decisions': {}}
        
        # This would implement the actual merge logic
        return {'action': 'merge', 'decisions': self.UserDecisions}
    
    def _CreateGitUpIgnoreOnly(self, DiffItems: List[DiffItem]) -> Dict[str, Any]:
        """Create .gitupignore file only."""
        for Item in DiffItems:
            self.UserDecisions[Item.Pattern] = {
                'action': 'safe',
                'reason': 'Create .gitupignore only',
                'confidence': 1.0
            }
        
        return self.GenerateFinalConfiguration()
    
    def _HandleSafeDecision(self, Item: DiffItem) -> Dict[str, Any]:
        """Handle safe decision."""
        if self.Console:
            Reason = Prompt.ask("Reason (optional)", default="Marked as safe")
        else:
            Reason = input("Reason (optional): ").strip() or "Marked as safe"
        
        return {
            'action': 'safe',
            'pattern': Item.Pattern,
            'reason': Reason,
            'confidence': 1.0
        }
    
    def _HandleIgnoreDecision(self, Item: DiffItem) -> Dict[str, Any]:
        """Handle ignore decision."""
        if self.Console:
            Reason = Prompt.ask("Reason for ignoring", default="User choice")
        else:
            Reason = input("Reason for ignoring: ").strip() or "User choice"
        
        return {
            'action': 'ignore',
            'pattern': Item.Pattern,
            'reason': Reason,
            'confidence': 1.0
        }
    
    def _HandleRenameDecision(self, Item: DiffItem) -> Dict[str, Any]:
        """Handle rename decision."""
        if self.Console:
            NewName = Prompt.ask("New pattern name")
        else:
            NewName = input("New pattern name: ").strip()
        
        return {
            'action': 'rename',
            'pattern': Item.Pattern,
            'new_pattern': NewName,
            'reason': 'User renamed pattern',
            'confidence': 1.0
        }
    
    def _HandleEditDecision(self, Item: DiffItem) -> Dict[str, Any]:
        """Handle edit decision."""
        if self.Console:
            self.Console.print("[yellow]Edit functionality not implemented yet[/yellow]")
        else:
            print("Edit functionality not implemented yet")
        
        return {
            'action': 'edit',
            'pattern': Item.Pattern,
            'reason': 'User requested edit',
            'confidence': 0.5
        }
    
    def _ShowHelp(self) -> None:
        """Show help information."""
        HelpText = """
[bold]GitUp Security Review Help[/bold]

[bold green]What is this?[/bold green]
GitUp analyzes your .gitignore file for security gaps and provides recommendations
to prevent accidentally committing sensitive files.

[bold green]Actions explained:[/bold green]
• [bold]Accept all[/bold] - Add all recommended patterns to .gitupignore
• [bold]Reject all[/bold] - Skip all recommendations
• [bold]Merge[/bold] - Add patterns to existing .gitignore
• [bold]Create .gitupignore[/bold] - Create separate security file
• [bold]Review individually[/bold] - Review each recommendation

[bold green]Review options:[/bold green]
• [bold]Safe[/bold] - File is safe to track in git
• [bold]Ignore[/bold] - Add to .gitignore (stop tracking)
• [bold]Rename[/bold] - Suggest a safer filename
• [bold]Edit[/bold] - Remove sensitive data from file
• [bold]Skip[/bold] - Skip this recommendation

[bold green]The .gitupignore system:[/bold green]
GitUp creates a .gitupignore file that works alongside your existing .gitignore.
This allows you to maintain security without disrupting your current workflow.
"""
        
        if self.Console:
            self.Console.print(Panel(HelpText, title="Help", border_style="blue"))
        else:
            print(HelpText)
    
    def _ShowItemHelp(self, Item: DiffItem) -> None:
        """Show help for a specific item."""
        HelpText = f"""
[bold]Pattern:[/bold] {Item.Pattern}
[bold]Why is this flagged?[/bold]
{Item.Description}

[bold]Risk Level:[/bold] {Item.SecurityLevel}
This indicates how critical this security issue is.

[bold]Your options:[/bold]
• [bold]Safe[/bold] - You've reviewed the files and they're safe
• [bold]Ignore[/bold] - Move to .gitignore to stop tracking
• [bold]Rename[/bold] - Change filename to be less sensitive
• [bold]Edit[/bold] - Remove sensitive data from files
"""
        
        if self.Console:
            self.Console.print(Panel(HelpText, title=f"Help: {Item.Pattern}", border_style="blue"))
        else:
            print(HelpText)
    
    def _GetRiskScore(self, RiskLevel: str) -> float:
        """Get numeric risk score from risk level."""
        RiskScores = {
            'critical': 4.0,
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0
        }
        return RiskScores.get(RiskLevel, 1.0)
    
    def _FindFileMatches(self, Pattern: str) -> List[str]:
        """Find files that match a pattern."""
        Matches = []
        
        try:
            import fnmatch
            for Root, Dirs, Files in os.walk(self.ProjectPath):
                for File in Files:
                    if fnmatch.fnmatch(File, Pattern):
                        FilePath = Path(Root) / File
                        RelativePath = FilePath.relative_to(self.ProjectPath)
                        Matches.append(str(RelativePath))
        except Exception:
            pass
        
        return Matches[:10]  # Limit to 10 matches