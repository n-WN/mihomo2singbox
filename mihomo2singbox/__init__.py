#!/usr/bin/env python3
"""
Mihomo (ClashMeta) 到 Sing-box 配置转换工具

这个包提供了将 Mihomo (ClashMeta) 配置文件转换为 Sing-box 配置文件的功能。
"""

from .main import MihomoToSingboxConverter, main

__version__ = "0.1.0"
__author__ = "n-WN"
# __email__ = "your-email@example.com"
__description__ = "Mihomo (ClashMeta) 配置转换为 Sing-box 配置的转换工具"

__all__ = ["MihomoToSingboxConverter", "main"]
