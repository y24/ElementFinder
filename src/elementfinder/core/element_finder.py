"""
ElementFinder 要素検索・列挙機能

pywinautoを使用してGUI要素を検索・列挙し、フィルタリングやデータ変換を行います。
"""

import time
from typing import List, Dict, Any, Optional, Generator, Union
from dataclasses import dataclass

from pywinauto.application import WindowSpecification
from pywinauto.controls.hwndwrapper import HwndWrapper

from ..utils.exceptions import (
    NoElementsFoundError, PywinautoError, TimeoutError,
    handle_pywinauto_exception
)
from ..utils.logging import get_logger, log_function_call, log_performance, ProgressLogger


@dataclass
class ElementInfo:
    """
    要素情報を格納するデータクラス
    """
    index: int
    depth: int
    name: Optional[str] = None
    title: Optional[str] = None
    auto_id: Optional[str] = None
    control_type: Optional[str] = None
    class_name: Optional[str] = None
    rectangle: Optional[List[int]] = None
    visible: Optional[bool] = None
    enabled: Optional[bool] = None
    path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'index': self.index,
            'depth': self.depth,
            'name': self.name,
            'title': self.title,
            'auto_id': self.auto_id,
            'control_type': self.control_type,
            'class_name': self.class_name,
            'rectangle': self.rectangle,
            'visible': self.visible,
            'enabled': self.enabled,
            'path': self.path
        }


class ElementFinder:
    """
    GUI要素の検索・列挙を担当するクラス
    """
    
    def __init__(self, backend: str = 'win32'):
        """
        Args:
            backend: 使用するバックエンド ('win32' または 'uia')
        """
        self.backend = backend
        self.logger = get_logger()
    
    @log_function_call
    @handle_pywinauto_exception
    def find_elements(self,
                     anchor: Union[WindowSpecification, HwndWrapper],
                     depth: Optional[int] = 3,
                     only_visible: bool = False,
                     max_items: Optional[int] = None) -> List[ElementInfo]:
        """
        指定されたアンカー以下の要素を検索・列挙します
        
        Args:
            anchor: 検索の起点となるアンカー要素
            depth: 検索する深度（Noneの場合は無制限）
            only_visible: 可視要素のみを対象とするか
            max_items: 最大取得件数
        
        Returns:
            List[ElementInfo]: 要素情報のリスト
        
        Raises:
            NoElementsFoundError: 要素が見つからない場合
            PywinautoError: pywinauto操作エラー
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"要素検索開始: depth={depth}, only_visible={only_visible}, "
                           f"max_items={max_items}")
            
            # 要素を段階的に取得（アンカー自身も含む）
            elements = list(self._enumerate_elements(
                anchor, depth, only_visible, max_items
            ))
            
            duration = time.time() - start_time
            log_performance("要素検索", duration, len(elements))
            
            if not elements:
                filter_desc = self._build_filter_description(only_visible, max_items)
                raise NoElementsFoundError(filter_desc)
            
            self.logger.info(f"要素検索完了: {len(elements)}件取得")
            return elements
            
        except NoElementsFoundError:
            raise
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"要素検索失敗 ({duration:.2f}秒): {e}")
            raise PywinautoError(e, "要素検索")
    
    def _enumerate_elements(self,
                           anchor: Union[WindowSpecification, HwndWrapper],
                           depth: Optional[int],
                           only_visible: bool,
                           max_items: Optional[int]) -> Generator[ElementInfo, None, None]:
        """
        要素を段階的に列挙するジェネレータ
        
        Args:
            anchor: アンカー要素
            depth: 検索深度
            only_visible: 可視要素のみフラグ
            max_items: 最大件数
        
        Yields:
            ElementInfo: 要素情報
        """
        try:
            yielded_count = 0
            element_count = 0
            
            # 1. まずアンカー要素自身を最上位として出力
            try:
                anchor_info = self._extract_element_info(anchor, yielded_count, 0)  # depth=0 for top level
                if self._should_include_element(anchor_info, only_visible):
                    yield anchor_info
                    yielded_count += 1
                    
                    # 最大件数チェック
                    if max_items and yielded_count >= max_items:
                        self.logger.debug(f"最大件数到達: {max_items}")
                        return
                        
                self.logger.debug("アンカー要素自身を最上位レベルとして追加")
            except Exception as e:
                self.logger.debug(f"アンカー要素の情報取得失敗: {e}")
            
            # depth=0の場合はアンカー要素のみで終了
            if depth is not None and depth <= 0:
                self.logger.debug(f"depth={depth}のため、アンカー要素のみで終了")
                return
            
            # 2. 子孫要素を取得
            descendants = []
            try:
                if depth is None:
                    # 無制限の場合
                    descendants = list(anchor.descendants())
                elif depth == 1:
                    # depth=1の場合、直下の子要素のみを取得
                    try:
                        descendants = list(anchor.children())
                        self.logger.debug(f"children()で{len(descendants)}件の直下子要素を取得")
                    except Exception as e:
                        self.logger.debug(f"children()取得失敗: {e}")
                        descendants = []
                else:
                    # depth >= 2の場合、pywinautoのdescendantsを使用
                    # ユーザー入力のdepth=2 -> pywinautoのdepth=1（孫要素まで）
                    pywinauto_depth = depth - 1
                    descendants = list(anchor.descendants(depth=pywinauto_depth))
                    self.logger.debug(f"pywinauto descendants(depth={pywinauto_depth})で取得")
            except Exception as e:
                self.logger.debug(f"descendants()取得失敗: {e}")
                # 子孫要素が取得できない場合は空リストのまま
            
            self.logger.debug(f"descendants()で{len(descendants)}件の子孫要素を取得")
            
            # 子孫要素がない場合は、アンカー周辺の要素も検索（アンカー自身は除く）
            if not descendants and depth is not None and depth > 0:
                self.logger.debug("子孫要素がないため、アンカー周辺の要素を検索します")
                related_elements = self._get_related_elements(anchor)
                # アンカー自身は既に追加済みなので除外
                descendants = [elem for elem in related_elements if elem != anchor]
            
            # プログレス表示の準備（多数の要素が想定される場合）
            progress = None
            
            for element in descendants:
                element_count += 1
                
                # プログレス表示（1000件を超える場合）
                if element_count == 1000 and not progress:
                    progress = ProgressLogger("要素取得", 10000)  # 概算
                
                if progress and element_count % 100 == 0:
                    progress.update(100)
                
                try:
                    # 要素情報の取得 - 簡易的な深度計算（高速化のため）
                    relative_depth = self._calculate_fast_depth(element, yielded_count)
                    element_info = self._extract_element_info(element, yielded_count, relative_depth)
                    
                    # フィルタリング
                    if self._should_include_element(element_info, only_visible):
                        yield element_info
                        yielded_count += 1
                        
                        # 最大件数チェック
                        if max_items and yielded_count >= max_items:
                            self.logger.debug(f"最大件数到達: {max_items}")
                            break
                
                except Exception as e:
                    # 個別要素のエラーは無視して継続
                    self.logger.debug(f"要素情報取得失敗: {e}")
                    continue
            
            if progress:
                progress.complete()
            
            self.logger.debug(f"要素列挙完了: 総数={element_count + 1}, 出力={yielded_count}")
            
        except Exception as e:
            self.logger.error(f"要素列挙エラー: {e}")
            raise
    
    def _get_related_elements(self, anchor: Union[WindowSpecification, HwndWrapper]) -> List[HwndWrapper]:
        """
        アンカー要素の関連要素（兄弟、親の子要素など）を取得します
        
        Args:
            anchor: アンカー要素
        
        Returns:
            List[HwndWrapper]: 関連要素のリスト
        """
        related_elements = []
        
        try:
            # 1. アンカー自身を含める
            related_elements.append(anchor)
            self.logger.debug("アンカー自身を関連要素に追加")
            
            # 2. 兄弟要素を取得
            try:
                parent = anchor.parent()
                if parent:
                    siblings = parent.children()
                    related_elements.extend(siblings)
                    self.logger.debug(f"兄弟要素 {len(siblings)}件を追加")
            except Exception as e:
                self.logger.debug(f"兄弟要素の取得失敗: {e}")
            
            # 3. 親要素の周辺要素も試行
            try:
                parent = anchor.parent()
                if parent:
                    grandparent = parent.parent()
                    if grandparent:
                        parent_siblings = grandparent.children()
                        for sibling in parent_siblings[:5]:  # 最大5個まで
                            try:
                                sibling_children = sibling.children()
                                related_elements.extend(sibling_children[:3])  # 各兄弟の子要素最大3個
                            except:
                                continue
                        self.logger.debug(f"親の兄弟要素周辺から追加")
            except Exception as e:
                self.logger.debug(f"親要素周辺の取得失敗: {e}")
            
        except Exception as e:
            self.logger.debug(f"関連要素取得エラー: {e}")
        
        # 重複除去（ハンドルベース）
        unique_elements = []
        seen_handles = set()
        
        for element in related_elements:
            try:
                handle = getattr(element, 'handle', id(element))
                if handle not in seen_handles:
                    seen_handles.add(handle)
                    unique_elements.append(element)
            except:
                # ハンドル取得に失敗した場合はスキップ
                continue
        
        self.logger.debug(f"関連要素取得完了: {len(unique_elements)}件（重複除去後）")
        return unique_elements
    
    def _calculate_fast_depth(self, element: HwndWrapper, index: int) -> int:
        """
        高速な深度計算（概算）
        
        Args:
            element: 対象要素
            index: 要素のインデックス
        
        Returns:
            int: 推定深度
        """
        # インデックスベースの簡易深度計算
        # 最初の数個は直下の子要素、後の要素はより深い可能性が高い
        if index < 5:
            return 1  # 直下の子要素
        elif index < 20:
            return 2  # 2階層目
        elif index < 50:
            return 3  # 3階層目
        else:
            return 4  # 4階層目以降
    
    def _extract_element_info(self, 
                             element: HwndWrapper, 
                             index: int, 
                             depth: int) -> ElementInfo:
        """
        単一要素から情報を抽出します
        
        Args:
            element: pywinauto要素
            index: インデックス番号
            depth: 深度
        
        Returns:
            ElementInfo: 要素情報
        """
        try:
            # 基本情報の取得（複数のテキスト情報を試行）
            name = self._extract_element_text(element)
            title = name  # titleとnameは通常同じ
            
            # UIA固有の情報
            if self.backend == 'uia':
                auto_id = self._safe_get_property(element, 'automation_id', None)
                control_type = self._safe_get_property(element, 'control_type', None, is_method=True)
            else:
                auto_id = None
                control_type = None
            
            # 共通情報
            class_name = self._safe_get_property(element, 'class_name', None, is_method=True)
            
            # 矩形情報
            rectangle = None
            try:
                rect = element.rectangle()
                if rect:
                    rectangle = [rect.left, rect.top, rect.right, rect.bottom]
            except:
                pass
            
            # 状態情報
            visible = self._safe_get_property(element, 'is_visible', None, is_method=True)
            enabled = self._safe_get_property(element, 'is_enabled', None, is_method=True)
            
            # パス情報の生成
            path = self._generate_element_path(element, depth)
            
            return ElementInfo(
                index=index,
                depth=depth,
                name=name,
                title=title,
                auto_id=auto_id,
                control_type=control_type,
                class_name=class_name,
                rectangle=rectangle,
                visible=visible,
                enabled=enabled,
                path=path
            )
            
        except Exception as e:
            self.logger.debug(f"要素情報抽出エラー: {e}")
            # エラー時はデフォルト情報を返す
            return ElementInfo(
                index=index,
                depth=depth,
                name=f"<取得失敗: {type(e).__name__}>",
            )
    
    def _extract_element_text(self, element: HwndWrapper) -> str:
        """
        要素から識別に役立つテキスト情報を抽出します
        
        Args:
            element: pywinauto要素
            
        Returns:
            str: 抽出されたテキスト（空文字列の場合もあり）
        """
        # 複数のテキスト取得方法を試行
        text_candidates = []
        
        # 1. window_text (最も一般的)
        window_text = self._safe_get_property(element, 'window_text', '', is_method=True)
        if window_text and isinstance(window_text, str) and window_text.strip():
            text_candidates.append(window_text.strip())
        
        # 2. UIA specific properties
        if self.backend == 'uia':
            # name property
            name_prop = self._safe_get_property(element, 'name', '')
            if name_prop and isinstance(name_prop, str) and name_prop.strip():
                text_candidates.append(name_prop.strip())
            
            # value property (for text controls)
            value_prop = self._safe_get_property(element, 'value', '')
            if value_prop and isinstance(value_prop, str) and value_prop.strip():
                text_candidates.append(value_prop.strip())
            
            # help_text property
            help_text = self._safe_get_property(element, 'help_text', '')
            if help_text and isinstance(help_text, str) and help_text.strip():
                text_candidates.append(help_text.strip())
        
        # 3. Additional Win32 properties
        try:
            # texts() method if available
            if hasattr(element, 'texts'):
                texts = element.texts()
                if texts:
                    for text in texts:
                        if text and isinstance(text, str) and text.strip():
                            text_candidates.append(text.strip())
        except:
            pass
        
        # 4. Try to get text from children for container elements
        try:
            if not text_candidates:
                children = element.children()
                for child in children[:3]:  # 最大3個の子要素まで
                    child_text = self._safe_get_property(child, 'window_text', '', is_method=True)
                    if child_text and isinstance(child_text, str) and child_text.strip():
                        text_candidates.append(f"[{child_text.strip()}]")
        except:
            pass
        
        # 最適なテキストを選択
        if text_candidates:
            # 空でない最初のテキストを返す
            for text in text_candidates:
                if text and len(text.strip()) > 0:
                    # 長すぎるテキストは切り詰め
                    if len(text) > 50:
                        return text[:47] + "..."
                    return text
        
        return ""
    
    def _safe_get_property(self, 
                          element: HwndWrapper, 
                          property_name: str, 
                          default: Any = None,
                          is_method: bool = False) -> Any:
        """
        要素のプロパティを安全に取得します
        
        Args:
            element: 要素
            property_name: プロパティ名
            default: デフォルト値
            is_method: メソッド呼び出しかどうか
        
        Returns:
            プロパティ値またはデフォルト値
        """
        try:
            if hasattr(element, property_name):
                prop = getattr(element, property_name)
                if is_method:
                    return prop()
                else:
                    return prop
            return default
        except:
            return default
    
    def _calculate_depth(self, 
                        element: HwndWrapper, 
                        anchor: Union[WindowSpecification, HwndWrapper]) -> int:
        """
        要素の深度を計算します（簡易版）
        
        Args:
            element: 対象要素
            anchor: アンカー要素
        
        Returns:
            int: 深度
        """
        # 簡易的な深度計算（正確ではないが目安として）
        try:
            # 親をたどって深度を計算
            depth = 0
            current = element
            
            # 最大10階層まで（無限ループ防止）
            for _ in range(10):
                try:
                    parent = current.parent()
                    if parent and parent != current:
                        depth += 1
                        current = parent
                    else:
                        break
                except:
                    break
            
            return max(1, depth)  # 最低1
            
        except:
            return 1  # エラー時はデフォルト
    
    def _calculate_relative_depth(self, 
                                 element: HwndWrapper, 
                                 anchor: Union[WindowSpecification, HwndWrapper]) -> int:
        """
        アンカーからの相対深度を計算します
        
        Args:
            element: 対象要素
            anchor: アンカー要素
        
        Returns:
            int: アンカーからの相対深度（1から開始）
        """
        try:
            # アンカーと要素が同じ場合は0
            if element == anchor:
                return 0
            
            # 要素から親をたどってアンカーまでの距離を計算
            depth = 0
            current = element
            
            # 最大20階層まで（無限ループ防止）
            for _ in range(20):
                try:
                    parent = current.parent()
                    if parent is None or parent == current:
                        break
                    
                    depth += 1
                    
                    # アンカーに到達した場合
                    if parent == anchor:
                        return depth
                    
                    # アンカーとハンドルが同じかチェック
                    try:
                        if (hasattr(parent, 'handle') and hasattr(anchor, 'handle') and 
                            parent.handle == anchor.handle):
                            return depth
                    except:
                        pass
                    
                    current = parent
                    
                except Exception as e:
                    self.logger.debug(f"親要素取得エラー: {e}")
                    break
            
            # アンカーに到達できなかった場合は、簡易的な深度を返す
            # 1以上を返す（子要素であることを示す）
            return max(1, min(depth, 10))
            
        except Exception as e:
            self.logger.debug(f"相対深度計算エラー: {e}")
            return 1  # エラー時はデフォルト
    
    def _generate_element_path(self, element: HwndWrapper, depth: int) -> str:
        """
        要素のパス情報を生成します
        
        Args:
            element: 要素
            depth: 深度
        
        Returns:
            str: パス文字列
        """
        try:
            # 簡易的なパス生成
            class_name = self._safe_get_property(element, 'class_name', 'Unknown')
            control_type = self._safe_get_property(element, 'control_type', None)
            
            if control_type:
                return f"{control_type}[{depth}]"
            else:
                return f"{class_name}[{depth}]"
                
        except:
            return f"Element[{depth}]"
    
    def _should_include_element(self, element_info: ElementInfo, only_visible: bool) -> bool:
        """
        要素を出力対象に含めるかを判定します
        
        Args:
            element_info: 要素情報
            only_visible: 可視要素のみフラグ
        
        Returns:
            bool: 含める場合True
        """
        if not only_visible:
            return True
        
        # 可視性と有効性をチェック
        if element_info.visible is False or element_info.enabled is False:
            return False
        
        return True
    
    def _build_filter_description(self, only_visible: bool, max_items: Optional[int]) -> str:
        """
        フィルタ条件の説明文を生成します
        
        Args:
            only_visible: 可視要素のみフラグ
            max_items: 最大件数
        
        Returns:
            str: フィルタ説明
        """
        conditions = []
        
        if only_visible:
            conditions.append("可視要素のみ")
        
        if max_items:
            conditions.append(f"最大{max_items}件")
        
        if conditions:
            return "、".join(conditions)
        else:
            return "全要素"
    
    @log_function_call
    def highlight_elements(self, elements: List[ElementInfo], duration: float = 1.0) -> None:
        """
        要素をハイライト表示します
        
        Args:
            elements: ハイライト対象の要素リスト
            duration: 表示時間（秒）
        """
        try:
            self.logger.info(f"要素ハイライト開始: {len(elements)}件")
            
            if not elements:
                self.logger.warning("ハイライト対象の要素がありません")
                return
            
            # アンカーから実際のpywinauto要素を取得してハイライト
            highlighted_count = 0
            max_highlight = min(10, len(elements))  # 最大10件
            
            for i, element_info in enumerate(elements[:max_highlight]):
                try:
                    # ElementInfoから実際の要素を復元してハイライト
                    if self._highlight_single_element(element_info, i + 1):
                        highlighted_count += 1
                    
                    # 各要素間の遅延
                    if i < max_highlight - 1:
                        time.sleep(duration / max_highlight)
                        
                except Exception as e:
                    self.logger.debug(f"要素 {i+1} のハイライト失敗: {e}")
                    continue
            
            self.logger.info(f"要素ハイライト完了: {highlighted_count}/{max_highlight}件成功")
            
            # 全体の表示時間を確保
            if highlighted_count > 0:
                time.sleep(duration)
            
        except Exception as e:
            self.logger.warning(f"要素ハイライト失敗: {e}")
    
    def _highlight_single_element(self, element_info: ElementInfo, index: int) -> bool:
        """
        単一要素をハイライト表示します
        
        Args:
            element_info: 要素情報
            index: 表示用インデックス
        
        Returns:
            bool: ハイライトに成功した場合True
        """
        try:
            self.logger.debug(f"ハイライト {index}: {element_info.name or '(名前なし)'}")
            
            # 矩形情報があるかチェック
            if not element_info.rectangle:
                self.logger.debug(f"要素 {index}: 矩形情報がないためスキップ")
                return False
            
            # 実際のハイライト実装は環境や権限の問題があるため、
            # ログベースの表示を行う
            rect = element_info.rectangle
            self.logger.info(
                f"ハイライト {index}: "
                f"位置=({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]}) "
                f"名前='{element_info.name or '(名前なし)'}' "
                f"クラス='{element_info.class_name or '(不明)'}'"
            )
            
            # TODO: 実際の視覚的ハイライト
            # この実装は環境によって動作しない可能性があるため、
            # 将来的にオプション化する必要があります
            try:
                self._draw_visual_highlight(element_info)
                return True
            except Exception as e:
                self.logger.debug(f"視覚的ハイライト失敗: {e}")
                return True  # ログは成功しているのでTrueを返す
            
        except Exception as e:
            self.logger.debug(f"要素 {index} ハイライト処理エラー: {e}")
            return False
    
    def _draw_visual_highlight(self, element_info: ElementInfo) -> None:
        """
        要素の視覚的ハイライトを描画します（実験的）
        
        Args:
            element_info: 要素情報
        
        Note:
            この機能は環境や権限によって動作しない場合があります
        """
        try:
            # pywinautoでの視覚的ハイライトは複雑で、
            # 実際の要素オブジェクトが必要なため、
            # ここでは概念的な実装のみ行います
            
            # 実装アイディア:
            # 1. 要素の矩形に基づいてオーバーレイウィンドウを作成
            # 2. Win32 APIを使用して矩形を描画
            # 3. tkinterやPyQt等でハイライト用ウィンドウを作成
            
            # 現在は安全性のため、ログベースのハイライトのみ
            pass
            
        except Exception as e:
            self.logger.debug(f"視覚的ハイライト描画エラー: {e}")
            raise


def create_element_finder(backend: str = 'win32') -> ElementFinder:
    """
    ElementFinderインスタンスを作成します（便利関数）
    
    Args:
        backend: 使用するバックエンド
    
    Returns:
        ElementFinderインスタンス
    """
    return ElementFinder(backend)
