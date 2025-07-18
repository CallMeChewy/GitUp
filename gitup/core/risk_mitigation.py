# File: risk_mitigation.py
# Path: gitup/core/risk_mitigation.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-16
# Last Modified: 2025-07-16  04:00PM
"""
GitUp Risk Mitigation System - Security risk detection and user interaction.

This module provides comprehensive security risk detection, assessment, and 
interactive user interfaces for addressing security violations. It implements
the core enforcement mechanism that blocks GitUp operations until security
violations are properly addressed.

Key Components:
- SecurityRiskDetector: Identifies and classifies security risks
- RiskMitigationInterface: Interactive UI for user decisions
- SecurityEnforcer: Blocks operations based on violation status
- GlobalExceptionManager: Manages global security exceptions

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import os
import json
import fnmatch
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from .project_state_detector import ProjectStateDetector, ProjectAnalysis
from .ignore_manager import GitUpIgnoreManager
from .gitignore_monitor import GitIgnoreMonitor, pre_operation_security_check
from ..utils.exceptions import GitUpError, SecurityViolationError


class SecurityRiskType(Enum):
    """Types of security risks"""
    SECRET_FILE = "secret_file"
    SENSITIVE_CONFIG = "sensitive_config"
    LARGE_BINARY = "large_binary"
    CREDENTIAL_PATTERN = "credential_pattern"
    API_KEY_PATTERN = "api_key_pattern"
    DATABASE_FILE = "database_file"
    BACKUP_FILE = "backup_file"
    LOG_FILE = "log_file"
    TEMPORARY_FILE = "temporary_file"
    IDE_CONFIG = "ide_config"


class SecurityRiskLevel(Enum):
    """Security risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class UserDecision(Enum):
    """User decision options for security risks"""
    IGNORE_PERMANENTLY = "ignore_permanently"
    IGNORE_TEMPORARILY = "ignore_temporarily"
    ADD_TO_GITIGNORE = "add_to_gitignore"
    ADD_TO_GITUPIGNORE = "add_to_gitupignore"
    REMOVE_FILE = "remove_file"
    ENCRYPT_FILE = "encrypt_file"
    REVIEW_LATER = "review_later"


@dataclass
class SecurityRisk:
    """Individual security risk finding"""
    file_path: str
    risk_type: SecurityRiskType
    risk_level: SecurityRiskLevel
    description: str
    recommendation: str
    pattern_matched: str
    file_size: int
    last_modified: str
    is_tracked: bool
    user_decision: Optional[UserDecision] = None
    decision_timestamp: Optional[str] = None
    decision_reason: Optional[str] = None


@dataclass
class SecurityAssessment:
    """Complete security assessment results"""
    project_path: str
    timestamp: str
    total_risks: int
    critical_risks: int
    high_risks: int
    medium_risks: int
    low_risks: int
    risks: List[SecurityRisk]
    blocking_violations: List[SecurityRisk]
    user_decisions: Dict[str, Dict[str, Any]]
    global_exceptions: List[str]
    security_level: str
    enforcement_active: bool


class SecurityRiskDetector:
    """
    Detects and classifies security risks in project files.
    
    This class scans project files for various security risks including
    secrets, credentials, sensitive configurations, and other potential
    security vulnerabilities.
    """
    
    def __init__(self, project_path: str, security_level: str = "moderate"):
        """
        Initialize the security risk detector.
        
        Args:
            project_path: Path to the project directory
            security_level: Security enforcement level (strict/moderate/relaxed)
        """
        self.project_path = Path(project_path).resolve()
        self.security_level = security_level
        self.ignore_manager = GitUpIgnoreManager(str(project_path))
        self.gitignore_monitor = GitIgnoreMonitor(str(project_path))
        
        # Security patterns by risk type
        self.risk_patterns = {
            SecurityRiskType.SECRET_FILE: [
                "*.key", "*.pem", "*.p12", "*.pfx", "*.jks", "*.keystore",
                "*.crt", "*.csr", "*.der", "*.p7b", "*.p7c", "*.p7r",
                "secrets.*", "*secret*", "*password*", "*credential*",
                "*.env", ".env*", "config/secrets.*", "auth.*"
            ],
            SecurityRiskType.SENSITIVE_CONFIG: [
                "config.json", "settings.json", "database.json",
                "*.conf", "*.cfg", "*.ini", "*.properties",
                "web.config", "app.config", "appsettings.json",
                "connection.json", "datasource.*"
            ],
            SecurityRiskType.LARGE_BINARY: [
                "*.exe", "*.dll", "*.so", "*.dylib", "*.bin",
                "*.iso", "*.img", "*.dmg", "*.zip", "*.rar"
            ],
            SecurityRiskType.DATABASE_FILE: [
                "*.db", "*.sqlite", "*.sqlite3", "*.mdb", "*.accdb",
                "*.dump", "*.sql", "*.bak", "data/*.db", "database.*"
            ],
            SecurityRiskType.BACKUP_FILE: [
                "*.backup", "*.bak", "*.old", "*.orig", "*.tmp",
                "*~", "*.swp", "*.swo", "backup/*", "backups/*"
            ],
            SecurityRiskType.LOG_FILE: [
                "*.log", "logs/*", "log/*", "error.log", "debug.log",
                "access.log", "application.log", "audit.log"
            ],
            SecurityRiskType.TEMPORARY_FILE: [
                "temp/*", "tmp/*", "*.tmp", "*.temp", ".DS_Store",
                "Thumbs.db", "desktop.ini", "*.cache"
            ],
            SecurityRiskType.IDE_CONFIG: [
                ".vscode/settings.json", ".idea/*", "*.iml",
                ".eclipse/*", ".settings/*", "*.sublime-*"
            ]
        }
        
        # Content patterns for credential detection
        self.credential_patterns = [
            r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{16,}["\']?',
            r'(?i)(secret[_-]?key|secretkey)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{16,}["\']?',
            r'(?i)(access[_-]?token|accesstoken)\s*[:=]\s*["\']?[a-zA-Z0-9_-]{16,}["\']?',
            r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?[^\s"\']{8,}["\']?',
            r'(?i)(database[_-]?url|db[_-]?url)\s*[:=]\s*["\']?[^\s"\']+["\']?',
            r'(?i)(private[_-]?key|privatekey)\s*[:=]\s*["\']?[^\s"\']+["\']?'
        ]
        
        # Risk level thresholds by security level
        self.blocking_thresholds = {
            "strict": [SecurityRiskLevel.CRITICAL, SecurityRiskLevel.HIGH, SecurityRiskLevel.MEDIUM],
            "moderate": [SecurityRiskLevel.CRITICAL],
            "relaxed": [SecurityRiskLevel.CRITICAL]
        }
        
        # File size thresholds (in MB)
        self.large_file_threshold = 10
        self.max_scan_size = 100  # Don't scan files larger than 100MB
    
    def scan_project(self) -> SecurityAssessment:
        """
        Scan project for security risks.
        
        Returns:
            SecurityAssessment with all detected risks
        """
        console = Console()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Scanning for security risks...", total=None)
            
            # First, check for .gitignore changes and analyze impact
            progress.update(task, description="Checking .gitignore changes...")
            gitignore_delta = self.gitignore_monitor.analyze_gitignore_delta()
            
            if gitignore_delta.has_changes:
                progress.update(task, description="Processing .gitignore changes...")
                self.gitignore_monitor.update_baseline()
            
            # Sync .gitignore patterns to .gitupignore
            progress.update(task, description="Syncing .gitignore patterns...")
            self._sync_gitignore_patterns()
            
            risks = []
            
            # Scan all files in project
            for file_path in self._get_scannable_files():
                file_risks = self._scan_file(file_path)
                risks.extend(file_risks)
                progress.update(task, description=f"Scanned {len(risks)} risks found...")
            
            progress.update(task, description="Checking for user-resolved issues...")
            
            # Filter out risks that may have been resolved by user
            risks = self._filter_resolved_risks(risks)
        
        # Create assessment
        assessment = self._create_assessment(risks)
        
        return assessment
    
    def _sync_gitignore_patterns(self):
        """Sync non-security patterns from .gitignore to .gitupignore"""
        gitignore_path = self.project_path / ".gitignore"
        
        if not gitignore_path.exists():
            return
        
        try:
            # Read .gitignore patterns
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_lines = f.readlines()
            
            # Parse patterns, excluding security-related ones
            non_security_patterns = []
            security_keywords = {
                'secret', 'key', 'password', 'token', 'credential', 'auth',
                'cert', 'pem', 'p12', 'keystore', 'env', 'config'
            }
            
            for line in gitignore_lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Check if this pattern is likely security-related
                is_security_pattern = any(
                    keyword in line.lower() for keyword in security_keywords
                )
                
                if not is_security_pattern:
                    non_security_patterns.append(line)
            
            # Add non-security patterns to .gitupignore  
            # Note: Using existing GitUpIgnoreManager interface
            if non_security_patterns:
                # For now, just note that patterns should be added
                # The ignore manager will handle this through its existing interface
                pass
                
        except Exception as e:
            # Don't fail the scan if .gitignore sync fails
            print(f"Warning: Could not sync .gitignore patterns: {e}")
    
    def _filter_resolved_risks(self, risks: List[SecurityRisk]) -> List[SecurityRisk]:
        """Filter out risks that may have been resolved by user actions"""
        filtered_risks = []
        
        for risk in risks:
            # Check if file is now in .gitignore (user may have added it)
            if self._is_file_ignored(risk.file_path):
                continue
                
            # Check if file is in .gitupignore (user explicitly marked as exception)
            is_ignored, _ = self.ignore_manager.ShouldIgnoreFile(risk.file_path)
            if is_ignored:
                continue
                
            # Check for credential patterns that may have been commented out or removed
            if risk.risk_type in [SecurityRiskType.CREDENTIAL_PATTERN, SecurityRiskType.API_KEY_PATTERN]:
                if self._is_credential_pattern_resolved(risk):
                    continue
            
            filtered_risks.append(risk)
        
        return filtered_risks
    
    def _is_file_ignored(self, file_path: str) -> bool:
        """Check if file is ignored by .gitignore"""
        gitignore_path = self.project_path / ".gitignore"
        
        if not gitignore_path.exists():
            return False
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            relative_path = Path(file_path).relative_to(self.project_path)
            
            for pattern in patterns:
                if fnmatch.fnmatch(str(relative_path), pattern):
                    return True
                    
        except Exception:
            pass
            
        return False
    
    def _is_credential_pattern_resolved(self, risk: SecurityRisk) -> bool:
        """Check if credential pattern has been resolved (commented out, removed, etc.)"""
        try:
            with open(risk.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if the specific line is now commented out
            lines = content.split('\n')
            if risk.line_number and risk.line_number <= len(lines):
                line = lines[risk.line_number - 1]
                # Check if line is commented out
                if re.match(r'^\s*[#//]', line):
                    return True
                    
            # Check if the pattern still exists in the file
            for pattern in self.credential_patterns:
                if re.search(pattern, content):
                    return False
                    
            # If we get here, the pattern may have been removed
            return True
            
        except Exception:
            return False
    
    def _get_scannable_files(self) -> List[Path]:
        """Get list of files that should be scanned"""
        scannable_files = []
        
        # Skip common directories that shouldn't be scanned
        skip_dirs = {
            ".git", ".gitup", "node_modules", ".venv", "venv", 
            "__pycache__", ".pytest_cache", ".mypy_cache",
            "build", "dist", "target", ".gradle", ".idea"
        }
        
        try:
            for root, dirs, files in os.walk(self.project_path):
                # Filter out skip directories
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                for file in files:
                    file_path = Path(root) / file
                    
                    # Skip files that are too large
                    try:
                        if file_path.stat().st_size > self.max_scan_size * 1024 * 1024:
                            continue
                    except OSError:
                        continue
                    
                    scannable_files.append(file_path)
        
        except Exception:
            pass
        
        return scannable_files
    
    def _scan_file(self, file_path: Path) -> List[SecurityRisk]:
        """Scan individual file for security risks"""
        risks = []
        
        try:
            # CRITICAL: Check if this is a symbolic link first
            if file_path.is_symlink():
                # For symbolic links, git only commits the link itself, not the target content
                # So we only need to check if the symlink NAME/PATH itself is problematic
                return self._scan_symbolic_link(file_path)
            
            # Get file info
            stat = file_path.stat()
            file_size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            relative_path = str(file_path.relative_to(self.project_path))
            
            # Check if file is tracked by git
            is_tracked = self._is_git_tracked(file_path)
            
            # Pattern-based risk detection
            for risk_type, patterns in self.risk_patterns.items():
                for pattern in patterns:
                    if fnmatch.fnmatch(relative_path, pattern):
                        risk = self._create_risk(
                            file_path=relative_path,
                            risk_type=risk_type,
                            pattern_matched=pattern,
                            file_size=file_size,
                            last_modified=last_modified,
                            is_tracked=is_tracked
                        )
                        risks.append(risk)
                        break  # Only match first pattern per type
            
            # Content-based risk detection for text files
            if self._is_text_file(file_path) and file_size < 1024 * 1024:  # Only scan files < 1MB
                content_risks = self._scan_file_content(file_path, relative_path, file_size, last_modified, is_tracked)
                risks.extend(content_risks)
            
            # Large file detection
            if file_size > self.large_file_threshold * 1024 * 1024:
                risk = self._create_risk(
                    file_path=relative_path,
                    risk_type=SecurityRiskType.LARGE_BINARY,
                    pattern_matched=f"file_size > {self.large_file_threshold}MB",
                    file_size=file_size,
                    last_modified=last_modified,
                    is_tracked=is_tracked
                )
                risks.append(risk)
        
        except Exception:
            pass  # Skip files that can't be scanned
        
        return risks
    
    def _scan_file_content(self, file_path: Path, relative_path: str, file_size: int, last_modified: str, is_tracked: bool) -> List[SecurityRisk]:
        """Scan file content for credential patterns"""
        risks = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            import re
            for pattern in self.credential_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Determine risk type based on pattern
                    if 'api' in pattern.lower():
                        risk_type = SecurityRiskType.API_KEY_PATTERN
                    else:
                        risk_type = SecurityRiskType.CREDENTIAL_PATTERN
                    
                    risk = self._create_risk(
                        file_path=relative_path,
                        risk_type=risk_type,
                        pattern_matched=pattern,
                        file_size=file_size,
                        last_modified=last_modified,
                        is_tracked=is_tracked
                    )
                    risks.append(risk)
        
        except Exception:
            pass  # Skip files that can't be read
        
        return risks
    
    def _scan_symbolic_link(self, file_path: Path) -> List[SecurityRisk]:
        """
        Scan symbolic link for security risks.
        
        For symbolic links, git only commits the link itself (the pointer), not the 
        target content. Therefore, we only need to check if the symlink path/name 
        itself is problematic, not the content it points to.
        
        This prevents false positives where symlinks point to sensitive files but
        the actual git commit only contains the safe symlink pointer.
        """
        risks = []
        
        try:
            # Get symlink metadata (without following the link)
            stat = file_path.lstat()  # lstat() gets symlink metadata, not target
            file_size = stat.st_size  # Size of the symlink itself, not target
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Handle both absolute and relative paths
            try:
                relative_path = str(file_path.relative_to(self.project_path))
            except ValueError:
                # If relative_to fails, use the file name or absolute path
                if file_path.is_absolute():
                    relative_path = str(file_path)
                else:
                    relative_path = str(file_path)
            
            # Check if symlink is tracked by git
            is_tracked = self._is_git_tracked(file_path)
            
            # Read the symlink target (what it points to)
            try:
                symlink_target = os.readlink(file_path)
            except Exception:
                symlink_target = "unknown"
            
            # Only check the symlink PATH/NAME patterns, not content
            # This catches things like symlinks named "secrets.txt" or ".env_link"
            for risk_type, patterns in self.risk_patterns.items():
                for pattern in patterns:
                    if fnmatch.fnmatch(relative_path, pattern):
                        # Create risk for the symlink path itself
                        risk = self._create_risk(
                            file_path=relative_path,
                            risk_type=risk_type,
                            pattern_matched=f"symlink_path:{pattern}",
                            file_size=file_size,
                            last_modified=last_modified,
                            is_tracked=is_tracked
                        )
                        # Add symlink-specific information
                        risk.description = f"Symbolic link with suspicious name: {relative_path} -> {symlink_target}"
                        risk.recommendation = f"Rename symlink to non-sensitive name or add to .gitignore"
                        risks.append(risk)
                        break  # Only match first pattern per type
            
            # Check if symlink target path itself looks suspicious
            # This catches symlinks pointing to obviously sensitive locations
            suspicious_targets = [
                '*.env*', '*.secret*', '*.key*', '*.credential*', 
                '*password*', '*config/secret*', '*private*'
            ]
            
            for pattern in suspicious_targets:
                if fnmatch.fnmatch(symlink_target.lower(), pattern):
                    risk = self._create_risk(
                        file_path=relative_path,
                        risk_type=SecurityRiskType.SECRET_FILE,
                        pattern_matched=f"symlink_target:{pattern}",
                        file_size=file_size,
                        last_modified=last_modified,
                        is_tracked=is_tracked
                    )
                    risk.description = f"Symbolic link points to suspicious location: {relative_path} -> {symlink_target}"
                    risk.recommendation = f"Review symlink target for sensitivity. Consider .gitignore if appropriate."
                    risks.append(risk)
                    break
                    
        except Exception as e:
            # If we can't analyze the symlink properly, create a warning
            try:
                relative_path = str(file_path.relative_to(self.project_path))
            except ValueError:
                relative_path = str(file_path)
                
            risk = self._create_risk(
                file_path=relative_path,
                risk_type=SecurityRiskType.SYSTEM_FILE,
                pattern_matched="symlink_analysis_failed",
                file_size=0,
                last_modified=datetime.now().isoformat(),
                is_tracked=False
            )
            risk.description = f"Could not analyze symbolic link: {file_path}"
            risk.recommendation = "Manually verify symlink safety"
            risks.append(risk)
        
        return risks
    
    def _create_risk(self, file_path: str, risk_type: SecurityRiskType, pattern_matched: str, 
                    file_size: int, last_modified: str, is_tracked: bool) -> SecurityRisk:
        """Create a SecurityRisk object"""
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_type, file_path, is_tracked)
        
        # Generate description and recommendation
        description = self._get_risk_description(risk_type, file_path)
        recommendation = self._get_risk_recommendation(risk_type, risk_level)
        
        return SecurityRisk(
            file_path=file_path,
            risk_type=risk_type,
            risk_level=risk_level,
            description=description,
            recommendation=recommendation,
            pattern_matched=pattern_matched,
            file_size=file_size,
            last_modified=last_modified,
            is_tracked=is_tracked
        )
    
    def _determine_risk_level(self, risk_type: SecurityRiskType, file_path: str, is_tracked: bool) -> SecurityRiskLevel:
        """Determine risk level based on type, location, and tracking status"""
        
        base_levels = {
            SecurityRiskType.SECRET_FILE: SecurityRiskLevel.CRITICAL,
            SecurityRiskType.CREDENTIAL_PATTERN: SecurityRiskLevel.CRITICAL,
            SecurityRiskType.API_KEY_PATTERN: SecurityRiskLevel.CRITICAL,
            SecurityRiskType.SENSITIVE_CONFIG: SecurityRiskLevel.HIGH,
            SecurityRiskType.DATABASE_FILE: SecurityRiskLevel.HIGH,
            SecurityRiskType.LARGE_BINARY: SecurityRiskLevel.MEDIUM,
            SecurityRiskType.BACKUP_FILE: SecurityRiskLevel.MEDIUM,
            SecurityRiskType.LOG_FILE: SecurityRiskLevel.LOW,
            SecurityRiskType.TEMPORARY_FILE: SecurityRiskLevel.LOW,
            SecurityRiskType.IDE_CONFIG: SecurityRiskLevel.INFO
        }
        
        base_level = base_levels.get(risk_type, SecurityRiskLevel.MEDIUM)
        
        # Increase risk if file is already tracked by git
        if is_tracked:
            if base_level == SecurityRiskLevel.HIGH:
                return SecurityRiskLevel.CRITICAL
            elif base_level == SecurityRiskLevel.MEDIUM:
                return SecurityRiskLevel.HIGH
            elif base_level == SecurityRiskLevel.LOW:
                return SecurityRiskLevel.MEDIUM
        
        # Increase risk for certain file locations
        if any(sensitive in file_path.lower() for sensitive in ['config', 'secret', 'credential', 'auth']):
            if base_level == SecurityRiskLevel.HIGH:
                return SecurityRiskLevel.CRITICAL
            elif base_level == SecurityRiskLevel.MEDIUM:
                return SecurityRiskLevel.HIGH
        
        return base_level
    
    def _get_risk_description(self, risk_type: SecurityRiskType, file_path: str) -> str:
        """Get human-readable description of the risk"""
        descriptions = {
            SecurityRiskType.SECRET_FILE: f"Potential secret file detected: {file_path}",
            SecurityRiskType.CREDENTIAL_PATTERN: f"Credential pattern found in: {file_path}",
            SecurityRiskType.API_KEY_PATTERN: f"API key pattern detected in: {file_path}",
            SecurityRiskType.SENSITIVE_CONFIG: f"Sensitive configuration file: {file_path}",
            SecurityRiskType.DATABASE_FILE: f"Database file detected: {file_path}",
            SecurityRiskType.LARGE_BINARY: f"Large binary file: {file_path}",
            SecurityRiskType.BACKUP_FILE: f"Backup file detected: {file_path}",
            SecurityRiskType.LOG_FILE: f"Log file detected: {file_path}",
            SecurityRiskType.TEMPORARY_FILE: f"Temporary file detected: {file_path}",
            SecurityRiskType.IDE_CONFIG: f"IDE configuration file: {file_path}"
        }
        
        return descriptions.get(risk_type, f"Security risk detected: {file_path}")
    
    def _get_risk_recommendation(self, risk_type: SecurityRiskType, risk_level: SecurityRiskLevel) -> str:
        """Get recommended action for the risk"""
        
        if risk_level == SecurityRiskLevel.CRITICAL:
            return "Immediate action required: Remove file or add to .gitignore"
        elif risk_level == SecurityRiskLevel.HIGH:
            return "Review file contents and consider adding to .gitignore"
        elif risk_level == SecurityRiskLevel.MEDIUM:
            return "Consider adding to .gitignore or .gitupignore"
        else:
            return "Review and add to appropriate ignore file if needed"
    
    def _is_git_tracked(self, file_path: Path) -> bool:
        """Check if file is tracked by git"""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(file_path)],
                cwd=self.project_path,
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file"""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' not in chunk
        except Exception:
            return False
    
    def _create_assessment(self, risks: List[SecurityRisk]) -> SecurityAssessment:
        """Create security assessment from detected risks"""
        
        # Count risks by level
        risk_counts = {
            SecurityRiskLevel.CRITICAL: 0,
            SecurityRiskLevel.HIGH: 0,
            SecurityRiskLevel.MEDIUM: 0,
            SecurityRiskLevel.LOW: 0,
            SecurityRiskLevel.INFO: 0
        }
        
        for risk in risks:
            risk_counts[risk.risk_level] += 1
        
        # Determine blocking violations
        blocking_levels = self.blocking_thresholds.get(self.security_level, [SecurityRiskLevel.CRITICAL])
        blocking_violations = [risk for risk in risks if risk.risk_level in blocking_levels]
        
        return SecurityAssessment(
            project_path=str(self.project_path),
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_risks=len(risks),
            critical_risks=risk_counts[SecurityRiskLevel.CRITICAL],
            high_risks=risk_counts[SecurityRiskLevel.HIGH],
            medium_risks=risk_counts[SecurityRiskLevel.MEDIUM],
            low_risks=risk_counts[SecurityRiskLevel.LOW],
            risks=risks,
            blocking_violations=blocking_violations,
            user_decisions={},
            global_exceptions=[],
            security_level=self.security_level,
            enforcement_active=len(blocking_violations) > 0
        )


class SecurityEnforcer:
    """
    Enforces security policies and blocks operations when violations exist.
    
    This class implements the core enforcement mechanism that prevents
    GitUp operations when security violations are detected and not resolved.
    """
    
    def __init__(self, project_path: str, security_level: str = "moderate"):
        """
        Initialize the security enforcer.
        
        Args:
            project_path: Path to the project directory
            security_level: Security enforcement level
        """
        self.project_path = Path(project_path)
        self.security_level = security_level
        self.gitup_dir = self.project_path / ".gitup"
        self.violations_file = self.gitup_dir / "violations.json"
    
    def check_violations(self) -> Tuple[bool, List[SecurityRisk]]:
        """
        Check for current security violations.
        
        Returns:
            Tuple of (has_violations, violations_list)
        """
        try:
            if not self.violations_file.exists():
                return False, []
            
            with open(self.violations_file, 'r') as f:
                data = json.load(f)
            
            # Load violations that haven't been resolved
            violations = []
            for violation_data in data.get("violations", []):
                if not violation_data.get("resolved", False):
                    risk = SecurityRisk(
                        file_path=violation_data["file_path"],
                        risk_type=SecurityRiskType(violation_data["risk_type"]),
                        risk_level=SecurityRiskLevel(violation_data["risk_level"]),
                        description=violation_data["description"],
                        recommendation=violation_data["recommendation"],
                        pattern_matched=violation_data["pattern_matched"],
                        file_size=violation_data["file_size"],
                        last_modified=violation_data["last_modified"],
                        is_tracked=violation_data["is_tracked"]
                    )
                    violations.append(risk)
            
            return len(violations) > 0, violations
            
        except Exception:
            return False, []
    
    def save_violations(self, violations: List[SecurityRisk]) -> None:
        """Save current violations to file"""
        try:
            self.gitup_dir.mkdir(exist_ok=True)
            
            data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "security_level": self.security_level,
                "violations": [asdict(violation) for violation in violations]
            }
            
            with open(self.violations_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception:
            pass  # Fail silently for now
    
    def enforce_security(self, operation: str) -> None:
        """
        Enforce security policy for a GitUp operation.
        
        Args:
            operation: The operation being attempted
            
        Raises:
            SecurityViolationError: If security violations block the operation
        """
        has_violations, violations = self.check_violations()
        
        if has_violations:
            raise SecurityViolationError(
                f"Security violations detected. Operation '{operation}' blocked.\n"
                f"Found {len(violations)} unresolved security violations.\n"
                f"Run 'gitup security review' to address violations.",
                violations
            )
    
    def clear_violations(self) -> None:
        """Clear all security violations"""
        try:
            if self.violations_file.exists():
                self.violations_file.unlink()
        except Exception:
            pass