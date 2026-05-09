import pytest
from pathlib import Path
from folder_archaeologist.scanner import Scanner
from folder_archaeologist.analyzer import Analyzer
from folder_archaeologist.report import Reporter
import json

@pytest.fixture
def sample_stats():
    root = Path("tests/fixtures/sample_tree")
    scanner = Scanner(str(root))
    scanner.scan()
    return scanner.get_stats()

def test_top_n_ranking(sample_stats):
    # There are 4 files in sample_tree: test1.txt, test2.txt, subdir/image.png, subdir/test1.txt
    # Extensions: .txt (3), .png (1)
    analyzer = Analyzer(sample_stats['files'], sample_stats['folders'], top_n=1)
    analysis = analyzer.analyze()
    
    assert len(analysis['extensions_count']) == 1
    assert len(analysis['extensions_size']) == 1
    assert len(analysis['top_large']) == 1
    assert len(analysis['top_old']) == 1
    assert len(analysis['duplicate_candidates']) <= 1

def test_max_depth_0():
    root = Path("tests/fixtures/sample_tree")
    # depth 0 should only see files/folders in root
    # root: test1.txt, test2.txt, empty_dir/, subdir/
    scanner = Scanner(str(root), max_depth=0)
    scanner.scan()
    stats = scanner.get_stats()
    
    # Files in root: test1.txt, test2.txt
    file_names = [f.path.name for f in stats['files']]
    assert "test1.txt" in file_names
    assert "test2.txt" in file_names
    assert "image.png" not in file_names # in subdir
    
    # Folders: root itself is counted
    folder_paths = [Path(f.path).resolve() for f in stats['folders']]
    assert root.resolve() in folder_paths
    assert not any("subdir" in str(p) and root.resolve() != p for p in folder_paths)

def test_max_depth_1():
    root = Path("tests/fixtures/sample_tree")
    # depth 1 should see root and its immediate children
    scanner = Scanner(str(root), max_depth=1)
    scanner.scan()
    stats = scanner.get_stats()
    
    file_names = [f.path.name for f in stats['files']]
    assert "test1.txt" in file_names
    assert "test2.txt" in file_names
    assert "image.png" in file_names # in subdir (depth 1)
    
    # Folders should include root, empty_dir, and subdir
    assert len(stats['folders']) == 3

def test_min_size_filtering(sample_stats):
    # root/test1.txt (7 bytes), root/test2.txt (7 bytes)
    # subdir/test1.txt (7 bytes), subdir/image.png (Large? It's a small png actually)
    # Let's set min_size to 8 to exclude the txt files
    analyzer = Analyzer(sample_stats['files'], sample_stats['folders'], min_size=8)
    analysis = analyzer.analyze()
    
    # Summary should be unchanged
    assert analysis['summary']['total_files'] == 4
    
    # Rankings should only have files >= 8 bytes
    for f in analysis['top_large']:
        assert f.size >= 8
    
    for f in analysis['top_old']:
        assert f.size >= 8
        
    for (size, name), paths in analysis['duplicate_candidates'].items():
        assert size >= 8

def test_report_settings_inclusion(sample_stats):
    settings = {"top_n": 5, "max_depth": 2, "min_size": 100}
    analyzer = Analyzer(sample_stats['files'], sample_stats['folders'], top_n=5, min_size=100)
    analysis = analyzer.analyze()
    reporter = Reporter(analysis, [], settings=settings)
    
    # JSON
    json_report = json.loads(reporter.to_json())
    assert json_report['settings']['top_n'] == 5
    assert json_report['settings']['max_depth'] == 2
    assert json_report['settings']['min_size'] == 100
    
    # Markdown
    md_report = reporter.to_markdown()
    assert "**Top-N**: 5" in md_report
    assert "**Max-Depth**: 2" in md_report
    assert "100.00 B" in md_report # format_size(100)
