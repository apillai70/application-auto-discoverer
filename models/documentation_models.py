"""
Pydantic models for documentation generation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentationType(str, Enum):
    """Types of documentation that can be generated"""
    NETWORK_OVERVIEW = "network_overview"
    APPLICATION_INVENTORY = "application_inventory"
    SECURITY_ASSESSMENT = "security_assessment"
    INFRASTRUCTURE_REPORT = "infrastructure_report"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    COMPLIANCE_REPORT = "compliance_report"
    TECHNICAL_DOCUMENTATION = "technical_documentation"

class DocumentFormat(str, Enum):
    """Output formats for documentation"""
    DOCX = "docx"  # Microsoft Word
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    XLSX = "xlsx"  # Excel for data reports

class DocumentStatus(str, Enum):
    """Documentation generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Legacy alias for backward compatibility
DocumentationStatus = DocumentStatus

class DocumentTemplate(BaseModel):
    """Documentation template model"""
    id: str
    name: str
    description: Optional[str] = None
    document_type: DocumentationType
    default_format: DocumentFormat
    
    # Template structure
    sections: List[str] = []
    include_diagrams: bool = True
    include_tables: bool = True
    include_appendices: bool = True
    
    # Styling
    template_file: Optional[str] = None  # Path to template file
    style_config: Dict[str, Any] = {}
    
    # Content configuration
    auto_generate_toc: bool = True
    include_executive_summary: bool = True
    include_methodology: bool = True
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    metadata: Dict[str, Any] = {}

class DocumentationRequest(BaseModel):
    """Request model for documentation generation"""
    name: str = Field(..., description="Name for the documentation")
    document_type: DocumentationType
    output_format: DocumentFormat = DocumentFormat.DOCX
    template_id: Optional[str] = None
    
    # Source data
    topology_id: Optional[str] = Field(None, description="ID of topology to document")
    analysis_id: Optional[str] = Field(None, description="ID of analysis to document")
    app_name: Optional[str] = Field(None, description="Application name for file tagging")
    
    # Content options
    include_executive_summary: bool = True
    include_technical_details: bool = True
    include_diagrams: bool = True
    include_raw_data: bool = False
    include_recommendations: bool = True
    
    # Sections to include
    sections: List[str] = []
    
    # Custom content
    custom_sections: Dict[str, str] = {}
    
    # Metadata
    author: Optional[str] = None
    organization: Optional[str] = None
    version: str = "1.0"
    
    metadata: Dict[str, Any] = {}

class DocumentationResponse(BaseModel):
    """Response model for documentation generation"""
    job_id: str
    status: DocumentStatus
    message: str
    estimated_duration: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.now)

class DocumentationJob(BaseModel):
    """Documentation generation job information"""
    job_id: str
    name: str
    document_type: DocumentationType
    output_format: DocumentFormat
    status: DocumentStatus
    progress_percentage: float = Field(0.0, ge=0, le=100)
    current_task: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    output_file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    page_count: Optional[int] = None
    
    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = []
    
    # Request details
    request: Optional[DocumentationRequest] = None
    
    metadata: Dict[str, Any] = {}

class DocumentSection(BaseModel):
    """Individual document section"""
    id: str
    title: str
    content: str
    section_type: str  # "text", "table", "diagram", "list"
    order: int = 0
    
    # Formatting
    style: Dict[str, Any] = {}
    include_in_toc: bool = True
    page_break_before: bool = False
    
    # Content data
    data: Optional[Dict[str, Any]] = None
    diagram_path: Optional[str] = None
    
    metadata: Dict[str, Any] = {}

class DocumentData(BaseModel):
    """Complete document data for generation"""
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    organization: Optional[str] = None
    version: str = "1.0"
    created_date: datetime = Field(default_factory=datetime.now)
    
    # Content
    executive_summary: Optional[str] = None
    sections: List[DocumentSection] = []
    appendices: List[DocumentSection] = []
    
    # References
    topology_data: Optional[Dict[str, Any]] = None
    analysis_data: Optional[Dict[str, Any]] = None
    diagrams: List[str] = []  # File paths to diagrams
    
    # Styling
    template_config: Dict[str, Any] = {}
    
    metadata: Dict[str, Any] = {}

class ReportConfig(BaseModel):
    """Report configuration options"""
    include_cover_page: bool = True
    include_table_of_contents: bool = True
    include_executive_summary: bool = True
    include_methodology: bool = True
    include_findings: bool = True
    include_recommendations: bool = True
    include_appendices: bool = True
    
    # Formatting
    header_footer: bool = True
    page_numbers: bool = True
    watermark: Optional[str] = None
    
    # Content depth
    detail_level: str = "standard"  # "summary", "standard", "detailed"
    technical_depth: str = "intermediate"  # "basic", "intermediate", "advanced"

class DocumentMetrics(BaseModel):
    """Documentation generation metrics"""
    job_id: str
    sections_generated: int = 0
    diagrams_included: int = 0
    tables_generated: int = 0
    total_pages: int = 0
    generation_time_seconds: float = 0.0
    file_size_bytes: int = 0