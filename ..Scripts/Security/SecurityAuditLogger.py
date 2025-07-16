# File: SecurityAuditLogger.py
# Path: Scripts/Security/SecurityAuditLogger.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-14
# Last Modified: 2025-07-14  11:26AM
"""
Security Audit Logger - Maintains audit trail logs for security validation
performed during git operations.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class SecurityAuditEntry:
    """Represents a single security audit entry"""
    Timestamp: str
    Operation: str  # 'INITIAL_COMMIT', 'AUTO_UPDATE', 'MANUAL_COMMIT'
    ProjectPath: str
    GitUser: str
    GitEmail: str
    ValidationResult: str  # 'PASSED', 'FAILED', 'BLOCKED'
    IssuesFound: int
    CriticalIssues: int
    HighIssues: int
    MediumIssues: int
    LowIssues: int
    CommitHash: Optional[str] = None
    CommitMessage: Optional[str] = None
    FilesChanged: List[str] = None
    SecurityReport: Dict = None

class SecurityAuditLogger:
    """Manages security audit logging"""
    
    def __init__(self, ProjectPath: str = "."):
        self.ProjectPath = Path(ProjectPath).resolve()
        self.AuditDir = self.ProjectPath / "Docs" / "Security"
        self.AuditDir.mkdir(parents=True, exist_ok=True)
        
        # Create audit files
        self.DailyLogFile = self.AuditDir / f"audit_{datetime.now().strftime('%Y-%m-%d')}.json"
        self.SummaryFile = self.AuditDir / "audit_summary.json"
        self.ConfigFile = self.AuditDir / "audit_config.json"
        
        # Initialize config if needed
        self._InitializeConfig()
    
    def _InitializeConfig(self):
        """Initialize audit configuration"""
        if not self.ConfigFile.exists():
            Config = {
                "audit_enabled": True,
                "log_retention_days": 90,
                "block_on_critical": True,
                "block_on_high": False,
                "notification_level": "INFO",
                "created": datetime.now().isoformat(),
                "project_path": str(self.ProjectPath)
            }
            
            with open(self.ConfigFile, 'w') as f:
                json.dump(Config, f, indent=2)
    
    def _GetGitUserInfo(self) -> tuple:
        """Get git user information"""
        try:
            import subprocess
            
            user = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True, text=True, cwd=self.ProjectPath
            ).stdout.strip()
            
            email = subprocess.run(
                ['git', 'config', 'user.email'],
                capture_output=True, text=True, cwd=self.ProjectPath
            ).stdout.strip()
            
            return user or "unknown", email or "unknown"
        except:
            return "unknown", "unknown"
    
    def _GetCommitInfo(self) -> tuple:
        """Get latest commit information"""
        try:
            import subprocess
            
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, cwd=self.ProjectPath
            )
            
            message_result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True, text=True, cwd=self.ProjectPath
            )
            
            commit_hash = hash_result.stdout.strip() if hash_result.returncode == 0 else None
            commit_message = message_result.stdout.strip() if message_result.returncode == 0 else None
            
            return commit_hash, commit_message
        except:
            return None, None
    
    def _GetChangedFiles(self) -> List[str]:
        """Get list of changed files"""
        try:
            import subprocess
            
            # Get staged files
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True, text=True, cwd=self.ProjectPath
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n') if result.stdout.strip() else []
            return []
        except:
            return []
    
    def LogSecurityValidation(self, Operation: str, ValidationResult: str, 
                            SecurityReport: Dict, CommitMessage: str = None) -> SecurityAuditEntry:
        """Log a security validation event"""
        
        # Extract issue counts from report
        SeverityCounts = SecurityReport.get('SeverityCounts', {})
        
        # Get git information
        GitUser, GitEmail = self._GetGitUserInfo()
        CommitHash, ActualCommitMessage = self._GetCommitInfo()
        ChangedFiles = self._GetChangedFiles()
        
        # Create audit entry
        Entry = SecurityAuditEntry(
            Timestamp=datetime.now().isoformat(),
            Operation=Operation,
            ProjectPath=str(self.ProjectPath),
            GitUser=GitUser,
            GitEmail=GitEmail,
            ValidationResult=ValidationResult,
            IssuesFound=SecurityReport.get('TotalIssues', 0),
            CriticalIssues=SeverityCounts.get('CRITICAL', 0),
            HighIssues=SeverityCounts.get('HIGH', 0),
            MediumIssues=SeverityCounts.get('MEDIUM', 0),
            LowIssues=SeverityCounts.get('LOW', 0),
            CommitHash=CommitHash,
            CommitMessage=CommitMessage or ActualCommitMessage,
            FilesChanged=ChangedFiles,
            SecurityReport=SecurityReport
        )
        
        # Write to daily log
        self._WriteToDailyLog(Entry)
        
        # Update summary
        self._UpdateSummary(Entry)
        
        return Entry
    
    def _WriteToDailyLog(self, Entry: SecurityAuditEntry):
        """Write entry to daily log file"""
        Entries = []
        
        # Read existing entries
        if self.DailyLogFile.exists():
            try:
                with open(self.DailyLogFile, 'r') as f:
                    Entries = json.load(f)
            except:
                Entries = []
        
        # Add new entry
        Entries.append(asdict(Entry))
        
        # Write back
        with open(self.DailyLogFile, 'w') as f:
            json.dump(Entries, f, indent=2)
    
    def _UpdateSummary(self, Entry: SecurityAuditEntry):
        """Update summary statistics"""
        Summary = {
            "last_updated": datetime.now().isoformat(),
            "total_validations": 0,
            "validations_passed": 0,
            "validations_failed": 0,
            "validations_blocked": 0,
            "total_issues_found": 0,
            "critical_issues_found": 0,
            "high_issues_found": 0,
            "recent_activity": []
        }
        
        # Read existing summary
        if self.SummaryFile.exists():
            try:
                with open(self.SummaryFile, 'r') as f:
                    Summary = json.load(f)
            except:
                pass
        
        # Update counters
        Summary["total_validations"] += 1
        Summary["total_issues_found"] += Entry.IssuesFound
        Summary["critical_issues_found"] += Entry.CriticalIssues
        Summary["high_issues_found"] += Entry.HighIssues
        
        if Entry.ValidationResult == "PASSED":
            Summary["validations_passed"] += 1
        elif Entry.ValidationResult == "FAILED":
            Summary["validations_failed"] += 1
        elif Entry.ValidationResult == "BLOCKED":
            Summary["validations_blocked"] += 1
        
        # Add to recent activity (keep last 10)
        RecentEntry = {
            "timestamp": Entry.Timestamp,
            "operation": Entry.Operation,
            "result": Entry.ValidationResult,
            "issues": Entry.IssuesFound,
            "commit_message": Entry.CommitMessage
        }
        
        Summary["recent_activity"].append(RecentEntry)
        if len(Summary["recent_activity"]) > 10:
            Summary["recent_activity"] = Summary["recent_activity"][-10:]
        
        # Write summary
        with open(self.SummaryFile, 'w') as f:
            json.dump(Summary, f, indent=2)
    
    def GetAuditSummary(self) -> Dict:
        """Get audit summary statistics"""
        if self.SummaryFile.exists():
            try:
                with open(self.SummaryFile, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def GetRecentAudits(self, Days: int = 7) -> List[Dict]:
        """Get recent audit entries"""
        RecentEntries = []
        
        # Check last N days
        for i in range(Days):
            Date = datetime.now() - datetime.timedelta(days=i)
            LogFile = self.AuditDir / f"audit_{Date.strftime('%Y-%m-%d')}.json"
            
            if LogFile.exists():
                try:
                    with open(LogFile, 'r') as f:
                        DailyEntries = json.load(f)
                        RecentEntries.extend(DailyEntries)
                except:
                    continue
        
        # Sort by timestamp (newest first)
        RecentEntries.sort(key=lambda x: x['Timestamp'], reverse=True)
        return RecentEntries
    
    def PrintAuditNotification(self, Entry: SecurityAuditEntry):
        """Print formatted audit notification"""
        Icon = {
            'PASSED': '✅',
            'FAILED': '⚠️',
            'BLOCKED': '🚫'
        }
        
        print(f"\n{Icon.get(Entry.ValidationResult, '📋')} SECURITY AUDIT LOG")
        print(f"   Operation: {Entry.Operation}")
        print(f"   Result: {Entry.ValidationResult}")
        print(f"   Issues Found: {Entry.IssuesFound}")
        
        if Entry.CriticalIssues > 0:
            print(f"   🚨 Critical: {Entry.CriticalIssues}")
        if Entry.HighIssues > 0:
            print(f"   ⚠️  High: {Entry.HighIssues}")
        if Entry.MediumIssues > 0:
            print(f"   💡 Medium: {Entry.MediumIssues}")
        if Entry.LowIssues > 0:
            print(f"   ℹ️  Low: {Entry.LowIssues}")
        
        print(f"   Logged: {Entry.Timestamp}")
        print(f"   Audit Trail: {self.DailyLogFile}")
        print()
    
    def CleanupOldLogs(self, RetentionDays: int = 90):
        """Clean up audit logs older than retention period"""
        CutoffDate = datetime.now() - datetime.timedelta(days=RetentionDays)
        
        for LogFile in self.AuditDir.glob("audit_*.json"):
            try:
                # Extract date from filename
                DateStr = LogFile.stem.replace("audit_", "")
                FileDate = datetime.strptime(DateStr, "%Y-%m-%d")
                
                if FileDate < CutoffDate:
                    LogFile.unlink()
                    print(f"Deleted old audit log: {LogFile}")
            except:
                continue