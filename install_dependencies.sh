#!/bin/bash

echo "🎌 CineFluent - Installing Dependencies"
echo "======================================="

# Check Python version
echo "Python version:"
python --version

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install core dependencies first
echo "Installing core FastAPI dependencies..."
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install pydantic[email]==2.4.2

# Install authentication and database
echo "Installing auth and database dependencies..."
pip install supabase==2.0.0
pip install python-dotenv==1.0.0
pip install sqlalchemy==2.0.23

# Install all requirements
echo "Installing all requirements..."
pip install -r requirements.txt

# Test FastAPI import
echo "Testing FastAPI import..."
python3 -c "import fastapi; print('✅ FastAPI imported successfully')"

# Test other critical imports
echo "Testing other imports..."
python3 -c "import supabase; print('✅ Supabase imported successfully')"
python3 -c "import uvicorn; print('✅ Uvicorn imported successfully')"

echo ""
echo "✅ Dependencies installation complete!"
echo "🚀 Ready to start the API server"