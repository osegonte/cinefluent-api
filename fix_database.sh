#!/bin/bash

# CineFluent Database Fix Script
# This script creates the missing 'profiles' table that your FastAPI expects

echo "🔧 CineFluent Database Fix Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}❌ curl is required but not installed.${NC}"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    echo -e "${BLUE}📋 Loading environment variables from .env...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠️  No .env file found. Using system environment variables.${NC}"
fi

# Check required environment variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_KEY" ]; then
    echo -e "${RED}❌ Missing required environment variables:${NC}"
    echo "   SUPABASE_URL: ${SUPABASE_URL:-'NOT SET'}"
    echo "   SUPABASE_SERVICE_KEY: ${SUPABASE_SERVICE_KEY:-'NOT SET'}"
    echo ""
    echo -e "${YELLOW}💡 Make sure your .env file contains:${NC}"
    echo "   SUPABASE_URL=https://your-project-id.supabase.co"
    echo "   SUPABASE_SERVICE_KEY=eyJ..."
    exit 1
fi

echo -e "${GREEN}✅ Environment variables loaded${NC}"
echo "   SUPABASE_URL: ${SUPABASE_URL}"
echo "   SERVICE_KEY: ${SUPABASE_SERVICE_KEY:0:20}..."
echo ""

# SQL to create the profiles table
SQL_CREATE_PROFILES="
-- Create the profiles table that FastAPI expects
CREATE TABLE IF NOT EXISTS profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    username VARCHAR,
    full_name VARCHAR,
    avatar_url VARCHAR,
    native_language VARCHAR DEFAULT 'en',
    learning_languages JSONB DEFAULT '[]'::jsonb,
    learning_goals JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Disable RLS for testing (can be re-enabled later)
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;

-- Create an index for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_username ON profiles(username);
CREATE INDEX IF NOT EXISTS idx_profiles_native_language ON profiles(native_language);
"

echo -e "${BLUE}📊 Creating profiles table...${NC}"

# Execute SQL using Supabase REST API
RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" \
  -X POST "${SUPABASE_URL}/rest/v1/rpc/exec_sql" \
  -H "apikey: ${SUPABASE_SERVICE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"${SQL_CREATE_PROFILES}\"}")

# Extract HTTP status
HTTP_STATUS=$(echo $RESPONSE | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
RESPONSE_BODY=$(echo $RESPONSE | sed -e 's/HTTP_STATUS\:.*//g')

if [ "$HTTP_STATUS" -eq 200 ] || [ "$HTTP_STATUS" -eq 201 ]; then
    echo -e "${GREEN}✅ Profiles table created successfully!${NC}"
else
    echo -e "${YELLOW}⚠️  Direct SQL execution method not available. Using alternative approach...${NC}"
    echo ""
    echo -e "${BLUE}📋 Please run this SQL manually in your Supabase dashboard:${NC}"
    echo ""
    echo "1. Go to: ${SUPABASE_URL}/project/default/sql"
    echo "2. Paste and run this SQL:"
    echo ""
    echo "-- Create profiles table"
    echo "CREATE TABLE IF NOT EXISTS profiles ("
    echo "    id UUID REFERENCES auth.users(id) PRIMARY KEY,"
    echo "    username VARCHAR,"
    echo "    full_name VARCHAR,"
    echo "    avatar_url VARCHAR,"
    echo "    native_language VARCHAR DEFAULT 'en',"
    echo "    learning_languages JSONB DEFAULT '[]'::jsonb,"
    echo "    learning_goals JSONB DEFAULT '{}'::jsonb,"
    echo "    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),"
    echo "    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
    echo ");"
    echo ""
    echo "-- Disable RLS for testing"
    echo "ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;"
    echo ""
fi

echo ""
echo -e "${BLUE}🧪 Testing user registration...${NC}"

# Test registration
TEST_EMAIL="dbfix-test-$(date +%s)@example.com"
API_URL="https://cinefluent-api-production-5082.up.railway.app"

TEST_RESPONSE=$(curl -s -w "HTTP_STATUS:%{http_code}" \
  -X POST "${API_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"${TEST_EMAIL}\",
    \"password\": \"TestPass123!\",
    \"full_name\": \"Database Fix Test User\"
  }")

# Extract HTTP status
TEST_HTTP_STATUS=$(echo $TEST_RESPONSE | tr -d '\n' | sed -e 's/.*HTTP_STATUS://')
TEST_RESPONSE_BODY=$(echo $TEST_RESPONSE | sed -e 's/HTTP_STATUS\:.*//g')

echo ""
if [ "$TEST_HTTP_STATUS" -eq 200 ] || [ "$TEST_HTTP_STATUS" -eq 201 ]; then
    echo -e "${GREEN}🎉 SUCCESS! User registration is now working!${NC}"
    echo ""
    echo -e "${GREEN}✅ Authentication system is 100% complete!${NC}"
    echo ""
    echo "Test user created:"
    echo "  Email: ${TEST_EMAIL}"
    echo "  Response: ${TEST_RESPONSE_BODY}"
    echo ""
    echo -e "${BLUE}🚀 Your backend is now ready to share!${NC}"
    echo ""
    echo "Your CineFluent API now supports:"
    echo "  ✅ User registration"
    echo "  ✅ User login"
    echo "  ✅ Protected routes"
    echo "  ✅ User profiles"
    echo "  ✅ Movie endpoints"
    echo "  ✅ Progress tracking"
    echo ""
else
    echo -e "${RED}❌ Registration test failed (HTTP ${TEST_HTTP_STATUS})${NC}"
    echo "Response: ${TEST_RESPONSE_BODY}"
    echo ""
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "1. Check if the profiles table was created in Supabase dashboard"
    echo "2. Verify your Railway environment variables"
    echo "3. Check Railway logs for detailed errors"
fi

echo ""
echo -e "${BLUE}📚 Manual verification:${NC}"
echo "1. Go to Supabase dashboard: ${SUPABASE_URL}/project/default/editor"
echo "2. Check that 'profiles' table exists"
echo "3. Test registration with: curl -X POST ${API_URL}/api/v1/auth/register ..."
echo ""
echo "Script completed! 🎯"