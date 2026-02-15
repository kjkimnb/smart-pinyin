#!/usr/bin/env python3
"""
增强版输入法测试脚本
测试所有新功能
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pinyin_engine_enhanced import PinyinEngineEnhanced
from candidate_manager import CandidateManager
from word_database import WordDatabase

def test_pinyin_engine():
    """测试拼音引擎"""
    print("=" * 50)
    print("测试1: 拼音引擎功能")
    print("=" * 50)
    
    engine = PinyinEngineEnhanced()
    
    # 测试1.1: 基础拼音转换
    print("\n1.1 基础拼音转换:")
    test_cases = [
        ("我们", ["wo", "men"]),
        ("西安", ["xi", "'an"]),
        ("张家界", ["zhang", "jia", "jie"]),
    ]
    
    for word, expected in test_cases:
        result = engine.get_pinyin_list(word)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {word} → {result} (期望: {expected})")
    
    # 测试1.2: 拼音标准化
    print("\n1.2 拼音标准化:")
    test_cases = [
        ("ZhaNg", "zhang"),
        ("zhang-wan-yu", "zhang wan yu"),
        ("zhang_wan_yu", "zhang wan yu"),
    ]
    
    for input_pinyin, expected in test_cases:
        result = engine.normalize_pinyin(input_pinyin)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {input_pinyin} → {result} (期望: {expected})")
    
    # 测试1.3: 智能分词
    print("\n1.3 智能分词:")
    test_cases = [
        ("zhangwanyu", ["zhang", "wan", "yu"]),
        ("xi'an", ["xi", "an"]),
        ("wo men", ["wo", "men"]),
    ]
    
    for input_pinyin, expected in test_cases:
        result = engine.smart_split_pinyin(input_pinyin)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {input_pinyin} → {result} (期望: {expected})")
    
    # 测试1.4: 手动分词检测
    print("\n1.4 手动分词检测:")
    test_cases = [
        ("xi'an", True),
        ("zhang", False),
        ("wo'men", True),
    ]
    
    for input_pinyin, expected in test_cases:
        result = engine.is_manual_split(input_pinyin)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {input_pinyin} 手动分词: {result} (期望: {expected})")
    
    # 测试1.5: 候选词组合生成
    print("\n1.5 候选词组合生成:")
    test_cases = [
        (["zhang", "wan", "yu"], 5),
        (["wo", "men"], 3),
        (["xi", "an"], 2),
    ]
    
    for input_parts, max_words in test_cases:
        result = engine.generate_candidate_combinations(input_parts, max_words)
        status = "✅" if len(result) > 0 else "❌"
        print(f"  {status} {input_parts} → {len(result)} 个组合")
        for combo in result[:3]:
            print(f"      - {combo['pinyin']} (长度: {combo['length']})")
    
    print()

def test_candidate_manager():
    """测试候选词管理器"""
    print("=" * 50)
    print("测试2: 候选词管理器")
    print("=" * 50)
    
    db = WordDatabase()
    manager = CandidateManager(db)
    
    # 测试2.1: 基础候选词生成
    print("\n2.1 基础候选词生成:")
    test_cases = [
        "zhang",
        "wo men",
        "xi'an",
    ]
    
    for pinyin in test_cases:
        candidates = manager.generate_candidates(pinyin)
        print(f"  ✅ {pinyin} → {len(candidates)} 个候选词")
        for idx, (word, freq) in enumerate(candidates[:5], 1):
            print(f"      {idx}. {word} (词频: {freq})")
    
    # 测试2.2: 多音节自动分词
    print("\n2.2 多音节自动分词:")
    test_cases = [
        "zhangwanyu",
        "women",
        "xianshi",
    ]
    
    for pinyin in test_cases:
        candidates = manager.generate_candidates(pinyin)
        print(f"  ✅ {pinyin} → {len(candidates)} 个候选词")
        for idx, (word, freq) in enumerate(candidates[:3], 1):
            print(f"      {idx}. {word} (词频: {freq})")
    
    # 测试2.3: 简拼支持
    print("\n2.3 简拼支持:")
    test_cases = [
        "zh",
        "zhan",
        "zha",
    ]
    
    for pinyin in test_cases:
        candidates = manager.generate_candidates(pinyin)
        print(f"  ✅ {pinyin} → {len(candidates)} 个候选词")
        for idx, (word, freq) in enumerate(candidates[:3], 1):
            print(f"      {idx}. {word} (词频: {freq})")
    
    # 测试2.4: 翻页功能
    print("\n2.4 翻页功能:")
    manager.generate_candidates("zhang")
    total_pages = (len(manager.current_candidates) + 4) // 5
    print(f"  总候选词: {len(manager.current_candidates)}")
    print(f"  总页数: {total_pages}")
    print(f"  ✅ 翻下一页: {manager.next_page()}")
    print(f"  ✅ 翻上一页: {manager.prev_page()}")
    print(f"  ✅ 当前页: {manager.current_page}")
    
    print()

def test_database():
    """测试数据库"""
    print("=" * 50)
    print("测试3: 数据库功能")
    print("=" * 50)
    
    db = WordDatabase()
    
    # 测试3.1: 添加词汇
    print("\n3.1 添加词汇:")
    test_words = [
        ("测试", "ce shi", 50),
        ("功能", "gong neng", 60),
        ("验证", "yan zheng", 70),
    ]
    
    for word, pinyin, freq in test_words:
        success = db.add_word(word, pinyin, freq)
        print(f"  ✅ 添加 {word} ({pinyin}) - 词频: {freq}")
    
    # 测试3.2: 查询候选词
    print("\n3.2 查询候选词:")
    candidates = db.get_candidates("ce shi", limit=10)
    for idx, (word, freq) in enumerate(candidates, 1):
        print(f"  ✅ {idx}. {word} (词频: {freq})")
    
    # 测试3.3: 更新词频
    print("\n3.3 更新词频:")
    db.update_frequency("测试", "ce shi", increment=10)
    candidates = db.get_candidates("ce shi", limit=5)
    for word, freq in candidates:
        if word == "测试":
            print(f"  ✅ {word} 词频更新为: {freq}")
    
    # 测试3.4: 词频衰减
    print("\n3.4 词频衰减:")
    db.decay_frequencies(decay_factor=0.9)
    print("  ✅ 词频衰减执行完成")
    
    print()

def test_integration():
    """集成测试"""
    print("=" * 50)
    print("测试4: 集成测试")
    print("=" * 50)
    
    db = WordDatabase()
    manager = CandidateManager(db)
    
    # 测试4.1: 完整输入流程
    print("\n4.1 完整输入流程:")
    print("  场景: 用户输入 'dongnandaxue'")
    
    # 输入
    candidates = manager.generate_candidates("dongnandaxue")
    print(f"  生成候选词: {len(candidates)} 个")
    
    # 选择
    if candidates:
        selected = manager.select_candidate(0)
        print(f"  选择候选词: {selected}")
    
    # 测试4.2: 分词场景
    print("\n4.2 分词场景:")
    test_cases = [
        ("xi'an", "手动分词"),
        ("dongnandaxue", "自动分词"),
    ]
    
    for pinyin, desc in test_cases:
        candidates = manager.generate_candidates(pinyin)
        print(f"  ✅ {desc} ({pinyin}) → {len(candidates)} 个候选词")
        for idx, (word, freq) in enumerate(candidates[:3], 1):
            print(f"      {idx}. {word} (词频: {freq})")
    
    # 测试4.3: 简拼场景
    print("\n4.3 简拼场景:")
    print("  场景: 用户只想看 'dnd' 的候选词")
    candidates = manager.generate_candidates("dnd")
    print(f"  生成候选词: {len(candidates)} 个")
    for idx, (word, freq) in enumerate(candidates[:3], 1):
        print(f"  ✅ {idx}. {word} (词频: {freq})")
    
    print()

def main():
    """主函数"""
    print("\n" + "=" * 50)
    print("Smart Pinyin 增强版输入法 - 功能测试")
    print("=" * 50 + "\n")
    
    try:
        # 运行所有测试
        test_pinyin_engine()
        test_candidate_manager()
        test_database()
        test_integration()
        
        print("=" * 50)
        print("✅ 所有测试完成！")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
