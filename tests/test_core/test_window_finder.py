"""
WindowFinder のテスト

WindowFinder クラスの動作をテストします。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

import pytest

from src.elementfinder.core.window_finder import WindowFinder, create_window_finder
from src.elementfinder.utils.exceptions import (
    WindowNotFoundError, BackendError, TimeoutError
)


class TestWindowFinder(unittest.TestCase):
    """WindowFinder クラスのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.window_finder = WindowFinder('win32')
    
    def test_init_valid_backend(self):
        """有効なバックエンドでの初期化テスト"""
        # win32 バックエンド
        finder_win32 = WindowFinder('win32')
        self.assertEqual(finder_win32.backend, 'win32')
        
        # uia バックエンド（comtypesが利用可能な場合）
        try:
            finder_uia = WindowFinder('uia')
            self.assertEqual(finder_uia.backend, 'uia')
        except BackendError:
            # comtypesが利用できない環境ではスキップ
            pass
    
    def test_init_invalid_backend(self):
        """無効なバックエンドでの初期化テスト"""
        with self.assertRaises(BackendError):
            WindowFinder('invalid_backend')
    
    @patch('src.elementfinder.core.window_finder.pywinauto.findwindows.find_windows')
    def test_find_window_success(self, mock_find_windows):
        """ウィンドウ発見成功のテスト"""
        # モックの設定
        mock_find_windows.return_value = [12345]  # ハンドルのリスト
        
        with patch('src.elementfinder.core.window_finder.pywinauto.Application') as mock_app:
            mock_window = Mock()
            mock_app.return_value.window.return_value = mock_window
            mock_window.exists.return_value = True
            
            # テスト実行
            result = self.window_finder.find_window("Test Window")
            
            # 検証
            self.assertEqual(result, mock_window)
            mock_find_windows.assert_called_once()
    
    @patch('src.elementfinder.core.window_finder.pywinauto.findwindows.find_windows')
    def test_find_window_not_found(self, mock_find_windows):
        """ウィンドウが見つからない場合のテスト"""
        # モックの設定（ウィンドウが見つからない）
        mock_find_windows.return_value = []
        
        # テスト実行・検証
        with self.assertRaises(WindowNotFoundError):
            self.window_finder.find_window("Nonexistent Window")
    
    @patch('src.elementfinder.core.window_finder.pywinauto.findwindows.find_windows')
    def test_find_window_timeout(self, mock_find_windows):
        """タイムアウトのテスト"""
        # モックの設定（常に空のリストを返す）
        mock_find_windows.return_value = []
        
        # テスト実行・検証（短いタイムアウトで）
        start_time = time.time()
        with self.assertRaises(TimeoutError):
            self.window_finder.find_window("Test Window", timeout=1)
        
        # タイムアウト時間が守られているかチェック（1.5秒以内）
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 1.5)
    
    def test_find_window_regex_mode(self):
        """正規表現モードのテスト"""
        with patch('src.elementfinder.core.window_finder.pywinauto.findwindows.find_windows') as mock_find:
            mock_find.return_value = [12345]
            
            with patch('src.elementfinder.core.window_finder.pywinauto.Application') as mock_app:
                mock_window = Mock()
                mock_app.return_value.window.return_value = mock_window
                mock_window.exists.return_value = True
                
                # 正規表現でウィンドウを検索
                result = self.window_finder.find_window("Test.*", is_regex=True)
                
                # 検証
                self.assertEqual(result, mock_window)
    
    def test_close(self):
        """クリーンアップのテスト"""
        # closeメソッドが例外を発生させないことを確認
        try:
            self.window_finder.close()
        except Exception as e:
            self.fail(f"close() raised {e} unexpectedly!")


class TestWindowFinderFactory(unittest.TestCase):
    """WindowFinder ファクトリ関数のテスト"""
    
    def test_create_window_finder(self):
        """create_window_finder 関数のテスト"""
        # デフォルトバックエンド
        finder_default = create_window_finder()
        self.assertIsInstance(finder_default, WindowFinder)
        self.assertEqual(finder_default.backend, 'win32')
        
        # 明示的なバックエンド指定
        finder_win32 = create_window_finder('win32')
        self.assertIsInstance(finder_win32, WindowFinder)
        self.assertEqual(finder_win32.backend, 'win32')


class TestWindowFinderIntegration(unittest.TestCase):
    """WindowFinder の結合テスト"""
    
    @unittest.skipIf(True, "実際のウィンドウが必要なため通常はスキップ")
    def test_find_notepad_window(self):
        """メモ帳ウィンドウの検索テスト（統合テスト）"""
        # 注意: このテストを実行するには、実際にメモ帳を開いておく必要があります
        finder = create_window_finder('win32')
        
        try:
            window = finder.find_window("メモ帳", timeout=2)
            self.assertIsNotNone(window)
        except (WindowNotFoundError, TimeoutError):
            # メモ帳が開いていない場合はスキップ
            self.skipTest("メモ帳ウィンドウが見つかりません")
        finally:
            finder.close()


if __name__ == '__main__':
    unittest.main()
