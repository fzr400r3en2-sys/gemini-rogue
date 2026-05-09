import pytest
from pathlib import Path
from folder_archaeologist.scanner import Scanner
from folder_archaeologist.analyzer import Analyzer

def test_analyzer_basic():
    root = Path("tests/fixtures/sample_tree")
    scanner = Scanner(str(root))
    scanner.scan()
    stats = scanner.get_stats()
    
    analyzer = Analyzer(stats['files'], stats['folders'])
    analysis = analyzer.analyze()
    
    assert analysis['summary']['total_files'] == 4
    assert analysis['summary']['total_folders'] == 3
    assert analysis['summary']['total_size'] > 0
    
    # test1.txt and subdir/test1.txt should have same size and name
    # root/test1.txt is "Hello\r\n" (7 bytes)
    # subdir/test1.txt is "Hello\r\n" (7 bytes)
    # So they should be in duplicate_candidates
    assert len(analysis['duplicate_candidates']) >= 1
    
    # Extensions
    ext_counts = dict(analysis['extensions_count'])
    assert ext_counts['.txt'] == 3
    assert ext_counts['.png'] == 1

def test_analyzer_empty_folders():
    root = Path("tests/fixtures/sample_tree")
    scanner = Scanner(str(root))
    scanner.scan()
    stats = scanner.get_stats()
    
    analyzer = Analyzer(stats['files'], stats['folders'])
    analysis = analyzer.analyze()
    
    assert any("empty_dir" in str(p) for p in analysis['empty_folders'])
