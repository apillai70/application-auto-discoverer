# =================== routers/compliance.py ===================
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any  # ← ADD THIS LINE
from enum import Enum
from datetime import datetime

router = APIRouter()

class ComplianceFramework(str, Enum):
    PCI_DSS = "PCI-DSS"
    SOX = "SOX"
    FFIEC = "FFIEC"
    GDPR = "GDPR"
    HIPAA = "HIPAA"
    ISO27001 = "ISO27001"

class ComplianceControl(BaseModel):
    id: str
    framework: ComplianceFramework
    title: str
    description: str
    status: str
    compliance_score: float
    last_assessment: str
    remediation_notes: Optional[str] = None

class ComplianceReport(BaseModel):
    framework: ComplianceFramework
    overall_score: float
    total_controls: int
    compliant_controls: int
    non_compliant_controls: int
    controls: List[ComplianceControl]
    generated_at: str

# Mock compliance data
COMPLIANCE_CONTROLS = {
    "PCI-DSS": [
        {
            "id": "PCI-1.1",
            "framework": "PCI-DSS",
            "title": "Install and maintain firewall configuration",
            "description": "Establish firewall and router configuration standards",
            "status": "compliant",
            "compliance_score": 95.0,
            "last_assessment": datetime.now().isoformat(),
            "remediation_notes": None
        },
        {
            "id": "PCI-2.1", 
            "framework": "PCI-DSS",
            "title": "Change vendor-supplied defaults",
            "description": "Always change vendor-supplied defaults before installing system",
            "status": "non_compliant",
            "compliance_score": 45.0,
            "last_assessment": datetime.now().isoformat(),
            "remediation_notes": "Default passwords found on 3 systems"
        }
    ],
    "SOX": [
        {
            "id": "SOX-404",
            "framework": "SOX",
            "title": "Management Assessment of Internal Controls",
            "description": "Annual assessment of internal control effectiveness",
            "status": "compliant",
            "compliance_score": 88.0,
            "last_assessment": datetime.now().isoformat(),
            "remediation_notes": None
        }
    ]
}

@router.get("/frameworks")
async def get_frameworks():
    """Get available compliance frameworks"""
    return {
        "frameworks": [
            {"name": "PCI-DSS", "description": "Payment Card Industry Data Security Standard"},
            {"name": "SOX", "description": "Sarbanes-Oxley Act"},
            {"name": "FFIEC", "description": "Federal Financial Institutions Examination Council"},
            {"name": "GDPR", "description": "General Data Protection Regulation"},
            {"name": "HIPAA", "description": "Health Insurance Portability and Accountability Act"},
            {"name": "ISO27001", "description": "Information Security Management System"}
        ]
    }

@router.get("/report/{framework}", response_model=ComplianceReport)
async def get_compliance_report(framework: ComplianceFramework):
    """Get compliance report for specific framework"""
    controls = COMPLIANCE_CONTROLS.get(framework.value, [])
    
    if not controls:
        raise HTTPException(status_code=404, detail=f"No data available for {framework.value}")
    
    total_controls = len(controls)
    compliant_controls = len([c for c in controls if c["status"] == "compliant"])
    non_compliant_controls = total_controls - compliant_controls
    
    overall_score = sum(c["compliance_score"] for c in controls) / total_controls if controls else 0
    
    return ComplianceReport(
        framework=framework,
        overall_score=round(overall_score, 1),
        total_controls=total_controls,
        compliant_controls=compliant_controls,
        non_compliant_controls=non_compliant_controls,
        controls=controls,
        generated_at=datetime.now().isoformat()
    )

@router.get("/dashboard")
async def get_compliance_dashboard():
    """Get compliance dashboard overview"""
    dashboard_data = {}
    
    for framework, controls in COMPLIANCE_CONTROLS.items():
        total = len(controls)
        compliant = len([c for c in controls if c["status"] == "compliant"])
        score = sum(c["compliance_score"] for c in controls) / total if controls else 0
        
        dashboard_data[framework] = {
            "total_controls": total,
            "compliant_controls": compliant,
            "compliance_percentage": round((compliant / total) * 100, 1) if total else 0,
            "average_score": round(score, 1),
            "status": "good" if score >= 80 else "needs_attention" if score >= 60 else "critical"
        }
    
    return {
        "frameworks": dashboard_data,
        "summary": {
            "total_frameworks": len(dashboard_data),
            "overall_compliance": round(sum(f["average_score"] for f in dashboard_data.values()) / len(dashboard_data), 1) if dashboard_data else 0
        },
        "last_updated": datetime.now().isoformat()
    }
