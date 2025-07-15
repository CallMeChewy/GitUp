# File: metadata_manager.py
# Path: /home/herb/Desktop/GitUp/gitup/core/metadata_manager.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:36PM
"""
Metadata management system for GitUp .gitupignore files.
Handles audit trails, user decisions, expiration tracking, and security metadata
for the .gitupignore system.
"""

import json
import os
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid


class DecisionType(Enum):
    """Types of user decisions."""
    SAFE = "safe"
    IGNORE = "ignore"
    RENAME = "rename"
    EDIT = "edit"
    REVIEW = "review"


class ActionType(Enum):
    """Types of actions in audit trail."""
    CREATED = "created"
    UPDATED = "updated"
    DECISION = "decision"
    REVIEWED = "reviewed"
    EXPIRED = "expired"
    IMPORTED = "imported"
    EXPORTED = "exported"


@dataclass
class UserDecision:
    """User decision record."""
    Pattern: str
    Decision: DecisionType
    Reason: str
    Timestamp: str
    UserId: str
    Confidence: float
    AutoReview: Optional[str] = None
    ExpiresAt: Optional[str] = None
    Tags: List[str] = None
    
    def __post_init__(self):
        if self.Tags is None:
            self.Tags = []


@dataclass
class AuditEntry:
    """Audit trail entry."""
    Id: str
    Action: ActionType
    Timestamp: str
    UserId: str
    Details: Dict[str, Any]
    GitUpVersion: str
    ProjectHash: str


@dataclass
class SecurityMetadata:
    """Security-related metadata."""
    SecurityLevel: str
    LastSecurityCheck: str
    NextSecurityCheck: str
    SecurityScore: float
    RiskLevel: str
    CriticalGaps: int
    HighGaps: int
    TotalGaps: int


@dataclass
class ProjectMetadata:
    """Project-specific metadata."""
    ProjectType: str
    ProjectName: str
    ProjectPath: str
    ProjectHash: str
    GitRemoteUrl: Optional[str] = None
    LastModified: Optional[str] = None
    FileCount: int = 0
    DirectoryCount: int = 0


class GitUpMetadataManager:
    """
    Comprehensive metadata management for .gitupignore system.
    
    Handles user decisions, audit trails, security metadata, and project information
    with support for expiration, reviews, and data integrity.
    """
    
    def __init__(self, ProjectPath: str):
        """
        Initialize the metadata manager.
        
        Args:
            ProjectPath: Path to the project directory
        """
        self.ProjectPath = Path(ProjectPath)
        self.MetadataPath = self.ProjectPath / '.gitupignore.meta'
        self.BackupPath = self.ProjectPath / '.gitupignore.meta.backup'
        
        # Load existing metadata or initialize
        self.Metadata = self._LoadMetadata()
        
        # Initialize components if not present
        self._InitializeMetadata()
    
    def AddUserDecision(self, Pattern: str, Decision: DecisionType, Reason: str, 
                       Confidence: float = 1.0, AutoReview: Optional[str] = None,
                       ExpiresAt: Optional[str] = None, Tags: List[str] = None) -> str:
        """
        Add a user decision to the metadata.
        
        Args:
            Pattern: File pattern the decision applies to
            Decision: Type of decision made
            Reason: Reason for the decision
            Confidence: Confidence level (0.0 to 1.0)
            AutoReview: Optional auto-review date
            ExpiresAt: Optional expiration date
            Tags: Optional tags for categorization
            
        Returns:
            Decision ID
        """
        DecisionId = str(uuid.uuid4())
        Timestamp = datetime.now(timezone.utc).isoformat()
        UserId = self._GetCurrentUser()
        
        UserDecisionObj = UserDecision(
            Pattern=Pattern,
            Decision=Decision,
            Reason=Reason,
            Timestamp=Timestamp,
            UserId=UserId,
            Confidence=Confidence,
            AutoReview=AutoReview,
            ExpiresAt=ExpiresAt,
            Tags=Tags or []
        )
        
        self.Metadata['user_decisions'][DecisionId] = asdict(UserDecisionObj)
        
        # Add audit entry
        self._AddAuditEntry(ActionType.DECISION, {
            'decision_id': DecisionId,
            'pattern': Pattern,
            'decision': Decision.value,
            'reason': Reason,
            'confidence': Confidence
        })
        
        self._SaveMetadata()
        return DecisionId
    
    def GetUserDecision(self, Pattern: str) -> Optional[UserDecision]:
        """
        Get user decision for a specific pattern.
        
        Args:
            Pattern: File pattern to check
            
        Returns:
            UserDecision object if found, None otherwise
        """
        for DecisionId, DecisionData in self.Metadata['user_decisions'].items():
            if DecisionData['Pattern'] == Pattern:
                # Check if decision has expired
                if self._IsDecisionExpired(DecisionData):
                    self._ExpireDecision(DecisionId)
                    return None
                
                return UserDecision(**DecisionData)
        
        return None
    
    def GetAllUserDecisions(self) -> Dict[str, UserDecision]:
        """
        Get all user decisions.
        
        Returns:
            Dictionary of decision IDs to UserDecision objects
        """
        Decisions = {}
        ExpiredDecisions = []
        
        for DecisionId, DecisionData in self.Metadata['user_decisions'].items():
            if self._IsDecisionExpired(DecisionData):
                ExpiredDecisions.append(DecisionId)
            else:
                Decisions[DecisionId] = UserDecision(**DecisionData)
        
        # Clean up expired decisions
        for DecisionId in ExpiredDecisions:
            self._ExpireDecision(DecisionId)
        
        return Decisions
    
    def UpdateUserDecision(self, DecisionId: str, **Updates) -> bool:
        """
        Update an existing user decision.
        
        Args:
            DecisionId: ID of decision to update
            **Updates: Fields to update
            
        Returns:
            True if updated successfully
        """
        if DecisionId not in self.Metadata['user_decisions']:
            return False
        
        DecisionData = self.Metadata['user_decisions'][DecisionId]
        
        # Update fields
        for Field, Value in Updates.items():
            if Field in DecisionData:
                DecisionData[Field] = Value
        
        # Update timestamp
        DecisionData['Timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # Add audit entry
        self._AddAuditEntry(ActionType.UPDATED, {
            'decision_id': DecisionId,
            'updated_fields': list(Updates.keys()),
            'updates': Updates
        })
        
        self._SaveMetadata()
        return True
    
    def DeleteUserDecision(self, DecisionId: str) -> bool:
        """
        Delete a user decision.
        
        Args:
            DecisionId: ID of decision to delete
            
        Returns:
            True if deleted successfully
        """
        if DecisionId not in self.Metadata['user_decisions']:
            return False
        
        DecisionData = self.Metadata['user_decisions'][DecisionId]
        
        # Add audit entry before deletion
        self._AddAuditEntry(ActionType.UPDATED, {
            'decision_id': DecisionId,
            'action': 'deleted',
            'pattern': DecisionData['Pattern']
        })
        
        del self.Metadata['user_decisions'][DecisionId]
        self._SaveMetadata()
        return True
    
    def GetAuditTrail(self, Limit: Optional[int] = None) -> List[AuditEntry]:
        """
        Get audit trail entries.
        
        Args:
            Limit: Optional limit on number of entries
            
        Returns:
            List of AuditEntry objects
        """
        Entries = []
        AuditData = self.Metadata.get('audit_trail', [])
        
        # Sort by timestamp (newest first)
        SortedEntries = sorted(AuditData, key=lambda x: x['Timestamp'], reverse=True)
        
        if Limit:
            SortedEntries = SortedEntries[:Limit]
        
        for EntryData in SortedEntries:
            Entries.append(AuditEntry(**EntryData))
        
        return Entries
    
    def GetSecurityMetadata(self) -> SecurityMetadata:
        """
        Get security metadata.
        
        Returns:
            SecurityMetadata object
        """
        SecurityData = self.Metadata.get('security_metadata', {})
        return SecurityMetadata(**SecurityData)
    
    def UpdateSecurityMetadata(self, **Updates) -> None:
        """
        Update security metadata.
        
        Args:
            **Updates: Fields to update
        """
        SecurityData = self.Metadata.get('security_metadata', {})
        SecurityData.update(Updates)
        SecurityData['LastSecurityCheck'] = datetime.now(timezone.utc).isoformat()
        
        self.Metadata['security_metadata'] = SecurityData
        
        self._AddAuditEntry(ActionType.UPDATED, {
            'component': 'security_metadata',
            'updated_fields': list(Updates.keys())
        })
        
        self._SaveMetadata()
    
    def GetProjectMetadata(self) -> ProjectMetadata:
        """
        Get project metadata.
        
        Returns:
            ProjectMetadata object
        """
        ProjectData = self.Metadata.get('project_metadata', {})
        return ProjectMetadata(**ProjectData)
    
    def UpdateProjectMetadata(self, **Updates) -> None:
        """
        Update project metadata.
        
        Args:
            **Updates: Fields to update
        """
        ProjectData = self.Metadata.get('project_metadata', {})
        ProjectData.update(Updates)
        
        self.Metadata['project_metadata'] = ProjectData
        
        self._AddAuditEntry(ActionType.UPDATED, {
            'component': 'project_metadata',
            'updated_fields': list(Updates.keys())
        })
        
        self._SaveMetadata()
    
    def GetExpiredDecisions(self) -> List[UserDecision]:
        """
        Get decisions that have expired.
        
        Returns:
            List of expired UserDecision objects
        """
        ExpiredDecisions = []
        
        for DecisionId, DecisionData in self.Metadata['user_decisions'].items():
            if self._IsDecisionExpired(DecisionData):
                ExpiredDecisions.append(UserDecision(**DecisionData))
        
        return ExpiredDecisions
    
    def GetDecisionsDueForReview(self) -> List[UserDecision]:
        """
        Get decisions that are due for review.
        
        Returns:
            List of UserDecision objects due for review
        """
        DueForReview = []
        CurrentTime = datetime.now(timezone.utc)
        
        for DecisionId, DecisionData in self.Metadata['user_decisions'].items():
            if DecisionData.get('AutoReview'):
                ReviewTime = datetime.fromisoformat(DecisionData['AutoReview'].replace('Z', '+00:00'))
                if CurrentTime >= ReviewTime:
                    DueForReview.append(UserDecision(**DecisionData))
        
        return DueForReview
    
    def ExportMetadata(self, OutputPath: str) -> bool:
        """
        Export metadata to file.
        
        Args:
            OutputPath: Path to export file
            
        Returns:
            True if exported successfully
        """
        try:
            with open(OutputPath, 'w') as f:
                json.dump(self.Metadata, f, indent=2)
            
            self._AddAuditEntry(ActionType.EXPORTED, {
                'export_path': OutputPath,
                'export_size': os.path.getsize(OutputPath)
            })
            
            return True
        except Exception:
            return False
    
    def ImportMetadata(self, ImportPath: str, MergeStrategy: str = 'overwrite') -> bool:
        """
        Import metadata from file.
        
        Args:
            ImportPath: Path to import file
            MergeStrategy: Strategy for merging ('overwrite', 'merge', 'append')
            
        Returns:
            True if imported successfully
        """
        try:
            with open(ImportPath, 'r') as f:
                ImportedData = json.load(f)
            
            if MergeStrategy == 'overwrite':
                self.Metadata = ImportedData
            elif MergeStrategy == 'merge':
                self._MergeMetadata(ImportedData)
            elif MergeStrategy == 'append':
                self._AppendMetadata(ImportedData)
            
            self._AddAuditEntry(ActionType.IMPORTED, {
                'import_path': ImportPath,
                'merge_strategy': MergeStrategy,
                'import_size': os.path.getsize(ImportPath)
            })
            
            self._SaveMetadata()
            return True
        except Exception:
            return False
    
    def GetStatistics(self) -> Dict[str, Any]:
        """
        Get metadata statistics.
        
        Returns:
            Dictionary with statistics
        """
        UserDecisions = self.Metadata.get('user_decisions', {})
        AuditTrail = self.Metadata.get('audit_trail', [])
        SecurityData = self.Metadata.get('security_metadata', {})
        
        # Decision statistics
        DecisionTypes = {}
        for DecisionData in UserDecisions.values():
            DecisionType = DecisionData.get('Decision', 'unknown')
            DecisionTypes[DecisionType] = DecisionTypes.get(DecisionType, 0) + 1
        
        # Audit statistics
        ActionTypes = {}
        for EntryData in AuditTrail:
            ActionType = EntryData.get('Action', 'unknown')
            ActionTypes[ActionType] = ActionTypes.get(ActionType, 0) + 1
        
        return {
            'total_decisions': len(UserDecisions),
            'decision_types': DecisionTypes,
            'total_audit_entries': len(AuditTrail),
            'action_types': ActionTypes,
            'expired_decisions': len(self.GetExpiredDecisions()),
            'due_for_review': len(self.GetDecisionsDueForReview()),
            'security_score': SecurityData.get('SecurityScore', 0.0),
            'risk_level': SecurityData.get('RiskLevel', 'unknown'),
            'last_updated': self.Metadata.get('last_updated'),
            'metadata_size': self._GetMetadataSize()
        }
    
    def CleanupExpiredDecisions(self) -> int:
        """
        Clean up expired decisions.
        
        Returns:
            Number of decisions cleaned up
        """
        ExpiredDecisions = []
        
        for DecisionId, DecisionData in self.Metadata['user_decisions'].items():
            if self._IsDecisionExpired(DecisionData):
                ExpiredDecisions.append(DecisionId)
        
        for DecisionId in ExpiredDecisions:
            self._ExpireDecision(DecisionId)
        
        return len(ExpiredDecisions)
    
    def ValidateIntegrity(self) -> Dict[str, Any]:
        """
        Validate metadata integrity.
        
        Returns:
            Dictionary with validation results
        """
        Issues = []
        
        # Check required fields
        RequiredFields = ['version', 'created', 'user_decisions', 'audit_trail']
        for Field in RequiredFields:
            if Field not in self.Metadata:
                Issues.append(f"Missing required field: {Field}")
        
        # Check decision structure
        for DecisionId, DecisionData in self.Metadata.get('user_decisions', {}).items():
            if not isinstance(DecisionData, dict):
                Issues.append(f"Invalid decision structure: {DecisionId}")
            
            RequiredDecisionFields = ['Pattern', 'Decision', 'Reason', 'Timestamp', 'UserId']
            for Field in RequiredDecisionFields:
                if Field not in DecisionData:
                    Issues.append(f"Missing decision field {Field} in {DecisionId}")
        
        # Check audit trail structure
        for i, EntryData in enumerate(self.Metadata.get('audit_trail', [])):
            if not isinstance(EntryData, dict):
                Issues.append(f"Invalid audit entry structure at index {i}")
        
        return {
            'is_valid': len(Issues) == 0,
            'issues': Issues,
            'last_validated': datetime.now(timezone.utc).isoformat()
        }
    
    # Private helper methods
    
    def _LoadMetadata(self) -> Dict[str, Any]:
        """Load metadata from file."""
        if not self.MetadataPath.exists():
            return {}
        
        try:
            with open(self.MetadataPath, 'r') as f:
                return json.load(f)
        except Exception:
            # Try backup if main file is corrupted
            if self.BackupPath.exists():
                try:
                    with open(self.BackupPath, 'r') as f:
                        return json.load(f)
                except Exception:
                    return {}
            return {}
    
    def _InitializeMetadata(self) -> None:
        """Initialize metadata structure if not present."""
        if not self.Metadata:
            self.Metadata = {
                'version': '1.0.0',
                'created': datetime.now(timezone.utc).isoformat(),
                'user_decisions': {},
                'audit_trail': [],
                'security_metadata': self._GetDefaultSecurityMetadata(),
                'project_metadata': self._GetDefaultProjectMetadata(),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # Add initial audit entry
            self._AddAuditEntry(ActionType.CREATED, {
                'component': 'metadata_system',
                'version': '1.0.0'
            })
    
    def _SaveMetadata(self) -> None:
        """Save metadata to file with backup."""
        # Create backup if main file exists
        if self.MetadataPath.exists():
            try:
                import shutil
                shutil.copy2(self.MetadataPath, self.BackupPath)
            except Exception:
                pass
        
        # Update timestamp
        self.Metadata['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save main file
        try:
            with open(self.MetadataPath, 'w') as f:
                json.dump(self.Metadata, f, indent=2)
        except Exception:
            pass  # Fail silently for now
    
    def _AddAuditEntry(self, Action: ActionType, Details: Dict[str, Any]) -> None:
        """Add entry to audit trail."""
        EntryId = str(uuid.uuid4())
        Timestamp = datetime.now(timezone.utc).isoformat()
        UserId = self._GetCurrentUser()
        ProjectHash = self._GetProjectHash()
        
        AuditEntryObj = AuditEntry(
            Id=EntryId,
            Action=Action,
            Timestamp=Timestamp,
            UserId=UserId,
            Details=Details,
            GitUpVersion='0.2.0',
            ProjectHash=ProjectHash
        )
        
        if 'audit_trail' not in self.Metadata:
            self.Metadata['audit_trail'] = []
        
        self.Metadata['audit_trail'].append(asdict(AuditEntryObj))
        
        # Keep audit trail to reasonable size
        if len(self.Metadata['audit_trail']) > 1000:
            self.Metadata['audit_trail'] = self.Metadata['audit_trail'][-1000:]
    
    def _GetCurrentUser(self) -> str:
        """Get current user ID."""
        return os.getenv('USER', 'unknown')
    
    def _GetProjectHash(self) -> str:
        """Get project hash for audit trail."""
        ProjectStr = str(self.ProjectPath)
        return hashlib.md5(ProjectStr.encode()).hexdigest()[:8]
    
    def _IsDecisionExpired(self, DecisionData: Dict[str, Any]) -> bool:
        """Check if decision has expired."""
        ExpiresAt = DecisionData.get('ExpiresAt')
        if not ExpiresAt:
            return False
        
        try:
            ExpirationTime = datetime.fromisoformat(ExpiresAt.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) >= ExpirationTime
        except Exception:
            return False
    
    def _ExpireDecision(self, DecisionId: str) -> None:
        """Expire a decision."""
        if DecisionId in self.Metadata['user_decisions']:
            DecisionData = self.Metadata['user_decisions'][DecisionId]
            
            self._AddAuditEntry(ActionType.EXPIRED, {
                'decision_id': DecisionId,
                'pattern': DecisionData['Pattern'],
                'original_decision': DecisionData['Decision']
            })
            
            del self.Metadata['user_decisions'][DecisionId]
    
    def _GetDefaultSecurityMetadata(self) -> Dict[str, Any]:
        """Get default security metadata."""
        return {
            'SecurityLevel': 'medium',
            'LastSecurityCheck': datetime.now(timezone.utc).isoformat(),
            'NextSecurityCheck': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            'SecurityScore': 0.0,
            'RiskLevel': 'unknown',
            'CriticalGaps': 0,
            'HighGaps': 0,
            'TotalGaps': 0
        }
    
    def _GetDefaultProjectMetadata(self) -> Dict[str, Any]:
        """Get default project metadata."""
        return {
            'ProjectType': 'unknown',
            'ProjectName': self.ProjectPath.name,
            'ProjectPath': str(self.ProjectPath),
            'ProjectHash': self._GetProjectHash(),
            'GitRemoteUrl': self._GetGitRemoteUrl(),
            'LastModified': datetime.now(timezone.utc).isoformat(),
            'FileCount': 0,
            'DirectoryCount': 0
        }
    
    def _GetGitRemoteUrl(self) -> Optional[str]:
        """Get git remote URL if available."""
        try:
            GitDir = self.ProjectPath / '.git'
            if GitDir.exists():
                ConfigPath = GitDir / 'config'
                if ConfigPath.exists():
                    with open(ConfigPath, 'r') as f:
                        for Line in f:
                            if 'url =' in Line:
                                return Line.split('url = ')[1].strip()
        except Exception:
            pass
        return None
    
    def _MergeMetadata(self, ImportedData: Dict[str, Any]) -> None:
        """Merge imported metadata."""
        # This is a simplified merge - in production would be more sophisticated
        for Key, Value in ImportedData.items():
            if Key == 'user_decisions':
                self.Metadata['user_decisions'].update(Value)
            elif Key == 'audit_trail':
                self.Metadata['audit_trail'].extend(Value)
            else:
                self.Metadata[Key] = Value
    
    def _AppendMetadata(self, ImportedData: Dict[str, Any]) -> None:
        """Append imported metadata."""
        # Similar to merge but more careful about conflicts
        self._MergeMetadata(ImportedData)
    
    def _GetMetadataSize(self) -> int:
        """Get metadata file size."""
        try:
            return os.path.getsize(self.MetadataPath)
        except Exception:
            return 0