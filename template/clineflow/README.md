# LLM References

Link reference repositories for Cline exploration via symlinks.

## Quick Start

```bash
# 1. Clone reference repos wherever you prefer
cd ~/projects  # or your preferred location
git clone https://github.com/Jaabaali/companions-api
git clone https://github.com/Jaabaali/studio-web-client

# 2. Configure jabaliweb
cd ~/jabaliweb
cp .clineflow.example .clineflow.local

# 3. Edit .clineflow.local with your paths
# Example:
#   COMPANIONS_API_PATH="/Users/yourname/projects/companions-api"
#   STUDIO_WEB_CLIENT_PATH="/Users/yourname/projects/studio-web-client"

# 4. Create symlinks (or just run npm run dev - it auto-runs)
npm run setup:refs
```

## Usage

Once set up, reference files are accessible at `clineflow/` via symlinks:

- Use with @ mentions: `@clineflow/companions-api/README.md`
- VSCode search works across symlinked files
- Terminal commands work normally
- Changes in reference repos appear immediately (live symlinks)

## Commands

```bash
# Setup
npm run setup:refs        # Create/update symlinks
npm run setup:refs:check  # Verify configuration
npm run setup:hooks       # Install git hooks (optional)
npm run setup:all         # Complete setup

# Manual operations
cd clineflow
./link-refs.sh           # Create symlinks
./link-refs.sh check     # Verify config
./link-refs.sh clean     # Remove symlinks
```

## Auto-Integration

Symlinks are automatically checked/created when you run:

```bash
npm run dev    # Runs predev → setup:refs automatically
npm install    # Runs postinstall → checks config
```

## Adding New References

1. Clone the new repository
2. Add entry to `clineflow/index.json`
3. Add variable to `.clineflow.example`
4. Add path to your `.clineflow.local`
5. Run `npm run setup:refs`

## Troubleshooting

**Symlinks not appearing?**
```bash
npm run setup:refs:check  # Verify configuration
```

**Need to re-link?**
```bash
cd clineflow && ./link-refs.sh clean
npm run setup:refs
```

**jq not installed?**
```bash
# macOS
brew install jq

# Linux
sudo apt-get install jq
```

## Structure

```
jabaliweb/
├── .clineflow.example       # Template (versioned)
├── .clineflow.local         # Your paths (gitignored)
│
└── clineflow/
    ├── README.md            # This file
    ├── index.json          # Registry
    ├── link-refs.sh        # Setup script
    │
    ├── companions-api/     # → Symlink to your clone
    └── studio-web-client/  # → Symlink to your clone
