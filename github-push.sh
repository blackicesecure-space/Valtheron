#!/bin/bash

# Valtheron - GitHub Push Script
# Automated push to blackicesecure-space/Valtheron

set -e

echo "========================================"
echo "Valtheron - GitHub Push"
echo "Repository: blackicesecure-space/Valtheron"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d ".git" ]; then
    echo -e "${RED}Error: Must be run from Valtheron root directory${NC}"
    exit 1
fi

echo -e "${CYAN}Step 1: Configuring Git remote${NC}"

# Check if remote already exists
if git remote get-url origin &> /dev/null; then
    CURRENT_URL=$(git remote get-url origin)
    echo -e "${YELLOW}Remote 'origin' already exists: ${CURRENT_URL}${NC}"

    # Verify it's the correct repository
    if [[ "$CURRENT_URL" != *"blackicesecure-space/Valtheron"* ]]; then
        echo -e "${YELLOW}Updating remote URL to match Valtheron repository...${NC}"
        git remote set-url origin https://github.com/blackicesecure-space/Valtheron.git
        echo -e "${GREEN}✓ Remote updated${NC}"
    else
        echo -e "${GREEN}✓ Remote already correctly configured${NC}"
    fi
else
    echo -e "${GREEN}Adding remote 'origin'${NC}"
    git remote add origin https://github.com/blackicesecure-space/Valtheron.git
    echo -e "${GREEN}✓ Remote configured${NC}"
fi
echo ""

echo -e "${CYAN}Step 2: Determining branch to push${NC}"

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "Current branch: ${YELLOW}${CURRENT_BRANCH}${NC}"

# Validate branch name for claude/ branches
if [[ "$CURRENT_BRANCH" == claude/* ]]; then
    echo -e "${GREEN}✓ Branch follows claude/ naming convention${NC}"

    # Extract session ID (everything after 'claude/')
    SESSION_ID="${CURRENT_BRANCH#claude/}"
    if [ -z "$SESSION_ID" ]; then
        echo -e "${RED}Error: Branch name 'claude/' must include a session ID${NC}"
        exit 1
    fi

    echo -e "Session ID: ${CYAN}${SESSION_ID}${NC}"
else
    echo -e "${YELLOW}Warning: Branch does not start with 'claude/'${NC}"
    echo -e "${YELLOW}Note: Push may fail with 403 error if branch protection is enabled${NC}"
fi
echo ""

echo -e "${CYAN}Step 3: Verifying repository status${NC}"
git status
echo ""

echo -e "${CYAN}Step 4: Pushing to GitHub with retry logic${NC}"
echo -e "${YELLOW}Note: Will retry up to 4 times with exponential backoff on network failures${NC}"
echo ""

# Push with retry logic
MAX_RETRIES=4
RETRY_COUNT=0
PUSH_SUCCESS=false

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if [ $RETRY_COUNT -gt 0 ]; then
        WAIT_TIME=$((2 ** $RETRY_COUNT))
        echo -e "${YELLOW}Retry attempt ${RETRY_COUNT}/${MAX_RETRIES} after ${WAIT_TIME}s delay...${NC}"
        sleep $WAIT_TIME
    fi

    echo -e "${CYAN}Attempting push to origin ${CURRENT_BRANCH}...${NC}"

    # Attempt to push
    if git push -u origin "$CURRENT_BRANCH" 2>&1; then
        PUSH_SUCCESS=true
        break
    else
        PUSH_EXIT_CODE=$?
        echo -e "${RED}Push failed with exit code: ${PUSH_EXIT_CODE}${NC}"

        # Check if it's a network error (retry) or other error (exit)
        if [ $PUSH_EXIT_CODE -eq 128 ] || [ $PUSH_EXIT_CODE -eq 1 ]; then
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo -e "${YELLOW}Network error detected, will retry...${NC}"
            fi
        else
            echo -e "${RED}Non-network error detected, aborting retries${NC}"
            break
        fi
    fi
done

if [ "$PUSH_SUCCESS" = true ]; then
    echo ""
    echo -e "${GREEN}========================================"
    echo "✓ Successfully Pushed to GitHub!"
    echo "========================================"
    echo ""
    echo "Repository: https://github.com/blackicesecure-space/Valtheron"
    echo "Branch: ${CURRENT_BRANCH}"
    echo ""
    echo "View your changes:"
    echo "  https://github.com/blackicesecure-space/Valtheron/tree/${CURRENT_BRANCH}"
    echo ""
    echo "Next steps:"
    echo "  1. Visit the repository on GitHub"
    echo "  2. Create a Pull Request if ready"
    echo "  3. Review changes in the GitHub UI"
    echo "  4. Check CI/CD pipeline status (if configured)"
    echo -e "${NC}"
else
    echo ""
    echo -e "${RED}========================================"
    echo "✗ Push Failed After ${RETRY_COUNT} Attempts"
    echo "========================================"
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. Branch name validation failed (403 error)"
    echo "   ✓ Branch must start with 'claude/' and include session ID"
    echo "   ✓ Current branch: ${CURRENT_BRANCH}"
    if [[ "$CURRENT_BRANCH" != claude/* ]]; then
        echo -e "   ${RED}✗ Branch does not follow required naming convention${NC}"
    fi
    echo ""
    echo "2. Repository doesn't exist or access denied"
    echo "   ✓ Verify repository exists: https://github.com/blackicesecure-space/Valtheron"
    echo "   ✓ Check you have push access to the repository"
    echo ""
    echo "3. Authentication failed"
    echo "   ✓ Use a Personal Access Token instead of password"
    echo "   ✓ Generate at: https://github.com/settings/tokens"
    echo "   ✓ Permissions needed: repo (full control)"
    echo ""
    echo "4. Network connectivity issues"
    echo "   ✓ Check internet connection"
    echo "   ✓ Try again later if GitHub is experiencing issues"
    echo ""
    echo "5. Branch protection rules"
    echo "   ✓ Check if branch requires pull request reviews"
    echo "   ✓ Verify you meet all protection requirements"
    echo ""
    echo "Debug commands:"
    echo "  git remote -v          # Verify remote URL"
    echo "  git branch --show-current  # Check current branch"
    echo "  git status             # Check repository status"
    echo "  git fetch origin       # Test connectivity"
    echo -e "${NC}"
    exit 1
fi
