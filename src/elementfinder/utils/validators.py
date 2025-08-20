"""
ElementFinder バリデーション機能

コマンドライン引数やパラメータの妥当性をチェックする機能を提供します。
"""

import re
from typing import List, Union, Optional, Any
from .exceptions import InvalidArgumentError


def validate_depth(depth_str: str) -> Union[int, None]:
    """
    深度パラメータの妥当性をチェックします
    
    Args:
        depth_str: 深度文字列（'max' または数値）
    
    Returns:
        int: 深度値（maxの場合はNone）
    
    Raises:
        InvalidArgumentError: 無効な深度値の場合
    """
    if depth_str.lower() == 'max':
        return None
    
    try:
        depth = int(depth_str)
        if depth < 0:
            raise InvalidArgumentError('depth', depth_str, '0以上の整数 または "max"')
        return depth
    except ValueError:
        raise InvalidArgumentError('depth', depth_str, '0以上の整数 または "max"')


def validate_fields(fields_str: str) -> List[str]:
    """
    出力フィールドの妥当性をチェックします
    
    Args:
        fields_str: カンマ区切りのフィールド名
    
    Returns:
        List[str]: 正規化されたフィールド名のリスト
    
    Raises:
        InvalidArgumentError: 無効なフィールド名の場合
    """
    # 使用可能なフィールド一覧
    valid_fields = {
        'index', 'depth', 'name', 'title', 'auto_id', 'control_type',
        'class_name', 'rectangle', 'visible', 'enabled', 'path'
    }
    
    if not fields_str.strip():
        raise InvalidArgumentError('fields', fields_str, 'カンマ区切りのフィールド名')
    
    # カンマで分割して正規化
    fields = [field.strip().lower() for field in fields_str.split(',')]
    
    # 空のフィールド名をチェック
    if '' in fields:
        raise InvalidArgumentError('fields', fields_str, '空のフィールド名は使用できません')
    
    # 無効なフィールド名をチェック
    invalid_fields = set(fields) - valid_fields
    if invalid_fields:
        valid_fields_str = ', '.join(sorted(valid_fields))
        raise InvalidArgumentError(
            'fields', 
            ', '.join(invalid_fields), 
            f'以下のいずれか: {valid_fields_str}'
        )
    
    # 重複を除去（順序は保持）
    unique_fields = []
    for field in fields:
        if field not in unique_fields:
            unique_fields.append(field)
    
    return unique_fields


def validate_timeout(timeout_str: str) -> int:
    """
    タイムアウト値の妥当性をチェックします
    
    Args:
        timeout_str: タイムアウト文字列
    
    Returns:
        int: タイムアウト値（秒）
    
    Raises:
        InvalidArgumentError: 無効なタイムアウト値の場合
    """
    try:
        timeout = int(timeout_str)
        if timeout < 1:
            raise InvalidArgumentError('timeout', timeout_str, '1以上の整数')
        return timeout
    except ValueError:
        raise InvalidArgumentError('timeout', timeout_str, '1以上の整数')


def validate_cursor_delay(delay_str: str) -> float:
    """
    カーソル遅延時間の妥当性をチェックします
    
    Args:
        delay_str: 遅延時間文字列
    
    Returns:
        float: 遅延時間（秒）
    
    Raises:
        InvalidArgumentError: 無効な遅延時間の場合
    """
    try:
        delay = float(delay_str)
        if delay < 0:
            raise InvalidArgumentError('cursor-delay', delay_str, '0以上の数値')
        return delay
    except ValueError:
        raise InvalidArgumentError('cursor-delay', delay_str, '0以上の数値')


def validate_max_items(max_items_str: str) -> int:
    """
    最大出力件数の妥当性をチェックします
    
    Args:
        max_items_str: 最大件数文字列
    
    Returns:
        int: 最大件数
    
    Raises:
        InvalidArgumentError: 無効な件数の場合
    """
    try:
        max_items = int(max_items_str)
        if max_items < 1:
            raise InvalidArgumentError('max-items', max_items_str, '1以上の整数')
        return max_items
    except ValueError:
        raise InvalidArgumentError('max-items', max_items_str, '1以上の整数')


def validate_found_index(index_str: str) -> int:
    """
    アンカー検索インデックスの妥当性をチェックします
    
    Args:
        index_str: インデックス文字列
    
    Returns:
        int: インデックス値
    
    Raises:
        InvalidArgumentError: 無効なインデックス値の場合
    """
    try:
        index = int(index_str)
        if index < 0:
            raise InvalidArgumentError('anchor-found-index', index_str, '0以上の整数')
        return index
    except ValueError:
        raise InvalidArgumentError('anchor-found-index', index_str, '0以上の整数')


def validate_backend(backend: str) -> str:
    """
    バックエンド名の妥当性をチェックします
    
    Args:
        backend: バックエンド名
    
    Returns:
        str: 正規化されたバックエンド名
    
    Raises:
        InvalidArgumentError: 無効なバックエンド名の場合
    """
    valid_backends = {'win32', 'uia'}
    backend_lower = backend.lower()
    
    if backend_lower not in valid_backends:
        raise InvalidArgumentError('backend', backend, 'win32 または uia')
    
    return backend_lower


def validate_window_title(title: str, is_regex: bool = False) -> str:
    """
    ウィンドウタイトルの妥当性をチェックします
    
    Args:
        title: ウィンドウタイトル
        is_regex: 正規表現として扱うかどうか
    
    Returns:
        str: 検証済みのタイトル
    
    Raises:
        InvalidArgumentError: 無効なタイトルの場合
    """
    if not title.strip():
        raise InvalidArgumentError('window-title', title, '空でない文字列')
    
    # 正規表現の場合は構文チェック
    if is_regex:
        try:
            re.compile(title)
        except re.error as e:
            raise InvalidArgumentError('window-title', title, f'有効な正規表現: {e}')
    
    return title.strip()


def validate_anchor_value(value: str, anchor_type: str) -> str:
    """
    アンカー条件値の妥当性をチェックします
    
    Args:
        value: アンカー値
        anchor_type: アンカー種別（control-type, title, name等）
    
    Returns:
        str: 検証済みの値
    
    Raises:
        InvalidArgumentError: 無効な値の場合
    """
    if not value.strip():
        raise InvalidArgumentError(f'anchor-{anchor_type}', value, '空でない文字列')
    
    # control-typeの場合は特別な検証
    if anchor_type == 'control-type':
        # UIAの一般的なcontrol-typeをチェック（完全ではないが主要なもの）
        common_types = {
            'button', 'edit', 'text', 'combobox', 'listbox', 'list', 'listitem',
            'treeview', 'treeitem', 'tabcontrol', 'tab', 'tabitem', 'group',
            'pane', 'window', 'dialog', 'menu', 'menuitem', 'menubar',
            'toolbar', 'statusbar', 'progressbar', 'slider', 'checkbox',
            'radiobutton', 'image', 'hyperlink', 'table', 'header',
            'headeritem', 'dataitem', 'scrollbar', 'custom'
        }
        
        # 大文字小文字を無視して比較
        value_lower = value.lower()
        if value_lower not in common_types:
            # 警告はするが、エラーにはしない（カスタムコントロールの可能性）
            pass
    
    return value.strip()


def validate_mutually_exclusive_options(args_dict: dict, 
                                       exclusive_groups: List[List[str]]) -> None:
    """
    相互排他的なオプションの組み合わせをチェックします
    
    Args:
        args_dict: 引数辞書
        exclusive_groups: 相互排他的なオプショングループのリスト
    
    Raises:
        InvalidArgumentError: 相互排他的なオプションが同時指定された場合
    """
    for group in exclusive_groups:
        specified = [opt for opt in group if args_dict.get(opt.replace('-', '_'))]
        
        if len(specified) > 1:
            raise InvalidArgumentError(
                'option-combination',
                ', '.join([f'--{opt}' for opt in specified]),
                f'以下のオプションは同時に指定できません: {", ".join([f"--{opt}" for opt in group])}'
            )


def validate_required_combinations(args_dict: dict,
                                  combinations: List[dict]) -> None:
    """
    必須の組み合わせオプションをチェックします
    
    Args:
        args_dict: 引数辞書
        combinations: 必須組み合わせの設定リスト
                     例: [{'if': 'cursor', 'then_optional': ['cursor_delay']}]
    
    Raises:
        InvalidArgumentError: 必要な組み合わせが不足している場合
    """
    for combo in combinations:
        condition_key = combo['if'].replace('-', '_')
        
        if args_dict.get(condition_key):
            # 必須オプションのチェック
            if 'then_required' in combo:
                for required_opt in combo['then_required']:
                    required_key = required_opt.replace('-', '_')
                    if not args_dict.get(required_key):
                        raise InvalidArgumentError(
                            'option-combination',
                            f'--{combo["if"]}',
                            f'--{combo["if"]}を指定する場合は--{required_opt}も必要です'
                        )
