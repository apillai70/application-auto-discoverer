"""
Frontend Security Logging Module

This module provides comprehensive security logging functionality for frontend applications,
including authentication events, access violations, and security-related activities.
"""

import logging
import json
import datetime
import hashlib
import os
from typing import Dict, Any, Optional
from enum import Enum


class SecurityEventType(Enum):
    """Enumeration of security event types"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    ACCESS_DENIED = "access_denied"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SESSION_EXPIRED = "session_expired"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_ATTEMPT = "csrf_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"


class SecurityLevel(Enum):
    """Security alert levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityLogger:
    """Main security logging class"""
    
    def __init__(self, log_file: str = "security.log", json_output: bool = True):
        """
        Initialize the security logger
        
        Args:
            log_file: Path to the log file
            json_output: Whether to format logs as JSON
        """
        self.log_file = log_file
        self.json_output = json_output
        self.setup_logger()
    
    def setup_logger(self):
        """Setup the logging configuration"""
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file) if os.path.dirname(self.log_file) else "logs"
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logger
        self.logger = logging.getLogger("frontend_security")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        if self.json_output:
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _get_client_info(self, request_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract client information from request data"""
        client_info = {
            "ip_address": "unknown",
            "user_agent": "unknown",
            "referer": "unknown"
        }
        
        if request_data:
            client_info.update({
                "ip_address": request_data.get("ip_address", "unknown"),
                "user_agent": request_data.get("user_agent", "unknown"),
                "referer": request_data.get("referer", "unknown")
            })
        
        return client_info
    
    def _hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for logging"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        level: SecurityLevel,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_data: Optional[Dict] = None,
        additional_data: Optional[Dict] = None
    ):
        """
        Log a security event
        
        Args:
            event_type: Type of security event
            level: Security level of the event
            message: Human-readable message
            user_id: ID of the user involved (will be hashed)
            session_id: Session ID (will be hashed)
            request_data: Request information (IP, user agent, etc.)
            additional_data: Any additional context data
        """
        timestamp = datetime.datetime.utcnow().isoformat()
        client_info = self._get_client_info(request_data)
        
        log_entry = {
            "timestamp": timestamp,
            "event_type": event_type.value,
            "security_level": level.value,
            "message": message,
            "user_id_hash": self._hash_sensitive_data(user_id) if user_id else None,
            "session_id_hash": self._hash_sensitive_data(session_id) if session_id else None,
            "client_info": client_info,
            "additional_data": additional_data or {}
        }
        
        if self.json_output:
            log_message = json.dumps(log_entry)
        else:
            log_message = f"[{level.value.upper()}] {event_type.value}: {message}"
        
        # Log based on security level
        if level == SecurityLevel.CRITICAL:
            self.logger.critical(log_message)
        elif level == SecurityLevel.HIGH:
            self.logger.error(log_message)
        elif level == SecurityLevel.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def log_authentication_event(
        self,
        event_type: SecurityEventType,
        user_id: str,
        success: bool,
        request_data: Optional[Dict] = None,
        failure_reason: Optional[str] = None
    ):
        """Log authentication-related events"""
        level = SecurityLevel.LOW if success else SecurityLevel.MEDIUM
        message = f"Authentication {event_type.value} for user"
        
        additional_data = {
            "success": success,
            "failure_reason": failure_reason
        }
        
        self.log_security_event(
            event_type=event_type,
            level=level,
            message=message,
            user_id=user_id,
            request_data=request_data,
            additional_data=additional_data
        )
    
    def log_access_violation(
        self,
        resource: str,
        user_id: Optional[str] = None,
        request_data: Optional[Dict] = None,
        attempted_action: Optional[str] = None
    ):
        """Log access violations and unauthorized attempts"""
        message = f"Access denied to resource: {resource}"
        
        additional_data = {
            "resource": resource,
            "attempted_action": attempted_action
        }
        
        self.log_security_event(
            event_type=SecurityEventType.ACCESS_DENIED,
            level=SecurityLevel.HIGH,
            message=message,
            user_id=user_id,
            request_data=request_data,
            additional_data=additional_data
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        description: str,
        user_id: Optional[str] = None,
        request_data: Optional[Dict] = None,
        risk_score: Optional[int] = None
    ):
        """Log suspicious activities"""
        level = SecurityLevel.CRITICAL if risk_score and risk_score > 80 else SecurityLevel.HIGH
        message = f"Suspicious activity detected: {activity_type}"
        
        additional_data = {
            "activity_type": activity_type,
            "description": description,
            "risk_score": risk_score
        }
        
        self.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            level=level,
            message=message,
            user_id=user_id,
            request_data=request_data,
            additional_data=additional_data
        )
    
    def log_data_access(
        self,
        resource_type: str,
        resource_id: str,
        action: str,
        user_id: str,
        request_data: Optional[Dict] = None
    ):
        """Log data access events"""
        message = f"Data access: {action} on {resource_type}"
        
        additional_data = {
            "resource_type": resource_type,
            "resource_id_hash": self._hash_sensitive_data(resource_id),
            "action": action
        }
        
        self.log_security_event(
            event_type=SecurityEventType.DATA_ACCESS,
            level=SecurityLevel.LOW,
            message=message,
            user_id=user_id,
            request_data=request_data,
            additional_data=additional_data
        )
    
    def log_attack_attempt(
        self,
        attack_type: SecurityEventType,
        payload: str,
        request_data: Optional[Dict] = None,
        blocked: bool = True
    ):
        """Log potential attack attempts"""
        message = f"Potential {attack_type.value} detected"
        
        additional_data = {
            "attack_type": attack_type.value,
            "payload_hash": self._hash_sensitive_data(payload),
            "blocked": blocked,
            "payload_length": len(payload)
        }
        
        self.log_security_event(
            event_type=attack_type,
            level=SecurityLevel.CRITICAL,
            message=message,
            request_data=request_data,
            additional_data=additional_data
        )


# Global security logger instance
security_logger = SecurityLogger(log_file="logs/frontend_security.log")


# Convenience functions
def log_login_success(user_id: str, request_data: Optional[Dict] = None):
    """Quick function to log successful login"""
    security_logger.log_authentication_event(
        SecurityEventType.LOGIN_SUCCESS, user_id, True, request_data
    )


def log_login_failure(user_id: str, reason: str, request_data: Optional[Dict] = None):
    """Quick function to log failed login"""
    security_logger.log_authentication_event(
        SecurityEventType.LOGIN_FAILURE, user_id, False, request_data, reason
    )


def log_access_denied(resource: str, user_id: Optional[str] = None, request_data: Optional[Dict] = None):
    """Quick function to log access denial"""
    security_logger.log_access_violation(resource, user_id, request_data)


def log_xss_attempt(payload: str, request_data: Optional[Dict] = None, blocked: bool = True):
    """Quick function to log XSS attempts"""
    security_logger.log_attack_attempt(
        SecurityEventType.XSS_ATTEMPT, payload, request_data, blocked
    )


def log_csrf_attempt(request_data: Optional[Dict] = None, blocked: bool = True):
    """Quick function to log CSRF attempts"""
    security_logger.log_attack_attempt(
        SecurityEventType.CSRF_ATTEMPT, "CSRF token mismatch", request_data, blocked
    )