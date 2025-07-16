# File: project_state_detector.py
# Path: gitup/core/project_state_detector.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-16
# Last Modified: 2025-07-16  02:45PM
"""
GitUp Project State Detection System
Foundation component for intelligent project analysis and setup recommendations.

This module provides the core intelligence for GitUp's adaptive behavior:
- Detects project development state (virgin, fresh, experienced, etc.)
- Assesses security risk levels based on project history
- Recommends appropriate setup complexity
- Enables smart defaults and user experience optimization

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from ..utils.exceptions import GitUpError


class ProjectState(Enum):
    """Project development state classification"""
    VIRGIN_DIRECTORY = "virgin_directory"      # No .git, no .gitignore
    FRESH_REPO = "fresh_repo"                  # Has .git, no .gitignore
    EXPERIENCED_REPO = "experienced_repo"      # Has .git + .gitignore
    GITHUB_REPO = "github_repo"                # Has GitHub remote
    MATURE_REPO = "mature_repo"                # GitHub + actions + history


class RiskLevel(Enum):
    """Security risk assessment levels"""
    LOW_RISK = "low_risk"           # Clean or new project
    MEDIUM_RISK = "medium_risk"     # Some development history
    HIGH_RISK = "high_risk"         # Secrets likely present


class SetupComplexity(Enum):
    """Required setup complexity levels"""
    MINIMAL_SETUP = "minimal_setup"        # Basic protection only
    STANDARD_SETUP = "standard_setup"      # Full GitUp features
    MIGRATION_SETUP = "migration_setup"    # History scanning needed
    ENTERPRISE_SETUP = "enterprise_setup"  # Full audit + compliance


@dataclass
class ProjectAnalysis:
    """Comprehensive project analysis results"""
    path: str
    state: ProjectState
    risk_level: RiskLevel
    setup_complexity: SetupComplexity
    
    # Detailed findings
    has_git: bool
    has_gitignore: bool
    has_github_remote: bool
    has_github_actions: bool
    commit_count: int
    days_since_creation: int
    file_count: int
    
    # Security indicators
    potential_secrets: List[str]
    sensitive_files: List[str]
    large_files: List[str]
    
    # Recommendations
    recommended_security_level: str
    recommended_templates: List[str]
    setup_warnings: List[str]
    
    # Metadata
    analysis_timestamp: str
    analysis_duration_ms: int


class ProjectStateDetector:
    """
    Core project state detection and analysis engine.
    
    This is the foundation component that enables all other GitUp functionality
    by providing intelligent project analysis and setup recommendations.
    """
    
    def __init__(self, project_path: str = ".", verbose: bool = False):
        """
        Initialize the project state detector.
        
        Args:
            project_path: Path to the project directory to analyze
            verbose: Enable verbose logging output
        """
        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        
        # Security patterns for detection
        self.secret_patterns = [
            "*.key", "*.pem", "*.p12", "*.pfx", "*.jks",
            "*secret*", "*password*", "*token*", "*api_key*",
            ".env", ".env.*", "config.json", "settings.json"
        ]
        
        self.sensitive_files = [
            "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
            "known_hosts", "authorized_keys", ".netrc",
            ".htpasswd", ".htaccess", "web.config"
        ]
        
        # Large file threshold (in MB)
        self.large_file_threshold = 10
        
        # Recent activity threshold (days)
        self.recent_activity_threshold = 30
    
    def analyze_project(self) -> ProjectAnalysis:
        """
        Perform comprehensive project analysis.
        
        Returns:
            ProjectAnalysis object containing complete analysis results
        """
        start_time = datetime.now()
        
        if self.verbose:
            print(f"🔍 Analyzing project: {self.project_path}")
        
        # Basic directory analysis
        has_git = self._has_git_repository()
        has_gitignore = self._has_gitignore()
        has_github_remote = self._has_github_remote() if has_git else False
        has_github_actions = self._has_github_actions()
        
        # Git repository analysis
        commit_count = self._get_commit_count() if has_git else 0
        days_since_creation = self._get_days_since_creation() if has_git else 0
        
        # File system analysis
        file_count = self._get_file_count()
        potential_secrets = self._find_potential_secrets()
        sensitive_files = self._find_sensitive_files()
        large_files = self._find_large_files()
        
        # State classification
        state = self._classify_project_state(
            has_git, has_gitignore, has_github_remote, has_github_actions
        )
        
        # Risk assessment
        risk_level = self._assess_risk_level(
            commit_count, days_since_creation, potential_secrets,
            sensitive_files, large_files
        )
        
        # Setup complexity determination
        setup_complexity = self._determine_setup_complexity(
            state, risk_level, commit_count, file_count
        )
        
        # Generate recommendations
        recommended_security_level = self._recommend_security_level(risk_level)
        recommended_templates = self._recommend_templates()
        setup_warnings = self._generate_setup_warnings(
            risk_level, potential_secrets, sensitive_files, large_files
        )
        
        # Calculate analysis duration
        end_time = datetime.now()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return ProjectAnalysis(
            path=str(self.project_path),
            state=state,
            risk_level=risk_level,
            setup_complexity=setup_complexity,
            has_git=has_git,
            has_gitignore=has_gitignore,
            has_github_remote=has_github_remote,
            has_github_actions=has_github_actions,
            commit_count=commit_count,
            days_since_creation=days_since_creation,
            file_count=file_count,
            potential_secrets=potential_secrets,
            sensitive_files=sensitive_files,
            large_files=large_files,
            recommended_security_level=recommended_security_level,
            recommended_templates=recommended_templates,
            setup_warnings=setup_warnings,
            analysis_timestamp=datetime.now().isoformat(),
            analysis_duration_ms=duration_ms
        )
    
    def _has_git_repository(self) -> bool:
        """Check if directory has a git repository"""
        return (self.project_path / ".git").exists()
    
    def _has_gitignore(self) -> bool:
        """Check if directory has a .gitignore file"""
        return (self.project_path / ".gitignore").exists()
    
    def _has_github_remote(self) -> bool:
        """Check if git repository has GitHub remote"""
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return "github.com" in result.stdout.lower()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def _has_github_actions(self) -> bool:
        """Check if project has GitHub Actions workflows"""
        actions_path = self.project_path / ".github" / "workflows"
        return actions_path.exists() and any(actions_path.glob("*.yml"))
    
    def _get_commit_count(self) -> int:
        """Get total number of commits in repository"""
        try:
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            return int(result.stdout.strip()) if result.returncode == 0 else 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            return 0
    
    def _get_days_since_creation(self) -> int:
        """Get days since repository creation"""
        try:
            result = subprocess.run(
                ["git", "log", "--reverse", "--format=%ct", "-n", "1"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                creation_timestamp = int(result.stdout.strip())
                creation_date = datetime.fromtimestamp(creation_timestamp)
                return (datetime.now() - creation_date).days
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError):
            pass
        return 0
    
    def _get_file_count(self) -> int:
        """Get total number of files in project (excluding .git)"""
        try:
            count = 0
            for root, dirs, files in os.walk(self.project_path):
                # Skip .git directory
                if ".git" in dirs:
                    dirs.remove(".git")
                count += len(files)
            return count
        except Exception:
            return 0
    
    def _find_potential_secrets(self) -> List[str]:
        """Find files that may contain secrets"""
        potential_secrets = []
        
        try:
            for pattern in self.secret_patterns:
                for file_path in self.project_path.rglob(pattern):
                    if not self._is_git_file(file_path):
                        relative_path = file_path.relative_to(self.project_path)
                        potential_secrets.append(str(relative_path))
        except Exception:
            pass
        
        return potential_secrets
    
    def _find_sensitive_files(self) -> List[str]:
        """Find sensitive configuration files"""
        sensitive_files = []
        
        try:
            for file_name in self.sensitive_files:
                for file_path in self.project_path.rglob(file_name):
                    if not self._is_git_file(file_path):
                        relative_path = file_path.relative_to(self.project_path)
                        sensitive_files.append(str(relative_path))
        except Exception:
            pass
        
        return sensitive_files
    
    def _find_large_files(self) -> List[str]:
        """Find files larger than threshold"""
        large_files = []
        
        try:
            for file_path in self.project_path.rglob("*"):
                if file_path.is_file() and not self._is_git_file(file_path):
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    if size_mb > self.large_file_threshold:
                        relative_path = file_path.relative_to(self.project_path)
                        large_files.append(f"{relative_path} ({size_mb:.1f}MB)")
        except Exception:
            pass
        
        return large_files
    
    def _is_git_file(self, file_path: Path) -> bool:
        """Check if file is in .git directory"""
        try:
            return ".git" in file_path.parts
        except Exception:
            return False
    
    def _classify_project_state(self, has_git: bool, has_gitignore: bool, 
                               has_github_remote: bool, has_github_actions: bool) -> ProjectState:
        """Classify project state based on detected features"""
        if has_github_actions:
            return ProjectState.MATURE_REPO
        elif has_github_remote:
            return ProjectState.GITHUB_REPO
        elif has_git and has_gitignore:
            return ProjectState.EXPERIENCED_REPO
        elif has_git:
            return ProjectState.FRESH_REPO
        else:
            return ProjectState.VIRGIN_DIRECTORY
    
    def _assess_risk_level(self, commit_count: int, days_since_creation: int,
                          potential_secrets: List[str], sensitive_files: List[str],
                          large_files: List[str]) -> RiskLevel:
        """Assess security risk level based on project characteristics"""
        risk_score = 0
        
        # Commit history risk
        if commit_count > 100:
            risk_score += 3
        elif commit_count > 20:
            risk_score += 2
        elif commit_count > 5:
            risk_score += 1
        
        # Age risk (older projects more likely to have accumulated secrets)
        if days_since_creation > 365:
            risk_score += 2
        elif days_since_creation > 90:
            risk_score += 1
        
        # File-based risk
        risk_score += len(potential_secrets) * 2
        risk_score += len(sensitive_files) * 1
        risk_score += len(large_files) * 1
        
        # Classify risk level
        if risk_score >= 8:
            return RiskLevel.HIGH_RISK
        elif risk_score >= 3:
            return RiskLevel.MEDIUM_RISK
        else:
            return RiskLevel.LOW_RISK
    
    def _determine_setup_complexity(self, state: ProjectState, risk_level: RiskLevel,
                                   commit_count: int, file_count: int) -> SetupComplexity:
        """Determine appropriate setup complexity"""
        if state == ProjectState.VIRGIN_DIRECTORY:
            return SetupComplexity.MINIMAL_SETUP
        
        if risk_level == RiskLevel.HIGH_RISK or commit_count > 50:
            return SetupComplexity.ENTERPRISE_SETUP
        
        if risk_level == RiskLevel.MEDIUM_RISK or commit_count > 10:
            return SetupComplexity.MIGRATION_SETUP
        
        return SetupComplexity.STANDARD_SETUP
    
    def _recommend_security_level(self, risk_level: RiskLevel) -> str:
        """Recommend security level based on risk assessment"""
        if risk_level == RiskLevel.HIGH_RISK:
            return "strict"
        elif risk_level == RiskLevel.MEDIUM_RISK:
            return "moderate"
        else:
            return "relaxed"
    
    def _recommend_templates(self) -> List[str]:
        """Recommend templates based on project analysis"""
        templates = []
        
        # Basic language detection
        if (self.project_path / "package.json").exists():
            if (self.project_path / "public").exists():
                templates.append("react-app")
            else:
                templates.append("node-web")
        elif (self.project_path / "requirements.txt").exists() or \
             (self.project_path / "setup.py").exists() or \
             (self.project_path / "pyproject.toml").exists():
            
            # Check for web frameworks in requirements.txt
            is_web_project = False
            if (self.project_path / "requirements.txt").exists():
                requirements_content = (self.project_path / "requirements.txt").read_text().lower()
                if any(framework in requirements_content for framework in ["flask", "django", "fastapi", "tornado"]):
                    is_web_project = True
            
            # Check for web framework imports in Python files
            if not is_web_project:
                for py_file in self.project_path.glob("*.py"):
                    try:
                        content = py_file.read_text().lower()
                        if any(framework in content for framework in ["flask", "django", "fastapi", "tornado"]):
                            is_web_project = True
                            break
                    except:
                        continue
            
            if is_web_project:
                templates.append("python-web")
            elif any(self.project_path.glob("**/jupyter*")) or \
                 any(self.project_path.glob("*.ipynb")):
                templates.append("python-data")
            else:
                templates.append("python-cli")
        elif (self.project_path / "README.md").exists() and \
             not any(self.project_path.glob("*.py")):
            templates.append("docs")
        
        # Default fallback
        if not templates:
            templates.append("python-cli")
        
        return templates
    
    def _generate_setup_warnings(self, risk_level: RiskLevel, 
                                potential_secrets: List[str],
                                sensitive_files: List[str],
                                large_files: List[str]) -> List[str]:
        """Generate setup warnings based on analysis"""
        warnings = []
        
        if risk_level == RiskLevel.HIGH_RISK:
            warnings.append("🔴 HIGH RISK: This project may contain secrets or sensitive data")
            warnings.append("🔍 Deep security scanning recommended before proceeding")
        
        if potential_secrets:
            warnings.append(f"⚠️  Found {len(potential_secrets)} potential secret files")
        
        if sensitive_files:
            warnings.append(f"⚠️  Found {len(sensitive_files)} sensitive configuration files")
        
        if large_files:
            warnings.append(f"⚠️  Found {len(large_files)} large files that may need .gitignore")
        
        return warnings
    
    def get_state_summary(self, analysis: ProjectAnalysis) -> str:
        """Get human-readable state summary"""
        state_descriptions = {
            ProjectState.VIRGIN_DIRECTORY: "🌱 New directory (no git, no .gitignore)",
            ProjectState.FRESH_REPO: "🔧 Fresh repository (git initialized, no .gitignore)",
            ProjectState.EXPERIENCED_REPO: "📝 Experienced repository (git + .gitignore)",
            ProjectState.GITHUB_REPO: "🐙 GitHub repository (connected to remote)",
            ProjectState.MATURE_REPO: "🏢 Mature repository (GitHub + Actions + history)"
        }
        
        return state_descriptions.get(analysis.state, str(analysis.state))
    
    def get_recommendations(self, analysis: ProjectAnalysis) -> Dict[str, Any]:
        """Get structured recommendations based on analysis"""
        return {
            "security_level": analysis.recommended_security_level,
            "templates": analysis.recommended_templates,
            "setup_complexity": analysis.setup_complexity.value,
            "immediate_actions": self._get_immediate_actions(analysis),
            "long_term_actions": self._get_long_term_actions(analysis)
        }
    
    def _get_immediate_actions(self, analysis: ProjectAnalysis) -> List[str]:
        """Get immediate actions based on analysis"""
        actions = []
        
        if analysis.state == ProjectState.VIRGIN_DIRECTORY:
            actions.append("Initialize git repository")
            actions.append("Create .gitignore file")
        
        if not analysis.has_gitignore:
            actions.append("Create project-appropriate .gitignore")
        
        if analysis.potential_secrets:
            actions.append("Review and secure potential secret files")
        
        if analysis.large_files:
            actions.append("Consider adding large files to .gitignore")
        
        return actions
    
    def _get_long_term_actions(self, analysis: ProjectAnalysis) -> List[str]:
        """Get long-term actions based on analysis"""
        actions = []
        
        if analysis.risk_level == RiskLevel.HIGH_RISK:
            actions.append("Implement comprehensive security scanning")
            actions.append("Set up audit logging")
        
        if not analysis.has_github_remote:
            actions.append("Consider setting up GitHub remote")
        
        if not analysis.has_github_actions:
            actions.append("Set up CI/CD with GitHub Actions")
        
        return actions