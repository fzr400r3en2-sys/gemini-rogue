from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from .scanner import FileInfo, FolderInfo

class Analyzer:
    def __init__(self, files: List[FileInfo], folders: List[FolderInfo], top_n: int = 20, min_size: int = 0):
        self.files = files
        self.folders = folders
        self.top_n = top_n
        self.min_size = min_size

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

        # Top Files - filtered by min_size
        accessible_files = [f for f in self.files if f.is_accessible]
        filtered_files = [f for f in accessible_files if f.size >= self.min_size]
        
        top_large = sorted(filtered_files, key=lambda x: x.size, reverse=True)[:self.top_n]
        top_old = sorted(filtered_files, key=lambda x: x.mtime)[:self.top_n]

        # Empty Folders
        empty_folders = [f.path for f in self.folders if f.is_empty]

        # Duplicates (Same size + same name) - filtered by min_size
        duplicates = defaultdict(list)
        for f in filtered_files:
            duplicates[(f.size, f.path.name)].append(f.path)
        
        duplicate_candidates = {k: v for k, v in duplicates.items() if len(v) > 1}
        # Limit duplicate candidates as well? The requirements say "ranking/display candidates" should be limited by top_n where applicable.
        # "重複候補表示" is listed under top_n.
        sorted_duplicates = sorted(duplicate_candidates.items(), key=lambda x: x[0][0], reverse=True)[:self.top_n]
        duplicate_candidates = dict(sorted_duplicates)

        return {
            "summary": {
                "total_files": total_files,
                "total_folders": total_folders,
                "total_size": total_size,
                "top_n": self.top_n,
                "max_depth": getattr(self, 'max_depth', None), # Placeholder if needed, but cli handles it
                "min_size": self.min_size
            },
            "extensions_count": sorted(ext_counter.items(), key=lambda x: x[1], reverse=True)[:self.top_n],
            "extensions_size": sorted(ext_size.items(), key=lambda x: x[1], reverse=True)[:self.top_n],
            "years_count": sorted(year_counter.items(), reverse=True),
            "top_large": top_large,
            "top_old": top_old,
            "empty_folders": empty_folders,
            "duplicate_candidates": duplicate_candidates
        }
