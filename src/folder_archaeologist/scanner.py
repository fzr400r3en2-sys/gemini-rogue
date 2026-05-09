import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

@dataclass
class FileInfo:
    path: Path
    size: int
    mtime: float
    extension: str
    is_accessible: bool = True

@dataclass
class FolderInfo:
    path: Path
    is_empty: bool
    is_accessible: bool = True

class Scanner:
    def __init__(self, root_path: str, excludes: Optional[List[str]] = None, max_depth: Optional[int] = None):
        self.root_path = Path(root_path)
        self.files: List[FileInfo] = []
        self.folders: List[FolderInfo] = []
        self.errors: List[str] = []
        self.excludes = excludes or []
        self.max_depth = max_depth

    def scan(self):
        if not self.root_path.exists():
            raise FileNotFoundError(f"Target folder does not exist: {self.root_path}")
        
        # We need a consistent base for relative_to
        # If we don't resolve, relative_to might fail if paths are like "." vs "sub"
        # But if we resolve root_path, we should resolve the walking path too.
        base_path = self.root_path.resolve()

        for root, dirs, files in os.walk(self.root_path):
            current_root = Path(root)
            current_root_resolved = current_root.resolve()
            
            # Calculate current depth
            try:
                depth = len(current_root_resolved.relative_to(base_path).parts)
            except ValueError:
                # Fallback for edge cases
                depth = 0

            # Prune excluded directories
            if self.excludes:
                dirs[:] = [d for d in dirs if d not in self.excludes]
            
            # Prune directories if max_depth is reached
            if self.max_depth is not None and depth >= self.max_depth:
                dirs[:] = []

            # Check for empty folders
            if not dirs and not files:
                self.folders.append(FolderInfo(path=current_root, is_empty=True))
            else:
                self.folders.append(FolderInfo(path=current_root, is_empty=False))

            for name in files:
                file_path = current_root / name
                try:
                    stat = file_path.stat()
                    self.files.append(FileInfo(
                        path=file_path,
                        size=stat.st_size,
                        mtime=stat.st_mtime,
                        extension=file_path.suffix.lower()
                    ))
                except (PermissionError, OSError) as e:
                    self.files.append(FileInfo(
                        path=file_path,
                        size=0,
                        mtime=0,
                        extension=file_path.suffix.lower(),
                        is_accessible=False
                    ))
                    self.errors.append(f"Cannot access {file_path}: {e}")

    def get_stats(self):
        return {
            "files": self.files,
            "folders": self.folders,
            "errors": self.errors
        }
