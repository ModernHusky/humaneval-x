# CodeGeeX-HumanEval-X 代码评测工具

## 1. 项目介绍

CodeGeeX-HumanEval-X 是一个专门为评估代码生成模型性能的工具，特别针对C++代码的生成质量进行评测。该工具采用功能正确性评估pass@k和代码质量评估CodeBLEU分数相结合的方式，全面衡量生成代码的质量。

### 主要功能

- 功能正确性评估：通过编译和运行生成的代码，验证其是否通过预设的测试用例
- CodeBLEU评分：评估生成代码与参考代码的结构相似度
- 数据流分析：通过解析代码的数据流图，分析变量依赖关系
- Pass@k指标计算：评估模型在k次尝试中至少产生一个正确解答的概率

## 2. 环境配置

### 系统要求

- Python 3.7+
- C++编译器（支持C++11标准）
- Windows/Linux/MacOS操作系统

### 安装依赖

1. 克隆代码库并进入项目目录

```bash
git clone https://github.com/your-repo/CodeGeeX.git
cd CodeGeeX/humaneval-x
```

2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 编译解析器

该工具使用tree-sitter进行代码解析，需要编译C++解析器：

```bash
cd parser
python build_cpp_parser.py
```

这将生成`cpp-parser.so`（Linux/MacOS）或`cpp-parser.dll`（Windows）文件。

## 3. 数据准备

### 数据格式

评测需要两类数据文件：

1. 参考代码文件（`./data/humaneval_cpp.jsonl.gz`）：包含问题定义和标准答案
2. 生成代码文件（`./data/samples_cpp.jsonl`）：包含模型生成的代码

生成代码文件的格式如下：

```json
{
  "task_id": "HumanEval/0",
  "prompt": "// 问题描述和函数签名...",
  "generation": "// 生成的代码实现...",
  "canonical_solution": "// 标准参考实现..."
}
```

### 准备测试数据

将参考代码放在`./data/humaneval_cpp.jsonl.gz`，将需要评测的生成代码放在`./data/samples_cpp.jsonl`。

## 4. 运行评测

### 基本评测

运行以下命令进行基本评测：

```bash
python evaluate_humaneval_x_with_bleu.py
```

### 自定义评测参数

可以在`evaluate_humaneval_x_with_bleu.py`中修改配置参数：

```python
CONFIG = {
    "refs_file": "./data/humaneval_cpp.jsonl.gz",  # 参考代码文件
    "hyp_file": "./data/samples_cpp.jsonl",        # 生成代码文件
    "lang": "cpp",                                 # 语言
    "tmp_dir": "./cpp",                            # 临时目录
    "out_dir": "./results",                        # 输出目录
    "timeout": 10.0,                               # 单次测试超时（秒）
    "k": [1, 10, 100],                             # pass@k的k值
    "example_test": False,                         # 是否使用示例测试用例
    "debug": True,                                 # 调试模式
}
```

### 运行单个测试

可以使用测试脚本运行单个代码片段的评测：

```bash
python test.py
```

或者运行CodeBLEU测试：

```bash
python test_codebleu.py
```

## 5. 评测指标

### 功能正确性

- **Pass@k**：在k次尝试中至少产生一个正确解答的概率
- **通过率**：通过测试用例的代码比例

### 代码质量评估

- **CodeBLEU分数**：结合n-gram匹配、加权n-gram匹配、语法结构匹配和数据流匹配的综合评分
  - **n-gram匹配**：与BLEU类似，评估词汇重合度
  - **加权n-gram匹配**：根据关键字重要性加权的n-gram匹配
  - **语法结构匹配**：评估代码的语法结构相似度
  - **数据流匹配**：评估代码的变量依赖关系相似度

## 6. 结果分析

### 结果文件

评测结果将保存在`./results/samples_cpp_results.jsonl`文件中，每行包含一个样本的评测结果：

```json
{
  "task_id": "HumanEval/0",
  "completion_id": 0,
  "test_code": "...",
  "prompt": "...",
  "generation": "...",
  "result": "passed",
  "passed": true,
  "finish": 1,
  "file": "...",
  "output": []
}
```

### 字段解释

- **task_id**：任务ID
- **result**：测试结果（"passed"或错误信息）
- **passed**：是否通过测试
- **finish**：代码生成是否完成（1表示完成，-1表示未完成）
- **output**：执行输出

### 统计分析

运行结束后，程序会输出统计信息：

- Pass@k值（k为1、10、100等）
- 各任务的通过率
- 平均CodeBLEU分数

## 7. 高级用法

### 自定义分词策略

可以修改`calc_code_bleu.py`中的`tokenize_code`函数来自定义代码分词策略：

```python
def tokenize_code(code):
    # 自定义分词逻辑
    # ...
    return tokens
```

### 自定义评测权重

可以调整CodeBLEU的权重参数：

```python
params = (0.25, 0.25, 0.25, 0.25)  # (ngram, weighted_ngram, syntax, dataflow)
```

### 自定义关键字列表

在`keywords/cpp.txt`中添加或修改C++关键字，以优化加权n-gram匹配。

## 8. 常见问题

### 编译错误

如果出现编译错误，请确保：
- C++编译器已正确安装
- 临时目录权限正确
- 生成的代码语法正确

### 解析器错误

如果出现解析器错误：
- 检查是否正确编译了C++解析器
- 确认`parser`目录下存在解析器库文件

### 分数异常

如果CodeBLEU分数异常：
- 检查分词策略是否合适
- 确认参考代码和生成代码格式正确
- 调整权重参数

## 9. 参考资料

- CodeBLEU论文：[https://arxiv.org/abs/2009.10297](https://arxiv.org/abs/2009.10297)
- HumanEval基准：[https://arxiv.org/abs/2107.03374](https://arxiv.org/abs/2107.03374)
- Tree-sitter解析器：[https://tree-sitter.github.io/tree-sitter/](https://tree-sitter.github.io/tree-sitter/) 