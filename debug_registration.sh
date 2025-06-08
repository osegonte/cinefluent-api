#!/bin/bash

# Debug Registration Script
# This script will help identify the exact database error

echo "🔍 CineFluent Registration Debug Script"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="https://cinefluent-api-production-5082.up.railway.app"

echo -e "${BLUE}📊 Testing API health...${NC}"
HEALTH_RESPONSE=$(curl -s "${API_URL}/api/v1/health")
echo "Health check: ${HEALTH_RESPONSE}"
echo ""

echo -e "${BLUE}🧪 Testing registration with verbose output...${NC}"

# Generate unique email for testing
TIMESTAMP=$(date +%s)
TEST_EMAIL="debug-${TIMESTAMP}@example.com"

echo "Testing with email: ${TEST_EMAIL}"
echo ""

# Test registration with full response
echo -e "${YELLOW}Running registration test...${NC}"
RESPONSE=$(curl -v -X POST "${API_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"TestPass123!\",
    \"full_name\": \"Debug Test User\"
  }" 2>&1)

echo "Full response:"
echo "${RESPONSE}"
echo ""

echo -e "${BLUE}💡 Possible issues to check in Railway logs:${NC}"
echo ""
echo "1. Missing UUID for 'id' field:"
echo "   ERROR: null value in column \"id\" violates not-null constraint"
echo ""
echo "2. Table doesn't exist:"
echo "   ERROR: relation \"profiles\" does not exist"
echo ""
echo "3. Permission denied:"
echo "   ERROR: permission denied for table profiles"
echo ""
echo "4. Wrong column names:"
echo "   ERROR: column \"username\" of relation \"profiles\" does not exist"
echo ""
echo "5. JSON format error:"
echo "   ERROR: invalid input syntax for type json"
echo ""

echo -e "${YELLOW}📋 Next steps:${NC}"
echo "1. Go to Railway dashboard: https://railway.app/dashboard"
echo "2. Click on 'cinefluent-api' service"
echo "3. Click 'Logs' tab"
echo "4. Look for errors that happened around $(date)"
echo "5. Share the exact error message you see"
echo ""

echo -e "${BLUE}🔧 Quick fixes to try:${NC}"
echo ""
echo "A. If you see UUID error, run this SQL in Supabase:"
echo "   ALTER TABLE profiles ALTER COLUMN id SET DEFAULT gen_random_uuid();"
echo ""
echo "B. If you see permission error, run this SQL:"
echo "   ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;"
echo ""
echo "C. If you see column error, check your FastAPI code matches the table structure"
echo ""

echo -e "${GREEN}🎯 The exact error message from Railway logs will tell us how to fix this!${NC}"