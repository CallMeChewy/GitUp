#!/usr/bin/env node

// File: gitup_tv955_wizard.js
// Path: gitup/gitup_tv955_wizard.js
// Standard: AIDEV-PascalCase-2.1
// Created: 2025-07-17
// Last Modified: 2025-07-17  10:30PM
/*
GitUp TV955 Project Wizard - Authentic CRT Terminal Experience

This is the GitUp Project Wizard designed specifically for the TV955 
terminal emulator. It provides an immersive retro computing experience 
for secure project creation with GitUp's multi-level interface system.

Features:
- Authentic CRT terminal experience
- Template-based project creation
- Multi-level interface (Hardcore/Newbie/Standard)
- Security-first project bootstrapping
- Integration with GitUp's risk mitigation system

Part of Project Himalaya demonstrating AI-human collaboration.
Project Creator: Herbert J. Bowers
Technical Implementation: Claude (Anthropic)
*/

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { spawn, execSync } = require('child_process');

// Interface Mode Detection
const INTERFACE_MODE = process.env.GITUP_MODE || 'standard';

// Template Definitions (from GitUp templates.py converted to JS)
const TEMPLATES = {
    'python-web': {
        name: 'Python Web Application',
        description: 'Flask/Django web application with high security',
        language: 'Python',
        security_level: 'high',
        dependencies: ['flask>=2.0.0', 'requests>=2.28.0', 'python-dotenv>=0.19.0'],
        directories: ['src', 'tests', 'docs', 'static', 'templates'],
        features: [
            'Flask web framework',
            'Virtual environment setup', 
            'GitGuard security integration',
            'Pre-commit hooks',
            'Development server configuration'
        ]
    },
    'python-data': {
        name: 'Python Data Science',
        description: 'Data science project with Jupyter and pandas',
        language: 'Python',
        security_level: 'medium',
        dependencies: ['pandas>=1.5.0', 'numpy>=1.24.0', 'jupyter>=1.0.0'],
        directories: ['src', 'data', 'notebooks', 'tests', 'docs'],
        features: [
            'Data science libraries',
            'Jupyter notebook support',
            'Data directory structure',
            'Model versioning',
            'Visualization tools'
        ]
    },
    'python-cli': {
        name: 'Python CLI Tool', 
        description: 'Command-line application with Click framework',
        language: 'Python',
        security_level: 'medium',
        dependencies: ['click>=8.0.0', 'rich>=12.0.0', 'typer>=0.7.0'],
        directories: ['src', 'tests', 'docs'],
        features: [
            'Click CLI framework',
            'Rich terminal output',
            'Command-line argument parsing',
            'Packaging for distribution'
        ]
    },
    'node-web': {
        name: 'Node.js Web Application',
        description: 'Express.js web application with security middleware',
        language: 'JavaScript',
        security_level: 'high',
        dependencies: ['express', 'dotenv', 'cors', 'helmet'],
        directories: ['src', 'tests', 'docs', 'public'],
        features: [
            'Express.js framework',
            'Security middleware', 
            'Environment configuration',
            'Static file serving'
        ]
    },
    'react-app': {
        name: 'React Application',
        description: 'Modern React application with build optimization',
        language: 'JavaScript',
        security_level: 'medium',
        dependencies: ['react', 'react-dom', 'react-scripts'],
        directories: ['src', 'public', 'tests', 'docs'],
        features: [
            'React framework',
            'Component-based architecture',
            'Hot reloading',
            'Build optimization'
        ]
    },
    'docs': {
        name: 'Documentation Project',
        description: 'Markdown documentation with asset management',
        language: 'Markdown',
        security_level: 'low',
        dependencies: [],
        directories: ['docs', 'assets', 'examples'],
        features: [
            'Documentation structure',
            'Markdown support',
            'Asset management',
            'Example code organization'
        ]
    }
};

class GitUpTV955Wizard {
    constructor() {
        this.currentStep = 'welcome';
        this.projectConfig = {};
        this.selectedTemplate = null;
        this.rl = readline.createInterface({
            input: process.stdin,
            output: process.stdout
        });
        
        // CRT Terminal effects
        this.initTerminal();
    }
    
    initTerminal() {
        // Enable raw mode for authentic terminal experience
        if (process.stdin.setRawMode) {
            process.stdin.setRawMode(false);
        }
        
        // Handle terminal size
        this.terminalWidth = process.stdout.columns || 80;
        this.terminalHeight = process.stdout.rows || 24;
    }
    
    clearScreen() {
        // CRT-style screen clear
        process.stdout.write('\x1B[2J\x1B[3J\x1B[H');
    }
    
    drawCRTBorder() {
        const width = this.terminalWidth;
        const line = '═'.repeat(width - 2);
        
        console.log('╔' + line + '╗');
    }
    
    drawCRTFooter() {
        const width = this.terminalWidth;
        const line = '═'.repeat(width - 2);
        
        console.log('╚' + line + '╝');
    }
    
    centerText(text, width = this.terminalWidth) {
        const padding = Math.max(0, Math.floor((width - text.length) / 2));
        return ' '.repeat(padding) + text;
    }
    
    async showWelcomeScreen() {
        this.clearScreen();
        
        if (INTERFACE_MODE === 'hardcore') {
            console.log('GitUp Project Wizard v2.1');
            console.log('Templates: python-web, python-data, python-cli, node-web, react-app, docs');
            console.log('Mode: ' + INTERFACE_MODE.toUpperCase());
            console.log();
        } else if (INTERFACE_MODE === 'newbie') {
            this.drawCRTBorder();
            console.log(this.centerText('🚀 WELCOME TO GITUP PROJECT WIZARD 🚀'));
            console.log(this.centerText('═══════════════════════════════════════════'));
            console.log();
            console.log(this.centerText('🎓 LEARNING MODE ACTIVATED'));
            console.log();
            console.log('┌─ What is the GitUp Project Wizard? ─┐');
            console.log('│                                      │');
            console.log('│ This wizard helps you create new    │');
            console.log('│ programming projects with built-in  │');
            console.log('│ security from day one!              │');
            console.log('│                                      │');
            console.log('│ We\'ll guide you through:            │');
            console.log('│ • Choosing the right project type   │');
            console.log('│ • Setting up security protection    │');
            console.log('│ • Creating a professional structure │');
            console.log('│                                      │');
            console.log('└──────────────────────────────────────┘');
            console.log();
            this.drawCRTFooter();
        } else {
            // Standard mode
            this.drawCRTBorder();
            console.log(this.centerText('GITUP PROJECT WIZARD v2.1'));
            console.log(this.centerText('Secure Project Creation System'));
            console.log(this.centerText('═══════════════════════════════════════'));
            console.log();
            console.log('  Create new projects with built-in security and best practices');
            console.log('  Choose from professional templates optimized for your workflow');
            console.log();
            this.drawCRTFooter();
        }
        
        await this.waitForKeypress('\nPress ENTER to continue...');
        this.showTemplateSelection();
    }
    
    showTemplateSelection() {
        this.clearScreen();
        
        if (INTERFACE_MODE === 'hardcore') {
            console.log('Select template:');
            Object.keys(TEMPLATES).forEach((key, index) => {
                console.log(`${index + 1}. ${key}`);
            });
            console.log('0. Exit');
        } else if (INTERFACE_MODE === 'newbie') {
            this.drawCRTBorder();
            console.log(this.centerText('🎯 CHOOSE YOUR PROJECT TYPE'));
            console.log(this.centerText('═══════════════════════════════'));
            console.log();
            
            Object.entries(TEMPLATES).forEach(([key, template], index) => {
                console.log(`  ${index + 1}. ${template.name}`);
                console.log(`     → ${template.description}`);
                console.log(`     → Security Level: ${template.security_level.toUpperCase()}`);
                console.log(`     → Language: ${template.language}`);
                
                // Show why this template is useful
                if (key === 'python-web') {
                    console.log('     💡 Perfect for building websites, APIs, or web applications');
                } else if (key === 'python-data') {
                    console.log('     💡 Great for data analysis, machine learning, and research');
                } else if (key === 'python-cli') {
                    console.log('     💡 Ideal for command-line tools and automation scripts');
                } else if (key === 'node-web') {
                    console.log('     💡 Modern web development with JavaScript/TypeScript');
                } else if (key === 'react-app') {
                    console.log('     💡 Interactive user interfaces and web applications');
                } else if (key === 'docs') {
                    console.log('     💡 Documentation websites and technical writing');
                }
                console.log();
            });
            
            console.log('  0. Exit Wizard');
            console.log();
            this.drawCRTFooter();
        } else {
            // Standard mode
            this.drawCRTBorder();
            console.log(this.centerText('PROJECT TEMPLATE SELECTION'));
            console.log(this.centerText('═══════════════════════════════'));
            console.log();
            
            Object.entries(TEMPLATES).forEach(([key, template], index) => {
                const securityIcon = template.security_level === 'high' ? '🔒' : 
                                    template.security_level === 'medium' ? '🔐' : '🔓';
                console.log(`  ${index + 1}. ${template.name} ${securityIcon}`);
                console.log(`     ${template.description}`);
                console.log(`     Language: ${template.language} | Security: ${template.security_level}`);
                console.log();
            });
            
            console.log('  0. Exit');
            console.log();
            this.drawCRTFooter();
        }
        
        this.promptTemplateSelection();
    }
    
    async promptTemplateSelection() {
        const templateKeys = Object.keys(TEMPLATES);
        
        this.rl.question('\nSelect option (0-' + templateKeys.length + '): ', (answer) => {
            const choice = parseInt(answer);
            
            if (choice === 0) {
                this.exitWizard();
                return;
            }
            
            if (choice >= 1 && choice <= templateKeys.length) {
                const templateKey = templateKeys[choice - 1];
                this.selectedTemplate = templateKey;
                this.showTemplateDetails();
            } else {
                console.log('Invalid selection. Please try again.');
                this.promptTemplateSelection();
            }
        });
    }
    
    showTemplateDetails() {
        this.clearScreen();
        const template = TEMPLATES[this.selectedTemplate];
        
        if (INTERFACE_MODE === 'hardcore') {
            console.log(`Template: ${template.name}`);
            console.log(`Security: ${template.security_level}`);
            console.log(`Dependencies: ${template.dependencies.join(', ')}`);
            console.log();
        } else {
            this.drawCRTBorder();
            console.log(this.centerText(`📋 ${template.name.toUpperCase()}`));
            console.log(this.centerText('═'.repeat(template.name.length + 4)));
            console.log();
            console.log(`  Description: ${template.description}`);
            console.log(`  Language: ${template.language}`);
            console.log(`  Security Level: ${template.security_level.toUpperCase()}`);
            console.log();
            console.log('  📁 Project Structure:');
            template.directories.forEach(dir => {
                console.log(`     └── ${dir}/`);
            });
            console.log();
            console.log('  ⚡ Features:');
            template.features.forEach(feature => {
                console.log(`     • ${feature}`);
            });
            console.log();
            
            if (template.dependencies.length > 0) {
                console.log('  📦 Key Dependencies:');
                template.dependencies.slice(0, 3).forEach(dep => {
                    console.log(`     • ${dep}`);
                });
                if (template.dependencies.length > 3) {
                    console.log(`     • ... and ${template.dependencies.length - 3} more`);
                }
                console.log();
            }
            
            this.drawCRTFooter();
        }
        
        this.promptProjectName();
    }
    
    async promptProjectName() {
        if (INTERFACE_MODE === 'newbie') {
            console.log('💡 Tip: Choose a descriptive name like "my-blog-site" or "data-analysis-tool"');
        }
        
        this.rl.question('Enter project name: ', (projectName) => {
            if (!projectName.trim()) {
                console.log('Project name cannot be empty. Please try again.');
                this.promptProjectName();
                return;
            }
            
            // Validate project name
            if (!/^[a-zA-Z0-9_-]+$/.test(projectName)) {
                console.log('Project name can only contain letters, numbers, hyphens, and underscores.');
                this.promptProjectName();
                return;
            }
            
            this.projectConfig.name = projectName.trim();
            this.promptProjectLocation();
        });
    }
    
    async promptProjectLocation() {
        const defaultLocation = process.cwd();
        
        if (INTERFACE_MODE === 'newbie') {
            console.log(`\n💡 This is where your project folder will be created.`);
            console.log(`   Default location: ${defaultLocation}`);
        }
        
        this.rl.question(`Project location [${defaultLocation}]: `, (location) => {
            this.projectConfig.location = location.trim() || defaultLocation;
            this.showProjectSummary();
        });
    }
    
    showProjectSummary() {
        this.clearScreen();
        const template = TEMPLATES[this.selectedTemplate];
        
        this.drawCRTBorder();
        console.log(this.centerText('🎯 PROJECT CREATION SUMMARY'));
        console.log(this.centerText('═══════════════════════════════'));
        console.log();
        console.log(`  Project Name: ${this.projectConfig.name}`);
        console.log(`  Template: ${template.name}`);
        console.log(`  Language: ${template.language}`);
        console.log(`  Security Level: ${template.security_level.toUpperCase()}`);
        console.log(`  Location: ${this.projectConfig.location}`);
        console.log(`  Full Path: ${path.join(this.projectConfig.location, this.projectConfig.name)}`);
        console.log();
        
        if (INTERFACE_MODE === 'newbie') {
            console.log('🔒 Security Features Included:');
            console.log('   • Smart .gitignore with security patterns');
            console.log('   • GitGuard integration for credential protection');
            console.log('   • Pre-configured security settings');
            console.log('   • Automated security scanning');
            console.log();
        }
        
        this.drawCRTFooter();
        
        this.rl.question('\nCreate this project? (y/N): ', (answer) => {
            if (answer.toLowerCase() === 'y' || answer.toLowerCase() === 'yes') {
                this.createProject();
            } else {
                this.showTemplateSelection();
            }
        });
    }
    
    async createProject() {
        console.log('\n🚀 Creating project...\n');
        
        try {
            const projectPath = path.join(this.projectConfig.location, this.projectConfig.name);
            const template = TEMPLATES[this.selectedTemplate];
            
            // Create project directory
            console.log('📁 Creating project directory...');
            fs.mkdirSync(projectPath, { recursive: true });
            
            // Create subdirectories
            console.log('📁 Creating project structure...');
            template.directories.forEach(dir => {
                fs.mkdirSync(path.join(projectPath, dir), { recursive: true });
                console.log(`   └── ${dir}/`);
            });
            
            // Generate .gitignore
            console.log('🔒 Generating secure .gitignore...');
            const gitignoreContent = this.generateGitignore(template);
            fs.writeFileSync(path.join(projectPath, '.gitignore'), gitignoreContent);
            
            // Generate README.md
            console.log('📝 Creating README.md...');
            const readmeContent = this.generateReadme(template);
            fs.writeFileSync(path.join(projectPath, 'README.md'), readmeContent);
            
            // Initialize git repository
            console.log('🔧 Initializing git repository...');
            process.chdir(projectPath);
            execSync('git init', { stdio: 'pipe' });
            
            // Create initial commit
            console.log('💾 Creating initial commit...');
            execSync('git add .', { stdio: 'pipe' });
            execSync('git commit -m "Initial commit: Created with GitUp TV955 Wizard"', { stdio: 'pipe' });
            
            console.log('\n✅ Project created successfully!');
            console.log(`📍 Location: ${projectPath}`);
            
            if (INTERFACE_MODE === 'newbie') {
                console.log('\n🎉 Congratulations! Your secure project is ready!');
                console.log('\nNext steps:');
                console.log(`   cd ${this.projectConfig.name}`);
                console.log('   # Start coding with built-in security!');
            }
            
            await this.waitForKeypress('\nPress ENTER to continue...');
            this.exitWizard();
            
        } catch (error) {
            console.error('\n❌ Error creating project:', error.message);
            await this.waitForKeypress('\nPress ENTER to continue...');
            this.showTemplateSelection();
        }
    }
    
    generateGitignore(template) {
        let gitignore = `# GitUp Generated .gitignore - ${template.name}\n`;
        gitignore += `# Template: ${this.selectedTemplate}\n`;
        gitignore += `# Generated: ${new Date().toISOString().split('T')[0]}\n\n`;
        
        // Add template-specific patterns
        if (template.language === 'Python') {
            gitignore += `# Python\n__pycache__/\n*.py[cod]\n*$py.class\n.Python\nbuild/\ndist/\n*.egg-info/\n.venv/\nvenv/\n\n`;
        } else if (template.language === 'JavaScript') {
            gitignore += `# Node.js\nnode_modules/\nnpm-debug.log*\nyarn-debug.log*\nyarn-error.log*\n.npm\n.node_repl_history\n\n`;
        }
        
        // Add security patterns
        gitignore += `# Security\n.env\n.env.local\n.env.*.local\n*.key\n*.pem\n*.p12\n*.pfx\n*.jks\n*.keystore\nsecrets.*\n*secret*\n*password*\n*credential*\n\n`;
        
        // Add GitUp specific
        gitignore += `# GitUp\n.gitup/\nbootstrap_logs/\n\n`;
        
        // Add common patterns
        gitignore += `# IDE\n.vscode/\n.idea/\n*.swp\n*.swo\n\n`;
        gitignore += `# OS\n.DS_Store\nThumbs.db\ndesktop.ini\n`;
        
        return gitignore;
    }
    
    generateReadme(template) {
        let readme = `# ${this.projectConfig.name}\n\n`;
        readme += `${template.description}\n\n`;
        readme += `**Created with**: GitUp TV955 Project Wizard  \n`;
        readme += `**Template**: ${template.name}  \n`;
        readme += `**Language**: ${template.language}  \n`;
        readme += `**Security Level**: ${template.security_level}  \n\n`;
        
        readme += `## 🚀 Quick Start\n\n`;
        if (template.language === 'Python') {
            readme += `\`\`\`bash\n# Create virtual environment\npython -m venv venv\nsource venv/bin/activate  # On Windows: venv\\Scripts\\activate\n\n# Install dependencies\npip install -r requirements.txt\n\`\`\`\n\n`;
        } else if (template.language === 'JavaScript') {
            readme += `\`\`\`bash\n# Install dependencies\nnpm install\n\n# Start development server\nnpm start\n\`\`\`\n\n`;
        }
        
        readme += `## 📋 Features\n\n`;
        template.features.forEach(feature => {
            readme += `- ${feature}\n`;
        });
        
        readme += `\n## 🔒 Security\n\n`;
        readme += `This project was created with GitUp's security-first approach:\n\n`;
        readme += `- Smart .gitignore patterns prevent credential exposure\n`;
        readme += `- GitGuard integration for continuous security monitoring\n`;
        readme += `- Pre-configured security settings\n`;
        readme += `- ${template.security_level.toUpperCase()} security level enforcement\n\n`;
        
        readme += `## 🤝 Contributing\n\n`;
        readme += `1. Fork the repository\n`;
        readme += `2. Create a feature branch\n`;
        readme += `3. Make your changes\n`;
        readme += `4. Run security checks\n`;
        readme += `5. Submit a pull request\n\n`;
        
        readme += `---\n\n`;
        readme += `**🏔️ Created with [GitUp](https://github.com/your-org/gitup) - Secure Development Made Simple**\n`;
        
        return readme;
    }
    
    async waitForKeypress(prompt) {
        return new Promise((resolve) => {
            this.rl.question(prompt, () => {
                resolve();
            });
        });
    }
    
    exitWizard() {
        if (INTERFACE_MODE === 'newbie') {
            console.log('\n🎓 Thanks for using GitUp TV955 Project Wizard!');
            console.log('   Keep building secure projects! 🚀');
        } else if (INTERFACE_MODE === 'hardcore') {
            console.log('Exit.');
        } else {
            console.log('\n👋 Goodbye from GitUp Project Wizard!');
        }
        
        this.rl.close();
        process.exit(0);
    }
    
    run() {
        console.log('Starting GitUp TV955 Project Wizard...');
        this.showWelcomeScreen();
    }
}

// Handle process events
process.on('SIGINT', () => {
    console.log('\n\nWizard interrupted. Goodbye!');
    process.exit(0);
});

process.on('uncaughtException', (error) => {
    console.error('\nUnexpected error:', error.message);
    process.exit(1);
});

// Start the wizard
const wizard = new GitUpTV955Wizard();
wizard.run();