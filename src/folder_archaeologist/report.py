import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

def format_size(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

class Reporter:
    def __init__(self, analysis: Dict[str, Any], errors: List[str]):
        self.analysis = analysis
        self.errors = errors

    def to_stdout(self):
        summary = self.analysis['summary']
        print("\n=== Folder Archaeology Summary ===")
        print(f"Total Files:   {summary['total_files']}")
        print(f"Total Folders: {summary['total_folders']}")
        print(f"Total Size:    {format_size(summary['total_size'])}")
        print("==================================\n")

    def to_json(self) -> str:
        # Convert Path and FileInfo objects to serializable format
        serializable = self._make_serializable(self.analysis)
        serializable['errors'] = self.errors
        return json.dumps(serializable, indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        summary = self.analysis['summary']
        lines = [
            "# Folder Archaeology Report",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Total Files: {summary['total_files']}",
            f"- Total Folders: {summary['total_folders']}",
            f"- Total Size: {format_size(summary['total_size'])}",
            "",
            "## Extensions by Count (Top 10)",
            "| Extension | Count |",
            "| --- | --- |"
        ]
        for ext, count in self.analysis['extensions_count'][:10]:
            lines.append(f"| {ext or '(no extension)'} | {count} |")
        
        lines.extend([
            "",
            "## Extensions by Size (Top 10)",
            "| Extension | Size |",
            "| --- | --- |"
        ])
        for ext, size in self.analysis['extensions_size'][:10]:
            lines.append(f"| {ext or '(no extension)'} | {format_size(size)} |")

        lines.extend([
            "",
            "## Files by Year",
            "| Year | Count |",
            "| --- | --- |"
        ])
        for year, count in self.analysis['years_count']:
            lines.append(f"| {year} | {count} |")

        lines.extend([
            "",
            "## Top 20 Large Files",
            "| File Path | Size | Last Modified |",
            "| --- | --- | --- |"
        ])
        for f in self.analysis['top_large']:
            mtime = datetime.fromtimestamp(f.mtime).strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"| {f.path} | {format_size(f.size)} | {mtime} |")

        lines.extend([
            "",
            "## Top 20 Oldest Files",
            "| File Path | Size | Last Modified |",
            "| --- | --- | --- |"
        ])
        for f in self.analysis['top_old']:
            mtime = datetime.fromtimestamp(f.mtime).strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"| {f.path} | {format_size(f.size)} | {mtime} |")

        lines.extend([
            "",
            "## Empty Folders",
        ])
        if self.analysis['empty_folders']:
            for path in self.analysis['empty_folders']:
                lines.append(f"- {path}")
        else:
            lines.append("None found.")

        lines.extend([
            "",
            "## Duplicate Candidates (Same Name & Size)",
            "| Name & Size | Paths |",
            "| --- | --- |"
        ])
        for (size, name), paths in self.analysis['duplicate_candidates'].items():
            path_list = "<br>".join(str(p) for p in paths)
            lines.append(f"| {name} ({format_size(size)}) | {path_list} |")

        if self.errors:
            lines.extend([
                "",
                "## Warnings / Errors",
            ])
            for err in self.errors:
                lines.append(f"- {err}")

        return "\n".join(lines)

    def _make_serializable(self, obj: Any) -> Any:
        if isinstance(obj, list):
            return [self._make_serializable(i) for i in obj]
        if isinstance(obj, dict):
            return {str(k) if not isinstance(k, tuple) else f"{k[0]}_{k[1]}": self._make_serializable(v) for k, v in obj.items()}
        if hasattr(obj, '__dict__'):
            data = obj.__dict__.copy()
            if 'path' in data:
                data['path'] = str(data['path'])
            return data
        if isinstance(obj, Path):
            return str(obj)
        return obj
