# File: exceptions.py
# Path: gitup/utils/exceptions.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:06PM
"""
GitUp Exception Classes
Custom exception hierarchy for GitUp error handling.
"""

class GitUpError(Exception):
    """Base exception for all GitUp errors"""
    pass

class TemplateError(GitUpError):
    """Exception raised for template-related errors"""
    pass

class BootstrapError(GitUpError):
    """Exception raised during project bootstrap process"""
    pass

class GitGuardIntegrationError(GitUpError):
    """Exception raised during GitGuard integration"""
    pass

class ConfigurationError(GitUpError):
    """Exception raised for configuration-related errors"""
    pass

class VirtualEnvironmentError(GitUpError):
    """Exception raised for virtual environment setup errors"""
    pass

class GitRepositoryError(GitUpError):
    """Exception raised for git repository operations"""
    pass

class SecurityViolationError(GitUpError):
    """Exception raised when security violations block operations"""
    
    def __init__(self, message: str, violations: list = None):
        super().__init__(message)
        self.violations = violations or []