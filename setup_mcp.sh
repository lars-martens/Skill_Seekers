#!/bin/bash
# Skill Seeker MCP Server - Quick Setup Script
# This script automates the MCP server setup for Claude Code using uv

set -e  # Exit on error

echo "=================================================="
echo "Skill Seeker MCP Server - Quick Setup (uv)"
echo "=================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check uv installation
echo "Step 1: Checking uv installation..."
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} uv not found"
    echo "uv is a fast Python package installer and resolver"
    read -p "Install uv now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh || {
            echo -e "${RED}❌ Failed to install uv${NC}"
            echo "Please install uv manually: https://github.com/astral-sh/uv"
            exit 1
        }
        # Source the shell config to get uv in PATH
        export PATH="$HOME/.cargo/bin:$PATH"
        if ! command -v uv &> /dev/null; then
            echo -e "${RED}❌ uv installation succeeded but not in PATH${NC}"
            echo "Please restart your shell or run: export PATH=\"\$HOME/.cargo/bin:\$PATH\""
            exit 1
        fi
    else
        echo -e "${RED}❌ uv is required for this setup${NC}"
        echo "Install manually: https://github.com/astral-sh/uv"
        exit 1
    fi
fi
echo -e "${GREEN}✓${NC} uv found"
echo ""

# Step 2: Check Python version
echo "Step 2: Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"
echo ""

# Step 3: Get repository path
REPO_PATH=$(pwd)
echo "Step 3: Repository location"
echo "Path: $REPO_PATH"
echo ""

# Step 4: Create virtual environment
echo "Step 4: Creating virtual environment with uv..."
if [ -d ".venv" ]; then
    echo -e "${YELLOW}⚠${NC} .venv already exists"
    read -p "Recreate virtual environment? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing .venv..."
        rm -rf .venv
        echo "Creating new virtual environment..."
        uv venv || {
            echo -e "${RED}❌ Failed to create virtual environment${NC}"
            exit 1
        }
        echo -e "${GREEN}✓${NC} Virtual environment created"
    else
        echo "Using existing virtual environment"
    fi
else
    echo "Creating virtual environment..."
    uv venv || {
        echo -e "${RED}❌ Failed to create virtual environment${NC}"
        exit 1
    }
    echo -e "${GREEN}✓${NC} Virtual environment created at .venv"
fi
echo ""

# Set paths for venv Python
VENV_PYTHON="$REPO_PATH/.venv/bin/python3"

# Step 5: Install dependencies
echo "Step 5: Installing Python dependencies..."
echo "This will install: mcp, requests, beautifulsoup4, and all project dependencies"
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing dependencies with uv..."
    source .venv/bin/activate
    # Use root requirements.txt if it exists (v2.0.0), otherwise fallback to skill_seeker_mcp/requirements.txt
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt || {
            echo -e "${RED}❌ Failed to install dependencies${NC}"
            exit 1
        }
    else
        uv pip install -r skill_seeker_mcp/requirements.txt || {
            echo -e "${RED}❌ Failed to install dependencies${NC}"
            exit 1
        }
    fi
    echo -e "${GREEN}✓${NC} Dependencies installed successfully"
else
    echo "Skipping dependency installation"
fi
echo ""

# Step 6: Test MCP server
echo "Step 6: Testing MCP server..."
timeout 3 "$VENV_PYTHON" skill_seeker_mcp/server.py 2>/dev/null || {
    if [ $? -eq 124 ]; then
        echo -e "${GREEN}✓${NC} MCP server starts correctly (timeout expected)"
    else
        echo -e "${YELLOW}⚠${NC} MCP server test inconclusive, but may still work"
    fi
}
echo ""

# Step 7: Optional - Run tests
echo "Step 7: Run test suite? (optional)"
read -p "Run MCP tests to verify everything works? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing pytest with uv..."
    source .venv/bin/activate
    uv pip install pytest || {
        echo -e "${YELLOW}⚠${NC} Could not install pytest, skipping tests"
    }

    if [ -f ".venv/bin/pytest" ]; then
        echo "Running MCP server tests..."
        "$VENV_PYTHON" -m pytest tests/test_mcp_server.py -v --tb=short || {
            echo -e "${RED}❌ Some tests failed${NC}"
            echo "The server may still work, but please check the errors above"
        }
    fi
else
    echo "Skipping tests"
fi
echo ""

# Step 8: Configure Claude Code
echo "Step 8: Configure Claude Code"
echo "=================================================="
echo ""
echo "You need to add this configuration to Claude Code:"
echo ""
echo -e "${YELLOW}Configuration file:${NC} ~/.config/claude-code/mcp.json"
echo ""
echo "Add this JSON configuration (paths are auto-detected for YOUR system):"
echo ""
echo -e "${GREEN}{"
echo "  \"mcpServers\": {"
echo "    \"skill-seeker\": {"
echo "      \"command\": \"$VENV_PYTHON\","
echo "      \"args\": ["
echo "        \"$REPO_PATH/skill_seeker_mcp/server.py\""
echo "      ],"
echo "      \"cwd\": \"$REPO_PATH\""
echo "    }"
echo "  }"
echo -e "}${NC}"
echo ""
echo -e "${YELLOW}Note:${NC} The paths above are YOUR actual paths (not placeholders!)"
echo ""

# Ask if user wants auto-configure
echo ""
read -p "Auto-configure Claude Code now? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if config already exists
    if [ -f ~/.config/claude-code/mcp.json ]; then
        echo -e "${YELLOW}⚠ Warning: ~/.config/claude-code/mcp.json already exists${NC}"
        echo "Current contents:"
        cat ~/.config/claude-code/mcp.json
        echo ""
        read -p "Overwrite? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Skipping auto-configuration"
            echo "Please manually add the skill-seeker server to your config"
            exit 0
        fi
    fi

    # Create config directory
    mkdir -p ~/.config/claude-code

    # Write configuration with actual expanded path
    cat > ~/.config/claude-code/mcp.json << EOF
{
  "mcpServers": {
    "skill-seeker": {
      "command": "$VENV_PYTHON",
      "args": [
        "$REPO_PATH/skill_seeker_mcp/server.py"
      ],
      "cwd": "$REPO_PATH"
    }
  }
}
EOF

    echo -e "${GREEN}✓${NC} Configuration written to ~/.config/claude-code/mcp.json"
    echo ""
    echo "Configuration contents:"
    cat ~/.config/claude-code/mcp.json
    echo ""

    # Verify the path exists
    if [ -f "$REPO_PATH/skill_seeker_mcp/server.py" ]; then
        echo -e "${GREEN}✓${NC} Verified: MCP server file exists at $REPO_PATH/skill_seeker_mcp/server.py"
    else
        echo -e "${RED}❌ Warning: MCP server not found at $REPO_PATH/skill_seeker_mcp/server.py${NC}"
        echo "Please check the path!"
    fi
else
    echo "Skipping auto-configuration"
    echo "Please manually add the skill-seeker configuration to ~/.config/claude-code/mcp.json"
fi
echo ""

# Step 9: Final instructions
echo "=================================================="
echo "Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. ${YELLOW}Restart Claude Code${NC} (quit and reopen, don't just close window)"
echo "  2. In Claude Code, test with: ${GREEN}\"List all available configs\"${NC}"
echo "  3. You should see 9 Skill Seeker tools available"
echo ""
echo "Available MCP Tools:"
echo "  • list_configs      - List all available preset configurations"
echo "  • generate_config   - Generate new config files"
echo "  • validate_config   - Validate config file structure"
echo "  • estimate_pages    - Estimate page count before scraping"
echo "  • scrape_docs       - Scrape and build a skill"
echo "  • package_skill     - Package skill into .zip file"
echo "  • upload_skill      - Upload .zip to Claude"
echo "  • split_config      - Split large documentation configs"
echo "  • generate_router   - Generate router/hub skills"
echo ""
echo "Example commands to try in Claude Code:"
echo "  • ${GREEN}List all available configs${NC}"
echo "  • ${GREEN}Estimate how many pages the React config will scrape${NC}"
echo "  • ${GREEN}Generate a config for the Django documentation${NC}"
echo ""
echo "Documentation:"
echo "  • MCP Setup Guide: ${YELLOW}docs/MCP_SETUP.md${NC}"
echo "  • Full docs: ${YELLOW}README.md${NC}"
echo ""
echo "Virtual Environment:"
echo "  • Location: ${YELLOW}$REPO_PATH/.venv${NC}"
echo "  • Python: ${YELLOW}$VENV_PYTHON${NC}"
echo "  • Activate: ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo "Troubleshooting:"
echo "  • Check logs: ~/Library/Logs/Claude Code/ (macOS)"
echo "  • Test server: $VENV_PYTHON skill_seeker_mcp/server.py"
echo "  • Run tests: $VENV_PYTHON -m pytest tests/test_mcp_server.py -v"
echo ""
echo "Happy skill creating! 🚀"
