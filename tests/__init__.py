"""
ElementFinder テストモジュール

各種テストの実行とセットアップを管理します。
"""

import sys
import os
from pathlib import Path

# テスト実行時にsrcディレクトリをPythonパスに追加
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# テスト用の設定
TEST_CONFIG = {
    'timeout': 5,
    'verbose': True,
    'skip_integration': True,  # 統合テストをデフォルトでスキップ
}

def run_all_tests():
    """全テストを実行する関数"""
    import unittest
    
    # テストディスカバリー
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    # テスト実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_unit_tests():
    """単体テストのみを実行する関数"""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 単体テストモジュールを個別に追加
    test_modules = [
        'test_core.test_window_finder',
        'test_core.test_element_finder', 
        'test_core.test_cursor_handler',
        'test_cli.test_parser',
        'test_utils.test_validators',
        'test_utils.test_exceptions',
        'test_output.test_formatters'
    ]
    
    for module in test_modules:
        try:
            tests = loader.loadTestsFromName(module)
            suite.addTest(tests)
        except ImportError as e:
            print(f"テストモジュール {module} のロードに失敗: {e}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    # テストディレクトリから直接実行された場合
    success = run_all_tests()
    sys.exit(0 if success else 1)
