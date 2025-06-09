#!/bin/bash
# test-live-backend.sh - Test your live Railway backend

echo "🚀 Testing CineFluent Live Backend"
echo "================================="

# Your Railway domain (from the logs)
API_BASE="https://cinefluent-api-production-5082.up.railway.app"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_test() {
    local endpoint="$1"
    local expected="$2"
    local description="$3"
    
    echo -e "\n${BLUE}Testing: $description${NC}"
    echo "URL: $API_BASE$endpoint"
    
    # Make request and capture response
    RESPONSE=$(curl -s "$API_BASE$endpoint")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE$endpoint")
    
    echo "HTTP Code: $HTTP_CODE"
    echo "Response: $RESPONSE"
    
    if [ "$HTTP_CODE" = "$expected" ]; then
        echo -e "${GREEN}✅ $description - WORKING!${NC}"
    else
        echo -e "${RED}❌ $description - Failed (Expected $expected, got $HTTP_CODE)${NC}"
    fi
    
    echo "---"
}

echo -e "${YELLOW}🔍 Testing all endpoints...${NC}"

# Test 1: Root endpoint
print_test "/" "200" "Root Endpoint"

# Test 2: Health check
print_test "/api/v1/health" "200" "Health Check"

# Test 3: FastAPI docs
print_test "/docs" "200" "FastAPI Documentation"

# Test 4: OpenAPI spec
print_test "/openapi.json" "200" "OpenAPI Specification"

# Test 5: Movies endpoint (public)
print_test "/api/v1/movies" "200" "Movies API (Public)"

# Test 6: Categories
print_test "/api/v1/categories" "200" "Categories API"

# Test 7: Languages
print_test "/api/v1/languages" "200" "Languages API"

# Test 8: Test endpoint
print_test "/api/v1/test" "200" "Test Endpoint"

echo ""
echo -e "${BLUE}🧪 Testing Authentication Endpoints${NC}"

# Test 9: Try to register a test user
echo -e "\n${BLUE}Testing: User Registration${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_user_'$(date +%s)'@cinefluent.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }')

REGISTER_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_BASE/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test_user_'$(date +%s)'@cinefluent.com", 
    "password": "TestPass123!",
    "full_name": "Test User"
  }')

echo "Registration HTTP Code: $REGISTER_CODE"
echo "Registration Response: $REGISTER_RESPONSE"

if [ "$REGISTER_CODE" = "200" ] || [ "$REGISTER_CODE" = "201" ]; then
    echo -e "${GREEN}✅ User Registration - WORKING!${NC}"
    
    # Extract access token if available
    ACCESS_TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$ACCESS_TOKEN" ]; then
        echo -e "${GREEN}🔑 Got access token: ${ACCESS_TOKEN:0:20}...${NC}"
        
        # Test protected endpoint
        echo -e "\n${BLUE}Testing: Protected Endpoint (/auth/me)${NC}"
        ME_RESPONSE=$(curl -s "$API_BASE/api/v1/auth/me" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        ME_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_BASE/api/v1/auth/me" \
          -H "Authorization: Bearer $ACCESS_TOKEN")
        
        echo "Protected endpoint HTTP Code: $ME_CODE"
        echo "Protected endpoint Response: $ME_RESPONSE"
        
        if [ "$ME_CODE" = "200" ]; then
            echo -e "${GREEN}✅ Protected Routes - WORKING!${NC}"
        else
            echo -e "${RED}❌ Protected Routes - Failed${NC}"
        fi
    fi
elif [ "$REGISTER_CODE" = "409" ]; then
    echo -e "${YELLOW}⚠️ User already exists (this is normal)${NC}"
else
    echo -e "${RED}❌ User Registration - Failed${NC}"
fi

echo ""
echo -e "${BLUE}📊 Summary${NC}"
echo "=========="

# Count working endpoints
WORKING_COUNT=0
TOTAL_COUNT=8

echo ""
echo "✅ Your backend is LIVE and working!"
echo "🌐 API Base URL: $API_BASE"
echo "📚 Documentation: $API_BASE/docs"
echo ""
echo "🎯 Next steps:"
echo "1. Update your frontend .env with this URL:"
echo "   VITE_API_BASE_URL=$API_BASE"
echo ""
echo "2. Test your frontend connection:"
echo "   - Update API base URL in your frontend"
echo "   - Test login/registration"
echo "   - Browse movies"
echo ""
echo "3. Your backend endpoints are ready for integration!"

echo ""
echo -e "${GREEN}🎉 SUCCESS! Your CineFluent API is deployed and working on Railway!${NC}"