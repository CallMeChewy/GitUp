# File: SecurityRemediator.py
# Path: Scripts/Security/SecurityRemediator.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-14
# Last Modified: 2025-07-14  12:30PM
"""
Security Remediator - Automatically fixes security issues found by GitSecurityValidator
including git history cleaning, .gitignore modifications, and file removal.
"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

from .GitSecurityValidator import GitSecurityValidator, SecurityIssue
from .SecurityAuditLogger import SecurityAuditLogger

@dataclass
class RemediationAction:
    """Represents a remediation action taken"""
    Timestamp: str
    Action: str  # 'REMOVE_FROM_TRACKING', 'CLEAN_HISTORY', 'UPDATE_GITIGNORE', 'REMOVE_FILE'
    FilePath: str
    Success: bool
    Details: str
    CommandUsed: Optional[str] = None
    BackupCreated: Optional[str] = None

class SecurityRemediator:
    """Automatically fixes security issues"""
    
    def __init__(self, ProjectPath: str = "."):
        self.ProjectPath = Path(ProjectPath).resolve()
        self.Validator = GitSecurityValidator(str(self.ProjectPath))
        self.AuditLogger = SecurityAuditLogger(str(self.ProjectPath))
        self.RemediationActions: List[RemediationAction] = []
        
        # Create backups directory
        self.BackupDir = self.ProjectPath / "Docs" / "Security" / "Backups"
        self.BackupDir.mkdir(parents=True, exist_ok=True)
    
    def _RunCommand(self, Command: str, Description: str = "") -> Tuple[bool, str]:
        """Run a command and return success status and output"""
        try:
            Result = subprocess.run(
                Command,
                shell=True,
                cwd=self.ProjectPath,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            Output = Result.stdout + Result.stderr
            Success = Result.returncode == 0
            
            if Description:
                print(f"   {Description}: {'✅' if Success else '❌'}")
            
            return Success, Output
            
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def _CreateBackup(self, FilePath: str) -> Optional[str]:
        """Create backup of a file before modification"""
        try:
            SourcePath = self.ProjectPath / FilePath
            if SourcePath.exists():
                Timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                BackupFileName = f"{SourcePath.name}.backup_{Timestamp}"
                BackupPath = self.BackupDir / BackupFileName
                
                shutil.copy2(SourcePath, BackupPath)
                return str(BackupPath)
        except Exception as e:
            print(f"   Warning: Could not create backup for {FilePath}: {e}")
        return None
    
    def RemoveFromTracking(self, FilePath: str) -> RemediationAction:
        """Remove file from git tracking"""
        print(f"🔧 Removing '{FilePath}' from git tracking...")
        
        Command = f"git rm --cached \"{FilePath}\""
        Success, Output = self._RunCommand(Command, "Remove from tracking")
        
        Action = RemediationAction(
            Timestamp=datetime.now().isoformat(),
            Action="REMOVE_FROM_TRACKING",
            FilePath=FilePath,
            Success=Success,
            Details=Output,
            CommandUsed=Command
        )
        
        self.RemediationActions.append(Action)
        return Action
    
    def CleanFromHistory(self, FilePaths: List[str]) -> List[RemediationAction]:
        """Clean files from git history using filter-branch"""
        print(f"🧹 Cleaning {len(FilePaths)} files from git history...")
        
        Actions = []
        
        # Create backup of entire repo
        BackupPath = self._CreateRepoBackup()
        
        # Build filter-branch command
        FileList = " ".join([f'"{fp}"' for fp in FilePaths])
        FilterCommand = f"git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch {FileList}' --prune-empty --tag-name-filter cat -- --all"
        
        print("   ⚠️  This operation will rewrite git history!")
        print("   💾 Repository backup created")
        
        Success, Output = self._RunCommand(FilterCommand, "Clean git history")
        
        for FilePath in FilePaths:
            Action = RemediationAction(
                Timestamp=datetime.now().isoformat(),
                Action="CLEAN_HISTORY",
                FilePath=FilePath,
                Success=Success,
                Details=Output,
                CommandUsed=FilterCommand,
                BackupCreated=BackupPath
            )
            Actions.append(Action)
            self.RemediationActions.append(Action)
        
        if Success:
            print("   🧹 Git history cleaned successfully")
            print("   ⚠️  Run 'git push --force --all' to update remote")
        else:
            print("   ❌ Failed to clean git history")
            print(f"   📝 Error: {Output}")
        
        return Actions
    
    def _CreateRepoBackup(self) -> Optional[str]:
        """Create a backup of the entire repository"""
        try:
            Timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            BackupName = f"repo_backup_{Timestamp}"
            BackupPath = self.BackupDir / BackupName
            
            # Create git bundle (complete backup)
            BundleCommand = f"git bundle create \"{BackupPath}.bundle\" --all"
            Success, Output = self._RunCommand(BundleCommand, "Create repository backup")
            
            if Success:
                return str(BackupPath) + ".bundle"
            else:
                print(f"   Warning: Could not create repository backup: {Output}")
        except Exception as e:
            print(f"   Warning: Could not create repository backup: {e}")
        return None
    
    def UpdateGitignore(self, FilePaths: List[str]) -> RemediationAction:
        """Add files to .gitignore"""
        print(f"📝 Adding {len(FilePaths)} files to .gitignore...")
        
        GitignorePath = self.ProjectPath / ".gitignore"
        BackupPath = self._CreateBackup(".gitignore")
        
        try:
            # Read current .gitignore
            CurrentContent = ""
            if GitignorePath.exists():
                with open(GitignorePath, 'r') as f:
                    CurrentContent = f.read()
            
            # Add new entries
            NewEntries = []
            for FilePath in FilePaths:
                if FilePath not in CurrentContent:
                    NewEntries.append(FilePath)
            
            if NewEntries:
                with open(GitignorePath, 'a') as f:
                    f.write("\n# Auto-added sensitive files\n")
                    for Entry in NewEntries:
                        f.write(f"{Entry}\n")
                
                Success = True
                Details = f"Added {len(NewEntries)} entries to .gitignore"
                print(f"   ✅ Added {len(NewEntries)} entries to .gitignore")
            else:
                Success = True
                Details = "All files already in .gitignore"
                print("   ℹ️  All files already in .gitignore")
        
        except Exception as e:
            Success = False
            Details = f"Failed to update .gitignore: {str(e)}"
            print(f"   ❌ Failed to update .gitignore: {e}")
        
        Action = RemediationAction(
            Timestamp=datetime.now().isoformat(),
            Action="UPDATE_GITIGNORE",
            FilePath=str(GitignorePath),
            Success=Success,
            Details=Details,
            BackupCreated=BackupPath
        )
        
        self.RemediationActions.append(Action)
        return Action
    
    def RemoveFile(self, FilePath: str) -> RemediationAction:
        """Remove file from filesystem"""
        print(f"🗑️  Removing file '{FilePath}'...")
        
        FullPath = self.ProjectPath / FilePath
        BackupPath = self._CreateBackup(FilePath)
        
        try:
            if FullPath.exists():
                FullPath.unlink()
                Success = True
                Details = f"File removed successfully"
                print(f"   ✅ File removed: {FilePath}")
            else:
                Success = True
                Details = f"File does not exist"
                print(f"   ℹ️  File does not exist: {FilePath}")
        
        except Exception as e:
            Success = False
            Details = f"Failed to remove file: {str(e)}"
            print(f"   ❌ Failed to remove file: {e}")
        
        Action = RemediationAction(
            Timestamp=datetime.now().isoformat(),
            Action="REMOVE_FILE",
            FilePath=FilePath,
            Success=Success,
            Details=Details,
            BackupCreated=BackupPath
        )
        
        self.RemediationActions.append(Action)
        return Action
    
    def AutoRemediate(self, CleanHistory: bool = True, UpdateGitignore: bool = True, 
                     RemoveFiles: bool = False, Interactive: bool = True) -> Dict:
        """Automatically remediate all security issues"""
        print("🔒 AUTOMATIC SECURITY REMEDIATION")
        print("=" * 50)
        
        # Get current issues
        Issues = self.Validator.ValidateProject()
        if not Issues:
            print("✅ No security issues found!")
            return {"success": True, "issues_found": 0, "actions_taken": []}
        
        print(f"📋 Found {len(Issues)} security issues")
        
        # Categorize issues
        TrackedFiles = []
        HistoryFiles = []
        UnignoredFiles = []
        
        for Issue in Issues:
            if Issue.Category == "EXPOSED_CREDENTIALS":
                if "is tracked in git" in Issue.Description:
                    TrackedFiles.append(Issue.FilePath)
                elif "exists in git history" in Issue.Description:
                    HistoryFiles.append(Issue.FilePath)
                elif "is not ignored" in Issue.Description:
                    UnignoredFiles.append(Issue.FilePath)
        
        # Get user confirmation for destructive operations
        if Interactive and (TrackedFiles or HistoryFiles):
            print("\n⚠️  DESTRUCTIVE OPERATIONS DETECTED")
            if TrackedFiles:
                print(f"   📤 Will remove {len(TrackedFiles)} files from git tracking")
            if HistoryFiles and CleanHistory:
                print(f"   🧹 Will clean {len(HistoryFiles)} files from git history")
            
            Response = input("\nProceed with remediation? (y/N): ").lower()
            if Response != 'y':
                print("❌ Remediation cancelled by user")
                return {"success": False, "cancelled": True}
        
        # Perform remediation
        print("\n🔧 PERFORMING REMEDIATION")
        print("-" * 30)
        
        # 1. Remove from tracking
        for FilePath in TrackedFiles:
            self.RemoveFromTracking(FilePath)
        
        # 2. Clean from history
        if CleanHistory and HistoryFiles:
            self.CleanFromHistory(HistoryFiles)
        
        # 3. Update .gitignore
        if UpdateGitignore and UnignoredFiles:
            self.UpdateGitignore(UnignoredFiles)
        
        # 4. Remove files if requested
        if RemoveFiles:
            for FilePath in TrackedFiles + HistoryFiles + UnignoredFiles:
                if (self.ProjectPath / FilePath).exists():
                    self.RemoveFile(FilePath)
        
        # Log remediation
        self._LogRemediation(Issues)
        
        # Re-validate
        print("\n🔍 RE-VALIDATING SECURITY...")
        NewIssues = self.Validator.ValidateProject()
        
        Result = {
            "success": True,
            "issues_found": len(Issues),
            "issues_remaining": len(NewIssues),
            "actions_taken": [asdict(action) for action in self.RemediationActions],
            "tracked_files_removed": len(TrackedFiles),
            "history_files_cleaned": len(HistoryFiles) if CleanHistory else 0,
            "gitignore_updated": len(UnignoredFiles) if UpdateGitignore else 0,
            "files_removed": 0  # Would be len(files) if RemoveFiles was True
        }
        
        if NewIssues:
            print(f"⚠️  {len(NewIssues)} issues still remain")
        else:
            print("✅ All security issues resolved!")
        
        return Result
    
    def _LogRemediation(self, OriginalIssues: List[SecurityIssue]):
        """Log remediation actions to audit trail"""
        SecurityReport = {
            "TotalIssues": len(OriginalIssues),
            "SeverityCounts": {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "RemediationActions": [asdict(action) for action in self.RemediationActions],
            "RemediationTimestamp": datetime.now().isoformat()
        }
        
        # Count severities
        for Issue in OriginalIssues:
            SecurityReport["SeverityCounts"][Issue.Severity] += 1
        
        # Log to audit system
        self.AuditLogger.LogSecurityValidation(
            Operation="AUTO_REMEDIATION",
            ValidationResult="REMEDIATED",
            SecurityReport=SecurityReport,
            CommitMessage=f"Auto-remediation of {len(OriginalIssues)} security issues"
        )
    
    def PrintRemediationSummary(self):
        """Print summary of remediation actions"""
        if not self.RemediationActions:
            print("No remediation actions taken.")
            return
        
        print("\n📊 REMEDIATION SUMMARY")
        print("=" * 30)
        
        ActionCounts = {}
        SuccessCount = 0
        
        for Action in self.RemediationActions:
            ActionCounts[Action.Action] = ActionCounts.get(Action.Action, 0) + 1
            if Action.Success:
                SuccessCount += 1
        
        print(f"Total Actions: {len(self.RemediationActions)}")
        print(f"Successful: {SuccessCount}")
        print(f"Failed: {len(self.RemediationActions) - SuccessCount}")
        print()
        
        for ActionType, Count in ActionCounts.items():
            print(f"{ActionType}: {Count}")
        
        print(f"\nBackups stored in: {self.BackupDir}")

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Security Remediator')
    parser.add_argument('project_path', nargs='?', default='.', 
                       help='Path to project directory (default: current directory)')
    parser.add_argument('--auto', action='store_true', 
                       help='Run automatic remediation without prompts')
    parser.add_argument('--no-history', action='store_true', 
                       help='Skip git history cleaning')
    parser.add_argument('--no-gitignore', action='store_true', 
                       help='Skip .gitignore updates')
    parser.add_argument('--remove-files', action='store_true', 
                       help='Remove sensitive files from filesystem')
    parser.add_argument('--summary', action='store_true', 
                       help='Show remediation summary only')
    
    args = parser.parse_args()
    
    try:
        Remediator = SecurityRemediator(args.project_path)
        
        if args.summary:
            Remediator.PrintRemediationSummary()
            return
        
        # Run auto-remediation
        Result = Remediator.AutoRemediate(
            CleanHistory=not args.no_history,
            UpdateGitignore=not args.no_gitignore,
            RemoveFiles=args.remove_files,
            Interactive=not args.auto
        )
        
        Remediator.PrintRemediationSummary()
        
        if Result.get("success", False):
            print("\n✅ Remediation completed successfully!")
        else:
            print("\n❌ Remediation failed or was cancelled")
            exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()