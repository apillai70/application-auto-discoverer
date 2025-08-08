# Testing CORS configuration
# test_cors.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_cors_preflight():
    """Test CORS preflight request"""
    response = client.options(
        "/api/topology/discover",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )
    
    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert "Access-Control-Allow-Methods" in response.headers

def test_cors_actual_request():
    """Test actual CORS request"""
    response = client.get(
        "/api/topology/nodes",
        headers={"Origin": "http://localhost:3000"}
    )
    
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

def test_cors_blocked_origin():
    """Test that unknown origins are blocked"""
    response = client.get(
        "/api/topology/nodes",
        headers={"Origin": "https://malicious-site.com"}
    )
    
    # Should not have CORS headers for blocked origins
    assert "Access-Control-Allow-Origin" not in response.headers