import pytest
import json
from pathlib import Path
from folder_archaeologist.scanner import Scanner
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
    assert "# Folder Archaeology Report" in md
    assert "## Summary" in md
    assert ".txt" in md
    
    js = reporter.to_json()
    data = json.loads(js)
    assert data['summary']['total_files'] == 4
    assert 'errors' in data
