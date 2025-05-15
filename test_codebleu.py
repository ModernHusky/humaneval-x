#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""CodeBLEU测试脚本"""

import sys
from calc_code_bleu import calc_code_bleu

def test_codebleu():
    """
    测试CodeBLEU评分计算是否正常
    """
    print("开始测试CodeBLEU计算...")
    
    # 测试C++相同代码
    ref_code = """
    #include <iostream>
    using namespace std;
    
    int add(int a, int b) {
        return a + b;
    }
    
    int main() {
        int x = 5;
        int y = 10;
        cout << add(x, y) << endl;
        return 0;
    }
    """
    
    # 完全相同的代码
    identical_code = ref_code
    
    # 稍微修改的代码
    similar_code = """
    #include <iostream>
    using namespace std;
    
    int add(int a, int b) {
        int result = a + b;
        return result;
    }
    
    int main() {
        int x = 5;
        int y = 10;
        cout << "Result: " << add(x, y) << endl;
        return 0;
    }
    """
    
    # 完全不同的代码
    different_code = """
    #include <iostream>
    #include <vector>
    using namespace std;
    
    int multiply(int a, int b) {
        return a * b;
    }
    
    int main() {
        vector<int> numbers = {1, 2, 3, 4, 5};
        for (int num : numbers) {
            cout << num << " ";
        }
        cout << endl;
        return 0;
    }
    """
    
    
    # 测试相似的代码
    print("\n=== 测试相似的代码 ===")
    score_similar = calc_code_bleu([[ref_code]], [similar_code], "cpp")
    print(f"相似代码的CodeBLEU分数: {score_similar}")
    
    # 测试不同的代码
    print("\n=== 测试完全不同的代码 ===")
    score_different = calc_code_bleu([[ref_code]], [different_code], "cpp")
    print(f"不同代码的CodeBLEU分数: {score_different}")
    
    # 测试结果验证
    # 使用code_bleu字段进行断言
    assert 0.3 <= score_similar['code_bleu'] <= 0.7, f"相似代码的分数应在0.3-0.7之间，实际为: {score_similar['code_bleu']}"
    assert score_different['code_bleu'] < 0.5, f"不同代码的分数应小于0.5，实际为: {score_different['code_bleu']}"
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    test_codebleu() 