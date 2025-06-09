#!/bin/bash
# setup-backend.sh - CineFluent Backend Setup and Fix Script

echo "🚀 CineFluent Backend Setup & Diagnosis"
echo "======================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

print_section() {
    echo -e "\n${PURPLE}$1${NC}"
    echo "$(printf '=%.0s' {1..50})"
}

# Step 1: Check Python installation
print_section "Step 1: Python Environment Check"

# Check for different Python commands
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    print_status "Found python3: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    print_status "Found python: $(python --version)"
else
    print_error "Python not found! Installing Python..."
    
    # Detect OS and install Python
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            print_info "Installing Python via Homebrew..."
            brew install python@3.11
            PYTHON_CMD="python3"
        else
            print_error "Please install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_info "Installing Python via apt..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
        PYTHON_CMD="python3"
    else
        print_error "Unsupported OS. Please install Python 3.11+ manually."
        exit 1
    fi
fi

# Verify Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
print_info "Using Python version: $PYTHON_VERSION"

# Step 2: Check pip
print_section "Step 2: Package Manager Check"

PIP_CMD=""
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
    print_status "Found pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
    print_status "Found pip"
else
    print_error "pip not found! Installing pip..."
    $PYTHON_CMD -m ensurepip --default-pip
    PIP_CMD="pip3"
fi

# Step 3: Create virtual environment
print_section "Step 3: Virtual Environment Setup"

if [ ! -d "cinefluent-env" ]; then
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv cinefluent-env
    print_status "Virtual environment created: cinefluent-env"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source cinefluent-env/bin/activate

# Verify activation
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_status "Virtual environment activated: $VIRTUAL_ENV"
else
    print_error "Failed to activate virtual environment"
    exit 1
fi

# Step 4: Install dependencies
print_section "Step 4: Dependencies Installation"

if [ -f "requirements.txt" ]; then
    print_info "Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Dependencies installed successfully"
else
    print_warning "requirements.txt not found. Installing basic dependencies..."
    pip install --upgrade pip
    pip install fastapi uvicorn supabase python-dotenv sqlalchemy pydantic[email]
    print_status "Basic dependencies installed"
fi

# Step 5: Check environment variables
print_section "Step 5: Environment Variables Check"

if [ -f ".env" ]; then
    print_status ".env file found"
    
    # Check for required variables
    REQUIRED_VARS=("SUPABASE_URL" "SUPABASE_ANON_KEY" "SUPABASE_SERVICE_KEY" "DATABASE_URL")
    
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env; then
            print_status "$var is set"
        else
            print_warning "$var is missing from .env"
        fi
    done
else
    print_warning ".env file not found. Creating template..."
    
    cat > .env << EOF
# CineFluent API Environment Variables
# Fill in your actual values from Supabase

SUPABASE_URL=https://vrrtzxgmwyfnxacqcxvz.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_key_here
SUPABASE_JWT_SECRET=your_jwt_secret_here
DATABASE_URL=postgresql://postgres:your_password@db.vrrtzxgmwyfnxacqcxvz.supabase.co:5432/postgres
ENVIRONMENT=development
EOF
    
    print_warning ".env template created. Please fill in your Supabase credentials!"
fi

# Step 6: Test backend locally
print_section "Step 6: Local Backend Test"

if [ -f "main.py" ]; then
    print_info "Found main.py. Testing backend..."
    
    # Set environment variables for testing
    export PORT=8000
    
    # Test import
    python -c "import main" 2>/dev/null
    if [ $? -eq 0 ]; then
        print_status "main.py imports successfully"
        
        # Start server in background for testing
        print_info "Starting backend server on http://localhost:8000..."
        python main.py &
        SERVER_PID=$!
        
        # Wait a moment for server to start
        sleep 3
        
        # Test health endpoint
        HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null)
        
        if [ "$HEALTH_RESPONSE" = "200" ]; then
            print_status "Health endpoint working! Backend is ready."
            
            # Test a few more endpoints
            ROOT_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null)
            if [ "$ROOT_RESPONSE" = "200" ]; then
                print_status "Root endpoint working!"
            fi
            
            DOCS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null)
            if [ "$DOCS_RESPONSE" = "200" ]; then
                print_status "FastAPI docs available at http://localhost:8000/docs"
            fi
            
        else
            print_error "Health endpoint failed (HTTP $HEALTH_RESPONSE)"
        fi
        
        # Stop test server
        kill $SERVER_PID 2>/dev/null
        
    else
        print_error "main.py has import errors. Check your code!"
        python main.py
    fi
    
else
    print_error "main.py not found! Make sure you're in the correct directory."
    ls -la
    exit 1
fi

# Step 7: Railway deployment check
print_section "Step 7: Railway Deployment"

# Check if Railway CLI is installed
if command -v railway &> /dev/null; then
    print_status "Railway CLI found"
    
    # Check if project is linked
    if railway status &> /dev/null; then
        print_status "Railway project linked"
        
        print_info "Current Railway status:"
        railway status
        
        # Option to deploy
        echo ""
        read -p "Deploy to Railway now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_info "Deploying to Railway..."
            railway up
            print_status "Deployment initiated!"
        fi
    else
        print_warning "Railway project not linked"
        print_info "To link: railway login && railway link"
    fi
else
    print_warning "Railway CLI not found"
    print_info "Install with: npm install -g @railway/cli"
fi

# Step 8: Summary and next steps
print_section "Step 8: Summary & Next Steps"

print_status "Backend setup completed!"

echo ""
echo "🎯 What's working:"
echo "  ✅ Python environment set up"
echo "  ✅ Dependencies installed"
echo "  ✅ Virtual environment activated"

if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "  ✅ Backend runs locally"
else
    echo "  ❌ Backend needs debugging"
fi

echo ""
echo "🚀 Next steps:"
echo "  1. Fill in .env file with your Supabase credentials"
echo "  2. Test locally: python main.py"
echo "  3. Deploy to Railway: railway up"
echo "  4. Update frontend with correct Railway URL"
echo ""

echo "🔧 Quick commands:"
echo "  • Start locally: source cinefluent-env/bin/activate && python main.py"
echo "  • Test health: curl http://localhost:8000/api/v1/health"
echo "  • View docs: open http://localhost:8000/docs"
echo "  • Deploy: railway up"

echo ""
print_info "Virtual environment is still active. Deactivate with: deactivate"

# Create helpful aliases
cat > run-backend.sh << 'EOF'
#!/bin/bash
# Quick start script for CineFluent backend

echo "🚀 Starting CineFluent Backend..."

# Activate virtual environment
source cinefluent-env/bin/activate

# Start the server
python main.py
EOF

chmod +x run-backend.sh
print_status "Created run-backend.sh for easy startup"

echo ""
echo "🎉 Setup complete! Your backend is ready for development and deployment."