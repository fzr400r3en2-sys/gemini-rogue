import argparse
import sys
from pathlib import Path
from .scanner import Scanner
from .analyzer import Analyzer
from .report import Reporter

def main():
    parser = argparse.ArgumentParser(description="Folder Archaeology Tool")
    parser.add_argument("target", help="Target folder to analyze")
    parser.add_argument("--report", help="Path to save Markdown report")
    parser.add_argument("--json", help="Path to save JSON report")
    
    args = parser.parse_args()
    
    target_path = Path(args.target)
    if not target_path.is_dir():
        print(f"Error: {target_path} is not a directory or does not exist.")
        sys.exit(1)
        
    print(f"Scanning {target_path}...")
    scanner = Scanner(args.target)
    try:
        scanner.scan()
    except Exception as e:
        print(f"Error during scan: {e}")
        sys.exit(1)
        
    stats = scanner.get_stats()
    analyzer = Analyzer(stats['files'], stats['folders'])
    analysis = analyzer.analyze()
    
    reporter = Reporter(analysis, stats['errors'])
    
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
