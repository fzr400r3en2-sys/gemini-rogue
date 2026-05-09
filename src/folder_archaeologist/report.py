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
    def __init__(self, analysis: Dict[str, Any], errors: List[str], excludes: List[str] = None, settings: Dict[str, Any] = None):
        self.analysis = analysis
        self.errors = errors
        self.excludes = excludes or []
        self.settings = settings or {}

    def to_stdout(self):
        summary = self.analysis['summary']
        print("\n=== Folder Archaeology Summary ===")
        print(f"Total Files:   {summary['total_files']}")
        print(f"Total Folders: {summary['total_folders']}")
        print(f"Total Size:    {format_size(summary['total_size'])}")
        if self.excludes:
            print(f"Excluded:      {', '.join(self.excludes)}")
        
        settings = self.settings
        print(f"Top-N:         {settings.get('top_n')}")
        print(f"Max-Depth:     {settings.get('max_depth') if settings.get('max_depth') is not None else 'Unlimited'}")
        print(f"Min-Size:      {format_size(settings.get('min_size', 0))}")
        print("==================================\n")

    def to_json(self) -> str:
        # Convert Path and FileInfo objects to serializable format
        serializable = self._make_serializable(self.analysis)
        serializable['errors'] = self.errors
        serializable['excludes'] = self.excludes
        serializable['settings'] = self.settings
        return json.dumps(serializable, indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        summary = self.analysis['summary']
        settings = self.settings
        top_n = settings.get('top_n', 20)
        
        lines = [
            "# Folder Archaeology Report",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            f"- Total Files: {summary['total_files']}",
            f"- Total Folders: {summary['total_folders']}",
            f"- Total Size: {format_size(summary['total_size'])}",
            ""
        ]
        
        lines.extend([
            "## Settings",
            f"- **Top-N**: {top_n}",
            f"- **Max-Depth**: {settings.get('max_depth') if settings.get('max_depth') is not None else 'Unlimited'}",
            f"- **Min-Size**: {format_size(settings.get('min_size', 0))}",
            ""
        ])

        if self.excludes:
            lines.extend([
                "## Exclusion Settings",
                "The following folders were excluded from the scan:",
                "",
            ])
            for ex in self.excludes:
                lines.append(f"- `{ex}`")
            lines.append("")

        lines.extend([
            f"## Extensions by Count (Top {top_n})",
            "| Extension | Count |",
            "| --- | --- |"
        ])
        for ext, count in self.analysis['extensions_count']:
            lines.append(f"| {ext or '(no extension)'} | {count} |")
        
        lines.extend([
            "",
            f"## Extensions by Size (Top {top_n})",
            "| Extension | Size |",
            "| --- | --- |"
        ])
        for ext, size in self.analysis['extensions_size']:
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
            f"## Top {top_n} Large Files",
            "| File Path | Size | Last Modified |",
            "| --- | --- | --- |"
        ])
        for f in self.analysis['top_large']:
            mtime = datetime.fromtimestamp(f.mtime).strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"| {f.path} | {format_size(f.size)} | {mtime} |")

        lines.extend([
            "",
            f"## Top {top_n} Oldest Files",
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
            f"## Duplicate Candidates (Top {top_n} by Size)",
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
