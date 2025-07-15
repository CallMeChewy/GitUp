# File: gitguard_integration.py
# Path: gitup/core/gitguard_integration.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:09PM
"""
GitGuard Integration Module
Handles integration between GitUp and GitGuard for seamless security setup.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.exceptions import GitGuardIntegrationError

class GitGuardIntegration:
    """Handles GitGuard integration and configuration"""
    
    def __init__(self):
        self.config_template = self._get_config_template()
    
    def setup_for_project(self, project_path: Path, template_info: Dict[str, Any], 
                          security_level: str = 'medium'):
        """Set up GitGuard configuration for a new project"""
        try:
            # Create .gitguard.yaml configuration
            config = self._generate_gitguard_config(
                project_path, template_info, security_level
            )
            
            config_path = project_path / '.gitguard.yaml'
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            # Create .gitup.yaml to track GitUp metadata
            gitup_config = self._generate_gitup_config(template_info, security_level)
            gitup_config_path = project_path / '.gitup.yaml'
            with open(gitup_config_path, 'w') as f:
                yaml.dump(gitup_config, f, default_flow_style=False, indent=2)
            
        except Exception as e:
            raise GitGuardIntegrationError(f"Failed to set up GitGuard integration: {e}")
    
    def _generate_gitguard_config(self, project_path: Path, template_info: Dict[str, Any], 
                                  security_level: str) -> Dict[str, Any]:
        """Generate GitGuard configuration based on project template"""
        
        # Base configuration
        config = {
            'project': {
                'name': project_path.name,
                'template': template_info['name'],
                'created': datetime.now().isoformat(),
                'gitup_version': '0.1.0',
                'bootstrap_method': 'gitup'
            },
            'security': self._get_security_config(security_level, template_info),
            'audit': self._get_audit_config(security_level),
            'remediation': self._get_remediation_config(security_level),
            'notification': self._get_notification_config(),
            'integration': self._get_integration_config()
        }
        
        return config
    
    def _get_security_config(self, security_level: str, template_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate security configuration based on level and template"""
        
        # Base security settings
        base_config = {
            'auto_fix_enabled': True,
            'max_file_size_mb': 1,
            'custom_patterns': []
        }
        
        # Security level configurations
        if security_level == 'low':
            base_config.update({
                'block_on_critical': False,
                'block_on_high': False,
                'scan_file_contents': True,
                'scan_git_history': False  # New project, no history
            })
        elif security_level == 'medium':
            base_config.update({
                'block_on_critical': False,  # Gentle start
                'block_on_high': False,
                'scan_file_contents': True,
                'scan_git_history': False
            })
        elif security_level == 'high':
            base_config.update({
                'block_on_critical': True,
                'block_on_high': True,
                'scan_file_contents': True,
                'scan_git_history': True
            })
        
        # Template-specific adjustments
        if template_info['name'] == 'python-web':
            base_config['custom_patterns'].extend([
                'SECRET_KEY.*',
                'DATABASE_URL.*',
                'API_KEY.*'
            ])
        elif template_info['name'] == 'python-data':
            base_config['custom_patterns'].extend([
                'DATA_SOURCE_.*',
                'MODEL_API_.*'
            ])
        elif template_info['name'] == 'node-web':
            base_config['custom_patterns'].extend([
                'JWT_SECRET.*',
                'SESSION_SECRET.*'
            ])
        
        return base_config
    
    def _get_audit_config(self, security_level: str) -> Dict[str, Any]:
        """Generate audit configuration"""
        return {
            'enabled': True,
            'retention_days': 90 if security_level == 'high' else 30,
            'log_format': 'json',
            'include_content': security_level == 'high',
            'compress_old_logs': True
        }
    
    def _get_remediation_config(self, security_level: str) -> Dict[str, Any]:
        """Generate remediation configuration"""
        return {
            'interactive_mode': security_level != 'high',  # Auto-fix in high security
            'create_backups': True,
            'clean_git_history': security_level == 'high',
            'update_gitignore': True,
            'remove_files': False  # Conservative default
        }
    
    def _get_notification_config(self) -> Dict[str, Any]:
        """Generate notification configuration"""
        return {
            'console_notifications': True,
            'email_alerts': False,
            'slack_webhook': None
        }
    
    def _get_integration_config(self) -> Dict[str, Any]:
        """Generate integration configuration"""
        return {
            'github_checks': False,
            'jira_project': None,
            'ci_cd_integration': False
        }
    
    def _generate_gitup_config(self, template_info: Dict[str, Any], 
                               security_level: str) -> Dict[str, Any]:
        """Generate GitUp metadata configuration"""
        return {
            'gitup': {
                'version': '0.1.0',
                'created': datetime.now().isoformat(),
                'template': {
                    'name': template_info['name'],
                    'description': template_info['description'],
                    'language': template_info['language'],
                    'security_level': security_level
                },
                'features': {
                    'virtual_environment': True,
                    'gitguard_integration': True,
                    'git_hooks': True,
                    'smart_gitignore': True
                },
                'project': {
                    'bootstrap_method': 'gitup_cli',
                    'gitignore_generated': True,
                    'dependencies_installed': True,
                    'git_initialized': True
                }
            }
        }
    
    def _get_config_template(self) -> Dict[str, Any]:
        """Get base configuration template"""
        return {
            'project': {
                'name': '',
                'template': '',
                'created': '',
                'gitup_version': '0.1.0'
            },
            'security': {
                'auto_fix_enabled': True,
                'block_on_critical': False,
                'block_on_high': False,
                'scan_file_contents': True,
                'scan_git_history': False,
                'max_file_size_mb': 1,
                'custom_patterns': []
            },
            'audit': {
                'enabled': True,
                'retention_days': 30,
                'log_format': 'json',
                'include_content': False,
                'compress_old_logs': True
            },
            'remediation': {
                'interactive_mode': True,
                'create_backups': True,
                'clean_git_history': False,
                'update_gitignore': True,
                'remove_files': False
            },
            'notification': {
                'console_notifications': True,
                'email_alerts': False,
                'slack_webhook': None
            },
            'integration': {
                'github_checks': False,
                'jira_project': None,
                'ci_cd_integration': False
            }
        }