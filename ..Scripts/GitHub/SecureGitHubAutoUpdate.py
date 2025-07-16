#!/usr/bin/env python3
# File: SecureGitHubAutoUpdate.py
# Path: Scripts/GitHub/SecureGitHubAutoUpdate.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-14
# Last Modified: 2025-07-14  11:30AM
"""
Secure GitHub Auto-Update Script - Enhanced with security validation and audit logging.
Performs comprehensive security checks before any git operations.
"""

import os
import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
import argparse

# Add Scripts directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from Security.GitSecurityValidator import GitSecurityValidator
from Security.SecurityAuditLogger import SecurityAuditLogger
from Security.SecurityRemediator import SecurityRemediator

class SecureGitHubAutoUpdater:
    """Enhanced GitHub auto-updater with security validation"""
    
    def __init__(self, RepoPath=None, RemoteName="origin", Branch="main"):
        """Initialize the secure GitHub auto-updater"""
        self.RepoPath = Path(RepoPath) if RepoPath else Path.cwd()
        self.RemoteName = RemoteName
        self.Branch = Branch
        
        # Initialize security components
        self.SecurityValidator = GitSecurityValidator(str(self.RepoPath))
        self.AuditLogger = SecurityAuditLogger(str(self.RepoPath))
        self.SecurityRemediator = SecurityRemediator(str(self.RepoPath))
        
        # Ensure we're in a git repository
        if not (self.RepoPath / '.git').exists():
            raise Exception(f"Not a git repository: {self.RepoPath}")
    
    def RunGitCommand(self, Command):
        """Execute git command and return result"""
        try:
            Result = subprocess.run(
                Command,
                cwd=self.RepoPath,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return Result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {Command}")
            print(f"Error: {e.stderr}")
            raise
    
    def CheckGitStatus(self):
        """Check if there are any changes to commit"""
        try:
            # Check for unstaged changes
            Unstaged = self.RunGitCommand("git diff --name-only")
            
            # Check for staged changes
            Staged = self.RunGitCommand("git diff --cached --name-only")
            
            # Check for untracked files
            Untracked = self.RunGitCommand("git ls-files --others --exclude-standard")
            
            Changes = {
                'unstaged': Unstaged.split('\n') if Unstaged else [],
                'staged': Staged.split('\n') if Staged else [],
                'untracked': Untracked.split('\n') if Untracked else []
            }
            
            return Changes
        except Exception as e:
            print(f"Error checking git status: {e}")
            return None
    
    def PerformSecurityValidation(self, Operation="AUTO_UPDATE") -> bool:
        """Perform comprehensive security validation"""
        print("🔒 PERFORMING SECURITY VALIDATION")
        print("-" * 30)
        
        # Run validation
        Issues = self.SecurityValidator.ValidateProject()
        SecurityReport = self.SecurityValidator.GenerateReport()
        
        # Print condensed report
        print(f"📋 Security Scan: {SecurityReport['TotalIssues']} issues found")
        
        SeverityCounts = SecurityReport['SeverityCounts']
        if SeverityCounts['CRITICAL'] > 0:
            print(f"   🚨 Critical: {SeverityCounts['CRITICAL']}")
        if SeverityCounts['HIGH'] > 0:
            print(f"   ⚠️  High: {SeverityCounts['HIGH']}")
        if SeverityCounts['MEDIUM'] > 0:
            print(f"   💡 Medium: {SeverityCounts['MEDIUM']}")
        if SeverityCounts['LOW'] > 0:
            print(f"   ℹ️  Low: {SeverityCounts['LOW']}")
        
        # Determine if we should block the commit
        BlockOnCritical = SeverityCounts['CRITICAL'] > 0
        BlockOnHigh = False  # Set to True if you want to block on HIGH issues
        
        ShouldBlock = BlockOnCritical or BlockOnHigh
        
        if ShouldBlock:
            print("\n🚫 UPDATE BLOCKED - Security issues found!")
            
            # Show critical and high issues
            for Issue in Issues:
                if Issue.Severity in ['CRITICAL', 'HIGH']:
                    print(f"   {Issue.Severity}: {Issue.Description}")
                    if Issue.Recommendation:
                        print(f"      Fix: {Issue.Recommendation}")
            
            # Offer automatic remediation
            print("\n🔧 AUTOMATIC REMEDIATION AVAILABLE")
            Response = input("Would you like to automatically fix these issues? (y/N): ").lower()
            
            if Response == 'y':
                print("\n🔄 Starting automatic remediation...")
                RemediationResult = self.SecurityRemediator.AutoRemediate(
                    CleanHistory=True,
                    UpdateGitignore=True,
                    RemoveFiles=False,
                    Interactive=False
                )
                
                if RemediationResult.get("success", False):
                    print("✅ Automatic remediation completed!")
                    print("🔍 Re-validating security...")
                    
                    # Re-validate after remediation
                    NewIssues = self.SecurityValidator.ValidateProject()
                    NewSecurityReport = self.SecurityValidator.GenerateReport()
                    
                    if NewSecurityReport['SeverityCounts']['CRITICAL'] == 0:
                        print("✅ Security validation now passes!")
                        return True
                    else:
                        print("❌ Some critical issues remain - commit still blocked")
                        return False
                else:
                    print("❌ Automatic remediation failed")
            
            # Log the blocked attempt
            AuditEntry = self.AuditLogger.LogSecurityValidation(
                Operation=Operation,
                ValidationResult="BLOCKED",
                SecurityReport=SecurityReport,
                CommitMessage="Auto-update blocked due to security issues"
            )
            self.AuditLogger.PrintAuditNotification(AuditEntry)
            
            print("\n📚 Fix these issues before committing.")
            return False
        
        elif SecurityReport['TotalIssues'] > 0:
            print(f"✅ Security validation passed with {SecurityReport['TotalIssues']} minor issues.")
            
            # Log successful validation with warnings
            AuditEntry = self.AuditLogger.LogSecurityValidation(
                Operation=Operation,
                ValidationResult="PASSED",
                SecurityReport=SecurityReport
            )
            self.AuditLogger.PrintAuditNotification(AuditEntry)
        
        else:
            print("✅ Security validation passed - No issues found!")
            
            # Log clean validation
            AuditEntry = self.AuditLogger.LogSecurityValidation(
                Operation=Operation,
                ValidationResult="PASSED",
                SecurityReport=SecurityReport
            )
            self.AuditLogger.PrintAuditNotification(AuditEntry)
        
        return True
    
    def AddFiles(self, Files=None):
        """Add files to staging area"""
        if Files:
            for File in Files:
                self.RunGitCommand(f"git add {File}")
        else:
            # Add all changes
            self.RunGitCommand("git add .")
    
    def CreateCommit(self, Message=None, AutoMessage=True):
        """Create a commit with given message"""
        if not Message and AutoMessage:
            Timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Message = f"Auto-update: {Timestamp}"
        elif not Message:
            raise ValueError("Commit message required when AutoMessage=False")
        
        self.RunGitCommand(f'git commit -m "{Message}"')
        return Message
    
    def PushToGitHub(self):
        """Push changes to GitHub"""
        PushCommand = f"git push {self.RemoteName} {self.Branch}"
        self.RunGitCommand(PushCommand)
    
    def SecureAutoUpdate(self, CommitMessage=None, Files=None, Verbose=True):
        """
        Complete secure auto-update workflow: validate, add, commit, push
        """
        if Verbose:
            print("🔐 SECURE AUTO-UPDATE PROCESS")
            print("=" * 40)
        
        try:
            # STEP 1: Security validation
            if not self.PerformSecurityValidation("AUTO_UPDATE"):
                if Verbose:
                    print("❌ Auto-update aborted due to security issues")
                return False
            
            # STEP 2: Check for changes
            Changes = self.CheckGitStatus()
            if not Changes:
                if Verbose:
                    print("❌ Error checking repository status")
                return False
            
            TotalChanges = len(Changes['unstaged']) + len(Changes['staged']) + len(Changes['untracked'])
            
            if TotalChanges == 0:
                if Verbose:
                    print("✅ No changes detected. Repository is up to date.")
                return True
            
            if Verbose:
                print(f"📁 Found {TotalChanges} changed/new files:")
                for File in Changes['unstaged'] + Changes['untracked']:
                    if File:  # Skip empty strings
                        print(f"   - {File}")
            
            # STEP 3: Add files
            if Verbose:
                print("📤 Adding files to staging area...")
            self.AddFiles(Files)
            
            # STEP 4: Create commit
            if Verbose:
                print("💾 Creating commit...")
            CommitMsg = self.CreateCommit(CommitMessage)
            
            # STEP 5: Push to GitHub
            if Verbose:
                print("🚀 Pushing to GitHub...")
            self.PushToGitHub()
            
            # STEP 6: Log successful operation
            PostCommitReport = self.SecurityValidator.GenerateReport()
            self.AuditLogger.LogSecurityValidation(
                Operation="AUTO_UPDATE",
                ValidationResult="PASSED",
                SecurityReport=PostCommitReport,
                CommitMessage=CommitMsg
            )
            
            if Verbose:
                print(f"✅ Secure auto-update completed successfully!")
                print(f"   Commit: {CommitMsg}")
                print(f"   Branch: {self.Branch}")
                print(f"   Security: VALIDATED")
                print(f"   Audit Log: {self.AuditLogger.DailyLogFile}")
            
            return True
            
        except Exception as e:
            # Log failed operation
            FailedReport = self.SecurityValidator.GenerateReport()
            self.AuditLogger.LogSecurityValidation(
                Operation="AUTO_UPDATE",
                ValidationResult="FAILED",
                SecurityReport=FailedReport,
                CommitMessage=f"Failed auto-update: {str(e)}"
            )
            
            if Verbose:
                print(f"❌ Error during secure auto-update: {e}")
            return False
    
    def GetSecuritySummary(self):
        """Get security audit summary"""
        return self.AuditLogger.GetAuditSummary()
    
    def PrintSecuritySummary(self):
        """Print security audit summary"""
        Summary = self.GetSecuritySummary()
        
        if Summary:
            print("\n📊 SECURITY AUDIT SUMMARY")
            print("=" * 30)
            print(f"Total Validations: {Summary.get('total_validations', 0)}")
            print(f"Passed: {Summary.get('validations_passed', 0)}")
            print(f"Failed: {Summary.get('validations_failed', 0)}")
            print(f"Blocked: {Summary.get('validations_blocked', 0)}")
            print(f"Critical Issues Found: {Summary.get('critical_issues_found', 0)}")
            print(f"High Issues Found: {Summary.get('high_issues_found', 0)}")
            print(f"Last Updated: {Summary.get('last_updated', 'Unknown')}")
            print()

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description="Secure GitHub Auto-Update Script")
    parser.add_argument("--path", default=".", help="Repository path (default: current directory)")
    parser.add_argument("--message", "-m", help="Commit message")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (less output)")
    parser.add_argument("--security-summary", "-s", action="store_true", help="Show security summary")
    parser.add_argument("--auto-fix", action="store_true", help="Automatically fix security issues without prompts")
    parser.add_argument("--no-history-clean", action="store_true", help="Skip git history cleaning during auto-fix")
    
    args = parser.parse_args()
    
    try:
        # Initialize secure updater
        Updater = SecureGitHubAutoUpdater(RepoPath=args.path)
        
        if args.security_summary:
            Updater.PrintSecuritySummary()
            return
        
        # Auto-fix security issues if requested
        if args.auto_fix:
            print("🔧 PRE-COMMIT AUTO-FIX ENABLED")
            print("=" * 40)
            
            RemediationResult = Updater.SecurityRemediator.AutoRemediate(
                CleanHistory=not args.no_history_clean,
                UpdateGitignore=True,
                RemoveFiles=False,
                Interactive=False
            )
            
            if RemediationResult.get("success", False):
                print("✅ Auto-fix completed successfully!")
            else:
                print("❌ Auto-fix failed")
                sys.exit(1)
        
        # Perform secure auto-update
        Success = Updater.SecureAutoUpdate(
            CommitMessage=args.message,
            Verbose=not args.quiet
        )
        sys.exit(0 if Success else 1)
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()