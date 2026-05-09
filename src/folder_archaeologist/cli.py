import argparse
import sys
import webbrowser
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

def open_html_report(path: Path):
    """Isolate browser opening for easier mocking in tests."""
    try:
        webbrowser.open(path.absolute().as_uri())
    except Exception as e:
        print(f"Error opening report in browser: {e}")

def main():
    parser = argparse.ArgumentParser(description="Folder Archaeology Tool")
    parser.add_argument("target", help="Target folder to analyze")
    parser.add_argument("--report", help="Path to save Markdown report")
    parser.add_argument("--json", help="Path to save JSON report")
    parser.add_argument("--html-report", help="Path to save HTML report")
    parser.add_argument("--output-dir", help="Directory to save all reports")
    parser.add_argument("--open-report", action="store_true", help="Open HTML report in default browser after generation")
    parser.add_argument("--no-default-excludes", action="store_true", help="Disable default excludes")
    parser.add_argument("--exclude", action="append", help="Additional folders to exclude (can be specified multiple times)")
    parser.add_argument("--top-n", type=int, default=20, help="Number of items in rankings (default: 20)")
    parser.add_argument("--max-depth", type=int, help="Maximum recursion depth (0: root only, default: unlimited)")
    parser.add_argument("--min-size", type=int, default=0, help="Minimum file size in bytes to be included in rankings (default: 0)")
    parser.add_argument("--hash-duplicates", action="store_true", help="Identify duplicates by SHA-256 hash (same size only)")
    parser.add_argument("--depth-summary", action="store_true", help="Display summary by recursion depth")
    parser.add_argument("--depth-summary-max", type=int, default=3, help="Maximum depth for depth summary (0-5, default: 3)")
    
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
    
    if args.depth_summary:
        if args.hash_duplicates:
            print("Error: --hash-duplicates cannot be used with --depth-summary.")
            sys.exit(1)
        if args.depth_summary_max < 0 or args.depth_summary_max > 5:
            print("Error: --depth-summary-max must be between 0 and 5.")
            sys.exit(1)

    # Handle --output-dir logic
    output_dir = None
    report_md = args.report
    report_json = args.json
    report_html = args.html_report

    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                print(f"Created output directory: {output_dir}")
            except Exception as e:
                print(f"Error creating output directory: {e}")
                sys.exit(1)
        
        # If ONLY --output-dir is specified (no specific report paths)
        if not (args.report or args.json or args.html_report):
            report_md = str(output_dir / "report.md")
            report_json = str(output_dir / "report.json")
            report_html = str(output_dir / "report.html")
        else:
            # If specific report paths are provided, join them if they are relative
            if args.report and not Path(args.report).is_absolute():
                report_md = str(output_dir / args.report)
            if args.json and not Path(args.json).is_absolute():
                report_json = str(output_dir / args.json)
            if args.html_report and not Path(args.html_report).is_absolute():
                report_html = str(output_dir / args.html_report)

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
        "hash_duplicates": args.hash_duplicates,
        "depth_summary": args.depth_summary,
        "depth_summary_max": args.depth_summary_max if args.depth_summary else None
    }

    # For depth summary, we override max_depth for efficiency
    scan_max_depth = args.max_depth
    if args.depth_summary:
        scan_max_depth = args.depth_summary_max

    scanner = Scanner(args.target, excludes=excludes, max_depth=scan_max_depth)
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
        hash_duplicates=args.hash_duplicates,
        depth_summary_max=args.depth_summary_max if args.depth_summary else None
    )
    analysis = analyzer.analyze()
    
    reporter = Reporter(analysis, stats['errors'], excludes=excludes, settings=settings)
    
    reporter.to_stdout()
    
    if report_md:
        md_path = Path(report_md)
        try:
            md_path.write_text(reporter.to_markdown(), encoding='utf-8')
            print(f"Markdown report saved to {md_path}")
        except Exception as e:
            print(f"Error saving Markdown report: {e}")
            
    if report_json:
        json_path = Path(report_json)
        try:
            json_path.write_text(reporter.to_json(), encoding='utf-8')
            print(f"JSON report saved to {json_path}")
        except Exception as e:
            print(f"Error saving JSON report: {e}")

    if report_html:
        html_path = Path(report_html)
        try:
            html_path.write_text(reporter.to_html(), encoding='utf-8')
            print(f"HTML report saved to {html_path}")
            if args.open_report:
                open_html_report(html_path)
        except Exception as e:
            print(f"Error saving HTML report: {e}")

if __name__ == "__main__":
    main()
