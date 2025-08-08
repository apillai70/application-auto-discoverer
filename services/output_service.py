import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from config.settings import settings
from utils.export_util import ExportUtil

logger = logging.getLogger(__name__)

class OutputService:
    """Service for managing output artifacts with app name tagging"""
    
    def __init__(self):
        self.export_util = ExportUtil()
        self._ensure_output_directories()
    
    def _ensure_output_directories(self):
        """Ensure all output directories exist"""
        directories = [
            settings.RESULTS_BASE_DIR,
            settings.EXCEL_OUTPUT_DIR,
            settings.VISIO_OUTPUT_DIR,
            settings.WORD_OUTPUT_DIR,
            settings.PDF_OUTPUT_DIR,
            settings.LUCID_OUTPUT_DIR
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
    
    def generate_filename(self, app_name: str, file_type: str, extension: str) -> str:
        """Generate filename with app name and date tag"""
        timestamp = datetime.now().strftime(settings.DATE_FORMAT)
        filename = f"{app_name}_{timestamp}_{file_type}.{extension}"
        return filename
    
    async def save_excel_output(self, data: Any, app_name: str, file_type: str = "topology") -> str:
        """Save data as Excel file with app name tag"""
        filename = self.generate_filename(app_name, file_type, "xlsx")
        file_path = os.path.join(settings.EXCEL_OUTPUT_DIR, filename)
        
        try:
            await self.export_util.export_to_excel(data, file_path)
            logger.info(f"Saved Excel output: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save Excel output: {str(e)}")
            raise
    
    async def save_visio_output(self, topology: Any, app_name: str, file_type: str = "network_diagram") -> str:
        """Save topology as Visio diagram with app name tag"""
        filename = self.generate_filename(app_name, file_type, "vsdx")
        file_path = os.path.join(settings.VISIO_OUTPUT_DIR, filename)
        
        try:
            await self.export_util.export_to_visio(topology, file_path)
            logger.info(f"Saved Visio output: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save Visio output: {str(e)}")
            raise
    
    async def save_word_output(self, documentation: Any, app_name: str, file_type: str = "documentation") -> str:
        """Save documentation as Word document with app name tag"""
        filename = self.generate_filename(app_name, file_type, "docx")
        file_path = os.path.join(settings.WORD_OUTPUT_DIR, filename)
        
        try:
            await self.export_util.export_to_word(documentation, file_path)
            logger.info(f"Saved Word output: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save Word output: {str(e)}")
            raise
    
    async def save_pdf_output(self, data: Any, app_name: str, file_type: str = "report") -> str:
        """Save data as PDF report with app name tag"""
        filename = self.generate_filename(app_name, file_type, "pdf")
        file_path = os.path.join(settings.PDF_OUTPUT_DIR, filename)
        
        try:
            await self.export_util.export_to_pdf(data, file_path)
            logger.info(f"Saved PDF output: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save PDF output: {str(e)}")
            raise
    
    async def save_lucid_output(self, topology: Any, app_name: str, file_type: str = "lucid_diagram") -> str:
        """Save topology as Lucid chart with app name tag"""
        filename = self.generate_filename(app_name, file_type, "lucid")
        file_path = os.path.join(settings.LUCID_OUTPUT_DIR, filename)
        
        try:
            await self.export_util.export_to_lucid(topology, file_path)
            logger.info(f"Saved Lucid output: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to save Lucid output: {str(e)}")
            raise
    
    async def save_all_formats(self, topology: Any, app_name: str) -> Dict[str, str]:
        """Save topology in all supported formats"""
        results = {}
        
        try:
            # Save Excel topology data
            results["excel"] = await self.save_excel_output(topology, app_name, "topology_data")
            
            # Save Visio network diagram
            results["visio"] = await self.save_visio_output(topology, app_name, "network_diagram")
            
            # Save Word documentation
            results["word"] = await self.save_word_output(topology, app_name, "network_documentation")
            
            # Save PDF report
            results["pdf"] = await self.save_pdf_output(topology, app_name, "topology_report")
            
            # Save Lucid chart
            results["lucid"] = await self.save_lucid_output(topology, app_name, "lucid_chart")
            
            logger.info(f"Saved all formats for app: {app_name}")
            return results
            
        except Exception as e:
            logger.error(f"Failed to save all formats for app {app_name}: {str(e)}")
            raise
    
    def list_outputs_for_app(self, app_name: str) -> Dict[str, List[str]]:
        """List all output files for a specific app"""
        outputs = {
            "excel": [],
            "visio": [],
            "word": [],
            "pdf": [],
            "lucid": []
        }
        
        # Search each output directory for files matching the app name
        directories = {
            "excel": settings.EXCEL_OUTPUT_DIR,
            "visio": settings.VISIO_OUTPUT_DIR,
            "word": settings.WORD_OUTPUT_DIR,
            "pdf": settings.PDF_OUTPUT_DIR,
            "lucid": settings.LUCID_OUTPUT_DIR
        }
        
        for output_type, directory in directories.items():
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.startswith(f"{app_name}_"):
                        outputs[output_type].append(filename)
        
        return outputs
    
    def cleanup_old_outputs(self, app_name: str, keep_latest: int = 5):
        """Clean up old output files, keeping only the latest N files"""
        outputs = self.list_outputs_for_app(app_name)
        
        directories = {
            "excel": settings.EXCEL_OUTPUT_DIR,
            "visio": settings.VISIO_OUTPUT_DIR,
            "word": settings.WORD_OUTPUT_DIR,
            "pdf": settings.PDF_OUTPUT_DIR,
            "lucid": settings.LUCID_OUTPUT_DIR
        }
        
        for output_type, files in outputs.items():
            if len(files) > keep_latest:
                directory = directories[output_type]
                
                # Sort files by modification time (newest first)
                file_paths = [os.path.join(directory, f) for f in files]
                file_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Remove old files
                files_to_remove = file_paths[keep_latest:]
                for file_path in files_to_remove:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed old output file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to remove file {file_path}: {str(e)}")
    
    def get_output_summary(self) -> Dict[str, Any]:
        """Get summary of all outputs"""
        summary = {
            "total_files": 0,
            "by_type": {},
            "by_app": {},
            "disk_usage": {}
        }
        
        directories = {
            "excel": settings.EXCEL_OUTPUT_DIR,
            "visio": settings.VISIO_OUTPUT_DIR,
            "word": settings.WORD_OUTPUT_DIR,
            "pdf": settings.PDF_OUTPUT_DIR,
            "lucid": settings.LUCID_OUTPUT_DIR
        }
        
        for output_type, directory in directories.items():
            if os.path.exists(directory):
                files = os.listdir(directory)
                summary["by_type"][output_type] = len(files)
                summary["total_files"] += len(files)
                
                # Calculate disk usage
                total_size = 0
                for filename in files:
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                
                summary["disk_usage"][output_type] = total_size
                
                # Track by app name
                for filename in files:
                    app_name = filename.split('_')[0]
                    if app_name not in summary["by_app"]:
                        summary["by_app"][app_name] = 0
                    summary["by_app"][app_name] += 1
        
        return summary