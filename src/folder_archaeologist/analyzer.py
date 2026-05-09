from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from .scanner import FileInfo, FolderInfo

class Analyzer:
    def __init__(self, files: List[FileInfo], folders: List[FolderInfo]):
        self.files = files
        self.folders = folders

    def analyze(self) -> Dict[str, Any]:
        total_files = len(self.files)
        total_folders = len(self.folders)
        total_size = sum(f.size for f in self.files if f.is_accessible)

        # Extensions
        ext_counter = Counter(f.extension for f in self.files if f.is_accessible)
        ext_size = defaultdict(int)
        for f in self.files:
            if f.is_accessible:
                ext_size[f.extension] += f.size

        # Years
        year_counter = Counter(datetime.fromtimestamp(f.mtime).year for f in self.files if f.is_accessible)

        # Top Files
        accessible_files = [f for f in self.files if f.is_accessible]
        top_large = sorted(accessible_files, key=lambda x: x.size, reverse=True)[:20]
        top_old = sorted(accessible_files, key=lambda x: x.mtime)[:20]

        # Empty Folders
        empty_folders = [f.path for f in self.folders if f.is_empty]

        # Duplicates (Same size + same name)
        duplicates = defaultdict(list)
        for f in accessible_files:
            duplicates[(f.size, f.path.name)].append(f.path)
        
        duplicate_candidates = {k: v for k, v in duplicates.items() if len(v) > 1}

        return {
            "summary": {
                "total_files": total_files,
                "total_folders": total_folders,
                "total_size": total_size
            },
            "extensions_count": sorted(ext_counter.items(), key=lambda x: x[1], reverse=True),
            "extensions_size": sorted(ext_size.items(), key=lambda x: x[1], reverse=True),
            "years_count": sorted(year_counter.items(), reverse=True),
            "top_large": top_large,
            "top_old": top_old,
            "empty_folders": empty_folders,
            "duplicate_candidates": duplicate_candidates
        }
