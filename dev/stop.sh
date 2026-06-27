#!/bin/bash

# Colors for output
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   iTaxEasy Mobile APK Backend - Stop Script${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Ensure we are in script directory parent
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.." || exit 1

echo -e "${YELLOW}Stopping and removing docker containers...${NC}"
docker compose -f docker-compose.dev.yml down
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dev environment stopped successfully.${NC}"
else
    echo -e "${YELLOW}Could not clean up containers cleanly.${NC}"
fi
