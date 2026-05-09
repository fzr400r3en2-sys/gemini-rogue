import pytest
from pathlib import Path
from folder_archaeologist.scanner import Scanner

def test_scanner_basic():
    root = Path("tests/fixtures/sample_tree")
    scanner = Scanner(str(root))
    scanner.scan()
    stats = scanner.get_stats()
    
    # test1.txt, test2.txt, subdir/image.png, subdir/test1.txt
    assert len(stats['files']) == 4
    # root, subdir, empty_dir
    assert len(stats['folders']) == 3
    
    extensions = [f.extension for f in stats['files']]
    assert ".txt" in extensions
    assert ".png" in extensions

def test_scanner_empty_dir():
    root = Path("tests/fixtures/sample_tree")
    scanner = Scanner(str(root))
    scanner.scan()
    stats = scanner.get_stats()
    
    empty_folders = [f for f in stats['folders'] if f.is_empty]
    assert any("empty_dir" in str(f.path) for f in empty_folders)
