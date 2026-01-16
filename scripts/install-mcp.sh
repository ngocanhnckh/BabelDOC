#!/bin/bash
#
# BabelDOC MCP Server Installer for Claude Code
# This script installs and configures the BabelDOC MCP server for use with Claude Code.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Header
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  BabelDOC MCP Server Installer${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Get the directory where BabelDOC is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BABELDOC_DIR="$(dirname "$SCRIPT_DIR")"

# Verify we're in the right directory
if [[ ! -f "$BABELDOC_DIR/pyproject.toml" ]]; then
    print_error "Could not find BabelDOC installation."
    print_error "Please run this script from the BabelDOC directory."
    exit 1
fi

print_info "BabelDOC directory: $BABELDOC_DIR"

# Check for uv
if ! command -v uv &> /dev/null; then
    print_warning "uv is not installed. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    print_success "uv installed successfully"
fi

# Check for Claude Code
if ! command -v claude &> /dev/null; then
    print_error "Claude Code CLI is not installed."
    print_error "Please install Claude Code first: https://docs.anthropic.com/en/docs/claude-code"
    exit 1
fi

print_success "Claude Code CLI found"

# Install BabelDOC dependencies
print_info "Installing BabelDOC dependencies..."
cd "$BABELDOC_DIR"
uv sync --quiet
print_success "Dependencies installed"

# Ask for translation service
echo ""
echo -e "${YELLOW}Which translation service would you like to use?${NC}"
echo "  1) OpenRouter (recommended - supports many models)"
echo "  2) OpenAI"
echo "  3) Both"
echo ""
read -p "Enter your choice [1-3] (default: 1): " SERVICE_CHOICE
SERVICE_CHOICE=${SERVICE_CHOICE:-1}

OPENROUTER_KEY=""
OPENAI_KEY=""
OPENROUTER_MODEL=""
OPENAI_MODEL=""

case $SERVICE_CHOICE in
    1)
        echo ""
        print_info "OpenRouter Configuration"
        echo -e "Get your API key from: ${BLUE}https://openrouter.ai/keys${NC}"
        echo ""
        read -p "Enter your OpenRouter API key: " OPENROUTER_KEY
        if [[ -z "$OPENROUTER_KEY" ]]; then
            print_error "OpenRouter API key is required"
            exit 1
        fi
        echo ""
        echo "Available models (examples):"
        echo "  - google/gemini-2.5-flash (default, fast & cheap)"
        echo "  - google/gemini-2.5-pro (better quality)"
        echo "  - anthropic/claude-3.5-sonnet"
        echo "  - openai/gpt-4o"
        echo ""
        read -p "Enter model name (press Enter for default): " OPENROUTER_MODEL
        OPENROUTER_MODEL=${OPENROUTER_MODEL:-google/gemini-2.5-flash}
        ;;
    2)
        echo ""
        print_info "OpenAI Configuration"
        echo -e "Get your API key from: ${BLUE}https://platform.openai.com/api-keys${NC}"
        echo ""
        read -p "Enter your OpenAI API key: " OPENAI_KEY
        if [[ -z "$OPENAI_KEY" ]]; then
            print_error "OpenAI API key is required"
            exit 1
        fi
        echo ""
        echo "Available models:"
        echo "  - gpt-4o-mini (default, fast & cheap)"
        echo "  - gpt-4o (better quality)"
        echo ""
        read -p "Enter model name (press Enter for default): " OPENAI_MODEL
        OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
        ;;
    3)
        echo ""
        print_info "OpenRouter Configuration"
        echo -e "Get your API key from: ${BLUE}https://openrouter.ai/keys${NC}"
        echo ""
        read -p "Enter your OpenRouter API key: " OPENROUTER_KEY
        if [[ -z "$OPENROUTER_KEY" ]]; then
            print_error "OpenRouter API key is required"
            exit 1
        fi
        read -p "Enter OpenRouter model (default: google/gemini-2.5-flash): " OPENROUTER_MODEL
        OPENROUTER_MODEL=${OPENROUTER_MODEL:-google/gemini-2.5-flash}

        echo ""
        print_info "OpenAI Configuration"
        echo -e "Get your API key from: ${BLUE}https://platform.openai.com/api-keys${NC}"
        echo ""
        read -p "Enter your OpenAI API key: " OPENAI_KEY
        if [[ -z "$OPENAI_KEY" ]]; then
            print_error "OpenAI API key is required"
            exit 1
        fi
        read -p "Enter OpenAI model (default: gpt-4o-mini): " OPENAI_MODEL
        OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Build the environment variables for claude mcp add
ENV_ARGS=""

if [[ -n "$OPENROUTER_KEY" ]]; then
    ENV_ARGS+="OPENROUTER_API_KEY=$OPENROUTER_KEY "
    if [[ -n "$OPENROUTER_MODEL" ]]; then
        ENV_ARGS+="OPENROUTER_MODEL=$OPENROUTER_MODEL "
    fi
fi

if [[ -n "$OPENAI_KEY" ]]; then
    ENV_ARGS+="OPENAI_API_KEY=$OPENAI_KEY "
    if [[ -n "$OPENAI_MODEL" ]]; then
        ENV_ARGS+="OPENAI_MODEL=$OPENAI_MODEL "
    fi
fi

# Add MCP server to Claude Code
echo ""
print_info "Adding BabelDOC MCP server to Claude Code..."

# Build the claude mcp add command with environment variables
CMD="claude mcp add babeldoc --scope user"

# Add environment variables one by one
if [[ -n "$OPENROUTER_KEY" ]]; then
    CMD+=" -e OPENROUTER_API_KEY=$OPENROUTER_KEY"
fi
if [[ -n "$OPENROUTER_MODEL" ]]; then
    CMD+=" -e OPENROUTER_MODEL=$OPENROUTER_MODEL"
fi
if [[ -n "$OPENAI_KEY" ]]; then
    CMD+=" -e OPENAI_API_KEY=$OPENAI_KEY"
fi
if [[ -n "$OPENAI_MODEL" ]]; then
    CMD+=" -e OPENAI_MODEL=$OPENAI_MODEL"
fi

CMD+=" -- uv run --directory $BABELDOC_DIR babeldoc-mcp"

# Execute the command
eval $CMD

if [[ $? -eq 0 ]]; then
    print_success "BabelDOC MCP server added to Claude Code!"
else
    print_error "Failed to add MCP server."
    print_info "You can try adding it manually with:"
    echo ""
    echo "  claude mcp add babeldoc \\"
    echo "    -e OPENROUTER_API_KEY=your_key \\"
    echo "    -- uv run --directory $BABELDOC_DIR babeldoc-mcp"
    echo ""
    exit 1
fi

# Verify installation
echo ""
print_info "Verifying installation..."
sleep 1

if claude mcp list 2>/dev/null | grep -q "babeldoc"; then
    print_success "BabelDOC MCP server is now available!"
else
    print_warning "Could not verify installation. You may need to restart Claude Code."
fi

# Print usage instructions
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo "  In Claude Code, you can now use the BabelDOC translation tools:"
echo ""
echo "  1. Translate a PDF:"
echo -e "     ${BLUE}\"Translate /path/to/document.pdf to Vietnamese\"${NC}"
echo ""
echo "  2. Check translation service status:"
echo -e "     ${BLUE}\"Check BabelDOC translation status\"${NC}"
echo ""
echo -e "${YELLOW}Supported languages:${NC}"
echo "  en (English), zh (Chinese), vi (Vietnamese), ja (Japanese),"
echo "  ko (Korean), es (Spanish), fr (French), de (German),"
echo "  pt (Portuguese), ru (Russian), ar (Arabic), th (Thai), id (Indonesian)"
echo ""
echo -e "${YELLOW}To uninstall:${NC}"
echo -e "  ${BLUE}claude mcp remove babeldoc${NC}"
echo ""
print_info "If you encounter any issues, please restart Claude Code."
echo ""
