import os
import glob
from pathlib import Path
from typing import Optional, List, Dict
import json
from datetime import datetime

class FileDiscoveryService:
    def __init__(self, data_staging_dir: str = "data_staging"):
        self.data_staging_dir = Path(data_staging_dir)
        self.processed_dir = self.data_staging_dir / "processed"
        self.failed_dir = self.data_staging_dir / "failed"
        self.pending_dir = self.data_staging_dir  # Root level for pending files
    
    def get_latest_processed_csv(self, pattern: str = "*traffic*.csv") -> Optional[str]:
        """Get the most recently processed CSV file"""
        if not self.processed_dir.exists():
            return None
            
        csv_files = list(self.processed_dir.glob(pattern))
        if not csv_files:
            return None
        
        # Sort by modification time, get the latest
        latest_file = max(csv_files, key=lambda f: f.stat().st_mtime)
        return latest_file.name
    
    def get_pending_csv_files(self, pattern: str = "*.csv") -> List[str]:
        """Get CSV files waiting to be processed (in root data_staging)"""
        csv_files = []
        for file_path in self.data_staging_dir.glob(pattern):
            # Only include files in root directory (not in subdirectories)
            if file_path.parent == self.data_staging_dir:
                csv_files.append(file_path.name)
        return sorted(csv_files, key=lambda f: (self.data_staging_dir / f).stat().st_mtime, reverse=True)
    
    def get_current_active_csv(self) -> Optional[str]:
        """Get the CSV file that should be used by the frontend
        Priority: 1) Latest processed, 2) Latest pending, 3) None
        """
        # First, try to get latest processed file
        latest_processed = self.get_latest_processed_csv()
        if latest_processed:
            return f"processed/{latest_processed}"
        
        # If no processed files, check for pending files
        pending_files = self.get_pending_csv_files("*traffic*.csv")
        if pending_files:
            return pending_files[0]  # Most recent pending
        
        return None
    
    def get_file_status_report(self) -> Dict:
        """Complete status of all CSV files in the pipeline"""
        processed_files = list(self.processed_dir.glob("*.csv")) if self.processed_dir.exists() else []
        failed_files = list(self.failed_dir.glob("*.csv")) if self.failed_dir.exists() else []
        pending_files = self.get_pending_csv_files()
        
        current_file = self.get_current_active_csv()
        
        return {
            "current_active_file": current_file,
            "current_endpoint": f"/data_staging/{current_file}" if current_file else None,
            "status": {
                "processed": {
                    "count": len(processed_files),
                    "files": [f.name for f in sorted(processed_files, key=lambda f: f.stat().st_mtime, reverse=True)]
                },
                "failed": {
                    "count": len(failed_files), 
                    "files": [f.name for f in sorted(failed_files, key=lambda f: f.stat().st_mtime, reverse=True)]
                },
                "pending": {
                    "count": len(pending_files),
                    "files": pending_files
                }
            },
            "last_updated": datetime.now().isoformat()
        }