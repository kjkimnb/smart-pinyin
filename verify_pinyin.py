#!/usr/bin/env python3
"""
简单验证脚本 - 测试拼音转换
"""

from pypinyin import pinyin, Style

def test_pinyin():
    """测试拼音转换"""
    print("=" * 50)
    print("拼音转换验证")
    print("=" * 50 + "\n")
    
    test_words = [
        ('我们', 'wo men'),
        ('西安', "xi 'an"),
        ('张家界', 'zhang jia jie'),
        ('张', 'zhang'),
    ]
    
    for word, expected in test_words:
        result = pinyin(word, style=Style.NORMAL, heteronym=False)
        pinyin_list = [item[0] for item in result if item and len(item) > 0 and item[0]]
        pinyin_str = ' '.join(pinyin_list)
        
        status = "✅" if pinyin_str == expected else "❌"
        print(f"{status} {word} → {pinyin_str} (期望: {expected})")

if __name__ == '__main__':
    test_pinyin()
