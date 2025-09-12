"""
File Manager Service
Handles file operations with security and cleanup
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import mimetypes
import hashlib

logger = logging.getLogger(__name__)

class FileManager:
    """Secure file management service"""
    
    def __init__(self, base_dir: Path, max_file_age_days: int = 7):
        self.base_dir = base_dir
        self.max_file_age_days = max_file_age_days
        self.allowed_extensions = {
            '.lucid', '.svg', '.pdf', '.json', '.docx', '.xlsx', 
            '.png', '.jpg', '.jpeg', '.txt', '.xml'
        }
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        
        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, content: str, filename: str, subdir: str = "") -> Path:
        """Save file with security checks"""
        try:
            # Validate filename
            safe_filename = self._sanitize_filename(filename)
            if not self._validate_extension(safe_filename):
                raise ValueError(f"Invalid file extension: {Path(safe_filename).suffix}")
            
            # Create target directory
            if subdir:
                target_dir = self.base_dir / subdir
            else:
                target_dir = self.base_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Create full path
            file_path = target_dir / safe_filename
            
            # Check content size
            content_bytes = content.encode('utf-8') if isinstance(content, str) else content
            if len(content_bytes) > self.max_file_size:
                raise ValueError(f"File too large: {len(content_bytes)} bytes")
            
            # Write file
            if isinstance(content, str):
                file_path.write_text(content, encoding='utf-8')
            else:
                file_path.write_bytes(content)
            
            logger.info(f"Saved file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise
    
    def get_file_info(self, filename: str, subdir: str = "") -> Optional[Dict]:
        """Get file information safely"""
        try:
            if subdir:
                file_path = self.base_dir / subdir / filename
            else:
                file_path = self._find_file_in_subdirs(filename)
            
            if not file_path or not file_path.exists():
                return None
            
            # Security check - ensure file is within base directory
            try:
                file_path.resolve().relative_to(self.base_dir.resolve())
            except ValueError:
                logger.warning(f"Path traversal attempt: {file_path}")
                return None
            
            stat = file_path.stat()
            
            return {
                "filename": file_path.name,
                "path": str(file_path),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": file_path.suffix,
                "mime_type": mimetypes.guess_type(str(file_path))[0],
                "checksum": self._calculate_checksum(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting file info for {filename}: {e}")
            return None
    
    def list_files(self, subdir: str = "", pattern: str = "*") -> List[Dict]:
        """List files in directory"""
        try:
            if subdir:
                search_dir = self.base_dir / subdir
            else:
                search_dir = self.base_dir
            
            if not search_dir.exists():
                return []
            
            files = []
            for file_path in search_dir.glob(pattern):
                if file_path.is_file():
                    file_info = self.get_file_info(file_path.name, subdir)
                    if file_info:
                        files.append(file_info)
            
            # Sort by modified date (newest first)
            files.sort(key=lambda x: x["modified"], reverse=True)
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {subdir}: {e}")
            return []
    
    def delete_file(self, filename: str, subdir: str = "") -> bool:
        """Delete file safely"""
        try:
            if subdir:
                file_path = self.base_dir / subdir / filename
            else:
                file_path = self._find_file_in_subdirs(filename)
            
            if not file_path or not file_path.exists():
                return False
            
            # Security check
            try:
                file_path.resolve().relative_to(self.base_dir.resolve())
            except ValueError:
                logger.warning(f"Path traversal attempt in delete: {file_path}")
                return False
            
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return False
    
    def cleanup_old_files(self) -> Dict[str, int]:
        """Clean up old files"""
        cutoff_date = datetime.now() - timedelta(days=self.max_file_age_days)
        
        deleted_count = 0
        error_count = 0
        total_size_freed = 0
        
        try:
            for file_path in self.base_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_modified < cutoff_date:
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            deleted_count += 1
                            total_size_freed += file_size
                            
                    except Exception as e:
                        logger.error(f"Error cleaning up file {file_path}: {e}")
                        error_count += 1
            
            # Clean up empty directories
            self._cleanup_empty_dirs()
            
            logger.info(f"Cleanup completed: {deleted_count} files deleted, {total_size_freed} bytes freed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            error_count += 1
        
        return {
            "deleted_files": deleted_count,
            "errors": error_count,
            "bytes_freed": total_size_freed
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_files = 0
            total_size = 0
            file_types = {}
            subdirs = {}
            
            for file_path in self.base_dir.rglob("*"):
                if file_path.is_file():
                    total_files += 1
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    
                    # Count by extension
                    extension = file_path.suffix.lower()
                    if extension in file_types:
                        file_types[extension]["count"] += 1
                        file_types[extension]["size"] += file_size
                    else:
                        file_types[extension] = {"count": 1, "size": file_size}
                    
                    # Count by subdirectory
                    try:
                        subdir = file_path.relative_to(self.base_dir).parts[0]
                        if subdir in subdirs:
                            subdirs[subdir]["count"] += 1
                            subdirs[subdir]["size"] += file_size
                        else:
                            subdirs[subdir] = {"count": 1, "size": file_size}
                    except IndexError:
                        # File is in root directory
                        if "root" in subdirs:
                            subdirs["root"]["count"] += 1
                            subdirs["root"]["size"] += file_size
                        else:
                            subdirs["root"] = {"count": 1, "size": file_size}
            
            return {
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types,
                "subdirectories": subdirs,
                "base_directory": str(self.base_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "total_files": 0,
                "total_size": 0,
                "error": str(e)
            }
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues"""
        # Remove path components
        safe_name = Path(filename).name
        
        # Remove dangerous characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '-', safe_name)
        
        # Replace multiple spaces/dashes
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        
        # Limit length
        if len(safe_name) > 100:
            name_part = safe_name[:95]
            ext_part = Path(safe_name).suffix
            safe_name = name_part + ext_part
        
        return safe_name.strip('-')
    
    def _validate_extension(self, filename: str) -> bool:
        """Validate file extension"""
        extension = Path(filename).suffix.lower()
        return extension in self.allowed_extensions
    
    def _find_file_in_subdirs(self, filename: str) -> Optional[Path]:
        """Find file in any subdirectory"""
        # First check root directory
        root_path = self.base_dir / filename
        if root_path.exists():
            return root_path
        
        # Then check subdirectories
        for subdir in self.base_dir.iterdir():
            if subdir.is_dir():
                file_path = subdir / filename
                if file_path.exists():
                    return file_path
        
        return None
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate file checksum"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    def _cleanup_empty_dirs(self):
        """Clean up empty directories"""
        for dirpath in sorted(self.base_dir.rglob("*"), reverse=True):
            if dirpath.is_dir() and dirpath != self.base_dir:
                try:
                    if not any(dirpath.iterdir()):
                        dirpath.rmdir()
                        logger.debug(f"Removed empty directory: {dirpath}")
                except Exception:
                    pass  # Directory not empty or other error

# Utility functions for the router
def create_file_managers() -> Dict[str, FileManager]:
    """Create file managers for different result types"""
    base_results_dir = Path("results")
    
    return {
        "diagrams": FileManager(base_results_dir / "diagrams"),
        "lucid": FileManager(base_results_dir / "lucid"),
        "pdf": FileManager(base_results_dir / "pdf"),
        "excel": FileManager(base_results_dir / "excel"),
        "document": FileManager(base_results_dir / "document")
    }