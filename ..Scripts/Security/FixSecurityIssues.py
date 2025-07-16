#!/usr/bin/env python3
# File: FixSecurityIssues.py
# Path: Scripts/Security/FixSecurityIssues.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-14
# Last Modified: 2025-07-14  12:35PM
"""
Security Issues Auto-Fixer - Standalone script for fixing security issues
detected by GitSecurityValidator with comprehensive logging and backup.
"""

import sys
import argparse
from pathlib import Path

# Add Security directory to path for imports
sys.path.append(str(Path(__file__).parent))

from GitSecurityValidator import GitSecurityValidator
from SecurityRemediator import SecurityRemediator
from SecurityAuditLogger import SecurityAuditLogger

def main():
    """Main function for security auto-fixer"""
    parser = argparse.ArgumentParser(
        description="Automatically fix security issues in git repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode - prompts before destructive operations
  python FixSecurityIssues.py
  
  # Automatic mode - fixes all issues without prompts
  python FixSecurityIssues.py --auto
  
  # Skip history cleaning (faster, but leaves traces)
  python FixSecurityIssues.py --no-history
  
  # Only validate, don't fix
  python FixSecurityIssues.py --validate-only
  
  # Show what would be fixed without doing it
  python FixSecurityIssues.py --dry-run
        """
    )
    
    parser.add_argument("project_path", nargs="?", default=".", 
                       help="Path to git repository (default: current directory)")
    parser.add_argument("--auto", action="store_true", 
                       help="Automatic mode - fix all issues without prompts")
    parser.add_argument("--validate-only", action="store_true", 
                       help="Only validate security, don't fix issues")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be fixed without doing it")
    parser.add_argument("--no-history", action="store_true", 
                       help="Skip git history cleaning (faster)")
    parser.add_argument("--no-gitignore", action="store_true", 
                       help="Skip .gitignore updates")
    parser.add_argument("--remove-files", action="store_true", 
                       help="Remove sensitive files from filesystem")
    parser.add_argument("--force-push", action="store_true", 
                       help="Automatically force push after history cleaning")
    parser.add_argument("--quiet", "-q", action="store_true", 
                       help="Quiet mode - minimal output")
    
    args = parser.parse_args()
    
    try:
        ProjectPath = Path(args.project_path).resolve()
        
        if not (ProjectPath / '.git').exists():
            print(f"❌ Error: '{ProjectPath}' is not a git repository")
            sys.exit(1)
        
        if not args.quiet:
            print("🔒 SECURITY ISSUES AUTO-FIXER")
            print("=" * 50)
            print(f"Project: {ProjectPath}")
            print()
        
        # Initialize components
        Validator = GitSecurityValidator(str(ProjectPath))
        Remediator = SecurityRemediator(str(ProjectPath))
        AuditLogger = SecurityAuditLogger(str(ProjectPath))
        
        # Validate current security status
        if not args.quiet:
            print("🔍 SCANNING FOR SECURITY ISSUES")
            print("-" * 30)
        
        Issues = Validator.ValidateProject()
        SecurityReport = Validator.GenerateReport()
        
        if not Issues:
            if not args.quiet:
                print("✅ No security issues found!")
            sys.exit(0)
        
        # Print issue summary
        if not args.quiet:
            print(f"📋 Found {len(Issues)} security issues:")
            SeverityCounts = SecurityReport['SeverityCounts']
            if SeverityCounts['CRITICAL'] > 0:
                print(f"   🚨 Critical: {SeverityCounts['CRITICAL']}")
            if SeverityCounts['HIGH'] > 0:
                print(f"   ⚠️  High: {SeverityCounts['HIGH']}")
            if SeverityCounts['MEDIUM'] > 0:
                print(f"   💡 Medium: {SeverityCounts['MEDIUM']}")
            if SeverityCounts['LOW'] > 0:
                print(f"   ℹ️  Low: {SeverityCounts['LOW']}")
            print()
        
        # Detailed issue listing
        if not args.quiet and not args.dry_run:
            print("📝 DETAILED ISSUES:")
            for Issue in Issues:
                print(f"   {Issue.Severity}: {Issue.Description}")
                if Issue.Recommendation:
                    print(f"      Fix: {Issue.Recommendation}")
            print()
        
        # Validate-only mode
        if args.validate_only:
            print("✅ Validation complete (no fixes applied)")
            sys.exit(1 if SeverityCounts['CRITICAL'] > 0 or SeverityCounts['HIGH'] > 0 else 0)
        
        # Dry-run mode
        if args.dry_run:
            print("🔍 DRY RUN - Actions that would be taken:")
            
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
            
            if TrackedFiles:
                print(f"   📤 Remove {len(TrackedFiles)} files from git tracking")
                for File in TrackedFiles:
                    print(f"      - {File}")
            
            if HistoryFiles and not args.no_history:
                print(f"   🧹 Clean {len(HistoryFiles)} files from git history")
                for File in HistoryFiles:
                    print(f"      - {File}")
            
            if UnignoredFiles and not args.no_gitignore:
                print(f"   📝 Add {len(UnignoredFiles)} files to .gitignore")
                for File in UnignoredFiles:
                    print(f"      - {File}")
            
            if args.remove_files:
                AllSensitiveFiles = list(set(TrackedFiles + HistoryFiles + UnignoredFiles))
                print(f"   🗑️  Remove {len(AllSensitiveFiles)} files from filesystem")
            
            print("\n💡 Run without --dry-run to apply these fixes")
            sys.exit(0)
        
        # Perform remediation
        if not args.quiet:
            print("🔧 STARTING REMEDIATION")
            print("-" * 30)
        
        RemediationResult = Remediator.AutoRemediate(
            CleanHistory=not args.no_history,
            UpdateGitignore=not args.no_gitignore,
            RemoveFiles=args.remove_files,
            Interactive=not args.auto
        )
        
        if RemediationResult.get("cancelled", False):
            print("❌ Remediation cancelled by user")
            sys.exit(1)
        
        if not RemediationResult.get("success", False):
            print("❌ Remediation failed")
            sys.exit(1)
        
        # Post-remediation validation
        if not args.quiet:
            print("\n🔍 POST-REMEDIATION VALIDATION")
            print("-" * 30)
        
        NewIssues = Validator.ValidateProject()
        NewSecurityReport = Validator.GenerateReport()
        
        if not args.quiet:
            IssuesResolved = len(Issues) - len(NewIssues)
            print(f"✅ Resolved {IssuesResolved} of {len(Issues)} issues")
            
            if NewIssues:
                print(f"⚠️  {len(NewIssues)} issues remain:")
                for Issue in NewIssues:
                    print(f"   {Issue.Severity}: {Issue.Description}")
            else:
                print("🎉 All security issues resolved!")
        
        # Force push if requested and history was cleaned
        if args.force_push and not args.no_history and RemediationResult.get("history_files_cleaned", 0) > 0:
            if not args.quiet:
                print("\n🚀 FORCE PUSHING TO REMOTE")
                print("-" * 30)
            
            import subprocess
            try:
                Result = subprocess.run(
                    ["git", "push", "--force", "--all"],
                    cwd=ProjectPath,
                    capture_output=True,
                    text=True
                )
                
                if Result.returncode == 0:
                    print("✅ Force push completed successfully")
                else:
                    print("❌ Force push failed:")
                    print(Result.stderr)
            except Exception as e:
                print(f"❌ Force push failed: {e}")
        
        # Print remediation summary
        if not args.quiet:
            print("\n📊 REMEDIATION SUMMARY")
            print("-" * 30)
            Result = RemediationResult
            print(f"Issues Found: {Result.get('issues_found', 0)}")
            print(f"Issues Remaining: {Result.get('issues_remaining', 0)}")
            print(f"Files Removed from Tracking: {Result.get('tracked_files_removed', 0)}")
            print(f"Files Cleaned from History: {Result.get('history_files_cleaned', 0)}")
            print(f"Files Added to .gitignore: {Result.get('gitignore_updated', 0)}")
            
            if Result.get('history_files_cleaned', 0) > 0 and not args.force_push:
                print("\n⚠️  IMPORTANT: Git history was rewritten!")
                print("   Run 'git push --force --all' to update remote repository")
                print("   Team members will need to re-clone the repository")
        
        # Exit with appropriate code
        sys.exit(0 if len(NewIssues) == 0 else 1)
        
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()