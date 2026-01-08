"""
ElementFinder カーソル位置処理機能

マウスカーソル位置の要素取得と、アンカー昇格処理を提供します。
"""

import time
from typing import Any, Optional, Union, Dict
import psutil

try:
    import win32gui
    import win32process
    _WIN32GUI_AVAILABLE = True
except ImportError:
    _WIN32GUI_AVAILABLE = False

from pywinauto import Desktop
from pywinauto.application import WindowSpecification
from pywinauto.controls.hwndwrapper import HwndWrapper

from ..utils.exceptions import (
    CursorError, PywinautoError, handle_pywinauto_exception
)
from ..utils.logging import get_logger, log_function_call


class CursorHandler:
    """
    カーソル位置の要素取得とアンカー昇格を担当するクラス
    """
    
    def __init__(self, backend: str = 'uia'):
        """
        Args:
            backend: 使用するバックエンド ('win32' または 'uia')
        """
        self.backend = backend
        self.logger = get_logger()
        
        # win32guiの利用可能性をチェック
        if not _WIN32GUI_AVAILABLE:
            self.logger.warning("win32guiが利用できません。カーソル機能が制限される可能性があります。")
    
    @log_function_call
    @handle_pywinauto_exception
    def get_cursor_element(self, 
                          delay: float = 0.0,
                          target_window: Optional[WindowSpecification] = None) -> Any:
        """
        マウスカーソル位置の要素を取得します
        
        Args:
            delay: カーソル位置取得前の遅延時間（秒）
            target_window: 対象ウィンドウ（アンカー昇格用）
        
        Returns:
            カーソル下の要素、またはアンカー昇格された要素
        
        Raises:
            CursorError: カーソル位置の要素取得に失敗した場合
            PywinautoError: pywinauto操作エラー
        """
        try:
            # 遅延処理
            if delay > 0:
                self.logger.info(f"カーソル位置取得まで{delay}秒待機...")
                time.sleep(delay)
            
            # カーソル位置の取得
            cursor_pos = self._get_cursor_position()
            self.logger.debug(f"カーソル位置: ({cursor_pos[0]}, {cursor_pos[1]})")
            
            # Desktop.from_pointを使用して要素を取得
            element = self._get_element_at_point(cursor_pos)
            
            # アンカー昇格処理
            if target_window:
                element = self._promote_to_window_anchor(element, target_window)
            
            # 要素の情報をログ出力
            self._log_element_info(element, cursor_pos)
            
            return element
            
        except CursorError:
            raise
        except Exception as e:
            self.logger.error(f"カーソル要素取得失敗: {e}")
            raise CursorError(f"カーソル位置の要素取得に失敗しました: {e}")
    
    def _get_cursor_position(self) -> tuple[int, int]:
        """
        現在のカーソル位置を取得します
        
        Returns:
            tuple[int, int]: (x, y) 座標
        
        Raises:
            CursorError: カーソル位置の取得に失敗した場合
        """
        try:
            if _WIN32GUI_AVAILABLE:
                # win32guiを使用（推奨）
                pos = win32gui.GetCursorPos()
                return pos
            else:
                # フォールバック: pywinautoのDesktopを使用
                # 注意: この方法は制限があります
                self.logger.warning("win32guiが利用できないため、フォールバック方法を使用します")
                raise CursorError("win32guiが利用できません。カーソル位置の正確な取得ができません。")
                
        except Exception as e:
            raise CursorError(f"カーソル位置の取得に失敗しました: {e}")
    
    def _get_element_at_point(self, point: tuple[int, int]) -> Any:
        """
        指定した座標の要素を取得します
        
        Args:
            point: (x, y) 座標
        
        Returns:
            座標上の要素
        
        Raises:
            CursorError: 要素の取得に失敗した場合
        """
        try:
            # Desktopインスタンスを作成
            desktop = Desktop(backend=self.backend)
            
            # from_pointで要素を取得
            element = desktop.from_point(point[0], point[1])
            
            if not element:
                raise CursorError(f"座標 ({point[0]}, {point[1]}) に要素が見つかりません")
            
            self.logger.debug(f"座標上の要素を取得: {type(element).__name__}")
            return element
            
        except Exception as e:
            raise CursorError(f"座標 ({point[0]}, {point[1]}) の要素取得に失敗: {e}")
    
    def _promote_to_window_anchor(self, 
                                 element: Any, 
                                 target_window: WindowSpecification) -> Any:
        """
        要素を指定ウィンドウ配下のアンカーに昇格させます
        
        Args:
            element: カーソル下の要素
            target_window: 対象ウィンドウ
        
        Returns:
            昇格されたアンカー要素
        """
        try:
            # 要素が既に対象ウィンドウ配下にあるかチェック
            if self._is_element_in_window(element, target_window):
                self.logger.debug("要素は既に対象ウィンドウ配下にあります")
                return element
            
            # ウィンドウ配下で最も近い要素を検索
            promoted_element = self._find_nearest_element_in_window(element, target_window)
            
            if promoted_element:
                self.logger.info("アンカー昇格に成功しました")
                return promoted_element
            else:
                self.logger.warning("アンカー昇格に失敗。元の要素を使用します")
                return element
                
        except Exception as e:
            self.logger.warning(f"アンカー昇格処理でエラー: {e}。元の要素を使用します")
            return element
    
    def _is_element_in_window(self, element: Any, window: WindowSpecification) -> bool:
        """
        要素が指定ウィンドウ配下にあるかチェックします
        
        Args:
            element: チェック対象の要素
            window: 対象ウィンドウ
        
        Returns:
            bool: ウィンドウ配下にある場合True
        """
        try:
            # 要素の親をたどってウィンドウを探す
            current = element
            for _ in range(20):  # 最大20階層まで
                try:
                    parent = current.parent()
                    if parent and hasattr(parent, 'handle') and hasattr(window, 'handle'):
                        # ハンドルが同じかチェック
                        if parent.handle == window.handle:
                            return True
                    current = parent
                except:
                    break
            return False
        except:
            return False
    
    def _find_nearest_element_in_window(self, 
                                       cursor_element: Any, 
                                       window: WindowSpecification) -> Optional[Any]:
        """
        ウィンドウ配下でカーソル要素に最も近い要素を見つけます
        
        Args:
            cursor_element: カーソル下の要素
            window: 対象ウィンドウ
        
        Returns:
            Optional[Any]: 見つかった要素、またはNone
        """
        try:
            # カーソル要素の矩形を取得
            cursor_rect = self._safe_get_rectangle(cursor_element)
            if not cursor_rect:
                return None
            
            # ウィンドウの子要素を取得
            children = window.descendants()
            best_element = None
            min_distance = float('inf')
            
            for child in children:
                try:
                    child_rect = self._safe_get_rectangle(child)
                    if not child_rect:
                        continue
                    
                    # 距離を計算（矩形の中心点間の距離）
                    distance = self._calculate_rect_distance(cursor_rect, child_rect)
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_element = child
                        
                except:
                    continue
            
            if best_element:
                self.logger.debug(f"最近接要素を発見（距離: {min_distance:.1f}）")
            
            return best_element
            
        except Exception as e:
            self.logger.debug(f"最近接要素検索でエラー: {e}")
            return None
    
    def _safe_get_rectangle(self, element: Any) -> Optional[tuple[int, int, int, int]]:
        """
        要素の矩形を安全に取得します
        
        Args:
            element: 対象要素
        
        Returns:
            Optional[tuple]: (left, top, right, bottom) または None
        """
        try:
            rect = element.rectangle()
            if rect:
                return (rect.left, rect.top, rect.right, rect.bottom)
        except:
            pass
        return None
    
    def _calculate_rect_distance(self, 
                                rect1: tuple[int, int, int, int], 
                                rect2: tuple[int, int, int, int]) -> float:
        """
        2つの矩形の中心点間の距離を計算します
        
        Args:
            rect1: 矩形1 (left, top, right, bottom)
            rect2: 矩形2 (left, top, right, bottom)
        
        Returns:
            float: 距離
        """
        try:
            # 矩形の中心点を計算
            center1_x = (rect1[0] + rect1[2]) / 2
            center1_y = (rect1[1] + rect1[3]) / 2
            center2_x = (rect2[0] + rect2[2]) / 2
            center2_y = (rect2[1] + rect2[3]) / 2
            
            # ユークリッド距離を計算
            distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5
            return distance
        except:
            return float('inf')
    
    def _log_element_info(self, element: Any, cursor_pos: tuple[int, int]) -> None:
        """
        取得した要素の情報をログ出力します
        
        Args:
            element: 要素
            cursor_pos: カーソル位置
        """
        try:
            # 基本情報
            element_type = type(element).__name__
            self.logger.info(f"カーソル要素取得成功: {element_type}")
            
            # 要素の詳細情報（可能な範囲で）
            try:
                window_text = element.window_text() if hasattr(element, 'window_text') else ""
                if window_text:
                    self.logger.debug(f"要素テキスト: '{window_text}'")
            except:
                pass
            
            try:
                class_name = element.class_name() if hasattr(element, 'class_name') else ""
                if class_name:
                    self.logger.debug(f"クラス名: '{class_name}'")
            except:
                pass
            
            # 矩形情報
            rect = self._safe_get_rectangle(element)
            if rect:
                self.logger.debug(f"要素矩形: ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
            
        except Exception as e:
            self.logger.debug(f"要素情報ログ出力でエラー: {e}")

    def get_parent_element(self, element: Any) -> Optional[Any]:
        """
        要素の親要素を取得します
        
        Args:
            element: 対象要素
        
        Returns:
            Optional[Any]: 親要素、またはNone（親が存在しない場合）
        
        Raises:
            CursorError: 親要素の取得に失敗した場合
        """
        try:
            self.logger.debug("親要素の取得を開始")
            
            # 親要素を取得
            parent = element.parent()
            
            # 親要素の妥当性チェック
            if parent is None:
                self.logger.info("親要素が存在しません（トップレベル要素）")
                return None
            
            if parent == element:
                self.logger.info("親要素が自分自身です（循環参照）")
                return None
            
            # 親要素の情報をログ出力
            self._log_parent_info(parent)
            
            return parent
            
        except Exception as e:
            self.logger.error(f"親要素取得でエラー: {e}")
            raise CursorError(f"親要素の取得に失敗しました: {e}")
    
    def _log_parent_info(self, parent: Any) -> None:
        """
        親要素の情報をログ出力します
        
        Args:
            parent: 親要素
        """
        try:
            # 基本情報
            parent_type = type(parent).__name__
            self.logger.info(f"親要素取得成功: {parent_type}")
            
            # 親要素の詳細情報（可能な範囲で）
            try:
                window_text = parent.window_text() if hasattr(parent, 'window_text') else ""
                if window_text:
                    self.logger.debug(f"親要素テキスト: '{window_text}'")
            except:
                pass
            
            try:
                class_name = parent.class_name() if hasattr(parent, 'class_name') else ""
                if class_name:
                    self.logger.debug(f"親要素クラス名: '{class_name}'")
            except:
                pass
            
            # 矩形情報
            rect = self._safe_get_rectangle(parent)
            if rect:
                self.logger.debug(f"親要素矩形: ({rect[0]}, {rect[1]}, {rect[2]}, {rect[3]})")
            
        except Exception as e:
            self.logger.debug(f"親要素情報ログ出力でエラー: {e}")
    
    def get_element_detailed_info(self, element: Any, cursor_pos: tuple[int, int]) -> Dict[str, Any]:
        """
        要素の詳細情報を取得します（uiaとwin32の両方）
        
        Args:
            element: 対象要素
            cursor_pos: カーソル位置 (x, y)
        
        Returns:
            Dict[str, Any]: 詳細情報の辞書
        """
        info = {
            'cursor_position': cursor_pos,
            'uia': {},
            'win32': {}
        }
        
        # UIAバックエンドで情報を取得
        try:
            uia_info = self._get_uia_element_info(element)
            info['uia'] = uia_info
        except Exception as e:
            self.logger.debug(f"UIA情報取得エラー: {e}")
            info['uia'] = {'error': str(e)}
        
        # Win32バックエンドで情報を取得
        try:
            win32_info = self._get_win32_element_info(element, cursor_pos)
            info['win32'] = win32_info
        except Exception as e:
            self.logger.debug(f"Win32情報取得エラー: {e}")
            info['win32'] = {'error': str(e)}
        
        return info
    
    def _get_uia_element_info(self, element: Any) -> Dict[str, Any]:
        """
        UIAバックエンドで要素情報を取得します
        
        Args:
            element: 対象要素
        
        Returns:
            Dict[str, Any]: UIA要素情報
        """
        info = {}
        
        try:
            # window_text / name
            if hasattr(element, 'window_text'):
                try:
                    info['window_text'] = element.window_text()
                except:
                    info['window_text'] = None
            
            if hasattr(element, 'name'):
                try:
                    info['name'] = element.name
                except:
                    try:
                        info['name'] = element.name()
                    except:
                        info['name'] = None
            
            # control_type
            if hasattr(element, 'control_type'):
                try:
                    val = element.control_type
                    if callable(val):
                        info['control_type'] = val()
                    else:
                        info['control_type'] = val
                except:
                    info['control_type'] = None
            
            # フォールバック: element_infoから取得
            if (not info.get('control_type') and 
                hasattr(element, 'element_info') and 
                hasattr(element.element_info, 'control_type')):
                try:
                    info['control_type'] = element.element_info.control_type
                except:
                    pass
            
            # automation_id
            if hasattr(element, 'automation_id'):
                try:
                    info['automation_id'] = element.automation_id()
                except:
                    info['automation_id'] = None
            
            # class_name
            if hasattr(element, 'class_name'):
                try:
                    info['class_name'] = element.class_name()
                except:
                    info['class_name'] = None
            
            # friendly_class_name
            if hasattr(element, 'friendly_class_name'):
                try:
                    info['friendly_class_name'] = element.friendly_class_name()
                except:
                    info['friendly_class_name'] = None
            
            # children_count
            try:
                children = element.children()
                info['children_count'] = len(children) if children else 0
            except:
                try:
                    children = list(element.descendants())
                    info['children_count'] = len(children) if children else 0
                except:
                    info['children_count'] = None
            
            # depth (階層の深さ)
            info['depth'] = self._calculate_element_depth(element)
            
            # rectangle
            rect = self._safe_get_rectangle(element)
            if rect:
                info['rectangle'] = {
                    'left': rect[0],
                    'top': rect[1],
                    'right': rect[2],
                    'bottom': rect[3],
                    'width': rect[2] - rect[0],
                    'height': rect[3] - rect[1]
                }
            else:
                info['rectangle'] = None
            
            # is_visible
            if hasattr(element, 'is_visible'):
                try:
                    info['is_visible'] = element.is_visible()
                except:
                    info['is_visible'] = None
            
            # ハンドル
            if hasattr(element, 'handle'):
                try:
                    info['handle'] = element.handle
                except:
                    info['handle'] = None
            
            # process名
            info['process_name'] = self._get_process_name_from_element(element)
            
        except Exception as e:
            self.logger.debug(f"UIA要素情報取得エラー: {e}")
            info['error'] = str(e)
        
        return info
    
    def _get_win32_element_info(self, element: Any, cursor_pos: tuple[int, int]) -> Dict[str, Any]:
        """
        Win32バックエンドで要素情報を取得します
        
        Args:
            element: 対象要素（UIAバックエンドの要素）
            cursor_pos: カーソル位置
        
        Returns:
            Dict[str, Any]: Win32要素情報
        """
        info = {}
        
        try:
            # Win32バックエンドで同じ位置の要素を取得
            desktop_win32 = Desktop(backend='win32')
            win32_element = desktop_win32.from_point(cursor_pos[0], cursor_pos[1])
            
            if not win32_element:
                info['error'] = 'Win32要素が見つかりません'
                return info
            
            # window_text / name
            if hasattr(win32_element, 'window_text'):
                try:
                    info['window_text'] = win32_element.window_text()
                except:
                    info['window_text'] = None
            
            # control_type (Win32では通常利用不可)
            info['control_type'] = None
            
            # automation_id (Win32では通常利用不可)
            info['automation_id'] = None
            
            # class_name
            if hasattr(win32_element, 'class_name'):
                try:
                    info['class_name'] = win32_element.class_name()
                except:
                    info['class_name'] = None
            
            # friendly_class_name (Win32では通常利用不可)
            info['friendly_class_name'] = None
            
            # children_count
            try:
                children = win32_element.children()
                info['children_count'] = len(children) if children else 0
            except:
                info['children_count'] = None
            
            # depth (階層の深さ)
            info['depth'] = self._calculate_element_depth(win32_element)
            
            # rectangle
            try:
                rect = win32_element.rectangle()
                if rect:
                    info['rectangle'] = {
                        'left': rect.left,
                        'top': rect.top,
                        'right': rect.right,
                        'bottom': rect.bottom,
                        'width': rect.width(),
                        'height': rect.height()
                    }
                else:
                    info['rectangle'] = None
            except:
                info['rectangle'] = None
            
            # is_visible
            if hasattr(win32_element, 'is_visible'):
                try:
                    info['is_visible'] = win32_element.is_visible()
                except:
                    info['is_visible'] = None
            
            # ハンドル
            if hasattr(win32_element, 'handle'):
                try:
                    info['handle'] = win32_element.handle
                except:
                    info['handle'] = None
            
            # process名
            info['process_name'] = self._get_process_name_from_element(win32_element)
            
        except Exception as e:
            self.logger.debug(f"Win32要素情報取得エラー: {e}")
            info['error'] = str(e)
        
        return info
    
    def _calculate_element_depth(self, element: Any) -> Optional[int]:
        """
        要素の階層の深さを計算します（ルートから）
        
        Args:
            element: 対象要素
        
        Returns:
            Optional[int]: 深度、計算できない場合はNone
        """
        try:
            depth = 0
            current = element
            
            # 最大20階層まで（無限ループ防止）
            for _ in range(20):
                try:
                    parent = current.parent()
                    if parent is None or parent == current:
                        break
                    depth += 1
                    current = parent
                except:
                    break
            
            return depth
        except:
            return None
    
    def _get_process_name_from_element(self, element: Any) -> Optional[str]:
        """
        要素からプロセス名を取得します
        
        Args:
            element: 対象要素
        
        Returns:
            Optional[str]: プロセス名、取得できない場合はNone
        """
        try:
            # ハンドルからプロセスIDを取得
            if hasattr(element, 'handle'):
                handle = element.handle
                
                if _WIN32GUI_AVAILABLE:
                    try:
                        _, pid = win32process.GetWindowThreadProcessId(handle)
                        process = psutil.Process(pid)
                        return process.name()
                    except:
                        pass
            
            # process_idメソッドを試行
            if hasattr(element, 'process_id'):
                try:
                    pid = element.process_id()
                    process = psutil.Process(pid)
                    return process.name()
                except:
                    pass
            
            return None
        except:
            return None


def create_cursor_handler(backend: str = 'win32') -> CursorHandler:
    """
    CursorHandlerインスタンスを作成します（便利関数）
    
    Args:
        backend: 使用するバックエンド
    
    Returns:
        CursorHandlerインスタンス
    """
    return CursorHandler(backend)
