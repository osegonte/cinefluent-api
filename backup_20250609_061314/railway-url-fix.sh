#!/bin/bash
# railway-url-fix.sh - Find and fix your correct Railway URL

echo "🔍 CineFluent Railway URL Diagnosis & Fix"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${YELLOW}🚨 Issue Detected: Railway built successfully but URL returns 404${NC}"
echo ""
echo "This means:"
echo "✅ Your code deployed successfully"
echo "✅ Backend is running on Railway"
echo "❌ Public URL is not connected to your service"
echo ""

echo -e "${BLUE}🔧 Step 1: Get Your Correct Railway URL${NC}"
echo "========================================"

# Check if Railway CLI can give us the correct URL
if command -v railway &> /dev/null; then
    echo "✅ Railway CLI found"
    echo ""
    echo "Getting your project information..."
    
    # Get railway status
    if railway status &> /dev/null; then
        echo -e "${GREEN}✅ Railway project linked${NC}"
        echo ""
        echo "Current Railway project status:"
        railway status
        echo ""
        
        # Try to get domain
        echo -e "${BLUE}Getting your Railway domain...${NC}"
        RAILWAY_DOMAIN=$(railway domain 2>/dev/null)
        
        if [ ! -z "$RAILWAY_DOMAIN" ]; then
            echo -e "${GREEN}✅ Found Railway domain: $RAILWAY_DOMAIN${NC}"
            
            # Test the actual domain
            echo ""
            echo -e "${YELLOW}Testing actual Railway domain...${NC}"
            TEST_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_DOMAIN")
            
            if [ "$TEST_RESPONSE" = "200" ]; then
                echo -e "${GREEN}🎉 SUCCESS! Your backend is working at: $RAILWAY_DOMAIN${NC}"
                
                # Test health endpoint
                HEALTH_TEST=$(curl -s "$RAILWAY_DOMAIN/api/v1/health")
                echo "Health check response: $HEALTH_TEST"
                
                # Create updated frontend config
                cat > frontend-config.txt << EOF
# ✅ CORRECTED Frontend Environment Variables
# Use this in your frontend .env.local:

VITE_API_BASE_URL=$RAILWAY_DOMAIN
VITE_API_VERSION=v1
VITE_ENVIRONMENT=production
VITE_DEBUG_MODE=false

# Test your connection with:
# curl $RAILWAY_DOMAIN/api/v1/health
EOF
                
                echo ""
                echo -e "${GREEN}📝 Created frontend-config.txt with correct URL${NC}"
                cat frontend-config.txt
                
            else
                echo -e "${RED}❌ Domain exists but returns HTTP $TEST_RESPONSE${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️ No domain found. Need to generate one.${NC}"
        fi
    else
        echo -e "${RED}❌ Railway project not linked${NC}"
        echo "Run: railway login && railway link"
    fi
else
    echo -e "${RED}❌ Railway CLI not found${NC}"
    echo "Install: npm install -g @railway/cli"
fi

echo ""
echo -e "${BLUE}🔧 Step 2: Manual Railway Dashboard Check${NC}"
echo "========================================"
echo ""
echo "1. Go to: https://railway.app/dashboard"
echo "2. Find your 'cinefluent-api' project"
echo "3. Click on your service"
echo "4. Go to Settings → Networking"
echo "5. Check 'Public Networking' section"
echo ""
echo "If no domain exists:"
echo "  → Click 'Generate Domain'"
echo "  → Select port 8080 (your app runs on this port)"
echo "  → Copy the generated URL"

echo ""
echo -e "${BLUE}🔧 Step 3: Force Railway Redeploy${NC}"
echo "========================================"
echo ""
echo "If domain exists but still returns 404:"

# Option to redeploy
echo ""
read -p "Redeploy to Railway now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚀 Redeploying to Railway...${NC}"
    
    # Check if we have railway CLI and project linked
    if command -v railway &> /dev/null && railway status &> /dev/null; then
        railway up
        echo ""
        echo -e "${GREEN}✅ Redeploy initiated!${NC}"
        echo ""
        echo "Wait 2-3 minutes, then test your URL again."
        
        # Wait and test
        echo "Waiting 30 seconds for deployment..."
        sleep 30
        
        # Get the domain again after redeploy
        NEW_DOMAIN=$(railway domain 2>/dev/null)
        if [ ! -z "$NEW_DOMAIN" ]; then
            echo ""
            echo -e "${BLUE}Testing redeployed service...${NC}"
            NEW_TEST=$(curl -s -o /dev/null -w "%{http_code}" "$NEW_DOMAIN")
            
            if [ "$NEW_TEST" = "200" ]; then
                echo -e "${GREEN}🎉 SUCCESS! Backend now working at: $NEW_DOMAIN${NC}"
            else
                echo -e "${YELLOW}⚠️ Still returning HTTP $NEW_TEST - may need more time${NC}"
            fi
        fi
        
    else
        echo -e "${RED}❌ Cannot redeploy: Railway CLI not set up${NC}"
    fi
fi

echo ""
echo -e "${BLUE}🔧 Step 4: Alternative URLs to Try${NC}"
echo "========================================"
echo ""
echo "Your service might be accessible at these URLs:"
echo "• https://cinefluent-api-production.up.railway.app"
echo "• https://cinefluent-api-production.railway.app" 
echo "• https://web-production-XXXX.up.railway.app"
echo ""
echo "Test each one manually:"

ALTERNATIVE_URLS=(
    "https://cinefluent-api-production.up.railway.app"
    "https://cinefluent-api-production.railway.app"
)

for url in "${ALTERNATIVE_URLS[@]}"; do
    echo ""
    echo -e "${BLUE}Testing: $url${NC}"
    ALT_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$ALT_CODE" = "200" ]; then
        echo -e "${GREEN}✅ FOUND! Working URL: $url${NC}"
        
        # Test health endpoint
        ALT_HEALTH=$(curl -s "$url/api/v1/health" 2>/dev/null)
        echo "Health response: $ALT_HEALTH"
        
        # Create config for this URL
        echo ""
        echo "Use this URL in your frontend:"
        echo "VITE_API_BASE_URL=$url"
        
    elif [ "$ALT_CODE" = "404" ]; then
        echo -e "${RED}❌ Returns 404: $url${NC}"
    else
        echo -e "${YELLOW}⚠️ HTTP $ALT_CODE: $url${NC}"
    fi
done

echo ""
echo -e "${PURPLE}🔧 Step 5: Create New Railway Service (Last Resort)${NC}"
echo "========================================"
echo ""
echo "If nothing above works, your current Railway service may be corrupted."
echo "Create a fresh Railway service:"
echo ""
echo "1. railway init (in your project directory)"
echo "2. railway up"
echo "3. railway domain"
echo "4. Copy the new URL"

echo ""
echo -e "${BLUE}📋 Summary${NC}"
echo "==========="
echo ""
echo "Your FastAPI code is working (build logs confirm this)."
echo "The issue is Railway URL configuration."
echo ""
echo "✅ What's working: Code deployment, Supabase connection, FastAPI server"
echo "❌ What's broken: Public URL routing to your service"
echo ""
echo "🎯 Next action: Get the correct Railway URL from dashboard or CLI"

echo ""
echo -e "${GREEN}Once you get the correct URL, your frontend integration will work perfectly!${NC}"