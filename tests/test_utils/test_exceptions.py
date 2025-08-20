"""
例外処理のテスト

utils.exceptions モジュールの動作をテストします。
"""

import unittest
from unittest.mock import Mock, patch

import pytest

from src.elementfinder.utils.exceptions import (
    ElementFinderError, InvalidArgumentError, WindowNotFoundError,
    BackendError, TimeoutError, AnchorNotFoundError, CursorError,
    NoElementsFoundError, PywinautoError, handle_pywinauto_exception
)


class TestElementFinderError(unittest.TestCase):
    """ElementFinderError 基底例外クラスのテスト"""
    
    def test_basic_error(self):
        """基本的なエラーのテスト"""
        error = ElementFinderError("Test error", exit_code=42)
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.exit_code, 42)
        self.assertEqual(str(error), "Test error")
    
    def test_default_exit_code(self):
        """デフォルト終了コードのテスト"""
        error = ElementFinderError("Test error")
        
        self.assertEqual(error.message, "Test error")
        self.assertEqual(error.exit_code, 1)  # デフォルト値
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = ElementFinderError("Test")
        self.assertIsInstance(error, Exception)


class TestInvalidArgumentError(unittest.TestCase):
    """InvalidArgumentError のテスト"""
    
    def test_invalid_argument_error(self):
        """無効引数エラーのテスト"""
        error = InvalidArgumentError("depth", "invalid", "1以上の整数")
        
        self.assertEqual(error.argument_name, "depth")
        self.assertEqual(error.argument_value, "invalid")
        self.assertEqual(error.expected_format, "1以上の整数")
        self.assertEqual(error.exit_code, 2)
        
        # メッセージの確認
        expected_message = "引数 'depth' の値 'invalid' が無効です。期待される形式: 1以上の整数"
        self.assertEqual(error.message, expected_message)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = InvalidArgumentError("test", "value", "format")
        self.assertIsInstance(error, ElementFinderError)


class TestWindowNotFoundError(unittest.TestCase):
    """WindowNotFoundError のテスト"""
    
    def test_window_not_found_error(self):
        """ウィンドウ未発見エラーのテスト"""
        error = WindowNotFoundError("Test Window", is_regex=False, timeout=5)
        
        self.assertEqual(error.window_title, "Test Window")
        self.assertFalse(error.is_regex)
        self.assertEqual(error.timeout, 5)
        self.assertEqual(error.exit_code, 1)
        
        # メッセージの確認
        expected_message = "ウィンドウ 'Test Window' が見つかりません（タイムアウト: 5秒）"
        self.assertEqual(error.message, expected_message)
    
    def test_window_not_found_error_regex(self):
        """正規表現ウィンドウ未発見エラーのテスト"""
        error = WindowNotFoundError("Test.*", is_regex=True, timeout=10)
        
        self.assertTrue(error.is_regex)
        
        # 正規表現の場合のメッセージ
        expected_message = "正規表現 'Test.*' にマッチするウィンドウが見つかりません（タイムアウト: 10秒）"
        self.assertEqual(error.message, expected_message)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = WindowNotFoundError("Test", False, 5)
        self.assertIsInstance(error, ElementFinderError)


class TestBackendError(unittest.TestCase):
    """BackendError のテスト"""
    
    def test_backend_error(self):
        """バックエンドエラーのテスト"""
        error = BackendError("uia", "comtypesが必要です")
        
        self.assertEqual(error.backend_name, "uia")
        self.assertEqual(error.details, "comtypesが必要です")
        self.assertEqual(error.exit_code, 1)
        
        # メッセージの確認
        expected_message = "バックエンド 'uia' でエラー: comtypesが必要です"
        self.assertEqual(error.message, expected_message)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = BackendError("test", "details")
        self.assertIsInstance(error, ElementFinderError)


class TestTimeoutError(unittest.TestCase):
    """TimeoutError のテスト"""
    
    def test_timeout_error(self):
        """タイムアウトエラーのテスト"""
        error = TimeoutError("ウィンドウ検索", 10)
        
        self.assertEqual(error.operation, "ウィンドウ検索")
        self.assertEqual(error.timeout_seconds, 10)
        self.assertEqual(error.exit_code, 1)
        
        # メッセージの確認
        expected_message = "ウィンドウ検索 がタイムアウトしました（10秒）"
        self.assertEqual(error.message, expected_message)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = TimeoutError("operation", 5)
        self.assertIsInstance(error, ElementFinderError)


class TestAnchorNotFoundError(unittest.TestCase):
    """AnchorNotFoundError のテスト"""
    
    def test_anchor_not_found_error(self):
        """アンカー未発見エラーのテスト"""
        conditions = {"control_type": "Button", "title": "OK"}
        error = AnchorNotFoundError(conditions, found_index=1)
        
        self.assertEqual(error.anchor_conditions, conditions)
        self.assertEqual(error.found_index, 1)
        self.assertEqual(error.exit_code, 2)
        
        # メッセージに条件が含まれていることを確認
        self.assertIn("control_type", error.message)
        self.assertIn("Button", error.message)
        self.assertIn("title", error.message)
        self.assertIn("OK", error.message)
        self.assertIn("1", error.message)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = AnchorNotFoundError({}, 0)
        self.assertIsInstance(error, ElementFinderError)


class TestCursorError(unittest.TestCase):
    """CursorError のテスト"""
    
    def test_cursor_error(self):
        """カーソルエラーのテスト"""
        error = CursorError("カーソル位置の取得に失敗")
        
        self.assertEqual(error.message, "カーソル位置の取得に失敗")
        self.assertEqual(error.exit_code, 3)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = CursorError("test")
        self.assertIsInstance(error, ElementFinderError)


class TestNoElementsFoundError(unittest.TestCase):
    """NoElementsFoundError のテスト"""
    
    def test_no_elements_found_error(self):
        """要素未発見エラーのテスト"""
        error = NoElementsFoundError("可視要素のみ")
        
        self.assertEqual(error.filter_description, "可視要素のみ")
        self.assertEqual(error.exit_code, 2)
        
        # メッセージの確認
        expected_message = "指定した条件（可視要素のみ）に一致する要素が見つかりません"
        self.assertEqual(error.message, expected_message)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = NoElementsFoundError("test")
        self.assertIsInstance(error, ElementFinderError)


class TestPywinautoError(unittest.TestCase):
    """PywinautoError のテスト"""
    
    def test_pywinauto_error(self):
        """pywinautoエラーのテスト"""
        original_error = Exception("Original error")
        error = PywinautoError(original_error, "要素検索")
        
        self.assertEqual(error.original_error, original_error)
        self.assertEqual(error.operation, "要素検索")
        self.assertEqual(error.exit_code, 4)
        
        # メッセージの確認
        expected_message = "pywinauto操作エラー（要素検索）: Original error"
        self.assertEqual(error.message, expected_message)
    
    def test_inheritance(self):
        """継承関係のテスト"""
        error = PywinautoError(Exception(), "test")
        self.assertIsInstance(error, ElementFinderError)


class TestHandlePywinautoExceptionDecorator(unittest.TestCase):
    """handle_pywinauto_exception デコレーターのテスト"""
    
    def test_decorator_normal_execution(self):
        """正常実行時のデコレーターテスト"""
        @handle_pywinauto_exception
        def test_function():
            return "success"
        
        result = test_function()
        self.assertEqual(result, "success")
    
    def test_decorator_with_pywinauto_exception(self):
        """pywinauto例外発生時のデコレーターテスト"""
        # pywinautoの例外をシミュレート
        class MockPywinautoException(Exception):
            pass
        
        @handle_pywinauto_exception
        def test_function():
            raise MockPywinautoException("pywinauto error")
        
        # PywinautoErrorに変換されることを確認
        with self.assertRaises(PywinautoError) as context:
            test_function()
        
        self.assertIn("pywinauto error", str(context.exception))
    
    def test_decorator_with_other_exception(self):
        """その他の例外のデコレーターテスト"""
        @handle_pywinauto_exception
        def test_function():
            raise ValueError("other error")
        
        # ValueError がそのまま発生することを確認
        with self.assertRaises(ValueError):
            test_function()
    
    def test_decorator_with_element_finder_error(self):
        """ElementFinderError系例外のデコレーターテスト"""
        @handle_pywinauto_exception
        def test_function():
            raise TimeoutError("timeout", 5)
        
        # ElementFinderError系はそのまま通す
        with self.assertRaises(TimeoutError):
            test_function()


class TestExceptionMessages(unittest.TestCase):
    """例外メッセージのテスト"""
    
    def test_japanese_messages(self):
        """日本語メッセージのテスト"""
        # 日本語のウィンドウタイトルでのエラー
        error = WindowNotFoundError("テストウィンドウ", False, 5)
        self.assertIn("テストウィンドウ", error.message)
        
        # 日本語の操作名でのエラー
        error = TimeoutError("要素検索", 10)
        self.assertIn("要素検索", error.message)
    
    def test_special_characters_in_messages(self):
        """特殊文字を含むメッセージのテスト"""
        # 特殊文字を含むウィンドウタイトル
        error = WindowNotFoundError("App [v1.0]", False, 5)
        self.assertIn("App [v1.0]", error.message)
        
        # 正規表現パターン
        error = WindowNotFoundError("App.*\\d+", True, 5)
        self.assertIn("App.*\\d+", error.message)


class TestExceptionChaining(unittest.TestCase):
    """例外チェーンのテスト"""
    
    def test_exception_chaining(self):
        """例外チェーンのテスト"""
        original = ValueError("Original error")
        chained = PywinautoError(original, "test operation")
        
        self.assertEqual(chained.original_error, original)
        self.assertIn("Original error", str(chained))


if __name__ == '__main__':
    unittest.main()
