"""
Fixed Excel Processing Router for PortScope Integration
Handles Excel file processing with archetype classification and WebSocket support
"""
import re
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any, List, Optional
from services.archetype_service import ArchetypeService
import pandas as pd
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
import json
import tempfile
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Job tracking for Excel processing
processing_jobs = {}
# WebSocket connection manager
active_websocket_connections = set()

# Initialize archetype service
archetype_service = ArchetypeService()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_job_update(self, job_id: str, data: dict):
        """Send job update to all connected clients"""
        message = {
            "job_id": job_id,
            "type": "job_update",
            **data
        }
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to broadcast WebSocket message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

# Global connection manager
manager = ConnectionManager()

# Update job with WebSocket notification
async def update_job_with_websocket(job_id: str, **updates):
    """Update job and send WebSocket notification"""
    if job_id in processing_jobs:
        processing_jobs[job_id].update(updates)
        processing_jobs[job_id]["updated_at"] = datetime.now().isoformat()
        
        # Send WebSocket update
        await manager.send_job_update(job_id, updates)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time job progress updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Keep connection alive and handle any incoming messages
            try:
                # Wait for messages (can be ping/pong or status requests)
                data = await websocket.receive_text()
                message = json.loads(data) if data else {}
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif message.get("type") == "get_job_status":
                    job_id = message.get("job_id")
                    if job_id and job_id in processing_jobs:
                        await websocket.send_json({
                            "type": "job_status",
                            "job_id": job_id,
                            **processing_jobs[job_id]
                        })
                elif message.get("type") == "get_all_jobs":
                    active_jobs = {
                        job_id: job for job_id, job in processing_jobs.items()
                        if job.get("status") in ["queued", "processing"]
                    }
                    await websocket.send_json({
                        "type": "all_jobs",
                        "jobs": active_jobs
                    })
                    
            except asyncio.TimeoutError:
                # Send heartbeat every 30 seconds
                await websocket.send_json({
                    "type": "heartbeat", 
                    "timestamp": datetime.now().isoformat(),
                    "active_jobs": len([j for j in processing_jobs.values() if j.get("status") in ["queued", "processing"]])
                })
                await asyncio.sleep(30)
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
    
@router.post("/api/process/excel")
async def process_excel_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    port_column: str = Form("port,dst_port,destination_port,dport"),
    protocol_column: str = Form("protocol,proto,ip_proto"),
    app_column: str = Form("app_id,application_id,id"),
    info_column: str = Form("info,description,details"),
    sheet_name: Optional[str] = Form(None),
    fallback_parsing: bool = Form(True)
):
    """
    Process uploaded Excel file and classify applications
    Enhanced with multi-column support and info field parsing
    """
    
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only Excel and CSV files are supported.")
    
    # Generate job ID
    job_id = str(uuid.uuid4())
    
    try:
        # Read the file
        content = await file.read()
        
        # Save temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
        temp_file.write(content)
        temp_file.close()
        
        # Initialize job
        processing_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "filename": file.filename,
            "total_rows": 0,
            "progress": 0,
            "message": "File uploaded, starting processing...",
            "started_at": datetime.now().isoformat(),
            "result": None,
            "error": None,
            "settings": {
                "port_column": port_column,
                "protocol_column": protocol_column,
                "app_column": app_column,
                "info_column": info_column,
                "sheet_name": sheet_name,
                "fallback_parsing": fallback_parsing
            }
        }
        
        # Send initial WebSocket update
        await manager.send_job_update(job_id, {
            "status": "queued",
            "progress": 0,
            "message": "Job created, initializing..."
        })
        
        # Start background processing
        background_tasks.add_task(
            process_excel_background,
            job_id,
            temp_file.name,
            port_column,
            protocol_column,
            app_column,
            info_column,
            sheet_name,
            fallback_parsing
        )
        
        # Get initial row count for response
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(temp_file.name)
            else:
                df = pd.read_excel(temp_file.name, sheet_name=sheet_name)
            
            processing_jobs[job_id]["total_rows"] = len(df)
            await manager.send_job_update(job_id, {"total_rows": len(df)})
        except Exception as e:
            processing_jobs[job_id]["total_rows"] = 0
            logger.warning(f"Could not determine row count: {e}")
        
        return {
            "job_id": job_id,
            "status": "queued",
            "total_rows": processing_jobs[job_id]["total_rows"],
            "message": "Processing started",
            "websocket_available": True
        }
        
    except Exception as e:
        error_message = f"Error processing file: {str(e)}"
        processing_jobs[job_id] = {
            "job_id": job_id,
            "status": "error",
            "error": error_message,
            "started_at": datetime.now().isoformat()
        }
        
        # Send error via WebSocket
        await manager.send_job_update(job_id, {
            "status": "error",
            "error": error_message
        })
        
        raise HTTPException(status_code=500, detail=error_message)

async def process_excel_background(
    job_id: str, 
    temp_file_path: str, 
    port_column: str,
    protocol_column: str,
    app_column: str,
    info_column: str,
    sheet_name: Optional[str],
    fallback_parsing: bool
):
    """
    Background task for Excel processing with progress updates via WebSocket
    """
    
    try:
        # Update job status
        await update_job_with_websocket(job_id, 
            status="processing",
            progress=10,
            message="Reading Excel file..."
        )
        
        # Read the Excel/CSV file
        if temp_file_path.endswith('.csv'):
            df = pd.read_csv(temp_file_path)
        else:
            df = pd.read_excel(temp_file_path, sheet_name=sheet_name)
        
        await update_job_with_websocket(job_id,
            total_rows=len(df),
            progress=30,
            message=f"Loaded {len(df)} rows, analyzing applications..."
        )
        
        # Analyze applications with enhanced column support
        applications = analyze_applications_from_excel_enhanced(
            df, port_column, protocol_column, app_column, info_column, fallback_parsing, job_id
        )
        
        await update_job_with_websocket(job_id,
            progress=60,
            message=f"Classified {len(applications)} applications, generating summary..."
        )
        
        # Classify archetypes using your archetype service
        classified_apps = []
        total_apps = len(applications)
        
        for i, app in enumerate(applications):
            # Update progress every 10 apps
            if i % 10 == 0 or i == total_apps - 1:
                progress = 60 + (30 * (i + 1) / total_apps)
                await update_job_with_websocket(job_id,
                    progress=int(progress),
                    message=f"Classifying application {i+1}/{total_apps}..."
                )
            
            # Use the archetype service to get details
            archetype_details = archetype_service.get_archetype_details(app.get("architecture", "Unknown"))
            
            app_with_details = {
                **app,
                "archetype_details": archetype_details,
                "cloud_readiness": archetype_details.get("cloud_readiness", "Unknown") if archetype_details else "Unknown",
                "modernization_effort": archetype_details.get("modernization_effort", "Unknown") if archetype_details else "Unknown",
                "aws_services": archetype_details.get("aws_services", []) if archetype_details else []
            }
            classified_apps.append(app_with_details)
        
        # Generate summary statistics
        summary = generate_processing_summary(classified_apps)
        
        # Create result
        result = {
            "applications": classified_apps,
            "summary": summary,
            "rows_processed": len(df),
            "applications_identified": len(classified_apps),
            "processing_time": (datetime.now() - datetime.fromisoformat(processing_jobs[job_id]["started_at"])).total_seconds()
        }
        
        # Save processed data for download
        results_dir = Path("results/excel")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = results_dir / f"processed_{job_id}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Update job completion
        await update_job_with_websocket(job_id,
            status="completed",
            progress=100,
            message="Processing completed successfully",
            result=result,
            completed_at=datetime.now().isoformat(),
            output_file=str(output_file)
        )
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Excel processing failed for job {job_id}: {error_message}")
        
        await update_job_with_websocket(job_id,
            status="error",
            error=error_message,
            completed_at=datetime.now().isoformat()
        )
    
    finally:
        # Clean up temp file
        try:
            Path(temp_file_path).unlink()
        except:
            pass

def analyze_applications_from_excel_enhanced(
    df: pd.DataFrame, 
    port_columns: str, 
    protocol_columns: str,
    app_columns: str, 
    info_columns: str,
    fallback_parsing: bool,
    job_id: str
) -> List[Dict[str, Any]]:
    """
    Enhanced analysis with multi-column support and info field parsing
    """
    
    applications = []
    
    # Parse column specifications (comma-separated)
    port_col_options = [col.strip() for col in port_columns.split(',')]
    protocol_col_options = [col.strip() for col in protocol_columns.split(',')]
    app_col_options = [col.strip() for col in app_columns.split(',')]
    info_col_options = [col.strip() for col in info_columns.split(',')]
    
    logger.info(f"Job {job_id}: Column options - Port: {port_col_options}, App: {app_col_options}")
    logger.info(f"Job {job_id}: Available columns: {list(df.columns)}")
    
    # Find the first matching column for each type
    port_col = next((col for col in port_col_options if col in df.columns), None)
    protocol_col = next((col for col in protocol_col_options if col in df.columns), None)
    app_col = next((col for col in app_col_options if col in df.columns), None)
    info_col = next((col for col in info_col_options if col in df.columns), None)
    
    logger.info(f"Job {job_id}: Using columns - Port: {port_col}, Protocol: {protocol_col}, App: {app_col}, Info: {info_col}")
    
    # Group by application
    if app_col and app_col in df.columns:
        app_groups = df.groupby(app_col)
    else:
        # Fallback: create synthetic app groups based on unique combinations
        if info_col and info_col in df.columns:
            # Group by info field patterns
            df['synthetic_app'] = df[info_col].fillna('unknown').apply(
                lambda x: f"App_{hash(str(x)[:50]) % 1000:03d}"
            )
        else:
            # Simple row-based grouping
            df['synthetic_app'] = df.index // 100
        app_groups = df.groupby('synthetic_app')
    
    for app_name, group in app_groups:
        # Extract ports from dedicated column or info field
        ports = []
        protocols = []
        services = []
        
        # Try dedicated port column first
        if port_col and port_col in group.columns:
            port_values = group[port_col].dropna()
            for val in port_values:
                try:
                    if isinstance(val, (int, float)) and not pd.isna(val):
                        ports.append(int(val))
                    elif isinstance(val, str) and val.isdigit():
                        ports.append(int(val))
                except (ValueError, TypeError):
                    pass
        
        # Try dedicated protocol column
        if protocol_col and protocol_col in group.columns:
            protocol_values = group[protocol_col].dropna().unique()
            protocols = [str(p).upper() for p in protocol_values if str(p).upper() in ['TCP', 'UDP', 'HTTP', 'HTTPS']]
        
        # Fallback parsing from info field if enabled and no dedicated columns found
        if fallback_parsing and (not ports or not protocols) and info_col and info_col in group.columns:
            for info_text in group[info_col].dropna():
                if pd.isna(info_text):
                    continue
                    
                parsed = parse_traffic_info(str(info_text))
                
                if parsed.get("port") and parsed["port"] not in ports:
                    ports.append(parsed["port"])
                if parsed.get("protocol") and parsed["protocol"] not in protocols:
                    protocols.append(parsed["protocol"])
                if parsed.get("service") and parsed["service"] not in services:
                    services.append(parsed["service"])
        
        # Remove duplicates and sort
        ports = sorted(list(set(ports)))
        protocols = list(set(protocols))
        services = list(set(services))
        
        # Classify architecture based on enhanced analysis
        architecture = classify_architecture_from_enhanced_data(group, ports, protocols, services)
        
        # Calculate metrics
        app_data = {
            "app_id": str(app_name),
            "app_name": str(app_name),
            "architecture": architecture,
            "ports": [str(p) for p in ports],
            "protocols": protocols,
            "services": services,
            "port_count": len(ports),
            "flow_count": len(group),
            "risk_level": calculate_risk_level(ports, len(group)),
            "confidence": calculate_confidence_score_enhanced(group, ports, protocols, services),
            "source_ips": group.get('src_ip', group.get('source_ip', pd.Series())).nunique() if 'src_ip' in group.columns or 'source_ip' in group.columns else 0,
            "dest_ips": group.get('dst_ip', group.get('dest_ip', pd.Series())).nunique() if 'dst_ip' in group.columns or 'dest_ip' in group.columns else 0,
            "parsing_method": "dedicated_columns" if (port_col or protocol_col) else "info_field_fallback"
        }
        
        applications.append(app_data)
    
    logger.info(f"Job {job_id}: Analyzed {len(applications)} applications")
    return applications

def parse_traffic_info(info_text):
    """
    Enhanced parser for traffic info string to extract port, protocol, and service information
    """
    if not info_text or not isinstance(info_text, str):
        return {"port": None, "protocol": None, "service": None, "component": None}
    
    result = {"port": None, "protocol": None, "service": None, "component": None}
    info_lower = info_text.lower()
    
    # Extract port number using multiple patterns
    port_patterns = [
        r'port\s+(\d+)',
        r':(\d{2,5})\b',
        r'(\d{2,5})/tcp',
        r'(\d{2,5})/udp',
        r'port=(\d+)'
    ]
    
    for pattern in port_patterns:
        port_match = re.search(pattern, info_lower)
        if port_match:
            try:
                port = int(port_match.group(1))
                if 1 <= port <= 65535:  # Valid port range
                    result["port"] = port
                    break
            except (ValueError, IndexError):
                continue
    
    # Extract protocol
    protocol_patterns = [
        r'over\s+([a-zA-Z]+)',
        r'protocol[:\s]+([a-zA-Z]+)',
        r'/([a-zA-Z]+)\b',
        r'\b(tcp|udp|http|https|ftp|ssh|smtp)\b'
    ]
    
    for pattern in protocol_patterns:
        protocol_match = re.search(pattern, info_lower)
        if protocol_match:
            protocol = protocol_match.group(1).upper()
            if protocol in ['TCP', 'UDP', 'HTTP', 'HTTPS', 'FTP', 'SSH', 'SMTP']:
                result["protocol"] = protocol
                break
    
    # Extract service type
    service_patterns = [
        r'^([a-zA-Z]+)\s+',
        r'\b(web|api|database|db|mail|file|auth|admin)\b',
        r'service[:\s]+([a-zA-Z]+)'
    ]
    
    for pattern in service_patterns:
        service_match = re.search(pattern, info_lower)
        if service_match:
            service_type = service_match.group(1).lower()
            if service_type in ['api', 'spa', 'web']:
                result["service"] = 'web'
            elif service_type in ['db', 'database', 'sql']:
                result["service"] = 'database'
            elif service_type in ['mail', 'smtp', 'email']:
                result["service"] = 'mail'
            elif service_type in ['file', 'ftp', 'share']:
                result["service"] = 'file'
            else:
                result["service"] = service_type
            break
   
    return result

def classify_architecture_from_enhanced_data(group: pd.DataFrame, ports: List, protocols: List, services: List) -> str:
    """
    Enhanced architecture classification using multiple data sources
    """
    
    port_set = set(str(p) for p in ports)
    protocol_set = set(protocols)
    service_set = set(services)
    
    # Microservices: Multiple high ports, container patterns, modern protocols
    microservices_indicators = 0
    if len([p for p in ports if int(str(p)) > 3000]) >= 3:
        microservices_indicators += 2
    if any(p in port_set for p in ['8080', '8443', '9090', '3000', '4000']):
        microservices_indicators += 1
    if 'HTTP' in protocol_set or 'HTTPS' in protocol_set:
        microservices_indicators += 1
    if microservices_indicators >= 3:
        return "Microservices"
    
    # Event-Driven: Messaging ports and protocols
    event_driven_ports = {'5672', '9092', '61616', '5432', '15672'}
    if any(str(p) in event_driven_ports for p in ports):
        return "Event-Driven"
    
    # Database-Centric: Database ports and services
    database_ports = {'3306', '1433', '5432', '1521', '27017'}
    if any(str(p) in database_ports for p in ports) or 'database' in service_set:
        return "Database-Centric"
    
    # Web + API Headless: Modern web patterns
    web_indicators = 0
    if any(str(p) in ['80', '443'] for p in ports):
        web_indicators += 1
    if any(str(p) in ['8080', '3000', '4000'] for p in ports):
        web_indicators += 1
    if 'web' in service_set or 'api' in service_set:
        web_indicators += 1
    if web_indicators >= 2:
        return "Web + API Headless"
    
    # Client-Server: Direct database access patterns, RDP
    if any(str(p) in ['1433', '3389', '1521'] for p in ports):
        return "Client-Server"
    
    # SOA: Enterprise service ports
    soa_ports = {'8080', '8443', '9080', '7001'}
    if any(str(p) in soa_ports for p in ports) and len(ports) > 2:
        return "SOA"
    
    # 3-Tier: Standard web application with clear tiers
    web_tier = any(str(p) in ['80', '443'] for p in ports)
    data_tier = any(str(p) in ['3306', '5432', '1433'] for p in ports)
    if web_tier and data_tier:
        return "3-Tier"
    
    # Default based on port patterns
    if len(ports) == 1:
        return "Monolithic"
    elif len(ports) > 5:
        return "SOA"
    else:
        return "Monolithic"

def calculate_confidence_score_enhanced(group: pd.DataFrame, ports: List, protocols: List, services: List) -> float:
    """
    Enhanced confidence calculation using multiple data sources
    """
    
    score = 0.3  # Base score
    
    # Port information quality
    if len(ports) > 5:
        score += 0.3
    elif len(ports) > 2:
        score += 0.2
    elif len(ports) > 0:
        score += 0.1
    
    # Protocol information
    if len(protocols) > 0:
        score += 0.2
    
    # Service identification
    if len(services) > 0:
        score += 0.1
    
    # Data volume
    if len(group) > 1000:
        score += 0.2
    elif len(group) > 100:
        score += 0.1
    
    # Data completeness
    if 'src_ip' in group.columns and 'dst_ip' in group.columns:
        score += 0.1
    
    return min(1.0, score)

def calculate_risk_level(ports: List, flow_count: int) -> str:
    """
    Calculate risk level based on ports and traffic volume
    """
    
    critical_risk_ports = {'23', '21', '135', '139', '445', '3389'}  # Telnet, FTP, SMB, RDP
    high_risk_ports = {'1433', '3306', '5432', '1521', '22', '25'}  # Databases, SSH, SMTP
    medium_risk_ports = {'80', '443', '8080', '8443', '53', '110', '143'}  # Web services, DNS, Mail
    
    port_strings = set(str(p) for p in ports)
    
    if port_strings & critical_risk_ports:
        return "critical"
    elif port_strings & high_risk_ports:
        return "high"
    elif len(port_strings & medium_risk_ports) > 3 or flow_count > 50000:
        return "high"
    elif len(port_strings & medium_risk_ports) > 1 or flow_count > 10000:
        return "medium"
    else:
        return "low"

def generate_processing_summary(applications: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate summary statistics for processed applications
    """
    
    if not applications:
        return {}
    
    # Architecture distribution
    arch_dist = {}
    for app in applications:
        arch = app.get("architecture", "Unknown")
        arch_dist[arch] = arch_dist.get(arch, 0) + 1
    
    # Risk distribution
    risk_dist = {}
    for app in applications:
        risk = app.get("risk_level", "unknown")
        risk_dist[risk] = risk_dist.get(risk, 0) + 1
    
    # Protocol analysis
    protocol_dist = {}
    for app in applications:
        for protocol in app.get("protocols", []):
            protocol_dist[protocol] = protocol_dist.get(protocol, 0) + 1
    
    return {
        "total_applications": len(applications),
        "architecture_distribution": arch_dist,
        "risk_distribution": risk_dist,
        "protocol_distribution": protocol_dist,
        "average_ports_per_app": sum(app.get("port_count", 0) for app in applications) / len(applications),
        "total_flows": sum(app.get("flow_count", 0) for app in applications),
        "parsing_methods": {
            method: len([app for app in applications if app.get("parsing_method") == method])
            for method in ["dedicated_columns", "info_field_fallback"]
        }
    }

@router.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """
    Get the status of a processing job
    """
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]

@router.get("/api/download/{job_id}")
async def download_results(job_id: str):
    """
    Download processed results
    """
    
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = processing_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    output_file = job.get("output_file")
    if not output_file or not Path(output_file).exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    
    return FileResponse(
        path=output_file,
        filename=f"processed_applications_{job_id}.json",
        media_type="application/json"
    )

@router.get("/api/classify/batch")
async def classify_applications_batch(applications: List[Dict[str, Any]]):
    """
    Batch classify applications using archetype service
    """
    
    try:
        classified = []
        for app in applications:
            archetype = app.get("architecture", "Unknown")
            archetype_details = archetype_service.get_archetype_details(archetype)
            strategy_recommendation = archetype_service.recommend_strategy(archetype)
            
            classified.append({
                **app,
                "archetype_details": archetype_details,
                "strategy_recommendation": strategy_recommendation
            })
        
        return {
            "success": True,
            "applications": classified,
            "total_classified": len(classified)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")

# Health check endpoint for WebSocket
@router.get("/api/ws/health")
async def websocket_health():
    """Check WebSocket service health"""
    return {
        "status": "healthy",
        "active_connections": len(manager.active_connections),
        "active_jobs": len([j for j in processing_jobs.values() if j.get("status") in ["queued", "processing"]]),
        "websocket_url": "/api/v1/excel/ws",
        "timestamp": datetime.now().isoformat()
    }