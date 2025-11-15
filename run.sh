#!/bin/bash

# Startup script for MCP File Server

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=== MCP File Server ===${NC}"
echo -e "${YELLOW}Secure web content fetching (NO JavaScript execution)${NC}"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error creating virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Checking dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo -e "${RED}Error installing dependencies${NC}"
    exit 1
fi

# Create cache directory
mkdir -p .fetch_cache

echo -e "${GREEN}File Server started!${NC}"
echo -e "${YELLOW}Cache directory: ${SCRIPT_DIR}/.fetch_cache${NC}"
echo -e "${YELLOW}Security features: Path traversal protection, prompt injection detection, cookie handling${NC}"
echo ""

# Start the server
python3 main.py "$@"