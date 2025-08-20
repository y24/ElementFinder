"""
CLIパーサーのテスト

ElementFinderArgumentParser クラスの動作をテストします。
"""

import unittest
import sys
from unittest.mock import patch

import pytest

from src.elementfinder.cli.parser import (
    ElementFinderArgumentParser, create_parser, parse_command_line
)
from src.elementfinder.utils.exceptions import InvalidArgumentError


class TestElementFinderArgumentParser(unittest.TestCase):
    """ElementFinderArgumentParser クラスのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.parser = ElementFinderArgumentParser()
    
    def test_init(self):
        """初期化のテスト"""
        parser = ElementFinderArgumentParser()
        self.assertIsNotNone(parser.parser)
    
    def test_parse_basic_args(self):
        """基本引数の解析テスト"""
        args = ['Test Window']
        result = self.parser.parse_args(args)
        
        self.assertEqual(result['window_title'], 'Test Window')
        self.assertEqual(result['backend'], 'win32')
        self.assertEqual(result['depth'], 3)
        self.assertEqual(result['timeout'], 5)
        self.assertFalse(result['title_re'])
        self.assertFalse(result['cursor'])
        self.assertFalse(result['json'])
    
    def test_parse_all_basic_options(self):
        """基本オプション全体の解析テスト"""
        args = [
            'Test Window',
            '--title-re',
            '--backend', 'uia',
            '--depth', '5',
            '--timeout', '10'
        ]
        result = self.parser.parse_args(args)
        
        self.assertEqual(result['window_title'], 'Test Window')
        self.assertTrue(result['title_re'])
        self.assertEqual(result['backend'], 'uia')
        self.assertEqual(result['depth'], 5)
        self.assertEqual(result['timeout'], 10)
    
    def test_parse_anchor_options(self):
        """アンカーオプションの解析テスト"""
        args = [
            'Test Window',
            '--anchor-control-type', 'Button',
            '--anchor-title', 'OK',
            '--anchor-name', 'okButton',
            '--anchor-class-name', 'TButton',
            '--anchor-auto-id', 'btn_ok',
            '--anchor-found-index', '2'
        ]
        result = self.parser.parse_args(args)
        
        anchor_conditions = result['anchor_conditions']
        self.assertEqual(anchor_conditions['control-type'], 'Button')
        self.assertEqual(anchor_conditions['title'], 'OK')
        self.assertEqual(anchor_conditions['name'], 'okButton')
        self.assertEqual(anchor_conditions['class-name'], 'TButton')
        self.assertEqual(anchor_conditions['auto-id'], 'btn_ok')
        self.assertEqual(result['anchor_found_index'], 2)
    
    def test_parse_cursor_options(self):
        """カーソルオプションの解析テスト"""
        args = [
            'Test Window',
            '--cursor',
            '--cursor-delay', '3.5'
        ]
        result = self.parser.parse_args(args)
        
        self.assertTrue(result['cursor'])
        self.assertEqual(result['cursor_delay'], 3.5)
    
    def test_parse_output_options(self):
        """出力オプションの解析テスト"""
        args = [
            'Test Window',
            '--json',
            '--fields', 'name,control_type,rectangle',
            '--emit-selector',
            '--max-items', '100',
            '--highlight'
        ]
        result = self.parser.parse_args(args)
        
        self.assertTrue(result['json'])
        self.assertEqual(result['fields'], ['name', 'control_type', 'rectangle'])
        self.assertTrue(result['emit_selector'])
        self.assertEqual(result['max_items'], 100)
        self.assertTrue(result['highlight'])
    
    def test_parse_filter_options(self):
        """フィルターオプションの解析テスト"""
        args = [
            'Test Window',
            '--only-visible'
        ]
        result = self.parser.parse_args(args)
        
        self.assertTrue(result['only_visible'])
    
    def test_parse_misc_options(self):
        """その他オプションの解析テスト"""
        args = [
            'Test Window',
            '--verbose'
        ]
        result = self.parser.parse_args(args)
        
        self.assertTrue(result['verbose'])
    
    def test_parse_depth_max(self):
        """depth=maxの解析テスト"""
        args = ['Test Window', '--depth', 'max']
        result = self.parser.parse_args(args)
        
        self.assertIsNone(result['depth'])  # max は None に変換される
    
    def test_parse_invalid_depth(self):
        """無効なdepthの解析テスト"""
        args = ['Test Window', '--depth', 'invalid']
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_invalid_backend(self):
        """無効なbackendの解析テスト"""
        # argparseレベルでエラーになるため、SystemExitが発生
        args = ['Test Window', '--backend', 'invalid']
        
        with self.assertRaises(SystemExit):
            self.parser.parse_args(args)
    
    def test_parse_invalid_timeout(self):
        """無効なtimeoutの解析テスト"""
        args = ['Test Window', '--timeout', 'invalid']
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_invalid_cursor_delay(self):
        """無効なcursor-delayの解析テスト"""
        args = ['Test Window', '--cursor-delay', 'invalid']
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_invalid_max_items(self):
        """無効なmax-itemsの解析テスト"""
        args = ['Test Window', '--max-items', 'invalid']
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_invalid_anchor_found_index(self):
        """無効なanchor-found-indexの解析テスト"""
        args = ['Test Window', '--anchor-found-index', 'invalid']
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_fields_without_json(self):
        """JSONなしでfieldsを指定した場合のテスト"""
        args = ['Test Window', '--fields', 'name,title']
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_help(self):
        """ヘルプ表示のテスト"""
        args = ['--help']
        
        with self.assertRaises(SystemExit):
            self.parser.parse_args(args)
    
    def test_parse_version(self):
        """バージョン表示のテスト"""
        args = ['--version']
        
        with self.assertRaises(SystemExit):
            self.parser.parse_args(args)
    
    def test_parse_empty_window_title(self):
        """空のウィンドウタイトルのテスト"""
        args = ['']  # 空文字列
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_regex_window_title(self):
        """正規表現ウィンドウタイトルのテスト"""
        args = ['Test.*Window', '--title-re']
        result = self.parser.parse_args(args)
        
        self.assertEqual(result['window_title'], 'Test.*Window')
        self.assertTrue(result['title_re'])
    
    def test_parse_invalid_regex_window_title(self):
        """無効な正規表現ウィンドウタイトルのテスト"""
        args = ['[invalid regex', '--title-re']
        
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_negative_values(self):
        """負の値のテスト"""
        # 負のtimeout
        args = ['Test', '--timeout', '-1']
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
        
        # 負のdepth
        args = ['Test', '--depth', '-1']
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
        
        # 負のmax-items
        args = ['Test', '--max-items', '-1']
        with self.assertRaises(InvalidArgumentError):
            self.parser.parse_args(args)
    
    def test_parse_edge_case_values(self):
        """境界値のテスト"""
        # depth=1（最小値）
        args = ['Test', '--depth', '1']
        result = self.parser.parse_args(args)
        self.assertEqual(result['depth'], 1)
        
        # timeout=1（最小値）
        args = ['Test', '--timeout', '1']
        result = self.parser.parse_args(args)
        self.assertEqual(result['timeout'], 1)
        
        # cursor-delay=0（最小値）
        args = ['Test', '--cursor-delay', '0']
        result = self.parser.parse_args(args)
        self.assertEqual(result['cursor_delay'], 0.0)


class TestParserFactory(unittest.TestCase):
    """パーサーファクトリ関数のテスト"""
    
    def test_create_parser(self):
        """create_parser 関数のテスト"""
        parser = create_parser()
        self.assertIsInstance(parser, ElementFinderArgumentParser)
    
    def test_parse_command_line(self):
        """parse_command_line 関数のテスト"""
        args = ['Test Window', '--backend', 'uia']
        result = parse_command_line(args)
        
        self.assertEqual(result['window_title'], 'Test Window')
        self.assertEqual(result['backend'], 'uia')


class TestParserComplexScenarios(unittest.TestCase):
    """複雑なシナリオのテスト"""
    
    def setUp(self):
        """テストの準備"""
        self.parser = ElementFinderArgumentParser()
    
    def test_full_feature_parsing(self):
        """全機能を使った解析テスト"""
        args = [
            'Test.*Application',
            '--title-re',
            '--backend', 'uia',
            '--depth', 'max',
            '--timeout', '10',
            '--anchor-control-type', 'Pane',
            '--anchor-title', 'Settings',
            '--anchor-found-index', '1',
            '--cursor',
            '--cursor-delay', '2.5',
            '--json',
            '--fields', 'name,control_type,rectangle,visible',
            '--emit-selector',
            '--max-items', '50',
            '--highlight',
            '--only-visible',
            '--verbose'
        ]
        
        result = self.parser.parse_args(args)
        
        # 全ての設定が正しく解析されていることを確認
        self.assertEqual(result['window_title'], 'Test.*Application')
        self.assertTrue(result['title_re'])
        self.assertEqual(result['backend'], 'uia')
        self.assertIsNone(result['depth'])  # max
        self.assertEqual(result['timeout'], 10)
        self.assertEqual(result['anchor_conditions']['control-type'], 'Pane')
        self.assertEqual(result['anchor_conditions']['title'], 'Settings')
        self.assertEqual(result['anchor_found_index'], 1)
        self.assertTrue(result['cursor'])
        self.assertEqual(result['cursor_delay'], 2.5)
        self.assertTrue(result['json'])
        self.assertEqual(len(result['fields']), 4)
        self.assertTrue(result['emit_selector'])
        self.assertEqual(result['max_items'], 50)
        self.assertTrue(result['highlight'])
        self.assertTrue(result['only_visible'])
        self.assertTrue(result['verbose'])
    
    def test_anchor_and_cursor_combination(self):
        """アンカーとカーソルの組み合わせテスト"""
        # 要件では「cursorが優先」とされているため、両方指定可能
        args = [
            'Test Window',
            '--anchor-title', 'Button',
            '--cursor'
        ]
        
        result = self.parser.parse_args(args)
        
        self.assertTrue(result['cursor'])
        self.assertEqual(result['anchor_conditions']['title'], 'Button')
        # 両方設定されているが、実際の処理ではcursorが優先される


if __name__ == '__main__':
    unittest.main()
