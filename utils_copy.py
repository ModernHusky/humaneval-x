import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Sequence
from data_utils import stream_jsonl, LANGUAGE_TAG
from collections import Counter

def ngrams(sequence: Sequence[Any], n: int) -> List[Tuple[Any, ...]]:
    """
    生成序列的n-gram元组
    
    Args:
        sequence: 输入序列
        n: n-gram的大小
    
    Returns:
        List[Tuple[Any, ...]]: n-gram元组列表
    """
    if len(sequence) < n:
        return []
    # 直接返回元组，而不是zip对象或列表
    return [tuple(sequence[i:i+n]) for i in range(len(sequence)-n+1)]

# 只保留C++相关的导入
IMPORT_HELPER = {
    "cpp": [
        "#include<stdlib.h>",
        "#include<algorithm>",
        "#include<math.h>",
        "#include<stdio.h>",
        "#include<vector>",
        "#include<string>",
        "#include<climits>",
        "#include<cstring>",
        "#include<iostream>",
    ]
}

def read_dataset(
    data_file: Optional[str] = None,
    dataset_type: str = "humaneval",
    num_shot: Optional[int] = None,
) -> Dict:
    """
    读取数据集
    
    Args:
        data_file: 数据文件路径
        dataset_type: 数据集类型
        num_shot: 样本数量
    
    Returns:
        Dict: 数据集字典
    """
    if num_shot is not None:
        print(f"{num_shot}-shot setting...")
        
    if "humaneval" not in dataset_type.lower():
        raise ValueError(f"不支持的数据集类型: {dataset_type}")
        
    if data_file is None:
        current_path = Path(__file__).parent
        data_file = current_path.parent / "humaneval-x" / "cpp" / "data" / "humaneval_cpp.jsonl.gz"
        
    dataset = {task["task_id"]: task for task in stream_jsonl(str(data_file))}
    return dataset

def read_translation_dataset(
    data_file_src: Optional[str] = None,
    data_file_tgt: Optional[str] = None,
    lang_src: Optional[str] = None,
    lang_tgt: Optional[str] = None,
    dataset_type: str = "humaneval",
) -> Dict:
    """
    读取翻译数据集
    
    Args:
        data_file_src: 源语言数据文件
        data_file_tgt: 目标语言数据文件
        lang_src: 源语言
        lang_tgt: 目标语言
        dataset_type: 数据集类型
    
    Returns:
        Dict: 翻译数据集字典
    """
    if "humaneval" not in dataset_type.lower():
        raise ValueError(f"不支持的数据集类型: {dataset_type}")
        
    dataset_src = {task["task_id"]: task for task in stream_jsonl(data_file_src)}
    dataset_tgt = {task["task_id"].split("/")[-1]: task for task in stream_jsonl(data_file_tgt)}
    
    for k, sample in dataset_src.items():
        prompt = "code translation\n"
        prompt += "C++:\n"
        prompt += dataset_src[k]["declaration"] + "\n" + dataset_src[k]["canonical_solution"].rstrip() + "\n"
        prompt += "C++:\n"
        prompt += dataset_tgt[k.split("/")[-1]]["declaration"]
        dataset_src[k]["prompt"] = prompt
        
    return dataset_src

def process_extra_prompt(prompt: str, language_type: Optional[str] = None) -> str:
    """
    处理额外提示
    
    Args:
        prompt: 原始提示
        language_type: 语言类型
    
    Returns:
        str: 处理后的提示
    """
    if language_type is None or language_type.lower() != "cpp":
        return prompt
        
    extra_prompt = LANGUAGE_TAG.get("cpp", "") + "\n"
    return extra_prompt + prompt

def is_code_generation_finished(
    code: str,
    language_type: Optional[str] = None,
    dataset: Optional[str] = None,
) -> bool:
    """
    检查代码生成是否完成
    
    Args:
        code: 生成的代码
        language_type: 语言类型
        dataset: 数据集类型
    
    Returns:
        bool: 是否完成
    """
    if language_type is None or dataset is None:
        return False
        
    if "humaneval" in dataset.lower() and language_type.lower() == "cpp":
        return code.count("{") + 1 == code.count("}")
        
    return False

def cleanup_code(
    code: str,
    language_type: Optional[str] = None,
    dataset: Optional[str] = None,
) -> str:
    """
    清理生成的代码
    
    Args:
        code: 原始代码
        language_type: 语言类型
        dataset: 数据集类型
    
    Returns:
        str: 清理后的代码
    """
    if language_type is None or dataset is None:
        return code
        
    if "humaneval" in dataset.lower() and language_type.lower() == "cpp":
        if '}' in code:
            code = code[:code.rfind('}')] + '}'
            
    return code
