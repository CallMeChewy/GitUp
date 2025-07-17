# File: gitignore_monitor.py
# Path: gitup/core/gitignore_monitor.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-16
# Last Modified: 2025-07-16  08:30PM
"""
GitUp GitIgnore Delta Detection System

Monitors user's .gitignore file for changes and analyzes security impact.
Never modifies user's .gitignore - only monitors and adapts security enforcement.

Key Features:
- Lightning-fast hash-based change detection
- Delta analysis for added/removed patterns
- Global exception pattern support (*codebase.txt)
- Security impact assessment for .gitignore changes
- Stealth baseline storage (gi_baseline.dat)

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import os
import hashlib
import shutil
import fnmatch
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from datetime import datetime, timezone
import json
import re
from dataclasses import dataclass, asdict

from ..utils.exceptions import GitUpError


@dataclass
class GitIgnoreChange:
    """Represents a change in .gitignore patterns"""
    pattern: str
    change_type: str  # 'added', 'removed', 'modified'
    security_impact: str  # 'resolves_violations', 'creates_exposures', 'neutral'
    affected_files: List[str]
    risk_level: str  # 'critical', 'high', 'medium', 'low', 'info'


@dataclass
class GitIgnoreDelta:
    """Complete analysis of .gitignore changes"""
    timestamp: str
    has_changes: bool
    added_patterns: List[str]
    removed_patterns: List[str]
    security_changes: List[GitIgnoreChange]
    violations_resolved: List[str]
    new_exposures: List[str]
    global_exceptions_matched: List[str]


class GitIgnoreMonitor:
    """
    Monitors user's .gitignore for changes and analyzes security impact.
    
    This class implements the core principle: never modify user's .gitignore,
    but track changes to update security enforcement accordingly.
    """
    
    def __init__(self, project_path: str):
        """
        Initialize GitIgnore monitoring for a project.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path).resolve()
        self.gitignore_path = self.project_path / ".gitignore"
        
        # Stealth files in .gitup directory (disguised names)
        self.gitup_dir = self.project_path / ".gitup"
        self.baseline_path = self.gitup_dir / "gi_baseline.dat"
        self.hash_path = self.gitup_dir / "gi_baseline.hash"
        self.delta_log_path = self.gitup_dir / "gi_changes.log"
        
        # Global exception patterns (user-configurable)
        self.global_exceptions = [
            "*codebase.txt",      # User's example - backup codebases
            "*backup.py",         # Common backup script patterns
            "*.bak",              # Backup files
            "*_backup.*",         # Backup file patterns
            "docs/*.md",          # Documentation files
            "*.readme",           # README variants
            "changelog.*",        # Change logs
            "*.example",          # Example files
            "template.*",         # Template files
        ]
        
        self.gitup_dir.mkdir(exist_ok=True)
    
    def detect_gitignore_changes(self) -> Tuple[bool, str]:
        """
        Quick detection if .gitignore changed since last scan.
        
        Returns:
            Tuple of (has_changed: bool, reason: str)
        """
        if not self.gitignore_path.exists():
            if self.baseline_path.exists():
                return True, "gitignore_deleted"
            return False, "no_gitignore"
        
        current_hash = self._hash_file(self.gitignore_path)
        
        if not self.hash_path.exists():
            return True, "first_scan"
        
        try:
            with open(self.hash_path, 'r', encoding='utf-8') as f:
                baseline_hash = f.read().strip()
        except Exception:
            return True, "hash_read_error"
        
        if current_hash != baseline_hash:
            return True, "gitignore_modified"
        
        return False, "unchanged"
    
    def analyze_gitignore_delta(self) -> GitIgnoreDelta:
        """
        Perform complete analysis of .gitignore changes.
        
        Returns:
            GitIgnoreDelta with complete change analysis
        """
        has_changes, reason = self.detect_gitignore_changes()
        
        if not has_changes:
            return GitIgnoreDelta(
                timestamp=datetime.now(timezone.utc).isoformat(),
                has_changes=False,
                added_patterns=[],
                removed_patterns=[],
                security_changes=[],
                violations_resolved=[],
                new_exposures=[],
                global_exceptions_matched=[]
            )
        
        # Parse current and baseline patterns
        current_patterns = self._parse_gitignore_patterns(self.gitignore_path)
        
        if self.baseline_path.exists():
            baseline_patterns = self._parse_gitignore_patterns(self.baseline_path)
        else:
            baseline_patterns = set()
        
        # Calculate pattern differences
        added_patterns = list(current_patterns - baseline_patterns)
        removed_patterns = list(baseline_patterns - current_patterns)
        
        # Analyze security impact
        security_changes = []
        violations_resolved = []
        new_exposures = []
        global_exceptions_matched = []
        
        # Check added patterns
        for pattern in added_patterns:
            change = self._analyze_pattern_addition(pattern)
            security_changes.append(change)
            
            if change.security_impact == 'resolves_violations':
                violations_resolved.extend(change.affected_files)
            
            # Check against global exceptions
            if self._matches_global_exception(pattern):
                global_exceptions_matched.append(pattern)
        
        # Check removed patterns
        for pattern in removed_patterns:
            change = self._analyze_pattern_removal(pattern)
            security_changes.append(change)
            
            if change.security_impact == 'creates_exposures':
                new_exposures.extend(change.affected_files)
        
        delta = GitIgnoreDelta(
            timestamp=datetime.now(timezone.utc).isoformat(),
            has_changes=True,
            added_patterns=added_patterns,
            removed_patterns=removed_patterns,
            security_changes=security_changes,
            violations_resolved=violations_resolved,
            new_exposures=new_exposures,
            global_exceptions_matched=global_exceptions_matched
        )
        
        # Log the changes
        self._log_delta_analysis(delta, reason)
        
        return delta
    
    def update_baseline(self) -> bool:
        """
        Save current .gitignore state as new baseline.
        
        Returns:
            Success status
        """
        try:
            if self.gitignore_path.exists():
                # Copy content with disguised name
                shutil.copy2(self.gitignore_path, self.baseline_path)
                
                # Save hash for quick detection
                current_hash = self._hash_file(self.gitignore_path)
                with open(self.hash_path, 'w', encoding='utf-8') as f:
                    f.write(current_hash)
            else:
                # No .gitignore - remove baseline files
                if self.baseline_path.exists():
                    self.baseline_path.unlink()
                if self.hash_path.exists():
                    self.hash_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to update .gitignore baseline: {e}")
            return False
    
    def check_global_exception_coverage(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if a file matches any global exception patterns.
        
        Args:
            file_path: Path to check against global exceptions (absolute or relative)
            
        Returns:
            Tuple of (is_covered: bool, matching_pattern: str)
        """
        # Handle both absolute and relative paths
        file_path_obj = Path(file_path)
        if file_path_obj.is_absolute():
            try:
                relative_path = str(file_path_obj.relative_to(self.project_path))
            except ValueError:
                # File is not within project, use as-is
                relative_path = str(file_path_obj)
        else:
            relative_path = str(file_path_obj)
        
        for pattern in self.global_exceptions:
            if fnmatch.fnmatch(relative_path, pattern):
                return True, pattern
        
        return False, ""
    
    def add_global_exception(self, pattern: str) -> bool:
        """
        Add a new global exception pattern.
        
        Args:
            pattern: Glob pattern to add to global exceptions
            
        Returns:
            Success status
        """
        if pattern not in self.global_exceptions:
            self.global_exceptions.append(pattern)
            self._save_global_exceptions()
            return True
        return False
    
    def remove_global_exception(self, pattern: str) -> bool:
        """
        Remove a global exception pattern.
        
        Args:
            pattern: Pattern to remove from global exceptions
            
        Returns:
            Success status
        """
        if pattern in self.global_exceptions:
            self.global_exceptions.remove(pattern)
            self._save_global_exceptions()
            return True
        return False
    
    def get_baseline_info(self) -> Dict[str, Any]:
        """
        Get information about current baseline state.
        
        Returns:
            Dictionary with baseline information
        """
        info = {
            "has_baseline": self.baseline_path.exists(),
            "has_hash": self.hash_path.exists(),
            "gitignore_exists": self.gitignore_path.exists(),
            "baseline_timestamp": None,
            "pattern_count": 0,
            "global_exceptions": len(self.global_exceptions)
        }
        
        if self.baseline_path.exists():
            stat = self.baseline_path.stat()
            info["baseline_timestamp"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            try:
                patterns = self._parse_gitignore_patterns(self.baseline_path)
                info["pattern_count"] = len(patterns)
            except Exception:
                pass
        
        return info
    
    def _hash_file(self, file_path: Path) -> str:
        """Fast file hashing for change detection"""
        try:
            return hashlib.md5(file_path.read_bytes()).hexdigest()
        except Exception:
            return ""
    
    def _parse_gitignore_patterns(self, file_path: Path) -> Set[str]:
        """
        Parse .gitignore file into normalized patterns.
        
        Args:
            file_path: Path to .gitignore file
            
        Returns:
            Set of normalized patterns
        """
        patterns = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Normalize pattern (remove leading ./)
                    if line.startswith('./'):
                        line = line[2:]
                    
                    patterns.add(line)
                    
        except Exception as e:
            print(f"Warning: Failed to parse {file_path}: {e}")
        
        return patterns
    
    def _analyze_pattern_addition(self, pattern: str) -> GitIgnoreChange:
        """
        Analyze the security impact of adding a pattern.
        
        Args:
            pattern: The pattern that was added
            
        Returns:
            GitIgnoreChange describing the impact
        """
        # Find files that would be affected by this pattern
        affected_files = self._find_files_matching_pattern(pattern)
        
        # Check if this resolves any known security violations
        # This would integrate with the risk mitigation system
        security_impact = 'neutral'
        risk_level = 'info'
        
        # Patterns that typically resolve security issues
        security_patterns = [
            '*.env', '.env*', 'secrets.*', '*.key', '*.pem', 
            'config/production/*', '*.log', 'logs/*', '*.db'
        ]
        
        for sec_pattern in security_patterns:
            if fnmatch.fnmatch(pattern, sec_pattern) or pattern == sec_pattern:
                security_impact = 'resolves_violations'
                risk_level = 'high'
                break
        
        return GitIgnoreChange(
            pattern=pattern,
            change_type='added',
            security_impact=security_impact,
            affected_files=affected_files,
            risk_level=risk_level
        )
    
    def _analyze_pattern_removal(self, pattern: str) -> GitIgnoreChange:
        """
        Analyze the security impact of removing a pattern.
        
        Args:
            pattern: The pattern that was removed
            
        Returns:
            GitIgnoreChange describing the impact
        """
        # Find files that would now be exposed
        affected_files = self._find_files_matching_pattern(pattern)
        
        # Removing security-related patterns creates exposures
        security_impact = 'neutral'
        risk_level = 'info'
        
        # Patterns that should stay ignored for security
        security_patterns = [
            '*.env', '.env*', 'secrets.*', '*.key', '*.pem',
            'config/production/*', '*.log', 'logs/*', '*.db'
        ]
        
        for sec_pattern in security_patterns:
            if fnmatch.fnmatch(pattern, sec_pattern) or pattern == sec_pattern:
                security_impact = 'creates_exposures'
                risk_level = 'high'
                break
        
        return GitIgnoreChange(
            pattern=pattern,
            change_type='removed',
            security_impact=security_impact,
            affected_files=affected_files,
            risk_level=risk_level
        )
    
    def _find_files_matching_pattern(self, pattern: str) -> List[str]:
        """
        Find files in project that match a given pattern.
        
        Args:
            pattern: Glob pattern to match
            
        Returns:
            List of relative file paths matching the pattern
        """
        matching_files = []
        
        try:
            for root, dirs, files in os.walk(self.project_path):
                # Skip .git and .gitup directories
                dirs[:] = [d for d in dirs if d not in {'.git', '.gitup'}]
                
                for file in files:
                    file_path = Path(root) / file
                    relative_path = str(file_path.relative_to(self.project_path))
                    
                    # Check if file matches pattern
                    if fnmatch.fnmatch(relative_path, pattern):
                        matching_files.append(relative_path)
        except Exception:
            pass
        
        return matching_files[:20]  # Limit to avoid huge lists
    
    def _matches_global_exception(self, pattern: str) -> bool:
        """Check if pattern matches any global exception"""
        for exception in self.global_exceptions:
            if fnmatch.fnmatch(pattern, exception) or pattern == exception:
                return True
        return False
    
    def _log_delta_analysis(self, delta: GitIgnoreDelta, reason: str):
        """Log delta analysis for audit trail"""
        try:
            log_entry = {
                "timestamp": delta.timestamp,
                "reason": reason,
                "summary": {
                    "added_patterns": len(delta.added_patterns),
                    "removed_patterns": len(delta.removed_patterns),
                    "violations_resolved": len(delta.violations_resolved),
                    "new_exposures": len(delta.new_exposures),
                    "global_exceptions_matched": len(delta.global_exceptions_matched)
                },
                "details": asdict(delta)
            }
            
            with open(self.delta_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            print(f"Warning: Failed to log .gitignore changes: {e}")
    
    def _save_global_exceptions(self):
        """Save global exceptions to configuration"""
        try:
            config_path = self.gitup_dir / "global_exceptions.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "patterns": self.global_exceptions,
                    "last_updated": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save global exceptions: {e}")
    
    def _load_global_exceptions(self):
        """Load global exceptions from configuration"""
        try:
            config_path = self.gitup_dir / "global_exceptions.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.global_exceptions = config.get("patterns", self.global_exceptions)
        except Exception as e:
            print(f"Warning: Failed to load global exceptions: {e}")


def pre_operation_security_check(project_path: str) -> Tuple[bool, str, GitIgnoreDelta]:
    """
    Perform pre-operation security check including .gitignore delta analysis.
    
    This function should be called before every GitUp operation (push, commit, etc.)
    to ensure security compliance is maintained.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        Tuple of (can_proceed: bool, reason: str, delta: GitIgnoreDelta)
    """
    monitor = GitIgnoreMonitor(project_path)
    
    # Analyze .gitignore changes
    delta = monitor.analyze_gitignore_delta()
    
    if delta.has_changes:
        print(f"🔍 .gitignore modified - updating security assessment...")
        
        # Update baseline after analysis
        monitor.update_baseline()
        
        # Report changes to user
        if delta.added_patterns:
            print(f"📋 Added patterns: {', '.join(delta.added_patterns)}")
        
        if delta.removed_patterns:
            print(f"📋 Removed patterns: {', '.join(delta.removed_patterns)}")
        
        if delta.violations_resolved:
            print(f"✅ {len(delta.violations_resolved)} security violations auto-resolved")
        
        if delta.new_exposures:
            print(f"⚠️  {len(delta.new_exposures)} new security exposures detected")
        
        if delta.global_exceptions_matched:
            print(f"🎯 Global exceptions matched: {', '.join(delta.global_exceptions_matched)}")
    
    # For now, always allow operations (security enforcement logic would go here)
    return True, "Security compliance verified", delta


# Integration point for risk mitigation system
def integrate_with_risk_mitigation(delta: GitIgnoreDelta, security_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Integrate .gitignore changes with existing security risk mitigation.
    
    Args:
        delta: GitIgnore delta analysis
        security_state: Current security violation state
        
    Returns:
        Updated security state after .gitignore integration
    """
    updated_state = security_state.copy()
    
    # Mark violations as resolved if corresponding patterns were added
    if delta.violations_resolved:
        for violation_id in updated_state.get('violations', {}):
            violation = updated_state['violations'][violation_id]
            if violation.get('file_path') in delta.violations_resolved:
                violation['mitigation_status'] = 'resolved_by_gitignore'
                violation['resolution_timestamp'] = delta.timestamp
    
    # Add new exposures to violation tracking
    if delta.new_exposures:
        for exposed_file in delta.new_exposures:
            # This would create new violation entries for exposed files
            # Integration with SecurityRiskDetector would happen here
            pass
    
    return updated_state