"""
ElementFinder のテスト

ElementFinder クラスの動作をテストします。
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import List

import pytest

from src.elementfinder.core.element_finder import (
    ElementFinder, ElementInfo, create_element_finder
)
from src.elementfinder.utils.exceptions import (
    NoElementsFoundError, PywinautoError
)


class TestElementInfo(unittest.TestCase):
    """ElementInfo データクラスのテスト"""
    
    def test_element_info_creation(self):
        """ElementInfo の作成テスト"""
        element_info = ElementInfo(
            index=1,
            depth=2,
            name="Test Button",
            title="Test Button",
            auto_id="btn_test",
            control_type="Button",
            class_name="Button",
            rectangle=[10, 20, 100, 50],
            visible=True,
            enabled=True,
            path="Button[2]"
        )
        
        self.assertEqual(element_info.index, 1)
        self.assertEqual(element_info.depth, 2)
        self.assertEqual(element_info.name, "Test Button")
        self.assertEqual(element_info.control_type, "Button")
        self.assertTrue(element_info.visible)
    
    def test_element_info_to_dict(self):
        """ElementInfo の辞書変換テスト"""
        element_info = ElementInfo(
            index=0,
            depth=1,
            name="Test",
            control_type="Button"
        )
        
        result = element_info.to_dict()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['index'], 0)
        self.assertEqual(result['depth'], 1)
        self.assertEqual(result['name'], "Test")
        self.assertEqual(result['control_type'], "Button")


class TestElementFinder(unittest.TestCase):
    """ElementFinder クラスのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.element_finder = ElementFinder('win32')
    
    def test_init(self):
        """初期化のテスト"""
        # win32 バックエンド
        finder_win32 = ElementFinder('win32')
        self.assertEqual(finder_win32.backend, 'win32')
        
        # uia バックエンド
        finder_uia = ElementFinder('uia')
        self.assertEqual(finder_uia.backend, 'uia')
    
    def test_find_elements_no_elements(self):
        """要素が見つからない場合のテスト"""
        # モックアンカーの作成
        mock_anchor = Mock()
        mock_anchor.descendants.return_value = []  # 空のリスト
        
        # テスト実行・検証
        with self.assertRaises(NoElementsFoundError):
            self.element_finder.find_elements(mock_anchor)
    
    def test_find_elements_success(self):
        """要素発見成功のテスト"""
        # モック要素の作成
        mock_element = Mock()
        mock_element.window_text.return_value = "Test Element"
        mock_element.class_name.return_value = "TestClass"
        mock_element.rectangle.return_value.left = 10
        mock_element.rectangle.return_value.top = 20
        mock_element.rectangle.return_value.right = 100
        mock_element.rectangle.return_value.bottom = 50
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        
        # モックアンカーの作成
        mock_anchor = Mock()
        mock_anchor.descendants.return_value = [mock_element]
        
        # テスト実行
        result = self.element_finder.find_elements(mock_anchor, depth=2)
        
        # 検証
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ElementInfo)
        self.assertEqual(result[0].name, "Test Element")
    
    def test_find_elements_with_depth_limit(self):
        """深度制限のテスト"""
        mock_element = Mock()
        mock_element.window_text.return_value = "Test"
        mock_element.class_name.return_value = "Test"
        mock_element.rectangle.return_value.left = 0
        mock_element.rectangle.return_value.top = 0
        mock_element.rectangle.return_value.right = 10
        mock_element.rectangle.return_value.bottom = 10
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True
        
        mock_anchor = Mock()
        mock_anchor.descendants.return_value = [mock_element]
        
        # 深度制限付きで実行
        result = self.element_finder.find_elements(mock_anchor, depth=3)
        
        # descendants が適切な引数で呼ばれたかチェック
        mock_anchor.descendants.assert_called_with(depth=3)
        self.assertEqual(len(result), 1)
    
    def test_find_elements_only_visible(self):
        """可視要素のみフィルタのテスト"""
        # 可視要素
        mock_visible = Mock()
        mock_visible.window_text.return_value = "Visible"
        mock_visible.class_name.return_value = "Visible"
        mock_visible.is_visible.return_value = True
        mock_visible.is_enabled.return_value = True
        mock_visible.rectangle.return_value.left = 0
        mock_visible.rectangle.return_value.top = 0
        mock_visible.rectangle.return_value.right = 10
        mock_visible.rectangle.return_value.bottom = 10
        
        # 非可視要素
        mock_hidden = Mock()
        mock_hidden.window_text.return_value = "Hidden"
        mock_hidden.class_name.return_value = "Hidden"
        mock_hidden.is_visible.return_value = False
        mock_hidden.is_enabled.return_value = True
        mock_hidden.rectangle.return_value.left = 0
        mock_hidden.rectangle.return_value.top = 0
        mock_hidden.rectangle.return_value.right = 10
        mock_hidden.rectangle.return_value.bottom = 10
        
        mock_anchor = Mock()
        mock_anchor.descendants.return_value = [mock_visible, mock_hidden]
        
        # only_visible=True で実行
        result = self.element_finder.find_elements(mock_anchor, only_visible=True)
        
        # 可視要素のみが結果に含まれることを確認
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Visible")
    
    def test_find_elements_max_items(self):
        """最大件数制限のテスト"""
        # 複数のモック要素を作成
        mock_elements = []
        for i in range(5):
            mock_element = Mock()
            mock_element.window_text.return_value = f"Element {i}"
            mock_element.class_name.return_value = f"Class{i}"
            mock_element.is_visible.return_value = True
            mock_element.is_enabled.return_value = True
            mock_element.rectangle.return_value.left = i * 10
            mock_element.rectangle.return_value.top = 0
            mock_element.rectangle.return_value.right = (i + 1) * 10
            mock_element.rectangle.return_value.bottom = 10
            mock_elements.append(mock_element)
        
        mock_anchor = Mock()
        mock_anchor.descendants.return_value = mock_elements
        
        # max_items=3 で実行
        result = self.element_finder.find_elements(mock_anchor, max_items=3)
        
        # 最大3件のみ返されることを確認
        self.assertEqual(len(result), 3)
    
    def test_safe_get_property(self):
        """_safe_get_property メソッドのテスト"""
        # プロパティが存在する場合
        mock_element = Mock()
        mock_element.test_property = "test_value"
        
        result = self.element_finder._safe_get_property(
            mock_element, 'test_property', 'default'
        )
        self.assertEqual(result, "test_value")
        
        # プロパティが存在しない場合
        result = self.element_finder._safe_get_property(
            mock_element, 'nonexistent', 'default'
        )
        self.assertEqual(result, 'default')
        
        # メソッド呼び出しの場合
        mock_element.test_method.return_value = "method_result"
        result = self.element_finder._safe_get_property(
            mock_element, 'test_method', 'default', is_method=True
        )
        self.assertEqual(result, "method_result")
    
    def test_should_include_element(self):
        """_should_include_element メソッドのテスト"""
        # 可視・有効な要素
        visible_element = ElementInfo(
            index=0, depth=1, visible=True, enabled=True
        )
        self.assertTrue(
            self.element_finder._should_include_element(visible_element, only_visible=True)
        )
        self.assertTrue(
            self.element_finder._should_include_element(visible_element, only_visible=False)
        )
        
        # 非可視要素
        hidden_element = ElementInfo(
            index=0, depth=1, visible=False, enabled=True
        )
        self.assertFalse(
            self.element_finder._should_include_element(hidden_element, only_visible=True)
        )
        self.assertTrue(
            self.element_finder._should_include_element(hidden_element, only_visible=False)
        )
    
    def test_highlight_elements_empty_list(self):
        """空の要素リストでのハイライトテスト"""
        # 例外が発生しないことを確認
        try:
            self.element_finder.highlight_elements([])
        except Exception as e:
            self.fail(f"highlight_elements([]) raised {e} unexpectedly!")
    
    def test_highlight_elements_with_elements(self):
        """要素リストでのハイライトテスト"""
        elements = [
            ElementInfo(
                index=0, depth=1, name="Test1", 
                rectangle=[0, 0, 10, 10]
            ),
            ElementInfo(
                index=1, depth=1, name="Test2", 
                rectangle=[10, 10, 20, 20]
            )
        ]
        
        # 例外が発生しないことを確認
        try:
            self.element_finder.highlight_elements(elements, duration=0.1)
        except Exception as e:
            self.fail(f"highlight_elements() raised {e} unexpectedly!")


class TestElementFinderFactory(unittest.TestCase):
    """ElementFinder ファクトリ関数のテスト"""
    
    def test_create_element_finder(self):
        """create_element_finder 関数のテスト"""
        # デフォルトバックエンド
        finder_default = create_element_finder()
        self.assertIsInstance(finder_default, ElementFinder)
        self.assertEqual(finder_default.backend, 'win32')
        
        # 明示的なバックエンド指定
        finder_uia = create_element_finder('uia')
        self.assertIsInstance(finder_uia, ElementFinder)
        self.assertEqual(finder_uia.backend, 'uia')


if __name__ == '__main__':
    unittest.main()
