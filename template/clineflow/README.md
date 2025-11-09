# Reference System

Link external repositories for Cline exploration via symlinks. This built-in feature allows Cline to access and explore code from other projects without copying files.

## Quick Start

```bash
# 1. Clone reference repos wherever you prefer
cd ~/projects  # or your preferred location
git clone https://github.com/your-org/backend-api
git clone https://github.com/your-org/frontend-app

# 2. Configure paths (back in your project)
cd ~/your-project
cp .clineflow.example .clineflow.local

# 3. Edit .clineflow.local with your repository paths
nano .clineflow.local

# Add your paths:
#   BACKEND_API_PATH="/Users/yourname/projects/backend-api"
#   FRONTEND_APP_PATH="/Users/yourname/projects/frontend-app"

# 4. Run the built-in setup script
./setup-refs.sh
```

## Usage

Once set up, reference files are accessible at `clineflow/` via symlinks:

- **@ Mentions**: Use `@clineflow/backend-api/README.md` in Cline conversations
- **VSCode Search**: Search works across symlinked files
- **Terminal Commands**: All commands work normally with symlinks
- **Live Updates**: Changes in reference repos appear immediately (real symlinks)

## How It Works

The `setup-refs.sh` script (installed with ClineFlow):

1. Reads `.clineflow.local` configuration
2. Finds all variables ending with `_PATH`
3. Creates symlinks in `clineflow/` directory
4. Validates paths and reports status

**Variable naming:** Variable names ending with `_PATH` automatically create symlinks. The symlink name is derived from the variable name:
- `BACKEND_API_PATH` → `clineflow/backend-api`
- `FRONTEND_APP_PATH` → `clineflow/frontend-app`
- `MY_TOOL_PATH` → `clineflow/my-tool`

## Integration with Build Tools

Integrate into your existing workflow:

```bash
# Node.js projects (package.json)
{
  "scripts": {
    "predev": "./setup-refs.sh",
    "postinstall": "./setup-refs.sh"
  }
}

# Python projects (Makefile)
.PHONY: dev
dev:
	./setup-refs.sh
	python manage.py runserver

# Go projects (Makefile)
.PHONY: build
build:
	./setup-refs.sh
	go build

# Or use git hooks
echo "./setup-refs.sh" > .git/hooks/post-checkout
chmod +x .git/hooks/post-checkout
```

## Adding New References

1. Clone the new repository to your preferred location
2. Add variable to `.clineflow.example` (optional, for team reference)
3. Add path variable to `.clineflow.local`:
   ```bash
   NEW_REPO_PATH="/path/to/new-repo"
   ```
4. Run `./setup-refs.sh` again - it will automatically create the new symlink

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
