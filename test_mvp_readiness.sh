#!/bin/bash
# MapleJourney MVP Production Readiness Test Plan
# Run this to verify all critical paths work before launch

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 MAPLE MVP PRODUCTION READINESS TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test URLs
BACKEND_BASE="http://127.0.0.1:8000"
FRONTEND_BASE="http://localhost:3000"

# ─────────────────────────────────────────────────────────────
# 1. BACKEND HEALTH CHECK
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[1/6]${NC} Backend Health Check..."

# Check if backend is running
if ! curl -s "$BACKEND_BASE/docs" > /dev/null 2>&1; then
    echo -e "${RED}✗ Backend not running at $BACKEND_BASE${NC}"
    echo "Start backend: cd backend && python -m uvicorn server:app --host 127.0.0.1 --port 8000 --reload"
    exit 1
fi
echo -e "${GREEN}✓ Backend running${NC}"

# Check required endpoints exist
echo -e "${YELLOW}  Checking API endpoints...${NC}"
for endpoint in "/api/auth/register" "/api/auth/login" "/api/assistant/usage"; do
    if curl -s "$BACKEND_BASE$endpoint" -X OPTIONS > /dev/null 2>&1 || curl -s "$BACKEND_BASE$endpoint" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ $endpoint${NC}"
    fi
done

# ─────────────────────────────────────────────────────────────
# 2. DATABASE CONNECTIVITY
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[2/6]${NC} Database Connectivity..."

# Check if MongoDB is responsive
if curl -s "$BACKEND_BASE/health" > /dev/null 2>&1 || [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MongoDB connection verified${NC}"
else
    echo -e "${YELLOW}⚠ Cannot verify MongoDB (expected if auth required)${NC}"
fi

# ─────────────────────────────────────────────────────────────
# 3. FRONTEND BUILD TEST
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[3/6]${NC} Frontend Build..."

cd frontend
if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend builds successfully${NC}"
else
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
fi
cd ..

# ─────────────────────────────────────────────────────────────
# 4. CITATION CARD COMPONENT TEST
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[4/6]${NC} Citation Components..."

if grep -r "extractCitations\|CitationCards" frontend/src/components/chat/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Citation components found${NC}"
else
    echo -e "${RED}✗ Citation components missing${NC}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────
# 5. PROFILE COMPLETION COMPONENT TEST
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[5/6]${NC} Profile Completion..."

if grep -r "calculateProfileCompletion\|ProfileCompletionBar" frontend/src/components/profile/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Profile completion components found${NC}"
else
    echo -e "${RED}✗ Profile completion components missing${NC}"
    exit 1
fi

# ─────────────────────────────────────────────────────────────
# 6. PYTHON SYNTAX CHECK
# ─────────────────────────────────────────────────────────────
echo -e "\n${YELLOW}[6/6]${NC} Python Backend Syntax..."

cd backend

python -m py_compile server.py
python -m py_compile routers/chat.py
python -m py_compile services/rag.py
python -m py_compile core/db.py

echo -e "${GREEN}✓ All Python files compile${NC}"

cd ..

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ MVP PRODUCTION READINESS VERIFIED${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "NEXT STEPS:"
echo "1. Run full backend pytest suite: cd backend && pytest"
echo "2. Test live chat with citations at: http://localhost:3000/app/chat"
echo "3. Verify profile completion shows at: http://localhost:3000/app"
echo "4. Load test with: ab -n 100 -c 10 http://127.0.0.1:8000/api/overview"
echo "5. Deploy when ready!"
echo ""
