"""
出力フォーマッターのテスト

output.formatters モジュールの動作をテストします。
"""

import unittest
import json
from unittest.mock import Mock, patch

import pytest

from src.elementfinder.core.element_finder import ElementInfo
from src.elementfinder.output.formatters import create_formatter


class TestFormatterFactory(unittest.TestCase):
    """フォーマッターファクトリのテスト"""
    
    def test_create_text_formatter(self):
        """テキストフォーマッター作成のテスト"""
        formatter = create_formatter('text')
        self.assertIsNotNone(formatter)
        
        # emit_selectorオプション付き
        formatter = create_formatter('text', emit_selector=True)
        self.assertIsNotNone(formatter)
    
    def test_create_json_formatter(self):
        """JSONフォーマッター作成のテスト"""
        formatter = create_formatter('json')
        self.assertIsNotNone(formatter)
        
        # fieldsオプション付き
        formatter = create_formatter('json', fields=['name', 'control_type'])
        self.assertIsNotNone(formatter)
    
    def test_invalid_format_type(self):
        """無効なフォーマットタイプのテスト"""
        with self.assertRaises(ValueError):
            create_formatter('invalid')


class TestTextFormatter(unittest.TestCase):
    """テキストフォーマッターのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.formatter = create_formatter('text')
        self.sample_elements = [
            ElementInfo(
                index=0,
                depth=1,
                name="Button1",
                title="Button1",
                control_type="Button",
                class_name="TButton",
                rectangle=[10, 20, 100, 50],
                visible=True,
                enabled=True
            ),
            ElementInfo(
                index=1,
                depth=2,
                name="Edit1",
                title="Edit1",
                control_type="Edit",
                class_name="TEdit",
                rectangle=[10, 60, 200, 80],
                visible=True,
                enabled=True
            )
        ]
    
    def test_format_elements_basic(self):
        """基本的な要素フォーマットのテスト"""
        result = self.formatter.format_elements(self.sample_elements)
        
        self.assertIsInstance(result, str)
        self.assertIn("Button1", result)
        self.assertIn("Edit1", result)
        self.assertIn("TButton", result)
        self.assertIn("TEdit", result)
    
    def test_format_elements_empty(self):
        """空の要素リストのテスト"""
        result = self.formatter.format_elements([])
        
        self.assertIsInstance(result, str)
        self.assertIn("要素が見つかりません", result)
    
    def test_format_elements_hierarchy(self):
        """階層表示のテスト"""
        result = self.formatter.format_elements(self.sample_elements)
        
        # 深度に応じたインデントがあることを確認
        lines = result.split('\n')
        depth1_line = next((line for line in lines if "Button1" in line), "")
        depth2_line = next((line for line in lines if "Edit1" in line), "")
        
        # depth=2の方がより深くインデントされていることを確認
        if depth1_line and depth2_line:
            depth1_indent = len(depth1_line) - len(depth1_line.lstrip())
            depth2_indent = len(depth2_line) - len(depth2_line.lstrip())
            self.assertGreater(depth2_indent, depth1_indent)
    
    def test_format_elements_with_selector(self):
        """セレクター付きフォーマットのテスト"""
        formatter_with_selector = create_formatter('text', emit_selector=True)
        result = formatter_with_selector.format_elements(self.sample_elements)
        
        self.assertIsInstance(result, str)
        self.assertIn("Button1", result)
        # セレクター情報が含まれていることを確認
        self.assertIn("child_window", result)
    
    def test_format_elements_special_characters(self):
        """特殊文字を含む要素のテスト"""
        special_elements = [
            ElementInfo(
                index=0,
                depth=1,
                name="Special & <Characters>",
                title="Special & <Characters>",
                control_type="Button",
                class_name="Special.Class"
            )
        ]
        
        result = self.formatter.format_elements(special_elements)
        
        self.assertIsInstance(result, str)
        self.assertIn("Special & <Characters>", result)
        self.assertIn("Special.Class", result)


class TestJSONFormatter(unittest.TestCase):
    """JSONフォーマッターのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.formatter = create_formatter('json')
        self.sample_elements = [
            ElementInfo(
                index=0,
                depth=1,
                name="Button1",
                title="Button1",
                auto_id="btn1",
                control_type="Button",
                class_name="TButton",
                rectangle=[10, 20, 100, 50],
                visible=True,
                enabled=True,
                path="Button[1]"
            ),
            ElementInfo(
                index=1,
                depth=2,
                name="Edit1",
                title="Edit1",
                auto_id="edit1",
                control_type="Edit",
                class_name="TEdit",
                rectangle=[10, 60, 200, 80],
                visible=False,
                enabled=True,
                path="Edit[2]"
            )
        ]
    
    def test_format_elements_basic(self):
        """基本的なJSONフォーマットのテスト"""
        result = self.formatter.format_elements(self.sample_elements)
        
        # JSONとしてパース可能か確認
        parsed = json.loads(result)
        
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 2)
        
        # 1番目の要素の内容確認
        first_element = parsed[0]
        self.assertEqual(first_element['index'], 0)
        self.assertEqual(first_element['name'], "Button1")
        self.assertEqual(first_element['control_type'], "Button")
        self.assertTrue(first_element['visible'])
    
    def test_format_elements_with_fields(self):
        """フィールド指定付きJSONフォーマットのテスト"""
        formatter_with_fields = create_formatter('json', fields=['name', 'control_type', 'visible'])
        result = formatter_with_fields.format_elements(self.sample_elements)
        
        parsed = json.loads(result)
        
        # 指定したフィールドのみが含まれていることを確認
        first_element = parsed[0]
        self.assertIn('name', first_element)
        self.assertIn('control_type', first_element)
        self.assertIn('visible', first_element)
        
        # 指定していないフィールドは含まれていないことを確認
        self.assertNotIn('auto_id', first_element)
        self.assertNotIn('class_name', first_element)
        self.assertNotIn('rectangle', first_element)
    
    def test_format_elements_empty(self):
        """空の要素リストのJSONテスト"""
        result = self.formatter.format_elements([])
        
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 0)
    
    def test_format_elements_null_values(self):
        """null値を含む要素のJSONテスト"""
        elements_with_nulls = [
            ElementInfo(
                index=0,
                depth=1,
                name=None,
                title="",
                auto_id=None,
                control_type="Unknown",
                class_name=None,
                rectangle=None,
                visible=None,
                enabled=None,
                path=None
            )
        ]
        
        result = self.formatter.format_elements(elements_with_nulls)
        
        parsed = json.loads(result)
        first_element = parsed[0]
        
        self.assertIsNone(first_element['name'])
        self.assertEqual(first_element['title'], "")
        self.assertIsNone(first_element['auto_id'])
        self.assertIsNone(first_element['rectangle'])
    
    def test_format_elements_japanese_text(self):
        """日本語テキストのJSONテスト"""
        japanese_elements = [
            ElementInfo(
                index=0,
                depth=1,
                name="ボタン",
                title="実行ボタン",
                control_type="Button",
                class_name="ボタンクラス"
            )
        ]
        
        result = self.formatter.format_elements(japanese_elements)
        
        parsed = json.loads(result)
        first_element = parsed[0]
        
        self.assertEqual(first_element['name'], "ボタン")
        self.assertEqual(first_element['title'], "実行ボタン")
        self.assertEqual(first_element['class_name'], "ボタンクラス")
    
    def test_json_output_structure(self):
        """JSON出力構造のテスト"""
        result = self.formatter.format_elements(self.sample_elements)
        parsed = json.loads(result)
        
        # 必須フィールドが全て含まれていることを確認
        required_fields = ['index', 'depth', 'name', 'title', 'auto_id', 
                          'control_type', 'class_name', 'rectangle', 
                          'visible', 'enabled', 'path']
        
        for element in parsed:
            for field in required_fields:
                self.assertIn(field, element)


class TestFormatterEdgeCases(unittest.TestCase):
    """フォーマッターの境界値テスト"""
    
    def test_large_element_list(self):
        """大量要素のフォーマットテスト"""
        large_elements = []
        for i in range(100):
            large_elements.append(
                ElementInfo(
                    index=i,
                    depth=1,
                    name=f"Element{i}",
                    control_type="Button"
                )
            )
        
        text_formatter = create_formatter('text')
        json_formatter = create_formatter('json')
        
        # フォーマット処理が完了することを確認
        text_result = text_formatter.format_elements(large_elements)
        json_result = json_formatter.format_elements(large_elements)
        
        self.assertIsInstance(text_result, str)
        self.assertIsInstance(json_result, str)
        
        # JSONの要素数確認
        parsed_json = json.loads(json_result)
        self.assertEqual(len(parsed_json), 100)
    
    def test_deep_hierarchy(self):
        """深い階層のフォーマットテスト"""
        deep_elements = []
        for depth in range(1, 11):  # depth 1-10
            deep_elements.append(
                ElementInfo(
                    index=depth-1,
                    depth=depth,
                    name=f"Depth{depth}",
                    control_type="Container"
                )
            )
        
        formatter = create_formatter('text')
        result = formatter.format_elements(deep_elements)
        
        self.assertIsInstance(result, str)
        # 深度の異なる要素が全て含まれていることを確認
        for depth in range(1, 11):
            self.assertIn(f"Depth{depth}", result)
    
    def test_very_long_strings(self):
        """非常に長い文字列のテスト"""
        long_name = "A" * 1000  # 1000文字の名前
        
        long_elements = [
            ElementInfo(
                index=0,
                depth=1,
                name=long_name,
                title=long_name,
                control_type="Button"
            )
        ]
        
        text_formatter = create_formatter('text')
        json_formatter = create_formatter('json')
        
        text_result = text_formatter.format_elements(long_elements)
        json_result = json_formatter.format_elements(long_elements)
        
        self.assertIn(long_name, text_result)
        
        parsed_json = json.loads(json_result)
        self.assertEqual(parsed_json[0]['name'], long_name)


if __name__ == '__main__':
    unittest.main()
