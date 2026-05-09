import pytest
import json
from pathlib import Path
from folder_archaeologist.scanner import Scanner, FileInfo
from folder_archaeologist.analyzer import Analyzer
from folder_archaeologist.report import Reporter

def test_report_formats():
    root = Path("tests/fixtures/sample_tree")
    scanner = Scanner(str(root))
    scanner.scan()
    stats = scanner.get_stats()
    
    analyzer = Analyzer(stats['files'], stats['folders'])
    analysis = analyzer.analyze()
    
    reporter = Reporter(analysis, stats['errors'])
    
    md = reporter.to_markdown()
    assert "# フォルダ解析レポート" in md
    assert "## 概要" in md
    assert ".txt" in md
    
    js = reporter.to_json()
    data = json.loads(js)
    assert data['summary']['total_files'] == 4
    assert 'errors' in data

def test_html_escape():
    import html
    
    # Create fake files with tricky names (avoiding '/' because WindowsPath converts it to '\')
    tricky_names = [
        '<script>alert(1)_.txt',
        'a&b.txt',
        'quote"test.txt'
    ]
    
    files = []
    for i, name in enumerate(tricky_names):
        files.append(FileInfo(path=Path(name), size=100*i, mtime=1600000000.0, extension=".txt", depth=0))
    
    analyzer = Analyzer(files=files, folders=[])
    analysis = analyzer.analyze()
    
    # Simulate empty folder with tricky name
    analysis['empty_folders'] = [Path('<dir>&')]
    
    reporter = Reporter(analysis, errors=[])
    html_output = reporter.to_html()
    
    # Ensure they are escaped
    assert html.escape('<script>alert(1)_.txt') in html_output
    assert html.escape('a&b.txt') in html_output
    assert html.escape('quote"test.txt') in html_output
    assert html.escape('<dir>&') in html_output
    
    # Ensure raw unescaped strings are NOT present
    assert '<script>alert(1)' not in html_output
