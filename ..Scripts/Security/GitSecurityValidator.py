# File: GitSecurityValidator.py
# Path: Scripts/Security/GitSecurityValidator.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-14
# Last Modified: 2025-07-14  11:21AM
"""
Git Security Validator - Scans projects for security issues in .gitignore files
and identifies potential credential exposure risks.
"""

import os
import re
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SecurityIssue:
    """Represents a security issue found in the project"""
    Severity: str  # 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    Category: str  # 'OVERLY_BROAD', 'EXPOSED_CREDENTIALS', 'MISSING_PROTECTION'
    Description: str
    FilePath: str
    LineNumber: Optional[int] = None
    Recommendation: str = ""

class GitSecurityValidator:
    """Validates git repositories for security issues"""
    
    def __init__(self, ProjectPath: str):
        self.ProjectPath = Path(ProjectPath)
        self.Issues: List[SecurityIssue] = []
        
        # Dangerous patterns in .gitignore
        self.DangerousPatterns = [
            r'^\*\.json$',
            r'^\*\.js$',
            r'^\*\.py$',
            r'^\*\.env$',
            r'^\*\.key$',
            r'^\*\.pem$',
            r'^\*\.p12$',
            r'^\*\.pfx$'
        ]
        
        # Sensitive file patterns
        self.SensitivePatterns = [
            r'.*credential.*',
            r'.*secret.*',
            r'.*key.*',
            r'.*token.*',
            r'.*password.*',
            r'.*auth.*',
            r'.*api.*key.*',
            r'.*\.pem$',
            r'.*\.p12$',
            r'.*\.pfx$',
            r'.*\.env$',
            r'.*config.*\.json$',
            r'.*settings.*\.json$'
        ]
        
    def ValidateProject(self) -> List[SecurityIssue]:
        """Main validation method"""
        self.Issues = []
        
        # Check if it's a git repository
        if not self._IsGitRepository():
            self.Issues.append(SecurityIssue(
                Severity="LOW",
                Category="MISSING_PROTECTION",
                Description="Directory is not a git repository",
                FilePath=str(self.ProjectPath),
                Recommendation="Initialize git repository if needed"
            ))
            return self.Issues
        
        # Validate .gitignore
        self._ValidateGitignore()
        
        # Check for exposed sensitive files
        self._CheckExposedSensitiveFiles()
        
        # Check for sensitive files in working directory
        self._CheckSensitiveFilesInWorkingDir()
        
        return self.Issues
    
    def _IsGitRepository(self) -> bool:
        """Check if directory is a git repository"""
        return (self.ProjectPath / '.git').exists()
    
    def _ValidateGitignore(self):
        """Validate .gitignore file for security issues"""
        GitignorePath = self.ProjectPath / '.gitignore'
        
        if not GitignorePath.exists():
            self.Issues.append(SecurityIssue(
                Severity="MEDIUM",
                Category="MISSING_PROTECTION",
                Description="No .gitignore file found",
                FilePath=str(GitignorePath),
                Recommendation="Create .gitignore file with appropriate exclusions"
            ))
            return
        
        # Read and analyze .gitignore
        with open(GitignorePath, 'r') as f:
            Lines = f.readlines()
        
        for LineNum, Line in enumerate(Lines, 1):
            CleanLine = Line.strip()
            if not CleanLine or CleanLine.startswith('#'):
                continue
                
            # Check for dangerous patterns
            for Pattern in self.DangerousPatterns:
                if re.match(Pattern, CleanLine):
                    self.Issues.append(SecurityIssue(
                        Severity="HIGH",
                        Category="OVERLY_BROAD",
                        Description=f"Overly broad pattern '{CleanLine}' may exclude important files",
                        FilePath=str(GitignorePath),
                        LineNumber=LineNum,
                        Recommendation=f"Replace '{CleanLine}' with specific file patterns"
                    ))
    
    def _CheckExposedSensitiveFiles(self):
        """Check for sensitive files currently tracked in git"""
        try:
            # Get list of tracked files
            Result = subprocess.run(
                ['git', 'ls-files'],
                cwd=self.ProjectPath,
                capture_output=True,
                text=True
            )
            
            if Result.returncode == 0:
                TrackedFiles = Result.stdout.splitlines()
                
                for FilePath in TrackedFiles:
                    for Pattern in self.SensitivePatterns:
                        if re.search(Pattern, FilePath, re.IGNORECASE):
                            self.Issues.append(SecurityIssue(
                                Severity="CRITICAL",
                                Category="EXPOSED_CREDENTIALS",
                                Description=f"Sensitive file '{FilePath}' is tracked in git",
                                FilePath=FilePath,
                                Recommendation=f"Remove with: git rm --cached {FilePath}"
                            ))
                            break
        except Exception as e:
            self.Issues.append(SecurityIssue(
                Severity="LOW",
                Category="MISSING_PROTECTION",
                Description=f"Could not check git tracked files: {str(e)}",
                FilePath=str(self.ProjectPath),
                Recommendation="Manually verify tracked files"
            ))
        
        # Check git history for sensitive files
        self._CheckGitHistoryForSensitiveFiles()
    
    def _CheckGitHistoryForSensitiveFiles(self):
        """Check git history for sensitive files that were previously committed"""
        try:
            # Get all files that have ever existed in git history
            Result = subprocess.run(
                ['git', 'log', '--all', '--full-history', '--name-only', '--pretty=format:'],
                cwd=self.ProjectPath,
                capture_output=True,
                text=True
            )
            
            if Result.returncode == 0:
                HistoryFiles = set(Result.stdout.splitlines())
                HistoryFiles.discard('')  # Remove empty strings
                
                for FilePath in HistoryFiles:
                    for Pattern in self.SensitivePatterns:
                        if re.search(Pattern, FilePath, re.IGNORECASE):
                            # Check if file is currently tracked
                            CurrentlyTracked = self._IsFileCurrentlyTracked(FilePath)
                            
                            if not CurrentlyTracked:
                                self.Issues.append(SecurityIssue(
                                    Severity="CRITICAL",
                                    Category="EXPOSED_CREDENTIALS",
                                    Description=f"Sensitive file '{FilePath}' exists in git history but not in current commit",
                                    FilePath=FilePath,
                                    Recommendation=f"Remove from history with: git filter-branch or BFG Repo-Cleaner"
                                ))
                            break
        except Exception as e:
            self.Issues.append(SecurityIssue(
                Severity="LOW",
                Category="MISSING_PROTECTION",
                Description=f"Could not check git history: {str(e)}",
                FilePath=str(self.ProjectPath),
                Recommendation="Manually verify git history for sensitive files"
            ))
    
    def _IsFileCurrentlyTracked(self, FilePath: str) -> bool:
        """Check if file is currently tracked in git"""
        try:
            Result = subprocess.run(
                ['git', 'ls-files', '--error-unmatch', FilePath],
                cwd=self.ProjectPath,
                capture_output=True,
                text=True
            )
            return Result.returncode == 0
        except:
            return False
    
    def _CheckSensitiveFilesInWorkingDir(self):
        """Check for sensitive files in working directory"""
        for Root, Dirs, Files in os.walk(self.ProjectPath):
            # Skip .git directory
            if '.git' in Dirs:
                Dirs.remove('.git')
                
            for File in Files:
                FilePath = os.path.join(Root, File)
                RelativePath = os.path.relpath(FilePath, self.ProjectPath)
                
                for Pattern in self.SensitivePatterns:
                    if re.search(Pattern, File, re.IGNORECASE):
                        # Check if file is properly ignored
                        if not self._IsFileIgnored(RelativePath):
                            self.Issues.append(SecurityIssue(
                                Severity="HIGH",
                                Category="MISSING_PROTECTION",
                                Description=f"Sensitive file '{RelativePath}' is not ignored",
                                FilePath=RelativePath,
                                Recommendation=f"Add '{RelativePath}' to .gitignore"
                            ))
                        break
    
    def _IsFileIgnored(self, FilePath: str) -> bool:
        """Check if file is ignored by git"""
        try:
            Result = subprocess.run(
                ['git', 'check-ignore', FilePath],
                cwd=self.ProjectPath,
                capture_output=True,
                text=True
            )
            return Result.returncode == 0
        except:
            return False
    
    def GenerateReport(self) -> Dict:
        """Generate security report"""
        SeverityCounts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        CategoryCounts = {}
        
        for Issue in self.Issues:
            SeverityCounts[Issue.Severity] += 1
            CategoryCounts[Issue.Category] = CategoryCounts.get(Issue.Category, 0) + 1
        
        return {
            'ProjectPath': str(self.ProjectPath),
            'TotalIssues': len(self.Issues),
            'SeverityCounts': SeverityCounts,
            'CategoryCounts': CategoryCounts,
            'Issues': [
                {
                    'Severity': Issue.Severity,
                    'Category': Issue.Category,
                    'Description': Issue.Description,
                    'FilePath': Issue.FilePath,
                    'LineNumber': Issue.LineNumber,
                    'Recommendation': Issue.Recommendation
                }
                for Issue in self.Issues
            ]
        }
    
    def PrintReport(self):
        """Print formatted security report"""
        Report = self.GenerateReport()
        
        print("=" * 60)
        print("🔒 GIT SECURITY VALIDATION REPORT")
        print("=" * 60)
        print(f"Project: {Report['ProjectPath']}")
        print(f"Total Issues: {Report['TotalIssues']}")
        print()
        
        # Print severity summary
        print("SEVERITY BREAKDOWN:")
        for Severity, Count in Report['SeverityCounts'].items():
            if Count > 0:
                Icon = {'CRITICAL': '🚨', 'HIGH': '⚠️', 'MEDIUM': '💡', 'LOW': 'ℹ️'}
                print(f"  {Icon[Severity]} {Severity}: {Count}")
        print()
        
        # Print issues by severity
        for Severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            SeverityIssues = [i for i in self.Issues if i.Severity == Severity]
            if SeverityIssues:
                print(f"{Severity} ISSUES:")
                for Issue in SeverityIssues:
                    print(f"  • {Issue.Description}")
                    print(f"    File: {Issue.FilePath}")
                    if Issue.LineNumber:
                        print(f"    Line: {Issue.LineNumber}")
                    if Issue.Recommendation:
                        print(f"    Fix: {Issue.Recommendation}")
                    print()

def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Git Security Validator')
    parser.add_argument('project_path', nargs='?', default='.', 
                       help='Path to project directory (default: current directory)')
    parser.add_argument('--json', action='store_true', 
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    # Validate project
    Validator = GitSecurityValidator(args.project_path)
    Issues = Validator.ValidateProject()
    
    if args.json:
        print(json.dumps(Validator.GenerateReport(), indent=2))
    else:
        Validator.PrintReport()
    
    # Exit with error code if critical issues found
    CriticalIssues = [i for i in Issues if i.Severity == 'CRITICAL']
    if CriticalIssues:
        exit(1)

if __name__ == "__main__":
    main()