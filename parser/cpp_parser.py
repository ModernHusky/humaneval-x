import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Union, Optional

# 确保解析器库加载正确
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir.parent))

from tree_sitter import Language, Parser

class CppDFG:
    """C++代码的数据流图分析器"""
    
    def __init__(self, code: str):
        """
        初始化C++数据流分析器
        
        Args:
            code: C++源代码
        """
        self.code = code
        self.variables = {}  # 变量字典: 变量名 -> 依赖变量列表
        self._setup_parser()
        
    def _setup_parser(self) -> None:
        """设置树解析器"""
        parser_path = Path(__file__).resolve().parent
        parser_lib = parser_path / ("cpp-parser.dll" if os.name == 'nt' else "cpp-parser.so")
        
        if not parser_lib.exists():
            raise FileNotFoundError(f"C++解析器库不存在: {parser_lib}")
            
        try:
            language = Language(str(parser_lib), 'cpp')
            self.parser = Parser()
            self.parser.set_language(language)
        except Exception as e:
            raise RuntimeError(f"初始化C++解析器失败: {e}")
    
    def _extract_identifier(self, node) -> Optional[str]:
        """从AST节点提取标识符名称"""
        if node.type == 'identifier':
            return self.code[node.start_byte:node.end_byte]
        return None
    
    def _process_assignment(self, node) -> None:
        """处理赋值语句，提取变量依赖关系"""
        if node.type != 'assignment_expression':
            return
            
        # 左值（被赋值的变量）
        left_node = node.child_by_field_name('left')
        if not left_node:
            return
            
        left_var = self._extract_identifier(left_node)
        if not left_var:
            return
            
        # 右值（表达式）
        right_node = node.child_by_field_name('right')
        if not right_node:
            return
            
        # 分析右侧表达式中的变量引用
        dependencies = set()
        self._collect_dependencies(right_node, dependencies)
        
        # 更新变量依赖关系
        if left_var in self.variables:
            self.variables[left_var].update(dependencies)
        else:
            self.variables[left_var] = dependencies
    
    def _process_declaration(self, node) -> None:
        """处理变量声明，提取初始化依赖关系"""
        if node.type != 'declaration':
            return
            
        # 查找声明符
        for child in node.children:
            if child.type == 'init_declarator':
                # 变量名
                declarator = child.child_by_field_name('declarator')
                if not declarator:
                    continue
                    
                var_name = self._extract_identifier(declarator)
                if not var_name:
                    continue
                    
                # 初始值
                value = child.child_by_field_name('value')
                if not value:
                    continue
                    
                # 收集依赖
                dependencies = set()
                self._collect_dependencies(value, dependencies)
                
                # 更新变量依赖关系
                if var_name in self.variables:
                    self.variables[var_name].update(dependencies)
                else:
                    self.variables[var_name] = dependencies
    
    def _collect_dependencies(self, node, dependencies: Set[str]) -> None:
        """收集表达式中的变量依赖"""
        if not node:
            return
            
        # 如果是标识符，添加到依赖集合
        if node.type == 'identifier':
            var_name = self.code[node.start_byte:node.end_byte]
            dependencies.add(var_name)
            return
            
        # 递归处理子节点
        for child in node.children:
            self._collect_dependencies(child, dependencies)
    
    def _traverse_tree(self, node) -> None:
        """遍历AST，提取数据流信息"""
        # 处理赋值表达式
        if node.type == 'assignment_expression':
            self._process_assignment(node)
        
        # 处理变量声明
        elif node.type == 'declaration':
            self._process_declaration(node)
            
        # 递归处理子节点
        for child in node.children:
            self._traverse_tree(child)
    
    def get_dfg(self) -> Dict[str, List[str]]:
        """
        获取数据流图
        
        Returns:
            Dict[str, List[str]]: 变量依赖关系图
        """
        try:
            # 解析代码
            tree = self.parser.parse(bytes(self.code, 'utf8'))
            root_node = tree.root_node
            
            # 遍历AST提取数据流关系
            self._traverse_tree(root_node)
            
            # 转换集合为列表
            result = {var: list(deps) for var, deps in self.variables.items()}
            return result
        except Exception as e:
            print(f"生成数据流图失败: {e}")
            return {}
    
    def visualize_dfg(self) -> str:
        """
        可视化数据流图
        
        Returns:
            str: 数据流图的文本表示
        """
        dfg = self.get_dfg()
        if not dfg:
            return "数据流图为空"
            
        result = ["数据流图:"]
        for var, deps in sorted(dfg.items()):
            if deps:
                result.append(f"{var} <- {', '.join(deps)}")
            else:
                result.append(f"{var} (无依赖)")
                
        return "\n".join(result)


# 测试代码
if __name__ == "__main__":
    test_code = """
    int main() {
        int a = 10;
        int b = a + 5;
        int c = a + b;
        return c;
    }
    """
    
    try:
        dfg_analyzer = CppDFG(test_code)
        dfg = dfg_analyzer.get_dfg()
        print(dfg_analyzer.visualize_dfg())
    except Exception as e:
        print(f"测试失败: {e}") 