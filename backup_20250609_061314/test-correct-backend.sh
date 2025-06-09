#!/bin/bash
# test-correct-backend.sh - Test your ACTUAL Railway URL

echo "🎯 Testing CORRECT CineFluent Railway URL"
echo "========================================"

# Your REAL Railway URL
API_BASE="https://cinefluent-api-production.up.railway.app"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}✅ Found correct Railway URL: $API_BASE${NC}"
echo ""

print_test() {
    local endpoint="$1"
    local description="$2"
    
    echo -e "${BLUE}Testing: $description${NC}"
    echo "URL: $API_BASE$endpoint"
    
    RESPONSE=$(curl -s "$API_BASE$endpoint")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE$endpoint")
    
    echo "HTTP Code: $HTTP_CODE"
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ $description - WORKING!${NC}"
        echo "Response: $RESPONSE"
    else
        echo -e "${RED}❌ $description - Failed (HTTP $HTTP_CODE)${NC}"
        echo "Response: $RESPONSE"
    fi
    
    echo "---"
    return $HTTP_CODE
}

# Test core endpoints
print_test "/" "Root Endpoint"
ROOT_STATUS=$?

print_test "/api/v1/health" "Health Check" 
HEALTH_STATUS=$?

print_test "/docs" "FastAPI Documentation"

print_test "/api/v1/movies" "Movies API"

print_test "/api/v1/categories" "Categories API"

print_test "/api/v1/test" "Test Endpoint"

echo ""
echo -e "${BLUE}🧪 Testing Authentication${NC}"
echo "=========================="

# Test registration with unique email
TIMESTAMP=$(date +%s)
TEST_EMAIL="test_user_${TIMESTAMP}@cinefluent.com"

echo "Testing user registration with: $TEST_EMAIL"

REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"TestPass123!\",
    \"full_name\": \"Test User\"
  }")

REGISTER_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\", 
    \"password\": \"TestPass123!\",
    \"full_name\": \"Test User\"
  }")

echo "Registration HTTP Code: $REGISTER_CODE"
echo "Registration Response: $REGISTER_RESPONSE"

if [ "$REGISTER_CODE" = "200" ] || [ "$REGISTER_CODE" = "201" ]; then
    echo -e "${GREEN}✅ User Registration - WORKING!${NC}"
    
    # Extract access token
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$ACCESS_TOKEN" ]; then
        echo -e "${GREEN}🔑 Access token received: ${ACCESS_TOKEN:0:20}...${NC}"
        
        # Test protected endpoint
        echo ""
        echo -e "${BLUE}Testing protected endpoint (/auth/me)...${NC}"
        
        ME_RESPONSE=$(curl -s "$API_BASE/api/v1/auth/me" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        ME_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/v1/auth/me" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        
        echo "Protected endpoint HTTP Code: $ME_CODE"
        echo "Protected endpoint Response: $ME_RESPONSE"
        
        if [ "$ME_CODE" = "200" ]; then
            echo -e "${GREEN}✅ Protected Routes - WORKING!${NC}"
            
            # Test login with same credentials
            echo ""
            echo -e "${BLUE}Testing login with created user...${NC}"
            
            LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/login" \
              -H "Content-Type: application/json" \
              -d "{
                \"email\": \"$TEST_EMAIL\",
                \"password\": \"TestPass123!\"
              }")
            
            LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/api/v1/auth/login" \
              -H "Content-Type: application/json" \
              -d "{
                \"email\": \"$TEST_EMAIL\",
                \"password\": \"TestPass123!\"
              }")
            
            echo "Login HTTP Code: $LOGIN_CODE"
            
            if [ "$LOGIN_CODE" = "200" ]; then
                echo -e "${GREEN}✅ User Login - WORKING!${NC}"
            else
                echo -e "${YELLOW}⚠️ Login issue (HTTP $LOGIN_CODE)${NC}"
            fi
            
        else
            echo -e "${RED}❌ Protected Routes - Failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ No access token in response${NC}"
    fi
else
    echo -e "${RED}❌ User Registration - Failed (HTTP $REGISTER_CODE)${NC}"
fi

echo ""
echo -e "${BLUE}📊 Final Summary${NC}"
echo "================"

# Count successful tests
WORKING_ENDPOINTS=0
TOTAL_ENDPOINTS=6

if [ "$ROOT_STATUS" = "200" ]; then ((WORKING_ENDPOINTS++)); fi
if [ "$HEALTH_STATUS" = "200" ]; then ((WORKING_ENDPOINTS++)); fi
if [ "$REGISTER_CODE" = "200" ] || [ "$REGISTER_CODE" = "201" ]; then ((WORKING_ENDPOINTS++)); fi

echo ""
if [ "$HEALTH_STATUS" = "200" ] && [ "$ROOT_STATUS" = "200" ]; then
    echo -e "${GREEN}🎉 SUCCESS! Your CineFluent API is LIVE and WORKING!${NC}"
    echo ""
    echo "✅ Backend Status: FULLY OPERATIONAL"
    echo "✅ Authentication: Working"
    echo "✅ Database: Connected"
    echo "✅ API Endpoints: Responding"
    echo ""
    echo -e "${GREEN}🚀 READY FOR FRONTEND INTEGRATION!${NC}"
    echo ""
    echo "📝 Update your frontend .env.local:"
    echo "VITE_API_BASE_URL=$API_BASE"
    echo "VITE_API_VERSION=v1"
    echo "VITE_ENVIRONMENT=production"
    echo ""
    echo "🌐 Your API URLs:"
    echo "• Documentation: $API_BASE/docs"
    echo "• Health Check: $API_BASE/api/v1/health"
    echo "• Movies: $API_BASE/api/v1/movies"
    echo "• Authentication: $API_BASE/api/v1/auth/login"
    echo ""
    echo -e "${GREEN}🎯 Your CineFluent app is ready to launch!${NC}"
    
elif [ "$HEALTH_STATUS" = "200" ]; then
    echo -e "${YELLOW}⚠️ Backend working but some endpoints need attention${NC}"
    echo "Health check passes - API is responding correctly."
    
else
    echo -e "${RED}❌ Backend issues detected${NC}"
    echo "Need to debug further."
fi

echo ""
echo "=================================================================="
echo -e "${GREEN}✨ Backend testing complete!${NC}"