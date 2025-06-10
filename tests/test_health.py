import pytest
from fastapi.testclient import TestClient

def test_root_endpoint(client):
    """Test root endpoint returns health status"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "CineFluent API"

def test_health_check(client):
    """Test detailed health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "environment" in data

def test_test_endpoint(client):
    """Test the test endpoint"""
    response = client.get("/api/v1/test")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "CineFluent API is working!"
    assert "timestamp" in data
