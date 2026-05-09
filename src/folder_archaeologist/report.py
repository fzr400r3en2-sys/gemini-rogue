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

        if 'depth_summary' in self.analysis:
            print("Depth Summary")
            for ds in self.analysis['depth_summary']:
                print(f"- depth {ds['depth']}: files={ds['files']}, folders={ds['folders']}, size={format_size(ds['size'])}")
            print("")

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
            "# フォルダ解析レポート",
            f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 概要",
            f"- 総ファイル数: {summary['total_files']}",
            f"- 総フォルダ数: {summary['total_folders']}",
            f"- 総サイズ: {format_size(summary['total_size'])}",
            ""
        ]

        if 'depth_summary' in self.analysis:
            lines.extend([
                "## 階層別サマリー",
                "| 階層 (depth) | ファイル数 | フォルダ数 | 合計サイズ |",
                "| --- | --- | --- | --- |"
            ])
            for ds in self.analysis['depth_summary']:
                lines.append(f"| {ds['depth']} | {ds['files']} | {ds['folders']} | {format_size(ds['size'])} |")
            lines.append("")
            # If depth_summary is present, we might skip other sections if they are empty
        
        lines.extend([
            "## 実行条件",
            f"- **Top-N**: {top_n}",
            f"- **最大解析階層 (Max-Depth)**: {settings.get('max_depth') if settings.get('max_depth') is not None else '無制限'}",
            f"- **最小ファイルサイズ (Min-Size)**: {format_size(settings.get('min_size', 0))}",
            f"- **重複検知モード**: {'SHA-256 ハッシュ' if is_hash else 'サイズ + ファイル名'}",
            ""
        ])

        if self.excludes:
            lines.extend([
                "## 除外設定",
                "以下のフォルダはスキャン対象から除外されました:",
                "",
            ])
            for ex in self.excludes:
                lines.append(f"- `{ex}`")
            lines.append("")

        if 'extensions_count' in self.analysis:
            lines.extend([
                f"## 拡張子別ファイル数ランキング (Top {top_n})",
                "| 拡張子 | カウント |",
                "| --- | --- |"
            ])
            for ext, count in self.analysis['extensions_count']:
                lines.append(f"| {ext or '(拡張子なし)'} | {count} |")
        
        if 'extensions_size' in self.analysis:
            lines.extend([
                "",
                f"## 拡張子別サイズランキング (Top {top_n})",
                "| 拡張子 | サイズ |",
                "| --- | --- |"
            ])
            for ext, size in self.analysis['extensions_size']:
                lines.append(f"| {ext or '(拡張子なし)'} | {format_size(size)} |")

        if 'years_count' in self.analysis:
            lines.extend([
                "",
                "## 年別ファイル数",
                "| 年 | カウント |",
                "| --- | --- |"
            ])
            for year, count in self.analysis['years_count']:
                lines.append(f"| {year} | {count} |")

        if 'top_large' in self.analysis:
            lines.extend([
                "",
                f"## 大容量ファイル (Top {top_n})",
                "| ファイルパス | サイズ | 最終更新日時 |",
                "| --- | --- | --- |"
            ])
            for f in self.analysis['top_large']:
                # Handle both object and dict (if re-loaded from JSON)
                path = f.path if hasattr(f, 'path') else f.get('path')
                size = f.size if hasattr(f, 'size') else f.get('size')
                mtime_val = f.mtime if hasattr(f, 'mtime') else f.get('mtime')
                mtime = datetime.fromtimestamp(mtime_val).strftime('%Y-%m-%d %H:%M:%S')
                lines.append(f"| {path} | {format_size(size)} | {mtime} |")

        if 'top_old' in self.analysis:
            lines.extend([
                "",
                f"## 長期間更新されていないファイル (Top {top_n})",
                "| ファイルパス | サイズ | 最終更新日時 |",
                "| --- | --- | --- |"
            ])
            for f in self.analysis['top_old']:
                path = f.path if hasattr(f, 'path') else f.get('path')
                size = f.size if hasattr(f, 'size') else f.get('size')
                mtime_val = f.mtime if hasattr(f, 'mtime') else f.get('mtime')
                mtime = datetime.fromtimestamp(mtime_val).strftime('%Y-%m-%d %H:%M:%S')
                lines.append(f"| {path} | {format_size(size)} | {mtime} |")

        if 'duplicate_candidates' in self.analysis:
            lines.extend([
                "",
                f"## 重複候補 (Top {top_n} サイズ順)",
                f"| {'ハッシュ' if is_hash else 'ファイル名'} & サイズ | パス |",
                "| --- | --- |"
            ])
            for (size, key), paths in self.analysis['duplicate_candidates'].items():
                path_list = "<br>".join(str(p) for p in paths)
                lines.append(f"| {key} ({format_size(size)}) | {path_list} |")

        if 'empty_folders' in self.analysis:
            lines.extend([
                "",
                "## 空フォルダ候補",
            ])
            if self.analysis['empty_folders']:
                for path in self.analysis['empty_folders']:
                    lines.append(f"- {path}")
            else:
                lines.append("該当なし")

        if self.errors:
            lines.extend([
                "",
                "## 警告 / エラー",
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

        def get_bar_html(value, max_value, color="#4a90e2", label=""):
            percentage = (value / max_value * 100) if max_value > 0 else 0
            return f"""
            <div class="bar-container">
                <div class="bar" style="width: {percentage}%; background-color: {color};"></div>
                <span class="bar-label">{label}</span>
            </div>
            """

        depth_summary_html = ""
        if 'depth_summary' in self.analysis:
            depth_data = self.analysis['depth_summary']
            max_files = max((ds['files'] for ds in depth_data), default=0)
            max_size = max((ds['size'] for ds in depth_data), default=0)
            
            rows = "".join(f"""
                <tr>
                    <td>{ds['depth']}</td>
                    <td>{ds['files']} {get_bar_html(ds['files'], max_files, "#6c757d")}</td>
                    <td>{ds['folders']}</td>
                    <td>{format_size(ds['size'])} {get_bar_html(ds['size'], max_size, "#17a2b8")}</td>
                </tr>
            """ for ds in depth_data)
            depth_summary_html = f"""
            <h2>階層別サマリー</h2>
            <table>
                <tr><th style="width: 80px;">階層</th><th>ファイル数</th><th style="width: 100px;">フォルダ数</th><th>合計サイズ</th></tr>
                {rows}
            </table>
            """

        # Extension Charts
        ext_count_data = self.analysis.get('extensions_count', [])
        max_ext_count = max((count for ext, count in ext_count_data), default=0)
        ext_count_rows = "".join(f"""
            <tr>
                <td>{html.escape(ext) or '(拡張子なし)'}</td>
                <td>{count} {get_bar_html(count, max_ext_count, "#4a90e2")}</td>
            </tr>
        """ for ext, count in ext_count_data)

        ext_size_data = self.analysis.get('extensions_size', [])
        max_ext_size = max((size for ext, size in ext_size_data), default=0)
        ext_size_rows = "".join(f"""
            <tr>
                <td>{html.escape(ext) or '(拡張子なし)'}</td>
                <td>{format_size(size)} {get_bar_html(size, max_ext_size, "#28a745")}</td>
            </tr>
        """ for ext, size in ext_size_data)

        html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>フォルダ解析レポート</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans JP", sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        h1, h2, h3 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; table-layout: fixed; }}
        th, td {{ text-align: left; padding: 12px; border-bottom: 1px solid #ddd; word-break: break-all; }}
        th {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .summary-card {{ background-color: #e9ecef; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; flex-wrap: wrap; gap: 20px; }}
        .summary-item {{ flex: 1; min-width: 200px; }}
        .summary-label {{ font-weight: bold; color: #495057; display: block; }}
        .summary-value {{ font-size: 1.2em; color: #212529; }}
        .warning {{ color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; margin-bottom: 5px; }}
        code {{ background-color: #f1f3f5; padding: 2px 4px; border-radius: 4px; font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }}
        .path-list {{ margin: 0; padding: 0; list-style: none; font-size: 0.9em; }}
        .bar-container {{ position: relative; width: 100%; height: 18px; background-color: #eee; border-radius: 9px; margin-top: 4px; overflow: hidden; }}
        .bar {{ height: 100%; border-radius: 9px; transition: width 0.3s ease; }}
        .bar-label {{ position: absolute; right: 8px; top: 0; font-size: 0.75em; color: #666; line-height: 18px; }}
    </style>
</head>
<body>
    <h1>フォルダ解析レポート</h1>
    <p>生成日時: {now}</p>

    <h2>概要</h2>
    <div class="summary-card">
        <div class="summary-item"><span class="summary-label">総ファイル数</span><span class="summary-value">{summary['total_files']}</span></div>
        <div class="summary-item"><span class="summary-label">総フォルダ数</span><span class="summary-value">{summary['total_folders']}</span></div>
        <div class="summary-item"><span class="summary-label">総サイズ</span><span class="summary-value">{format_size(summary['total_size'])}</span></div>
    </div>

    {depth_summary_html}

    <h2>実行条件</h2>
    <table>
        <tr><th style="width: 200px;">項目</th><th>設定値</th></tr>
        <tr><td>表示件数 (Top-N)</td><td>{top_n}</td></tr>
        <tr><td>最大解析階層 (Max-Depth)</td><td>{settings.get('max_depth') if settings.get('max_depth') is not None else '無制限'}</td></tr>
        <tr><td>最小ファイルサイズ (Min-Size)</td><td>{format_size(settings.get('min_size', 0))}</td></tr>
        <tr><td>重複検知モード</td><td>{'SHA-256 ハッシュ' if is_hash else 'サイズ + ファイル名'}</td></tr>
        <tr><td>除外フォルダ</td><td>{html.escape(', '.join(self.excludes)) if self.excludes else 'なし'}</td></tr>
    </table>

    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 400px;">
            <h3>拡張子別ファイル数ランキング (Top {top_n})</h3>
            <table>
                <tr><th style="width: 150px;">拡張子</th><th>カウント</th></tr>
                {ext_count_rows}
            </table>
        </div>
        <div style="flex: 1; min-width: 400px;">
            <h3>拡張子別サイズランキング (Top {top_n})</h3>
            <table>
                <tr><th style="width: 150px;">拡張子</th><th>サイズ</th></tr>
                {ext_size_rows}
            </table>
        </div>
    </div>

    <h3>年別ファイル数</h3>
    <table>
        <tr><th style="width: 150px;">年</th><th>カウント</th></tr>
        {"".join(f"<tr><td>{year}</td><td>{count}</td></tr>" for year, count in self.analysis.get('years_count', []))}
    </table>

    <h3>大容量ファイル (Top {top_n})</h3>
    <table style="table-layout: auto;">
        <tr><th>ファイルパス</th><th style="width: 120px;">サイズ</th><th style="width: 180px;">最終更新日時</th></tr>
        {"".join(f"<tr><td><code>{html.escape(str(f.path if hasattr(f, 'path') else f.get('path')))}</code></td><td>{format_size(f.size if hasattr(f, 'size') else f.get('size'))}</td><td>{datetime.fromtimestamp(f.mtime if hasattr(f, 'mtime') else f.get('mtime')).strftime('%Y-%m-%d %H:%M:%S')}</td></tr>" for f in self.analysis.get('top_large', []))}
    </table>

    <h3>長期間更新されていないファイル (Top {top_n})</h3>
    <table style="table-layout: auto;">
        <tr><th>ファイルパス</th><th style="width: 120px;">サイズ</th><th style="width: 180px;">最終更新日時</th></tr>
        {"".join(f"<tr><td><code>{html.escape(str(f.path if hasattr(f, 'path') else f.get('path')))}</code></td><td>{format_size(f.size if hasattr(f, 'size') else f.get('size'))}</td><td>{datetime.fromtimestamp(f.mtime if hasattr(f, 'mtime') else f.get('mtime')).strftime('%Y-%m-%d %H:%M:%S')}</td></tr>" for f in self.analysis.get('top_old', []))}
    </table>

    <h3>重複候補 (Top {top_n} サイズ順)</h3>
    <table style="table-layout: auto;">
        <tr><th style="width: 200px;">{'ハッシュ' if is_hash else 'ファイル名'} & サイズ</th><th>パス</th></tr>
        {"".join(f"<tr><td>{html.escape(str(key))}<br>({format_size(size)})</td><td><ul class='path-list'>{''.join(f'<li><code>{html.escape(str(p))}</code></li>' for p in paths)}</ul></td></tr>" for (size, key), paths in self.analysis.get('duplicate_candidates', {}).items())}
    </table>

    <h3>空フォルダ候補</h3>
    {"<ul>" + "".join(f"<li><code>{html.escape(str(p))}</code></li>" for p in self.analysis.get('empty_folders', [])) + "</ul>" if self.analysis.get('empty_folders') else "<p>該当なし</p>"}

    {"<h3>警告 / エラー</h3>" if self.errors else ""}
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
