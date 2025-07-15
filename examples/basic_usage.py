#!/usr/bin/env python3
"""
GitUp Basic Usage Example
Demonstrates how to use GitUp programmatically
"""

from pathlib import Path
from gitup.core.bootstrap import ProjectBootstrap
from gitup.core.templates import TemplateManager

def main():
    """Example of using GitUp programmatically"""
    
    # 1. List available templates
    print("🚀 GitUp - Available Templates")
    print("=" * 40)
    
    template_manager = TemplateManager()
    templates = template_manager.list_templates()
    
    for template in templates:
        print(f"📋 {template['name']}: {template['description']}")
        print(f"   Language: {template['language']}")
        print(f"   Security: {template['security_level']}")
        print()
    
    # 2. Get detailed template info
    print("🔍 Template Details - Python Web")
    print("=" * 40)
    
    template_info = template_manager.get_template_info('python-web')
    print(f"Name: {template_info['name']}")
    print(f"Description: {template_info['description']}")
    print(f"Dependencies: {', '.join(template_info['dependencies'])}")
    print(f"Features: {', '.join(template_info['features'])}")
    print()
    
    # 3. Example bootstrap (dry run)
    print("🧪 Bootstrap Example (Dry Run)")
    print("=" * 40)
    
    bootstrapper = ProjectBootstrap(
        project_name="example-web-app",
        template="python-web",
        parent_path="/tmp",
        security_level="medium",
        dry_run=True,
        verbose=True
    )
    
    try:
        result = bootstrapper.run()
        print(f"✅ Bootstrap simulation completed: {result}")
    except Exception as e:
        print(f"❌ Bootstrap simulation failed: {e}")

if __name__ == "__main__":
    main()