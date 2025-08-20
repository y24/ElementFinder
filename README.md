# ElementFinder

GUIアプリケーションの要素特定を効率化するCLIツール

## 概要

ElementFinderは、WindowsのGUIアプリケーションから要素を効率的に特定し、pywinautoでの自動化を支援するためのコマンドラインツールです。

「ウィンドウ全体→アンカーで範囲を絞る→浅い階層だけ出す→欲しい属性で刺す」をサクッと実行できます。

## 特徴

- **効率的な要素検索**: 深度制限とアンカー機能で必要な要素だけを抽出
- **複数バックエンド対応**: win32とUIAバックエンドをサポート
- **柔軟な出力形式**: 人間向けテキストと機械向けJSON出力
- **カーソル連携**: マウス位置をアンカーとして使用可能
- **pywinautoセレクタ生成**: 自動化スクリプト作成を支援

## インストール

### 依存関係

- Python 3.9以上（推奨: 3.10以上）
- Windows 10/11（x64）

### セットアップ

```bash
# 本番環境
pip install -r requirements.txt

# 開発環境
pip install -r requirements-dev.txt

# パッケージとしてインストール
pip install -e .
```

## 基本的な使用方法

### 1. 簡単な要素列挙

```bash
# メモ帳の要素を3階層まで取得
elementfinder "メモ帳"

# 設定ウィンドウをUIA Backend で取得
elementfinder "設定" --backend uia
```

### 2. アンカーを使用した範囲絞り込み

```bash
# Paneタイプの要素をアンカーにして検索
elementfinder "アプリ - 設定" --backend uia --anchor-control-type Pane --depth 3

# 複数条件でアンカーを特定
elementfinder "アプリ" --anchor-title "詳細設定" --anchor-class-name "Dialog"
```

### 3. JSON出力とフィールド指定

```bash
# JSON形式で出力
elementfinder "アプリ" --json

# 特定のフィールドのみ出力
elementfinder "アプリ" --json --fields name,auto_id,control_type,rectangle
```

### 4. カーソル位置の活用

```bash
# 5秒後のカーソル下要素をアンカーに
elementfinder "アプリ" --cursor --cursor-delay 5 --depth max
```

### 5. フィルタリングと制限

```bash
# 可視要素のみ、最大50件
elementfinder "アプリ" --only-visible --max-items 50

# 要素をハイライト表示
elementfinder "アプリ" --highlight
```

## コマンドラインオプション

### 位置引数

- `WINDOW_TITLE`: ウィンドウタイトル（完全一致、`--title-re`で正規表現可）

### 主要オプション

- `--backend {win32,uia}`: バックエンド選択（デフォルト: win32）
- `--depth <N|max>`: 検索深度（デフォルト: 3）
- `--timeout <SEC>`: ウィンドウ待機時間（デフォルト: 5）

### アンカー指定

- `--anchor-control-type <TYPE>`: アンカーのcontrol_type（UIA用）
- `--anchor-title <TEXT>`: アンカーのタイトル
- `--anchor-name <TEXT>`: アンカーの名前
- `--anchor-class-name <CLASS>`: アンカーのクラス名
- `--anchor-auto-id <ID>`: アンカーの自動ID
- `--anchor-found-index <INT>`: 複数マッチ時の選択インデックス（デフォルト: 0）

### カーソル指定

- `--cursor`: マウスカーソル下の要素をアンカーとして使用
- `--cursor-delay <SEC>`: カーソル取得までの遅延時間（デフォルト: 5）

### 出力制御

- `--json`: JSON形式で出力
- `--fields <CSV>`: JSON出力時のフィールド指定
- `--emit-selector`: pywinautoセレクタを併記
- `--max-items <N>`: 最大出力件数
- `--highlight`: 出力対象要素をハイライト表示

### フィルター

- `--only-visible`: 可視かつ有効な要素のみ出力

### その他

- `--verbose`: 詳細ログを出力
- `--version`: バージョン情報を表示

## 使用例

### 例1: 設定ダイアログの詳細分析

```bash
elementfinder "アプリ - 設定" \
  --backend uia \
  --anchor-control-type Pane \
  --anchor-title "設定" \
  --depth 3 \
  --only-visible \
  --emit-selector
```

### 例2: JSON形式での自動化用データ取得

```bash
elementfinder "計算機" \
  --json \
  --fields name,auto_id,control_type,rectangle \
  --max-items 20 > calculator_elements.json
```

### 例3: カーソル位置からの詳細検索

```bash
elementfinder "アプリ" \
  --cursor \
  --cursor-delay 3 \
  --depth max \
  --highlight
```

## 出力形式

### テキスト出力（デフォルト）

```
[0] Window name='メモ帳' class='Notepad' visible=True enabled=True rect=(100,100,800,600)
  [1] Edit name='' auto_id='edit1' class='Edit' visible=True enabled=True rect=(110,130,790,580)
  [2] MenuBar name='メニュー バー' class='#32768' visible=True enabled=True rect=(100,100,800,130)
    [3] MenuItem name='ファイル(F)' class='#32768' visible=True enabled=True rect=(100,100,150,130)
```

### JSON出力

```json
[
  {
    "index": 0,
    "depth": 1,
    "name": "メモ帳",
    "title": "メモ帳",
    "auto_id": null,
    "control_type": "Window",
    "class_name": "Notepad",
    "rectangle": [100, 100, 800, 600],
    "visible": true,
    "enabled": true,
    "path": "Window[1]"
  }
]
```

## 終了コード

- `0`: 正常終了
- `1`: ウィンドウ未検出（タイムアウト）
- `2`: アンカー未検出
- `3`: カーソル取得失敗
- `4`: 要素0件（フィルタにより空）
- `5`: 無効な引数
- `100`: 予期しない例外

## 開発情報

### プロジェクト構造

```
ElementFinder/
├── src/elementfinder/
│   ├── cli/          # CLI関連
│   ├── core/         # コア機能
│   ├── output/       # 出力機能
│   └── utils/        # ユーティリティ
├── tests/            # テスト
├── requirements.txt  # 依存関係
└── setup.py         # パッケージ設定
```

### 開発環境セットアップ

```bash
# 開発用依存関係のインストール
pip install -r requirements-dev.txt

# 開発モードでインストール
pip install -e .

# テスト実行
pytest

# コード品質チェック
black src/ tests/
flake8 src/ tests/
mypy src/
```

## ライセンス

MIT License

## 貢献

プルリクエストや課題報告をお待ちしています。

## 将来の機能

- アンカーの多段指定
- 簡易クエリフィルタ機能
- アクション実行機能
- 録画・再生機能
- クロスプラットフォーム対応

---

**注意**: 現在のバージョンは初期実装段階です。カーソル機能などの一部機能は今後のバージョンで実装予定です。
