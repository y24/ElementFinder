**ElementFinder 要件定義（初版）**

# 1. 目的

GUIアプリの要素特定を効率化するCLI。
「ウィンドウ全体→アンカーで範囲を絞る→浅い階層だけ出す→欲しい属性で刺す」をサクッとやるためのツール。

# 2. 対象環境

* OS: Windows 10/11（x64）
* Python: 3.9+（推奨 3.10+）
* 依存: `pywinauto`, `comtypes`（UIA使用時）
* 権限: 通常ユーザー。対象プロセスが高権限の場合は要管理者昇格

# 3. 入出力概要

* **入力**: ウィンドウタイトル（必須）、オプション各種（backend、depth、anchor、cursor、only-visible など）
* **出力（標準出力）**:

  * 既定: 人間が読みやすいツリー（print_control_identifiers 風に要約）
  * 機械可読: `--json` 指定時に JSON 配列（各要素の属性を列挙）
  * 追加: `--emit-selector` で pywinauto の `child_window(...)` スニペットを併記

# 4. コマンド仕様

```
elementfinder <WINDOW_TITLE>
  [--title-re] 
  [--backend {win32,uia}] 
  [--depth <N|max>]
  [--anchor-control-type <TYPE>]
  [--anchor-title <TEXT>]
  [--anchor-name <TEXT>]
  [--anchor-class-name <CLASS>]
  [--anchor-auto-id <ID>]
  [--anchor-found-index <INT>]               # 既定 0
  [--cursor] [--cursor-delay <SEC>]          # 既定 5
  [--only-visible]                           # 非表示要素を除外
  [--max-items <N>]                           # 出力上限（既定: 無制限）
  [--json] [--fields <CSV>]                  # 出力項目を制御
  [--highlight]                              # 出力対象を一瞬アウトライン描画
  [--timeout <SEC>]                           # ウィンドウ待機（既定 5）
  [--verbose]
  [--version]
```

### 4.1 位置引数

* `WINDOW_TITLE`: ウィンドウタイトルの完全一致。`--title-re` を付けると正規表現扱い。

### 4.2 主なオプション

* `--backend`: 既定 `win32`。`uia` 明示で UIA バックエンド。
* `--depth`: 既定 `3`。`N` または `max`（全取得）。
  取得は「アンカー以下の子孫」に限定（アンカー未指定時はトップウィンドウ）。
* `--anchor-*`: 親コンテナ（アンカー）を一意に特定するための属性群。複数同値がある場合は `--anchor-found-index`（既定 0）で選択。

  * `control_type`（uia 用）、`title`/`name`、`class_name`、`auto_id` をサポート。
* `--cursor`: 実行後に `--cursor-delay` 秒待ち、マウス下の要素をアンカーとして採用。
  `--anchor-*` と併用時は **cursor が優先**（直感優先）。
* `--only-visible`: 可視かつ有効な要素のみ出力。
* `--json`: JSON 出力。
  既定は人間向けの簡易ツリー。`--fields` で出力列を制限（例: `--fields name,auto_id,control_type,rectangle`）。
* `--highlight`: 出力対象（上位 N 件）を順にアウトライン描画して視認性を上げる。
* `--timeout`: 対象ウィンドウの出現を待機。

# 5. 出力仕様

### 5.1 テキスト出力（既定）

* インデントで階層表現。各行は主要属性のサマリ。

```
[2] Button name='保存' auto_id='saveBtn' class='Button' visible=True enabled=True rect=(X1,Y1,X2,Y2)
```

* 行頭の `[index]` は当ツール内の並び番号（descendants 抽出順）。
  `--emit-selector` 有効時は、各行の末尾に pywinauto セレクタ例を併記：

```
selector: child_window(auto_id="saveBtn", control_type="Button")
```

### 5.2 JSON 出力

* 配列形式。各要素は下記キーを持つ（存在しない値は `null`）。

```json
{
  "index": 2,
  "depth": 3,
  "name": "保存",
  "title": "保存",
  "auto_id": "saveBtn",
  "control_type": "Button",
  "class_name": "Button",
  "rectangle": [x1,y1,x2,y2],
  "visible": true,
  "enabled": true,
  "path": "Window>Pane[0]>Group[1]>Button[2]"
}
```

# 6. 動作ロジック（概要）

1. **ウィンドウ特定**: `title` or `title_re` で `app.window(...)`。`--timeout` まで待機。
2. **アンカー決定**:

   * `--cursor` 指定時: `Desktop.from_point` で要素取得→最上位ウィンドウ配下まで昇格してアンカー化。
   * それ以外: `dlg.child_window(**anchor_kwargs, found_index=...)`。未指定なら `dlg` 自身。
3. **要素列挙**: `anchor.descendants(depth=N)`（`max` 時は制限なし）。
   `--only-visible` なら `is_visible() and is_enabled()` でフィルタ。
4. **整形**: 指定 `--fields` に従い整形。`--highlight` 時は短時間 `draw_outline()`。
5. **出力**: テキスト or JSON。`--max-items` で打ち切り。

# 7. エラーハンドリング & 終了コード

* `0`: 正常終了
* `1`: ウィンドウ未検出（timeout）
* `2`: アンカー未検出
* `3`: カーソル取得失敗 / タイムアウト
* `4`: 要素 0 件（フィルタにより空）
* `5`: 無効な引数（depth/fields 等）
* `100`: 予期しない例外

標準エラー出力に人間向けメッセージ（`--json` でもエラーはテキストで良い）。

# 8. 例

```powershell
# 1) 設定ウィンドウの Pane をアンカーにして浅く列挙（UIA）
elementfinder "アプリ - 設定" --backend uia --anchor-control-type Pane --anchor-title 設定 --depth 3 --only-visible

# 2) 5秒後のカーソル下をアンカーに、全取得を JSON で
elementfinder "アプリ" --cursor --cursor-delay 5 --depth max --json --fields name,auto_id,control_type,rectangle

# 3) アンカーが複数ヒット、2番目を採用
elementfinder "アプリ" --anchor-control-type Group --anchor-title 詳細 --anchor-found-index 1 --depth 2

# 4) セレクタ生成を同時表示
elementfinder "アプリ" --backend uia --depth 2 --emit-selector
```

# 9. 非機能要件

* **パフォーマンス**: `depth=3` で 1 万要素規模でも 2〜3 秒以内（目安）。
  UIA で大量時は逐次 yield（ジェネレータ）でメモリ圧を回避。
* **安定性**: 取得失敗時の再試行 1 回（UIA の一時的ブレ対策）。
* **可観測性**: `--verbose` でバックエンド、アンカー決定手順、要素件数、除外件数をログ出力。

# 10. セキュリティ / プライバシ

* 既定でウィンドウテキストを出力。ただし `--redact-text` オプション（将来）で `name/title` を `***` にマスク可能にする。
* 出力は標準出力のみ。ファイル書き込みは将来の `--out <path>` で。

# 11. 拡張（将来）

* アンカーの**多段指定**（親→子→孫）: `--anchor ...` を複数回指定してパスで切り込み。
* **フィルタ**: `--where "control_type=Button AND name~=保存"` の簡易クエリ。
* **アクション**: `--action highlight|invoke|click`（安全のため既定オフ）。
* **録画**: 選択要素のセレクタを CSV/JSON に蓄積。

# 12. 受け入れ基準（サンプル）

* **AC-01**: `--depth` 省略時に 3 階層までが出力されること。
* **AC-02**: `--backend uia` 指定時、`control_type`/`auto_id` が JSON に含まれること。
* **AC-03**: `--anchor-*` で複数一致時、`--anchor-found-index` により選択が切り替わること。
* **AC-04**: `--cursor` 使用時、指定遅延後にカーソル直下要素がアンカーとして採用されること。
* **AC-05**: `--only-visible` で非表示/無効要素が出力されないこと。
* **AC-06**: ウィンドウ未検出時、終了コード `1` を返すこと。

# 13. テスト観点（抜粋）

* Notepad/電卓/独自アプリでの E2E（win32/UIA 両方）
* 多重タブや仮想化リスト（遅延ロード）の可視要素制限
* 日本語タイトル/正規表現マッチ
* 大量要素時の `max` と `depth=3` の時間差
* 画面 DPI/マルチモニタでの `--cursor` 精度
