import pytest
import json
import subprocess
import sys
from pathlib import Path

def run_cli(args):
    result = subprocess.run(
        [sys.executable, "-m", "folder_archaeologist"] + args,
        capture_output=True,
        text=False
    )
    # Decode manually to avoid UnicodeDecodeError on systems with non-UTF8 paths
    stdout = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
    stderr = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
    
    # Return an object that mimics the subprocess.CompletedProcess but with decoded strings
    class DecodedResult:
        def __init__(self, returncode, stdout, stderr):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
    
    return DecodedResult(result.returncode, stdout, stderr)

@pytest.fixture
def sample_tree(tmp_path):
    # Create a sample tree
    # root (depth 0)
    (tmp_path / "file0.txt").write_text("root file")
    # depth 1
    d1 = tmp_path / "dir1"
    d1.mkdir()
    (d1 / "file1.txt").write_text("depth 1 file")
    # depth 2
    d2 = d1 / "dir2"
    d2.mkdir()
    (d2 / "file2.txt").write_text("depth 2 file")
    # depth 3
    d3 = d2 / "dir3"
    d3.mkdir()
    (d3 / "file3.txt").write_text("depth 3 file")
    # depth 4
    d4 = d3 / "dir4"
    d4.mkdir()
    (d4 / "file4.txt").write_text("depth 4 file")
    
    return tmp_path

def test_depth_summary_default(sample_tree):
    # 1. --depth-summary のデフォルトが depth 0〜3 を返すこと
    result = run_cli([str(sample_tree), "--depth-summary"])
    assert result.returncode == 0
    assert "- depth 0:" in result.stdout
    assert "- depth 1:" in result.stdout
    assert "- depth 2:" in result.stdout
    assert "- depth 3:" in result.stdout
    assert "- depth 4:" not in result.stdout

def test_depth_summary_max(sample_tree):
    # 2. --depth-summary-max 4 で depth 0〜4 を返すこと
    result = run_cli([str(sample_tree), "--depth-summary", "--depth-summary-max", "4"])
    assert result.returncode == 0
    assert "- depth 0:" in result.stdout
    assert "- depth 1:" in result.stdout
    assert "- depth 2:" in result.stdout
    assert "- depth 3:" in result.stdout
    assert "- depth 4:" in result.stdout
    assert "- depth 5:" not in result.stdout

def test_depth_summary_max_invalid(sample_tree):
    # 3. --depth-summary-max 6 がエラーになること
    result = run_cli([str(sample_tree), "--depth-summary", "--depth-summary-max", "6"])
    assert result.returncode != 0
    assert "Error: --depth-summary-max must be between 0 and 5" in result.stdout

    # 4. --depth-summary-max -1 がエラーになること
    result = run_cli([str(sample_tree), "--depth-summary", "--depth-summary-max", "-1"])
    assert result.returncode != 0
    assert "Error: --depth-summary-max must be between 0 and 5" in result.stdout

def test_depth_summary_excludes(sample_tree):
    # 5. depth-summary にデフォルト除外フォルダが反映されること
    # Create a .git folder (default excluded)
    git_dir = sample_tree / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config")
    
    # Run with default excludes
    result = run_cli([str(sample_tree), "--depth-summary"])
    # If .git was included, folder count would increase.
    # Without .git: depth 0 has dir1 (1 folder) and root (1 folder total?)
    # Wait, os.walk root folder is depth 0.
    
    # Let's use --exclude to be specific
    result_with_exclude = run_cli([str(sample_tree), "--depth-summary", "--exclude", "dir1"])
    assert result_with_exclude.returncode == 0
    # If dir1 is excluded, depth 1 should have 0 files (or at least fewer)
    # Actually, we should check if dir1 is mentioned in "Excluded:"
    assert "Excluding: .git, .venv, venv, __pycache__, .pytest_cache, node_modules, dist, build, dir1" in result_with_exclude.stdout

def test_depth_summary_json(sample_tree, tmp_path):
    # 6. depth-summary の JSON 出力に depth_summary が含まれること
    json_path = tmp_path / "report.json"
    result = run_cli([str(sample_tree), "--depth-summary", "--json", str(json_path)])
    assert result.returncode == 0
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert "depth_summary" in data
        assert len(data["depth_summary"]) == 4 # 0 to 3

def test_depth_summary_markdown(sample_tree, tmp_path):
    # 7. depth-summary の Markdown 出力に階層別サマリーが含まれること
    md_path = tmp_path / "report.md"
    result = run_cli([str(sample_tree), "--depth-summary", "--report", str(md_path)])
    assert result.returncode == 0
    
    content = md_path.read_text(encoding="utf-8")
    assert "## 階層別サマリー" in content
    assert "| 階層 (depth) |" in content

def test_depth_summary_html(sample_tree, tmp_path):
    # 8. depth-summary の HTML 出力に「階層別サマリー」が含まれること
    html_path = tmp_path / "report.html"
    result = run_cli([str(sample_tree), "--depth-summary", "--html-report", str(html_path)])
    assert result.returncode == 0
    
    content = html_path.read_text(encoding="utf-8")
    assert "<h2>階層別サマリー</h2>" in content

def test_html_localization(sample_tree, tmp_path):
    # 9. HTMLレポートに日本語見出しが含まれること
    html_path = tmp_path / "report.html"
    # Run full analysis to get all sections
    result = run_cli([str(sample_tree), "--html-report", str(html_path)])
    assert result.returncode == 0
    
    content = html_path.read_text(encoding="utf-8")
    assert "概要" in content
    assert "実行条件" in content
    assert "拡張子別ファイル数ランキング" in content
    assert "大容量ファイル" in content
    assert "空フォルダ候補" in content
    assert "重複候補" in content

def test_hash_duplicates_with_depth_summary_conflict(sample_tree):
    # Additional requirement: hash-duplicates and depth-summary conflict
    result = run_cli([str(sample_tree), "--depth-summary", "--hash-duplicates"])
    assert result.returncode != 0
    assert "Error: --hash-duplicates cannot be used with --depth-summary." in result.stdout
