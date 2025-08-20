"""
ElementFinder コマンドライン引数解析

要件定義書に基づく完全なコマンドライン引数の解析を提供します。
"""

import argparse
import sys
from typing import Dict, Any, Optional

from ..utils.exceptions import InvalidArgumentError
from ..utils.validators import (
    validate_depth, validate_fields, validate_timeout, validate_cursor_delay,
    validate_max_items, validate_found_index, validate_backend,
    validate_window_title, validate_anchor_value,
    validate_mutually_exclusive_options, validate_required_combinations
)
from .. import __version__


class ElementFinderArgumentParser:
    """
    ElementFinder専用のコマンドライン引数解析クラス
    """
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """
        argparseパーサーを作成します
        
        Returns:
            設定済みのArgumentParserインスタンス
        """
        parser = argparse.ArgumentParser(
            prog='findui',
            description='GUIアプリケーションの要素特定を効率化するCLIツール',
            epilog='''
使用例:
  # 設定ウィンドウのPane要素をアンカーに、3階層まで取得（UIA）
  findui "アプリ - 設定" --backend uia --anchor-control-type Pane --depth 3
  
  # カーソル下の要素をアンカーに、全階層をJSON出力（ウィンドウタイトル不要）
  findui --cursor --depth max --json
  
  # 複数マッチ時の2番目を選択
  findui "アプリ" --anchor-title "詳細" --anchor-found-index 1
            ''',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # 位置引数（--cursor指定時はオプション）
        parser.add_argument(
            'window_title',
            nargs='?',  # オプション引数に変更
            help='ウィンドウタイトル（完全一致、--title-reで正規表現可、--cursor指定時は不要）'
        )
        
        # オプション引数
        self._add_basic_options(parser)
        self._add_anchor_options(parser)
        self._add_cursor_options(parser)
        self._add_output_options(parser)
        self._add_filter_options(parser)
        self._add_misc_options(parser)
        
        return parser
    
    def _add_basic_options(self, parser: argparse.ArgumentParser) -> None:
        """基本オプションを追加"""
        
        parser.add_argument(
            '--title-re',
            action='store_true',
            help='ウィンドウタイトルを正規表現として扱う'
        )
        
        parser.add_argument(
            '--backend',
            choices=['win32', 'uia'],
            default='win32',
            help='使用するバックエンド（既定: win32）'
        )
        
        parser.add_argument(
            '--depth',
            type=str,
            default='3',
            help='取得する階層の深さ（0以上の整数 または "max", 既定: 3）'
        )
        
        parser.add_argument(
            '--timeout',
            type=str,
            default='5',
            help='ウィンドウ待機タイムアウト秒数（既定: 5）'
        )
    
    def _add_anchor_options(self, parser: argparse.ArgumentParser) -> None:
        """アンカー関連オプションを追加"""
        
        anchor_group = parser.add_argument_group('アンカー指定', 'アンカー要素を特定するためのオプション')
        
        anchor_group.add_argument(
            '--anchor-control-type',
            help='アンカーのcontrol_type（UIA用）'
        )
        
        anchor_group.add_argument(
            '--anchor-title',
            help='アンカーのタイトル'
        )
        
        anchor_group.add_argument(
            '--anchor-name',
            help='アンカーの名前'
        )
        
        anchor_group.add_argument(
            '--anchor-class-name',
            help='アンカーのクラス名'
        )
        
        anchor_group.add_argument(
            '--anchor-auto-id',
            help='アンカーの自動ID'
        )
        
        anchor_group.add_argument(
            '--anchor-found-index',
            type=str,
            default='0',
            help='アンカーの複数マッチ時の選択インデックス（既定: 0）'
        )
    
    def _add_cursor_options(self, parser: argparse.ArgumentParser) -> None:
        """カーソル関連オプションを追加"""
        
        cursor_group = parser.add_argument_group('カーソル指定', 'マウスカーソル位置をアンカーにするオプション')
        
        cursor_group.add_argument(
            '--cursor',
            action='store_true',
            help='マウスカーソル下の要素をアンカーとして使用'
        )
        
        cursor_group.add_argument(
            '--cursor-delay',
            type=str,
            default='5',
            help='カーソル位置取得までの遅延時間（秒, 既定: 5）'
        )
    
    def _add_output_options(self, parser: argparse.ArgumentParser) -> None:
        """出力関連オプションを追加"""
        
        output_group = parser.add_argument_group('出力制御', '出力形式と内容を制御するオプション')
        
        output_group.add_argument(
            '--json',
            action='store_true',
            help='JSON形式で出力'
        )
        
        output_group.add_argument(
            '--fields',
            type=str,
            help='JSON出力時の出力フィールド（カンマ区切り）'
        )
        
        output_group.add_argument(
            '--emit-selector',
            action='store_true',
            help='pywinautoセレクタを併記'
        )
        

        
        output_group.add_argument(
            '--pywinauto-native',
            action='store_true',
            help='pywinautoのprint_control_identifiers()を直接実行'
        )
        
        output_group.add_argument(
            '--max-items',
            type=str,
            help='最大出力件数'
        )
        
        output_group.add_argument(
            '--highlight',
            action='store_true',
            help='出力対象要素をハイライト表示'
        )
        
        output_group.add_argument(
            '--show-rectangle',
            action='store_true',
            help='座標情報を表示する'
        )
    
    def _add_filter_options(self, parser: argparse.ArgumentParser) -> None:
        """フィルター関連オプションを追加"""
        
        filter_group = parser.add_argument_group('フィルター', '出力要素を絞り込むオプション')
        
        filter_group.add_argument(
            '--only-visible',
            action='store_true',
            help='可視かつ有効な要素のみ出力'
        )
    
    def _add_misc_options(self, parser: argparse.ArgumentParser) -> None:
        """その他のオプションを追加"""
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='詳細ログを出力'
        )
        
        parser.add_argument(
            '--version',
            action='version',
            version=f'%(prog)s {__version__}',
            help='バージョン情報を表示'
        )
    
    def parse_args(self, args: Optional[list] = None) -> Dict[str, Any]:
        """
        コマンドライン引数を解析し、バリデーションを実行します
        
        Args:
            args: 解析する引数リスト（テスト用、Noneの場合はsys.argvを使用）
        
        Returns:
            Dict[str, Any]: 解析・検証済みの引数辞書
        
        Raises:
            InvalidArgumentError: 引数が無効な場合
            SystemExit: --help または --version 指定時
        """
        # 引数解析
        if args is None:
            args = sys.argv[1:]
        
        try:
            parsed_args = self.parser.parse_args(args)
        except SystemExit as e:
            # --help や --version、引数エラー時
            raise e
        
        # 引数辞書に変換
        args_dict = vars(parsed_args)
        
        # カスタムバリデーション実行
        validated_args = self._validate_arguments(args_dict)
        
        return validated_args
    
    def _validate_arguments(self, args_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析済み引数の詳細バリデーションを実行します
        
        Args:
            args_dict: 解析済み引数辞書
        
        Returns:
            Dict[str, Any]: 検証・正規化済み引数辞書
        
        Raises:
            InvalidArgumentError: バリデーションエラー
        """
        validated = {}
        
        # ウィンドウタイトル（--cursor指定時は不要）
        if args_dict['cursor'] and not args_dict['window_title']:
            # --cursor指定時はwindow_titleが未指定でもOK
            validated['window_title'] = None
            validated['title_re'] = False
        else:
            # window_titleが必須の場合
            if not args_dict['window_title']:
                raise InvalidArgumentError(
                    'window_title',
                    'required when not using --cursor',
                    '--cursorを指定しない場合はウィンドウタイトルが必須です'
                )
            validated['window_title'] = validate_window_title(
                args_dict['window_title'], 
                args_dict['title_re']
            )
            validated['title_re'] = args_dict['title_re']
        
        # バックエンド
        validated['backend'] = validate_backend(args_dict['backend'])
        
        # 深度
        validated['depth'] = validate_depth(args_dict['depth'])
        
        # タイムアウト
        validated['timeout'] = validate_timeout(args_dict['timeout'])
        
        # アンカー関連
        anchor_conditions = {}
        for anchor_key in ['anchor_control_type', 'anchor_title', 'anchor_name', 
                          'anchor_class_name', 'anchor_auto_id']:
            value = args_dict.get(anchor_key)
            if value:
                # キー名を正規化（anchor_control_type -> control_type）
                key_name = anchor_key.replace('anchor_', '').replace('_', '-')
                anchor_conditions[key_name] = validate_anchor_value(value, key_name)
        
        validated['anchor_conditions'] = anchor_conditions
        validated['anchor_found_index'] = validate_found_index(args_dict['anchor_found_index'])
        
        # カーソル関連
        validated['cursor'] = args_dict['cursor']
        validated['cursor_delay'] = validate_cursor_delay(args_dict['cursor_delay'])
        
        # 出力関連
        validated['json'] = args_dict['json']
        
        if args_dict.get('fields'):
            validated['fields'] = validate_fields(args_dict['fields'])
        else:
            validated['fields'] = None
        
        validated['emit_selector'] = args_dict['emit_selector']
        validated['pywinauto_native'] = args_dict['pywinauto_native']
        
        if args_dict.get('max_items'):
            validated['max_items'] = validate_max_items(args_dict['max_items'])
        else:
            validated['max_items'] = None
        
        validated['highlight'] = args_dict['highlight']
        validated['show_rectangle'] = args_dict.get('show_rectangle', False)
        
        # フィルター関連
        validated['only_visible'] = args_dict['only_visible']
        
        # その他
        validated['verbose'] = args_dict['verbose']
        
        # 相互排他的オプションのチェック
        exclusive_groups = [
            ['json', 'pywinauto_native']  # 出力形式は一つだけ選択可能
        ]
        validate_mutually_exclusive_options(args_dict, exclusive_groups)
        
        # 必須組み合わせのチェック
        combinations = [
            # 現在の要件では特になし（cursorとcursor-delayは独立）
        ]
        validate_required_combinations(args_dict, combinations)
        
        # 論理的妥当性のチェック
        self._validate_logical_consistency(validated)
        
        return validated
    
    def _validate_logical_consistency(self, args: Dict[str, Any]) -> None:
        """
        引数の論理的整合性をチェックします
        
        Args:
            args: 検証済み引数辞書
        
        Raises:
            InvalidArgumentError: 論理的に矛盾する引数の組み合わせ
        """
        # JSONオプションとfieldsの組み合わせ
        if args['fields'] and not args['json']:
            raise InvalidArgumentError(
                'fields',
                'specified without --json',
                '--fieldsは--jsonと併用してください'
            )
        
        # cursorとanchor条件の重複警告（エラーではない）
        if args['cursor'] and args['anchor_conditions']:
            # 要件では「cursor が優先」と明記されているため、エラーではない
            pass
        
        # アンカー条件が一つも指定されていない場合の確認
        if not args['cursor'] and not args['anchor_conditions']:
            # これは有効（ウィンドウ全体が対象になる）
            pass


def create_parser() -> ElementFinderArgumentParser:
    """
    ElementFinderの引数パーサーを作成します
    
    Returns:
        ElementFinderArgumentParserインスタンス
    """
    return ElementFinderArgumentParser()


def parse_command_line(args: Optional[list] = None) -> Dict[str, Any]:
    """
    コマンドライン引数を解析します（便利関数）
    
    Args:
        args: 解析する引数リスト（テスト用）
    
    Returns:
        Dict[str, Any]: 解析・検証済み引数辞書
    
    Raises:
        InvalidArgumentError: 引数が無効な場合
        SystemExit: --help や --version 指定時
    """
    parser = create_parser()
    return parser.parse_args(args)
