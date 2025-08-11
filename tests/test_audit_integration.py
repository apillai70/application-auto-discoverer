# tests/test_audit_integration.py - Integration tests

import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
import json

class TestAuditIntegration:
    """Integration tests for the audit system"""
    
    @pytest.fixture
    async def client(self):
        """Create test client"""
        from main import app
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    async def test_audit_overview(self, client):
        """Test audit system overview"""
        response = await client.get("/api/v1/audit/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "capabilities" in data
        assert "statistics" in data
    
    async def test_create_authentication_event(self, client):
        """Test creating authentication audit event"""
        event = {
            "event_type": "authentication",
            "user_id": "test.user@company.com",
            "action": "login",
            "result": "failure",
            "source_ip": "192.168.1.100",
            "auth_details": {
                "identity_provider": "AzureAD",
                "failure_reason": "Invalid password"
            }
        }
        
        response = await client.post("/api/v1/audit/events", json=event)
        assert response.status_code == 200
        data = response.json()
        assert "event_id" in data
        assert "risk_level" in data
    
    async def test_bulk_event_processing(self, client):
        """Test bulk event processing"""
        events = []
        for i in range(5):
            event = {
                "event_type": "authentication",
                "user_id": f"user{i}@company.com",
                "action": "login",
                "result": "failure",
                "source_ip": "203.0.113.50"
            }
            events.append(event)
        
        bulk_payload = {
            "events": events,
            "source_system": "TestSystem"
        }
        
        response = await client.post("/api/v1/audit/events/bulk", json=bulk_payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["event_ids"]) == 5
    
    async def test_risk_assessment(self, client):
        """Test risk assessment functionality"""
        # Create a high-risk event
        event = {
            "event_type": "authentication",
            "user_id": "admin@company.com",
            "action": "login",
            "result": "success",
            "source_ip": "185.220.101.182",  # Suspicious IP
            "timestamp": (datetime.utcnow() - timedelta(hours=22)).isoformat(),  # 2 AM
            "device_info": {
                "is_trusted": False,
                "device_fingerprint": "suspicious_device"
            },
            "geographic_info": {
                "country": "Unknown"
            }
        }
        
        response = await client.post("/api/v1/audit/events", json=event)
        assert response.status_code == 200
        data = response.json()
        
        # Risk level should be elevated
        assert data["risk_level"] in ["medium", "high", "critical"]
    
    async def test_azure_ad_integration(self, client):
        """Test Azure AD integration endpoint"""
        azure_event = {
            "userPrincipalName": "integration.test@company.com",
            "activityDisplayName": "Sign-in activity",
            "resultType": "50126",
            "ipAddress": "203.0.113.100",
            "failureReason": "Invalid credentials"
        }
        
        response = await client.post("/api/v1/audit/integrations/azure-ad", json=azure_event)
        assert response.status_code == 200
        data = response.json()
        assert "event_id" in data
    
    async def test_suspicious_activity_detection(self, client):
        """Test suspicious activity detection"""
        # Create multiple failed attempts from same IP
        for i in range(3):
            event = {
                "event_type": "authentication",
                "user_id": f"victim{i}@company.com",
                "action": "login",
                "result": "failure",
                "source_ip": "198.51.100.42",
                "auth_details": {
                    "failure_reason": "Brute force attempt"
                }
            }
            await client.post("/api/v1/audit/events", json=event)
        
        # Check suspicious activity
        response = await client.get("/api/v1/audit/suspicious-activity")
        assert response.status_code == 200
        data = response.json()
        assert "suspicious_ips" in data
    
    async def test_audit_query(self, client):
        """Test advanced audit querying"""
        query = {
            "event_types": ["authentication"],
            "results": ["failure"],
            "limit": 10
        }
        
        response = await client.post("/api/v1/audit/events/query", json=query)
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "total_count" in data

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])