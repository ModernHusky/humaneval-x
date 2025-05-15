# Copyright (c) Microsoft Corporation. 
# Licensed under the MIT license.

import platform
import os
from pathlib import Path
from parser_utils import (remove_comments_and_docstrings,
                   tree_to_token_index,
                   index_to_code_token,
                   tree_to_variable_index)
from tree_sitter import Language, Parser

def calc_syntax_match(references, candidate, lang):
    return corpus_syntax_match([references], [candidate], lang)

def corpus_syntax_match(references, candidates, lang):   
    # 根据操作系统选择正确的库文件
    parser_dir = Path(__file__).parent / "parser"
    if platform.system() == 'Windows':
        lib_path = parser_dir / "cpp-parser.dll"
    else:
        lib_path = parser_dir / "cpp-parser.so"
    
    if not lib_path.exists():
        print(f"错误: 找不到C++解析器文件: {lib_path}")
        print("请先运行 parser/setup_parser.py 和 parser/build_cpp_parser.py")
        return 0.0
    
    try:
        CPP_LANGUAGE = Language(str(lib_path), lang)
        parser = Parser()
        parser.set_language(CPP_LANGUAGE)
    except Exception as e:
        print(f"初始化解析器失败: {e}")
        return 0.0

    match_count = 0
    total_count = 0

    for i in range(len(candidates)):
        references_sample = references[i]
        candidate = candidates[i] 
        for reference in references_sample:
            try:
                candidate=remove_comments_and_docstrings(candidate,'cpp')
            except:
                pass    

            candidate_tree = parser.parse(bytes(candidate,'utf8')).root_node

            reference_tree = parser.parse(bytes(reference,'utf8')).root_node

            def get_all_sub_trees(root_node):
                node_stack = []
                sub_tree_sexp_list = []
                depth = 1
                node_stack.append([root_node, depth])
                while len(node_stack) != 0:
                    cur_node, cur_depth = node_stack.pop()
                    sub_tree_sexp_list.append([cur_node.sexp(), cur_depth])
                    for child_node in cur_node.children:
                        if len(child_node.children) != 0:
                            depth = cur_depth + 1
                            node_stack.append([child_node, depth])
                return sub_tree_sexp_list
            cand_sexps = [x[0] for x in get_all_sub_trees(candidate_tree)]
            ref_sexps = get_all_sub_trees(reference_tree)

            # print(cand_sexps)
            # print(ref_sexps)
            
            for sub_tree, depth in ref_sexps:
                if sub_tree in cand_sexps:
                     match_count += 1
            total_count += len(ref_sexps)          
       
    score = match_count / total_count
    return score
