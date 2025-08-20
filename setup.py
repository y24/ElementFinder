#!/usr/bin/env python3
"""
ElementFinder - GUIアプリケーションの要素特定を効率化するCLIツール
"""

from setuptools import setup, find_packages
import os

# README.mdの読み込み
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "GUIアプリケーションの要素特定を効率化するCLIツール"

setup(
    name="elementfinder",
    version="0.1.0",
    description="GUIアプリケーションの要素特定を効率化するCLIツール",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="ElementFinder Development Team",
    author_email="dev@elementfinder.local",
    url="https://github.com/your-org/elementfinder",
    license="MIT",
    
    # パッケージ設定
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    # Python要件
    python_requires=">=3.9",
    
    # 依存関係
    install_requires=[
        "pywinauto>=0.6.8",
        "comtypes>=1.1.14",
    ],
    

    
    # エントリーポイント
    entry_points={
        "console_scripts": [
            "elementfinder=elementfinder.main:main",
        ],
    },
    
    # 分類
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    
    # キーワード
    keywords="gui automation windows pywinauto cli element finder",
    
    # プロジェクトURL
    project_urls={
        "Bug Reports": "https://github.com/your-org/elementfinder/issues",
        "Source": "https://github.com/your-org/elementfinder",
        "Documentation": "https://github.com/your-org/elementfinder/wiki",
    },
    
    # ファイルの含有設定
    include_package_data=True,
    zip_safe=False,
)
