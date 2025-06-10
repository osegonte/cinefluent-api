import pytest

def test_auth_endpoints_exist(client):
    """Test that auth endpoints are accessible"""
    # Test register endpoint (should fail without data, but endpoint should exist)
    response = client.post("/api/v1/auth/register")
    assert response.status_code in [400, 422]  # Bad request or validation error
    
    # Test login endpoint
    response = client.post("/api/v1/auth/login")
    assert response.status_code in [400, 422]
    
    # Test me endpoint (should fail without auth)
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401  # Unauthorized

def test_auth_test_endpoint(client):
    """Test auth test endpoint without authentication"""
    response = client.get("/api/v1/test/auth")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] == False
