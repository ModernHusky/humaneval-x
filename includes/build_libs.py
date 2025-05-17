import os
import subprocess
import platform
import glob
from pathlib import Path

def compile_library(cpp_file, output_dir):
    """编译单个库文件"""
    # 获取文件名（不含扩展名）
    file_name = os.path.splitext(os.path.basename(cpp_file))[0]
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 根据操作系统确定输出文件扩展名
    if platform.system() == 'Windows':
        output_ext = '.lib'
    else:
        output_ext = '.a'
    
    # 构建输出文件路径
    output_file = os.path.join(output_dir, f'lib{file_name}{output_ext}')
    
    # 构建编译命令
    compile_cmd = [
        'g++',
        '-c',  # 只编译不链接
        cpp_file,
        '-o', output_file
    ]
    
    print(f"编译 {cpp_file} -> {output_file}")
    
    try:
        # 执行编译命令
        result = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"成功编译 {file_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"编译 {file_name} 失败:")
        print(f"错误信息: {e.stderr}")
        return False

def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 设置源文件目录和输出目录
    source_dir = script_dir
    output_dir = os.path.join(script_dir, 'libs')
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 查找所有.cpp文件
    cpp_files = glob.glob(os.path.join(source_dir, '*.cpp'))
    
    if not cpp_files:
        print("未找到任何.cpp文件")
        return
    
    print(f"找到 {len(cpp_files)} 个源文件:")
    for cpp_file in cpp_files:
        print(f"- {os.path.basename(cpp_file)}")
    
    # 编译所有找到的源文件
    success_count = 0
    for cpp_file in cpp_files:
        if compile_library(cpp_file, output_dir):
            success_count += 1
    
    print(f"\n编译完成: {success_count}/{len(cpp_files)} 个文件成功编译")

if __name__ == '__main__':
    main() 