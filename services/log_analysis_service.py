import asyncio
import uuid
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from fastapi import UploadFile
from models.topology_models import (
    LogSource, AnalysisProgress, AnalysisStatus,
    TopologyNode, TopologyEdge, NetworkTopology
)
from utils.file_utils import FileUtils
from utils.network_utils import NetworkUtils
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LogAnalysisService:
    """Service for analyzing logs from various sources to discover network topology"""
    
    def __init__(self):
        self.file_utils = FileUtils()
        self.network_utils = NetworkUtils()
        self.active_analyses: Dict[str, AnalysisProgress] = {}
        self.analysis_results: Dict[str, NetworkTopology] = {}
        
        # Ensure all required directories exist
        directories = [
            settings.DATA_STAGING_DIR,
            settings.PROCESSED_DIR,
            settings.FAILED_DIR,
            settings.RESULTS_BASE_DIR,
            settings.EXCEL_OUTPUT_DIR,
            settings.VISIO_OUTPUT_DIR,
            settings.WORD_OUTPUT_DIR,
            settings.PDF_OUTPUT_DIR,
            settings.LUCID_OUTPUT_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
        
    async def save_uploaded_file(self, file: UploadFile, log_source: str) -> str:
        """Save uploaded file to data_staging directory"""
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{log_source}_{timestamp}_{file.filename}"
        file_path = os.path.join(settings.DATA_STAGING_DIR, filename)
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved uploaded file to staging: {file_path}")
        return file_path
    
    async def move_to_processed(self, file_path: str) -> str:
        """Move file from staging to processed folder"""
        filename = os.path.basename(file_path)
        processed_path = os.path.join(settings.PROCESSED_DIR, filename)
        
        try:
            os.rename(file_path, processed_path)
            logger.info(f"Moved file to processed: {processed_path}")
            return processed_path
        except Exception as e:
            logger.error(f"Failed to move file to processed: {str(e)}")
            raise
    
    async def move_to_failed(self, file_path: str, error_message: str) -> str:
        """Move file from staging to failed folder with error info"""
        filename = os.path.basename(file_path)
        failed_path = os.path.join(settings.FAILED_DIR, filename)
        
        try:
            os.rename(file_path, failed_path)
            
            # Create error log file
            error_file = failed_path + ".error"
            with open(error_file, "w") as f:
                f.write(f"Processing failed at: {datetime.now()}\n")
                f.write(f"Error: {error_message}\n")
            
            logger.info(f"Moved file to failed: {failed_path}")
            return failed_path
        except Exception as e:
            logger.error(f"Failed to move file to failed: {str(e)}")
            raise
    
    async def start_file_analysis(self, file_path: str, log_source: str) -> str:
        """Start analysis of a log file"""
        analysis_id = str(uuid.uuid4())
        
        # Initialize analysis progress
        progress = AnalysisProgress(
            analysis_id=analysis_id,
            status=AnalysisStatus.PENDING,
            progress_percentage=0.0,
            current_task="Initializing analysis",
            started_at=datetime.now()
        )
        
        self.active_analyses[analysis_id] = progress
        
        logger.info(f"Started log analysis {analysis_id} for file {file_path}")
        return analysis_id
    
    async def process_log_file(self, analysis_id: str):
        """Process the log file in the background"""
        if analysis_id not in self.active_analyses:
            logger.error(f"Analysis {analysis_id} not found")
            return
        
        progress = self.active_analyses[analysis_id]
        file_path = None
        
        try:
            progress.status = AnalysisStatus.RUNNING
            progress.current_task = "Loading log file"
            progress.progress_percentage = 10.0
            
            # Get file path from analysis metadata (you'd store this during start_file_analysis)
            file_path = progress.metadata.get("file_path") if hasattr(progress, 'metadata') else None
            
            progress.current_task = "Parsing log data"
            progress.progress_percentage = 25.0
            
            # Parse the log file based on source
            log_data = await self._parse_log_file(analysis_id)
            progress.records_processed = len(log_data) if log_data else 0
            progress.progress_percentage = 50.0
            
            progress.current_task = "Discovering network topology"
            progress.progress_percentage = 60.0
            
            # Extract topology information
            topology = await self._extract_topology(log_data, analysis_id)
            progress.connections_found = len(topology.edges) if topology else 0
            progress.applications_discovered = len([n for n in topology.nodes if n.services]) if topology else 0
            progress.progress_percentage = 90.0
            
            # Store results
            if topology:
                self.analysis_results[analysis_id] = topology
            
            # Move file to processed folder
            if file_path and os.path.exists(file_path):
                await self.move_to_processed(file_path)
            
            progress.status = AnalysisStatus.COMPLETED
            progress.progress_percentage = 100.0
            progress.current_task = "Analysis completed"
            progress.completed_at = datetime.now()
            
            logger.info(f"Completed log analysis {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error in log analysis {analysis_id}: {str(e)}")
            progress.status = AnalysisStatus.FAILED
            progress.error_message = str(e)
            progress.completed_at = datetime.now()
            
            # Move file to failed folder
            if file_path and os.path.exists(file_path):
                try:
                    await self.move_to_failed(file_path, str(e))
                except Exception as move_error:
                    logger.error(f"Failed to move file to failed folder: {move_error}")
    
    async def _parse_log_file(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Parse log file based on its format and source"""
        progress = self.active_analyses[analysis_id]
        
        # This is a placeholder - actual implementation would parse different log formats
        # For now, return simulated data
        return [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "source_ip": "192.168.1.100",
                "dest_ip": "192.168.1.200",
                "source_port": 80,
                "dest_port": 8080,
                "protocol": "TCP",
                "application": "HTTP",
                "bytes_sent": 1024,
                "bytes_received": 2048
            }
        ]
    
    async def _extract_topology(self, log_data: List[Dict[str, Any]], analysis_id: str) -> NetworkTopology:
        """Extract network topology from parsed log data"""
        if not log_data:
            return NetworkTopology(
                id=str(uuid.uuid4()),
                name=f"Analysis {analysis_id}",
                description="Empty topology - no data processed"
            )
        
        # Extract unique nodes (IP addresses)
        unique_ips = set()
        connections = []
        
        for record in log_data:
            source_ip = record.get("source_ip")
            dest_ip = record.get("dest_ip")
            
            if source_ip:
                unique_ips.add(source_ip)
            if dest_ip:
                unique_ips.add(dest_ip)
            
            # Track connections
            if source_ip and dest_ip:
                connections.append({
                    "source": source_ip,
                    "destination": dest_ip,
                    "protocol": record.get("protocol", "TCP"),
                    "application": record.get("application", "Unknown"),
                    "bytes_sent": record.get("bytes_sent", 0),
                    "bytes_received": record.get("bytes_received", 0)
                })
        
        # Create topology nodes
        nodes = []
        for ip in unique_ips:
            # Determine node type based on IP patterns or application data
            node_type = self.network_utils.determine_node_type_from_ip(ip)
            
            # Extract services for this node
            services = list(set([
                conn["application"] for conn in connections 
                if conn["source"] == ip or conn["destination"] == ip
            ]))
            
            node = TopologyNode(
                id=str(uuid.uuid4()),
                ip_address=ip,
                node_type=node_type,
                services=services,
                discovered_at=datetime.now()
            )
            nodes.append(node)
        
        # Create topology edges
        edges = []
        node_map = {node.ip_address: node.id for node in nodes}
        
        # Group connections by source-destination pair
        connection_groups = {}
        for conn in connections:
            key = (conn["source"], conn["destination"])
            if key not in connection_groups:
                connection_groups[key] = []
            connection_groups[key].append(conn)
        
        for (source_ip, dest_ip), conn_group in connection_groups.items():
            if source_ip in node_map and dest_ip in node_map:
                # Aggregate connection data
                total_bytes = sum(c["bytes_sent"] + c["bytes_received"] for c in conn_group)
                protocols = list(set(c["protocol"] for c in conn_group))
                
                edge = TopologyEdge(
                    id=str(uuid.uuid4()),
                    source_node_id=node_map[source_ip],
                    target_node_id=node_map[dest_ip],
                    connection_type=self.network_utils.determine_connection_type(protocols),
                    metadata={
                        "total_bytes": total_bytes,
                        "protocols": protocols,
                        "connection_count": len(conn_group)
                    }
                )
                edges.append(edge)
        
        # Create topology
        topology = NetworkTopology(
            id=str(uuid.uuid4()),
            name=f"Log Analysis {analysis_id}",
            description=f"Network topology discovered from log analysis on {datetime.now()}",
            nodes=nodes,
            edges=edges,
            created_at=datetime.now()
        )
        
        return topology
    
    async def parse_extrahop_logs(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse ExtraHop log files"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Convert DataFrame to list of dictionaries
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error parsing ExtraHop logs: {str(e)}")
            raise
    
    async def parse_splunk_logs(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse Splunk log files"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Convert DataFrame to list of dictionaries
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error parsing Splunk logs: {str(e)}")
            raise
    
    async def parse_dynatrace_logs(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse DynaTrace log files"""
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Convert DataFrame to list of dictionaries
            return df.to_dict('records')
            
        except Exception as e:
            logger.error(f"Error parsing DynaTrace logs: {str(e)}")
            raise
    
    async def get_analysis_status(self, analysis_id: str) -> Optional[AnalysisProgress]:
        """Get the status of an analysis"""
        return self.active_analyses.get(analysis_id)
    
    async def get_analysis_results(self, analysis_id: str) -> Optional[NetworkTopology]:
        """Get the results of a completed analysis"""
        return self.analysis_results.get(analysis_id)
    
    async def cancel_analysis(self, analysis_id: str) -> bool:
        """Cancel a running analysis"""
        if analysis_id not in self.active_analyses:
            return False
        
        progress = self.active_analyses[analysis_id]
        if progress.status in [AnalysisStatus.RUNNING, AnalysisStatus.PENDING]:
            progress.status = AnalysisStatus.CANCELLED
            progress.completed_at = datetime.now()
            progress.current_task = "Analysis cancelled"
            logger.info(f"Cancelled log analysis {analysis_id}")
            return True
        
        return False
    
    async def get_supported_formats(self) -> List[str]:
        """Get list of supported log file formats"""
        return settings.SUPPORTED_LOG_FORMATS
    
    async def validate_log_file(self, file_path: str) -> Dict[str, Any]:
        """Validate log file format and structure"""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension not in ['.csv', '.xlsx', '.json']:
                return {"valid": False, "error": "Unsupported file format"}
            
            # Basic file size check
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > settings.MAX_FILE_SIZE_MB:
                return {"valid": False, "error": f"File too large: {file_size_mb:.1f}MB"}
            
            # Try to read the file
            if file_extension == '.csv':
                df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows
            elif file_extension == '.xlsx':
                df = pd.read_excel(file_path, nrows=5)  # Read first 5 rows
            
            return {
                "valid": True,
                "file_size_mb": file_size_mb,
                "columns": list(df.columns),
                "sample_rows": len(df)
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}