"""
CursorHandler のテスト

CursorHandler クラスの動作をテストします。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time

import pytest

from src.elementfinder.core.cursor_handler import (
    CursorHandler, create_cursor_handler
)
from src.elementfinder.utils.exceptions import CursorError


class TestCursorHandler(unittest.TestCase):
    """CursorHandler クラスのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.cursor_handler = CursorHandler('win32')
    
    def test_init(self):
        """初期化のテスト"""
        # win32 バックエンド
        handler_win32 = CursorHandler('win32')
        self.assertEqual(handler_win32.backend, 'win32')
        
        # uia バックエンド
        handler_uia = CursorHandler('uia')
        self.assertEqual(handler_uia.backend, 'uia')
    
    @patch('src.elementfinder.core.cursor_handler._WIN32GUI_AVAILABLE', True)
    @patch('src.elementfinder.core.cursor_handler.win32gui.GetCursorPos')
    def test_get_cursor_position_success(self, mock_get_cursor_pos):
        """カーソル位置取得成功のテスト"""
        # モックの設定
        mock_get_cursor_pos.return_value = (100, 200)
        
        # テスト実行
        pos = self.cursor_handler._get_cursor_position()
        
        # 検証
        self.assertEqual(pos, (100, 200))
        mock_get_cursor_pos.assert_called_once()
    
    @patch('src.elementfinder.core.cursor_handler._WIN32GUI_AVAILABLE', False)
    def test_get_cursor_position_no_win32gui(self):
        """win32gui利用不可時のテスト"""
        # テスト実行・検証
        with self.assertRaises(CursorError):
            self.cursor_handler._get_cursor_position()
    
    @patch('src.elementfinder.core.cursor_handler.Desktop')
    def test_get_element_at_point_success(self, mock_desktop):
        """座標上の要素取得成功のテスト"""
        # モックの設定
        mock_element = Mock()
        mock_desktop_instance = Mock()
        mock_desktop_instance.from_point.return_value = mock_element
        mock_desktop.return_value = mock_desktop_instance
        
        # テスト実行
        result = self.cursor_handler._get_element_at_point((100, 200))
        
        # 検証
        self.assertEqual(result, mock_element)
        mock_desktop.assert_called_once_with(backend='win32')
        mock_desktop_instance.from_point.assert_called_once_with(100, 200)
    
    @patch('src.elementfinder.core.cursor_handler.Desktop')
    def test_get_element_at_point_no_element(self, mock_desktop):
        """座標上に要素がない場合のテスト"""
        # モックの設定（要素なし）
        mock_desktop_instance = Mock()
        mock_desktop_instance.from_point.return_value = None
        mock_desktop.return_value = mock_desktop_instance
        
        # テスト実行・検証
        with self.assertRaises(CursorError):
            self.cursor_handler._get_element_at_point((100, 200))
    
    @patch('src.elementfinder.core.cursor_handler.time.sleep')
    @patch.object(CursorHandler, '_get_cursor_position')
    @patch.object(CursorHandler, '_get_element_at_point')
    def test_get_cursor_element_with_delay(self, mock_get_element, mock_get_pos, mock_sleep):
        """遅延付きカーソル要素取得のテスト"""
        # モックの設定
        mock_get_pos.return_value = (100, 200)
        mock_element = Mock()
        mock_get_element.return_value = mock_element
        
        # テスト実行
        result = self.cursor_handler.get_cursor_element(delay=2.5)
        
        # 検証
        self.assertEqual(result, mock_element)
        mock_sleep.assert_called_once_with(2.5)
        mock_get_pos.assert_called_once()
        mock_get_element.assert_called_once_with((100, 200))
    
    def test_safe_get_rectangle_success(self):
        """矩形取得成功のテスト"""
        # モック要素の作成
        mock_element = Mock()
        mock_rect = Mock()
        mock_rect.left = 10
        mock_rect.top = 20
        mock_rect.right = 100
        mock_rect.bottom = 80
        mock_element.rectangle.return_value = mock_rect
        
        # テスト実行
        result = self.cursor_handler._safe_get_rectangle(mock_element)
        
        # 検証
        self.assertEqual(result, (10, 20, 100, 80))
    
    def test_safe_get_rectangle_failure(self):
        """矩形取得失敗のテスト"""
        # モック要素の作成（rectangle()が例外を発生）
        mock_element = Mock()
        mock_element.rectangle.side_effect = Exception("Rectangle error")
        
        # テスト実行
        result = self.cursor_handler._safe_get_rectangle(mock_element)
        
        # 検証（Noneが返されることを確認）
        self.assertIsNone(result)
    
    def test_calculate_rect_distance(self):
        """矩形間距離計算のテスト"""
        # 矩形1: 中心点 (5, 5)
        rect1 = (0, 0, 10, 10)
        # 矩形2: 中心点 (15, 15)
        rect2 = (10, 10, 20, 20)
        
        # テスト実行
        distance = self.cursor_handler._calculate_rect_distance(rect1, rect2)
        
        # 検証（距離は約14.14）
        expected_distance = ((10 ** 2) + (10 ** 2)) ** 0.5
        self.assertAlmostEqual(distance, expected_distance, places=2)
    
    def test_is_element_in_window_success(self):
        """要素がウィンドウ配下にある場合のテスト"""
        # モック要素とウィンドウの作成
        mock_window = Mock()
        mock_window.handle = 12345
        
        mock_parent = Mock()
        mock_parent.handle = 12345  # 同じハンドル
        
        mock_element = Mock()
        mock_element.parent.return_value = mock_parent
        
        # テスト実行
        result = self.cursor_handler._is_element_in_window(mock_element, mock_window)
        
        # 検証
        self.assertTrue(result)
    
    def test_is_element_in_window_failure(self):
        """要素がウィンドウ配下にない場合のテスト"""
        # モック要素とウィンドウの作成
        mock_window = Mock()
        mock_window.handle = 12345
        
        mock_parent = Mock()
        mock_parent.handle = 67890  # 異なるハンドル
        
        mock_element = Mock()
        mock_element.parent.return_value = mock_parent
        
        # テスト実行
        result = self.cursor_handler._is_element_in_window(mock_element, mock_window)
        
        # 検証
        self.assertFalse(result)
    
    @patch.object(CursorHandler, '_safe_get_rectangle')
    def test_find_nearest_element_in_window(self, mock_get_rect):
        """ウィンドウ内最近接要素検索のテスト"""
        # カーソル要素の矩形（中心点 5, 5）
        cursor_rect = (0, 0, 10, 10)
        
        # ウィンドウの子要素の矩形
        child1_rect = (5, 5, 15, 15)    # 中心点 10, 10（距離約7.07）
        child2_rect = (20, 20, 30, 30)  # 中心点 25, 25（距離約28.28）
        
        # モックの設定
        mock_get_rect.side_effect = [cursor_rect, child1_rect, child2_rect]
        
        mock_child1 = Mock()
        mock_child2 = Mock()
        
        mock_window = Mock()
        mock_window.descendants.return_value = [mock_child1, mock_child2]
        
        # テスト実行
        result = self.cursor_handler._find_nearest_element_in_window(
            Mock(), mock_window
        )
        
        # 検証（child1が最近接）
        self.assertEqual(result, mock_child1)
    
    def test_promote_to_window_anchor_already_in_window(self):
        """既にウィンドウ配下の要素のアンカー昇格テスト"""
        mock_element = Mock()
        mock_window = Mock()
        
        # _is_element_in_window が True を返すようにモック
        with patch.object(self.cursor_handler, '_is_element_in_window', return_value=True):
            result = self.cursor_handler._promote_to_window_anchor(mock_element, mock_window)
            
            # 元の要素がそのまま返されることを確認
            self.assertEqual(result, mock_element)


class TestCursorHandlerFactory(unittest.TestCase):
    """CursorHandler ファクトリ関数のテスト"""
    
    def test_create_cursor_handler(self):
        """create_cursor_handler 関数のテスト"""
        # デフォルトバックエンド
        handler_default = create_cursor_handler()
        self.assertIsInstance(handler_default, CursorHandler)
        self.assertEqual(handler_default.backend, 'win32')
        
        # 明示的なバックエンド指定
        handler_uia = create_cursor_handler('uia')
        self.assertIsInstance(handler_uia, CursorHandler)
        self.assertEqual(handler_uia.backend, 'uia')


class TestCursorHandlerIntegration(unittest.TestCase):
    """CursorHandler の結合テスト"""
    
    @unittest.skipIf(True, "実際のカーソル操作が必要なため通常はスキップ")
    def test_get_actual_cursor_element(self):
        """実際のカーソル要素取得テスト（統合テスト）"""
        # 注意: このテストは実際の環境でのカーソル操作が必要です
        handler = create_cursor_handler('win32')
        
        try:
            # 短い遅延でテスト
            element = handler.get_cursor_element(delay=0.1)
            self.assertIsNotNone(element)
        except CursorError:
            # カーソル取得に失敗した場合はスキップ
            self.skipTest("カーソル要素の取得に失敗しました")


if __name__ == '__main__':
    unittest.main()
