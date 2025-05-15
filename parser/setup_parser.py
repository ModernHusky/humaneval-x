#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Windows 平台下，仅为 C++ 设置 tree-sitter 解析器的脚本
"""
import os
import sys
import subprocess


def run_command(cmd, cwd=None):
    """执行命令并返回是否成功"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    return result.returncode == 0


def setup_cpp_parser():
    """克隆并构建 tree-sitter-cpp 解析器"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_name = "tree-sitter-cpp"
    repo_url = f"https://github.com/tree-sitter/{repo_name}.git"
    repo_dir = os.path.join(base_dir, repo_name)

    # 克隆仓库
    if not os.path.exists(repo_dir):
        print(f"克隆 {repo_name} 仓库...")
        if not run_command(f"git clone {repo_url}", cwd=base_dir):
            sys.exit(1)
    else:
        print(f"{repo_name} 已存在，跳过克隆")

    # 构建解析器
    print(f"构建 {repo_name} 解析器...")
    # Windows 平台使用 npm
    if not os.path.exists(os.path.join(repo_dir, "node_modules")):
        if not run_command("npm install", cwd=repo_dir):
            sys.exit(1)
    if not run_command("npm run build", cwd=repo_dir):
        sys.exit(1)


def main():

    print("开始设置 C++ 语言解析器...")
    setup_cpp_parser()
    print("✅ C++ Tree-sitter 解析器设置完成！")


if __name__ == '__main__':
    main()
