"""
Pydantic models for diagram generation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DiagramType(str, Enum):
    """Types of diagrams that can be generated"""
    NETWORK_TOPOLOGY = "network_topology"
    APPLICATION_DEPENDENCY = "application_dependency"
    DATA_FLOW = "data_flow"
    INFRASTRUCTURE = "infrastructure"
    SERVICE_MAP = "service_map"
    COMPONENT_DIAGRAM = "component_diagram"

class DiagramFormat(str, Enum):
    """Output formats for diagrams"""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    VSDX = "vsdx"  # Visio
    LUCID = "lucid"
    DOT = "dot"    # Graphviz

class DiagramLayout(str, Enum):
    """Diagram layout algorithms"""
    HIERARCHICAL = "hierarchical"
    CIRCULAR = "circular"
    FORCE_DIRECTED = "force_directed"
    LAYERED = "layered"
    TREE = "tree"
    RADIAL = "radial"

class DiagramStatus(str, Enum):
    """Diagram generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DiagramRequest(BaseModel):
    """Request model for diagram generation"""
    name: str = Field(..., description="Name for the diagram")
    diagram_type: DiagramType
    output_format: DiagramFormat = DiagramFormat.PNG
    layout: DiagramLayout = DiagramLayout.HIERARCHICAL
    topology_id: Optional[str] = Field(None, description="ID of topology to visualize")
    app_name: Optional[str] = Field(None, description="Application name for file tagging")
    
    # Visual options
    include_labels: bool = True
    include_ip_addresses: bool = True
    include_ports: bool = False
    color_by_type: bool = True
    show_connections: bool = True
    
    # Size and quality options
    width: int = Field(1920, ge=800, le=4096)
    height: int = Field(1080, ge=600, le=4096)
    dpi: int = Field(300, ge=72, le=600)
    
    # Filters
    node_types: Optional[List[str]] = None
    exclude_nodes: Optional[List[str]] = None
    connection_types: Optional[List[str]] = None
    
    metadata: Dict[str, Any] = {}

class DiagramResponse(BaseModel):
    """Response model for diagram generation"""
    job_id: str
    status: DiagramStatus
    message: str
    estimated_duration: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.now)

class DiagramJob(BaseModel):
    """Diagram generation job information"""
    job_id: str
    name: str
    diagram_type: DiagramType
    output_format: DiagramFormat
    status: DiagramStatus
    progress_percentage: float = Field(0.0, ge=0, le=100)
    current_task: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    output_file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    
    # Error handling
    error_message: Optional[str] = None
    warnings: List[str] = []
    
    # Request details
    request: Optional[DiagramRequest] = None
    
    metadata: Dict[str, Any] = {}

class DiagramTemplate(BaseModel):
    """Diagram template configuration"""
    id: str
    name: str
    description: Optional[str] = None
    diagram_type: DiagramType
    default_format: DiagramFormat
    default_layout: DiagramLayout
    
    # Template settings
    color_scheme: Dict[str, str] = {}
    node_styles: Dict[str, Any] = {}
    edge_styles: Dict[str, Any] = {}
    
    # Layout settings
    spacing: Dict[str, float] = {}
    sizing: Dict[str, Any] = {}
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DiagramElement(BaseModel):
    """Individual diagram element"""
    id: str
    element_type: str  # "node" or "edge"
    label: str
    position: Optional[Dict[str, float]] = None  # x, y coordinates
    style: Dict[str, Any] = {}
    properties: Dict[str, Any] = {}

class DiagramData(BaseModel):
    """Complete diagram data for rendering"""
    title: str
    description: Optional[str] = None
    elements: List[DiagramElement]
    layout_info: Dict[str, Any] = {}
    style_info: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

class DiagramExport(BaseModel):
    """Diagram export configuration"""
    job_id: str
    formats: List[DiagramFormat]
    app_name: str
    include_metadata: bool = True
    compress: bool = False