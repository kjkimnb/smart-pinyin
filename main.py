#!/usr/bin/env python3
"""
中文输入法 - 命令行版
主入口文件
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import InputMethodCLI

def main():
    """主函数"""
    cli = InputMethodCLI()
    cli.run()

if __name__ == "__main__":
    main()
