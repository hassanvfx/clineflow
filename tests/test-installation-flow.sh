#!/bin/bash
# ClineFlow Installation Test Suite
# Tests complete installation flow and the absence of retired reference artifacts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPOSITORY_ROOT=$(cd "$(dirname "$0")/.." && pwd)
INSTALL_SOURCE="${INSTALL_SOURCE:-$REPOSITORY_ROOT/install.sh}"
TEMPLATE_BASE_URL="${TEMPLATE_BASE_URL:-file://$REPOSITORY_ROOT/template}"
TEST_DIR=""
VERBOSE=false
NO_CLEANUP=false
FAILED=0
PASSED=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --no-cleanup)
            NO_CLEANUP=true
            shift
            ;;
        --help|-h)
            echo "ClineFlow Test Suite"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v     Show detailed output"
            echo "  --no-cleanup      Keep test environment after completion"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Helper function for verbose output
verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}    [VERBOSE] $1${NC}"
    fi
}

# Test result tracking
pass_test() {
    echo -e "${GREEN}  ✅ $1${NC}"
    PASSED=$((PASSED + 1))
}

fail_test() {
    echo -e "${RED}  ❌ $1${NC}"
    FAILED=$((FAILED + 1))
}

warn_test() {
    echo -e "${YELLOW}  ⚠️  $1${NC}"
}

# Cleanup function
cleanup() {
    if [ "$NO_CLEANUP" = true ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Test environment preserved at: $TEST_DIR${NC}"
        return
    fi
    
    if [ -n "$TEST_DIR" ] && [ -d "$TEST_DIR" ]; then
        verbose "Cleaning up test environment: $TEST_DIR"
        rm -rf "$TEST_DIR"
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Phase 1: Create test environment
create_test_environment() {
    echo ""
    echo -e "${BLUE}📦 Phase 1: Environment Setup${NC}"
    
    # Create unique test directory
    TEST_DIR=$(mktemp -d /tmp/clineflow-test-XXXXXX)
    verbose "Created test directory: $TEST_DIR"
    
    # Create test project directory
    mkdir -p "$TEST_DIR/test-project"
    cd "$TEST_DIR/test-project"
    git init > /dev/null 2>&1
    git config user.name "Test User" > /dev/null 2>&1
    git config user.email "test@example.com" > /dev/null 2>&1
    pass_test "Created test project directory"

    # Legacy journals must remain untouched when the native OKF workflow is installed.
    mkdir -p docs/journals
    echo "# Legacy journal" > docs/journals/legacy-task.md
    LEGACY_JOURNAL_HASH=$(shasum -a 256 docs/journals/legacy-task.md | awk '{print $1}')
    
}

# Phase 2: Run ClineFlow installation
run_installation() {
    echo ""
    echo -e "${BLUE}📥 Phase 2: ClineFlow Installation${NC}"
    
    cd "$TEST_DIR/test-project"
    
    # Copy the checked-out installer so CI verifies the current branch, not main.
    verbose "Copying install script from: $INSTALL_SOURCE"
    if ! cp "$INSTALL_SOURCE" install.sh; then
        fail_test "Failed to copy install script"
        return 1
    fi
    pass_test "Copied install script from current checkout"
    
    # Make executable
    chmod +x install.sh
    
    # Run installation (suppress output unless verbose)
    verbose "Running installation..."
    if [ "$VERBOSE" = true ]; then
        CLINEFLOW_BASE_URL="$TEMPLATE_BASE_URL" bash install.sh
    else
        CLINEFLOW_BASE_URL="$TEMPLATE_BASE_URL" bash install.sh > /dev/null 2>&1
    fi
    
    pass_test "Installation completed successfully"
    
    # Verify files were created
    if [ -f .clinerules ] && [ -f AGENTS.md ] && [ -d clineflow ] && [ -f clineflow/WORKING_WITH_CODEX.md ] && [ -f knowledge/index.md ] && [ -f knowledge/log.md ] && [ -f knowledge/journals/TASK_TEMPLATE.md ] && [ -f validate-okf ] && [ -x clineflow-doctor ]; then
        pass_test "All files created in correct locations"
    else
        fail_test "Missing expected files after installation"
        return 1
    fi

    if [ ! -e setup-refs.sh ] && [ ! -e .clineflow.example ] && [ ! -e clineflow/README.md ] && ! grep -qxF '.clineflow.local' .gitignore 2>/dev/null; then
        pass_test "Retired reference artifacts are not installed or configured"
    else
        fail_test "Retired reference artifacts were installed or configured"
        return 1
    fi

    if [ "$(shasum -a 256 docs/journals/legacy-task.md | awk '{print $1}')" = "$LEGACY_JOURNAL_HASH" ]; then
        pass_test "Legacy journals preserved unchanged"
    else
        fail_test "Legacy journal was modified during installation"
    fi

    if bash validate-okf > /dev/null 2>&1; then
        pass_test "Generated knowledge bundle passes OKF validation"
    else
        fail_test "Generated knowledge bundle did not pass OKF validation"
    fi

    if grep -q "ChatGPT Codex" AGENTS.md && grep -q "WORKING_WITH_CODEX.md" AGENTS.md; then
        pass_test "Generated AGENTS.md includes the Codex workflow"
    else
        fail_test "Generated AGENTS.md does not include the Codex workflow"
        return 1
    fi

    if bash clineflow-doctor > /dev/null 2>&1; then
        pass_test "ClineFlow doctor passes on the generated installation"
    else
        fail_test "ClineFlow doctor did not pass on the generated installation"
        return 1
    fi
}

# Phase 2b: Verify Codex compatibility and doctor failures
test_codex_integration() {
    echo ""
    echo -e "${BLUE}🤖 Phase 2b: Codex Integration${NC}"

    cd "$TEST_DIR/test-project"

    printf '%s\n' "# Existing user instructions" "Do not replace these rules." > AGENTS.md

    local agents_hash
    agents_hash=$(shasum -a 256 AGENTS.md | awk '{print $1}')
    if CLINEFLOW_BASE_URL="$TEMPLATE_BASE_URL" bash install.sh > /dev/null 2>&1 && [ "$agents_hash" = "$(shasum -a 256 AGENTS.md | awk '{print $1}')" ]; then
        pass_test "Existing AGENTS.md is preserved on reinstall"
    else
        fail_test "Existing AGENTS.md was changed on reinstall"
    fi

    local doctor_fixture="$TEST_DIR/doctor-fixture"
    mkdir -p "$doctor_fixture"
    git init "$doctor_fixture" > /dev/null 2>&1
    cp AGENTS.md clineflow-doctor validate-okf "$doctor_fixture/"
    cp -R knowledge "$doctor_fixture/knowledge"
    chmod +x "$doctor_fixture/clineflow-doctor" "$doctor_fixture/validate-okf"

    mkdir -p "$doctor_fixture/no-pyyaml"
    cat > "$doctor_fixture/no-pyyaml/python3" << 'EOF'
#!/bin/sh
exit 1
EOF
    chmod +x "$doctor_fixture/no-pyyaml/python3"
    if (cd "$doctor_fixture" && PATH="$doctor_fixture/no-pyyaml:$PATH" bash ./clineflow-doctor --strict) > "$doctor_fixture/strict.out" 2>&1 && grep -q "Strict validation skipped" "$doctor_fixture/strict.out"; then
        pass_test "Doctor warns but passes when optional PyYAML is unavailable"
    else
        fail_test "Doctor did not handle unavailable PyYAML as optional"
    fi

    rm "$doctor_fixture/AGENTS.md"
    if ! (cd "$doctor_fixture" && bash ./clineflow-doctor) > "$doctor_fixture/missing-agents.out" 2>&1 && grep -q "Missing shared Codex and agent instructions" "$doctor_fixture/missing-agents.out"; then
        pass_test "Doctor reports missing AGENTS.md"
    else
        fail_test "Doctor did not report missing AGENTS.md"
    fi

    cp AGENTS.md "$doctor_fixture/AGENTS.md"
    rm "$doctor_fixture/knowledge/log.md"
    if ! (cd "$doctor_fixture" && bash ./clineflow-doctor) > "$doctor_fixture/missing-log.out" 2>&1 && grep -q "Missing OKF bundle log" "$doctor_fixture/missing-log.out"; then
        pass_test "Doctor reports a missing required knowledge file"
    else
        fail_test "Doctor did not report a missing required knowledge file"
    fi
}

# Generate final report
generate_report() {
    local total=$((PASSED + FAILED))
    local duration=$SECONDS
    
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 All $PASSED tests passed!${NC}"
    else
        echo -e "${RED}❌ $FAILED test(s) failed, $PASSED passed${NC}"
    fi
    
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}📊 Test Summary:${NC}"
    echo -e "   Duration: ${duration} seconds"
    echo -e "   Tests: $PASSED passed, $FAILED failed"
    echo -e "   Environment: $TEST_DIR"
    
    if [ "$NO_CLEANUP" = false ]; then
        echo -e "   Cleaned up: ✅"
    else
        echo -e "   Cleaned up: ⚠️  Preserved for debugging"
    fi
    
    echo ""
    
    # Return appropriate exit code
    if [ $FAILED -eq 0 ]; then
        return 0
    else
        return 1
    fi
}

# Main execution
main() {
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🧪 ClineFlow Installation Test Suite${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
    
    # Track execution time
    SECONDS=0
    
    # Run test phases
    create_test_environment
    run_installation
    test_codex_integration
    
    # Generate report and exit with appropriate code
    generate_report
}

# Run main function
main
