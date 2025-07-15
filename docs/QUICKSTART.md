# GitUp Quick Start Guide

Get up and running with GitUp in minutes!

## Installation

```bash
# Install from PyPI (when available)
pip install gitup

# Or install from source
git clone https://github.com/CallMeChewy/GitUp.git
cd GitUp
pip install -e .
```

## Basic Usage

### 1. List Available Templates

```bash
gitup templates
```

Output:
```
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Template    ┃ Description                           ┃ Language   ┃ Security ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ python-web  │ Python web application (Flask/Django) │ Python     │ high     │
│ python-data │ Python data science project           │ Python     │ medium   │
│ python-cli  │ Python command-line tool              │ Python     │ medium   │
│ node-web    │ Node.js web application               │ JavaScript │ high     │
│ react-app   │ React application                     │ JavaScript │ medium   │
│ docs        │ Documentation project                 │ Markdown   │ low      │
└─────────────┴───────────────────────────────────────┴────────────┴──────────┘
```

### 2. Get Template Details

```bash
gitup templates --template=python-web
```

### 3. Bootstrap a New Project

```bash
# Basic usage (auto-detects template)
gitup bootstrap my-awesome-project

# Specify template
gitup bootstrap my-web-app --template=python-web

# Choose security level
gitup bootstrap my-app --template=python-web --security=high

# Test with dry run first
gitup bootstrap my-app --template=python-web --dry-run
```

### 4. Navigate and Start Coding

```bash
cd my-awesome-project
source .venv/bin/activate  # Activate virtual environment
gitup status              # Check project status
```

## Command Reference

### Bootstrap Options

```bash
gitup bootstrap PROJECT_NAME [OPTIONS]
```

**Options:**
- `--template, -t`: Project template (default: auto)
- `--path, -p`: Parent directory (default: current)
- `--security, -s`: Security level (low/medium/high)
- `--no-venv`: Skip virtual environment setup
- `--no-gitguard`: Skip GitGuard integration
- `--dry-run`: Preview without creating

### Template Management

```bash
gitup templates                    # List all templates
gitup templates --template=NAME    # Show template details
gitup templates --all             # Show all template info
```

### Project Management

```bash
gitup status [PROJECT_PATH]        # Show project status
gitup upgrade [PROJECT_PATH]       # Upgrade existing project
```

### Configuration

```bash
gitup config show                  # Show current config
gitup config --help               # Configuration options
```

## What GitUp Creates

When you run `gitup bootstrap my-project`, GitUp creates:

```
my-project/
├── .git/                  # Git repository
│   └── hooks/            # Pre-commit security hooks
├── .venv/                # Virtual environment
├── src/                  # Source code
├── tests/                # Test directory
├── docs/                 # Documentation
├── .gitignore            # Smart, context-aware gitignore
├── .gitguard.yaml        # GitGuard security configuration
├── .gitup.yaml           # GitUp project metadata
├── requirements.txt      # Python dependencies
├── activate_env.sh       # Environment activation script
└── README.md            # Project documentation
```

## Security Features

GitUp integrates GitGuard security from day one:

### Pre-commit Hooks
- Automatic security scanning before each commit
- Blocks commits with critical security issues
- Provides remediation suggestions

### Smart .gitignore
- Context-aware file exclusions
- Prevents accidental credential commits
- Template-specific security patterns

### Security Levels
- **Low**: Basic security, minimal restrictions
- **Medium**: Balanced security and usability
- **High**: Maximum security, strict validation

## Example Workflows

### Python Web Application

```bash
# Create a Flask web app
gitup bootstrap my-web-app --template=python-web --security=high

# Navigate and activate environment
cd my-web-app
source .venv/bin/activate

# Start coding
code src/main.py

# Secure commit
gitguard commit -m "Add user authentication"
```

### Data Science Project

```bash
# Create a data science project
gitup bootstrap ml-project --template=python-data --security=medium

# Navigate and activate environment
cd ml-project
source .venv/bin/activate

# Start with Jupyter
jupyter notebook
```

### CLI Tool

```bash
# Create a command-line tool
gitup bootstrap my-cli-tool --template=python-cli --security=medium

# Navigate and activate environment
cd my-cli-tool
source .venv/bin/activate

# Test the generated CLI
python src/main.py
```

## Troubleshooting

### Common Issues

**Git not configured:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**Virtual environment issues:**
```bash
# Recreate virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**GitGuard errors:**
```bash
# Check security status
gitguard status

# Fix issues automatically
gitguard fix --auto
```

### Getting Help

```bash
gitup --help                    # General help
gitup bootstrap --help          # Bootstrap command help
gitup templates --help          # Template command help
```

## Next Steps

1. **Explore Templates**: Try different project templates
2. **Customize Security**: Adjust security levels for your needs
3. **Learn GitGuard**: Master the integrated security features
4. **Contribute**: Add your own templates and improvements

## Community

- **GitHub**: https://github.com/CallMeChewy/GitUp
- **Issues**: Report bugs and request features
- **Discussions**: Ask questions and share ideas
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

Happy coding with GitUp! 🚀