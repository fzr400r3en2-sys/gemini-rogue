# folder-archaeologist

A read-only local folder analysis tool to discover what's buried in your directories.

## 目的
指定したローカルフォルダを解析し、ファイル構成、サイズ、拡張子分布、重複候補などの統計情報をレポートとして出力します。

## 安全性について
- **読み取り専用**: ファイルの削除、移動、名前の変更は一切行いません。
- **内容非表示**: ファイルの本文（中身）は読み取らず、メタデータ（ファイル名、サイズ、更新日時等）のみを使用します。

## インストール方法
```bash
# クローンまたはダウンロード後
pip install .
```

## 実行方法
```bash
# 直接実行
python -m folder_archaeologist "C:\path\to\analyze" --report report.md --json report.json

# インストール後のコマンド
folder-archaeologist "C:\path\to\analyze" --report report.md
```

## 出力項目
- 総ファイル数 / 総フォルダ数 / 総サイズ
- 拡張子別ファイル数 / サイズランキング
- 年別ファイル数
- 大容量ファイル TOP 20
- 長期間更新されていないファイル TOP 20
- 空フォルダ候補
- 同一サイズ・同一ファイル名による重複候補

## 制限事項
- アクセス権限のないファイルは解析できません（警告としてレポートに記載されます）。
- 重複判定は「ファイル名」と「サイズ」のみで行うため、内容が異なる場合でも候補に挙がることがあります。

## 今後の拡張候補
- 特定の拡張子の除外設定
- ハッシュ値（MD5/SHA256）による厳密な重複チェック（オプション）
- インタラクティブなHTMLレポート
