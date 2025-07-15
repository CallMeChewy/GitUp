# File: pattern_analyzer.py
# Path: /home/herb/Desktop/GitUp/gitup/core/pattern_analyzer.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:35PM
"""
Pattern analysis system for GitUp security scanning.
Analyzes .gitignore patterns against security requirements and provides
intelligent suggestions for pattern conflicts and improvements.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class SecurityLevel(Enum):
    """Security level enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatternCategory(Enum):
    """Pattern category enumeration."""
    SECRETS = "secrets"
    DATABASES = "databases"
    LOGS = "logs"
    BACKUPS = "backups"
    IDE = "ide"
    CACHE = "cache"
    DEPENDENCIES = "dependencies"
    BUILD = "build"
    CUSTOM = "custom"


@dataclass
class SecurityPattern:
    """Security pattern definition."""
    Pattern: str
    Category: PatternCategory
    SecurityLevel: SecurityLevel
    Description: str
    FileExtensions: List[str]
    ExampleFiles: List[str]
    FalsePositiveRisk: float  # 0.0 to 1.0


@dataclass
class PatternAnalysis:
    """Pattern analysis result."""
    Pattern: str
    IsSecurityRisk: bool
    SecurityLevel: SecurityLevel
    Category: PatternCategory
    Confidence: float
    Recommendations: List[str]
    ConflictsWith: List[str]
    ExampleMatches: List[str]


class GitUpPatternAnalyzer:
    """
    Advanced pattern analyzer for GitUp security scanning.
    
    Analyzes .gitignore patterns for security gaps, conflicts, and provides
    intelligent suggestions for improving project security.
    """
    
    def __init__(self, ProjectPath: str):
        """
        Initialize the pattern analyzer.
        
        Args:
            ProjectPath: Path to the project directory
        """
        self.ProjectPath = Path(ProjectPath)
        self.SecurityPatterns = self._LoadSecurityPatterns()
        self.ProjectType = self._DetectProjectType()
        self.ProjectSpecificPatterns = self._GetProjectSpecificPatterns()
    
    def AnalyzePatterns(self, ExistingPatterns: List[str]) -> Dict[str, any]:
        """
        Analyze existing .gitignore patterns for security issues.
        
        Args:
            ExistingPatterns: List of patterns from .gitignore
            
        Returns:
            Dictionary with analysis results
        """
        Analysis = {
            'security_gaps': [],
            'pattern_conflicts': [],
            'recommendations': [],
            'risk_assessment': {},
            'project_specific': []
        }
        
        # Find security gaps
        Analysis['security_gaps'] = self._FindSecurityGaps(ExistingPatterns)
        
        # Find pattern conflicts
        Analysis['pattern_conflicts'] = self._FindPatternConflicts(ExistingPatterns)
        
        # Generate recommendations
        Analysis['recommendations'] = self._GenerateRecommendations(ExistingPatterns)
        
        # Assess overall risk
        Analysis['risk_assessment'] = self._AssessRisk(ExistingPatterns)
        
        # Add project-specific patterns
        Analysis['project_specific'] = self._GetProjectSpecificRecommendations(ExistingPatterns)
        
        return Analysis
    
    def ValidatePattern(self, Pattern: str) -> PatternAnalysis:
        """
        Validate a single pattern for security implications.
        
        Args:
            Pattern: Pattern to validate
            
        Returns:
            PatternAnalysis object with validation results
        """
        IsSecurityRisk = self._IsSecurityRisk(Pattern)
        SecurityLevel = self._GetPatternSecurityLevel(Pattern)
        Category = self._GetPatternCategory(Pattern)
        Confidence = self._GetConfidenceScore(Pattern)
        
        Recommendations = []
        ConflictsWith = []
        ExampleMatches = []
        
        if IsSecurityRisk:
            Recommendations = self._GetPatternRecommendations(Pattern)
            ConflictsWith = self._FindConflictingPatterns(Pattern)
            ExampleMatches = self._GetExampleMatches(Pattern)
        
        return PatternAnalysis(
            Pattern=Pattern,
            IsSecurityRisk=IsSecurityRisk,
            SecurityLevel=SecurityLevel,
            Category=Category,
            Confidence=Confidence,
            Recommendations=Recommendations,
            ConflictsWith=ConflictsWith,
            ExampleMatches=ExampleMatches
        )
    
    def GetSecurityScore(self, ExistingPatterns: List[str]) -> Dict[str, any]:
        """
        Calculate security score for current .gitignore patterns.
        
        Args:
            ExistingPatterns: List of patterns from .gitignore
            
        Returns:
            Dictionary with security score and details
        """
        TotalPatterns = len(self.SecurityPatterns)
        CoveredPatterns = 0
        SecurityGaps = 0
        RiskLevel = SecurityLevel.LOW
        
        for SecurityPattern in self.SecurityPatterns:
            if self._IsPatternCovered(SecurityPattern.Pattern, ExistingPatterns):
                CoveredPatterns += 1
            else:
                SecurityGaps += 1
                if SecurityPattern.SecurityLevel.value == SecurityLevel.CRITICAL.value:
                    RiskLevel = SecurityLevel.CRITICAL
                elif SecurityPattern.SecurityLevel.value == SecurityLevel.HIGH.value and RiskLevel != SecurityLevel.CRITICAL:
                    RiskLevel = SecurityLevel.HIGH
        
        CoveragePercent = (CoveredPatterns / TotalPatterns) * 100 if TotalPatterns > 0 else 0
        
        return {
            'score': CoveragePercent,
            'coverage': f"{CoveredPatterns}/{TotalPatterns}",
            'security_gaps': SecurityGaps,
            'risk_level': RiskLevel.value,
            'recommendations_count': len(self._GenerateRecommendations(ExistingPatterns))
        }
    
    def GenerateSecurityPatterns(self, SecurityLevel: SecurityLevel = SecurityLevel.MEDIUM) -> List[str]:
        """
        Generate recommended security patterns based on project type and security level.
        
        Args:
            SecurityLevel: Desired security level
            
        Returns:
            List of recommended patterns
        """
        RecommendedPatterns = []
        
        for SecurityPattern in self.SecurityPatterns:
            if self._ShouldIncludePattern(SecurityPattern, SecurityLevel):
                RecommendedPatterns.append(SecurityPattern.Pattern)
        
        # Add project-specific patterns
        if self.ProjectType in self.ProjectSpecificPatterns:
            ProjectPatterns = self.ProjectSpecificPatterns[self.ProjectType]
            for Pattern in ProjectPatterns:
                if Pattern['security_level'] == SecurityLevel.value or SecurityLevel == SecurityLevel.HIGH:
                    RecommendedPatterns.append(Pattern['pattern'])
        
        return sorted(set(RecommendedPatterns))
    
    def FindFilesMatchingPatterns(self, Patterns: List[str]) -> Dict[str, List[str]]:
        """
        Find files in project that match given patterns.
        
        Args:
            Patterns: List of patterns to match
            
        Returns:
            Dictionary mapping patterns to matched files
        """
        Matches = {}
        
        for Pattern in Patterns:
            Matches[Pattern] = []
            
            for Root, Dirs, Files in os.walk(self.ProjectPath):
                for File in Files:
                    FilePath = Path(Root) / File
                    RelativePath = FilePath.relative_to(self.ProjectPath)
                    
                    if self._PatternMatches(Pattern, str(RelativePath)):
                        Matches[Pattern].append(str(RelativePath))
        
        return Matches
    
    # Private helper methods
    
    def _LoadSecurityPatterns(self) -> List[SecurityPattern]:
        """Load security patterns database."""
        return [
            # Critical security patterns
            SecurityPattern(
                Pattern="*.env",
                Category=PatternCategory.SECRETS,
                SecurityLevel=SecurityLevel.CRITICAL,
                Description="Environment files containing secrets",
                FileExtensions=[".env"],
                ExampleFiles=[".env", ".env.local", ".env.production"],
                FalsePositiveRisk=0.1
            ),
            SecurityPattern(
                Pattern="*.key",
                Category=PatternCategory.SECRETS,
                SecurityLevel=SecurityLevel.CRITICAL,
                Description="Private key files",
                FileExtensions=[".key", ".pem"],
                ExampleFiles=["private.key", "server.key", "ssl.key"],
                FalsePositiveRisk=0.1
            ),
            SecurityPattern(
                Pattern="secrets.json",
                Category=PatternCategory.SECRETS,
                SecurityLevel=SecurityLevel.CRITICAL,
                Description="JSON files containing secrets",
                FileExtensions=[".json"],
                ExampleFiles=["secrets.json", "config/secrets.json"],
                FalsePositiveRisk=0.2
            ),
            
            # High security patterns
            SecurityPattern(
                Pattern="*.db",
                Category=PatternCategory.DATABASES,
                SecurityLevel=SecurityLevel.HIGH,
                Description="Database files",
                FileExtensions=[".db", ".sqlite", ".sqlite3"],
                ExampleFiles=["app.db", "data.sqlite", "users.db"],
                FalsePositiveRisk=0.4
            ),
            SecurityPattern(
                Pattern="*.log",
                Category=PatternCategory.LOGS,
                SecurityLevel=SecurityLevel.HIGH,
                Description="Log files that may contain sensitive data",
                FileExtensions=[".log"],
                ExampleFiles=["app.log", "error.log", "access.log"],
                FalsePositiveRisk=0.3
            ),
            
            # Medium security patterns
            SecurityPattern(
                Pattern="*.backup",
                Category=PatternCategory.BACKUPS,
                SecurityLevel=SecurityLevel.MEDIUM,
                Description="Backup files",
                FileExtensions=[".backup", ".bak"],
                ExampleFiles=["data.backup", "config.bak"],
                FalsePositiveRisk=0.2
            ),
            SecurityPattern(
                Pattern="node_modules/",
                Category=PatternCategory.DEPENDENCIES,
                SecurityLevel=SecurityLevel.MEDIUM,
                Description="Node.js dependencies",
                FileExtensions=[],
                ExampleFiles=["node_modules/"],
                FalsePositiveRisk=0.1
            ),
            
            # Low security patterns
            SecurityPattern(
                Pattern="*.tmp",
                Category=PatternCategory.CACHE,
                SecurityLevel=SecurityLevel.LOW,
                Description="Temporary files",
                FileExtensions=[".tmp", ".temp"],
                ExampleFiles=["temp.tmp", "cache.temp"],
                FalsePositiveRisk=0.1
            ),
            SecurityPattern(
                Pattern=".DS_Store",
                Category=PatternCategory.IDE,
                SecurityLevel=SecurityLevel.LOW,
                Description="macOS system files",
                FileExtensions=[],
                ExampleFiles=[".DS_Store"],
                FalsePositiveRisk=0.0
            )
        ]
    
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
        elif (self.ProjectPath / 'pom.xml').exists():
            return 'java'
        else:
            return 'unknown'
    
    def _GetProjectSpecificPatterns(self) -> Dict[str, List[Dict[str, any]]]:
        """Get project-specific security patterns."""
        return {
            'python': [
                {'pattern': '__pycache__/', 'security_level': 'low', 'reason': 'Python cache files'},
                {'pattern': '*.pyc', 'security_level': 'low', 'reason': 'Python bytecode'},
                {'pattern': '.pytest_cache/', 'security_level': 'low', 'reason': 'Pytest cache'},
                {'pattern': 'venv/', 'security_level': 'medium', 'reason': 'Virtual environment'},
                {'pattern': '.env', 'security_level': 'critical', 'reason': 'Environment variables'}
            ],
            'node': [
                {'pattern': 'node_modules/', 'security_level': 'medium', 'reason': 'Node dependencies'},
                {'pattern': 'npm-debug.log*', 'security_level': 'medium', 'reason': 'NPM debug logs'},
                {'pattern': '.npm', 'security_level': 'low', 'reason': 'NPM cache'},
                {'pattern': 'dist/', 'security_level': 'low', 'reason': 'Build output'},
                {'pattern': '.env', 'security_level': 'critical', 'reason': 'Environment variables'}
            ],
            'java': [
                {'pattern': 'target/', 'security_level': 'low', 'reason': 'Maven build directory'},
                {'pattern': '*.class', 'security_level': 'low', 'reason': 'Java bytecode'},
                {'pattern': '*.jar', 'security_level': 'medium', 'reason': 'JAR files'},
                {'pattern': '.gradle/', 'security_level': 'low', 'reason': 'Gradle cache'}
            ]
        }
    
    def _FindSecurityGaps(self, ExistingPatterns: List[str]) -> List[Dict[str, any]]:
        """Find security gaps in existing patterns."""
        Gaps = []
        
        for SecurityPattern in self.SecurityPatterns:
            if not self._IsPatternCovered(SecurityPattern.Pattern, ExistingPatterns):
                Gaps.append({
                    'pattern': SecurityPattern.Pattern,
                    'category': SecurityPattern.Category.value,
                    'security_level': SecurityPattern.SecurityLevel.value,
                    'description': SecurityPattern.Description,
                    'risk_score': self._GetRiskScore(SecurityPattern),
                    'recommended_action': 'add_to_gitupignore'
                })
        
        return sorted(Gaps, key=lambda x: x['risk_score'], reverse=True)
    
    def _FindPatternConflicts(self, ExistingPatterns: List[str]) -> List[Dict[str, any]]:
        """Find conflicts between existing patterns."""
        Conflicts = []
        
        for Pattern in ExistingPatterns:
            if self._IsSecurityRisk(Pattern):
                Conflicts.append({
                    'pattern': Pattern,
                    'issue': 'potential_security_risk',
                    'description': self._GetSecurityRiskDescription(Pattern),
                    'recommendation': 'review_and_decide'
                })
        
        return Conflicts
    
    def _GenerateRecommendations(self, ExistingPatterns: List[str]) -> List[Dict[str, any]]:
        """Generate recommendations for improving security."""
        Recommendations = []
        
        # Check for missing critical patterns
        CriticalGaps = [gap for gap in self._FindSecurityGaps(ExistingPatterns) 
                       if gap['security_level'] == 'critical']
        
        if CriticalGaps:
            Recommendations.append({
                'priority': 'high',
                'action': 'add_critical_patterns',
                'description': f"Add {len(CriticalGaps)} critical security patterns",
                'patterns': [gap['pattern'] for gap in CriticalGaps]
            })
        
        # Check for project-specific recommendations
        if self.ProjectType in self.ProjectSpecificPatterns:
            ProjectPatterns = self.ProjectSpecificPatterns[self.ProjectType]
            MissingProjectPatterns = []
            
            for Pattern in ProjectPatterns:
                if not self._IsPatternCovered(Pattern['pattern'], ExistingPatterns):
                    MissingProjectPatterns.append(Pattern['pattern'])
            
            if MissingProjectPatterns:
                Recommendations.append({
                    'priority': 'medium',
                    'action': 'add_project_specific',
                    'description': f"Add {len(MissingProjectPatterns)} {self.ProjectType}-specific patterns",
                    'patterns': MissingProjectPatterns
                })
        
        return Recommendations
    
    def _AssessRisk(self, ExistingPatterns: List[str]) -> Dict[str, any]:
        """Assess overall risk level."""
        SecurityGaps = self._FindSecurityGaps(ExistingPatterns)
        CriticalGaps = len([gap for gap in SecurityGaps if gap['security_level'] == 'critical'])
        HighGaps = len([gap for gap in SecurityGaps if gap['security_level'] == 'high'])
        
        if CriticalGaps > 0:
            RiskLevel = 'critical'
        elif HighGaps > 2:
            RiskLevel = 'high'
        elif HighGaps > 0:
            RiskLevel = 'medium'
        else:
            RiskLevel = 'low'
        
        return {
            'overall_risk': RiskLevel,
            'critical_gaps': CriticalGaps,
            'high_gaps': HighGaps,
            'total_gaps': len(SecurityGaps),
            'immediate_action_required': CriticalGaps > 0
        }
    
    def _GetProjectSpecificRecommendations(self, ExistingPatterns: List[str]) -> List[Dict[str, any]]:
        """Get project-specific recommendations."""
        if self.ProjectType not in self.ProjectSpecificPatterns:
            return []
        
        Recommendations = []
        ProjectPatterns = self.ProjectSpecificPatterns[self.ProjectType]
        
        for Pattern in ProjectPatterns:
            if not self._IsPatternCovered(Pattern['pattern'], ExistingPatterns):
                Recommendations.append({
                    'pattern': Pattern['pattern'],
                    'reason': Pattern['reason'],
                    'security_level': Pattern['security_level'],
                    'project_type': self.ProjectType
                })
        
        return Recommendations
    
    def _IsPatternCovered(self, Pattern: str, ExistingPatterns: List[str]) -> bool:
        """Check if pattern is covered by existing patterns."""
        for ExistingPattern in ExistingPatterns:
            if self._PatternMatches(Pattern, ExistingPattern) or Pattern == ExistingPattern:
                return True
        return False
    
    def _PatternMatches(self, Pattern: str, TestPattern: str) -> bool:
        """Check if patterns match using glob-like matching."""
        import fnmatch
        return fnmatch.fnmatch(TestPattern, Pattern)
    
    def _IsSecurityRisk(self, Pattern: str) -> bool:
        """Check if pattern represents a security risk."""
        SecurityKeywords = ['secret', 'key', 'password', 'token', 'credential', 'auth', 'config']
        
        for Keyword in SecurityKeywords:
            if Keyword in Pattern.lower():
                return True
        
        return False
    
    def _GetPatternSecurityLevel(self, Pattern: str) -> SecurityLevel:
        """Get security level for a pattern."""
        CriticalPatterns = ['.env', '*.key', '*.pem', 'secrets.json']
        HighPatterns = ['*.db', '*.log', 'config.json']
        
        for CriticalPattern in CriticalPatterns:
            if self._PatternMatches(Pattern, CriticalPattern):
                return SecurityLevel.CRITICAL
        
        for HighPattern in HighPatterns:
            if self._PatternMatches(Pattern, HighPattern):
                return SecurityLevel.HIGH
        
        return SecurityLevel.LOW
    
    def _GetPatternCategory(self, Pattern: str) -> PatternCategory:
        """Get category for a pattern."""
        if any(keyword in Pattern.lower() for keyword in ['secret', 'key', 'password', 'token']):
            return PatternCategory.SECRETS
        elif any(keyword in Pattern.lower() for keyword in ['db', 'database', 'sqlite']):
            return PatternCategory.DATABASES
        elif any(keyword in Pattern.lower() for keyword in ['log', 'logs']):
            return PatternCategory.LOGS
        elif any(keyword in Pattern.lower() for keyword in ['backup', 'bak']):
            return PatternCategory.BACKUPS
        else:
            return PatternCategory.CUSTOM
    
    def _GetConfidenceScore(self, Pattern: str) -> float:
        """Get confidence score for pattern analysis."""
        # This is a simplified implementation
        # In production, would use machine learning or more sophisticated analysis
        if self._IsSecurityRisk(Pattern):
            return 0.8
        else:
            return 0.6
    
    def _GetPatternRecommendations(self, Pattern: str) -> List[str]:
        """Get recommendations for a pattern."""
        if self._IsSecurityRisk(Pattern):
            return [
                "Review file contents for sensitive data",
                "Consider adding to .gitupignore",
                "Ensure proper access controls"
            ]
        else:
            return ["Pattern appears safe"]
    
    def _FindConflictingPatterns(self, Pattern: str) -> List[str]:
        """Find patterns that might conflict."""
        # This is a simplified implementation
        return []
    
    def _GetExampleMatches(self, Pattern: str) -> List[str]:
        """Get example files that would match this pattern."""
        # This would search the actual filesystem in production
        return [f"example_{Pattern}"]
    
    def _ShouldIncludePattern(self, SecurityPattern: SecurityPattern, SecurityLevel: SecurityLevel) -> bool:
        """Check if pattern should be included based on security level."""
        LevelHierarchy = {
            SecurityLevel.LOW: 1,
            SecurityLevel.MEDIUM: 2,
            SecurityLevel.HIGH: 3,
            SecurityLevel.CRITICAL: 4
        }
        
        return LevelHierarchy.get(SecurityPattern.SecurityLevel, 0) <= LevelHierarchy.get(SecurityLevel, 0)
    
    def _GetRiskScore(self, SecurityPattern: SecurityPattern) -> float:
        """Get risk score for a security pattern."""
        LevelScores = {
            SecurityLevel.LOW: 1.0,
            SecurityLevel.MEDIUM: 2.0,
            SecurityLevel.HIGH: 3.0,
            SecurityLevel.CRITICAL: 4.0
        }
        
        return LevelScores.get(SecurityPattern.SecurityLevel, 0.0)
    
    def _GetSecurityRiskDescription(self, Pattern: str) -> str:
        """Get description of security risk for a pattern."""
        if 'secret' in Pattern.lower():
            return "Pattern may match files containing secrets"
        elif 'config' in Pattern.lower():
            return "Configuration files may contain sensitive data"
        elif 'key' in Pattern.lower():
            return "Pattern may match private key files"
        else:
            return "Pattern may have security implications"