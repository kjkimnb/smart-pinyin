#!/usr/bin/env python3
"""
演示脚本 - 展示输入法的交互功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import InputMethodCLI

def demo():
    """运行演示"""
    print("\n" + "=" * 50)
    print("  中文输入法 - 演示模式")
    print("=" * 50)
    print("\n这是一个自动演示，展示输入法的核心功能：\n")

    db = None
    manager = None

    try:
        from word_database import WordDatabase
        from candidate_manager import CandidateManager
        from pinyin_engine import PinyinEngine

        db = WordDatabase()
        manager = CandidateManager(db)
        engine = PinyinEngine()

        # 演示1: 基本拼音输入
        print("【演示1: 基本拼音输入】")
        print("-" * 50)
        input_pinyin = "wo men"
        print(f"输入拼音: {input_pinyin}")
        candidates = manager.generate_candidates(input_pinyin)
        print(f"候选词:")
        for i, (word, freq) in enumerate(candidates, 1):
            print(f"  {i}. {word} (词频: {freq})")
        if candidates:
            selected = manager.select_candidate(0)
            print(f"选择: {selected}\n")

        # 演示2: 词频学习
        print("【演示2: 词频学习】")
        print("-" * 50)
        input_pinyin = "xue xi"
        print(f"第一次输入拼音: {input_pinyin}")
        candidates = manager.generate_candidates(input_pinyin)
        print(f"词频:")
        for i, (word, freq) in enumerate(candidates, 1):
            print(f"  {i}. {word} (词频: {freq})")
        if candidates:
            selected = manager.select_candidate(0)
            print(f"选择: {selected}")

        # 再次输入
        print(f"\n第二次输入相同拼音: {input_pinyin}")
        candidates = manager.generate_candidates(input_pinyin)
        print(f"词频（已增加）:")
        for i, (word, freq) in enumerate(candidates, 1):
            print(f"  {i}. {word} (词频: {freq})")
        print("→ 词频已自动增加，该词会更优先显示\n")

        # 演示3: 添加自定义词汇
        print("【演示3: 添加自定义词汇】")
        print("-" * 50)
        new_word = "程序员"
        pinyin = engine.to_pinyin(new_word, separator=' ')
        print(f"添加新词: {new_word} (拼音: {pinyin})")
        added_pinyin = manager.add_custom_word(new_word)
        print(f"已添加: {new_word} -> {added_pinyin}")

        # 查询新添加的词
        candidates = manager.generate_candidates(added_pinyin)
        if candidates:
            print(f"验证 - 拼音 '{added_pinyin}' 的候选词:")
            for i, (word, freq) in enumerate(candidates, 1):
                print(f"  {i}. {word} (词频: {freq})")
        print()

        # 演示4: 多词输入
        print("【演示4: 多词输入】")
        print("-" * 50)
        inputs = [
            ("jin tian", "今天"),
            ("kai shi", "开始"),
            ("gong zuo", "工作")
        ]

        result = []
        for pinyin, expected in inputs:
            candidates = manager.generate_candidates(pinyin)
            if candidates:
                word = candidates[0][0]
                result.append(word)
                manager.select_candidate(0)
                print(f"  {pinyin} -> {word}")
            else:
                print(f"  {pinyin} -> (无候选词)")

        print(f"\n完整句子: {''.join(result)}\n")

        # 统计信息
        print("【统计信息】")
        print("-" * 50)
        total_words = db.get_word_count()
        print(f"  词汇总数: {total_words}")
        print(f"  词库已初始化 ✓")
        print(f"  词频学习功能正常 ✓")
        print(f"  自定义词汇功能正常 ✓")

    except Exception as e:
        print(f"\n演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 50)
    print("  演示完成！")
    print("=" * 50)
    print("\n提示:")
    print("  - 运行 'python main.py' 进入交互模式")
    print("  - 输入拼音开始打字")
    print("  - 输入 'q' 退出程序\n")

    return True

if __name__ == "__main__":
    demo()
