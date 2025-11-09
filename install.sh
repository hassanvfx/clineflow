#!/bin/bash
# ClineFlow Installer
# https://github.com/hassanvfx/clineflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script version
VERSION="1.0.0"

# Base URL for raw files (GitHub)
BASE_URL="https://raw.githubusercontent.com/hassanvfx/clineflow/main/template"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to check requirements
check_requirements() {
    if ! command -v git >/dev/null 2>&1; then
        print_error "Git is not installed. Please install git first."
        exit 1
    fi
}

# Function to detect if in git repository
is_git_repo() {
    git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

# Function to download file
download_file() {
    local url=$1
    local dest=$2
    
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "$url" -o "$dest"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$url" -O "$dest"
    else
        print_error "Neither curl nor wget found. Please install one of them."
        exit 1
    fi
}

# Function to install workflow files
install_workflow() {
    print_info "Installing ClineFlow..."
    echo
    
    # Create directories
    print_info "Creating directory structure..."
    mkdir -p clineflow docs/journals
    print_success "Directories created"
    
    # Download template files
    print_info "Downloading workflow files..."
    
    # .clinerules
    if [ ! -f .clinerules ] || [ "$FORCE" = true ]; then
        download_file "${BASE_URL}/.clinerules" ".clinerules"
        print_success ".clinerules"
    else
        print_warning ".clinerules already exists (skipping, use --force to overwrite)"
    fi
    
    # clineflow files
    local clineflow_files=("JOURNAL_TEMPLATE.md" "PROCEDURES.md" "WORKING_WITH_CLINE.md" "README.md")
    for file in "${clineflow_files[@]}"; do
        if [ ! -f "clineflow/$file" ] || [ "$FORCE" = true ]; then
            download_file "${BASE_URL}/clineflow/${file}" "clineflow/$file"
            print_success "clineflow/$file"
        else
            print_warning "clineflow/$file already exists (skipping)"
        fi
    done
    
    # .gitignore for journals
    touch docs/journals/.gitkeep
    print_success "docs/journals/.gitkeep"
    
    # Reference system files
    if [ ! -f setup-refs.sh ] || [ "$FORCE" = true ]; then
        download_file "${BASE_URL}/setup-refs.sh" "setup-refs.sh"
        chmod +x setup-refs.sh
        print_success "setup-refs.sh"
    else
        print_warning "setup-refs.sh already exists (skipping)"
    fi
    
    if [ ! -f .clineflow.example ] || [ "$FORCE" = true ]; then
        download_file "${BASE_URL}/.clineflow.example" ".clineflow.example"
        print_success ".clineflow.example"
    else
        print_warning ".clineflow.example already exists (skipping)"
    fi
    
    echo
    print_success "Installation complete!"
    echo
}

# Function to show next steps
show_next_steps() {
    echo -e "${GREEN}🎉 Success!${NC} ClineFlow is installed."
    echo
    echo "📚 Next Steps:"
    echo "  1. Review and customize .clinerules for your project"
    echo "  2. Read clineflow/WORKING_WITH_CLINE.md for complete guide"
    echo "  3. Create your first journal: docs/journals/your-feature.md"
    echo "  4. (Optional) Set up reference system: ./setup-refs.sh --help"
    echo "  5. Start working with Cline in your IDE"
    echo "  6. Try the intelligent commit: just say 'please commit'"
    echo
    echo "📖 Documentation: clineflow/WORKING_WITH_CLINE.md"
    echo "🔗 Reference System: clineflow/README.md"
    echo "🐛 Issues: https://github.com/hassanvfx/clineflow/issues"
    echo
}

# Function to uninstall
uninstall_workflow() {
    print_warning "Uninstalling ClineFlow..."
    echo
    
    read -p "Are you sure you want to remove all workflow files? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Uninstall cancelled"
        exit 0
    fi
    
    rm -f .clinerules
    rm -rf clineflow
    rm -rf docs/journals
    
    print_success "Workflow files removed"
}

# Parse command line arguments
DRY_RUN=false
FORCE=false
UNINSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --uninstall)
            UNINSTALL=true
            shift
            ;;
        --version)
            echo "ClineFlow Installer v${VERSION}"
            exit 0
            ;;
        --help|-h)
            echo "ClineFlow Installer"
            echo
            echo "Usage: $0 [options]"
            echo
            echo "Options:"
            echo "  --dry-run      Show what would be installed without installing"
            echo "  --force        Overwrite existing files"
            echo "  --uninstall    Remove workflow files"
            echo "  --version      Show version"
            echo "  --help, -h     Show this help message"
            echo
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main installation flow
echo
echo "═══════════════════════════════════════════════════════════"
echo "   ClineFlow Installer v${VERSION}"
echo "═══════════════════════════════════════════════════════════"
echo

check_requirements

if [ "$UNINSTALL" = true ]; then
    uninstall_workflow
    exit 0
fi

if [ "$DRY_RUN" = true ]; then
    print_info "DRY RUN MODE - No files will be created"
    echo
    print_info "Would create:"
    echo "  .clinerules"
    echo "  clineflow/JOURNAL_TEMPLATE.md"
    echo "  clineflow/PROCEDURES.md"
    echo "  clineflow/WORKING_WITH_CLINE.md"
    echo "  clineflow/README.md"
    echo "  docs/journals/.gitkeep"
    echo "  setup-refs.sh"
    echo "  .clineflow.example"
    echo
    exit 0
fi

# Check if in git repo
if ! is_git_repo; then
    print_warning "Not in a git repository"
    read -p "Initialize git repository here? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git init
        print_success "Git repository initialized"
    else
        print_info "Continuing without git..."
    fi
fi

# Install workflow
install_workflow
show_next_steps
