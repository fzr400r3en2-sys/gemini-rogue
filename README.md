# folder-archaeologist

A read-only local folder analysis tool to discover what's buried in your directories.
指定したローカルフォルダを解析し、ファイル構成、サイズ、拡張子分布、重複、空フォルダなどの統計情報をレポートとして出力します。

## 目的
肥大化したプロジェクトフォルダやバックアップデータの整理を支援するために、ディスク使用量の内訳や不要と思われるファイル（重複、大容量、長期未更新）を可視化します。

## 安全設計
- **読み取り専用**: ファイルの削除、移動、名前の変更、内容の書き換えは一切行いません。
- **プライバシー配慮**: デフォルトではファイル名とメタデータのみを使用します。ハッシュ計算オプションを有効にした場合でも、ファイル内容を保存したり外部に送信したりすることはありません。
- **低負荷**: チャンク単位での読み込み（ハッシュ計算時）や、除外設定（デフォルトで `.git`, `node_modules`, `.venv` 等を除外）により、システムへの負荷を最小限に抑えます。

## インストール方法
```powershell
# クローンまたはダウンロード後
pip install .
```

## 実行例 (Windows PowerShell)
```powershell
# 解析前に規模を安全に確認（階層別サマリー）
python -m folder_archaeologist "C:\Users\user\Downloads" --depth-summary

# 階層別サマリーの深さを指定（最大5まで）
python -m folder_archaeologist "C:\Users\user\Downloads" --depth-summary --depth-summary-max 4

# 基本的な解析
python -m folder_archaeologist "C:\path\to\analyze" --report report.md

# 全オプション活用例 (HTML, JSONレポート出力, ハッシュ重複検出)
python -m folder_archaeologist "C:\Users\Public" `
    --report report.md `
    --json report.json `
    --html-report report.html `
    --hash-duplicates `
    --top-n 10 `
    --max-depth 3 `
    --min-size 1048576
```

## オプション説明
- `target`: 解析対象のフォルダパス（必須）。
- `--depth-summary`: 指定フォルダを対象に、複数の max-depth 値ごとの概算サマリー（ファイル数・フォルダ数・総サイズ）をまとめて表示します。安全な事前確認用です。
- `--depth-summary-max <N>`: depth 0〜N まで確認します。未指定時は 3、上限は 5 です。
- `--report <PATH>`: Markdown形式のレポートを保存。
- `--json <PATH>`: JSON形式の詳細データを保存。
- `--html-report <PATH>`: インタラクティブで美しいHTMLレポートを保存。
- `--hash-duplicates`: ファイルサイズが同一の場合にSHA-256ハッシュ値を計算して、厳密な重複チェックを行います（デフォルトはサイズと名前で判定）。
- `--top-n <N>`: 各ランキング（大容量ファイル等）の表示件数（デフォルト: 20）。
- `--max-depth <N>`: 探索するディレクトリの最大深さ（0はルートのみ）。
- `--min-size <BYTES>`: ランキング対象にする最小ファイルサイズ。
- `--exclude <DIR>`: 除外するディレクトリ名（複数指定可）。
- `--no-default-excludes`: `.git`, `node_modules` 等のデフォルト除外設定を無効化。

## 安全な使い方（事前確認）
大規模なフォルダ（ネットワークドライブやバックアップディスクなど）をいきなり深い階層まで解析すると、完了まで時間がかかったりシステムに負荷がかかったりする場合があります。

そのような場合は、まず `--depth-summary` を使用して、浅い階層（depth 0〜3程度）でのファイル数や容量の増え方を確認することをお勧めします。

- `--depth-summary` ではハッシュ計算や詳細なランキング（全ファイルソートなど）を行わないため、非常に安全かつ高速に規模感を把握できます。
- 規模を確認した後、適切な `--max-depth` や `--min-size` を設定して詳細解析を実行してください。

## テスト方法
```powershell
# pytestによるテスト実行
python -m pytest

# 型チェック/コンパイルチェック
python -m compileall src\folder_archaeologist
```

## 制限事項
- **アクセス権限**: 読み取り権限がないファイルやフォルダは解析できず、レポートに「警告」として記載されます。
- **ネットワークドライブ**: 解析可能ですが、ハッシュ計算を有効にするとネットワーク負荷が高くなる可能性があります。
- **メモリ使用量**: 非常に膨大なファイル数（数百万〜）を解析する場合、メモリ使用量が増加することがあります。

## 今後の拡張候補
- **GUI版**: デスクトップアプリケーションとしての提供。
- **グラフ表示**: HTMLレポート内での円グラフや時系列グラフの強化。
- **定期実行**: 差分解析（前回との比較）機能。
