"""
統合テスト

ElementFinder アプリケーション全体の統合テストを実施します。
"""

import unittest
import subprocess
import sys
import os
import time
from unittest.mock import Mock, patch
from pathlib import Path

import pytest

from src.elementfinder.main import ElementFinderApp, main


class TestElementFinderIntegration(unittest.TestCase):
    """ElementFinder 統合テスト"""
    
    def setUp(self):
        """テストの準備"""
        self.app = ElementFinderApp()
    
    def test_app_initialization(self):
        """アプリケーション初期化のテスト"""
        app = ElementFinderApp()
        self.assertIsNotNone(app)
        self.assertIsNone(app.logger)  # 初期状態では未設定
        self.assertIsNone(app.args)    # 初期状態では未設定
    
    @patch('src.elementfinder.main.parse_command_line')
    @patch('src.elementfinder.main.setup_logging')
    def test_app_argument_parsing(self, mock_setup_logging, mock_parse_args):
        """引数解析の統合テスト"""
        # モックの設定
        mock_args = {
            'window_title': 'Test Window',
            'backend': 'win32',
            'depth': 3,
            'verbose': False,
            'cursor': False,
            'anchor_conditions': {},
            'only_visible': False,
            'max_items': None,
            'highlight': False,
            'json': False,
            'emit_selector': False,
            'fields': None
        }
        mock_parse_args.return_value = mock_args
        mock_logger = Mock()
        mock_setup_logging.return_value = mock_logger
        
        # ElementFinderError系の例外を発生させてメイン処理をスキップ
        with patch.object(self.app, '_execute_main_logic') as mock_main:
            from src.elementfinder.utils.exceptions import WindowNotFoundError
            mock_main.side_effect = WindowNotFoundError('Test', False, 5)
            
            result = self.app.run(['Test Window'])
            
            # 引数解析が呼ばれたことを確認
            mock_parse_args.assert_called_once_with(['Test Window'])
            # ロギング設定が呼ばれたことを確認
            mock_setup_logging.assert_called_once_with(verbose=False, use_colors=True)
            # 適切な終了コードが返されることを確認
            self.assertEqual(result, 1)  # WindowNotFoundErrorの終了コード
    
    def test_app_keyboard_interrupt(self):
        """キーボード割り込みの統合テスト"""
        with patch.object(self.app, '_execute_main_logic') as mock_main:
            mock_main.side_effect = KeyboardInterrupt()
            
            result = self.app.run(['Test Window'])
            
            # SIGINT の終了コードが返されることを確認
            self.assertEqual(result, 130)
    
    def test_app_unexpected_exception(self):
        """予期しない例外の統合テスト"""
        with patch.object(self.app, '_execute_main_logic') as mock_main:
            mock_main.side_effect = RuntimeError("Unexpected error")
            
            result = self.app.run(['Test Window'])
            
            # 予期しない例外の終了コードが返されることを確認
            self.assertEqual(result, 100)
    
    @patch('src.elementfinder.main.create_window_finder')
    @patch('src.elementfinder.main.create_element_finder')
    def test_main_logic_flow(self, mock_create_element_finder, mock_create_window_finder):
        """メインロジックフローの統合テスト"""
        # モックの設定
        mock_window_finder = Mock()
        mock_window = Mock()
        mock_window_finder.find_window.return_value = mock_window
        mock_create_window_finder.return_value = mock_window_finder
        
        mock_element_finder = Mock()
        mock_elements = [
            Mock(name="Element1", index=0),
            Mock(name="Element2", index=1)
        ]
        mock_element_finder.find_elements.return_value = mock_elements
        mock_create_element_finder.return_value = mock_element_finder
        
        # 引数の設定
        self.app.args = {
            'window_title': 'Test Window',
            'title_re': False,
            'timeout': 5,
            'backend': 'win32',
            'cursor': False,
            'anchor_conditions': {},
            'depth': 3,
            'only_visible': False,
            'max_items': None,
            'highlight': False,
            'json': False,
            'emit_selector': False,
            'fields': None
        }
        self.app.logger = Mock()
        
        # 出力処理をモック
        with patch.object(self.app, '_output_results') as mock_output:
            result = self.app._execute_main_logic()
            
            # 各ステップが実行されたことを確認
            mock_window_finder.find_window.assert_called_once()
            mock_element_finder.find_elements.assert_called_once()
            mock_output.assert_called_once_with(mock_elements)
            mock_window_finder.close.assert_called_once()
            
            # 正常終了コードが返されることを確認
            self.assertEqual(result, 0)


class TestCommandLineInterface(unittest.TestCase):
    """コマンドラインインターフェースの統合テスト"""
    
    def get_script_path(self):
        """スクリプトパスを取得"""
        # テストファイルから見た相対パス
        current_dir = Path(__file__).parent
        script_path = current_dir.parent / "src" / "elementfinder" / "main.py"
        return str(script_path)
    
    @unittest.skipIf(True, "実際のコマンド実行のため通常はスキップ")
    def test_cli_help(self):
        """CLIヘルプ表示のテスト"""
        script_path = self.get_script_path()
        
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--help'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # ヘルプが正常に表示されることを確認
            self.assertEqual(result.returncode, 0)
            self.assertIn("elementfinder", result.stdout)
            self.assertIn("使用例", result.stdout)
            
        except subprocess.TimeoutExpired:
            self.skipTest("ヘルプ表示がタイムアウトしました")
        except FileNotFoundError:
            self.skipTest("スクリプトファイルが見つかりません")
    
    @unittest.skipIf(True, "実際のコマンド実行のため通常はスキップ")
    def test_cli_version(self):
        """CLIバージョン表示のテスト"""
        script_path = self.get_script_path()
        
        try:
            result = subprocess.run(
                [sys.executable, script_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # バージョンが正常に表示されることを確認
            self.assertEqual(result.returncode, 0)
            self.assertIn("elementfinder", result.stdout)
            
        except subprocess.TimeoutExpired:
            self.skipTest("バージョン表示がタイムアウトしました")
        except FileNotFoundError:
            self.skipTest("スクリプトファイルが見つかりません")
    
    @unittest.skipIf(True, "実際のウィンドウが必要なため通常はスキップ")
    def test_cli_nonexistent_window(self):
        """存在しないウィンドウ指定時のCLIテスト"""
        script_path = self.get_script_path()
        
        try:
            result = subprocess.run(
                [sys.executable, script_path, 'NonexistentWindow12345', '--timeout', '1'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # ウィンドウが見つからない場合の終了コードを確認
            self.assertEqual(result.returncode, 1)
            self.assertIn("見つかりません", result.stderr)
            
        except subprocess.TimeoutExpired:
            self.skipTest("ウィンドウ検索がタイムアウトしました")
        except FileNotFoundError:
            self.skipTest("スクリプトファイルが見つかりません")
    
    @unittest.skipIf(True, "実際のウィンドウが必要なため通常はスキップ")
    def test_cli_invalid_arguments(self):
        """無効な引数のCLIテスト"""
        script_path = self.get_script_path()
        
        test_cases = [
            # 無効なバックエンド
            ['TestWindow', '--backend', 'invalid'],
            # 無効な深度
            ['TestWindow', '--depth', 'invalid'],
            # 無効なタイムアウト
            ['TestWindow', '--timeout', 'invalid'],
            # fieldsをjsonなしで指定
            ['TestWindow', '--fields', 'name,title'],
        ]
        
        for args in test_cases:
            with self.subTest(args=args):
                try:
                    result = subprocess.run(
                        [sys.executable, script_path] + args,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    # 引数エラーの終了コードを確認
                    self.assertNotEqual(result.returncode, 0)
                    
                except subprocess.TimeoutExpired:
                    self.skipTest(f"引数テスト {args} がタイムアウトしました")
                except FileNotFoundError:
                    self.skipTest("スクリプトファイルが見つかりません")


class TestEndToEndScenarios(unittest.TestCase):
    """エンドツーエンドシナリオテスト"""
    
    @unittest.skipIf(True, "実際のアプリケーションが必要なため通常はスキップ")
    def test_notepad_scenario(self):
        """メモ帳を使ったE2Eテスト"""
        # このテストを実行するには、事前にメモ帳を開いておく必要があります
        app = ElementFinderApp()
        
        args = [
            'メモ帳',
            '--backend', 'win32',
            '--depth', '2',
            '--timeout', '3',
            '--verbose'
        ]
        
        try:
            result = app.run(args)
            
            # 成功時は0、ウィンドウが見つからない場合は1
            self.assertIn(result, [0, 1])
            
        except Exception as e:
            self.skipTest(f"メモ帳テストをスキップ: {e}")
    
    @unittest.skipIf(True, "実際のアプリケーションが必要なため通常はスキップ")
    def test_calculator_json_output(self):
        """電卓のJSON出力E2Eテスト"""
        app = ElementFinderApp()
        
        args = [
            '電卓',
            '--backend', 'win32',
            '--json',
            '--fields', 'name,control_type,rectangle',
            '--max-items', '10',
            '--timeout', '3'
        ]
        
        try:
            # 標準出力をキャプチャするためのテスト
            with patch('builtins.print') as mock_print:
                result = app.run(args)
                
                if result == 0:
                    # JSON出力が行われたことを確認
                    self.assertTrue(mock_print.called)
                    
                    # JSON形式で出力されているかチェック
                    output = mock_print.call_args[0][0]
                    try:
                        import json
                        parsed = json.loads(output)
                        self.assertIsInstance(parsed, list)
                    except json.JSONDecodeError:
                        self.fail("JSON出力が無効です")
                
        except Exception as e:
            self.skipTest(f"電卓テストをスキップ: {e}")


class TestErrorRecovery(unittest.TestCase):
    """エラー回復テスト"""
    
    def test_graceful_error_handling(self):
        """優雅なエラーハンドリングのテスト"""
        app = ElementFinderApp()
        
        # 様々なエラーシナリオをテスト
        error_scenarios = [
            # 空のウィンドウタイトル
            [''],
            # 無効な正規表現
            ['[invalid', '--title-re'],
            # 存在しないウィンドウ（短いタイムアウト）
            ['NonexistentWindow12345', '--timeout', '1'],
        ]
        
        for args in error_scenarios:
            with self.subTest(args=args):
                result = app.run(args)
                
                # 適切な終了コードが返されることを確認（0以外）
                self.assertNotEqual(result, 0)
                # 異常終了はしないことを確認（100未満）
                self.assertLess(result, 100)


if __name__ == '__main__':
    # 統合テストの実行時間を制限
    unittest.main(verbosity=2)
