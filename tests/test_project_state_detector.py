# File: test_project_state_detector.py
# Path: tests/test_project_state_detector.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-16
# Last Modified: 2025-07-16  02:50PM
"""
Tests for ProjectStateDetector - Foundation Component
Comprehensive test suite for the core project analysis engine.
"""

import os
import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

from gitup.core.project_state_detector import (
    ProjectStateDetector, ProjectState, RiskLevel, SetupComplexity,
    ProjectAnalysis
)


class TestProjectStateDetector:
    """Test suite for ProjectStateDetector core functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        self.detector = ProjectStateDetector(str(self.project_path))
    
    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_virgin_directory_detection(self):
        """Test detection of virgin directory (no git, no .gitignore)"""
        # Create empty directory
        analysis = self.detector.analyze_project()
        
        assert analysis.state == ProjectState.VIRGIN_DIRECTORY
        assert not analysis.has_git
        assert not analysis.has_gitignore
        assert not analysis.has_github_remote
        assert not analysis.has_github_actions
        assert analysis.commit_count == 0
        assert analysis.risk_level == RiskLevel.LOW_RISK
        assert analysis.setup_complexity == SetupComplexity.MINIMAL_SETUP
    
    def test_fresh_repo_detection(self):
        """Test detection of fresh repository (git, no .gitignore)"""
        # Create .git directory
        git_dir = self.project_path / ".git"
        git_dir.mkdir()
        
        analysis = self.detector.analyze_project()
        
        assert analysis.state == ProjectState.FRESH_REPO
        assert analysis.has_git
        assert not analysis.has_gitignore
        assert not analysis.has_github_remote
        assert not analysis.has_github_actions
    
    def test_experienced_repo_detection(self):
        """Test detection of experienced repository (git + .gitignore)"""
        # Create .git directory and .gitignore
        git_dir = self.project_path / ".git"
        git_dir.mkdir()
        gitignore = self.project_path / ".gitignore"
        gitignore.write_text("*.pyc\n__pycache__/\n")
        
        analysis = self.detector.analyze_project()
        
        assert analysis.state == ProjectState.EXPERIENCED_REPO
        assert analysis.has_git
        assert analysis.has_gitignore
        assert not analysis.has_github_remote
        assert not analysis.has_github_actions
    
    def test_github_repo_detection(self):
        """Test detection of GitHub repository"""
        # Create .git directory and .gitignore
        git_dir = self.project_path / ".git"
        git_dir.mkdir()
        gitignore = self.project_path / ".gitignore"
        gitignore.write_text("*.pyc\n")
        
        # Mock git remote command to return GitHub remote
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "origin\thttps://github.com/user/repo.git (fetch)\n"
            mock_run.return_value = mock_result
            
            analysis = self.detector.analyze_project()
            
            assert analysis.state == ProjectState.GITHUB_REPO
            assert analysis.has_github_remote
    
    def test_mature_repo_detection(self):
        """Test detection of mature repository (GitHub + Actions)"""
        # Create full project structure
        git_dir = self.project_path / ".git"
        git_dir.mkdir()
        gitignore = self.project_path / ".gitignore"
        gitignore.write_text("*.pyc\n")
        
        # Create GitHub Actions
        actions_dir = self.project_path / ".github" / "workflows"
        actions_dir.mkdir(parents=True)
        (actions_dir / "ci.yml").write_text("name: CI\n")
        
        # Mock git remote command
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "origin\thttps://github.com/user/repo.git (fetch)\n"
            mock_run.return_value = mock_result
            
            analysis = self.detector.analyze_project()
            
            assert analysis.state == ProjectState.MATURE_REPO
            assert analysis.has_github_actions
    
    def test_risk_assessment_low_risk(self):
        """Test low risk assessment for new/clean projects"""
        # Create minimal project
        analysis = self.detector.analyze_project()
        
        assert analysis.risk_level == RiskLevel.LOW_RISK
        assert len(analysis.potential_secrets) == 0
        assert len(analysis.sensitive_files) == 0
        assert analysis.recommended_security_level == "relaxed"
    
    def test_risk_assessment_medium_risk(self):
        """Test medium risk assessment"""
        # Create project with some risk indicators
        (self.project_path / "config.json").write_text('{"api_key": "secret"}')
        (self.project_path / ".env").write_text("SECRET_KEY=mysecret")
        
        # Mock git commands to simulate some history
        with patch('subprocess.run') as mock_run:
            def mock_git_command(cmd, **kwargs):
                if "rev-list" in cmd:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "15"  # 15 commits
                    return result
                elif "log" in cmd:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "1640995200"  # Mock timestamp
                    return result
                else:
                    result = MagicMock()
                    result.returncode = 1
                    return result
            
            mock_run.side_effect = mock_git_command
            
            analysis = self.detector.analyze_project()
            
            assert analysis.risk_level == RiskLevel.MEDIUM_RISK
            assert len(analysis.potential_secrets) >= 2
            assert analysis.recommended_security_level == "moderate"
    
    def test_risk_assessment_high_risk(self):
        """Test high risk assessment"""
        # Create project with many risk indicators
        secret_files = [
            ".env", "config.json", "secret.key", "private.pem",
            "password.txt", "token.json", "api_key.txt"
        ]
        
        for file_name in secret_files:
            (self.project_path / file_name).write_text("sensitive content")
        
        # Create large file
        large_file = self.project_path / "large_file.bin"
        large_file.write_bytes(b"x" * (15 * 1024 * 1024))  # 15MB file
        
        # Mock git commands to simulate extensive history
        with patch('subprocess.run') as mock_run:
            def mock_git_command(cmd, **kwargs):
                if "rev-list" in cmd:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "150"  # 150 commits
                    return result
                elif "log" in cmd:
                    result = MagicMock()
                    result.returncode = 0
                    result.stdout = "1609459200"  # Mock old timestamp
                    return result
                else:
                    result = MagicMock()
                    result.returncode = 1
                    return result
            
            mock_run.side_effect = mock_git_command
            
            analysis = self.detector.analyze_project()
            
            assert analysis.risk_level == RiskLevel.HIGH_RISK
            assert len(analysis.potential_secrets) >= 6
            assert len(analysis.large_files) >= 1
            assert analysis.recommended_security_level == "strict"
    
    def test_setup_complexity_determination(self):
        """Test setup complexity determination logic"""
        # Test minimal setup for virgin directory
        analysis = self.detector.analyze_project()
        assert analysis.setup_complexity == SetupComplexity.MINIMAL_SETUP
        
        # Test standard setup for basic git repo
        git_dir = self.project_path / ".git"
        git_dir.mkdir()
        
        analysis = self.detector.analyze_project()
        assert analysis.setup_complexity == SetupComplexity.STANDARD_SETUP
        
        # Test migration setup for medium risk
        (self.project_path / ".env").write_text("SECRET=test")
        (self.project_path / "config.json").write_text('{"key": "value"}')
        
        analysis = self.detector.analyze_project()
        assert analysis.setup_complexity == SetupComplexity.MIGRATION_SETUP
    
    def test_template_recommendations(self):
        """Test template recommendation logic"""
        # Test Python project detection
        (self.project_path / "requirements.txt").write_text("flask==2.0.0\n")
        (self.project_path / "app.py").write_text("from flask import Flask\n")
        
        analysis = self.detector.analyze_project()
        assert "python-web" in analysis.recommended_templates
        
        # Test Node.js project detection
        package_json = self.project_path / "package.json"
        package_json.write_text('{"name": "test", "dependencies": {"express": "^4.0.0"}}')
        (self.project_path / "requirements.txt").unlink()  # Remove Python indicator
        
        analysis = self.detector.analyze_project()
        assert "node-web" in analysis.recommended_templates
        
        # Test React project detection
        (self.project_path / "public").mkdir()
        (self.project_path / "public" / "index.html").write_text("<html></html>")
        
        analysis = self.detector.analyze_project()
        assert "react-app" in analysis.recommended_templates
    
    def test_file_detection_methods(self):
        """Test individual file detection methods"""
        # Test secret file detection
        secret_files = [".env", "secret.key", "password.txt"]
        for file_name in secret_files:
            (self.project_path / file_name).write_text("content")
        
        secrets = self.detector._find_potential_secrets()
        assert len(secrets) >= 3
        
        # Test sensitive file detection
        (self.project_path / "id_rsa").write_text("private key")
        (self.project_path / ".netrc").write_text("machine github.com")
        
        sensitive = self.detector._find_sensitive_files()
        assert len(sensitive) >= 2
        
        # Test large file detection
        large_file = self.project_path / "large.bin"
        large_file.write_bytes(b"x" * (20 * 1024 * 1024))  # 20MB
        
        large_files = self.detector._find_large_files()
        assert len(large_files) >= 1
        assert "large.bin" in large_files[0]
    
    def test_git_repository_analysis(self):
        """Test git repository analysis methods"""
        # Test without git
        assert not self.detector._has_git_repository()
        assert self.detector._get_commit_count() == 0
        
        # Test with git directory
        git_dir = self.project_path / ".git"
        git_dir.mkdir()
        
        assert self.detector._has_git_repository()
        
        # Mock git commands
        with patch('subprocess.run') as mock_run:
            # Mock commit count
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "42"
            mock_run.return_value = mock_result
            
            count = self.detector._get_commit_count()
            assert count == 42
    
    def test_state_summary_generation(self):
        """Test human-readable state summary generation"""
        analysis = self.detector.analyze_project()
        summary = self.detector.get_state_summary(analysis)
        
        assert "New directory" in summary
        assert "🌱" in summary
    
    def test_recommendations_generation(self):
        """Test structured recommendations generation"""
        analysis = self.detector.analyze_project()
        recommendations = self.detector.get_recommendations(analysis)
        
        assert "security_level" in recommendations
        assert "templates" in recommendations
        assert "setup_complexity" in recommendations
        assert "immediate_actions" in recommendations
        assert "long_term_actions" in recommendations
        
        # Check that recommendations are sensible
        assert recommendations["security_level"] == "relaxed"
        assert isinstance(recommendations["templates"], list)
        assert len(recommendations["immediate_actions"]) > 0
    
    def test_analysis_metadata(self):
        """Test analysis metadata generation"""
        analysis = self.detector.analyze_project()
        
        assert analysis.path == str(self.project_path)
        assert analysis.analysis_timestamp is not None
        assert analysis.analysis_duration_ms >= 0
        assert analysis.file_count >= 0
    
    def test_error_handling(self):
        """Test error handling in detection methods"""
        # Test with non-existent directory
        invalid_detector = ProjectStateDetector("/nonexistent/path")
        
        # Should not raise exception, but handle gracefully
        analysis = invalid_detector.analyze_project()
        assert analysis.state == ProjectState.VIRGIN_DIRECTORY
        assert analysis.file_count == 0
    
    def test_verbose_mode(self):
        """Test verbose mode output"""
        verbose_detector = ProjectStateDetector(str(self.project_path), verbose=True)
        
        # Should not raise exception with verbose output
        analysis = verbose_detector.analyze_project()
        assert analysis is not None
    
    def test_git_file_filtering(self):
        """Test filtering of .git files from analysis"""
        # Create .git directory with files
        git_dir = self.project_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")
        (git_dir / "objects").mkdir()
        
        # Create regular project files
        (self.project_path / "main.py").write_text("print('hello')")
        
        analysis = self.detector.analyze_project()
        
        # Should count regular files but not .git files
        assert analysis.file_count == 1
        
        # .git files should not appear in secret detection
        secrets = self.detector._find_potential_secrets()
        assert not any(".git" in secret for secret in secrets)
    
    def test_performance_requirements(self):
        """Test that analysis meets performance requirements"""
        # Create a moderately complex project
        for i in range(50):
            (self.project_path / f"file_{i}.py").write_text(f"# File {i}")
        
        (self.project_path / "subdir").mkdir()
        for i in range(20):
            (self.project_path / "subdir" / f"sub_{i}.txt").write_text(f"Sub {i}")
        
        analysis = self.detector.analyze_project()
        
        # Should complete within reasonable time (< 2 seconds as per spec)
        assert analysis.analysis_duration_ms < 2000
        assert analysis.file_count == 70


class TestProjectAnalysisDataclass:
    """Test the ProjectAnalysis dataclass"""
    
    def test_project_analysis_creation(self):
        """Test ProjectAnalysis dataclass creation"""
        analysis = ProjectAnalysis(
            path="/test/path",
            state=ProjectState.VIRGIN_DIRECTORY,
            risk_level=RiskLevel.LOW_RISK,
            setup_complexity=SetupComplexity.MINIMAL_SETUP,
            has_git=False,
            has_gitignore=False,
            has_github_remote=False,
            has_github_actions=False,
            commit_count=0,
            days_since_creation=0,
            file_count=0,
            potential_secrets=[],
            sensitive_files=[],
            large_files=[],
            recommended_security_level="relaxed",
            recommended_templates=["python-cli"],
            setup_warnings=[],
            analysis_timestamp="2025-07-16T14:30:00",
            analysis_duration_ms=150
        )
        
        assert analysis.path == "/test/path"
        assert analysis.state == ProjectState.VIRGIN_DIRECTORY
        assert analysis.risk_level == RiskLevel.LOW_RISK
        assert analysis.setup_complexity == SetupComplexity.MINIMAL_SETUP
        assert not analysis.has_git
        assert analysis.commit_count == 0
        assert analysis.recommended_security_level == "relaxed"
        assert "python-cli" in analysis.recommended_templates


class TestEnums:
    """Test the enum classes"""
    
    def test_project_state_enum(self):
        """Test ProjectState enum values"""
        assert ProjectState.VIRGIN_DIRECTORY.value == "virgin_directory"
        assert ProjectState.FRESH_REPO.value == "fresh_repo"
        assert ProjectState.EXPERIENCED_REPO.value == "experienced_repo"
        assert ProjectState.GITHUB_REPO.value == "github_repo"
        assert ProjectState.MATURE_REPO.value == "mature_repo"
    
    def test_risk_level_enum(self):
        """Test RiskLevel enum values"""
        assert RiskLevel.LOW_RISK.value == "low_risk"
        assert RiskLevel.MEDIUM_RISK.value == "medium_risk"
        assert RiskLevel.HIGH_RISK.value == "high_risk"
    
    def test_setup_complexity_enum(self):
        """Test SetupComplexity enum values"""
        assert SetupComplexity.MINIMAL_SETUP.value == "minimal_setup"
        assert SetupComplexity.STANDARD_SETUP.value == "standard_setup"
        assert SetupComplexity.MIGRATION_SETUP.value == "migration_setup"
        assert SetupComplexity.ENTERPRISE_SETUP.value == "enterprise_setup"