"""
バリデーターのテスト

utils.validators モジュールの動作をテストします。
"""

import unittest
import re

import pytest

from src.elementfinder.utils.validators import (
    validate_depth, validate_fields, validate_timeout, validate_cursor_delay,
    validate_max_items, validate_found_index, validate_backend,
    validate_window_title, validate_anchor_value,
    validate_mutually_exclusive_options, validate_required_combinations
)
from src.elementfinder.utils.exceptions import InvalidArgumentError


class TestDepthValidator(unittest.TestCase):
    """深度バリデーターのテスト"""
    
    def test_validate_depth_valid_numbers(self):
        """有効な数値のテスト"""
        # 正の整数
        self.assertEqual(validate_depth('1'), 1)
        self.assertEqual(validate_depth('3'), 3)
        self.assertEqual(validate_depth('10'), 10)
        self.assertEqual(validate_depth('100'), 100)
    
    def test_validate_depth_max(self):
        """maxキーワードのテスト"""
        self.assertIsNone(validate_depth('max'))
        self.assertIsNone(validate_depth('MAX'))
        self.assertIsNone(validate_depth('Max'))
    
    def test_validate_depth_invalid(self):
        """無効な値のテスト"""
        # 0以下
        with self.assertRaises(InvalidArgumentError):
            validate_depth('0')
        with self.assertRaises(InvalidArgumentError):
            validate_depth('-1')
        
        # 非数値
        with self.assertRaises(InvalidArgumentError):
            validate_depth('abc')
        with self.assertRaises(InvalidArgumentError):
            validate_depth('1.5')
        
        # 空文字列
        with self.assertRaises(InvalidArgumentError):
            validate_depth('')


class TestFieldsValidator(unittest.TestCase):
    """フィールドバリデーターのテスト"""
    
    def test_validate_fields_valid(self):
        """有効なフィールド指定のテスト"""
        # 単一フィールド
        result = validate_fields('name')
        self.assertEqual(result, ['name'])
        
        # 複数フィールド
        result = validate_fields('name,title,class_name')
        self.assertEqual(result, ['name', 'title', 'class_name'])
        
        # スペース込み
        result = validate_fields('name, title , class_name')
        self.assertEqual(result, ['name', 'title', 'class_name'])
    
    def test_validate_fields_all_valid_fields(self):
        """全ての有効フィールドのテスト"""
        valid_fields = ['name', 'title', 'auto_id', 'control_type', 'class_name', 
                       'rectangle', 'visible', 'enabled', 'path', 'index', 'depth']
        
        for field in valid_fields:
            result = validate_fields(field)
            self.assertEqual(result, [field])
    
    def test_validate_fields_invalid(self):
        """無効なフィールド指定のテスト"""
        # 無効なフィールド名
        with self.assertRaises(InvalidArgumentError):
            validate_fields('invalid_field')
        
        # 混在（有効と無効）
        with self.assertRaises(InvalidArgumentError):
            validate_fields('name,invalid_field')
        
        # 空文字列
        with self.assertRaises(InvalidArgumentError):
            validate_fields('')
        
        # 空の要素
        with self.assertRaises(InvalidArgumentError):
            validate_fields('name,,title')


class TestTimeoutValidator(unittest.TestCase):
    """タイムアウトバリデーターのテスト"""
    
    def test_validate_timeout_valid(self):
        """有効なタイムアウト値のテスト"""
        self.assertEqual(validate_timeout('1'), 1)
        self.assertEqual(validate_timeout('5'), 5)
        self.assertEqual(validate_timeout('30'), 30)
        self.assertEqual(validate_timeout('100'), 100)
    
    def test_validate_timeout_invalid(self):
        """無効なタイムアウト値のテスト"""
        # 0以下
        with self.assertRaises(InvalidArgumentError):
            validate_timeout('0')
        with self.assertRaises(InvalidArgumentError):
            validate_timeout('-1')
        
        # 非数値
        with self.assertRaises(InvalidArgumentError):
            validate_timeout('abc')
        with self.assertRaises(InvalidArgumentError):
            validate_timeout('1.5')


class TestCursorDelayValidator(unittest.TestCase):
    """カーソル遅延バリデーターのテスト"""
    
    def test_validate_cursor_delay_valid(self):
        """有効な遅延時間のテスト"""
        self.assertEqual(validate_cursor_delay('0'), 0.0)
        self.assertEqual(validate_cursor_delay('1'), 1.0)
        self.assertEqual(validate_cursor_delay('5.5'), 5.5)
        self.assertEqual(validate_cursor_delay('10'), 10.0)
    
    def test_validate_cursor_delay_invalid(self):
        """無効な遅延時間のテスト"""
        # 負の値
        with self.assertRaises(InvalidArgumentError):
            validate_cursor_delay('-1')
        with self.assertRaises(InvalidArgumentError):
            validate_cursor_delay('-0.5')
        
        # 非数値
        with self.assertRaises(InvalidArgumentError):
            validate_cursor_delay('abc')


class TestMaxItemsValidator(unittest.TestCase):
    """最大件数バリデーターのテスト"""
    
    def test_validate_max_items_valid(self):
        """有効な最大件数のテスト"""
        self.assertEqual(validate_max_items('1'), 1)
        self.assertEqual(validate_max_items('10'), 10)
        self.assertEqual(validate_max_items('100'), 100)
        self.assertEqual(validate_max_items('1000'), 1000)
    
    def test_validate_max_items_invalid(self):
        """無効な最大件数のテスト"""
        # 0以下
        with self.assertRaises(InvalidArgumentError):
            validate_max_items('0')
        with self.assertRaises(InvalidArgumentError):
            validate_max_items('-1')
        
        # 非数値
        with self.assertRaises(InvalidArgumentError):
            validate_max_items('abc')
        with self.assertRaises(InvalidArgumentError):
            validate_max_items('1.5')


class TestFoundIndexValidator(unittest.TestCase):
    """発見インデックスバリデーターのテスト"""
    
    def test_validate_found_index_valid(self):
        """有効なインデックスのテスト"""
        self.assertEqual(validate_found_index('0'), 0)
        self.assertEqual(validate_found_index('1'), 1)
        self.assertEqual(validate_found_index('10'), 10)
    
    def test_validate_found_index_invalid(self):
        """無効なインデックスのテスト"""
        # 負の値
        with self.assertRaises(InvalidArgumentError):
            validate_found_index('-1')
        
        # 非数値
        with self.assertRaises(InvalidArgumentError):
            validate_found_index('abc')
        with self.assertRaises(InvalidArgumentError):
            validate_found_index('1.5')


class TestBackendValidator(unittest.TestCase):
    """バックエンドバリデーターのテスト"""
    
    def test_validate_backend_valid(self):
        """有効なバックエンドのテスト"""
        self.assertEqual(validate_backend('win32'), 'win32')
        self.assertEqual(validate_backend('uia'), 'uia')
    
    def test_validate_backend_invalid(self):
        """無効なバックエンドのテスト"""
        with self.assertRaises(InvalidArgumentError):
            validate_backend('invalid')
        with self.assertRaises(InvalidArgumentError):
            validate_backend('WIN32')  # 大文字小文字厳密
        with self.assertRaises(InvalidArgumentError):
            validate_backend('')


class TestWindowTitleValidator(unittest.TestCase):
    """ウィンドウタイトルバリデーターのテスト"""
    
    def test_validate_window_title_normal(self):
        """通常のウィンドウタイトルのテスト"""
        title = "Test Window"
        result = validate_window_title(title, False)
        self.assertEqual(result, title)
    
    def test_validate_window_title_regex_valid(self):
        """有効な正規表現ウィンドウタイトルのテスト"""
        title = "Test.*Window"
        result = validate_window_title(title, True)
        self.assertEqual(result, title)
        
        # 複雑な正規表現
        title = r"^App\s+\d+\.\d+$"
        result = validate_window_title(title, True)
        self.assertEqual(result, title)
    
    def test_validate_window_title_regex_invalid(self):
        """無効な正規表現ウィンドウタイトルのテスト"""
        # 不正な正規表現
        with self.assertRaises(InvalidArgumentError):
            validate_window_title("[invalid", True)
        
        with self.assertRaises(InvalidArgumentError):
            validate_window_title("*invalid", True)
    
    def test_validate_window_title_empty(self):
        """空のウィンドウタイトルのテスト"""
        with self.assertRaises(InvalidArgumentError):
            validate_window_title("", False)
        
        with self.assertRaises(InvalidArgumentError):
            validate_window_title("", True)
        
        with self.assertRaises(InvalidArgumentError):
            validate_window_title("   ", False)  # 空白のみ


class TestAnchorValueValidator(unittest.TestCase):
    """アンカー値バリデーターのテスト"""
    
    def test_validate_anchor_value_valid(self):
        """有効なアンカー値のテスト"""
        # 基本的な値
        self.assertEqual(validate_anchor_value("Button", "control-type"), "Button")
        self.assertEqual(validate_anchor_value("OK", "title"), "OK")
        self.assertEqual(validate_anchor_value("btn_ok", "auto-id"), "btn_ok")
        
        # 特殊文字を含む値
        self.assertEqual(validate_anchor_value("Form.Button", "class-name"), "Form.Button")
    
    def test_validate_anchor_value_empty(self):
        """空のアンカー値のテスト"""
        with self.assertRaises(InvalidArgumentError):
            validate_anchor_value("", "control-type")
        
        with self.assertRaises(InvalidArgumentError):
            validate_anchor_value("   ", "title")


class TestMutuallyExclusiveValidator(unittest.TestCase):
    """相互排他オプションバリデーターのテスト"""
    
    def test_validate_mutually_exclusive_options_valid(self):
        """有効な相互排他オプションのテスト"""
        # 排他グループが指定されていない場合（現在の仕様）
        args = {'option1': True, 'option2': False}
        groups = []
        
        # 例外が発生しないことを確認
        try:
            validate_mutually_exclusive_options(args, groups)
        except Exception as e:
            self.fail(f"validate_mutually_exclusive_options raised {e} unexpectedly!")
    
    def test_validate_mutually_exclusive_options_conflict(self):
        """相互排他オプションの競合テスト"""
        # 将来的な拡張のためのテスト（現在は空の実装）
        pass


class TestRequiredCombinationsValidator(unittest.TestCase):
    """必須組み合わせバリデーターのテスト"""
    
    def test_validate_required_combinations_valid(self):
        """有効な必須組み合わせのテスト"""
        # 必須組み合わせが指定されていない場合（現在の仕様）
        args = {'option1': True, 'option2': True}
        combinations = []
        
        # 例外が発生しないことを確認
        try:
            validate_required_combinations(args, combinations)
        except Exception as e:
            self.fail(f"validate_required_combinations raised {e} unexpectedly!")


class TestValidatorEdgeCases(unittest.TestCase):
    """バリデーター境界値テスト"""
    
    def test_very_large_numbers(self):
        """非常に大きな数値のテスト"""
        # 大きなタイムアウト値
        result = validate_timeout('999999')
        self.assertEqual(result, 999999)
        
        # 大きな深度
        result = validate_depth('999999')
        self.assertEqual(result, 999999)
    
    def test_float_precision(self):
        """浮動小数点精度のテスト"""
        # 高精度の遅延時間
        result = validate_cursor_delay('1.23456789')
        self.assertAlmostEqual(result, 1.23456789, places=8)
    
    def test_unicode_strings(self):
        """Unicode文字列のテスト"""
        # 日本語ウィンドウタイトル
        title = "テストアプリケーション"
        result = validate_window_title(title, False)
        self.assertEqual(result, title)
        
        # 日本語アンカー値
        value = "ボタン"
        result = validate_anchor_value(value, "title")
        self.assertEqual(result, value)


if __name__ == '__main__':
    unittest.main()
