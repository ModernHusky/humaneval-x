import os
import sys
import json
import gzip
import numpy as np
import platform
import subprocess
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
    "refs_file": "./data/humaneval_cpp.jsonl.gz",  # 参考代码文件（仅用于问题定义）
    "hyp_file": "./data/samples_cpp.jsonl",        # 生成代码文件（包含 canonical_solution）
    "lang": "cpp",                            # 语言
    "tmp_dir": "./cpp",                       # 临时目录
    "out_dir": "./results",                   # 输出目录
    "timeout": 10.0,                          # 单次测试超时（秒）
    "k": [1, 10, 100],                        # pass@k 的 k 值
    "example_test": False,                    # 是否使用示例测试用例
    "debug": True,                           # 调试模式
}

LANGUAGE_NAME = {"cpp": "CPP"}

def process_humaneval_test(sample, problems, example_test=False):
    """生成完整的 C++ 测试代码。"""
    task_id = sample["task_id"]
    prompt = sample["prompt"]
    if example_test and "example_test" in problems[task_id] and problems[task_id]["example_test"] != "":
        test = problems[task_id]["example_test"]
    else:
        test = problems[task_id]["test"]
    code = sample["generation"]

    test_set_up = "".join(s + "\r\n" for s in IMPORT_HELPER["cpp"] if s not in prompt)  # 使用 \r\n
    return test_set_up + "\r\n" + prompt + code + "\r\n" + test

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

def evaluate_functional_correctness():
    """评估生成的 C++ 代码，计算 pass@k 和 CodeBLEU（单线程）。"""
    # 设置工作目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # 加载配置
    refs_file = CONFIG["refs_file"]
    hyp_file = CONFIG["hyp_file"]
    lang = CONFIG["lang"]
    tmp_dir = CONFIG["tmp_dir"]
    out_dir = CONFIG["out_dir"]
    timeout = CONFIG["timeout"]
    k_values = CONFIG["k"]
    example_test = CONFIG["example_test"]
    debug = CONFIG["debug"]

    print(f"系统平台: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print(f"配置参数: {CONFIG}")

    # 验证文件存在
    if not os.path.exists(refs_file):
        raise FileNotFoundError(f"参考文件未找到: {refs_file}")
    if not os.path.exists(hyp_file):
        raise FileNotFoundError(f"生成代码文件未找到: {hyp_file}")

    # 加载问题集和生成代码
    try:
        problems = read_dataset(refs_file, dataset_type="humaneval")
        print(f"成功加载问题集: {len(problems)} 个问题")
    except Exception as e:
        raise RuntimeError(f"加载问题集失败: {e}")
    try:
        sample_jsonl = stream_jsonl_all(hyp_file)
        print(f"成功加载生成代码: {len(sample_jsonl)} 个样本")
    except Exception as e:
        raise RuntimeError(f"加载生成代码失败: {e}")

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
    suffix = "_example_test.jsonl" if example_test else "_results.jsonl"
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, os.path.basename(hyp_file).replace(".jsonl", suffix))

    # 收集 CodeBLEU 数据
    codebleu_results = []

    # 单线程执行功能正确性测试
    completion_id = Counter()
    results = defaultdict(list)

    k = 0
    print("处理样本...")
    for sample in tqdm(valid_samples):
        k+=1
        if k > 5:
            break
        task_id = sample["task_id"]
        tmp_dir_ = os.path.join(tmp_dir, "evaluation")
        os.makedirs(tmp_dir_, exist_ok=True)
        try:
            sample["test_code"] = process_humaneval_test(sample, problems, example_test)
        except Exception as e:
            print(f"生成测试代码失败 (task_id: {task_id}): {e}")
            continue
        if not sample["test_code"]:
            print(f"测试代码为空 (task_id: {task_id})")
            continue

        # 单线程执行 check_correctness
        try:
            result = check_correctness(task_id, sample, lang, timeout, tmp_dir_, completion_id[task_id])
            if result and "passed" in result:
                results[task_id].append((completion_id[task_id], result))
                print(f"任务 {task_id} 结果: {result['result']}")
            else:
                print(f"无效结果 (task_id: {task_id}): {result}")
        except Exception as e:
            print(f"测试执行错误 (task_id: {task_id}): {e}")
        completion_id[task_id] += 1

        # 收集 CodeBLEU 数据
        codebleu_results.append({
            "task_id": task_id,
            "generated": sample["generation"],
            "reference": sample["canonical_solution"]
        })

    # 计算 pass@k
    total = []
    correct = []
    for task_id, res in results.items():
        total.append(len(res))
        correct.append(sum(r[1]["passed"] for r in res))
    if total and correct:
        try:
            pass_at_k = {}
            for k_value in k_values:
                if (np.array(total) >= k_value).all():
                    pass_at_k[f"pass@{k_value}"] = estimate_pass_at_k(
                        np.array(total), 
                        np.array(correct), 
                        k_value
                    ).mean()
            print("Pass@k 结果:", pass_at_k)
        except Exception as e:
            print(f"计算 pass@k 失败: {e}")

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
            except Exception as e:
                print(f"计算 CodeBLEU 失败: {e}")
                if debug:
                    import traceback
                    traceback.print_exc()
        else:
            print(f"CodeBLEU 计算失败: 生成代码数量 ({len(generated_codes)}) 与参考代码数量 ({len(reference_codes_list)}) 不匹配")

    # 保存结果
    try:
        with (gzip.open(out_file, "wt") if out_file.endswith(".gz") else open(out_file, "w")) as fp:
            for res in results.values():
                for _, r in res:
                    fp.write(json.dumps(r) + "\n")
        print(f"评估完成，结果保存至: {out_file}")
    except Exception as e:
        print(f"保存结果失败: {e}")

def main():
    try:
        evaluate_functional_correctness()
    except Exception as e:
        print(f"评估过程中发生错误: {e}")
        if CONFIG.get("debug"):
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()