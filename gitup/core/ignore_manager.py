# File: ignore_manager.py
# Path: /home/herb/Desktop/GitUp/gitup/core/ignore_manager.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:34PM
"""
GitUp ignore management system - handles .gitupignore files and user decisions.
This module provides the core functionality for analyzing existing .gitignore files,
detecting security gaps, and managing the .gitupignore system alongside metadata.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timezone
import fnmatch


class GitUpIgnoreManager:
    """
    Core manager for .gitupignore system.
    
    Handles analysis of existing .gitignore files, detection of security gaps,
    user decision management, and combined ignore logic.
    """
    
    def __init__(self, ProjectPath: str):
        """
        Initialize the GitUpIgnoreManager.
        
        Args:
            ProjectPath: Path to the project directory
        """
        self.ProjectPath = Path(ProjectPath)
        self.GitIgnorePath = self.ProjectPath / '.gitignore'
        self.GitUpIgnorePath = self.ProjectPath / '.gitupignore'
        self.MetadataPath = self.ProjectPath / '.gitupignore.meta'
        
        # Security patterns that should be ignored
        self.SecurityPatterns = {
            'secrets': [
                '*.env',
                '*.env.*',
                '.env',
                '.env.*',
                'secrets.json',
                'secrets.yaml',
                'secrets.yml',
                'config/secrets.*',
                'secrets/*',
                '*.key',
                '*.pem',
                '*.p12',
                '*.pfx',
                '*.keystore',
                'keystore.*',
                'credentials.json',
                'service-account.json',
                'auth.json'
            ],
            'databases': [
                '*.db',
                '*.sqlite',
                '*.sqlite3',
                '*.sql',
                '*.dump',
                '*.bak',
                'database.json',
                'Data/Databases/*',
                'data/*.db',
                'db/*'
            ],
            'logs': [
                '*.log',
                'logs/*',
                'log/*',
                'error.log',
                'debug.log',
                'access.log',
                'application.log'
            ],
            'backups': [
                '*.backup',
                '*.bak',
                '*.old',
                '*.orig',
                '*.tmp',
                'backup/*',
                'backups/*',
                'temp/*',
                'tmp/*'
            ],
            'ide': [
                '.vscode/settings.json',
                '.idea/*',
                '*.swp',
                '*.swo',
                '*~',
                '.DS_Store',
                'Thumbs.db',
                'desktop.ini'
            ]
        }
        
        # Load existing metadata if available
        self.UserDecisions = self._LoadMetadata()
    
    def AnalyzeExistingGitIgnore(self) -> Dict[str, List[str]]:
        """
        Analyze existing .gitignore file for security gaps.
        
        Returns:
            Dictionary with 'missing_patterns' and 'conflicts' keys
        """
        ExistingPatterns = self._ReadGitIgnorePatterns()
        MissingPatterns = []
        PotentialConflicts = []
        
        # Check for missing security patterns
        for Category, Patterns in self.SecurityPatterns.items():
            for Pattern in Patterns:
                if not self._IsPatternCovered(Pattern, ExistingPatterns):
                    MissingPatterns.append({
                        'pattern': Pattern,
                        'category': Category,
                        'risk_level': self._GetRiskLevel(Pattern, Category)
                    })
        
        # Check for potential conflicts
        for ExistingPattern in ExistingPatterns:
            if self._CouldBeSecurityIssue(ExistingPattern):
                PotentialConflicts.append({
                    'pattern': ExistingPattern,
                    'reason': self._GetConflictReason(ExistingPattern)
                })
        
        return {
            'missing_patterns': MissingPatterns,
            'conflicts': PotentialConflicts,
            'existing_patterns': ExistingPatterns
        }
    
    def CreateSuggestions(self) -> Dict[str, any]:
        """
        Generate .gitupignore suggestions based on analysis.
        
        Returns:
            Dictionary with suggestions and metadata
        """
        Analysis = self.AnalyzeExistingGitIgnore()
        
        Suggestions = {
            'security_additions': [],
            'conflict_resolutions': [],
            'metadata': {
                'created': datetime.now(timezone.utc).isoformat(),
                'project_type': self._DetectProjectType(),
                'analysis_summary': {
                    'missing_patterns': len(Analysis['missing_patterns']),
                    'conflicts': len(Analysis['conflicts'])
                }
            }
        }
        
        # Add missing security patterns
        for Missing in Analysis['missing_patterns']:
            Suggestions['security_additions'].append({
                'pattern': Missing['pattern'],
                'category': Missing['category'],
                'risk_level': Missing['risk_level'],
                'recommended_action': 'add_to_gitupignore'
            })
        
        # Add conflict resolutions
        for Conflict in Analysis['conflicts']:
            Suggestions['conflict_resolutions'].append({
                'pattern': Conflict['pattern'],
                'reason': Conflict['reason'],
                'options': self._GetResolutionOptions(Conflict['pattern'])
            })
        
        return Suggestions
    
    def ApplyUserDecisions(self, Decisions: Dict[str, Dict[str, any]]) -> None:
        """
        Apply user decisions to .gitupignore and metadata.
        
        Args:
            Decisions: Dictionary of user decisions per pattern
        """
        GitUpIgnoreContent = []
        
        # Add header
        GitUpIgnoreContent.append("# GitUp Security Ignore File")
        GitUpIgnoreContent.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        GitUpIgnoreContent.append("# This file works alongside .gitignore for security-focused patterns")
        GitUpIgnoreContent.append("")
        
        # Process decisions by category
        Categories = {}
        for Pattern, Decision in Decisions.items():
            Category = Decision.get('category', 'other')
            if Category not in Categories:
                Categories[Category] = []
            Categories[Category].append((Pattern, Decision))
        
        # Write patterns by category
        for Category, Patterns in Categories.items():
            if Patterns:
                GitUpIgnoreContent.append(f"# {Category.title()} Security Patterns")
                for Pattern, Decision in Patterns:
                    if Decision['action'] == 'add_to_gitupignore':
                        GitUpIgnoreContent.append(Pattern)
                        if Decision.get('comment'):
                            GitUpIgnoreContent.append(f"# {Decision['comment']}")
                GitUpIgnoreContent.append("")
        
        # Write .gitupignore file
        with open(self.GitUpIgnorePath, 'w') as f:
            f.write('\n'.join(GitUpIgnoreContent))
        
        # Update metadata
        self.UserDecisions.update(Decisions)
        self._SaveMetadata()
    
    def ShouldIgnoreFile(self, FilePath: str) -> Tuple[bool, str]:
        """
        Check if file should be ignored (combined .gitignore + .gitupignore logic).
        
        Args:
            FilePath: Path to check
            
        Returns:
            Tuple of (should_ignore, reason)
        """
        RelativePath = self._GetRelativePath(FilePath)
        
        # Check .gitignore first
        if self._IsGitIgnored(RelativePath):
            return True, "matched .gitignore"
        
        # Check .gitupignore
        if self._IsGitUpIgnored(RelativePath):
            return True, "matched .gitupignore"
        
        # Check user decisions
        if self._IsUserApproved(RelativePath):
            return True, "user approved"
        
        return False, "not ignored"
    
    def IsUserApproved(self, FilePath: str) -> bool:
        """
        Check if user has explicitly approved this file.
        
        Args:
            FilePath: Path to check
            
        Returns:
            True if user approved
        """
        RelativePath = self._GetRelativePath(FilePath)
        
        for Pattern, Decision in self.UserDecisions.items():
            if fnmatch.fnmatch(RelativePath, Pattern):
                return Decision.get('decision') == 'safe'
        
        return False
    
    def GetIgnoreStatus(self) -> Dict[str, any]:
        """
        Get current ignore status and statistics.
        
        Returns:
            Dictionary with status information
        """
        return {
            'gitignore_exists': self.GitIgnorePath.exists(),
            'gitupignore_exists': self.GitUpIgnorePath.exists(),
            'metadata_exists': self.MetadataPath.exists(),
            'user_decisions': len(self.UserDecisions),
            'last_updated': self._GetLastUpdated(),
            'project_type': self._DetectProjectType()
        }
    
    # Private helper methods
    
    def _ReadGitIgnorePatterns(self) -> List[str]:
        """Read and parse .gitignore file patterns."""
        if not self.GitIgnorePath.exists():
            return []
        
        Patterns = []
        try:
            with open(self.GitIgnorePath, 'r') as f:
                for Line in f:
                    Line = Line.strip()
                    if Line and not Line.startswith('#'):
                        Patterns.append(Line)
        except Exception:
            return []
        
        return Patterns
    
    def _IsPatternCovered(self, Pattern: str, ExistingPatterns: List[str]) -> bool:
        """Check if a security pattern is covered by existing patterns."""
        for ExistingPattern in ExistingPatterns:
            if fnmatch.fnmatch(Pattern, ExistingPattern):
                return True
            if Pattern == ExistingPattern:
                return True
        return False
    
    def _GetRiskLevel(self, Pattern: str, Category: str) -> str:
        """Determine risk level for a pattern."""
        HighRisk = ['secrets', 'databases']
        MediumRisk = ['logs', 'backups']
        
        if Category in HighRisk:
            return 'high'
        elif Category in MediumRisk:
            return 'medium'
        else:
            return 'low'
    
    def _CouldBeSecurityIssue(self, Pattern: str) -> bool:
        """Check if an existing pattern could be a security issue."""
        SecurityKeywords = ['config', 'secret', 'key', 'password', 'token', 'credential']
        
        for Keyword in SecurityKeywords:
            if Keyword in Pattern.lower():
                return True
        
        return False
    
    def _GetConflictReason(self, Pattern: str) -> str:
        """Get reason why a pattern might be a conflict."""
        if 'config' in Pattern.lower():
            return "Configuration files may contain sensitive data"
        elif 'key' in Pattern.lower():
            return "Key files typically contain sensitive credentials"
        elif 'secret' in Pattern.lower():
            return "Files with 'secret' in name may contain sensitive data"
        else:
            return "Pattern may conflict with security requirements"
    
    def _DetectProjectType(self) -> str:
        """Detect project type based on files present."""
        if (self.ProjectPath / 'package.json').exists():
            return 'node'
        elif (self.ProjectPath / 'requirements.txt').exists():
            return 'python'
        elif (self.ProjectPath / 'Cargo.toml').exists():
            return 'rust'
        elif (self.ProjectPath / 'go.mod').exists():
            return 'go'
        else:
            return 'unknown'
    
    def _GetResolutionOptions(self, Pattern: str) -> List[str]:
        """Get resolution options for a conflict pattern."""
        return [
            'keep_in_gitignore',
            'move_to_gitupignore',
            'add_to_both',
            'remove_entirely'
        ]
    
    def _GetRelativePath(self, FilePath: str) -> str:
        """Get relative path from project root."""
        try:
            return str(Path(FilePath).relative_to(self.ProjectPath))
        except ValueError:
            return str(Path(FilePath))
    
    def _IsGitIgnored(self, FilePath: str) -> bool:
        """Check if file is ignored by .gitignore."""
        # This is a simplified implementation
        # In production, would use gitpython or similar
        GitIgnorePatterns = self._ReadGitIgnorePatterns()
        
        for Pattern in GitIgnorePatterns:
            if fnmatch.fnmatch(FilePath, Pattern):
                return True
        
        return False
    
    def _IsGitUpIgnored(self, FilePath: str) -> bool:
        """Check if file is ignored by .gitupignore."""
        if not self.GitUpIgnorePath.exists():
            return False
        
        try:
            with open(self.GitUpIgnorePath, 'r') as f:
                for Line in f:
                    Line = Line.strip()
                    if Line and not Line.startswith('#'):
                        if fnmatch.fnmatch(FilePath, Line):
                            return True
        except Exception:
            return False
        
        return False
    
    def _IsUserApproved(self, FilePath: str) -> bool:
        """Check if user has approved this file."""
        return self.IsUserApproved(FilePath)
    
    def _LoadMetadata(self) -> Dict[str, any]:
        """Load metadata from .gitupignore.meta file."""
        if not self.MetadataPath.exists():
            return {}
        
        try:
            with open(self.MetadataPath, 'r') as f:
                Data = json.load(f)
                return Data.get('user_decisions', {})
        except Exception:
            return {}
    
    def _SaveMetadata(self) -> None:
        """Save metadata to .gitupignore.meta file."""
        Metadata = {
            'version': '1.0.0',
            'created': datetime.now(timezone.utc).isoformat(),
            'project_type': self._DetectProjectType(),
            'user_decisions': self.UserDecisions,
            'audit_trail': self._GetAuditTrail(),
            'last_updated': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            with open(self.MetadataPath, 'w') as f:
                json.dump(Metadata, f, indent=2)
        except Exception:
            pass  # Fail silently for now
    
    def _GetAuditTrail(self) -> List[Dict[str, any]]:
        """Get audit trail for metadata."""
        return [
            {
                'action': 'metadata_updated',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'user': os.getenv('USER', 'unknown'),
                'gitup_version': '0.2.0'
            }
        ]
    
    def _GetLastUpdated(self) -> Optional[str]:
        """Get last updated timestamp."""
        if self.MetadataPath.exists():
            try:
                with open(self.MetadataPath, 'r') as f:
                    Data = json.load(f)
                    return Data.get('last_updated')
            except Exception:
                pass
        return None