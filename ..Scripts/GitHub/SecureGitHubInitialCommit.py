#!/usr/bin/env python3
# File: SecureGitHubInitialCommit.py
# Path: Scripts/GitHub/SecureGitHubInitialCommit.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-14
# Last Modified: 2025-07-14  11:28AM
"""
Secure Initial Commit and Push Script - Enhanced with security validation
and audit logging. Performs comprehensive security checks before any git operations.
"""

import subprocess
import sys
import os
from pathlib import Path

# Add Scripts directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from Security.GitSecurityValidator import GitSecurityValidator
from Security.SecurityAuditLogger import SecurityAuditLogger

def RunCommand(Command, Description, Check=True):
    """Run a shell command and handle errors."""
    print(f"-> {Description}")
    try:
        Result = subprocess.run(Command, shell=True, capture_output=True, text=True)
        if Result.stdout:
            print(Result.stdout.strip())
        if Result.stderr:
            print(Result.stderr.strip(), file=sys.stderr)
        if Check and Result.returncode != 0:
            print(f"Error: Command failed: {Command}", file=sys.stderr)
            sys.exit(1)
        return Result
    except Exception as e:
        print(f"Exception while running '{Command}': {e}", file=sys.stderr)
        sys.exit(1)

def PerformSecurityValidation(ProjectPath: str, AuditLogger: SecurityAuditLogger) -> bool:
    """Perform comprehensive security validation"""
    print("🔒 PERFORMING SECURITY VALIDATION")
    print("=" * 50)
    
    # Initialize validator
    Validator = GitSecurityValidator(ProjectPath)
    
    # Run validation
    Issues = Validator.ValidateProject()
    SecurityReport = Validator.GenerateReport()
    
    # Print condensed report
    print(f"📋 Security Scan Complete:")
    print(f"   Total Issues: {SecurityReport['TotalIssues']}")
    
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
    BlockOnHigh = SeverityCounts['HIGH'] > 0  # You can adjust this policy
    
    ShouldBlock = BlockOnCritical or BlockOnHigh
    
    if ShouldBlock:
        print("\n🚫 COMMIT BLOCKED - Security issues found!")
        print("\nIssues requiring attention:")
        
        # Show critical and high issues
        for Issue in Issues:
            if Issue.Severity in ['CRITICAL', 'HIGH']:
                print(f"   {Issue.Severity}: {Issue.Description}")
                if Issue.Recommendation:
                    print(f"      Fix: {Issue.Recommendation}")
        
        # Log the blocked attempt
        AuditEntry = AuditLogger.LogSecurityValidation(
            Operation="INITIAL_COMMIT",
            ValidationResult="BLOCKED",
            SecurityReport=SecurityReport,
            CommitMessage="Initial commit blocked due to security issues"
        )
        AuditLogger.PrintAuditNotification(AuditEntry)
        
        print("\n📚 Fix these issues and run the script again.")
        print("💡 Tip: Check the full report with:")
        print("   python Scripts/Security/GitSecurityValidator.py")
        
        return False
    
    elif SecurityReport['TotalIssues'] > 0:
        print(f"\n💡 Security validation passed with {SecurityReport['TotalIssues']} minor issues.")
        print("   These issues are informational and won't block the commit.")
        
        # Log successful validation with warnings
        AuditEntry = AuditLogger.LogSecurityValidation(
            Operation="INITIAL_COMMIT",
            ValidationResult="PASSED",
            SecurityReport=SecurityReport
        )
        AuditLogger.PrintAuditNotification(AuditEntry)
    
    else:
        print("\n✅ Security validation passed - No issues found!")
        
        # Log clean validation
        AuditEntry = AuditLogger.LogSecurityValidation(
            Operation="INITIAL_COMMIT",
            ValidationResult="PASSED",
            SecurityReport=SecurityReport
        )
        AuditLogger.PrintAuditNotification(AuditEntry)
    
    print("=" * 50)
    return True

def main():
    """Create initial commit for the project and push to GitHub with security validation."""
    ProjectName = os.path.basename(os.getcwd())
    ProjectPath = os.getcwd()
    
    print(f"🚀 SECURE INITIAL COMMIT PROCESS")
    print(f"Project: {ProjectName}")
    print("=" * 50)
    
    # Initialize audit logger
    AuditLogger = SecurityAuditLogger(ProjectPath)
    
    # STEP 1: Security validation
    if not PerformSecurityValidation(ProjectPath, AuditLogger):
        sys.exit(1)
    
    # STEP 2: Standard git operations (from original script)
    print("🔐 PROCEEDING WITH GIT OPERATIONS")
    print("=" * 50)
    
    # Check if GitHub CLI is available and authenticated
    RunCommand("gh auth status", "Checking GitHub CLI authentication status")

    # 1. Ensure we are in a git repository
    if not os.path.isdir('.git'):
        print("This is not a git repository.")
        RunCommand("git init", "Initializing new git repository")
    else:
        print("Git repository already exists locally.")

    # 2. Check if the repository on GitHub exists
    print(f"Checking for GitHub repository '{ProjectName}'...")
    RepoCheckResult = RunCommand(f"gh repo view {ProjectName}", "Checking GitHub repository existence", check=False)
    RepoExistsOnGitHub = RepoCheckResult.returncode == 0

    if RepoExistsOnGitHub:
        print("Repository exists on GitHub.")
        # If it exists, check if it's empty.
        # First, ensure remote 'origin' is set up to point to it.
        RemoteCheckResult = RunCommand("git remote get-url origin", "Checking for remote 'origin'", check=False)
        if RemoteCheckResult.returncode != 0:
            GhUser = RunCommand("gh api user --jq .login", "Getting GitHub username").stdout.strip()
            AddRemoteCmd = f"git remote add origin https://github.com/{GhUser}/{ProjectName}.git"
            RunCommand(AddRemoteCmd, "Adding remote 'origin'")
        
        # Now check for commits on the remote.
        RemoteCommitCheck = RunCommand("git ls-remote --heads origin", "Checking for commits on remote", check=False)
        if RemoteCommitCheck.stdout.strip():
            print("GitHub repository is not empty. Aborting script.", file=sys.stderr)
            print("This script is for initializing a project. The remote already has content.", file=sys.stderr)
            sys.exit(1)
        print("GitHub repository is empty. Ready to push.")
    
    # 3. Check for local commits
    LocalCommitCheck = RunCommand("git rev-parse --verify HEAD", "Checking for local commits", check=False)
    HasLocalCommits = LocalCommitCheck.returncode == 0

    if not HasLocalCommits:
        print("No local commits found. Creating initial commit.")
        # Use 'git add -A' to ensure all changes (new, modified, and deleted files) are staged.
        RunCommand("git add -A", "Adding all files and changes to staging area")
        
        # Check if there is anything to commit
        StatusCheck = RunCommand("git status --porcelain", "Checking for changes to commit", check=False)
        if not StatusCheck.stdout.strip():
            print("No changes to commit. Working directory is clean.")
            # If remote is also empty, there is nothing to do.
            if not RepoExistsOnGitHub:
                 print("Aborting because there are no local changes to create a new repository with.")
                 sys.exit(0)
        else:
            CommitMessage = f"Initial commit for {ProjectName}"
            RunCommand(f'git commit -m "{CommitMessage}"', "Creating initial commit")
            
            # Log successful commit
            PostCommitReport = GitSecurityValidator(ProjectPath).GenerateReport()
            AuditLogger.LogSecurityValidation(
                Operation="INITIAL_COMMIT",
                ValidationResult="PASSED",
                SecurityReport=PostCommitReport,
                CommitMessage=CommitMessage
            )
    else:
        print("Local commits already exist.")

    # 4. Push to GitHub
    if not RepoExistsOnGitHub:
        print("Creating new GitHub repository and pushing...")
        # This command creates the repo, sets the remote, and pushes.
        CreateCmd = f"gh repo create {ProjectName} --public --source=. --remote=origin --push"
        RunCommand(CreateCmd, "Creating GitHub repository and pushing initial commit")
    else:
        # The repo exists on GitHub (but is empty), and we have local commits.
        print("Pushing local commits to empty GitHub repository...")
        # Find current branch to push
        BranchName = RunCommand("git symbolic-ref --short HEAD", "Getting current branch name").stdout.strip()
        RunCommand(f"git push -u origin {BranchName}", f"Pushing to origin/{BranchName}")

    print("\n✅ SECURE INITIAL SETUP COMPLETED SUCCESSFULLY!")
    GhUser = RunCommand("gh api user --jq .login", "Getting GitHub username").stdout.strip()
    print(f"🌐 GitHub URL: https://github.com/{GhUser}/{ProjectName}")
    print(f"📋 Security audit logs: {AuditLogger.AuditDir}")
    print(f"🔒 Security validation: PASSED")

if __name__ == "__main__":
    main()