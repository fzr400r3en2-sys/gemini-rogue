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
    parser.add_argument("--html-report", help="Path to save HTML report")
    parser.add_argument("--no-default-excludes", action="store_true", help="Disable default excludes")
    parser.add_argument("--exclude", action="append", help="Additional folders to exclude (can be specified multiple times)")
    parser.add_argument("--top-n", type=int, default=20, help="Number of items in rankings (default: 20)")
    parser.add_argument("--max-depth", type=int, help="Maximum recursion depth (0: root only, default: unlimited)")
    parser.add_argument("--min-size", type=int, default=0, help="Minimum file size in bytes to be included in rankings (default: 0)")
    parser.add_argument("--hash-duplicates", action="store_true", help="Identify duplicates by SHA-256 hash (same size only)")
    
    args = parser.parse_args()
    
    target_path = Path(args.target)
    if not target_path.is_dir():
        print(f"Error: {target_path} is not a directory or does not exist.")
        sys.exit(1)

    # Validation
    if args.top_n <= 0:
        print("Error: --top-n must be greater than 0.")
        sys.exit(1)
    if args.max_depth is not None and args.max_depth < 0:
        print("Error: --max-depth must be 0 or greater.")
        sys.exit(1)
    if args.min_size < 0:
        print("Error: --min-size must be 0 or greater.")
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
        
    settings = {
        "top_n": args.top_n,
        "max_depth": args.max_depth,
        "min_size": args.min_size,
        "hash_duplicates": args.hash_duplicates
    }

    scanner = Scanner(args.target, excludes=excludes, max_depth=args.max_depth)
    try:
        scanner.scan()
    except Exception as e:
        print(f"Error during scan: {e}")
        sys.exit(1)
        
    stats = scanner.get_stats()
    analyzer = Analyzer(
        stats['files'], 
        stats['folders'], 
        top_n=args.top_n, 
        min_size=args.min_size,
        hash_duplicates=args.hash_duplicates
    )
    analysis = analyzer.analyze()
    
    reporter = Reporter(analysis, stats['errors'], excludes=excludes, settings=settings)
    
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

    if args.html_report:
        html_path = Path(args.html_report)
        try:
            html_path.write_text(reporter.to_html(), encoding='utf-8')
            print(f"HTML report saved to {html_path}")
        except Exception as e:
            print(f"Error saving HTML report: {e}")

if __name__ == "__main__":
    main()
