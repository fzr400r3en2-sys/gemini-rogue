import argparse
import sys
from pathlib import Path
from .scanner import Scanner
from .analyzer import Analyzer
from .report import Reporter

DEFAULT_EXCLUDES = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "dist",
    "build"
]

def main():
    parser = argparse.ArgumentParser(description="Folder Archaeology Tool")
    parser.add_argument("target", help="Target folder to analyze")
    parser.add_argument("--report", help="Path to save Markdown report")
    parser.add_argument("--json", help="Path to save JSON report")
    parser.add_argument("--no-default-excludes", action="store_true", help="Disable default excludes")
    parser.add_argument("--exclude", action="append", help="Additional folders to exclude (can be specified multiple times)")
    
    args = parser.parse_args()
    
    target_path = Path(args.target)
    if not target_path.is_dir():
        print(f"Error: {target_path} is not a directory or does not exist.")
        sys.exit(1)

    # Prepare exclusion list
    excludes = []
    if not args.no_default_excludes:
        excludes.extend(DEFAULT_EXCLUDES)
    if args.exclude:
        excludes.extend(args.exclude)
    # Remove duplicates but maintain some order if possible (set doesn't, but list(dict.fromkeys()) does)
    excludes = list(dict.fromkeys(excludes))
        
    print(f"Scanning {target_path}...")
    if excludes:
        print(f"Excluding: {', '.join(excludes)}")
        
    scanner = Scanner(args.target, excludes=excludes)
    try:
        scanner.scan()
    except Exception as e:
        print(f"Error during scan: {e}")
        sys.exit(1)
        
    stats = scanner.get_stats()
    analyzer = Analyzer(stats['files'], stats['folders'])
    analysis = analyzer.analyze()
    
    reporter = Reporter(analysis, stats['errors'], excludes=excludes)
    
    reporter.to_stdout()
    
    if args.report:
        report_path = Path(args.report)
        try:
            report_path.write_text(reporter.to_markdown(), encoding='utf-8')
            print(f"Markdown report saved to {report_path}")
        except Exception as e:
            print(f"Error saving Markdown report: {e}")
            
    if args.json:
        json_path = Path(args.json)
        try:
            json_path.write_text(reporter.to_json(), encoding='utf-8')
            print(f"JSON report saved to {json_path}")
        except Exception as e:
            print(f"Error saving JSON report: {e}")

if __name__ == "__main__":
    main()
