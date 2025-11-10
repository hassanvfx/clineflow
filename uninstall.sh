#!/bin/bash
# ClineFlow Uninstaller
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

# Function to show what will be removed
show_removal_list() {
    echo -e "${YELLOW}The following will be removed:${NC}"
    echo ""
    
    [ -f .clinerules ] && echo "  • .clinerules"
    [ -d clineflow ] && echo "  • clineflow/ (including any reference symlinks)"
    [ -f setup-refs.sh ] && echo "  • setup-refs.sh"
    [ -f .clineflow.example ] && echo "  • .clineflow.example"
    [ -f .clineflow.local ] && echo "  • .clineflow.local"
    
    echo ""
    echo -e "${GREEN}The following will be PRESERVED:${NC}"
    echo "  • docs/journals/ (your task journals are safe)"
    echo ""
}

# Function to clean reference symlinks
clean_refs() {
    if [ -f setup-refs.sh ]; then
        print_info "Cleaning reference symlinks..."
        if bash setup-refs.sh --clean 2>/dev/null; then
            print_success "Reference symlinks cleaned"
        else
            print_warning "Could not clean reference symlinks (continuing anyway)"
        fi
    fi
}

# Function to remove files
remove_files() {
    local removed_count=0
    
    print_info "Removing ClineFlow files..."
    echo ""
    
    # Remove .clinerules
    if [ -f .clinerules ]; then
        rm -f .clinerules
        print_success "Removed .clinerules"
        removed_count=$((removed_count + 1))
    fi
    
    # Remove clineflow directory
    if [ -d clineflow ]; then
        rm -rf clineflow
        print_success "Removed clineflow/"
        removed_count=$((removed_count + 1))
    fi
    
    # Remove setup-refs.sh
    if [ -f setup-refs.sh ]; then
        rm -f setup-refs.sh
        print_success "Removed setup-refs.sh"
        removed_count=$((removed_count + 1))
    fi
    
    # Remove .clineflow.example
    if [ -f .clineflow.example ]; then
        rm -f .clineflow.example
        print_success "Removed .clineflow.example"
        removed_count=$((removed_count + 1))
    fi
    
    # Remove .clineflow.local if exists
    if [ -f .clineflow.local ]; then
        rm -f .clineflow.local
        print_success "Removed .clineflow.local"
        removed_count=$((removed_count + 1))
    fi
    
    echo ""
    return $removed_count
}

# Function to show help
show_help() {
    echo "ClineFlow Uninstaller"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --dry-run      Preview what would be removed without removing"
    echo "  --yes, -y      Skip confirmation prompt"
    echo "  --version      Show version"
    echo "  --help, -h     Show this help message"
    echo ""
    exit 0
}

# Parse command line arguments
DRY_RUN=false
SKIP_CONFIRM=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --yes|-y)
            SKIP_CONFIRM=true
            shift
            ;;
        --version)
            echo "ClineFlow Uninstaller v${VERSION}"
            exit 0
            ;;
        --help|-h)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main uninstall flow
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "   ClineFlow Uninstaller v${VERSION}"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Show what will be removed
show_removal_list

# Dry run mode
if [ "$DRY_RUN" = true ]; then
    print_info "DRY RUN MODE - No files will be removed"
    echo ""
    exit 0
fi

# Check if anything to remove
if [ ! -f .clinerules ] && [ ! -d clineflow ] && [ ! -f setup-refs.sh ] && [ ! -f .clineflow.example ] && [ ! -f .clineflow.local ]; then
    print_warning "No ClineFlow files found to remove"
    exit 0
fi

# Confirmation prompt
if [ "$SKIP_CONFIRM" = false ]; then
    echo -e "${YELLOW}⚠ Are you sure you want to remove ClineFlow?${NC}"
    read -p "Type 'yes' to confirm: " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Uninstall cancelled"
        exit 0
    fi
fi

# Clean reference symlinks first
clean_refs

echo ""

# Remove files
remove_files
removed_count=$?

# Success message
echo ""
echo "═══════════════════════════════════════════════════════════"
if [ $removed_count -gt 0 ]; then
    echo -e "${GREEN}✓ Uninstall complete! Removed $removed_count item(s)${NC}"
else
    echo -e "${YELLOW}⚠ No files were removed${NC}"
fi
echo "═══════════════════════════════════════════════════════════"
echo ""

# Reminder about journals
if [ -d docs/journals ]; then
    echo -e "${BLUE}📚 Note: Your journals are preserved in docs/journals/${NC}"
    echo -e "${BLUE}   Remove manually if desired:${NC} rm -rf docs/journals/"
    echo ""
fi

print_success "ClineFlow has been uninstalled"
echo ""
