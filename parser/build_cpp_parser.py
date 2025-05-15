#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
为C++语言构建tree-sitter解析器
"""
import os
import sys
import platform
from tree_sitter import Language

def main():
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查是否已存在tree-sitter-cpp目录
    cpp_dir = os.path.join(current_dir, "tree-sitter-cpp")
    if not os.path.exists(cpp_dir):
        print(f"错误: 未找到tree-sitter-cpp目录，请先运行setup_parser.py")
        return False
    
    # 根据操作系统选择输出文件名
    if platform.system() == 'Windows':
        output_file = os.path.join(current_dir, "cpp-parser.dll")
    else:
        output_file = os.path.join(current_dir, "cpp-parser.so")
    
    # 构建C++解析器
    print(f"构建C++解析器到: {output_file}")
    try:
        Language.build_library(
            # 输出文件名
            output_file,
            # 仅包含C++
            [cpp_dir]
        )
        print("C++解析器构建成功！")
        return True
    except Exception as e:
        print(f"构建C++解析器失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 