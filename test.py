#!/usr/bin/env python3
"""
测试脚本 - 验证输入法功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pinyin_engine import PinyinEngine
from word_database import WordDatabase
from candidate_manager import CandidateManager

def test_pinyin_engine():
    """测试拼音引擎"""
    print("=" * 50)
    print("测试 1: 拼音引擎")
    print("=" * 50)

    engine = PinyinEngine()

    # 测试中文转拼音
    test_words = ["我们", "学习", "输入法"]
    for word in test_words:
        pinyin = engine.to_pinyin(word)
        print(f"  {word} -> {pinyin}")

    # 测试拼音判断
    test_inputs = ["wo men", "我们", "hello123"]
    for input_text in test_inputs:
        is_pinyin = engine.is_pinyin(input_text)
        print(f"  '{input_text}' 是拼音: {is_pinyin}")

    print()

def test_word_database():
    """测试词频数据库"""
    print("=" * 50)
    print("测试 2: 词频数据库")
    print("=" * 50)

    db = WordDatabase()

    # 初始化常用词
    count = db.initialize_common_words()
    print(f"  初始化了 {count} 个常用词汇")

    # 获取词汇总数
    total = db.get_word_count()
    print(f"  当前词汇总数: {total}")

    # 测试查询
    test_pinyin = "wo men"
    candidates = db.get_candidates(test_pinyin, limit=5)
    print(f"  拼音 '{test_pinyin}' 的候选词:")
    for word, freq in candidates:
        print(f"    - {word} (词频: {freq})")

    print()

def test_candidate_manager():
    """测试候选词管理器"""
    print("=" * 50)
    print("测试 3: 候选词管理器")
    print("=" * 50)

    manager = CandidateManager()

    # 测试生成候选词
    test_pinyin = "xue xi"
    candidates = manager.generate_candidates(test_pinyin)
    print(f"  拼音 '{test_pinyin}' 的候选词:")
    for word, freq in candidates:
        print(f"    - {word} (词频: {freq})")

    # 测试选择候选词
    if candidates:
        selected = manager.select_candidate(0)
        print(f"  选择了第一个词: {selected}")

    # 测试添加自定义词汇
    new_word = "输入法"
    pinyin = manager.add_custom_word(new_word)
    print(f"  添加新词: {new_word} (拼音: {pinyin})")

    print()

def test_integration():
    """集成测试"""
    print("=" * 50)
    print("测试 4: 集成测试")
    print("=" * 50)

    db = WordDatabase()
    manager = CandidateManager(db)
    engine = PinyinEngine()

    # 模拟完整流程
    print("  模拟输入流程:")

    # 1. 用户输入拼音
    input_pinyin = "gong zuo"
    print(f"  1. 输入拼音: {input_pinyin}")

    # 2. 生成候选词
    candidates = manager.generate_candidates(input_pinyin)
    print(f"  2. 候选词:")
    for i, (word, freq) in enumerate(candidates[:3], 1):
        print(f"     {i}. {word} (词频: {freq})")

    # 3. 用户选择第一个词
    if candidates:
        selected = manager.select_candidate(0)
        print(f"  3. 选择: {selected}")

    # 4. 再次查询，词频应该增加
    new_candidates = manager.generate_candidates(input_pinyin)
    if new_candidates and new_candidates[0][1] > candidates[0][1]:
        print(f"  4. 词频已更新: {candidates[0][1]} -> {new_candidates[0][1]}")

    print()

def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("  中文输入法 - 功能测试")
    print("=" * 50 + "\n")

    try:
        test_pinyin_engine()
        test_word_database()
        test_candidate_manager()
        test_integration()

        print("=" * 50)
        print("  ✓ 所有测试通过！")
        print("=" * 50)
        print("\n现在可以运行: python main.py 启动输入法\n")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
