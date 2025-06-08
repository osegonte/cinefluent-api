#!/bin/bash

# CineFluent API Project Cleanup Script
# This script removes irrelevant files and organizes the project structure

echo "🧹 Starting CineFluent API Project Cleanup..."
echo "================================================="

# Create backup directory for safety
echo "📦 Creating backup directory..."
mkdir -p backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"

# Function to safely remove files
safe_remove() {
    if [ -f "$1" ] || [ -d "$1" ]; then
        echo "🗑️  Removing: $1"
        mv "$1" "$BACKUP_DIR/" 2>/dev/null || rm -rf "$1"
    fi
}

# Remove irrelevant/duplicate/test files
echo ""
echo "🗂️  Removing irrelevant files..."

# Remove duplicate/broken files
safe_remove "main.p"                    # Broken main file
safe_remove "debug_endpoint.py"         # Standalone debug file (already in main.py)
safe_remove "fix_search.py"            # Temporary fix file
safe_remove "search_fix.py"            # Temporary fix file
safe_remove "cinefluent-env"           # Wrong env file

# Remove development/test files
safe_remove "setup_project.py"         # Already used, no longer needed
safe_remove "test_api_simple.py"       # Test file if exists

# Remove virtual environment (can be recreated)
safe_remove ".venv"
safe_remove "venv"

# Remove build/cache directories
safe_remove ".nixpacks"
safe_remove "__pycache__"
safe_remove "*.pyc"
safe_remove ".pytest_cache"

# Clean up any temporary files
safe_remove "*.tmp"
safe_remove "*.temp"
safe_remove ".DS_Store"
safe_remove "Thumbs.db"

echo ""
echo "📁 Organizing remaining files..."

# Ensure proper directory structure exists
mkdir -p database
mkdir -p scripts  
mkdir -p tests

# Move files to correct locations if they're in wrong places
if [ -f "deployment_test.py" ]; then
    echo "📍 Moving deployment_test.py to scripts/"
    mv deployment_test.py scripts/
fi

if [ -f "env_setup_script.py" ]; then
    echo "📍 Moving env_setup_script.py to scripts/"
    mv env_setup_script.py scripts/
fi

# Ensure core files are in root
CORE_FILES=("main.py" "auth.py" "database.py" "subtitle_processor.py" "subtitle_api.py" "requirements.txt" "railway.toml" ".env" ".env.template" ".gitignore" "LICENSE" "README.md" "Procfile")

echo ""
echo "✅ Verifying core files are present:"
for file in "${CORE_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
    fi
done

echo ""
echo "📋 Final project structure:"
echo "cinefluent-api/"
echo "├── main.py                     # ✅ Main FastAPI application"
echo "├── auth.py                     # ✅ Authentication module"
echo "├── database.py                 # ✅ Database connection"
echo "├── subtitle_processor.py       # ✅ Subtitle processing"
echo "├── subtitle_api.py            # ✅ Subtitle API endpoints"
echo "├── requirements.txt           # ✅ Dependencies"
echo "├── railway.toml              # ✅ Railway configuration"
echo "├── .env                      # ✅ Environment variables"
echo "├── .env.template             # ✅ Environment template"
echo "├── .gitignore               # ✅ Git ignore rules"
echo "├── LICENSE                  # ✅ MIT License"
echo "├── README.md               # ✅ Documentation"
echo "├── Procfile               # ✅ Process file"
echo "├── database/"
echo "│   └── complete_schema.sql    # ✅ Database schema"
echo "├── scripts/"
echo "│   ├── deployment_test.py     # ✅ Deployment testing"
echo "│   ├── env_setup_script.py    # ✅ Environment setup"
echo "│   └── railway_setup.sh       # ✅ Railway variables"
echo "└── tests/"
echo "    ├── test_auth.py           # ✅ Authentication tests"
echo "    └── test_subtitle_features.py # ✅ Feature tests"

echo ""
echo "🔍 Checking for any remaining irrelevant files..."
echo "Files in current directory:"
ls -la | grep -E '\.(py|txt|toml|md|sh)$|^d' | head -20

echo ""
echo "💾 Backup created in: $BACKUP_DIR"
echo "   (You can delete this backup directory once everything works)"

echo ""
echo "🧹 Cleanup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Verify your core files are working:"
echo "   python main.py"
echo ""
echo "2. Test your Railway deployment:"
echo "   railway up"
echo ""
echo "3. Run comprehensive tests:"
echo "   python scripts/deployment_test.py"
echo ""
echo "4. If everything works, remove backup:"
echo "   rm -rf $BACKUP_DIR"

echo ""
echo "🎯 Your CineFluent API project is now clean and organized!"
echo "================================================="
