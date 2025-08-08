from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NodeType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    SERVER = "server"
    WORKSTATION = "workstation"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    UNKNOWN = "unknown"

class ConnectionType(str, Enum):
    ETHERNET = "ethernet"
    WIFI = "wifi"
    FIBER = "fiber"
    SERIAL = "serial"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class NodeType(str, Enum):
    ROUTER = "router"
    SWITCH = "switch"
    SERVER = "server"
    WORKSTATION = "workstation"
    FIREWALL = "firewall"
    LOAD_BALANCER = "load_balancer"
    UNKNOWN = "unknown"

class ConnectionType(str, Enum):
    ETHERNET = "ethernet"
    WIFI = "wifi"
    FIBER = "fiber"
    SERIAL = "serial"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"

class LogSource(str, Enum):
    EXTRAHOP = "extrahop"
    SPLUNK = "splunk"
    DYNATRACE = "dynatrace"
    UNKNOWN = "unknown"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class LogAnalysisRequest(BaseModel):
    """Request model for log analysis"""
    log_source: LogSource = LogSource.UNKNOWN
    file_paths: List[str] = Field(..., description="Paths to log files")
    analysis_type: str = Field(default="topology", description="Type of analysis to perform")
    time_range_start: Optional[datetime] = Field(default=None, description="Start time for analysis")
    time_range_end: Optional[datetime] = Field(default=None, description="End time for analysis")
    include_connections: bool = Field(default=True, description="Include connection analysis")
    include_applications: bool = Field(default=True, description="Include application discovery")
    analysis_name: Optional[str] = Field(default=None, description="Name for the analysis")

class LogAnalysisResponse(BaseModel):
    """Response model for log analysis initiation"""
    analysis_id: str
    status: AnalysisStatus
    message: str
    estimated_duration: Optional[int] = None
    started_at: datetime = Field(default_factory=datetime.now)

class AnalysisProgress(BaseModel):
    """Analysis progress information"""
    analysis_id: str
    status: AnalysisStatus
    progress_percentage: float = Field(ge=0, le=100)
    current_task: Optional[str] = None
    records_processed: int = 0
    connections_found: int = 0
    applications_discovered: int = 0
    estimated_time_remaining: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}

class TopologyNode(BaseModel):
    """Represents a node in the network topology"""
    id: str
    name: Optional[str] = None
    ip_address: str
    mac_address: Optional[str] = None
    node_type: NodeType = NodeType.UNKNOWN
    vendor: Optional[str] = None
    model: Optional[str] = None
    os_info: Optional[str] = None
    hostname: Optional[str] = None
    ports: List[int] = []
    services: List[str] = []
    interfaces: List[Dict[str, Any]] = []
    location: Optional[str] = None
    description: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = {}

    @validator('ip_address')
    def validate_ip(cls, v):
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')

class TopologyEdge(BaseModel):
    """Represents a connection between two nodes"""
    id: str
    source_node_id: str
    target_node_id: str
    connection_type: ConnectionType = ConnectionType.UNKNOWN
    bandwidth: Optional[str] = None
    latency: Optional[float] = None
    packet_loss: Optional[float] = None
    source_interface: Optional[str] = None
    target_interface: Optional[str] = None
    vlan_id: Optional[int] = None
    is_active: bool = True
    discovered_at: datetime = Field(default_factory=datetime.now)
    last_tested: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

class NetworkTopology(BaseModel):
    """Complete network topology representation"""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: List[TopologyNode] = []
    edges: List[TopologyEdge] = []
    subnets: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    scan_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class NetworkInterface(BaseModel):
    """Network interface information"""
    name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    interface_type: str = "ethernet"
    speed: Optional[str] = None
    duplex: Optional[str] = None
    mtu: Optional[int] = None
    is_up: bool = True
    vlan_id: Optional[int] = None
    description: Optional[str] = None

class ServiceInfo(BaseModel):
    """Service running on a node"""
    name: str
    port: int
    protocol: str = "tcp"
    state: str = "open"
    version: Optional[str] = None
    banner: Optional[str] = None
    product: Optional[str] = None
    extra_info: Optional[str] = None

class SubnetInfo(BaseModel):
    """Subnet information"""
    network: str
    netmask: str
    gateway: Optional[str] = None
    dns_servers: List[str] = []
    dhcp_range: Optional[str] = None
    vlan_id: Optional[int] = None
    description: Optional[str] = None
    node_count: int = 0

# Legacy aliases for backward compatibility (if needed)
NetworkScanRequest = LogAnalysisRequest
NetworkScanResponse = LogAnalysisResponse
ScanProgress = AnalysisProgress
ScanStatus = AnalysisStatus

class TopologyNode(BaseModel):
    """Represents a node in the network topology"""
    id: str
    name: Optional[str] = None
    ip_address: str
    mac_address: Optional[str] = None
    node_type: NodeType = NodeType.UNKNOWN
    vendor: Optional[str] = None
    model: Optional[str] = None
    os_info: Optional[str] = None
    hostname: Optional[str] = None
    ports: List[int] = []
    services: List[str] = []
    interfaces: List[Dict[str, Any]] = []
    location: Optional[str] = None
    description: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
    metadata: Dict[str, Any] = {}

    @validator('ip_address')
    def validate_ip(cls, v):
        import ipaddress
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('Invalid IP address format')

class TopologyEdge(BaseModel):
    """Represents a connection between two nodes"""
    id: str
    source_node_id: str
    target_node_id: str
    connection_type: ConnectionType = ConnectionType.UNKNOWN
    bandwidth: Optional[str] = None
    latency: Optional[float] = None
    packet_loss: Optional[float] = None
    source_interface: Optional[str] = None
    target_interface: Optional[str] = None
    vlan_id: Optional[int] = None
    is_active: bool = True
    discovered_at: datetime = Field(default_factory=datetime.now)
    last_tested: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

class NetworkTopology(BaseModel):
    """Complete network topology representation"""
    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: List[TopologyNode] = []
    edges: List[TopologyEdge] = []
    subnets: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    scan_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class NetworkInterface(BaseModel):
    """Network interface information"""
    name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    netmask: Optional[str] = None
    gateway: Optional[str] = None
    interface_type: str = "ethernet"
    speed: Optional[str] = None
    duplex: Optional[str] = None
    mtu: Optional[int] = None
    is_up: bool = True
    vlan_id: Optional[int] = None
    description: Optional[str] = None

class ServiceInfo(BaseModel):
    """Service running on a node"""
    name: str
    port: int
    protocol: str = "tcp"
    state: str = "open"
    version: Optional[str] = None
    banner: Optional[str] = None
    product: Optional[str] = None
    extra_info: Optional[str] = None

class SubnetInfo(BaseModel):
    """Subnet information"""
    network: str
    netmask: str
    gateway: Optional[str] = None
    dns_servers: List[str] = []
    dhcp_range: Optional[str] = None
    vlan_id: Optional[int] = None
    description: Optional[str] = None
    node_count: int = 0