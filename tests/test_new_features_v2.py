import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from folder_archaeologist.cli import main
import sys
import shutil

@pytest.fixture
def temp_workspace(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (target / "file1.txt").write_text("hello", encoding='utf-8')
    (target / "file2.py").write_text("print('test')", encoding='utf-8')
    subdir = target / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("world" * 100, encoding='utf-8')
    return target

def test_output_dir_default(temp_workspace, tmp_path, monkeypatch):
    output_dir = tmp_path / "reports"
    
    # Simulate: python -m folder_archaeologist <target> --output-dir <reports>
    test_args = ["folder_archaeologist", str(temp_workspace), "--output-dir", str(output_dir)]
    monkeypatch.setattr(sys, "argv", test_args)
    
    main()
    
    assert output_dir.exists()
    assert (output_dir / "report.md").exists()
    assert (output_dir / "report.json").exists()
    assert (output_dir / "report.html").exists()

def test_output_dir_with_relative_paths(temp_workspace, tmp_path, monkeypatch):
    output_dir = tmp_path / "reports_rel"
    
    # Simulate: python -m folder_archaeologist <target> --output-dir <reports> --report r.md --html-report h.html
    test_args = [
        "folder_archaeologist", str(temp_workspace), 
        "--output-dir", str(output_dir),
        "--report", "r.md",
        "--html-report", "h.html"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    main()
    
    assert output_dir.exists()
    assert (output_dir / "r.md").exists()
    assert (output_dir / "h.html").exists()
    assert not (output_dir / "report.json").exists() # Should not generate if specific reports are requested?
    # Wait, my implementation says:
    # if not (args.report or args.json or args.html_report):
    #     generate all 3
    # else:
    #     only generate requested ones (joined with output_dir)
    # This matches the test assertion.

def test_open_report_mocked(temp_workspace, tmp_path, monkeypatch):
    output_dir = tmp_path / "reports_open"
    
    test_args = [
        "folder_archaeologist", str(temp_workspace), 
        "--output-dir", str(output_dir),
        "--open-report"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    with patch("folder_archaeologist.cli.open_html_report") as mock_open:
        main()
        mock_open.assert_called_once()
        args, _ = mock_open.call_args
        assert isinstance(args[0], Path)
        assert args[0].name == "report.html"

def test_html_graphs_content(temp_workspace, tmp_path, monkeypatch):
    output_dir = tmp_path / "reports_graphs"
    output_dir.mkdir()
    
    test_args = [
        "folder_archaeologist", str(temp_workspace), 
        "--html-report", str(output_dir / "test.html"),
        "--depth-summary"
    ]
    monkeypatch.setattr(sys, "argv", test_args)
    
    main()
    
    html_content = (output_dir / "test.html").read_text(encoding='utf-8')
    assert "bar-container" in html_content
    assert "bar" in html_content
    assert "階層別サマリー" in html_content
    assert "拡張子別ファイル数ランキング" in html_content
    assert "拡張子別サイズランキング" in html_content
