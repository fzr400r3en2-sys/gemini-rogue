import pytest
import shutil
import os
from pathlib import Path
from src.folder_archaeologist.scanner import Scanner, FileInfo
from src.folder_archaeologist.analyzer import Analyzer
from src.folder_archaeologist.report import Reporter

@pytest.fixture
def local_tmp_path():
    p = Path("./tmp_test_dir")
    if p.exists():
        shutil.rmtree(p)
    p.mkdir()
    yield p
    if p.exists():
        shutil.rmtree(p)

def test_hash_calculation(local_tmp_path):
    file1 = local_tmp_path / "file1.txt"
    file1.write_text("hello world")
    
    info = FileInfo(path=file1, size=file1.stat().st_size, mtime=file1.stat().st_mtime, extension=".txt")
    h = info.calculate_sha256()
    
    import hashlib
    expected = hashlib.sha256(b"hello world").hexdigest()
    assert h == expected

def test_hash_duplicates(local_tmp_path):
    file1 = local_tmp_path / "file1.txt"
    file2 = local_tmp_path / "file2.txt"
    file3 = local_tmp_path / "file3.txt"
    
    file1.write_text("same content")
    file2.write_text("same content")
    file3.write_text("different content")
    
    files = [
        FileInfo(path=file1, size=file1.stat().st_size, mtime=file1.stat().st_mtime, extension=".txt"),
        FileInfo(path=file2, size=file2.stat().st_size, mtime=file2.stat().st_mtime, extension=".txt"),
        FileInfo(path=file3, size=file3.stat().st_size, mtime=file3.stat().st_mtime, extension=".txt"),
    ]
    
    analyzer = Analyzer(files=files, folders=[], hash_duplicates=True)
    analysis = analyzer.analyze()
    
    dupes = analysis['duplicate_candidates']
    assert len(dupes) == 1
    # Key is (size, hash)
    key = list(dupes.keys())[0]
    assert len(dupes[key]) == 2
    # Convert to strings for comparison if needed, but Path objects should work
    assert any(str(p).endswith("file1.txt") for p in dupes[key])
    assert any(str(p).endswith("file2.txt") for p in dupes[key])

def test_html_report_generation():
    # Minimal data for report
    analysis = {
        "summary": {"total_files": 1, "total_folders": 0, "total_size": 10, "top_n": 5, "min_size": 0, "hash_duplicates": False},
        "extensions_count": [(".txt", 1)],
        "extensions_size": [(".txt", 10)],
        "years_count": [(2023, 1)],
        "top_large": [],
        "top_old": [],
        "empty_folders": [],
        "duplicate_candidates": {}
    }
    reporter = Reporter(analysis, errors=[], excludes=[], settings={"top_n": 5})
    html_out = reporter.to_html()
    
    assert "<!DOCTYPE html>" in html_out
    assert "フォルダ解析レポート" in html_out
    assert "総ファイル数" in html_out
