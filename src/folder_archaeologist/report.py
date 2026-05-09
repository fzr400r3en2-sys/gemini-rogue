import json
import html
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
        if settings.get('hash_duplicates'):
            print("Mode:          SHA-256 Hash Duplication Detection")
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
        is_hash = settings.get('hash_duplicates', False)
        
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
            f"- **Duplication Mode**: {'SHA-256 Hash' if is_hash else 'Size + Name'}",
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
            f"## {'Hash' if is_hash else 'Candidate'} Duplicates (Top {top_n} by Size)",
            "| " + ("Hash & " if is_hash else "Name & ") + "Size | Paths |",
            "| --- | --- |"
        ])
        for (size, key), paths in self.analysis['duplicate_candidates'].items():
            path_list = "<br>".join(str(p) for p in paths)
            lines.append(f"| {key} ({format_size(size)}) | {path_list} |")

        lines.extend([
            "",
            "## Empty Folders",
        ])
        if self.analysis['empty_folders']:
            for path in self.analysis['empty_folders']:
                lines.append(f"- {path}")
        else:
            lines.append("None found.")

        if self.errors:
            lines.extend([
                "",
                "## Warnings / Errors",
            ])
            for err in self.errors:
                lines.append(f"- {err}")

        return "\n".join(lines)

    def to_html(self) -> str:
        summary = self.analysis['summary']
        settings = self.settings
        top_n = settings.get('top_n', 20)
        is_hash = settings.get('hash_duplicates', False)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Folder Archaeology Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .summary-card {{ background-color: #e9ecef; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 20px; }}
        .summary-item {{ flex: 1; min-width: 200px; }}
        .summary-label {{ font-weight: bold; color: #495057; display: block; }}
        .summary-value {{ font-size: 1.2em; color: #212529; }}
        .warning {{ color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; margin-bottom: 5px; }}
        code {{ background-color: #f1f3f5; padding: 2px 4px; border-radius: 4px; font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
        .path-list {{ margin: 0; padding: 0; list-style: none; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>Folder Archaeology Report</h1>
    <p>Generated on: {now}</p>

    <h2>Summary</h2>
    <div class="summary-card">
        <div class="summary-item"><span class="summary-label">Total Files</span><span class="summary-value">{summary['total_files']}</span></div>
        <div class="summary-item"><span class="summary-label">Total Folders</span><span class="summary-value">{summary['total_folders']}</span></div>
        <div class="summary-item"><span class="summary-label">Total Size</span><span class="summary-value">{format_size(summary['total_size'])}</span></div>
    </div>

    <h2>Execution Conditions</h2>
    <table>
        <tr><th>Setting</th><th>Value</th></tr>
        <tr><td>Top-N</td><td>{top_n}</td></tr>
        <tr><td>Max-Depth</td><td>{settings.get('max_depth') if settings.get('max_depth') is not None else 'Unlimited'}</td></tr>
        <tr><td>Min-Size</td><td>{format_size(settings.get('min_size', 0))}</td></tr>
        <tr><td>Duplication Mode</td><td>{'SHA-256 Hash' if is_hash else 'Size + Name'}</td></tr>
        <tr><td>Excludes</td><td>{html.escape(', '.join(self.excludes)) if self.excludes else 'None'}</td></tr>
    </table>

    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 400px;">
            <h3>Extensions by Count (Top {top_n})</h3>
            <table>
                <tr><th>Extension</th><th>Count</th></tr>
                {"".join(f"<tr><td>{html.escape(ext) or '(no extension)'}</td><td>{count}</td></tr>" for ext, count in self.analysis['extensions_count'])}
            </table>
        </div>
        <div style="flex: 1; min-width: 400px;">
            <h3>Extensions by Size (Top {top_n})</h3>
            <table>
                <tr><th>Extension</th><th>Size</th></tr>
                {"".join(f"<tr><td>{html.escape(ext) or '(no extension)'}</td><td>{format_size(size)}</td></tr>" for ext, size in self.analysis['extensions_size'])}
            </table>
        </div>
    </div>

    <h3>Files by Year</h3>
    <table>
        <tr><th>Year</th><th>Count</th></tr>
        {"".join(f"<tr><td>{year}</td><td>{count}</td></tr>" for year, count in self.analysis['years_count'])}
    </table>

    <h3>Top {top_n} Large Files</h3>
    <table>
        <tr><th>File Path</th><th>Size</th><th>Last Modified</th></tr>
        {"".join(f"<tr><td><code>{html.escape(str(f.path))}</code></td><td>{format_size(f.size)}</td><td>{datetime.fromtimestamp(f.mtime).strftime('%Y-%m-%d %H:%M:%S')}</td></tr>" for f in self.analysis['top_large'])}
    </table>

    <h3>Top {top_n} Oldest Files</h3>
    <table>
        <tr><th>File Path</th><th>Size</th><th>Last Modified</th></tr>
        {"".join(f"<tr><td><code>{html.escape(str(f.path))}</code></td><td>{format_size(f.size)}</td><td>{datetime.fromtimestamp(f.mtime).strftime('%Y-%m-%d %H:%M:%S')}</td></tr>" for f in self.analysis['top_old'])}
    </table>

    <h3>{'Hash' if is_hash else 'Candidate'} Duplicates (Top {top_n} by Size)</h3>
    <table>
        <tr><th>{'Hash' if is_hash else 'Name'} & Size</th><th>Paths</th></tr>
        {"".join(f"<tr><td>{html.escape(str(key))}<br>({format_size(size)})</td><td><ul class='path-list'>{''.join(f'<li><code>{html.escape(str(p))}</code></li>' for p in paths)}</ul></td></tr>" for (size, key), paths in self.analysis['duplicate_candidates'].items())}
    </table>

    <h3>Empty Folders</h3>
    {"<ul>" + "".join(f"<li><code>{html.escape(str(p))}</code></li>" for p in self.analysis['empty_folders']) + "</ul>" if self.analysis['empty_folders'] else "<p>None found.</p>"}

    {"<h3>Warnings / Errors</h3>" if self.errors else ""}
    {"".join(f"<div class='warning'>{html.escape(err)}</div>" for err in self.errors)}

</body>
</html>"""
        return html_content

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
