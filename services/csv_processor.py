"""
CSV Processing Service
Handles CSV file processing with proper error handling and memory management
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVProcessor:
    """Service for processing CSV files with enhanced error handling"""
    
    def __init__(self, max_rows: int = 100000, chunk_size: int = 10000):
        self.max_rows = max_rows
        self.chunk_size = chunk_size
        self.encoding_options = ['utf-8', 'windows-1252', 'iso-8859-1', 'cp1252']
        
        # Classification rules for archetype detection
        self.classification_rules = self._load_classification_rules()
    
    def _load_classification_rules(self) -> Dict:
        """Load classification rules with fallback"""
        try:
            import yaml
            yaml_path = Path("templates/archetype_templates.yaml")
            if yaml_path.exists():
                with open(yaml_path, 'r') as f:
                    return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load classification rules: {e}")
        
        # Fallback rules
        return {
            'archetypes': {
                'three_tier': {'name': '3-Tier'},
                'microservices': {'name': 'Microservices'},
                'monolithic': {'name': 'Monolithic'}
            },
            'port_database': {
                'well_known': {
                    80: {'category': 'web', 'service': 'HTTP'},
                    443: {'category': 'web', 'service': 'HTTPS'},
                    3306: {'category': 'database', 'service': 'MySQL'},
                    5432: {'category': 'database', 'service': 'PostgreSQL'}
                }
            },
            'scoring_weights': {
                'required_ports_match': 10,
                'optional_ports_match': 3,
                'forbidden_violation': -15
            }
        }
    
    async def load_application_data(self, csv_path: Path) -> Tuple[List[Dict], Dict]:
        """Load and process application data from CSV"""
        if not csv_path.exists():
            logger.warning(f"CSV file not found: {csv_path}")
            return self._get_demo_applications(), {"source": "demo_data"}
        
        try:
            # Load CSV with encoding detection
            df = await self._load_csv_with_encoding(csv_path)
            if df is None:
                return self._get_demo_applications(), {"source": "demo_data", "error": "encoding_failed"}
            
            # Check file size
            if len(df) > self.max_rows:
                logger.warning(f"CSV too large ({len(df)} rows), truncating to {self.max_rows}")
                df = df.head(self.max_rows)
            
            # Process applications
            applications = []
            processing_stats = {
                "total_rows": len(df),
                "processed_apps": 0,
                "skipped_apps": 0,
                "errors": []
            }
            
            for idx, row in df.iterrows():
                try:
                    app = await self._process_application_row(row, idx)
                    if app:
                        applications.append(app)
                        processing_stats["processed_apps"] += 1
                    else:
                        processing_stats["skipped_apps"] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing row {idx}: {str(e)}"
                    logger.error(error_msg)
                    processing_stats["errors"].append(error_msg)
                    processing_stats["skipped_apps"] += 1
            
            metadata = {
                "source": "csv_file",
                "file_path": str(csv_path),
                "processed_at": datetime.now().isoformat(),
                "stats": processing_stats
            }
            
            logger.info(f"Processed {processing_stats['processed_apps']} applications from CSV")
            return applications, metadata
            
        except Exception as e:
            logger.error(f"Critical error processing CSV {csv_path}: {e}")
            return self._get_demo_applications(), {
                "source": "demo_data", 
                "error": str(e)
            }
    
    async def _load_csv_with_encoding(self, csv_path: Path) -> Optional[pd.DataFrame]:
        """Load CSV with automatic encoding detection"""
        for encoding in self.encoding_options:
            try:
                logger.info(f"Attempting to load CSV with {encoding} encoding")
                df = pd.read_csv(csv_path, encoding=encoding)
                logger.info(f"Successfully loaded CSV with {encoding} encoding: {len(df)} rows")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error loading CSV with {encoding}: {e}")
                continue
        
        logger.error("Failed to load CSV with any encoding")
        return None
    
    async def _process_application_row(self, row: pd.Series, idx: int) -> Optional[Dict]:
        """Process a single application row"""
        try:
            # Extract basic information
            app_name = self._safe_string(row.get('app_name') or row.get('name') or row.get('application_name'))
            if not app_name:
                return None
            
            app_id = self._safe_string(row.get('app_id') or row.get('id')) or self._generate_app_id(app_name)
            
            # Extract owner/team information
            owner = self._safe_string(
                row.get('owner') or 
                row.get('team') or 
                row.get('responsible_team') or 
                "Unknown"
            )
            
            # Extract application type
            app_type = self._safe_string(
                row.get('type') or 
                row.get('application_type') or 
                row.get('app_type') or 
                "application"
            )
            
            # Extract environment
            environment = self._safe_string(
                row.get('environment') or 
                row.get('env') or 
                "production"
            )
            
            # Generate archetype based on available data
            archetype = await self._classify_application(app_name, row)
            
            # Create application object
            application = {
                "id": app_id,
                "name": app_name,
                "archetype": archetype,
                "type": app_type,
                "owner": owner,
                "environment": environment,
                "status": self._determine_status(row),
                "x": float(abs(hash(app_name)) % 800),
                "y": float((abs(hash(app_name)) // 800) % 600),
                "metadata": {
                    "row_index": idx,
                    "processing_timestamp": datetime.now().isoformat()
                }
            }
            
            # Add optional fields if available
            if 'description' in row and pd.notna(row['description']):
                application['description'] = self._safe_string(row['description'])
            
            if 'technology' in row and pd.notna(row['technology']):
                application['technology'] = self._safe_string(row['technology'])
            
            return application
            
        except Exception as e:
            logger.error(f"Error processing application row {idx}: {e}")
            return None
    
    def _safe_string(self, value: Any) -> str:
        """Safely convert value to string"""
        if pd.isna(value):
            return ""
        return str(value).strip()
    
    def _generate_app_id(self, app_name: str) -> str:
        """Generate consistent app ID from name"""
        # Remove special characters and create abbreviation
        clean_name = re.sub(r'[^\w\s]', '', app_name)
        words = clean_name.split()
        
        if len(words) >= 2:
            # Use first letters of first few words
            id_parts = [word[0].upper() for word in words[:3] if word]
        else:
            # Use first 3 characters
            id_parts = [app_name[:3].upper()]
        
        # Add hash for uniqueness
        hash_suffix = str(abs(hash(app_name)) % 1000).zfill(3)
        return ''.join(id_parts) + hash_suffix
    
    async def _classify_application(self, app_name: str, row: pd.Series) -> str:
        """Classify application into archetype"""
        try:
            # Name-based classification
            app_name_lower = app_name.lower()
            
            # Direct keyword matching
            if any(word in app_name_lower for word in ['api', 'service', 'micro']):
                return 'Microservices'
            elif any(word in app_name_lower for word in ['web', 'portal', 'ui', 'frontend']):
                return 'Web + API Headless'
            elif any(word in app_name_lower for word in ['db', 'database', 'data']):
                return 'Client-Server'
            elif any(word in app_name_lower for word in ['message', 'queue', 'kafka', 'mq']):
                return 'Event-Driven'
            elif any(word in app_name_lower for word in ['mainframe', 'cobol', 'legacy']):
                return 'Mainframe'
            elif any(word in app_name_lower for word in ['batch', 'etl', 'pipeline']):
                return 'ETL/Data Pipeline'
            
            # Technology-based classification
            technology = self._safe_string(row.get('technology', ''))
            if technology:
                tech_lower = technology.lower()
                if any(word in tech_lower for word in ['spring', 'docker', 'kubernetes']):
                    return 'Microservices'
                elif any(word in tech_lower for word in ['react', 'angular', 'vue']):
                    return 'Web + API Headless'
                elif any(word in tech_lower for word in ['oracle', 'sql', 'postgres']):
                    return 'Client-Server'
            
            # Default classification
            return '3-Tier'
            
        except Exception as e:
            logger.error(f"Error classifying application {app_name}: {e}")
            return '3-Tier'
    
    def _determine_status(self, row: pd.Series) -> str:
        """Determine application status from row data"""
        status = self._safe_string(row.get('status', '')).lower()
        
        if status in ['active', 'running', 'production', 'prod']:
            return 'active'
        elif status in ['inactive', 'stopped', 'deprecated']:
            return 'inactive'
        elif status in ['development', 'dev', 'testing', 'test']:
            return 'development'
        else:
            return 'active'  # Default assumption
    
    def _get_demo_applications(self) -> List[Dict]:
        """Get demo applications when CSV processing fails"""
        return [
            {
                "id": "DEMO001",
                "name": "Customer Web Portal",
                "archetype": "Web + API Headless",
                "type": "web_application",
                "owner": "Digital Banking Team",
                "environment": "production",
                "status": "active",
                "x": 200.0,
                "y": 150.0,
                "metadata": {
                    "demo": True,
                    "generated_at": datetime.now().isoformat()
                }
            },
            {
                "id": "DEMO002",
                "name": "Core Banking API",
                "archetype": "Microservices",
                "type": "api_service",
                "owner": "Core Banking Team",
                "environment": "production",
                "status": "active",
                "x": 400.0,
                "y": 200.0,
                "metadata": {
                    "demo": True,
                    "generated_at": datetime.now().isoformat()
                }
            },
            {
                "id": "DEMO003",
                "name": "Payment Processing Engine",
                "archetype": "Event-Driven",
                "type": "service",
                "owner": "Payments Team",
                "environment": "production",
                "status": "active",
                "x": 300.0,
                "y": 350.0,
                "metadata": {
                    "demo": True,
                    "generated_at": datetime.now().isoformat()
                }
            },
            {
                "id": "DEMO004",
                "name": "Customer Database",
                "archetype": "Client-Server",
                "type": "database",
                "owner": "Data Management Team",
                "environment": "production",
                "status": "active",
                "x": 500.0,
                "y": 250.0,
                "metadata": {
                    "demo": True,
                    "generated_at": datetime.now().isoformat()
                }
            }
        ]
    
    async def validate_csv_structure(self, csv_path: Path) -> Dict[str, Any]:
        """Validate CSV structure and return analysis"""
        if not csv_path.exists():
            return {"valid": False, "error": "File not found"}
        
        try:
            # Load just the header and first few rows
            df = await self._load_csv_with_encoding(csv_path)
            if df is None:
                return {"valid": False, "error": "Could not read file with any encoding"}
            
            sample_df = df.head(5)
            
            # Analyze structure
            analysis = {
                "valid": True,
                "total_rows": len(df),
                "columns": list(df.columns),
                "sample_data": sample_df.to_dict('records'),
                "required_columns": {
                    "app_name": any(col.lower() in ['app_name', 'name', 'application_name'] for col in df.columns),
                    "app_id": any(col.lower() in ['app_id', 'id'] for col in df.columns)
                },
                "optional_columns": {
                    "owner": any(col.lower() in ['owner', 'team'] for col in df.columns),
                    "type": any(col.lower() in ['type', 'app_type'] for col in df.columns),
                    "technology": any(col.lower() in ['technology', 'tech'] for col in df.columns)
                },
                "recommendations": []
            }
            
            # Add recommendations
            if not analysis["required_columns"]["app_name"]:
                analysis["recommendations"].append("Add 'app_name' or 'name' column for application names")
            
            if not analysis["required_columns"]["app_id"]:
                analysis["recommendations"].append("Add 'app_id' or 'id' column for unique identifiers")
            
            if len(df) > self.max_rows:
                analysis["recommendations"].append(f"File has {len(df)} rows, only first {self.max_rows} will be processed")
            
            return analysis
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "recommendations": ["Check file format and encoding"]
            }