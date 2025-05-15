# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.

from tree_sitter import Language, Parser
import platform

# 根据操作系统确定输出文件扩展名
if platform.system() == 'Windows':
    lib_name = 'cpp-parser.dll'
else:
    lib_name = 'cpp-parser.so'

Language.build_library(
  # 存储生成的解析器库文件
  lib_name,

  # 只包含 C++ 语言解析器
  [
    'tree-sitter-cpp'
  ]
)

