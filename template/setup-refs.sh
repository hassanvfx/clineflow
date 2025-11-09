#!/bin/bash
# ClineFlow Reference System Setup Script
# Creates symlinks to external repositories for Cline exploration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration file
CONFIG_FILE=".clineflow.local"
EXAMPLE_CONFIG=".clineflow.example"
REFS_DIR="clineflow"

# Parse command line arguments
CLEAN_MODE=false

show_help() {
    echo "ClineFlow Reference System Setup"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --clean    Remove all reference symlinks"
    echo "  --help     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Create symlinks from .clineflow.local"
    echo "  $0 --clean      # Remove all symlinks"
    echo ""
    exit 0
}

clean_symlinks() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}   Cleaning Reference Symlinks${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    
    if [ ! -d "$REFS_DIR" ]; then
        echo -e "${YELLOW}⚠ No $REFS_DIR directory found${NC}"
        exit 0
    fi
    
    REMOVED_COUNT=0
    
    # Find and remove symlinks
    for link in "$REFS_DIR"/*; do
        if [ -L "$link" ]; then
            rm "$link"
            echo -e "${GREEN}✓ Removed: $(basename "$link")${NC}"
            REMOVED_COUNT=$((REMOVED_COUNT + 1))
        fi
    done
    
    echo ""
    if [ $REMOVED_COUNT -gt 0 ]; then
        echo -e "${GREEN}✓ Removed $REMOVED_COUNT symlink(s)${NC}"
    else
        echo -e "${YELLOW}⚠ No symlinks found to remove${NC}"
    fi
    echo ""
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_MODE=true
            shift
            ;;
        --help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}✗ Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$CLEAN_MODE" = true ]; then
    clean_symlinks
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   ClineFlow Reference System Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠ Configuration file not found: $CONFIG_FILE${NC}"
    if [ -f "$EXAMPLE_CONFIG" ]; then
        echo -e "${BLUE}ℹ Creating from example...${NC}"
        cp "$EXAMPLE_CONFIG" "$CONFIG_FILE"
        echo -e "${GREEN}✓ Created $CONFIG_FILE${NC}"
        echo -e "${YELLOW}⚠ Please edit $CONFIG_FILE with your repository paths${NC}"
        echo -e "${BLUE}  Then run this script again.${NC}"
    else
        echo -e "${RED}✗ Example config not found: $EXAMPLE_CONFIG${NC}"
        echo -e "${BLUE}  Please create $CONFIG_FILE manually${NC}"
    fi
    exit 1
fi

# Source the configuration
echo -e "${BLUE}ℹ Loading configuration from $CONFIG_FILE...${NC}"
source "$CONFIG_FILE"

# Create refs directory if it doesn't exist
if [ ! -d "$REFS_DIR" ]; then
    echo -e "${BLUE}ℹ Creating directory: $REFS_DIR/${NC}"
    mkdir -p "$REFS_DIR"
fi

# Track success
SUCCESS_COUNT=0
TOTAL_COUNT=0

# Function to create symlink
create_symlink() {
    local var_name="$1"
    local link_name="$2"
    local target_path="${!var_name}"
    
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    
    if [ -z "$target_path" ]; then
        return # Skip if variable is not set
    fi
    
    echo -e "${BLUE}ℹ Processing: $link_name${NC}"
    
    # Check if target exists
    if [ ! -d "$target_path" ]; then
        echo -e "${YELLOW}  ⚠ Target not found: $target_path${NC}"
        echo -e "${YELLOW}    Skipping $link_name${NC}"
        return
    fi
    
    local link_path="$REFS_DIR/$link_name"
    
    # Remove existing symlink if it exists
    if [ -L "$link_path" ]; then
        echo -e "${BLUE}  ℹ Removing existing symlink${NC}"
        rm "$link_path"
    elif [ -e "$link_path" ]; then
        echo -e "${RED}  ✗ Path exists but is not a symlink: $link_path${NC}"
        echo -e "${RED}    Please remove it manually${NC}"
        return
    fi
    
    # Create symlink
    ln -sf "$target_path" "$link_path"
    echo -e "${GREEN}  ✓ Created symlink: $link_name → $target_path${NC}"
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
}

# Parse config file for *_PATH variables and create symlinks
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Creating symlinks...${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

while IFS='=' read -r var_name var_value; do
    # Skip comments and empty lines
    [[ "$var_name" =~ ^#.*$ ]] && continue
    [[ -z "$var_name" ]] && continue
    
    # Check if variable ends with _PATH
    if [[ "$var_name" =~ _PATH$ ]]; then
        # Remove _PATH suffix and convert to lowercase for link name
        link_name=$(echo "${var_name%_PATH}" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
        create_symlink "$var_name" "$link_name"
    fi
done < "$CONFIG_FILE"

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
if [ $SUCCESS_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ Setup complete! Created $SUCCESS_COUNT symlink(s)${NC}"
    echo ""
    echo -e "${BLUE}📚 You can now reference these repos in Cline:${NC}"
    echo -e "${BLUE}   Example: @clineflow/backend-api/README.md${NC}"
else
    echo -e "${YELLOW}⚠ No symlinks created${NC}"
    echo -e "${BLUE}ℹ Make sure $CONFIG_FILE has valid repository paths${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
