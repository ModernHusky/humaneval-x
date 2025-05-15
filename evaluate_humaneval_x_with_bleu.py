import os
import sys
import json
import gzip
import numpy as np
import platform
import subprocess
import re
from typing import *
from tqdm.auto import tqdm
from collections import Counter, defaultdict

# 导入 calc_code_bleu
from calc_code_bleu import calc_code_bleu

from utils_eval import read_dataset, IMPORT_HELPER
from metric import estimate_pass_at_k
from execution import check_correctness

# 配置参数
CONFIG = {
    "refs_file": "./private_data/reference_codes.jsonl",  # 参考代码文件
    "hyp_file": "./private_data/request_to_code.jsonl",   # 生成代码文件
    "lang": "cpp",                                # 语言
    "tmp_dir": "./cpp",                           # 临时目录
    "out_dir": "./results",                       # 输出目录
    "timeout": 10.0,                              # 单次测试超时（秒）
    "k": [1, 10, 100],                            # pass@k 的 k 值
    "example_test": False,                        # 是否使用示例测试用例
    "debug": True,                               # 调试模式
}

LANGUAGE_NAME = {"cpp": "CPP"}

def extract_code_from_tags(text):
    """从<代码></代码>标签中提取代码"""
    match = re.search(r'<代码>(.*?)</代码>', text, re.DOTALL)
    if match:
        return match.group(1)
    return ""

def load_new_data_format():
    """
    加载新格式的数据
    
    Returns:
        tuple: (problems, sample_jsonl) 问题集和生成的代码样本
    """
    # 加载参考代码
    refs_file = CONFIG["refs_file"]
    hyp_file = CONFIG["hyp_file"]
    
    problems = {}
    with open(refs_file, 'r', encoding='utf-8') as f:
        for line in f:
            if any(not x.isspace() for x in line):
                try:
                    data = json.loads(line)
                    key = data.get("key")
                    template = data.get("template-1", "")
                    code = extract_code_from_tags(template)
                    
                    # 从模板中提取需求部分作为提示
                    prompt_match = re.search(r'<需求>(.*?)</需求>', template, re.DOTALL)
                    prompt = prompt_match.group(1) if prompt_match else ""
                    
                    # 构造类似 humaneval 的问题格式
                    problems[key] = {
                        "task_id": key,
                        "prompt": prompt,
                        "canonical_solution": code
                    }
                except json.JSONDecodeError as e:
                    print(f"JSON 解析错误: {e}, 行: {line}")
    
    # 加载生成的代码
    sample_jsonl = []
    with open(hyp_file, 'r', encoding='utf-8') as f:
        for line in f:
            if any(not x.isspace() for x in line):
                try:
                    data = json.loads(line)
                    conversations = data.get("conversations", [])
                    
                    # 获取人类询问和GPT回答
                    human_msg = next((msg for msg in conversations if msg.get("from") == "human"), None)
                    gpt_msg = next((msg for msg in conversations if msg.get("from") == "gpt"), None)
                    
                    if human_msg and gpt_msg:
                        key = human_msg.get("key", "")
                        if key in problems:
                            sample_jsonl.append({
                                "task_id": key,
                                "generation": gpt_msg.get("value", ""),
                                "prompt": problems[key]["prompt"],
                                "canonical_solution": problems[key]["canonical_solution"]
                            })
                except json.JSONDecodeError as e:
                    print(f"JSON 解析错误: {e}, 行: {line}")
                    
    return problems, sample_jsonl

def stream_jsonl_all(filename: str) -> Iterable[Dict]:
    """读取 JSONL 文件（支持 gzip）。"""
    results = []
    opener = gzip.open if filename.endswith(".gz") else open
    with opener(filename, "rt") as fp:
        for line in fp:
            if any(not x.isspace() for x in line):
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError as e:
                    print(f"JSON 解析错误: {e}, 行: {line}")
    return results

def evaluate_code_bleu():
    """评估生成的 C++ 代码，计算 CodeBLEU 分数"""
    # 设置工作目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 加载配置
    refs_file = CONFIG["refs_file"]
    hyp_file = CONFIG["hyp_file"]
    lang = CONFIG["lang"]
    out_dir = CONFIG["out_dir"]
    debug = CONFIG["debug"]

    print(f"系统平台: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print(f"配置参数: {CONFIG}")

    # 验证文件存在
    if not os.path.exists(refs_file):
        raise FileNotFoundError(f"参考文件未找到: {refs_file}")
    if not os.path.exists(hyp_file):
        raise FileNotFoundError(f"生成代码文件未找到: {hyp_file}")

    # 加载新格式的数据
    try:
        problems, sample_jsonl = load_new_data_format()
        print(f"成功加载问题集: {len(problems)} 个问题")
        print(f"成功加载生成代码: {len(sample_jsonl)} 个样本")
    except Exception as e:
        raise RuntimeError(f"加载数据失败: {e}")

    # 验证输入数据
    valid_samples = []
    for i, sample in enumerate(sample_jsonl):
        required_fields = ["task_id", "generation", "prompt", "canonical_solution"]
        if not all(k in sample for k in required_fields):
            print(f"无效样本 (行 {i+1}): 缺少字段 {set(required_fields) - set(sample.keys())}")
            continue
        if sample["task_id"] not in problems:
            print(f"跳过样本 (行 {i+1}): 任务 {sample['task_id']} 不在问题集中")
            continue
        valid_samples.append(sample)

    print(f"有效样本数量: {len(valid_samples)}")

    # 构造输出文件
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, os.path.basename(hyp_file).replace(".jsonl", "_codebleu_results.jsonl"))

    # 收集 CodeBLEU 数据
    codebleu_results = []
    for sample in tqdm(valid_samples, desc="处理样本"):
        codebleu_results.append({
            "task_id": sample["task_id"],
            "generated": sample["generation"],
            "reference": sample["canonical_solution"]
        })

    # 计算 CodeBLEU
    if codebleu_results:
        generated_codes = [r["generated"] for r in codebleu_results]
        reference_codes_list = [[r["reference"]] for r in codebleu_results]
        print(f"生成代码数量: {len(generated_codes)}, 参考代码数量: {len(reference_codes_list)}")
        
        if generated_codes and len(generated_codes) == len(reference_codes_list):
            try:
                print("开始计算 CodeBLEU...")
                
                # 确保C++解析器已构建
                parser_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parser")
                cpp_parser_file = os.path.join(parser_dir, "cpp-parser.dll" if platform.system() == 'Windows' else "cpp-parser.so")
                
                if not os.path.exists(cpp_parser_file):
                    print("C++解析器不存在，尝试构建...")
                    
                    # 运行build_cpp_parser.py构建解析器
                    build_cpp_script = os.path.join(parser_dir, "build_cpp_parser.py")
                    if os.path.exists(build_cpp_script):
                        try:
                            print("运行build_cpp_parser.py...")
                            subprocess.run([sys.executable, build_cpp_script], check=True)
                            print("C++解析器构建成功")
                        except subprocess.CalledProcessError:
                            print("警告: 构建C++解析器失败，CodeBLEU计算可能不准确")
                
                codebleu_score = calc_code_bleu(reference_codes_list, generated_codes, lang)
                print("CodeBLEU 结果:", codebleu_score)
                
                # 保存结果
                with open(out_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "codebleu_score": codebleu_score,
                        "samples": codebleu_results
                    }, f, indent=2, ensure_ascii=False)
                print(f"评估完成，结果保存至: {out_file}")
                
            except Exception as e:
                print(f"计算 CodeBLEU 失败: {e}")
                if debug:
                    import traceback
                    traceback.print_exc()
        else:
            print(f"CodeBLEU 计算失败: 生成代码数量 ({len(generated_codes)}) 与参考代码数量 ({len(reference_codes_list)}) 不匹配")

def main():
    try:
        evaluate_code_bleu()
    except Exception as e:
        print(f"评估过程中发生错误: {e}")
        if CONFIG.get("debug"):
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()