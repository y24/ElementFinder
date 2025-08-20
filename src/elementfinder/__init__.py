"""
ElementFinder - GUIアプリケーションの要素特定を効率化するCLIツール

このパッケージは、WindowsのGUIアプリケーションの要素を効率的に特定し、
pywinautoでの自動化を支援するためのCLIツールを提供します。
"""

__version__ = "0.1.0"
__author__ = "ElementFinder Development Team"
__email__ = "dev@elementfinder.local"
__license__ = "MIT"

# パッケージレベルで使用する主要な例外をエクスポート
from .utils.exceptions import (
    ElementFinderError,
    WindowNotFoundError,
    AnchorNotFoundError,
    CursorError,
    NoElementsFoundError,
    InvalidArgumentError,
)

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__license__",
    "ElementFinderError",
    "WindowNotFoundError",
    "AnchorNotFoundError", 
    "CursorError",
    "NoElementsFoundError",
    "InvalidArgumentError",
]
