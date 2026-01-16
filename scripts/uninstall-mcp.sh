#!/bin/bash
#
# BabelDOC MCP Server Uninstaller for Claude Code
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo ""
echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}  BabelDOC MCP Server Uninstaller${NC}"
echo -e "${YELLOW}======================================${NC}"
echo ""

# Check for Claude Code
if ! command -v claude &> /dev/null; then
    print_error "Claude Code CLI is not installed."
    exit 1
fi

print_info "Removing BabelDOC MCP server from Claude Code..."

claude mcp remove babeldoc 2>/dev/null

if [[ $? -eq 0 ]]; then
    print_success "BabelDOC MCP server removed successfully!"
else
    print_error "Failed to remove MCP server (it may not have been installed)"
fi

echo ""
print_info "You may need to restart Claude Code for changes to take effect."
echo ""
