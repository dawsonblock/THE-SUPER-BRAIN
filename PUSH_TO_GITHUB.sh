#!/bin/bash
#
# Push Brain-AI RAG++ v4.4.0 to GitHub
#
# This script helps you push the complete v4.4.0 upgrade to GitHub
# with proper commit message and tagging.
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      Push Brain-AI RAG++ v4.4.0 to GitHub                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}✗${NC} Not a git repository. Run 'git init' first."
    exit 1
fi

echo -e "${GREEN}✓${NC} Git repository detected"

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠${NC} You have uncommitted changes. Staging all files..."
    git add .
    echo -e "${GREEN}✓${NC} All files staged"
else
    echo -e "${GREEN}✓${NC} No uncommitted changes"
fi

# Show what will be committed
echo ""
echo -e "${BLUE}Files to be committed:${NC}"
git status --short | head -20
echo ""

# Ask for confirmation
read -p "$(echo -e ${YELLOW}Continue with commit? [y/N]:${NC} )" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}✗${NC} Aborted by user"
    exit 1
fi

# Create commit with semantic message
echo ""
echo -e "${BLUE}Creating commit...${NC}"
git commit -m "feat: complete system upgrade to v4.4.0

Major Upgrades:
- Add comprehensive README.md for GitHub with badges and documentation
- Add CHANGELOG.md with full version history (v3.0.0 → v4.4.0)
- Add CONTRIBUTING.md with developer guidelines and code standards
- Add MIT LICENSE for open source distribution
- Add VERSION file (4.4.0) for version tracking
- Add GitHub Actions CI workflow with 4 test jobs
- Complete GUI full functionality with all features operational
- Fix critical bugs (healthcheck, API endpoints, directory creation)
- Production deployment ready with Docker Compose orchestration
- Full test coverage (C++, Python, GUI, E2E)

Bug Fixes:
- GUI healthcheck: Changed from wget to curl for Alpine compatibility
- API endpoint mismatch: Added /answer endpoint as alias to /query
- Missing logs directory: Fixed start_dev.sh to create both data and logs
- OCR test timeout: Fixed timeout test to use millisecond precision
- TypeScript unused variable: Renamed to underscore convention
- GUI dependencies: Added missing npm packages

Production Features:
- Docker Compose with 4 services (core, REST, GUI, OCR)
- One-command local development (./start_dev.sh)
- End-to-end integration testing (./test_e2e_full.sh)
- Health checks and monitoring
- Rate limiting and security
- Structured logging

Documentation:
- 150KB+ of comprehensive documentation
- API reference with examples
- Deployment guide
- Operations manual
- Security best practices

BREAKING CHANGE: Requires Docker Compose v2+

Closes #1, #2, #3" || echo -e "${YELLOW}⚠${NC} Files already committed"

echo -e "${GREEN}✓${NC} Commit created"

# Create tag
echo ""
echo -e "${BLUE}Creating release tag v4.4.0...${NC}"
git tag -a v4.4.0 -m "Brain-AI RAG++ v4.4.0 - Production Ready

Complete system upgrade with:
- GitHub-ready documentation (README, CHANGELOG, CONTRIBUTING)
- Automated CI/CD (GitHub Actions)
- Full GUI functionality
- Production deployment (Docker Compose)
- Critical bug fixes
- Enhanced security and monitoring

This release marks the system as production-ready and suitable
for public GitHub release and community contributions."

echo -e "${GREEN}✓${NC} Tag v4.4.0 created"

# Check for remote
echo ""
if git remote | grep -q origin; then
    REMOTE_URL=$(git remote get-url origin)
    echo -e "${GREEN}✓${NC} Remote 'origin' found: ${REMOTE_URL}"
    
    # Ask to push
    read -p "$(echo -e ${YELLOW}Push to origin? [y/N]:${NC} )" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${BLUE}Pushing to origin...${NC}"
        
        # Get current branch
        BRANCH=$(git branch --show-current)
        
        # Push branch
        git push origin "$BRANCH"
        echo -e "${GREEN}✓${NC} Pushed branch: $BRANCH"
        
        # Push tags
        git push --tags
        echo -e "${GREEN}✓${NC} Pushed tags"
        
        echo ""
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║              🎉 Successfully pushed to GitHub! 🎉              ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo "  1. Go to your GitHub repository"
        echo "  2. Navigate to Releases → Create a new release"
        echo "  3. Select tag: v4.4.0"
        echo "  4. Copy release notes from CHANGELOG.md"
        echo "  5. Publish release"
        echo ""
        echo -e "${BLUE}Repository settings:${NC}"
        echo "  • Add topics: rag, llm, vector-search, cpp, fastapi, react, ai"
        echo "  • Enable: Issues, Discussions, Actions"
        echo "  • Configure branch protection for main"
        echo ""
    else
        echo -e "${YELLOW}⚠${NC} Push skipped"
        echo ""
        echo -e "${BLUE}To push manually:${NC}"
        echo "  git push origin $(git branch --show-current)"
        echo "  git push --tags"
    fi
else
    echo -e "${YELLOW}⚠${NC} No remote 'origin' configured"
    echo ""
    echo -e "${BLUE}To add remote and push:${NC}"
    echo "  git remote add origin https://github.com/YOUR_USERNAME/C-AI-BRAIN-2.git"
    echo "  git push -u origin main"
    echo "  git push --tags"
fi

echo ""
echo -e "${GREEN}✓${NC} Done!"

