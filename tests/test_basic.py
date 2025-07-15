# File: test_basic.py
# Path: tests/test_basic.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-15
# Last Modified: 2025-07-15  02:10PM
"""
Basic tests for GitUp functionality
"""

import pytest
from pathlib import Path
from gitup.core.templates import TemplateManager
from gitup.core.gitguard_integration import GitGuardIntegration

class TestTemplateManager:
    """Test template management functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.template_manager = TemplateManager()
    
    def test_list_templates(self):
        """Test listing available templates"""
        templates = self.template_manager.list_templates()
        assert len(templates) > 0
        
        # Check required fields
        for template in templates:
            assert 'name' in template
            assert 'description' in template
            assert 'language' in template
            assert 'security_level' in template
    
    def test_get_template_info(self):
        """Test getting template information"""
        template_info = self.template_manager.get_template_info('python-web')
        
        assert template_info['name'] == 'python-web'
        assert template_info['language'] == 'Python'
        assert 'dependencies' in template_info
        assert 'gitignore' in template_info
        assert len(template_info['dependencies']) > 0
    
    def test_invalid_template(self):
        """Test handling of invalid template"""
        with pytest.raises(Exception):
            self.template_manager.get_template_info('invalid-template')

class TestGitGuardIntegration:
    """Test GitGuard integration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.integration = GitGuardIntegration()
    
    def test_security_config_generation(self):
        """Test security configuration generation"""
        template_info = {
            'name': 'python-web',
            'language': 'Python'
        }
        
        config = self.integration._get_security_config('medium', template_info)
        
        assert 'block_on_critical' in config
        assert 'scan_file_contents' in config
        assert 'custom_patterns' in config
        assert isinstance(config['custom_patterns'], list)
    
    def test_audit_config_generation(self):
        """Test audit configuration generation"""
        config = self.integration._get_audit_config('high')
        
        assert config['enabled'] is True
        assert config['retention_days'] == 90  # High security = longer retention
        assert config['log_format'] == 'json'