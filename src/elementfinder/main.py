"""
ElementFinder メインエントリーポイント

CLIアプリケーションのメイン実行ロジックを提供します。
"""

import sys
import traceback
from typing import Dict, Any, Optional

from .cli.parser import parse_command_line
from .core.window_finder import create_window_finder
from .core.element_finder import create_element_finder
from .core.cursor_handler import create_cursor_handler
from .output.formatters import create_formatter
from .utils.exceptions import ElementFinderError, CursorError
from .utils.logging import setup_logging, get_logger


class ElementFinderApp:
    """
    ElementFinderアプリケーションのメインクラス
    """
    
    def __init__(self):
        self.logger = None
        self.args = None
    
    def run(self, args: Optional[list] = None) -> int:
        """
        アプリケーションを実行します
        
        Args:
            args: コマンドライン引数（テスト用）
        
        Returns:
            int: 終了コード
        """
        try:
            # 引数解析
            self.args = parse_command_line(args)
            
            # ロギング設定
            self.logger = setup_logging(
                verbose=self.args['verbose'],
                use_colors=True
            )
            
            self.logger.info("ElementFinder 開始")
            self.logger.debug(f"引数: {self.args}")
            
            # メイン処理の実行
            return self._execute_main_logic()
            
        except ElementFinderError as e:
            # 予期された例外（適切な終了コード付き）
            if self.logger:
                self.logger.error(e.message)
            else:
                print(f"エラー: {e.message}", file=sys.stderr)
            return e.exit_code
            
        except KeyboardInterrupt:
            if self.logger:
                self.logger.info("ユーザーによる中断")
            else:
                print("中断されました", file=sys.stderr)
            return 130  # SIGINT
            
        except SystemExit as e:
            # --help や --version による正常終了
            return e.code if e.code is not None else 0
            
        except Exception as e:
            # 予期しない例外
            error_msg = f"予期しないエラーが発生しました: {e}"
            
            if self.logger:
                self.logger.error(error_msg)
                self.logger.debug(f"トレースバック:\n{traceback.format_exc()}")
            else:
                print(f"エラー: {error_msg}", file=sys.stderr)
                if '--verbose' in (args or sys.argv):
                    traceback.print_exc()
            
            return 100  # 予期しない例外の終了コード
    
    def _execute_main_logic(self) -> int:
        """
        メイン処理ロジックを実行します
        
        Returns:
            int: 終了コード
        """
        # 1. ウィンドウの特定
        self.logger.info("ステップ1: ウィンドウ特定")
        window_finder = create_window_finder(self.args['backend'])
        
        window = window_finder.find_window(
            self.args['window_title'],
            self.args['title_re'],
            self.args['timeout']
        )
        
        # 2. アンカーの決定
        self.logger.info("ステップ2: アンカー決定")
        anchor = self._resolve_anchor(window)
        
        # 3. 要素の列挙
        self.logger.info("ステップ3: 要素列挙")
        element_finder = create_element_finder(self.args['backend'])
        
        elements = element_finder.find_elements(
            anchor,
            depth=self.args['depth'],
            only_visible=self.args['only_visible'],
            max_items=self.args['max_items']
        )
        
        # 4. ハイライト表示（指定された場合）
        if self.args['highlight']:
            self.logger.info("ステップ4: ハイライト表示")
            element_finder.highlight_elements(elements)
        
        # 5. 出力
        self.logger.info("ステップ5: 出力生成")
        self._output_results(elements)
        
        # 6. クリーンアップ
        window_finder.close()
        
        self.logger.info(f"ElementFinder 完了: {len(elements)}件出力")
        return 0
    
    def _resolve_anchor(self, window) -> Any:
        """
        アンカー要素を決定します
        
        Args:
            window: 対象ウィンドウ
        
        Returns:
            アンカー要素
        """
        # カーソル指定の場合
        if self.args['cursor']:
            return self._resolve_cursor_anchor(window)
        
        # アンカー条件指定の場合
        if self.args['anchor_conditions']:
            return self._resolve_condition_anchor(window)
        
        # 指定なしの場合はウィンドウ自身
        self.logger.debug("アンカー未指定: ウィンドウ全体を対象")
        return window
    
    def _resolve_cursor_anchor(self, target_window: Optional[Any] = None) -> Any:
        """
        カーソル位置のアンカーを解決します
        
        Args:
            target_window: アンカー昇格用の対象ウィンドウ
        
        Returns:
            カーソル下の要素
        
        Raises:
            CursorError: カーソル位置の取得に失敗した場合
        """
        try:
            cursor_handler = create_cursor_handler(self.args['backend'])
            
            # カーソル下の要素を取得（アンカー昇格は行わない）
            element = cursor_handler.get_cursor_element(
                delay=self.args['cursor_delay'],
                target_window=None  # アンカー昇格を無効化
            )
            
            self.logger.info(f"カーソル位置の要素をアンカーとして使用: {type(element).__name__}")
            
            return element
            
        except CursorError as e:
            self.logger.error(f"カーソルアンカー解決失敗: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"カーソルアンカー解決で予期しないエラー: {e}")
            raise CursorError(f"カーソル位置の解決に失敗しました: {e}")
    
    def _resolve_condition_anchor(self, window) -> Any:
        """
        条件指定のアンカーを解決します
        
        Args:
            window: 対象ウィンドウ
        
        Returns:
            アンカー要素
        """
        conditions = self.args['anchor_conditions']
        found_index = self.args['anchor_found_index']
        
        self.logger.debug(f"アンカー条件: {conditions}, インデックス: {found_index}")
        
        try:
            # pywinautoのchild_windowを使用
            # 条件を適切にマッピング
            kwargs = {}
            
            for key, value in conditions.items():
                if key == 'control-type':
                    kwargs['control_type'] = value
                elif key == 'title':
                    kwargs['title'] = value
                elif key == 'name':
                    kwargs['title'] = value  # nameもtitleとして扱う
                elif key == 'class-name':
                    kwargs['class_name'] = value
                elif key == 'auto-id':
                    kwargs['auto_id'] = value
            
            # found_indexを指定
            kwargs['found_index'] = found_index
            
            anchor = window.child_window(**kwargs)
            
            # 存在確認
            if not anchor.exists():
                from .utils.exceptions import AnchorNotFoundError
                raise AnchorNotFoundError(conditions, found_index)
            
            self.logger.debug(f"アンカー解決成功: {kwargs}")
            return anchor
            
        except Exception as e:
            self.logger.error(f"アンカー解決失敗: {e}")
            raise
    
    def _output_results(self, elements) -> None:
        """
        結果を出力します
        
        Args:
            elements: 要素リスト
        """
        try:
            if self.args['json']:
                # JSON出力
                formatter = create_formatter('json', fields=self.args['fields'])
                output = formatter.format_elements(elements)
            elif self.args['pywinauto_style']:
                # pywinauto風出力
                formatter = create_formatter(
                    'pywinauto',
                    emit_selector=self.args['emit_selector'],
                    show_alternative_ids=True
                )
                output = formatter.format_elements(elements)
            elif self.args['pywinauto_native']:
                # pywinauto native出力
                formatter = create_formatter('pywinauto-native', depth=self.args['depth'])
                # pywinauto nativeの場合、元のwindow要素を渡す必要がある
                output = self._format_pywinauto_native(formatter, elements)
            else:
                # テキスト出力
                formatter = create_formatter('text', emit_selector=self.args['emit_selector'])
                output = formatter.format_elements(elements)
            
            print(output)
            
        except Exception as e:
            self.logger.error(f"出力生成失敗: {e}")
            raise
    
    def _format_pywinauto_native(self, formatter, elements) -> str:
        """
        pywinauto nativeフォーマッタで出力を生成します
        
        Args:
            formatter: PywinautoNativeFormatterインスタンス
            elements: 要素リスト
        
        Returns:
            str: フォーマット済み出力
        """
        try:
            # アンカー要素を取得（ウィンドウまたはアンカー）
            anchor = self._resolve_anchor_for_native()
            
            # pywinauto nativeフォーマッタで出力
            return formatter.format_elements(elements, window_element=anchor)
            
        except Exception as e:
            self.logger.error(f"pywinauto native出力失敗: {e}")
            return f"エラー: pywinauto native出力の生成に失敗しました: {e}"
    
    def _resolve_anchor_for_native(self):
        """
        pywinauto native用のアンカー要素を解決します
        
        Returns:
            pywinauto要素
        """
        # ウィンドウの特定（メインロジックと同じ）
        window_finder = create_window_finder(self.args['backend'])
        
        try:
            window = window_finder.find_window(
                self.args['window_title'],
                self.args['title_re'],
                self.args['timeout']
            )
            
            # アンカーの決定（メインロジックと同じ）
            anchor = self._resolve_anchor(window)
            
            return anchor
            
        finally:
            window_finder.close()


def main() -> int:
    """
    メイン関数（CLIエントリーポイント）
    
    Returns:
        int: 終了コード
    """
    app = ElementFinderApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
