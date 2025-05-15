#!/usr/bin/env python
# -*- coding: utf-8 -*-

from calc_code_bleu import calc_code_bleu

# 参考代码
reference_code = """
int add(int a, int b) {
    return a + b;
}
"""

# 候选代码（稍微不同）
candidate_code = """
int add(int a, int b) {
    int result = a + b;
    return result;
}
"""

# 正确调用方式
score = calc_code_bleu([[reference_code]], [candidate_code], lang="cpp")
print(f"CodeBLEU分数: {score}")