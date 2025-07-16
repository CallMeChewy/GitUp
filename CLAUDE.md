# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GitUp is an enhanced project bootstrap tool that builds on GitGuard's security foundation. It's part of Project Himalaya, demonstrating AI-human collaboration between Herbert J. Bowers (project creator) and Claude (technical implementation).

**Core Vision**: Transform the painful 30-60 minute project setup process into a 30-second one-command bootstrap experience with built-in security.

## System Design Philosophy

- Console-based system designed for curl installation
- Intentionally removed GUI packages for a lightweight design
- Goal to provide a full, old-fashioned CRT terminal experience (reminiscent of TV955)
- User interfaces should launch full-screen terminal interfaces as child processes when necessary
- Emphasis on maintaining a user-friendly approach despite minimalist console design

## Key Architecture

### Main Components

- **CLI Interface** (`gitup/cli.py`): Click-based command-line interface with rich console output
- **Bootstrap Engine** (`gitup/core/bootstrap.py`): Core project creation and setup logic
- **Template System** (`gitup/core/templates.py`): Project template management and processing
- **GitGuard Integration** (`gitup/core/gitguard_integration.py`): Security scanning and compliance
- **Ignore Manager** (`gitup/core/ignore_manager.py`): Revolutionary .gitupignore system
- **Diff Interface** (`gitup/core/diff_interface.py`): Interactive security pattern review
- **Metadata Manager** (`gitup/core/metadata_manager.py`): Audit trails and user decisions

### Project States and Detection

GitUp uses a sophisticated project state detection system:
- **VIRGIN_DIRECTORY**: No .git, no .gitignore  
- **FRESH_REPO**: Has .git, no .gitignore
- **EXPERIENCED_REPO**: Has .git + .gitignore
- **GITHUB_REPO**: Has GitHub remote
- **MATURE_REPO**: GitHub + actions + history

### Security Architecture

Three security levels with different enforcement:
- **Strict**: Blocks critical, high, and medium risks
- **Moderate**: Blocks critical only, auto-remediates others
- **Relaxed**: Blocks critical only, basic scanning depth

[... rest of the existing content remains unchanged ...]