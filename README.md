# ElementFinder

GUIアプリケーションの要素特定を効率化するCLIツール

## 概要

ElementFinderは、WindowsのGUIアプリケーションの要素を効率的に特定し、pywinautoでの自動化を支援するCLIツールです。対象ウィンドウの要素階層を取得し、pywinautoで使用できるセレクタを生成したり、JSON形式での構造化データとして出力することができます。

## 主な機能

- **ウィンドウ特定**: タイトル名（完全一致・正規表現）でウィンドウを特定
- **要素列挙**: 指定した深度まで要素階層を取得
- **アンカー機能**: 特定の要素を起点とした子要素の取得
- **カーソル機能**: マウスカーソル位置の要素をアンカーとして使用
- **複数の出力形式**: テキスト、JSON、pywinautoセレクタ生成
- **フィルタリング**: 可視要素のみの出力、最大件数制限
- **バックエンド対応**: Win32・UI Automation両対応
- **ハイライト表示**: 対象要素の視覚的な確認

## インストール

### 前提条件

- Python 3.9以上
- Windows 10/11 (x64)

### インストール方法

```powershell
# リポジトリをクローン
git clone https://github.com/your-org/elementfinder.git
cd elementfinder

# 依存関係をインストール
pip install -r requirements.txt

# パッケージをインストール（開発モード）
pip install -e .
```

### 依存関係

- `pywinauto>=0.6.8` - Windows GUI自動化ライブラリ
- `comtypes>=1.1.14` - UI Automationバックエンド用
- `pywin32>=306` - Win32 APIアクセス用

## 使用方法

### 基本的な使用方法

```powershell
# メモ帳の要素を3階層まで取得
findui "無題 - メモ帳"

# 正規表現でウィンドウを検索
findui ".*設定.*" --title-re

# UI Automationバックエンドを使用
findui "アプリ名" --backend uia
```

### アンカー指定

```powershell
# control_typeでアンカーを指定
findui "アプリ" --anchor-control-type Pane

# タイトルでアンカーを指定
findui "アプリ" --anchor-title "設定"

# 複数マッチ時のインデックス指定
findui "アプリ" --anchor-title "詳細" --anchor-found-index 1
```

### カーソル機能

```powershell
# カーソル位置の要素をアンカーにして取得（ウィンドウタイトル不要）
findui --cursor

# カーソル取得までの遅延時間を指定
findui --cursor --cursor-delay 3
```

### 出力形式

```powershell
# JSON形式で出力
findui "アプリ" --json

# 特定のフィールドのみをJSON出力
findui "アプリ" --json --fields "name,control_type,rectangle"

# pywinautoセレクタを併記
findui "アプリ" --emit-selector
```

### フィルタリング・制限

```powershell
# 可視要素のみを出力
findui "アプリ" --only-visible

# 最大出力件数を制限
findui "アプリ" --max-items 50

# 取得階層の深さを指定
findui "アプリ" --depth 5

# 全階層を取得
findui "アプリ" --depth max
```

### その他のオプション

```powershell
# 要素をハイライト表示
findui "アプリ" --highlight

# 詳細ログを出力
findui "アプリ" --verbose

# タイムアウト時間を指定
findui "アプリ" --timeout 10
```

## コマンドライン引数

### 位置引数

- `window_title` - ウィンドウタイトル（完全一致、--title-reで正規表現可、--cursor指定時は不要）

### 基本オプション

- `--title-re` - ウィンドウタイトルを正規表現として扱う
- `--backend {win32,uia}` - 使用するバックエンド（既定: win32）
- `--depth DEPTH` - 取得する階層の深さ（0以上の整数 または "max", 既定: 3）
- `--timeout SECONDS` - ウィンドウ待機タイムアウト秒数（既定: 5）

### アンカー指定

- `--anchor-control-type TYPE` - アンカーのcontrol_type（UIA用）
- `--anchor-title TITLE` - アンカーのタイトル
- `--anchor-name NAME` - アンカーの名前
- `--anchor-class-name CLASS` - アンカーのクラス名
- `--anchor-auto-id ID` - アンカーの自動ID
- `--anchor-found-index INDEX` - 複数マッチ時の選択インデックス（既定: 0）

### カーソル指定

- `--cursor` - マウスカーソル下の要素をアンカーとして使用
- `--cursor-delay SECONDS` - カーソル位置取得までの遅延時間（既定: 5）

### 出力制御

- `--json` - JSON形式で出力
- `--fields FIELDS` - JSON出力時の出力フィールド（カンマ区切り）
- `--emit-selector` - pywinautoセレクタを併記
- `--pywinauto-native` - pywinautoのprint_control_identifiers()を直接実行
- `--max-items COUNT` - 最大出力件数
- `--highlight` - 出力対象要素をハイライト表示

### フィルター

- `--only-visible` - 可視かつ有効な要素のみ出力

### その他

- `--verbose` - 詳細ログを出力
- `--version` - バージョン情報を表示

## 使用例

### 1. メモ帳の要素構造を確認

```powershell
findui "タイトルなし - メモ帳" --depth 2 --only-visible
```

### 2. 設定画面の特定要素を起点に詳細取得

```powershell
findui "設定" --anchor-control-type TabItem --anchor-title "詳細設定" --depth max --json
```

### 3. カーソル位置から要素情報を取得

```powershell
findui "アプリケーション名" --cursor --cursor-delay 3 --highlight --verbose
```

### 4. pywinautoスクリプト用のセレクタ生成

```powershell
findui "電卓" --anchor-title "結果" --emit-selector --max-items 10
```

## 出力形式

### テキスト形式（デフォルト）

```
Window - 'タイトルなし - メモ帳'    (L0, T0, R800, B600)
['タイトルなし - メモ帳', 'タイトルなし - メモ帳Window', 'Window']
child_window(title="タイトルなし - メモ帳", control_type="Window", class_name="Notepad")
   | 
   | Edit - ''    (L8, T31, R784, B539)
   | ['Edit', 'Edit1']
   | child_window(control_type="Edit", class_name="Edit")
```

### JSON形式

```json
[
  {
    "index": 0,
    "depth": 0,
    "name": null,
    "title": "無題 - メモ帳",
    "control_type": "Window",
    "rectangle": [0, 0, 800, 600],
    "visible": true,
    "enabled": true
  }
]
```

## エラーコード

- `0` - 正常終了
- `1` - ウィンドウが見つからない
- `2` - アンカーが見つからない
- `3` - カーソル位置の取得に失敗
- `10` - 引数エラー
- `100` - 予期しないエラー
- `130` - ユーザー中断（Ctrl+C）

## トラブルシューティング

### よくある問題

#### 1. "comtypes not found"エラー

```powershell
pip install comtypes>=1.1.14
```

#### 2. 管理者権限が必要な場合

一部のアプリケーションでは、ElementFinderを管理者として実行する必要があります。

#### 3. UIAバックエンドで要素が見つからない

Win32バックエンドを試してください：

```powershell
findui "アプリ名" --backend win32
```

#### 4. 大量の要素で動作が重い

出力を制限してください：

```powershell
findui "アプリ名" --depth 2 --max-items 100 --only-visible
```

## 開発

このプロジェクトは社内ツールとして開発されており、テスト環境は最小限に抑えられています。

### 開発環境のセットアップ

```powershell
# 依存関係をインストール
pip install -r requirements.txt

# パッケージを開発モードでインストール
pip install -e .
```

