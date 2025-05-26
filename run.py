#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 开关机动画制作工具
"""

import sys
import os
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    missing_deps = []
    
    try:
        import PyQt5
    except ImportError:
        missing_deps.append('PyQt5')
    
    try:
        import PIL
    except ImportError:
        missing_deps.append('Pillow')
    
    if missing_deps:
        print("❌ 缺少以下依赖:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        print("\n或者手动安装:")
        print("pip install PyQt5 Pillow")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 启动开关机动画制作工具...") # Removed "Android"
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 导入主程序
    try:
        from main import main as run_main
        print("✅ 依赖检查通过，启动程序...")
        run_main()
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
