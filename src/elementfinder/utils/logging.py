"""
ElementFinder ロギング設定

アプリケーション全体で統一されたロギング機能を提供します。
--verboseオプションの有無により、ログレベルを動的に制御します。
"""

import logging
import sys
from typing import Optional


class ElementFinderFormatter(logging.Formatter):
    """
    ElementFinder専用のログフォーマッタ
    
    ログレベルに応じて色付けやプレフィックスを変更します。
    """
    
    # ANSIカラーコード（Windows Terminal対応）
    COLORS = {
        'DEBUG': '\033[36m',     # シアン
        'INFO': '\033[32m',      # 緑
        'WARNING': '\033[33m',   # 黄
        'ERROR': '\033[31m',     # 赤
        'CRITICAL': '\033[35m',  # マゼンタ
        'RESET': '\033[0m'       # リセット
    }
    
    def __init__(self, use_colors: bool = True):
        """
        Args:
            use_colors: カラー出力を使用するかどうか
        """
        super().__init__()
        self.use_colors = use_colors and sys.stderr.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをフォーマットします"""
        
        # ログレベルに応じたプレフィックス
        level_prefix = {
            'DEBUG': '[DEBUG]',
            'INFO': '[INFO] ',
            'WARNING': '[WARN] ',
            'ERROR': '[ERROR]',
            'CRITICAL': '[FATAL]'
        }.get(record.levelname, '[LOG]  ')
        
        # メッセージの組み立て
        message = f"{level_prefix} {record.getMessage()}"
        
        # カラー化
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            message = f"{color}{message}{reset}"
        
        return message


def setup_logging(verbose: bool = False, 
                 log_file: Optional[str] = None,
                 use_colors: bool = True) -> logging.Logger:
    """
    ElementFinderのロギングを設定します
    
    Args:
        verbose: 詳細ログ出力を有効にするか
        log_file: ログファイルのパス（Noneの場合はファイル出力しない）
        use_colors: カラー出力を使用するか
    
    Returns:
        設定済みのロガーインスタンス
    """
    
    # ロガーの取得
    logger = logging.getLogger('elementfinder')
    
    # 既存のハンドラをクリア（重複防止）
    logger.handlers.clear()
    
    # ログレベルの設定
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_handler.setFormatter(ElementFinderFormatter(use_colors=use_colors))
    logger.addHandler(console_handler)
    
    # ファイルハンドラの設定（指定された場合のみ）
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # ファイル出力用のフォーマッタ（色なし、タイムスタンプ付き）
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        except (OSError, IOError) as e:
            # ファイル出力に失敗してもアプリケーションは継続
            logger.warning(f"ログファイルの作成に失敗しました: {log_file} ({e})")
    
    # 上位ロガーへの伝播を無効化
    logger.propagate = False
    
    return logger


def get_logger(name: str = 'elementfinder') -> logging.Logger:
    """
    ElementFinderのロガーを取得します
    
    Args:
        name: ロガー名（デフォルト: 'elementfinder'）
    
    Returns:
        ロガーインスタンス
    
    Note:
        setup_logging()を事前に呼び出しておく必要があります。
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    関数呼び出しをログ出力するデコレータ
    
    デバッグ時に関数の実行開始・終了をトレースするために使用します。
    
    Usage:
        @log_function_call
        def some_function(arg1, arg2):
            # 処理
            return result
    """
    def wrapper(*args, **kwargs):
        logger = get_logger()
        
        # 引数の文字列化（長すぎる場合は省略）
        args_str = ', '.join([str(arg)[:50] + '...' if len(str(arg)) > 50 
                             else str(arg) for arg in args])
        kwargs_str = ', '.join([f"{k}={str(v)[:50] + '...' if len(str(v)) > 50 else str(v)}" 
                               for k, v in kwargs.items()])
        
        all_args = []
        if args_str:
            all_args.append(args_str)
        if kwargs_str:
            all_args.append(kwargs_str)
        
        args_display = ', '.join(all_args) if all_args else ''
        
        logger.debug(f"関数呼び出し開始: {func.__name__}({args_display})")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"関数呼び出し完了: {func.__name__}")
            return result
        except Exception as e:
            logger.debug(f"関数呼び出し失敗: {func.__name__} - {type(e).__name__}: {e}")
            raise
    
    return wrapper


# パフォーマンス測定用のログ出力
def log_performance(operation: str, duration: float, count: Optional[int] = None):
    """
    パフォーマンス情報をログ出力します
    
    Args:
        operation: 操作名
        duration: 実行時間（秒）
        count: 処理件数（オプション）
    """
    logger = get_logger()
    
    if count is not None:
        rate = count / duration if duration > 0 else 0
        logger.info(f"パフォーマンス: {operation} - {duration:.2f}秒 "
                   f"({count}件, {rate:.1f}件/秒)")
    else:
        logger.info(f"パフォーマンス: {operation} - {duration:.2f}秒")


# プログレス表示用（将来の拡張用）
class ProgressLogger:
    """
    長時間実行される操作の進行状況をログ出力するクラス
    """
    
    def __init__(self, operation: str, total: int):
        """
        Args:
            operation: 操作名
            total: 総件数
        """
        self.logger = get_logger()
        self.operation = operation
        self.total = total
        self.current = 0
        self.last_logged_percent = -1
    
    def update(self, increment: int = 1):
        """
        進行状況を更新します
        
        Args:
            increment: 増分（デフォルト: 1）
        """
        self.current += increment
        percent = int((self.current / self.total) * 100) if self.total > 0 else 0
        
        # 10%刻みでログ出力
        if percent >= self.last_logged_percent + 10:
            self.logger.info(f"{self.operation}: {self.current}/{self.total} ({percent}%)")
            self.last_logged_percent = percent
    
    def complete(self):
        """処理完了をログ出力します"""
        self.logger.info(f"{self.operation}: 完了 ({self.current}/{self.total})")
