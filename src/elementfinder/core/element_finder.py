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
            
            # 要素を段階的に取得
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
            # descendants()を使用して子孫要素を取得
            if depth is None:
                # 無制限の場合
                descendants = anchor.descendants()
            else:
                # 深度制限
                descendants = anchor.descendants(depth=depth)
            
            # プログレス表示の準備（多数の要素が想定される場合）
            progress = None
            element_count = 0
            yielded_count = 0
            
            for element in descendants:
                element_count += 1
                
                # プログレス表示（1000件を超える場合）
                if element_count == 1000 and not progress:
                    progress = ProgressLogger("要素取得", 10000)  # 概算
                
                if progress and element_count % 100 == 0:
                    progress.update(100)
                
                try:
                    # 要素情報の取得
                    element_info = self._extract_element_info(
                        element, yielded_count, self._calculate_depth(element, anchor)
                    )
                    
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
            
            self.logger.debug(f"要素列挙完了: 総数={element_count}, 出力={yielded_count}")
            
        except Exception as e:
            self.logger.error(f"要素列挙エラー: {e}")
            raise
    
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
            # 基本情報の取得
            name = self._safe_get_property(element, 'window_text', '', is_method=True)
            title = name  # titleとnameは通常同じ
            
            # UIA固有の情報
            if self.backend == 'uia':
                auto_id = self._safe_get_property(element, 'automation_id', None)
                control_type = self._safe_get_property(element, 'control_type', None)
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
            
            # 実装は将来的にpywinautoのdraw_outline等を使用
            # 現在は概念的な実装
            for i, element_info in enumerate(elements[:10]):  # 最大10件
                self.logger.debug(f"ハイライト {i+1}: {element_info.name}")
                
                # TODO: 実際のハイライト処理
                # element.draw_outline(colour='red', thickness=2)
                
                if i < len(elements) - 1:
                    time.sleep(duration / len(elements))
            
            self.logger.info("要素ハイライト完了")
            
        except Exception as e:
            self.logger.warning(f"要素ハイライト失敗: {e}")


def create_element_finder(backend: str = 'win32') -> ElementFinder:
    """
    ElementFinderインスタンスを作成します（便利関数）
    
    Args:
        backend: 使用するバックエンド
    
    Returns:
        ElementFinderインスタンス
    """
    return ElementFinder(backend)
