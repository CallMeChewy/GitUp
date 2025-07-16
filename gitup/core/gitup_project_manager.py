# File: gitup_project_manager.py
# Path: gitup/core/gitup_project_manager.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-16
# Last Modified: 2025-07-16  03:45PM
"""
GitUp Project Manager - Centralized .gitup/ directory management system.

This module implements the proper .gitup/ directory structure as specified in the
master specification, providing centralized management of all GitUp files and
state tracking.

File Structure:
my-project/
├── .gitup/              # GitUp's hidden directory
│   ├── config.yaml      # Project security settings
│   ├── state.json       # Current project state
│   ├── audit.log        # All operations log
│   ├── compliance.json  # Security compliance status
│   ├── .gitupignore     # GitUp-specific patterns
│   ├── .gitupignore.meta # User decision metadata
│   └── cache/           # Performance optimizations

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from .project_state_detector import ProjectStateDetector, ProjectAnalysis
from ..utils.exceptions import GitUpError


@dataclass
class GitUpProjectState:
    """Project state tracking for GitUp operations"""
    last_gitup_commit: Optional[str] = None
    last_git_commit: Optional[str] = None
    vanilla_git_detected: bool = False
    compliance_status: str = "UNKNOWN"
    security_level: str = "moderate"
    init_timestamp: Optional[str] = None
    last_audit: Optional[str] = None
    project_analysis: Optional[Dict[str, Any]] = None


@dataclass
class GitUpProjectConfig:
    """Project configuration for GitUp settings"""
    security_level: str = "moderate"
    block_on_critical: bool = True
    block_on_high: bool = False
    block_on_medium: bool = False
    auto_remediation: bool = True
    scan_depth: str = "standard"
    audit_enabled: bool = True
    compliance_checks: bool = True
    template_type: Optional[str] = None
    user_preferences: Dict[str, Any] = None


class GitUpProjectManager:
    """
    Centralized manager for GitUp project operations.
    
    This class implements the proper .gitup/ directory structure and provides
    unified management of all GitUp files, state tracking, and configuration.
    """
    
    def __init__(self, project_path: str = ".", verbose: bool = False):
        """
        Initialize the GitUp project manager.
        
        Args:
            project_path: Path to the project directory
            verbose: Enable verbose logging output
        """
        self.project_path = Path(project_path).resolve()
        self.verbose = verbose
        
        # Define .gitup directory structure
        self.gitup_dir = self.project_path / ".gitup"
        self.config_path = self.gitup_dir / "config.yaml"
        self.state_path = self.gitup_dir / "state.json"
        self.audit_path = self.gitup_dir / "audit.log"
        self.compliance_path = self.gitup_dir / "compliance.json"
        self.cache_dir = self.gitup_dir / "cache"
        
        # GitUp ignore files within .gitup directory
        self.gitupignore_path = self.gitup_dir / ".gitupignore"
        self.gitupignore_meta_path = self.gitup_dir / ".gitupignore.meta"
        
        # Initialize logging
        self._setup_logging()
        
        # Load or initialize project state and config
        self.state = self._load_state()
        self.config = self._load_config()
        
        # Initialize project state detector
        self.state_detector = ProjectStateDetector(str(self.project_path), verbose)
    
    def initialize_project(self, force: bool = False) -> Dict[str, Any]:
        """
        Initialize GitUp for a project with proper directory structure.
        
        Args:
            force: Force initialization even if .gitup already exists
            
        Returns:
            Dictionary with initialization results
        """
        if self.gitup_dir.exists() and not force:
            return {
                "status": "already_initialized",
                "message": "Project already has GitUp initialized",
                "gitup_dir": str(self.gitup_dir)
            }
        
        try:
            # Create .gitup directory structure
            self._create_directory_structure()
            
            # Run project analysis
            analysis = self.state_detector.analyze_project()
            
            # Initialize configuration based on analysis
            self._initialize_config(analysis)
            
            # Initialize state tracking
            self._initialize_state(analysis)
            
            # Initialize compliance tracking
            self._initialize_compliance(analysis)
            
            # Create initial .gitupignore
            self._initialize_gitupignore(analysis)
            
            # Log initialization
            self._log_operation("project_initialized", {
                "project_path": str(self.project_path),
                "analysis_summary": {
                    "state": analysis.state.value,
                    "risk_level": analysis.risk_level.value,
                    "setup_complexity": analysis.setup_complexity.value
                }
            })
            
            return {
                "status": "initialized",
                "message": "GitUp successfully initialized",
                "gitup_dir": str(self.gitup_dir),
                "analysis": asdict(analysis)
            }
            
        except Exception as e:
            self._log_operation("initialization_failed", {"error": str(e)})
            raise GitUpError(f"Failed to initialize GitUp project: {e}")
    
    def get_project_status(self) -> Dict[str, Any]:
        """
        Get comprehensive project status information.
        
        Returns:
            Dictionary with complete project status
        """
        if not self.gitup_dir.exists():
            return {
                "initialized": False,
                "message": "GitUp not initialized for this project"
            }
        
        # Run fresh analysis
        analysis = self.state_detector.analyze_project()
        
        # Check compliance status
        compliance_status = self._check_compliance()
        
        return {
            "initialized": True,
            "gitup_dir": str(self.gitup_dir),
            "project_analysis": asdict(analysis),
            "current_state": asdict(self.state),
            "current_config": asdict(self.config),
            "compliance_status": compliance_status,
            "files_status": {
                "config_exists": self.config_path.exists(),
                "state_exists": self.state_path.exists(),
                "audit_exists": self.audit_path.exists(),
                "compliance_exists": self.compliance_path.exists(),
                "gitupignore_exists": self.gitupignore_path.exists(),
                "cache_dir_exists": self.cache_dir.exists()
            }
        }
    
    def update_security_level(self, level: str) -> None:
        """
        Update security level and reconfigure accordingly.
        
        Args:
            level: New security level (strict/moderate/relaxed)
        """
        valid_levels = ["strict", "moderate", "relaxed"]
        if level not in valid_levels:
            raise GitUpError(f"Invalid security level: {level}. Must be one of {valid_levels}")
        
        # Update configuration
        self.config.security_level = level
        self._apply_security_level_config(level)
        
        # Update state
        self.state.security_level = level
        self.state.last_audit = datetime.now(timezone.utc).isoformat()
        
        # Save changes
        self._save_config()
        self._save_state()
        
        # Log the change
        self._log_operation("security_level_updated", {
            "old_level": self.state.security_level,
            "new_level": level
        })
    
    def run_compliance_check(self) -> Dict[str, Any]:
        """
        Run comprehensive compliance check and update status.
        
        Returns:
            Dictionary with compliance results
        """
        try:
            # Run project analysis
            analysis = self.state_detector.analyze_project()
            
            # Check various compliance aspects
            compliance_results = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": "UNKNOWN",
                "security_analysis": {
                    "risk_level": analysis.risk_level.value,
                    "potential_secrets": len(analysis.potential_secrets),
                    "sensitive_files": len(analysis.sensitive_files),
                    "large_files": len(analysis.large_files)
                },
                "file_compliance": self._check_file_compliance(),
                "git_compliance": self._check_git_compliance(),
                "audit_trail": self._get_recent_audit_entries()
            }
            
            # Determine overall status
            compliance_results["overall_status"] = self._determine_compliance_status(compliance_results)
            
            # Update compliance file
            self._save_compliance(compliance_results)
            
            # Update state
            self.state.compliance_status = compliance_results["overall_status"]
            self.state.last_audit = compliance_results["timestamp"]
            self._save_state()
            
            # Log compliance check
            self._log_operation("compliance_check_completed", {
                "status": compliance_results["overall_status"],
                "issues_found": compliance_results.get("issues_count", 0)
            })
            
            return compliance_results
            
        except Exception as e:
            self._log_operation("compliance_check_failed", {"error": str(e)})
            raise GitUpError(f"Compliance check failed: {e}")
    
    def migrate_legacy_files(self) -> Dict[str, Any]:
        """
        Migrate legacy .gitupignore files to new .gitup/ structure.
        
        Returns:
            Dictionary with migration results
        """
        legacy_gitupignore = self.project_path / ".gitupignore"
        legacy_meta = self.project_path / ".gitupignore.meta"
        
        migration_results = {
            "files_migrated": [],
            "files_backed_up": [],
            "errors": []
        }
        
        try:
            # Create .gitup directory if it doesn't exist
            if not self.gitup_dir.exists():
                self._create_directory_structure()
            
            # Migrate .gitupignore
            if legacy_gitupignore.exists():
                # Create backup
                backup_path = self.project_path / f".gitupignore.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                legacy_gitupignore.rename(backup_path)
                migration_results["files_backed_up"].append(str(backup_path))
                
                # Copy to new location
                self.gitupignore_path.write_text(backup_path.read_text())
                migration_results["files_migrated"].append(str(self.gitupignore_path))
            
            # Migrate .gitupignore.meta
            if legacy_meta.exists():
                # Create backup
                backup_path = self.project_path / f".gitupignore.meta.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                legacy_meta.rename(backup_path)
                migration_results["files_backed_up"].append(str(backup_path))
                
                # Copy to new location
                self.gitupignore_meta_path.write_text(backup_path.read_text())
                migration_results["files_migrated"].append(str(self.gitupignore_meta_path))
            
            # Log migration
            self._log_operation("legacy_files_migrated", migration_results)
            
            migration_results["status"] = "success"
            return migration_results
            
        except Exception as e:
            error_msg = f"Migration failed: {e}"
            migration_results["errors"].append(error_msg)
            migration_results["status"] = "failed"
            self._log_operation("migration_failed", {"error": error_msg})
            return migration_results
    
    # Private helper methods
    
    def _create_directory_structure(self) -> None:
        """Create the .gitup directory structure"""
        self.gitup_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create .gitup/.gitignore to exclude cache from git
        gitup_gitignore = self.gitup_dir / ".gitignore"
        gitup_gitignore.write_text("cache/\n*.tmp\n*.log\n")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        if not self.gitup_dir.exists():
            return
        
        log_format = "%(asctime)s - %(levelname)s - %(message)s"
        logging.basicConfig(
            level=logging.INFO if self.verbose else logging.WARNING,
            format=log_format,
            handlers=[
                logging.FileHandler(self.audit_path),
                logging.StreamHandler() if self.verbose else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_state(self) -> GitUpProjectState:
        """Load project state from state.json"""
        if not self.state_path.exists():
            return GitUpProjectState()
        
        try:
            with open(self.state_path, 'r') as f:
                data = json.load(f)
            return GitUpProjectState(**data)
        except Exception:
            return GitUpProjectState()
    
    def _save_state(self) -> None:
        """Save project state to state.json"""
        try:
            with open(self.state_path, 'w') as f:
                json.dump(asdict(self.state), f, indent=2)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not save state: {e}")
    
    def _load_config(self) -> GitUpProjectConfig:
        """Load project configuration from config.yaml"""
        if not self.config_path.exists():
            return GitUpProjectConfig()
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
            return GitUpProjectConfig(**data)
        except Exception:
            return GitUpProjectConfig()
    
    def _save_config(self) -> None:
        """Save project configuration to config.yaml"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(asdict(self.config), f, default_flow_style=False)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not save config: {e}")
    
    def _initialize_config(self, analysis: ProjectAnalysis) -> None:
        """Initialize configuration based on project analysis"""
        self.config.security_level = analysis.recommended_security_level
        self.config.template_type = analysis.recommended_templates[0] if analysis.recommended_templates else None
        self._apply_security_level_config(analysis.recommended_security_level)
        self._save_config()
    
    def _initialize_state(self, analysis: ProjectAnalysis) -> None:
        """Initialize state tracking based on project analysis"""
        self.state.init_timestamp = datetime.now(timezone.utc).isoformat()
        self.state.security_level = analysis.recommended_security_level
        self.state.compliance_status = "INITIALIZED"
        self.state.project_analysis = asdict(analysis)
        self._save_state()
    
    def _initialize_compliance(self, analysis: ProjectAnalysis) -> None:
        """Initialize compliance tracking"""
        compliance_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "initialization": True,
            "project_state": analysis.state.value,
            "risk_level": analysis.risk_level.value,
            "security_warnings": analysis.setup_warnings,
            "compliance_status": "INITIALIZED"
        }
        self._save_compliance(compliance_data)
    
    def _initialize_gitupignore(self, analysis: ProjectAnalysis) -> None:
        """Initialize .gitupignore file based on analysis"""
        content = [
            "# GitUp Security Ignore File",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "# This file works alongside .gitignore for security-focused patterns",
            "",
            "# Other Security Patterns",
            ""
        ]
        
        self.gitupignore_path.write_text('\n'.join(content))
        
        # Initialize metadata
        meta_data = {
            "version": "1.0.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "user_decisions": {}
        }
        
        with open(self.gitupignore_meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2)
    
    def _apply_security_level_config(self, level: str) -> None:
        """Apply security level configuration"""
        if level == "strict":
            self.config.block_on_critical = True
            self.config.block_on_high = True
            self.config.block_on_medium = True
            self.config.auto_remediation = False
            self.config.scan_depth = "deep"
        elif level == "moderate":
            self.config.block_on_critical = True
            self.config.block_on_high = False
            self.config.block_on_medium = False
            self.config.auto_remediation = True
            self.config.scan_depth = "standard"
        elif level == "relaxed":
            self.config.block_on_critical = True
            self.config.block_on_high = False
            self.config.block_on_medium = False
            self.config.auto_remediation = True
            self.config.scan_depth = "basic"
    
    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log operation to audit log"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "user": os.getenv('USER', 'unknown'),
            "gitup_version": "0.2.0",
            "details": details
        }
        
        try:
            # Append to audit log
            with open(self.audit_path, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass  # Fail silently for logging
    
    def _check_compliance(self) -> Dict[str, Any]:
        """Check current compliance status"""
        if not self.compliance_path.exists():
            return {"status": "UNKNOWN", "message": "No compliance data available"}
        
        try:
            with open(self.compliance_path, 'r') as f:
                return json.load(f)
        except Exception:
            return {"status": "ERROR", "message": "Could not read compliance data"}
    
    def _save_compliance(self, data: Dict[str, Any]) -> None:
        """Save compliance data to compliance.json"""
        try:
            with open(self.compliance_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            if self.verbose:
                print(f"Warning: Could not save compliance data: {e}")
    
    def _check_file_compliance(self) -> Dict[str, Any]:
        """Check file-based compliance"""
        return {
            "gitupignore_exists": self.gitupignore_path.exists(),
            "gitupignore_meta_exists": self.gitupignore_meta_path.exists(),
            "audit_log_exists": self.audit_path.exists(),
            "config_exists": self.config_path.exists()
        }
    
    def _check_git_compliance(self) -> Dict[str, Any]:
        """Check git-related compliance"""
        return {
            "git_repo_exists": (self.project_path / ".git").exists(),
            "gitignore_exists": (self.project_path / ".gitignore").exists(),
            "gitup_in_gitignore": self._is_gitup_in_gitignore()
        }
    
    def _is_gitup_in_gitignore(self) -> bool:
        """Check if .gitup is properly ignored in .gitignore"""
        gitignore_path = self.project_path / ".gitignore"
        if not gitignore_path.exists():
            return False
        
        try:
            content = gitignore_path.read_text()
            return ".gitup/" in content or ".gitup" in content
        except Exception:
            return False
    
    def _get_recent_audit_entries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        if not self.audit_path.exists():
            return []
        
        try:
            entries = []
            with open(self.audit_path, 'r') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line.strip()))
            return entries[-limit:]  # Return last N entries
        except Exception:
            return []
    
    def _determine_compliance_status(self, results: Dict[str, Any]) -> str:
        """Determine overall compliance status from results"""
        # Simple compliance determination logic
        if results.get("security_analysis", {}).get("potential_secrets", 0) > 0:
            return "RISK_DETECTED"
        elif results.get("file_compliance", {}).get("gitupignore_exists", False):
            return "COMPLIANT"
        else:
            return "PARTIAL_COMPLIANCE"