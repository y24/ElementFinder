"""
ElementFinder 出力フォーマッタ

要素情報を人間が読みやすい形式やJSON形式に変換する機能を提供します。
"""

import json
import io
import sys
from contextlib import redirect_stdout
from typing import List, Dict, Any, Optional, Union

from ..core.element_finder import ElementInfo
from ..utils.logging import get_logger





class JSONFormatter:
    """
    JSON形式の出力フォーマッタ
    """
    
    def __init__(self, fields: Optional[List[str]] = None):
        """
        Args:
            fields: 出力するフィールドのリスト（Noneの場合は全フィールド）
        """
        self.fields = fields
        self.logger = get_logger()
    
    def format_elements(self, elements: List[ElementInfo]) -> str:
        """
        要素リストをJSON形式でフォーマットします
        
        Args:
            elements: 要素情報のリスト
        
        Returns:
            str: JSON文字列
        """
        element_dicts = []
        
        for element in elements:
            element_dict = element.to_dict()
            
            # フィールド絞り込み
            if self.fields:
                filtered_dict = {}
                for field in self.fields:
                    if field in element_dict:
                        filtered_dict[field] = element_dict[field]
                element_dict = filtered_dict
            
            element_dicts.append(element_dict)
        
        try:
            return json.dumps(element_dicts, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"JSON変換エラー: {e}")
            return json.dumps({"error": f"JSON変換に失敗しました: {e}"}, ensure_ascii=False, indent=2)


class PywinautoStyleFormatter:
    """
    pywinautoのprint_control_identifiers()風の出力フォーマッタ
    """
    
    def __init__(self, emit_selector: bool = True, show_alternative_ids: bool = True):
        """
        Args:
            emit_selector: child_windowセレクタを併記するか
            show_alternative_ids: 代替識別子リストを表示するか
        """
        self.emit_selector = emit_selector
        self.show_alternative_ids = show_alternative_ids
        self.logger = get_logger()
    
    def format_elements(self, elements: List[ElementInfo]) -> str:
        """
        要素リストをpywinauto風の形式でフォーマットします
        
        Args:
            elements: 要素情報のリスト
        
        Returns:
            str: フォーマット済みテキスト
        """
        if not elements:
            return "要素が見つかりませんでした。"
        
        lines = []
        for i, element in enumerate(elements):
            # 各要素の出力セクションを生成
            element_lines = self._format_single_element(element)
            lines.extend(element_lines)
            
            # 最後の要素以外は空白行を追加（次の要素の階層に応じたパイプ付き）
            if i < len(elements) - 1:
                next_element = elements[i + 1]
                blank_line_indent = self._get_pipe_indent(next_element.depth)
                lines.append(blank_line_indent)
        
        return "\n".join(lines)
    
    def _format_single_element(self, element: ElementInfo) -> List[str]:
        """
        単一要素をpywinauto風にフォーマットします
        
        Args:
            element: 要素情報
        
        Returns:
            List[str]: フォーマット済み行のリスト
        """
        lines = []
        
        # パイプインデント
        indent = self._get_pipe_indent(element.depth)
        
        # 1行目: 要素種別 - 'タイトル' (位置情報)
        first_line = self._format_element_header(element)
        if first_line:  # ヘッダー行が生成された場合のみ追加
            lines.append(f"{indent}{first_line}")
        
        # 2行目: 代替識別子リスト（オプション）
        if self.show_alternative_ids:
            alt_ids = self._generate_alternative_ids(element)
            if alt_ids:
                lines.append(f"{indent}{alt_ids}")
        
        # 3行目: child_windowセレクタ（オプション）
        if self.emit_selector:
            selector = self._generate_child_window_selector(element)
            if selector:
                lines.append(f"{indent}{selector}")
        
        return lines
    
    def _format_element_header(self, element: ElementInfo) -> str:
        """
        要素ヘッダー行を生成します（control_type - 'title' (位置)形式）
        
        Args:
            element: 要素情報
        
        Returns:
            str: ヘッダー行
        """
        # control_typeを取得（デフォルトはclass_name）
        control_type = element.control_type or element.class_name or "Element"
        
        # タイトル部分（シングルクォートで囲む）
        title = element.name or element.title or ""
        title_part = f"'{title}'"
        
        # 位置情報
        position_part = ""
        if element.rectangle:
            left, top, right, bottom = element.rectangle
            position_part = f"    (L{left}, T{top}, R{right}, B{bottom})"
        
        return f"{control_type} - {title_part}{position_part}"
    
    def _generate_alternative_ids(self, element: ElementInfo) -> str:
        """
        代替識別子のリストを生成します（pywinauto風）
        
        Args:
            element: 要素情報
        
        Returns:
            str: 代替識別子リスト文字列
        """
        ids = []
        
        # 基本的な識別子
        if element.name and element.name.strip():
            ids.append(element.name.strip())
        
        # control_typeとnameの組み合わせ
        if element.name and element.control_type:
            clean_name = element.name.strip()
            ids.append(f"{clean_name}{element.control_type}")
        
        # control_type単体
        if element.control_type:
            ids.append(element.control_type)
        
        # class_nameとnameの組み合わせ
        if element.name and element.class_name and element.class_name != element.control_type:
            clean_name = element.name.strip()
            ids.append(f"{clean_name}{element.class_name}")
        
        # class_name単体
        if element.class_name and element.class_name != element.control_type:
            ids.append(element.class_name)
        
        # インデックス付きバリエーション
        if element.name:
            clean_name = element.name.strip()
            ids.append(f"{clean_name}{element.index}")
        
        if element.control_type:
            ids.append(f"{element.control_type}{element.index}")
        
        # 重複除去
        unique_ids = []
        seen = set()
        for id_val in ids:
            if id_val and id_val not in seen:
                unique_ids.append(id_val)
                seen.add(id_val)
        
        if unique_ids:
            # pywinauto風にシングルクォートで囲む
            quoted_ids = [f"'{id_val}'" for id_val in unique_ids]
            return f"[{', '.join(quoted_ids)}]"
        
        return ""
    
    def _generate_child_window_selector(self, element: ElementInfo) -> str:
        """
        child_windowセレクタを生成します
        
        Args:
            element: 要素情報
        
        Returns:
            str: child_windowセレクタ文字列
        """
        conditions = []
        
        # titleまたはname（空でない場合のみ）
        if element.name and element.name.strip():
            conditions.append(f'title="{element.name.strip()}"')
        elif element.title and element.title.strip() and element.title != element.name:
            conditions.append(f'title="{element.title.strip()}"')
        
        # auto_id（最も確実な識別子）
        auto_id_value = None
        if element.auto_id:
            if callable(element.auto_id):
                try:
                    auto_id_value = element.auto_id()
                except:
                    auto_id_value = None
            else:
                auto_id_value = element.auto_id
            
            if auto_id_value and str(auto_id_value).strip():
                conditions.append(f'auto_id="{auto_id_value}"')
        
        # control_type（利用可能なら追加）
        if element.control_type and element.control_type.strip():
            conditions.append(f'control_type="{element.control_type}"')
        
        # class_name（常に追加、識別に重要）
        if element.class_name and element.class_name.strip():
            conditions.append(f'class_name="{element.class_name}"')
        
        # 条件が何もない場合のフォールバック
        if not conditions:
            # titleがあればそれだけでも有効
            pass  # titleは上で既にチェック済み
        
        return f"child_window({', '.join(conditions)})"
    
    def _get_pipe_indent(self, depth: int) -> str:
        """
        パイプ文字を使った階層インデントを生成します
        
        Args:
            depth: 要素の深度
        
        Returns:
            str: インデント文字列
        """
        if depth <= 0:
            return ""
        
        # pywinauto風の階層表示:
        # depth 0: "" (ウィンドウレベル)
        # depth 1: "   | "
        # depth 2: "   |    | "
        # depth 3: "   |    |    | "
        
        indent = ""
        for level in range(1, depth + 1):
            indent += "   | "
        
        return indent


class PywinautoNativeFormatter:
    """
    pywinautoのprint_control_identifiers()を直接使用するフォーマッタ
    """
    
    def __init__(self, depth: Optional[int] = None):
        """
        Args:
            depth: print_control_identifiersの深度パラメータ
        """
        self.depth = depth
        self.logger = get_logger()
    
    def format_elements(self, elements: List[ElementInfo], window_element=None) -> str:
        """
        pywinautoのprint_control_identifiers()を直接使用して出力します
        
        Args:
            elements: 要素情報のリスト（このフォーマッタでは使用されない）
            window_element: pywinautoのwindow要素
        
        Returns:
            str: pywinauto native出力
        """
        if window_element is None:
            return "エラー: pywinauto要素が提供されていません。"
        
        try:
            # pywinautoのprint_control_identifiers()の出力をキャプチャ
            output_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer):
                if self.depth is not None:
                    window_element.print_control_identifiers(depth=self.depth)
                else:
                    window_element.print_control_identifiers()
            
            result = output_buffer.getvalue()
            return result if result else "出力が生成されませんでした。"
            
        except Exception as e:
            self.logger.error(f"pywinauto native出力エラー: {e}")
            return f"エラー: pywinautoのprint_control_identifiers()実行失敗: {e}"


def create_formatter(format_type: str, **kwargs) -> Union[JSONFormatter, PywinautoStyleFormatter, PywinautoNativeFormatter]:
    """
    フォーマッタを作成します（便利関数）
    
    Args:
        format_type: フォーマット種別 ('json', 'pywinauto', 'pywinauto-native')
        **kwargs: フォーマッタ固有の引数
    
    Returns:
        フォーマッタインスタンス
    
    Raises:
        ValueError: 不明なフォーマット種別
    """
    if format_type == 'json':
        return JSONFormatter(**kwargs)
    elif format_type == 'pywinauto':
        return PywinautoStyleFormatter(**kwargs)
    elif format_type == 'pywinauto-native':
        return PywinautoNativeFormatter(**kwargs)
    else:
        raise ValueError(f"不明なフォーマット種別: {format_type}")
