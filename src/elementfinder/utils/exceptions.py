"""
ElementFinder カスタム例外クラス

アプリケーション固有のエラー状況を表現し、適切な終了コードとエラーメッセージを提供します。
"""

from typing import Optional


class ElementFinderError(Exception):
    """
    ElementFinderの基底例外クラス
    
    すべてのElementFinder固有の例外はこのクラスを継承します。
    """
    
    def __init__(self, message: str, exit_code: int = 100):
        """
        Args:
            message: エラーメッセージ
            exit_code: プロセス終了コード（デフォルト: 100）
        """
        super().__init__(message)
        self.message = message
        self.exit_code = exit_code
    
    def __str__(self) -> str:
        return self.message


class WindowNotFoundError(ElementFinderError):
    """
    対象ウィンドウが見つからない場合の例外
    
    タイムアウト時間内にウィンドウが検出されなかった場合に発生します。
    終了コード: 1
    """
    
    def __init__(self, window_title: str, timeout: int):
        message = f"ウィンドウが見つかりません: '{window_title}' (タイムアウト: {timeout}秒)"
        super().__init__(message, exit_code=1)
        self.window_title = window_title
        self.timeout = timeout


class AnchorNotFoundError(ElementFinderError):
    """
    アンカー要素が見つからない場合の例外
    
    指定されたアンカー条件に一致する要素が見つからなかった場合に発生します。
    終了コード: 2
    """
    
    def __init__(self, anchor_conditions: dict, found_index: int = 0):
        conditions_str = ", ".join([f"{k}='{v}'" for k, v in anchor_conditions.items()])
        message = f"アンカー要素が見つかりません: {conditions_str} (インデックス: {found_index})"
        super().__init__(message, exit_code=2)
        self.anchor_conditions = anchor_conditions
        self.found_index = found_index


class CursorError(ElementFinderError):
    """
    カーソル位置の要素取得に失敗した場合の例外
    
    --cursorオプション使用時にカーソル下の要素が取得できなかった場合に発生します。
    終了コード: 3
    """
    
    def __init__(self, message: str = "カーソル位置の要素取得に失敗しました"):
        super().__init__(message, exit_code=3)


class NoElementsFoundError(ElementFinderError):
    """
    フィルタ条件により要素が0件になった場合の例外
    
    --only-visibleなどのフィルタにより、出力対象要素が存在しなくなった場合に発生します。
    終了コード: 4
    """
    
    def __init__(self, filter_description: str = "指定されたフィルタ条件"):
        message = f"要素が見つかりません: {filter_description}により0件"
        super().__init__(message, exit_code=4)
        self.filter_description = filter_description


class InvalidArgumentError(ElementFinderError):
    """
    無効な引数が指定された場合の例外
    
    depth、fieldsなどの引数値が無効な場合に発生します。
    終了コード: 5
    """
    
    def __init__(self, argument_name: str, value: str, expected: str):
        message = f"無効な引数値: --{argument_name}={value} (期待値: {expected})"
        super().__init__(message, exit_code=5)
        self.argument_name = argument_name
        self.value = value
        self.expected = expected


class PywinautoError(ElementFinderError):
    """
    pywinauto関連のエラーをラップする例外
    
    pywinautoライブラリの例外を統一的に扱うためのラッパーです。
    """
    
    def __init__(self, original_error: Exception, context: str = ""):
        if context:
            message = f"pywinautoエラー ({context}): {str(original_error)}"
        else:
            message = f"pywinautoエラー: {str(original_error)}"
        super().__init__(message, exit_code=100)
        self.original_error = original_error
        self.context = context


class TimeoutError(ElementFinderError):
    """
    操作タイムアウトの例外
    
    各種操作（ウィンドウ検索、要素取得等）でタイムアウトが発生した場合に使用します。
    """
    
    def __init__(self, operation: str, timeout: int):
        message = f"操作タイムアウト: {operation} ({timeout}秒)"
        super().__init__(message, exit_code=100)
        self.operation = operation
        self.timeout = timeout


class BackendError(ElementFinderError):
    """
    バックエンド関連のエラー
    
    win32またはUIAバックエンドの初期化や操作で問題が発生した場合に使用します。
    """
    
    def __init__(self, backend: str, message: str):
        full_message = f"バックエンドエラー ({backend}): {message}"
        super().__init__(full_message, exit_code=100)
        self.backend = backend


def handle_pywinauto_exception(func):
    """
    pywinautoの例外をElementFinderError系にラップするデコレータ
    
    Usage:
        @handle_pywinauto_exception
        def some_pywinauto_operation():
            # pywinauto operations
            pass
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # pywinauto固有の例外パターンをチェック
            error_str = str(e).lower()
            
            if "window not found" in error_str or "could not find" in error_str:
                raise WindowNotFoundError("不明", 5)  # デフォルト値
            elif "timeout" in error_str:
                raise TimeoutError(func.__name__, 5)  # デフォルト値
            else:
                raise PywinautoError(e, func.__name__)
    
    return wrapper
