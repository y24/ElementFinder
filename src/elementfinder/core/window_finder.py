"""
ElementFinder ウィンドウ特定機能

pywinautoを使用してウィンドウを特定し、適切なバックエンドでアクセス可能にします。
"""

import re
import time
from typing import Optional, Any

import pywinauto
from pywinauto.application import WindowSpecification

from ..utils.exceptions import (
    WindowNotFoundError, BackendError, PywinautoError, TimeoutError,
    handle_pywinauto_exception
)
from ..utils.logging import get_logger, log_function_call, log_performance


class WindowFinder:
    """
    ウィンドウの特定とアクセスを担当するクラス
    """
    
    def __init__(self, backend: str = 'uia'):
        """
        Args:
            backend: 使用するバックエンド ('win32' または 'uia')
        """
        self.backend = backend
        self.logger = get_logger()
        
        # バックエンドの初期化チェック
        self._validate_backend()
    
    def _validate_backend(self) -> None:
        """
        指定されたバックエンドが使用可能かチェックします
        
        Raises:
            BackendError: バックエンドが使用できない場合
        """
        try:
            if self.backend == 'uia':
                # UIAバックエンドの場合、comtypesが必要
                import comtypes
                self.logger.debug(f"UIAバックエンド使用可能: comtypes {comtypes.__version__}")
            
            # pywinautoでのバックエンド設定テスト（Desktopを使用）
            from pywinauto import Desktop
            test_desktop = Desktop(backend=self.backend)
            self.logger.debug(f"バックエンド '{self.backend}' の初期化に成功")
            
        except ImportError as e:
            if self.backend == 'uia':
                raise BackendError(
                    self.backend,
                    "UIAバックエンドにはcomtypesパッケージが必要です"
                ) from e
            else:
                raise BackendError(self.backend, f"バックエンドの初期化に失敗: {e}") from e
        except Exception as e:
            raise BackendError(self.backend, f"バックエンドの初期化に失敗: {e}") from e
    
    @log_function_call
    @handle_pywinauto_exception
    def find_window(self, 
                   window_title: str, 
                   is_regex: bool = False,
                   timeout: int = 5) -> WindowSpecification:
        """
        指定されたタイトルのウィンドウを検索します
        
        Args:
            window_title: ウィンドウタイトル
            is_regex: タイトルを正規表現として扱うかどうか
            timeout: タイムアウト時間（秒）
        
        Returns:
            WindowSpecification: 見つかったウィンドウ
        
        Raises:
            WindowNotFoundError: ウィンドウが見つからない場合
            BackendError: バックエンド操作エラー
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"ウィンドウ検索開始: '{window_title}' "
                           f"(正規表現: {is_regex}, タイムアウト: {timeout}秒)")
            
            # タイムアウト付きでウィンドウを検索
            window = self._search_window_with_timeout(
                window_title, is_regex, timeout
            )
            
            duration = time.time() - start_time
            log_performance("ウィンドウ検索", duration)
            
            self.logger.info(f"ウィンドウ検索成功: {self._get_window_info(window)}")
            
            return window
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"ウィンドウ検索失敗 ({duration:.2f}秒): {e}")
            
            if isinstance(e, (WindowNotFoundError, BackendError)):
                raise
            else:
                # その他の例外をWindowNotFoundErrorにラップ
                raise WindowNotFoundError(window_title, timeout) from e
    
    def _search_window_with_timeout(self,
                                   window_title: str,
                                   is_regex: bool,
                                   timeout: int) -> WindowSpecification:
        """
        タイムアウト付きでウィンドウを検索します
        
        Args:
            window_title: ウィンドウタイトル
            is_regex: 正規表現フラグ
            timeout: タイムアウト時間
        
        Returns:
            WindowSpecification: 見つかったウィンドウ
        
        Raises:
            WindowNotFoundError: タイムアウトまたはウィンドウ未発見
        """
        end_time = time.time() + timeout
        last_exception = None
        retry_count = 0
        
        while time.time() < end_time:
            try:
                # ウィンドウ検索の実行
                if is_regex:
                    window = self._find_window_by_regex(window_title)
                else:
                    window = self._find_window_by_title(window_title)
                
                # ウィンドウの存在確認
                if self._verify_window_exists(window):
                    return window
                
            except Exception as e:
                last_exception = e
                retry_count += 1
                
                # 短時間待機してリトライ
                time.sleep(0.5)
                
                self.logger.debug(f"ウィンドウ検索リトライ {retry_count}: {e}")
        
        # タイムアウト
        self.logger.error(f"ウィンドウ検索タイムアウト: {timeout}秒経過")
        if last_exception:
            self.logger.debug(f"最後の例外: {last_exception}")
        
        raise WindowNotFoundError(window_title, timeout)
    
    def _find_window_by_title(self, title: str) -> WindowSpecification:
        """
        完全一致でウィンドウを検索します
        
        Args:
            title: ウィンドウタイトル
        
        Returns:
            WindowSpecification: ウィンドウ仕様
        """
        # pywinautoのDesktopを使用してウィンドウを検索
        from pywinauto import Desktop
        desktop = Desktop(backend=self.backend)
        
        # ウィンドウを検索
        return desktop.window(title=title)
    
    def _find_window_by_regex(self, title_pattern: str) -> WindowSpecification:
        """
        正規表現でウィンドウを検索します
        
        Args:
            title_pattern: タイトルの正規表現パターン
        
        Returns:
            WindowSpecification: ウィンドウ仕様
        
        Raises:
            WindowNotFoundError: マッチするウィンドウが見つからない場合
        """
        try:
            # 正規表現パターンをコンパイル
            pattern = re.compile(title_pattern, re.IGNORECASE)
            
            # pywinautoのDesktopを使用してウィンドウを検索
            from pywinauto import Desktop
            desktop = Desktop(backend=self.backend)
            
            # 正規表現でウィンドウを検索
            return desktop.window(title_re=title_pattern)
            
        except re.error as e:
            raise WindowNotFoundError(
                title_pattern, 0
            ) from e
    
    def _verify_window_exists(self, window: WindowSpecification) -> bool:
        """
        ウィンドウが実際に存在するかを確認します
        
        Args:
            window: ウィンドウ仕様
        
        Returns:
            bool: ウィンドウが存在する場合True
        """
        try:
            # exists()メソッドで存在確認
            if window.exists(timeout=1):
                # 追加確認: ウィンドウが応答可能か
                _ = window.window_text()
                return True
            return False
            
        except Exception as e:
            self.logger.debug(f"ウィンドウ存在確認失敗: {e}")
            return False
    
    def _get_window_info(self, window: WindowSpecification) -> str:
        """
        ウィンドウの情報を取得します（ログ用）
        
        Args:
            window: ウィンドウ仕様
        
        Returns:
            str: ウィンドウ情報の文字列
        """
        try:
            info_parts = []
            
            # タイトル
            title = window.window_text()
            if title:
                info_parts.append(f"title='{title}'")
            
            # クラス名
            try:
                class_name = window.class_name()
                if class_name:
                    info_parts.append(f"class='{class_name}'")
            except:
                pass
            
            # プロセスID
            try:
                process_id = window.process_id()
                if process_id:
                    info_parts.append(f"pid={process_id}")
            except:
                pass
            
            # 矩形
            try:
                rect = window.rectangle()
                info_parts.append(f"rect={rect}")
            except:
                pass
            
            return ", ".join(info_parts) if info_parts else "不明"
            
        except Exception as e:
            return f"情報取得失敗: {e}"
    
    @log_function_call
    def list_all_windows(self) -> list:
        """
        現在のデスクトップの全ウィンドウを列挙します（デバッグ用）
        
        Returns:
            list: ウィンドウ情報のリスト
        """
        try:
            windows = []
            
            # pywinautoのDesktopを使用してウィンドウ列挙
            from pywinauto import Desktop
            desktop = Desktop(backend=self.backend)
            
            for window in desktop.windows():
                try:
                    window_info = {
                        'title': window.window_text(),
                        'class_name': window.class_name(),
                        'process_id': window.process_id(),
                        'visible': window.is_visible(),
                        'enabled': window.is_enabled(),
                    }
                    windows.append(window_info)
                except:
                    # 個別ウィンドウのエラーは無視
                    continue
            
            self.logger.debug(f"ウィンドウ一覧取得完了: {len(windows)}件")
            return windows
            
        except Exception as e:
            self.logger.warning(f"ウィンドウ一覧取得失敗: {e}")
            return []
    
    def get_backend(self) -> str:
        """
        使用中のバックエンド名を取得します
        
        Returns:
            str: バックエンド名
        """
        return self.backend
    
    def close(self) -> None:
        """
        リソースをクリーンアップします
        """
        self.logger.debug("WindowFinderをクローズしました")


def create_window_finder(backend: str = 'uia') -> WindowFinder:
    """
    WindowFinderインスタンスを作成します（便利関数）
    
    Args:
        backend: 使用するバックエンド
    
    Returns:
        WindowFinderインスタンス
    
    Raises:
        BackendError: バックエンドが使用できない場合
    """
    return WindowFinder(backend)
