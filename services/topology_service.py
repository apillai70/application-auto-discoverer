# services/topology_service.py
"""
Service for managing network topology operations
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from models.topology_models import (
    LogAnalysisRequest, NetworkTopology, TopologyNode, 
    TopologyEdge, AnalysisProgress, AnalysisStatus
)
from services.log_analysis_service import LogAnalysisService

logger = logging.getLogger(__name__)

class TopologyService:
    """Service for managing network topology operations"""
    
    def __init__(self):
        self.log_analysis_service = LogAnalysisService()
        self.active_analyses: Dict[str, AnalysisProgress] = {}
        self.topologies: Dict[str, NetworkTopology] = {}
        self.analysis_results: Dict[str, NetworkTopology] = {}
    
    async def start_analysis(self, request: LogAnalysisRequest) -> str:
        """Start a new topology analysis"""
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
        logger.info(f"Started topology analysis {analysis_id}")
        return analysis_id
    
    async def execute_analysis(self, analysis_id: str):
        """Execute the analysis in the background"""
        if analysis_id not in self.active_analyses:
            logger.error(f"Analysis {analysis_id} not found")
            return
        
        # Delegate to log analysis service
        await self.log_analysis_service.process_log_file(analysis_id)
    
    async def get_analysis_status(self, analysis_id: str) -> Optional[AnalysisProgress]:
        """Get the status of an analysis"""
        return self.active_analyses.get(analysis_id)
    
    async def get_analysis_results(self, analysis_id: str) -> Optional[NetworkTopology]:
        """Get analysis results"""
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
            logger.info(f"Cancelled analysis {analysis_id}")
            return True
        
        return False
