import os
import gzip
import json

from typing import *

LANGUAGE_TAG = {
    "c++": "// language: C++",
    "cpp": "// language: C++"
}


def stream_jsonl(filename: str) -> Iterable[Dict]:
    """
    Parses each jsonl line and yields it as a dictionary
    """
    filename = os.path.normpath(filename)  # 规范化路径
    if filename.endswith(".gz"):
        with open(filename, "rb") as gzfp:
            with gzip.open(gzfp, "rt", encoding='utf-8') as fp:
                for line in fp:
                    if any(not x.isspace() for x in line):
                        yield json.loads(line)
    else:
        with open(filename, "r", encoding='utf-8') as fp:
            for line in fp:
                if any(not x.isspace() for x in line):
                    yield json.loads(line)


def write_jsonl(filename: str, data: Iterable[Dict], append: bool = False):
    """
    Writes an iterable of dictionaries to jsonl
    """
    filename = os.path.normpath(os.path.expanduser(filename))  # 规范化路径
    if append:
        mode = "ab"
    else:
        mode = "wb"
    
    if filename.endswith(".gz"):
        with open(filename, mode) as fp:
            with gzip.GzipFile(fileobj=fp, mode="wb") as gzfp:
                for x in data:
                    gzfp.write((json.dumps(x) + "\n").encode("utf-8"))
    else:
        with open(filename, mode) as fp:
            for x in data:
                fp.write((json.dumps(x) + "\n").encode("utf-8"))
                
                
def sliding_window(
    prompt_tokens: list, 
    code_tokens: list, 
    seq_len: int, 
    sliding_stride: int, 
    minimum_code_len: int = 1,
) -> Iterable[Tuple[list, list]]:
    """
    Generate a series of (prompt, code) pairs by sliding the window over the code.
    """
    prompt_len = len(prompt_tokens)
    code_len = len(code_tokens)
    total_len = prompt_len + code_len

    start_idx = max(0, prompt_len - seq_len + minimum_code_len)  # at least `minimum_code_len` code token should be in the window
    end_idx = max(0, total_len - seq_len)
    start_idx = min(start_idx, end_idx)

    for i in range(start_idx, end_idx + 1, sliding_stride):
        current_prompt = prompt_tokens[i:i + seq_len]
        current_code = code_tokens[max(i - prompt_len, 0):i - prompt_len + seq_len]
        yield current_prompt, current_code

    if (end_idx - start_idx) % sliding_stride != 0:
        current_prompt = prompt_tokens[end_idx:end_idx + seq_len]
        current_code = code_tokens[max(end_idx - prompt_len, 0):end_idx - prompt_len + seq_len]
        yield current_prompt, current_code
