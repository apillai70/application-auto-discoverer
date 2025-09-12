# demo_comprehensive_logging.py
"""
Comprehensive Logging System Demo
Demonstrates all features and capabilities of the logging system
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import random
from typing import List, Dict, Any

# Demo configuration
DEMO_CONFIG = {
    "comprehensive_logging": {
        "enabled": True,
        "batch_size": 20,
        "batch_timeout": 3.0,
        "queue_max_size": 5000,
        "log_retention_days": 30,
        "enable_uvicorn_interception": True,
        "enable_frontend_logging": True,
        "enable_incident_management": True
    },
    
    "log_classification": {
        "auto_classify": True,
        "sensitivity_detection": True,
        "pii_detection": True,
        "incident_detection": True,
        "risk_scoring": True,
        "tag_generation": True
    },
    
    "access_control": {
        "role_based_access": True,
        "log_sanitization": True,
        "audit_log_access": True
    },
    
    "servicenow": {
        "enabled": False,  # Disabled for demo
        "base_url": "https://demo-instance.service-now.com",
        "max_tickets_per_hour": 5
    },
    
    "storage": {
        "log_storage": {
            "base_path": "demo_logs",
            "retention_days": 30,
            "max_file_size_mb": 10
        }
    },
    
    "classification_rules": {
        "level_keywords": {
            "EMERGENCY": ["system_down", "complete_failure", "data_loss", "security_breach"],
            "ALERT": ["service_unavailable", "data_corruption", "authentication_failure"],
            "CRITICAL": ["exception", "fatal", "crash", "timeout", "database_error"],
            "ERROR": ["error", "failed", "exception", "invalid", "denied"],
            "WARNING": ["warning", "deprecated", "retry", "fallback", "slow"],
            "NOTICE": ["started", "stopped", "configured", "initialized"],
            "INFO": ["request", "response", "success", "completed"],
            "DEBUG": ["debug", "trace", "verbose"]
        },
        
        "sensitive_patterns": [
            "password[\"\\s]*[:=][\"\\s]*[^\"\\s]+",
            "token[\"\\s]*[:=][\"\\s]*[^\"\\s]+",
            "api[_-]?key[\"\\s]*[:=][\"\\s]*[^\"\\s]+",
            "\\b\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}\\b"
        ],
        
        "incident_conditions": {
            "SEV1_CRITICAL": {
                "levels": ["EMERGENCY", "ALERT"],
                "keywords": ["system_down", "security_breach", "data_loss"]
            },
            "SEV2_HIGH": {
                "levels": ["CRITICAL"],
                "keywords": ["database_error", "authentication_failure"]
            }
        }
    }
}

class LoggingDemo:
    """Comprehensive logging system demonstration"""
    
    def __init__(self):
        self.logger = None
        self.demo_users = [
            {"id": "user_001", "name": "Alice Johnson", "role": "admin"},
            {"id": "user_002", "name": "Bob Smith", "role": "user"},
            {"id": "user_003", "name": "Carol Davis", "role": "developer"},
            {"id": "user_004", "name": "David Wilson", "role": "security"}
        ]
        
        self.demo_scenarios = [
            "normal_operations",
            "performance_issues", 
            "security_events",
            "critical_failures",
            "user_activities",
            "api_interactions"
        ]
    
    async def initialize_system(self):
        """Initialize the comprehensive logging system"""
        print("🚀 Initializing Comprehensive Logging System Demo...")
        
        # Ensure demo directory exists
        Path("demo_logs").mkdir(exist_ok=True)
        
        try:
            from services.comprehensive_logging_system import initialize_comprehensive_logging
            self.logger = initialize_comprehensive_logging(DEMO_CONFIG)
            await self.logger.start()
            
            print("✅ Comprehensive logging system initialized")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize logging system: {e}")
            return False
    
    async def demo_basic_logging(self):
        """Demonstrate basic logging functionality"""
        print("\n📝 Demo 1: Basic Logging Functionality")
        print("-" * 50)
        
        basic_logs = [
            {
                'level': 'INFO',
                'source': 'DEMO',
                'log_type': 'SYSTEM_EVENT',
                'message': 'Demo system started successfully',
                'details': {
                    'demo_version': '1.0.0',
                    'timestamp': datetime.now().isoformat(),
                    'environment': 'demo'
                }
            },
            {
                'level': 'DEBUG',
                'source': 'DEMO',
                'log_type': 'SYSTEM_EVENT', 
                'message': 'Debug information for system initialization',
                'details': {
                    'memory_usage': '128MB',
                    'cpu_usage': '15%',
                    'active_connections': 5
                }
            },
            {
                'level': 'NOTICE',
                'source': 'DEMO',
                'log_type': 'SYSTEM_EVENT',
                'message': 'Configuration loaded from demo_config.yaml',
                'details': {
                    'config_file': 'demo_config.yaml',
                    'settings_count': 25
                }
            }
        ]
        
        for log in basic_logs:
            await self.logger.log_entry(log)
            print(f"  📝 Logged: {log['level']} - {log['message']}")
            await asyncio.sleep(0.5)
        
        print("✅ Basic logging demo completed")
    
    async def demo_api_request_logging(self):
        """Demonstrate API request/response logging"""
        print("\n🌐 Demo 2: API Request/Response Logging")
        print("-" * 50)
        
        api_scenarios = [
            {
                'method': 'GET',
                'endpoint': '/api/v1/users',
                'status': 200,
                'duration': 145,
                'user_id': 'user_001'
            },
            {
                'method': 'POST',
                'endpoint': '/api/v1/auth/login',
                'status': 200,
                'duration': 320,
                'user_id': 'user_002'
            },
            {
                'method': 'PUT',
                'endpoint': '/api/v1/users/profile',
                'status': 400,
                'duration': 89,
                'user_id': 'user_003'
            },
            {
                'method': 'DELETE',
                'endpoint': '/api/v1/data/cleanup',
                'status': 500,
                'duration': 5432,
                'user_id': 'user_001'
            }
        ]
        
        for scenario in api_scenarios:
            # Log request
            await self.logger.log_entry({
                'level': 'INFO',
                'source': 'API',
                'log_type': 'REQUEST',
                'message': f"{scenario['method']} {scenario['endpoint']} - Request received",
                'user_id': scenario['user_id'],
                'details': {
                    'method': scenario['method'],
                    'endpoint': scenario['endpoint'],
                    'user_id': scenario['user_id'],
                    'request_time': datetime.now().isoformat()
                }
            })
            
            # Simulate processing time
            await asyncio.sleep(scenario['duration'] / 1000)
            
            # Log response
            level = 'ERROR' if scenario['status'] >= 500 else 'WARNING' if scenario['status'] >= 400 else 'INFO'
            await self.logger.log_entry({
                'level': level,
                'source': 'API',
                'log_type': 'RESPONSE',
                'message': f"{scenario['method']} {scenario['endpoint']} - {scenario['status']} ({scenario['duration']}ms)",
                'user_id': scenario['user_id'],
                'details': {
                    'method': scenario['method'],
                    'endpoint': scenario['endpoint'],
                    'status_code': scenario['status'],
                    'duration_ms': scenario['duration'],
                    'response_time': datetime.now().isoformat()
                }
            })
            
            print(f"  🌐 API Call: {scenario['method']} {scenario['endpoint']} - {scenario['status']} ({scenario['duration']}ms)")
        
        print("✅ API logging demo completed")
    
    async def demo_security_events(self):
        """Demonstrate security event logging"""
        print("\n🔒 Demo 3: Security Event Logging")
        print("-" * 50)
        
        security_events = [
            {
                'level': 'WARNING',
                'message': 'Failed login attempt detected',
                'details': {
                    'username': 'admin',
                    'ip_address': '192.168.1.100',
                    'attempt_count': 3,
                    'user_agent': 'Mozilla/5.0 (Suspicious Bot)'
                }
            },
            {
                'level': 'INFO',
                'message': 'Successful user authentication',
                'details': {
                    'user_id': 'user_002',
                    'ip_address': '10.0.1.50',
                    'mfa_enabled': True,
                    'login_method': 'oauth'
                }
            },
            {
                'level': 'ALERT',
                'message': 'Potential SQL injection attempt blocked',
                'details': {
                    'attack_type': 'sql_injection',
                    'blocked_query': "'; DROP TABLE users; --",
                    'source_ip': '203.0.113.42',
                    'endpoint': '/api/v1/search'
                }
            },
            {
                'level': 'CRITICAL',
                'message': 'Unauthorized access to sensitive data attempted',
                'details': {
                    'user_id': 'user_003',
                    'resource': '/admin/sensitive-data',
                    'required_permission': 'admin',
                    'user_permission': 'user'
                }
            }
        ]
        
        for event in security_events:
            await self.logger.log_entry({
                'level': event['level'],
                'source': 'SECURITY',
                'log_type': 'SECURITY',
                'message': event['message'],
                'details': event['details']
            })
            
            print(f"  🔒 Security Event: {event['level']} - {event['message']}")
            await asyncio.sleep(1)
        
        print("✅ Security events demo completed")
    
    async def demo_sensitive_data_handling(self):
        """Demonstrate sensitive data detection and masking"""
        print("\n🎭 Demo 4: Sensitive Data Handling")
        print("-" * 50)
        
        sensitive_data_logs = [
            {
                'level': 'INFO',
                'message': 'User registration with password=secret123 and token=abc123xyz',
                'details': {
                    'username': 'newuser',
                    'password': 'verysecretpassword',
                    'api_key': 'sk-1234567890abcdef',
                    'email': 'user@example.com',
                    'phone': '555-123-4567',
                    'credit_card': '4532-1234-5678-9012'
                }
            },
            {
                'level': 'WARNING',
                'message': 'Authentication failed for token bearer xyz789',
                'details': {
                    'auth_token': 'bearer-token-very-secret',
                    'user_id': 'user_001',
                    'failure_reason': 'expired_token'
                }
            },
            {
                'level': 'INFO',
                'message': 'Payment processing completed',
                'details': {
                    'customer_id': 'cust_123',
                    'amount': '$299.99',
                    'card_last_four': '9012',
                    'transaction_id': 'txn_987654321',
                    'ssn': '123-45-6789'  # This should be masked
                }
            }
        ]
        
        for log in sensitive_data_logs:
            await self.logger.log_entry({
                'level': log['level'],
                'source': 'APPLICATION',
                'log_type': 'SYSTEM_EVENT',
                'message': log['message'],
                'details': log['details']
            })
            
            print(f"  🎭 Sensitive Data Log: {log['level']} - Contains PII/sensitive data")
            await asyncio.sleep(0.8)
        
        print("✅ Sensitive data handling demo completed")
        print("   (Sensitive data should be automatically detected and masked)")
    
    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring"""
        print("\n⚡ Demo 5: Performance Monitoring")
        print("-" * 50)
        
        performance_events = [
            {
                'level': 'INFO',
                'message': 'Database query performance normal',
                'details': {
                    'query_type': 'SELECT',
                    'execution_time': 250,
                    'rows_returned': 150,
                    'table': 'users'
                }
            },
            {
                'level': 'WARNING',
                'message': 'Slow database query detected',
                'details': {
                    'query_type': 'JOIN',
                    'execution_time': 3500,
                    'threshold': 1000,
                    'affected_tables': ['users', 'orders', 'products']
                }
            },
            {
                'level': 'ERROR',
                'message': 'Database connection timeout',
                'details': {
                    'timeout_seconds': 30,
                    'connection_pool_size': 10,
                    'active_connections': 10,
                    'queue_length': 25
                }
            },
            {
                'level': 'INFO',
                'message': 'Cache hit performance metrics',
                'details': {
                    'cache_hit_ratio': 0.85,
                    'total_requests': 1000,
                    'cache_hits': 850,
                    'cache_misses': 150,
                    'avg_response_time': 45
                }
            }
        ]
        
        for event in performance_events:
            await self.logger.log_entry({
                'level': event['level'],
                'source': 'SYSTEM',
                'log_type': 'PERFORMANCE',
                'message': event['message'],
                'details': event['details']
            })
            
            print(f"  ⚡ Performance: {event['level']} - {event['message']}")
            await asyncio.sleep(0.7)
        
        print("✅ Performance monitoring demo completed")
    
    async def demo_incident_creation(self):
        """Demonstrate automatic incident detection and creation"""
        print("\n🚨 Demo 6: Incident Detection and Creation")
        print("-" * 50)
        
        print("  Sending critical logs to trigger incident detection...")
        
        # Send correlated critical logs that should trigger incident creation
        critical_logs = [
            {
                'level': 'CRITICAL',
                'source': 'DATABASE',
                'log_type': 'ERROR',
                'message': 'Database system_down - Primary database server unreachable',
                'correlation_id': 'incident_demo_001',
                'details': {
                    'server': 'db-primary-01',
                    'error_code': 'CONNECTION_REFUSED',
                    'last_response': '2 minutes ago',
                    'affected_services': ['api', 'web', 'mobile']
                }
            },
            {
                'level': 'ALERT',
                'source': 'NETWORK',
                'log_type': 'ERROR',
                'message': 'Network connectivity failure detected',
                'correlation_id': 'incident_demo_001',
                'details': {
                    'network_segment': '10.0.1.0/24',
                    'packet_loss': '100%',
                    'last_ping': 'failed'
                }
            },
            {
                'level': 'EMERGENCY',
                'source': 'SYSTEM',
                'log_type': 'ERROR',
                'message': 'Complete service failure - All systems down',
                'correlation_id': 'incident_demo_001',
                'details': {
                    'affected_users': 5000,
                    'estimated_downtime': '15 minutes',
                    'financial_impact': 'high'
                }
            }
        ]
        
        for log in critical_logs:
            await self.logger.log_entry(log)
            print(f"  🚨 Critical Event: {log['level']} - {log['message']}")
            await asyncio.sleep(2)
        
        print("  ⏱️  Waiting for incident correlation window...")
        await asyncio.sleep(5)
        
        print("✅ Incident detection demo completed")
        print("   (Check system for automatically created incidents)")
    
    async def demo_frontend_logging_simulation(self):
        """Simulate frontend logging events"""
        print("\n🌐 Demo 7: Frontend Logging Simulation")
        print("-" * 50)
        
        frontend_events = [
            {
                'event_type': 'user_action',
                'action': 'page_load',
                'level': 'INFO',
                'details': {
                    'page_url': 'https://demo.example.com/dashboard',
                    'load_time': 1250,
                    'dom_elements': 145
                }
            },
            {
                'event_type': 'user_action',
                'action': 'button_click',
                'level': 'INFO',
                'details': {
                    'element_id': 'submit_form',
                    'element_text': 'Submit',
                    'form_id': 'user_profile_form'
                }
            },
            {
                'event_type': 'api_call',
                'action': 'api_request',
                'level': 'INFO',
                'details': {
                    'url': '/api/v1/user/profile',
                    'method': 'PUT',
                    'status_code': 200,
                    'duration_ms': 345
                }
            },
            {
                'event_type': 'error',
                'action': 'javascript_error',
                'level': 'ERROR',
                'details': {
                    'message': 'TypeError: Cannot read property of undefined',
                    'filename': 'app.js',
                    'line_number': 127,
                    'stack_trace': 'at validateForm (app.js:127:15)'
                }
            },
            {
                'event_type': 'security',
                'action': 'security_violation',
                'level': 'WARNING',
                'details': {
                    'violation_type': 'rapid_clicking',
                    'click_count': 15,
                    'time_window': '2 seconds'
                }
            }
        ]
        
        for event in frontend_events:
            # Simulate frontend log submission
            frontend_log = {
                'level': event['level'],
                'source': 'FRONTEND',
                'log_type': 'USER_ACTION' if event['event_type'] == 'user_action' else event['event_type'].upper(),
                'message': f"Frontend {event['event_type']}: {event['action']}",
                'session_id': 'demo_session_123',
                'user_id': 'demo_user',
                'details': {
                    **event['details'],
                    'page_url': 'https://demo.example.com/dashboard',
                    'user_agent': 'Demo Browser 1.0',
                    'device_fingerprint': 'demo_device_001'
                }
            }
            
            await self.logger.log_entry(frontend_log)
            print(f"  🌐 Frontend Event: {event['event_type']} - {event['action']}")
            await asyncio.sleep(1)
        
        print("✅ Frontend logging simulation completed")
    
    async def demo_log_analytics(self):
        """Demonstrate log analytics and statistics"""
        print("\n📊 Demo 8: Log Analytics and Statistics")
        print("-" * 50)
        
        # Get system statistics
        stats = self.logger.get_statistics()
        
        print(f"  📈 Total logs processed: {stats['logs_processed']}")
        print(f"  🎫 Incidents created: {stats['incidents_created']}")
        print(f"  ❌ Processing errors: {stats['errors']}")
        print(f"  📥 Current queue size: {stats['queue_size']}")
        print(f"  🎫 ServiceNow enabled: {stats['servicenow_enabled']}")
        print(f"  ⏰ Last processed: {stats['last_processed']}")
        
        # Generate some analytics
        print(f"\n  📊 Log Analytics Summary:")
        print(f"    • Processing rate: ~{stats['logs_processed']/10:.1f} logs/minute")
        print(f"    • Error rate: {stats['errors']/max(stats['logs_processed'], 1)*100:.2f}%")
        print(f"    • Incident rate: {stats['incidents_created']/max(stats['logs_processed'], 1)*100:.2f}%")
        
        print("✅ Log analytics demo completed")
    
    async def demonstrate_full_system(self):
        """Run complete system demonstration"""
        print("🎬 COMPREHENSIVE LOGGING SYSTEM DEMO")
        print("=" * 60)
        print("This demo showcases all features of the logging system:")
        print("  • Basic logging functionality")
        print("  • API request/response logging") 
        print("  • Security event detection")
        print("  • Sensitive data masking")
        print("  • Performance monitoring")
        print("  • Incident detection and creation")
        print("  • Frontend logging simulation")
        print("  • Log analytics and statistics")
        print("=" * 60)
        
        if not await self.initialize_system():
            return False
        
        try:
            # Run all demo scenarios
            await self.demo_basic_logging()
            await self.demo_api_request_logging() 
            await self.demo_security_events()
            await self.demo_sensitive_data_handling()
            await self.demo_performance_monitoring()
            await self.demo_incident_creation()
            await self.demo_frontend_logging_simulation()
            
            # Wait for all processing to complete
            print("\n⏳ Waiting for all logs to be processed...")
            await asyncio.sleep(5)
            
            await self.demo_log_analytics()
            
            print("\n" + "=" * 60)
            print("🎉 DEMO COMPLETED SUCCESSFULLY!")
            print("✅ All logging system features demonstrated")
            print(f"📁 Demo logs saved to: {Path('demo_logs').absolute()}")
            print("📖 Check the log files to see the actual logged data")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            if self.logger:
                await self.logger.stop()

async def main():
    """Main demo function"""
    demo = LoggingDemo()
    success = await demo.demonstrate_full_system()
    
    if success:
        print("\n🎊 Demo completed successfully!")
        print("You can now:")
        print("  1. Review the generated log files in demo_logs/")
        print("  2. Run the test suite: python test_comprehensive_logging.py") 
        print("  3. Start the full application: python enhanced_main_with_comprehensive_logging.py")
    else:
        print("\n💥 Demo encountered issues")
        print("Please check the error messages above and ensure all components are properly installed")

if __name__ == "__main__":
    asyncio.run(main())