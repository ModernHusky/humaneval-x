# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# -*- coding:utf-8 -*-
import argparse
import os

import bleu
import weighted_ngram_match
import syntax_match
import dataflow_match
    
def calc_code_bleu(references, hypothesis, lang, params=(0.15, 0.15, 0.35, 0.35)):
    """
    计算 CodeBLEU 分数，支持 C++。
    
    Args:
        references: List[List[str]]，参考代码列表，每个元素是某任务的多个参考实现
        hypothesis: List[str]，生成代码列表
        lang: str,编程语言('cpp')
        params: tuple,权重 (alpha, beta, gamma, theta) for ngram, weighted ngram, syntax, dataflow
    
    Returns:
        dict,包含 ngram_match, weighted_ngram_match, syntax_match, dataflow_match, code_bleu 分数
    """
    alpha, beta, gamma, theta = params

    # 验证语言
    supported_langs = ['cpp']
    if lang not in supported_langs:
        raise ValueError(f"不支持的语言: {lang}. 支持的语言: {supported_langs}")

    # 打印调试信息
    print(f"参考代码数量: {len(references)}, 生成代码数量: {len(hypothesis)}")
    if references and references[0]:
        print(f"参考代码示例: {references[0][0][:50]}...")
    if hypothesis:
        print(f"生成代码示例: {hypothesis[0][:50]}...")
    
    # 分词处理
    tokenized_hyps = []
    for hyp in hypothesis:
        tokens = hyp.replace('\n', ' ').replace('\t', ' ').split()
        tokenized_hyps.append(tokens)
    
    tokenized_refs = []
    for refs in references:
        tokenized_refs_inner = []
        for ref in refs:
            tokens = ref.replace('\n', ' ').replace('\t', ' ').split()
            tokenized_refs_inner.append(tokens)
        tokenized_refs.append(tokenized_refs_inner)
    
    # 打印分词结果
    print(f"分词后参考代码示例: {tokenized_refs[0][0][:10]}...")
    print(f"分词后生成代码示例: {tokenized_hyps[0][:10]}...")
    
    # 计算 ngram match (BLEU)
    ngram_match_score = bleu.corpus_bleu(
        tokenized_refs, 
        tokenized_hyps, 
        weights=(0.25, 0.25, 0.25, 0.25), 
        smoothing_function=bleu.SmoothingFunction().method1
    )

    # 计算 weighted ngram match
    keyword_file = f'keywords/{lang}.txt'
    if not os.path.exists(keyword_file):
        raise FileNotFoundError(f"关键字文件未找到: {keyword_file}")
    keywords = [x.strip() for x in open(keyword_file, 'r', encoding='utf-8').readlines()]
    def make_weights(reference_tokens, key_word_list):
        return {token: 1 if token in key_word_list else 0.2 for token in reference_tokens}
    tokenized_refs_with_weights = [[[reference_tokens, make_weights(reference_tokens, keywords)]
                                   for reference_tokens in ref] for ref in tokenized_refs]
    weighted_ngram_match_score = weighted_ngram_match.corpus_bleu(tokenized_refs_with_weights, tokenized_hyps)

    # 计算 syntax match
    syntax_match_score = syntax_match.corpus_syntax_match(references, hypothesis, lang)

    # 计算 dataflow match
    dataflow_match_score = dataflow_match.corpus_dataflow_match(references, hypothesis, lang)

    # 计算 CodeBLEU 分数
    code_bleu_score = (alpha * ngram_match_score +
                       beta * weighted_ngram_match_score +
                       gamma * syntax_match_score +
                       theta * dataflow_match_score)

    return {
        'ngram_match': ngram_match_score,
        'weighted_ngram_match': weighted_ngram_match_score,
        'syntax_match': syntax_match_score,
        'dataflow_match': dataflow_match_score,
        'code_bleu': code_bleu_score
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--refs', type=str, nargs='+', required=True, help='reference files')
    parser.add_argument('--hyp', type=str, required=True, help='hypothesis file')
    parser.add_argument('--lang', type=str, required=True, choices=['cpp'], help='programming language')
    parser.add_argument('--params', type=str, default='0.25,0.25,0.25,0.25', help='alpha, beta, gamma, theta')
    args = parser.parse_args()

    lang = args.lang
    alpha, beta, gamma, theta = [float(x) for x in args.params.split(',')]
    pre_references = [[x.strip() for x in open(file, 'r', encoding='utf-8').readlines()] for file in args.refs]
    hypothesis = [x.strip() for x in open(args.hyp, 'r', encoding='utf-8').readlines()]
    result = calc_code_bleu(pre_references, hypothesis, lang, params=(alpha, beta, gamma, theta))
    print('ngram match: {0}, weighted ngram match: {1}, syntax_match: {2}, dataflow_match: {3}'.format(
        result['ngram_match'], result['weighted_ngram_match'], result['syntax_match'], result['dataflow_match']))
    print('CodeBLEU score: ', result['code_bleu'])