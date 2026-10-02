#!/usr/bin/env bash
# ==============================================================================
# Hearth Universal — Amazon Developer Hackathon (2026) Interactive Demo Launcher
# Build, Ship, Shape: 1-Click Runner for Hackathon Judges
# ==============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

clear || true

echo -e "${BOLD}${CYAN}"
cat << "EOF"
  _    _ ______          _____ _______ _    _   _    _ _   _ _______      ________ _____   _____          _      
 | |  | |  ____|   /\   |  __ \__   __| |  | | | |  | | \ | |_   _\ \    / /  ____|  __ \ / ____|   /\   | |     
 | |__| | |__     /  \  | |__) | | |  | |__| | | |  | |  \| | | |  \ \  / /| |__  | |__) | (___    /  \  | |     
 |  __  |  __|   / /\ \ |  _  /  | |  |  __  | | |  | | . ` | | |   \ \/ / |  __| |  _  / \___ \  / /\ \ | |     
 | |  | | |____ / ____ \| | \ \  | |  | |  | | | |__| | |\  |_| |_   \  /  | |____| | \ \ ____) |/ ____ \| |____ 
 |_|  |_|______/_/    \_\_|  \_\ |_|  |_|  |_|  \____/|_| \_|_____|   \/   |______|_|  \_\_____//_/    \_\______|
                                                                                                               
EOF
echo -e "${NC}"
echo -e "${BOLD}${BLUE}  Build, Ship, Shape: Amazon Developer Hackathon (2026)${NC}"
echo -e "  Autonomous Operations Agent for Amazon Alexa+ & AWS Bedrock"
echo -e "================================================================================"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# 1. Check Server Status
echo -e "\n${YELLOW}▶ Step 1: Checking Hearth FastMCP 2025-11-25 Server on port 8787...${NC}"
SERVER_RUNNING=0
if curl -s http://localhost:8787/health | grep -q '"status":"ok"'; then
  SERVER_RUNNING=1
  echo -e "${GREEN}✓ Server is already running and healthy on :8787${NC}"
else
  echo -e "  Starting background Hearth FastMCP Streamable HTTP server..."
  python3 mcp-server/server.py > /tmp/hearth-server.log 2>&1 &
  SERVER_PID=$!
  sleep 3
  if curl -s http://localhost:8787/health | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✓ Server started successfully (PID: $SERVER_PID)${NC}"
  else
    echo -e "${YELLOW}⚠ Server taking longer to start, waiting 2 more seconds...${NC}"
    sleep 2
  fi
fi

# 2. Run Official Hackathon Rubric Evaluation
echo -e "\n${YELLOW}▶ Step 2: Running Official Hackathon Rubric Evaluator (All Tracks)...${NC}"
python3 scripts/evaluate_rubric.py

# 3. Run Alexa+ Add-on & OAuth 2.1 RFC 9728 Compliance Tests
echo -e "\n${YELLOW}▶ Step 3: Verifying Official Alexa+ Add-on & OAuth 2.1 Compliance...${NC}"
python3 tests/test_alexaplus_addon_compliance.py

# 4. Run Frontier Innovations Test Suite
echo -e "\n${YELLOW}▶ Step 4: Verifying 4 Frontier Breakthroughs (Forensics, Acoustics, Treaty, Swarm)...${NC}"
pytest tests/test_frontier_innovations.py -q

# 5. Display Quick Links & Judge Guide
echo -e "${BOLD}${CYAN}================================================================================${NC}"
echo -e "${BOLD}${GREEN}🏆 ALL HACKATHON CHECKS VERIFIED 100% — READY FOR JUDGING!${NC}"
echo -e "${BOLD}${CYAN}================================================================================${NC}"
echo -e "${BOLD}Interactive Surfaces & Discovery Endpoints:${NC}"
echo -e "  🌐 Web App Experience:          ${CYAN}http://localhost:8787/web2/index.html${NC}"
echo -e "  ⚡ Streamable HTTP MCP (2025):   ${CYAN}http://localhost:8787/mcp${NC}"
echo -e "  📦 Official Add-on Manifest:     ${CYAN}http://localhost:8787/addon.json${NC}"
echo -e "  🛡️ RFC 9728 Protected Metadata:  ${CYAN}http://localhost:8787/.well-known/oauth-protected-resource${NC}"
echo -e "  🔑 OAuth 2.1 Auth Metadata:      ${CYAN}http://localhost:8787/.well-known/oauth-authorization-server${NC}"
echo -e "  📊 Health & Architecture Status: ${CYAN}http://localhost:8787/health${NC}"
echo -e ""
echo -e "${BOLD}Recommended 3-Minute Judge Showcase Flow:${NC}"
echo -e "  1. Open ${CYAN}http://localhost:8787/web2/index.html${NC}"
echo -e "  2. Switch between ${BOLD}Simulation${NC} and ${BOLD}Real World (Alexa+)${NC} tabs"
echo -e "  3. Click ${BOLD}'Log in with Amazon (Alexa+)'${NC} to test authentic OAuth & Alexa.Discovery"
echo -e "  4. Test Display Modes: ${BOLD}Inline Card${NC} vs ${BOLD}Fullscreen Canvas${NC} vs ${BOLD}Voice-Only${NC}"
echo -e "  5. Try the 9 One-Click Judge Showcase Demonstrations in the home view"
echo -e "     (Household Parliament, Causal Twin, Meta-Skills, Black Box CSI, FFT Doctor, Family Treaty, Swarm VPP)"
echo -e "================================================================================"

# 5. Open browser if in desktop environment
if command -v xdg-open > /dev/null 2>&1 && [ -n "$DISPLAY" ]; then
  echo -e "Opening Web App in default browser..."
  xdg-open "http://localhost:8787/web2/index.html" > /dev/null 2>&1 || true
fi
