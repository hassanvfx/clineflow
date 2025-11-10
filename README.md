# ClineFlow

> 🤖 Transform Cline into your AI development partner with persistent memory

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Easy as 1-2-3

**Turn Cline into a teammate who remembers everything**

### 1️⃣ Install ClineFlow
```bash
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/install.sh | bash
```

### 2️⃣ Ask Cline "How can we work?"
Cline reads your project's workflow and becomes context-aware. Through journals, every conversation builds on the last - **Cline remembers what you built, why you built it, and what's next.**

### 3️⃣ Say "please commit"
Cline automatically:
- 📝 Documents your decisions in the active journal
- 💾 Commits code + updated journal together
- 🔄 Creates context for your next session

**Result:** Every new task starts with full context. No more "what did we do last time?" 🎉

---

## 💡 Why This Changes Everything

**Without ClineFlow:**
- ❌ Each Cline session starts from scratch
- ❌ You repeat context manually every time
- ❌ No history of why decisions were made
- ❌ Can't resume work seamlessly

**With ClineFlow:**
- ✅ **Persistent Memory**: Journals capture every decision, every conversation
- ✅ **Seamless Continuation**: New tasks load previous context automatically
- ✅ **True Collaboration**: Cline becomes a partner who remembers your project
- ✅ **Zero Context Loss**: Work today, continue tomorrow without explanation

**This isn't just documentation - it's turning Cline into a teammate with memory.**

---

## 🔄 Returns Accepted Anytime

Changed your mind? No hard feelings!

```bash
./uninstall.sh
```

Your `docs/journals/` are safe and require manual removal if desired. [See all options →](#installation-options)

---

## ✨ Features

- **🚀 Intelligent Commits**: Just say "please commit" and Cline automatically stages, documents, and commits
- **📝 Unified Journaling**: Every task documented in structured journals with automatic context capture
- **🎯 Universal**: Works with Python, JavaScript, Go, Rust, Java - any language with git
- **📏 Code Organization**: Built-in guidelines for maintainable, composable code
- **🔄 Multi-Task Support**: Continue related work in the same journal for complete context
- **💡 Zero Dependencies**: Just bash + git required

## 🎬 Quick Start

### One-Line Install

```bash
# Using curl
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/install.sh | bash

# Using wget
wget -qO- https://raw.githubusercontent.com/hassanvfx/clineflow/main/install.sh | bash
```

### What Gets Installed

```
your-project/
├── .clinerules                    # Cline assistant rules
├── clineflow/                     # Reference documentation
│   ├── JOURNAL_TEMPLATE.md        # Template for task journals
│   ├── PROCEDURES.md              # Standard operating procedures
│   ├── WORKING_WITH_CLINE.md      # Complete user guide
│   └── README.md                  # ClineFlow overview
└── docs/
    └── journals/                  # Your task journals go here
        └── .gitkeep
```

## 🚀 How It Works

### 1. Start a Task

Create a journal for your work:

```bash
# Create journal from template
cp clineflow/JOURNAL_TEMPLATE.md docs/journals/my-feature.md
```

### 2. Work with Cline

Tell Cline what you want to build. The workflow guides Cline to:
- Keep code modular and focused (300-500 LOC per file)
- Document decisions as you go
- Maintain clear context

### 3. Intelligent Commit

When ready to commit, just say:

```
"please commit"
```

Cline will automatically:
1. ✅ Detect your active journal
2. ✅ Generate a context-aware journal entry
3. ✅ Append entry to your journal
4. ✅ Stage all changes including updated journal
5. ✅ Create a descriptive commit message
6. ✅ Execute `git commit`

**One command. Complete documentation. Every time.**

## 📖 Core Concepts

### Intelligent Commits

Traditional workflow:
```bash
# You have to do this manually
git add .
# Write journal entry
# Update journal file
git add docs/journals/my-feature.md
git commit -m "feat: implement feature"
```

With Cline Workflow:
```bash
# Just say to Cline:
"please commit"

# ✓ Journal auto-updated
# ✓ Changes staged
# ✓ Committed with context
```

### Unified Journaling

**Every task MUST have a journal.** This keeps your development:
- 📚 **Documented**: Complete history of decisions
- 🔄 **Contextual**: New Cline tasks load previous context
- 🎯 **Organized**: All related work in one place

**Multi-Task Pattern:**
```markdown
# Task 1 - Initial Implementation
(work documented here)

# Task 2 - Bug Fix
(continuation documented here)

# Task 3 - Refinements
(more work documented here)
```

Keep related work in the same journal for complete context.

### Code Organization

Built-in guidelines ensure maintainable code:

- **Module/File Size**: 300-500 LOC ideal, >1K LOC unacceptable
- **Single Responsibility**: Each file has one clear purpose
- **Composition Over Monoliths**: Break large files into focused units

**Universal:** Works for any language - Python classes, JavaScript components, Go packages, Rust modules, etc.

## 🛠️ Advanced Usage

### Installation Options

```bash
# Dry run (see what would be installed)
./install.sh --dry-run

# Force overwrite existing files
./install.sh --force

# Uninstall
./install.sh --uninstall

# Show help
./install.sh --help
```

### Returns Accepted Anytime 🔄

Changed your mind? No hard feelings!

Download and run the uninstall script in your project directory:

```bash
# Using curl
curl -fsSL https://raw.githubusercontent.com/hassanvfx/clineflow/main/uninstall.sh | bash

# Using wget
wget -qO- https://raw.githubusercontent.com/hassanvfx/clineflow/main/uninstall.sh | bash

# Or if you have the repo
./uninstall.sh
```

**What gets removed:**
- `.clinerules`
- `clineflow/` directory
- `setup-refs.sh` and `.clineflow.example`
- `.clineflow.local` (if exists)
- Reference symlinks (if configured)

**⚠️ Note:** Your `docs/journals/` are safe and require manual removal if desired.

**Options:**
```bash
./uninstall.sh --dry-run    # Preview what would be removed
./uninstall.sh --yes        # Skip confirmation prompt
./uninstall.sh --help       # Show all options
```

### Customization

Edit `.clinerules` to customize for your project:
- Adjust code size limits
- Add project-specific rules
- Configure documentation patterns

### Reference System (Optional)

**Link other codebases for Cline exploration** - useful when you want Cline to have context from external projects.

**What it does:**
- Creates symlinks in `clineflow/` pointing to other repositories
- Cline can explore those repos using @ mentions: `@clineflow/backend-api/README.md`
- No file duplication - changes sync instantly via symlinks

**Quick setup (3 steps):**

1. **Clone external repos** wherever you prefer:
   ```bash
   cd ~/projects
   git clone https://github.com/your-org/backend-api
   ```

2. **Configure paths** in your project:
   ```bash
   # Copy example config
   cp .clineflow.example .clineflow.local
   
   # Edit with your paths
   nano .clineflow.local
   ```
   
   Add your repository paths:
   ```bash
   BACKEND_API_PATH="/Users/yourname/projects/backend-api"
   FRONTEND_APP_PATH="/Users/yourname/projects/frontend-app"
   ```

3. **Run the setup script** (included with ClineFlow):
   ```bash
   ./setup-refs.sh
   ```

**Result:** Cline can now explore linked repos as if they were part of your project!

**Full details:** See [clineflow/README.md](template/clineflow/README.md) for advanced configuration.

## 📚 Documentation

- **[WORKING_WITH_CLINE.md](template/clineflow/WORKING_WITH_CLINE.md)** - Complete user guide
- **[PROCEDURES.md](template/clineflow/PROCEDURES.md)** - Standard operating procedures
- **[JOURNAL_TEMPLATE.md](template/clineflow/JOURNAL_TEMPLATE.md)** - Journal template
- **[clineflow/README.md](template/clineflow/README.md)** - Reference system overview

## 🤔 Why This Workflow?

### Problem: AI Context Loss

Working with AI assistants across multiple sessions, you lose context:
- What did we decide last time?
- Why did we implement it this way?
- What were the trade-offs?

### Solution: Unified Journaling

Every task documented. Every decision recorded. Complete context available for:
- Future AI sessions
- Team members
- Future you

### Bonus: Intelligent Commits

Commits automatically include:
- Code changes
- Updated documentation
- Context-aware journal entries

**One workflow. Complete history. Zero overhead.**

## 🎯 Best Practices

1. **One Journal Per Feature/Bug**: Create focused journals
2. **Commit Frequently**: Just say "please commit" often
3. **Multi-Task Same Journal**: Keep related work together
4. **Read Your Journals**: Before starting related work, review the journal
5. **Customize .clinerules**: Adapt to your project's needs

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Create a journal documenting your work
5. Submit a pull request

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

## 🙏 Acknowledgments

Created to solve the challenge of maintaining context and documentation when working with AI assistants.

## 🐛 Issues & Support

- **Issues**: [GitHub Issues](https://github.com/hassanvfx/clineflow/issues)
- **Discussions**: [GitHub Discussions](https://github.com/hassanvfx/clineflow/discussions)

## 🚀 What's Next?

After installation:

1. **Read the Guide**: `clineflow/WORKING_WITH_CLINE.md`
2. **Create Your First Journal**: `docs/journals/your-feature.md`
3. **Start Building**: Tell Cline what you want
4. **Commit Intelligently**: Just say "please commit"

**Happy Building! 🎉**

---

Made with ❤️ for developers working with AI assistants
