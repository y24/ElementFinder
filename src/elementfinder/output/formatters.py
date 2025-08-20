"""
ElementFinder 出力フォーマッタ

要素情報を人間が読みやすい形式やJSON形式に変換する機能を提供します。
"""

import json
from typing import List, Dict, Any, Optional, Union

from ..core.element_finder import ElementInfo
from ..utils.logging import get_logger


class TextFormatter:
    """
    テキスト形式の出力フォーマッタ
    """
    
    def __init__(self, emit_selector: bool = False):
        """
        Args:
            emit_selector: pywinautoセレクタを併記するか
        """
        self.emit_selector = emit_selector
        self.logger = get_logger()
    
    def format_elements(self, elements: List[ElementInfo]) -> str:
        """
        要素リストをテキスト形式でフォーマットします
        
        Args:
            elements: 要素情報のリスト
        
        Returns:
            str: フォーマット済みテキスト
        """
        if not elements:
            return "要素が見つかりませんでした。"
        
        lines = []
        for element in elements:
            line = self._format_single_element(element)
            lines.append(line)
            
            # セレクタ併記
            if self.emit_selector:
                selector = self._generate_selector(element)
                if selector:
                    lines.append(f"  selector: {selector}")
        
        return "\n".join(lines)
    
    def _format_single_element(self, element: ElementInfo) -> str:
        """
        単一要素をフォーマットします
        
        Args:
            element: 要素情報
        
        Returns:
            str: フォーマット済み行
        """
        # インデント（深度に応じて）
        indent = "  " * (element.depth - 1) if element.depth > 1 else ""
        
        # 基本情報の組み立て
        parts = [f"[{element.index}]"]
        
        # 要素種別
        if element.control_type:
            parts.append(str(element.control_type))
        elif element.class_name:
            parts.append(str(element.class_name))
        else:
            parts.append("Element")
        
        # 名前/タイトル
        if element.name:
            parts.append(f"name='{str(element.name)}'")
        
        # auto_id
        if element.auto_id:
            parts.append(f"auto_id='{str(element.auto_id)}'")
        
        # クラス名（control_typeと異なる場合のみ）
        if element.class_name and element.class_name != element.control_type:
            parts.append(f"class='{str(element.class_name)}'")
        
        # 状態情報
        if element.visible is not None:
            parts.append(f"visible={element.visible}")
        
        if element.enabled is not None:
            parts.append(f"enabled={element.enabled}")
        
        # 矩形情報
        if element.rectangle:
            rect_str = f"({element.rectangle[0]},{element.rectangle[1]},{element.rectangle[2]},{element.rectangle[3]})"
            parts.append(f"rect={rect_str}")
        
        return f"{indent}{' '.join(parts)}"
    
    def _generate_selector(self, element: ElementInfo) -> Optional[str]:
        """
        pywinautoセレクタを生成します
        
        Args:
            element: 要素情報
        
        Returns:
            Optional[str]: セレクタ文字列
        """
        conditions = []
        
        # auto_idが最も確実
        if element.auto_id:
            conditions.append(f'auto_id="{element.auto_id}"')
        
        # control_type
        if element.control_type:
            conditions.append(f'control_type="{element.control_type}"')
        
        # 名前（auto_idがない場合）
        if not element.auto_id and element.name:
            conditions.append(f'title="{element.name}"')
        
        # クラス名（他の条件がない場合）
        if not conditions and element.class_name:
            conditions.append(f'class_name="{element.class_name}"')
        
        if conditions:
            return f"child_window({', '.join(conditions)})"
        
        return None


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


def create_formatter(format_type: str, **kwargs) -> Union[TextFormatter, JSONFormatter]:
    """
    フォーマッタを作成します（便利関数）
    
    Args:
        format_type: フォーマット種別 ('text' または 'json')
        **kwargs: フォーマッタ固有の引数
    
    Returns:
        フォーマッタインスタンス
    
    Raises:
        ValueError: 不明なフォーマット種別
    """
    if format_type == 'text':
        return TextFormatter(**kwargs)
    elif format_type == 'json':
        return JSONFormatter(**kwargs)
    else:
        raise ValueError(f"不明なフォーマット種別: {format_type}")
