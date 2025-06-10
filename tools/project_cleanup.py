#!/usr/bin/env python3
"""
CineFluent Project Cleanup Tool
Unified cleanup with smart detection
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

class ProjectCleanup:
    """Smart project cleanup"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.cleaned_files = 0
        self.total_size = 0
    
    def quick_clean(self):
        """Quick cleanup of common files"""
        print("🧹 Quick Project Cleanup")
        print("=" * 30)
        
        # Python cache
        self._remove_pattern("**/__pycache__", "Python cache directories")
        self._remove_pattern("**/*.pyc", "Python bytecode files")
        self._remove_pattern("**/*.pyo", "Python optimized files")
        
        # Logs and temp files
        self._remove_pattern("**/*.log", "Log files")
        self._remove_pattern("**/*.tmp", "Temporary files")
        self._remove_pattern("**/*.bak", "Backup files")
        self._remove_pattern("**/.*~", "Editor temp files")
        
        # System files
        self._remove_pattern("**/.DS_Store", "macOS metadata")
        self._remove_pattern("**/Thumbs.db", "Windows thumbnails")
        
        # Development caches
        self._remove_if_exists(".pytest_cache", "Pytest cache")
        self._remove_if_exists(".mypy_cache", "MyPy cache")
        self._remove_if_exists(".coverage", "Coverage data")
        self._remove_if_exists("htmlcov", "Coverage reports")
        
        print(f"\n✅ Cleanup complete!")
        print(f"📊 Files cleaned: {self.cleaned_files}")
    
    def _remove_pattern(self, pattern, description):
        """Remove files matching pattern"""
        files = list(self.project_root.glob(pattern))
        for file_path in files:
            try:
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                self.cleaned_files += 1
            except Exception as e:
                pass
        
        if files:
            print(f"  🗑️  Removed {len(files)} {description}")
    
    def _remove_if_exists(self, path, description):
        """Remove file/directory if it exists"""
        path_obj = self.project_root / path
        if path_obj.exists():
            try:
                if path_obj.is_dir():
                    shutil.rmtree(path_obj)
                else:
                    path_obj.unlink()
                print(f"  🗑️  Removed {description}")
                self.cleaned_files += 1
            except Exception as e:
                pass

if __name__ == "__main__":
    cleanup = ProjectCleanup()
    cleanup.quick_clean()
