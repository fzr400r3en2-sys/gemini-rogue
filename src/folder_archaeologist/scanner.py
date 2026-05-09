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
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.files: List[FileInfo] = []
        self.folders: List[FolderInfo] = []
        self.errors: List[str] = []

    def scan(self):
        if not self.root_path.exists():
            raise FileNotFoundError(f"Target folder does not exist: {self.root_path}")
        
        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)
            
            # Check for empty folders
            if not dirs and not files:
                self.folders.append(FolderInfo(path=root_path, is_empty=True))
            else:
                self.folders.append(FolderInfo(path=root_path, is_empty=False))

            for name in files:
                file_path = root_path / name
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
