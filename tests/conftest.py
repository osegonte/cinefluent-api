import pytest
import os
from fastapi.testclient import TestClient
from main import app

# Set test environment
os.environ["ENVIRONMENT"] = "test"

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def test_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@cinefluent.com", 
        "password": "testpassword123",
        "full_name": "Test User"
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    # Store original values
    original_env = os.environ.copy()
    
    # Set test-specific environment variables
    os.environ["ENVIRONMENT"] = "test"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
