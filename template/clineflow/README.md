# Reference System

Link external repositories for Cline exploration via symlinks. This allows Cline to access and explore code from other projects without copying files.

## Quick Start

```bash
# 1. Clone reference repos wherever you prefer
cd ~/projects  # or your preferred location
git clone https://github.com/your-org/backend-api
git clone https://github.com/your-org/frontend-app

# 2. Create configuration file in your project
cd ~/your-project
cp .clineflow.example .clineflow.local

# 3. Edit .clineflow.local with your paths
# Example:
#   BACKEND_API_PATH="/Users/yourname/projects/backend-api"
#   FRONTEND_APP_PATH="/Users/yourname/projects/frontend-app"

# 4. Create symlinks using your setup script
./setup-refs.sh  # or integrate into your build process
```

## Usage

Once set up, reference files are accessible at `clineflow/` via symlinks:

- **@ Mentions**: Use `@clineflow/backend-api/README.md` in Cline conversations
- **VSCode Search**: Search works across symlinked files
- **Terminal Commands**: All commands work normally with symlinks
- **Live Updates**: Changes in reference repos appear immediately (real symlinks)

## Setup Script Example

Create a `setup-refs.sh` script in your project:

```bash
#!/bin/bash
# Load configuration
source .clineflow.local

# Create symlinks
mkdir -p clineflow
ln -sf "$BACKEND_API_PATH" clineflow/backend-api
ln -sf "$FRONTEND_APP_PATH" clineflow/frontend-app

echo "✓ Reference symlinks created"
```

## Integration Examples

Integrate into your existing workflow:

```bash
# Node.js projects (package.json)
{
  "scripts": {
    "setup:refs": "./setup-refs.sh",
    "predev": "npm run setup:refs",
    "postinstall": "./setup-refs.sh"
  }
}

# Python projects (Makefile)
setup-refs:
	./setup-refs.sh

dev: setup-refs
	python manage.py runserver

# Go projects
build: setup-refs
	./setup-refs.sh && go build
```

## Adding New References

1. Clone the new repository to your preferred location
2. Add variable to `.clineflow.example` (for team reference)
3. Add path to your `.clineflow.local` (your local config)
4. Update your setup script to create the symlink
5. Run your setup script to create the symlink

## Troubleshooting

**Symlinks not appearing?**
- Check paths in `.clineflow.local` are correct
- Verify referenced repos exist at specified paths
- Ensure you have permission to create symlinks

**Need to re-link?**
```bash
# Remove old symlinks
rm clineflow/backend-api clineflow/frontend-app

# Re-run setup
./setup-refs.sh
```

**Permission issues?**
```bash
# On Windows, symlinks may require admin privileges
# Consider using WSL or Git Bash with admin rights
```

## Structure

```
your-project/
├── .clineflow.example       # Template (versioned)
├── .clineflow.local         # Your paths (gitignored)
├── setup-refs.sh            # Your setup script
│
└── clineflow/
    ├── README.md            # This file
    ├── backend-api/         # → Symlink to your clone
    └── frontend-app/        # → Symlink to your clone
```

## Benefits

- **No File Duplication**: Reference repos stay in their original location
- **Always Current**: Changes sync instantly via symlinks
- **Cline Context**: Cline can explore referenced codebases with @ mentions
- **VSCode Integration**: Search and navigation work seamlessly
- **Team Flexibility**: Each developer can place repos anywhere via `.clineflow.local`
