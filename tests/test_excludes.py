import pytest
import shutil
import os
from pathlib import Path
from folder_archaeologist.scanner import Scanner
from folder_archaeologist.cli import DEFAULT_EXCLUDES

@pytest.fixture
def local_tmp_path():
    path = Path("tests/tmp_test_dir")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    yield path
    if path.exists():
        shutil.rmtree(path)

def test_scanner_default_excludes(local_tmp_path):
    tmp_path = local_tmp_path
    # Create a dummy structure
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "file.txt").write_text("dummy")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('hello')")
    
    # Run scanner with default excludes
    scanner = Scanner(str(tmp_path), excludes=DEFAULT_EXCLUDES)
    scanner.scan()
    stats = scanner.get_stats()
    
    # .venv should be excluded
    file_paths = [str(f.path.relative_to(tmp_path)) for f in stats['files']]
    assert not any(".venv" in p for p in file_paths)
    
    folder_paths = [str(f.path.relative_to(tmp_path)) for f in stats['folders']]
    assert not any(p == ".venv" for p in folder_paths)

def test_scanner_no_excludes(local_tmp_path):
    tmp_path = local_tmp_path
    # Create a dummy structure
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "file.txt").write_text("dummy")
    
    # Run scanner with NO excludes
    scanner = Scanner(str(tmp_path), excludes=[])
    scanner.scan()
    stats = scanner.get_stats()
    
    # .venv should NOT be excluded
    file_paths = [str(f.path.relative_to(tmp_path)) for f in stats['files']]
    assert any(".venv" in p for p in file_paths)

def test_scanner_custom_exclude(local_tmp_path):
    tmp_path = local_tmp_path
    # Create a dummy structure
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "file.txt").write_text("dummy")
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "file.txt").write_text("dummy")
    
    # Run scanner with custom exclude
    scanner = Scanner(str(tmp_path), excludes=["target"])
    scanner.scan()
    stats = scanner.get_stats()
    
    # 'target' should be excluded
    file_paths = [str(f.path.relative_to(tmp_path)) for f in stats['files']]
    assert not any("target" in p for p in file_paths)
    assert any("other" in p for p in file_paths)
