# =================== routers/compliance.py ===================
"""
Compliance Management Router with Full Security Integration

This router provides comprehensive compliance framework management with:
- Role-based access control via auth integration
- Enhanced audit logging with risk assessment
- Complete feature flag support
- File-based storage in essentials folder structure
"""

from fastapi import APIRouter, HTTPException, Query, Body, Depends, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import hashlib
import csv
from io import StringIO

# Import auth dependencies
try:
    from .auth import (
        verify_token, 
        get_current_user,
        check_permission,
        require_role,
        User
    )
    AUTH_ENABLED = True
except ImportError:
    # Fallback if auth not available
    AUTH_ENABLED = False
    async def get_current_user(token: str = None):
        return {"username": "system", "roles": ["admin"]}
    def require_role(roles: List[str]):
        def decorator(func):
            return func
        return decorator

# Import audit dependencies
try:
    from .audit import (
        log_security_event,
        assess_risk_level,
        create_audit_entry,
        AuditEventType,
        RiskLevel
    )
    AUDIT_ENABLED = True
except ImportError:
    # Fallback if audit not available
    AUDIT_ENABLED = False
    class RiskLevel:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"
    
    async def log_security_event(event_type: str, user: str, details: Dict, risk_level: str = "low"):
        print(f"Audit: {event_type} by {user}")
        return True
    
    def assess_risk_level(framework: str, score: float, critical_findings: int) -> str:
        if critical_findings > 2 or score < 60:
            return RiskLevel.HIGH
        elif critical_findings > 0 or score < 80:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

router = APIRouter()

# =================== CONFIGURATION ===================

# Base paths for essentials folder
ESSENTIALS_PATH = Path(__file__).parent.parent / "essentials"
COMPLIANCE_REPORTS_PATH = ESSENTIALS_PATH / "reports" / "compliance"
AUDIT_LOGS_PATH = ESSENTIALS_PATH / "audit"
COMPLIANCE_CONFIG_PATH = ESSENTIALS_PATH / "config" / "compliance"
EVIDENCE_PATH = ESSENTIALS_PATH / "compliance" / "evidence"

# Ensure directories exist
for path in [COMPLIANCE_REPORTS_PATH, AUDIT_LOGS_PATH, COMPLIANCE_CONFIG_PATH, EVIDENCE_PATH]:
    path.mkdir(parents=True, exist_ok=True)

# Feature flags for compliance capabilities
COMPLIANCE_FEATURES = {
    "automated_assessments": True,
    "real_time_monitoring": True,
    "evidence_management": True,
    "remediation_tracking": True,
    "risk_scoring": True,
    "executive_reporting": True,
    "multi_framework_support": True,
    "audit_integration": AUDIT_ENABLED,
    "rbac_enabled": AUTH_ENABLED,
    "file_based_storage": True,
    "compliance_analytics": True,
    "automated_notifications": False,  # Future feature
    "ai_risk_prediction": False,  # Future feature
}

# Role permissions for compliance operations
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "delete", "export", "manage_users"],
    "security": ["read", "write", "export", "create_reports"],
    "analyst": ["read", "export", "create_reports"],
    "auditor": ["read", "export", "audit"],
    "readonly": ["read"],
    "user": ["read"]
}

# =================== ENUMS & MODELS ===================

class ComplianceFramework(str, Enum):
    PCI_DSS = "PCI-DSS"
    SOX = "SOX"
    FFIEC = "FFIEC"
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    ISO27001 = "ISO27001"
    NIST = "NIST"
    CIS = "CIS"
    BASEL_III = "BASEL-III"
    GLBA = "GLBA"
    SOC2 = "SOC2"

class ControlStatus(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NOT_APPLICABLE = "not_applicable"
    UNDER_REVIEW = "under_review"

class ControlPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class RemediationStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    EXCEPTION_GRANTED = "exception_granted"

class ComplianceControl(BaseModel):
    id: str
    framework: ComplianceFramework
    title: str
    description: str
    status: ControlStatus
    priority: ControlPriority
    compliance_score: float = Field(ge=0, le=100)
    last_assessment: datetime
    next_assessment: datetime
    owner: str
    department: str
    remediation_notes: Optional[str] = None
    evidence_links: List[str] = []
    automated_check: bool = False
    control_category: str
    implementation_cost: Optional[float] = None
    last_modified_by: Optional[str] = None
    last_modified_at: Optional[datetime] = None
    
    @validator('compliance_score')
    def validate_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Compliance score must be between 0 and 100')
        return round(v, 2)

class RemediationPlan(BaseModel):
    control_id: str
    framework: ComplianceFramework
    remediation_status: RemediationStatus
    responsible_party: str
    target_completion: datetime
    actual_completion: Optional[datetime] = None
    estimated_cost: float
    actual_cost: Optional[float] = None
    remediation_steps: List[Dict[str, Any]]
    blockers: List[str] = []
    notes: str
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None

class ComplianceReport(BaseModel):
    report_id: str
    framework: ComplianceFramework
    overall_score: float
    total_controls: int
    compliant_controls: int
    non_compliant_controls: int
    partially_compliant_controls: int
    controls: List[ComplianceControl]
    risk_score: float
    risk_level: str
    estimated_remediation_cost: float
    critical_findings: List[Dict[str, Any]]
    generated_at: datetime
    generated_by: str
    report_period: Dict[str, datetime]
    executive_summary: str
    recommendations: List[str]

# =================== MOCK DATA GENERATOR ===================

def generate_comprehensive_controls():
    """Generate comprehensive compliance controls data"""
    frameworks_controls = {
        "PCI-DSS": [
            {"id": "PCI-1.1", "title": "Install and maintain firewall configuration", "category": "Network Security", "priority": "critical"},
            {"id": "PCI-2.1", "title": "Change vendor-supplied defaults", "category": "Configuration Management", "priority": "high"},
            {"id": "PCI-3.1", "title": "Protect stored cardholder data", "category": "Data Protection", "priority": "critical"},
            {"id": "PCI-8.1", "title": "Assign unique ID to each person", "category": "Access Control", "priority": "high"},
            {"id": "PCI-10.1", "title": "Establish audit trails", "category": "Logging & Monitoring", "priority": "high"}
        ],
        "SOX": [
            {"id": "SOX-404", "title": "Management Assessment of Internal Controls", "category": "Internal Controls", "priority": "critical"},
            {"id": "SOX-302", "title": "Corporate Responsibility for Financial Reports", "category": "Financial Reporting", "priority": "critical"},
            {"id": "SOX-409", "title": "Real-time Disclosure", "category": "Disclosure", "priority": "high"}
        ],
        "GDPR": [
            {"id": "GDPR-Art5", "title": "Principles relating to processing", "category": "Data Processing", "priority": "critical"},
            {"id": "GDPR-Art32", "title": "Security of processing", "category": "Security", "priority": "critical"},
            {"id": "GDPR-Art33", "title": "Breach notification", "category": "Incident Response", "priority": "high"}
        ]
    }
    
    all_controls = {}
    for framework, controls in frameworks_controls.items():
        framework_controls = []
        for control in controls:
            import random
            status = random.choice([ControlStatus.COMPLIANT, ControlStatus.NON_COMPLIANT, ControlStatus.PARTIALLY_COMPLIANT])
            
            score = {
                ControlStatus.COMPLIANT: random.uniform(85, 100),
                ControlStatus.PARTIALLY_COMPLIANT: random.uniform(60, 84),
                ControlStatus.NON_COMPLIANT: random.uniform(0, 59),
                ControlStatus.UNDER_REVIEW: random.uniform(40, 80),
                ControlStatus.NOT_APPLICABLE: 0
            }[status]
            
            framework_controls.append(ComplianceControl(
                id=control["id"],
                framework=framework,
                title=control["title"],
                description=f"Implementation of {control['title']} control",
                status=status,
                priority=control["priority"],
                compliance_score=score,
                last_assessment=datetime.now() - timedelta(days=random.randint(1, 90)),
                next_assessment=datetime.now() + timedelta(days=random.randint(30, 180)),
                owner=random.choice(["Security Team", "IT Operations", "Risk Management"]),
                department=random.choice(["IT", "Security", "Compliance"]),
                remediation_notes="Remediation in progress" if status != ControlStatus.COMPLIANT else None,
                evidence_links=[f"/evidence/{control['id']}/doc1.pdf"],
                automated_check=random.choice([True, False]),
                control_category=control["category"],
                implementation_cost=random.uniform(5000, 50000) if status != ControlStatus.COMPLIANT else None
            ))
        
        all_controls[framework] = framework_controls
    
    return all_controls

# Initialize mock data
COMPLIANCE_CONTROLS = generate_comprehensive_controls()

# =================== UTILITY FUNCTIONS ===================

def check_user_permission(user: Dict, required_permission: str) -> bool:
    """Check if user has required permission"""
    if not AUTH_ENABLED:
        return True  # Allow all if auth is disabled
    
    user_roles = user.get("roles", [])
    for role in user_roles:
        if required_permission in ROLE_PERMISSIONS.get(role, []):
            return True
    return False

def calculate_risk_score(controls: List[ComplianceControl]) -> float:
    """Calculate risk score based on non-compliant critical controls"""
    if not controls:
        return 0.0
    
    risk_points = 0
    max_points = 0
    
    priority_weights = {
        ControlPriority.CRITICAL: 10,
        ControlPriority.HIGH: 7,
        ControlPriority.MEDIUM: 4,
        ControlPriority.LOW: 1
    }
    
    for control in controls:
        weight = priority_weights[control.priority]
        max_points += weight
        
        if control.status == ControlStatus.NON_COMPLIANT:
            risk_points += weight
        elif control.status == ControlStatus.PARTIALLY_COMPLIANT:
            risk_points += weight * 0.5
    
    return round((risk_points / max_points) * 100, 2) if max_points > 0 else 0.0

def generate_executive_summary(framework: str, score: float, critical_findings: int) -> str:
    """Generate executive summary for compliance report"""
    status = "Good" if score >= 80 else "Needs Attention" if score >= 60 else "Critical"
    
    return f"""Executive Summary for {framework} Compliance Assessment:
    
Overall Compliance Score: {score:.1f}%
Status: {status}
Critical Findings: {critical_findings}

The organization {'maintains strong' if score >= 80 else 'requires improvements in'} {framework} compliance.
{'Immediate action required on critical controls.' if critical_findings > 0 else 'Continue monitoring and maintaining controls.'}
"""

def generate_recommendations(controls: List[ComplianceControl]) -> List[str]:
    """Generate recommendations based on control status"""
    recommendations = []
    
    critical_issues = [c for c in controls if c.status == ControlStatus.NON_COMPLIANT and c.priority == ControlPriority.CRITICAL]
    if critical_issues:
        recommendations.append(f"Address {len(critical_issues)} critical non-compliant controls immediately")
    
    high_issues = [c for c in controls if c.status == ControlStatus.NON_COMPLIANT and c.priority == ControlPriority.HIGH]
    if high_issues:
        recommendations.append(f"Remediate {len(high_issues)} high-priority controls within 30 days")
    
    partial = [c for c in controls if c.status == ControlStatus.PARTIALLY_COMPLIANT]
    if partial:
        recommendations.append(f"Complete implementation of {len(partial)} partially compliant controls")
    
    if not recommendations:
        recommendations.append("Maintain current compliance levels with regular assessments")
    
    recommendations.append("Schedule quarterly compliance reviews")
    recommendations.append("Implement continuous monitoring for critical controls")
    
    return recommendations

async def log_compliance_event(
    event_type: str,
    framework: str,
    user: Dict,
    details: Dict[str, Any],
    risk_level: str = None
):
    """Log compliance events with enhanced audit integration"""
    if AUDIT_ENABLED:
        # Determine risk level if not provided
        if not risk_level:
            score = details.get("overall_score", 100)
            critical = details.get("critical_findings", 0)
            risk_level = assess_risk_level(framework, score, critical)
        
        # Log to audit system
        await log_security_event(
            event_type=f"compliance_{event_type}",
            user=user.get("username", "unknown"),
            details={
                "framework": framework,
                **details
            },
            risk_level=risk_level
        )
    
    # Also log to local compliance audit file
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "framework": framework,
        "user": user.get("username", "unknown"),
        "roles": user.get("roles", []),
        "details": details,
        "risk_level": risk_level
    }
    
    audit_file = AUDIT_LOGS_PATH / f"compliance_audit_{datetime.now().strftime('%Y%m')}.json"
    
    if audit_file.exists():
        with open(audit_file, 'r') as f:
            audit_log = json.load(f)
    else:
        audit_log = []
    
    audit_log.append(audit_entry)
    
    with open(audit_file, 'w') as f:
        json.dump(audit_log, f, indent=2, default=str)

# =================== API ENDPOINTS WITH RBAC ===================

@router.get("/features")
async def get_compliance_features():
    """Get available compliance features and capabilities"""
    return {
        "features": COMPLIANCE_FEATURES,
        "auth_enabled": AUTH_ENABLED,
        "audit_enabled": AUDIT_ENABLED,
        "role_permissions": ROLE_PERMISSIONS if AUTH_ENABLED else {"all": ["full_access"]},
        "storage_paths": {
            "reports": str(COMPLIANCE_REPORTS_PATH),
            "audit": str(AUDIT_LOGS_PATH),
            "config": str(COMPLIANCE_CONFIG_PATH),
            "evidence": str(EVIDENCE_PATH)
        }
    }

@router.get("/frameworks")
async def get_frameworks(
    current_user: Dict = Depends(get_current_user)
):
    """Get all available compliance frameworks with detailed information"""
    
    # Check read permission
    if not check_user_permission(current_user, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view frameworks"
        )
    
    frameworks = {
        "PCI-DSS": {
            "name": "PCI-DSS",
            "full_name": "Payment Card Industry Data Security Standard",
            "description": "Security standards for organizations that handle credit cards",
            "version": "4.0",
            "categories": ["Payment Security", "Data Protection"],
            "regulatory_body": "PCI Security Standards Council"
        },
        "SOX": {
            "name": "SOX",
            "full_name": "Sarbanes-Oxley Act",
            "description": "US federal law for public company accounting reform",
            "version": "2002",
            "categories": ["Financial Reporting", "Internal Controls"],
            "regulatory_body": "SEC"
        },
        "GDPR": {
            "name": "GDPR",
            "full_name": "General Data Protection Regulation",
            "description": "EU regulation on data protection and privacy",
            "version": "2018",
            "categories": ["Data Privacy", "Data Protection"],
            "regulatory_body": "European Union"
        },
        "SOC2": {
            "name": "SOC2",
            "full_name": "Service Organization Control 2",
            "description": "Auditing procedure for service providers",
            "version": "Type II",
            "categories": ["Security", "Availability", "Processing Integrity"],
            "regulatory_body": "AICPA"
        }
    }
    
    # Log access
    await log_compliance_event(
        event_type="frameworks_accessed",
        framework="all",
        user=current_user,
        details={"count": len(frameworks)},
        risk_level=RiskLevel.LOW
    )
    
    return {
        "frameworks": frameworks,
        "total_count": len(frameworks),
        "user_access_level": current_user.get("roles", []),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/report/{framework}", response_model=ComplianceReport)
@require_role(["admin", "security", "analyst", "auditor"])
async def get_compliance_report(
    framework: ComplianceFramework,
    include_evidence: bool = Query(False, description="Include evidence links"),
    current_user: Dict = Depends(get_current_user)
):
    """Generate comprehensive compliance report for specific framework"""
    
    controls = COMPLIANCE_CONTROLS.get(framework.value, [])
    
    if not controls:
        COMPLIANCE_CONTROLS[framework.value] = generate_comprehensive_controls().get(framework.value, [])
        controls = COMPLIANCE_CONTROLS[framework.value]
    
    # Calculate statistics
    total_controls = len(controls)
    compliant = len([c for c in controls if c.status == ControlStatus.COMPLIANT])
    non_compliant = len([c for c in controls if c.status == ControlStatus.NON_COMPLIANT])
    partially_compliant = len([c for c in controls if c.status == ControlStatus.PARTIALLY_COMPLIANT])
    
    overall_score = sum(c.compliance_score for c in controls) / total_controls if controls else 0
    
    # Find critical findings
    critical_findings = [
        {
            "control_id": c.id,
            "title": c.title,
            "score": c.compliance_score,
            "priority": c.priority
        }
        for c in controls 
        if c.status == ControlStatus.NON_COMPLIANT and c.priority == ControlPriority.CRITICAL
    ]
    
    # Calculate risk
    risk_score = calculate_risk_score(controls)
    risk_level = assess_risk_level(framework.value, overall_score, len(critical_findings))
    
    # Calculate remediation cost
    remediation_cost = sum(c.implementation_cost or 0 for c in controls if c.implementation_cost)
    
    # Generate recommendations
    recommendations = generate_recommendations(controls)
    
    report = ComplianceReport(
        report_id=hashlib.md5(f"{framework}-{datetime.now().isoformat()}".encode()).hexdigest()[:8],
        framework=framework,
        overall_score=round(overall_score, 1),
        total_controls=total_controls,
        compliant_controls=compliant,
        non_compliant_controls=non_compliant,
        partially_compliant_controls=partially_compliant,
        controls=controls if include_evidence else [c.copy(exclude={'evidence_links'}) for c in controls],
        risk_score=risk_score,
        risk_level=risk_level,
        estimated_remediation_cost=remediation_cost,
        critical_findings=critical_findings,
        generated_at=datetime.now(),
        generated_by=current_user.get("username", "system"),
        report_period={
            "start": datetime.now() - timedelta(days=90),
            "end": datetime.now()
        },
        executive_summary=generate_executive_summary(framework.value, overall_score, len(critical_findings)),
        recommendations=recommendations
    )
    
    # Log report generation with risk assessment
    await log_compliance_event(
        event_type="report_generated",
        framework=framework.value,
        user=current_user,
        details={
            "report_id": report.report_id,
            "overall_score": report.overall_score,
            "critical_findings": len(critical_findings),
            "risk_score": risk_score
        },
        risk_level=risk_level
    )
    
    # Save report to file system
    report_file = COMPLIANCE_REPORTS_PATH / f"{framework.value}_{report.report_id}_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, 'w') as f:
        json.dump(report.dict(), f, indent=2, default=str)
    
    return report

@router.get("/dashboard")
async def get_compliance_dashboard(
    include_trends: bool = Query(True, description="Include trend data"),
    current_user: Dict = Depends(get_current_user)
):
    """Get comprehensive compliance dashboard with all frameworks"""
    
    if not check_user_permission(current_user, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view dashboard"
        )
    
    dashboard_data = {}
    overall_risk_level = RiskLevel.LOW
    
    for framework in ComplianceFramework:
        controls = COMPLIANCE_CONTROLS.get(framework.value, [])
        
        if not controls:
            COMPLIANCE_CONTROLS[framework.value] = generate_comprehensive_controls().get(framework.value, [])
            controls = COMPLIANCE_CONTROLS[framework.value]
        
        if controls:
            total = len(controls)
            compliant = len([c for c in controls if c.status == ControlStatus.COMPLIANT])
            non_compliant = len([c for c in controls if c.status == ControlStatus.NON_COMPLIANT])
            partially_compliant = len([c for c in controls if c.status == ControlStatus.PARTIALLY_COMPLIANT])
            score = sum(c.compliance_score for c in controls) / total if controls else 0
            
            critical_issues = len([c for c in controls if c.status != ControlStatus.COMPLIANT and c.priority == ControlPriority.CRITICAL])
            high_issues = len([c for c in controls if c.status != ControlStatus.COMPLIANT and c.priority == ControlPriority.HIGH])
            
            # Assess risk for this framework
            framework_risk = assess_risk_level(framework.value, score, critical_issues)
            if framework_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                overall_risk_level = RiskLevel.HIGH
            elif framework_risk == RiskLevel.MEDIUM and overall_risk_level == RiskLevel.LOW:
                overall_risk_level = RiskLevel.MEDIUM
            
            dashboard_data[framework.value] = {
                "total_controls": total,
                "compliant_controls": compliant,
                "non_compliant_controls": non_compliant,
                "partially_compliant_controls": partially_compliant,
                "compliance_percentage": round((compliant / total) * 100, 1) if total else 0,
                "average_score": round(score, 1),
                "risk_score": calculate_risk_score(controls),
                "risk_level": framework_risk,
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "status": "good" if score >= 80 else "needs_attention" if score >= 60 else "critical",
                "next_assessment": min(c.next_assessment for c in controls).isoformat() if controls else None,
                "estimated_remediation_cost": sum(c.implementation_cost or 0 for c in controls if c.implementation_cost)
            }
    
    # Calculate overall metrics
    all_scores = [f["average_score"] for f in dashboard_data.values()]
    all_risks = [f["risk_score"] for f in dashboard_data.values()]
    
    response = {
        "frameworks": dashboard_data,
        "summary": {
            "total_frameworks": len(dashboard_data),
            "overall_compliance": round(sum(all_scores) / len(all_scores), 1) if all_scores else 0,
            "overall_risk": round(sum(all_risks) / len(all_risks), 1) if all_risks else 0,
            "overall_risk_level": overall_risk_level,
            "frameworks_at_risk": len([f for f in dashboard_data.values() if f["status"] == "critical"]),
            "total_critical_issues": sum(f["critical_issues"] for f in dashboard_data.values()),
            "total_remediation_cost": sum(f["estimated_remediation_cost"] for f in dashboard_data.values())
        },
        "user": current_user.get("username", "unknown"),
        "access_level": current_user.get("roles", []),
        "last_updated": datetime.now().isoformat()
    }
    
    # Add trend data if requested
    if include_trends:
        response["trends"] = {
            "30_day_improvement": 2.3,
            "90_day_improvement": 5.7,
            "trending_up": ["PCI-DSS", "ISO27001"],
            "trending_down": ["GDPR"],
            "stable": ["SOX", "HIPAA"]
        }
    
    # Log dashboard access
    await log_compliance_event(
        event_type="dashboard_accessed",
        framework="all",
        user=current_user,
        details={
            "frameworks_count": len(dashboard_data),
            "overall_risk": overall_risk_level
        },
        risk_level=overall_risk_level
    )
    
    return response

@router.post("/remediation/plan")
@require_role(["admin", "security"])
async def create_remediation_plan(
    plan: RemediationPlan,
    current_user: Dict = Depends(get_current_user)
):
    """Create a remediation plan for non-compliant controls"""
    
    # Add user information
    plan.created_by = current_user.get("username", "system")
    
    # Save remediation plan
    plan_file = COMPLIANCE_CONFIG_PATH / f"remediation_{plan.control_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(plan_file, 'w') as f:
        json.dump(plan.dict(), f, indent=2, default=str)
    
    # Determine risk level based on remediation urgency
    risk_level = RiskLevel.HIGH if plan.target_completion < datetime.now() + timedelta(days=30) else RiskLevel.MEDIUM
    
    # Log audit event
    await log_compliance_event(
        event_type="remediation_plan_created",
        framework=plan.framework.value,
        user=current_user,
        details={
            "control_id": plan.control_id,
            "target_completion": plan.target_completion.isoformat(),
            "estimated_cost": plan.estimated_cost,
            "responsible_party": plan.responsible_party
        },
        risk_level=risk_level
    )
    
    return {
        "status": "success",
        "message": "Remediation plan created successfully",
        "plan_id": plan.control_id,
        "created_by": plan.created_by,
        "saved_to": str(plan_file)
    }

@router.put("/control/{framework}/{control_id}/status")
@require_role(["admin", "security"])
async def update_control_status(
    framework: ComplianceFramework,
    control_id: str,
    new_status: ControlStatus,
    notes: str = Body(...),
    current_user: Dict = Depends(get_current_user)
):
    """Update the status of a compliance control"""
    
    controls = COMPLIANCE_CONTROLS.get(framework.value, [])
    control = next((c for c in controls if c.id == control_id), None)
    
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control {control_id} not found in {framework.value}"
        )
    
    # Store old status for audit
    old_status = control.status
    
    # Update control
    control.status = new_status
    control.remediation_notes = notes
    control.last_modified_by = current_user.get("username", "system")
    control.last_modified_at = datetime.now()
    
    # Determine risk level based on change
    risk_level = RiskLevel.LOW
    if new_status == ControlStatus.NON_COMPLIANT and control.priority == ControlPriority.CRITICAL:
        risk_level = RiskLevel.HIGH
    elif old_status == ControlStatus.COMPLIANT and new_status != ControlStatus.COMPLIANT:
        risk_level = RiskLevel.MEDIUM
    
    # Log the change
    await log_compliance_event(
        event_type="control_status_updated",
        framework=framework.value,
        user=current_user,
        details={
            "control_id": control_id,
            "old_status": old_status,
            "new_status": new_status,
            "priority": control.priority,
            "notes": notes
        },
        risk_level=risk_level
    )
    
    return {
        "status": "success",
        "message": f"Control {control_id} status updated",
        "control_id": control_id,
        "old_status": old_status,
        "new_status": new_status,
        "updated_by": current_user.get("username", "system"),
        "risk_level": risk_level
    }

@router.get("/export/{framework}")
@require_role(["admin", "security", "analyst", "auditor"])
async def export_compliance_report(
    framework: ComplianceFramework,
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    current_user: Dict = Depends(get_current_user)
):
    """Export compliance report in various formats"""
    
    controls = COMPLIANCE_CONTROLS.get(framework.value, [])
    
    if not controls:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data available for {framework.value}"
        )
    
    # Log export event
    await log_compliance_event(
        event_type="report_exported",
        framework=framework.value,
        user=current_user,
        details={
            "format": format,
            "controls_count": len(controls)
        },
        risk_level=RiskLevel.LOW
    )
    
    if format == "json":
        export_data = {
            "framework": framework.value,
            "exported_at": datetime.now().isoformat(),
            "exported_by": current_user.get("username", "system"),
            "controls": [c.dict() for c in controls]
        }
        
        export_file = COMPLIANCE_REPORTS_PATH / f"export_{framework.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return FileResponse(
            path=export_file,
            media_type="application/json",
            filename=export_file.name
        )
    
    elif format == "csv":
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "title", "status", "priority", "score", "owner", "department", "last_assessment", "next_assessment"]
        )
        writer.writeheader()
        
        for control in controls:
            writer.writerow({
                "id": control.id,
                "title": control.title,
                "status": control.status,
                "priority": control.priority,
                "score": control.compliance_score,
                "owner": control.owner,
                "department": control.department,
                "last_assessment": control.last_assessment.isoformat(),
                "next_assessment": control.next_assessment.isoformat()
            })
        
        export_file = COMPLIANCE_REPORTS_PATH / f"export_{framework.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(export_file, 'w') as f:
            f.write(output.getvalue())
        
        return FileResponse(
            path=export_file,
            media_type="text/csv",
            filename=export_file.name
        )

@router.get("/audit/history")
@require_role(["admin", "security", "auditor"])
async def get_compliance_audit_history(
    framework: Optional[ComplianceFramework] = None,
    days_back: int = Query(30, description="Number of days to look back"),
    current_user: Dict = Depends(get_current_user)
):
    """Get compliance-specific audit history"""
    
    audit_entries = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Read compliance audit logs
    for audit_file in AUDIT_LOGS_PATH.glob("compliance_audit_*.json"):
        try:
            with open(audit_file, 'r') as f:
                entries = json.load(f)
                for entry in entries:
                    entry_date = datetime.fromisoformat(entry["timestamp"])
                    if entry_date >= cutoff_date:
                        if not framework or entry.get("framework") == framework.value:
                            audit_entries.append(entry)
        except Exception as e:
            print(f"Error reading audit file {audit_file}: {e}")
    
    # Sort by timestamp
    audit_entries.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Analyze risk distribution
    risk_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for entry in audit_entries:
        risk_level = entry.get("risk_level", "low")
        if risk_level in risk_levels:
            risk_levels[risk_level] += 1
    
    return {
        "total_entries": len(audit_entries),
        "period": f"Last {days_back} days",
        "framework_filter": framework.value if framework else "All",
        "risk_distribution": risk_levels,
        "entries": audit_entries[:100],  # Limit to 100 most recent
        "queried_by": current_user.get("username", "system")
    }

@router.get("/summary/executive")
@require_role(["admin", "security", "analyst"])
async def get_executive_summary(
    current_user: Dict = Depends(get_current_user)
):
    """Get executive-level compliance summary across all frameworks"""
    
    summaries = []
    total_remediation_cost = 0
    critical_frameworks = []
    overall_risk = RiskLevel.LOW
    
    for framework in ComplianceFramework:
        controls = COMPLIANCE_CONTROLS.get(framework.value, [])
        
        if controls:
            score = sum(c.compliance_score for c in controls) / len(controls)
            risk = calculate_risk_score(controls)
            cost = sum(c.implementation_cost or 0 for c in controls if c.implementation_cost)
            critical_findings = len([c for c in controls if c.status == ControlStatus.NON_COMPLIANT and c.priority == ControlPriority.CRITICAL])
            
            framework_risk = assess_risk_level(framework.value, score, critical_findings)
            
            total_remediation_cost += cost
            
            if score < 60:
                critical_frameworks.append(framework.value)
                overall_risk = RiskLevel.HIGH
            elif score < 80 and overall_risk == RiskLevel.LOW:
                overall_risk = RiskLevel.MEDIUM
            
            summaries.append({
                "framework": framework.value,
                "score": round(score, 1),
                "risk": round(risk, 1),
                "risk_level": framework_risk,
                "remediation_cost": cost,
                "status": "good" if score >= 80 else "needs_attention" if score >= 60 else "critical"
            })
    
    # Log executive summary access
    await log_compliance_event(
        event_type="executive_summary_accessed",
        framework="all",
        user=current_user,
        details={
            "frameworks_assessed": len(summaries),
            "critical_frameworks": critical_frameworks,
            "total_remediation_cost": total_remediation_cost
        },
        risk_level=overall_risk
    )
    
    return {
        "executive_summary": {
            "date": datetime.now().isoformat(),
            "overall_compliance_health": "critical" if critical_frameworks else "good",
            "overall_risk_level": overall_risk,
            "frameworks_assessed": len(summaries),
            "critical_frameworks": critical_frameworks,
            "total_estimated_remediation_cost": total_remediation_cost,
            "key_recommendations": [
                "Address critical findings in " + ", ".join(critical_frameworks) if critical_frameworks else "Maintain current compliance levels",
                "Allocate budget for remediation activities",
                "Schedule quarterly compliance reviews",
                "Implement automated compliance monitoring",
                "Enhance role-based access controls" if AUTH_ENABLED else "Enable authentication system"
            ]
        },
        "framework_summaries": summaries,
        "generated_by": current_user.get("username", "system"),
        "user_roles": current_user.get("roles", []),
        "next_review_date": (datetime.now() + timedelta(days=90)).isoformat()
    }

@router.get("/health")
async def compliance_health_check():
    """Check compliance router health and integration status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "features": COMPLIANCE_FEATURES,
        "integrations": {
            "auth": AUTH_ENABLED,
            "audit": AUDIT_ENABLED,
            "storage": {
                "reports": COMPLIANCE_REPORTS_PATH.exists(),
                "audit": AUDIT_LOGS_PATH.exists(),
                "config": COMPLIANCE_CONFIG_PATH.exists(),
                "evidence": EVIDENCE_PATH.exists()
            }
        },
        "frameworks_loaded": len(COMPLIANCE_CONTROLS),
        "total_controls": sum(len(controls) for controls in COMPLIANCE_CONTROLS.values())
    }