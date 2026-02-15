"""
智能拼音转换引擎（增强版）
支持分词、多音节智能分词
"""

from pypinyin import pinyin, Style, load_phrases_dict
import re
from typing import List, Tuple

class PinyinEngineEnhanced:
    """增强版拼音引擎类"""

    def __init__(self):
        """初始化拼音引擎"""
        self._load_custom_phrases()
        self._load_pinyin_dict()
        
        # 常见单音节（用于分词）
        self.single_syllables = self._load_single_syllables()

    def _load_single_syllables(self):
        """加载常见单音节列表"""
        # 简化的单音节列表（实际应该从字典加载）
        common_syllables = {
            'a', 'ai', 'an', 'ang', 'ao',
            'ba', 'bai', 'ban', 'bang', 'bao',
            'zha', 'zhai', 'zhan', 'zhang', 'zhao',
            'cha', 'chai', 'chan', 'chang', 'chao',
            'sha', 'shai', 'shan', 'shang', 'shao',
            'z', 'zh', 'ch', 'sh',
            'd', 'da', 'de', 'di', 'du',
            'n', 'na', 'ne', 'ni', 'nu',
            'y', 'ya', 'ye', 'yi', 'yu',
            'w', 'wa', 'wo', 'wu', 'wang',
        }
        return common_syllables

    def _load_custom_phrases(self):
        """加载自定义词组"""
        custom_phrases = {
            "我们": [["wo", "men"]],
            "你们": [["ni", "men"]],
            "他们": [["ta", "men"]],
            "工作": [["gong", "zuo"]],
            "学习": [["xue", "xi"]],
            "西安": [["xi", "'an"]],  # 带'的拼音
            "西安人": [["xi", "'an", "ren"]],
            "西安市": [["xi", "'an", "shi"]],
            "张家界": [["zhang", "jia", "jie"]],
        }
        load_phrases_dict(custom_phrases)

    def _load_pinyin_dict(self):
        """加载拼音字典（用于分词）"""
        # 这里简化处理，实际应该从拼音字典文件加载
        pass

    def normalize_pinyin(self, pinyin_text):
        """
        标准化拼音，保留分隔符
        
        Args:
            pinyin_text: 拼音文本（可能包含 ' 作为分词符）
            
        Returns:
            标准化后的拼音
        """
        if not pinyin_text:
            return ""

        # 转小写
        pinyin_text = pinyin_text.lower()
        
        # 保留'作为分词符（用于xi'an）
        pinyin_text = pinyin_text.replace('-', "'")
        
        # 移除多余空格
        pinyin_text = ' '.join(pinyin_text.split())
        
        return pinyin_text

    def smart_split_pinyin(self, pinyin_text: str) -> List[str]:
        """
        智能分词 - 处理多音节输入
        
        策略：
        1. 先检查是否有明确的分词符（'）
        2. 如果没有，尝试自动分词
        3. 从长到短尝试匹配
        
        Args:
            pinyin_text: 拼音字符串（如 "zhangwanyu"）
            
        Returns:
            分词后的拼音列表（如 ["zhang", "wan", "yu"]）
        """
        if not pinyin_text:
            return []
            
        normalized = self.normalize_pinyin(pinyin_text)
        
        # 策略1：检查是否有明确分词符（手动分词优先级最高）
        if "'" in normalized:
            # 有'分隔符，直接按'分割
            parts = normalized.split("'")
            return [p.strip() for p in parts if p.strip()]
        
        # 策略2：如果有空格，按空格分割
        if ' ' in normalized:
            parts = normalized.split()
            return [p.strip() for p in parts if p.strip()]
        
        # 策略3：自动分词
        return self._auto_split_pinyin(normalized)

    def _auto_split_pinyin(self, pinyin_text: str) -> List[str]:
        """
        自动分词 - 从后向前贪婪匹配
        
        Args:
            pinyin_text: 连续的拼音字符串
            
        Returns:
            分词后的拼音列表
        """
        if not pinyin_text:
            return []
            
        # 如果很短，直接返回
        if len(pinyin_text) <= 2:
            return [pinyin_text] if pinyin_text else []
            
        # 从后向前匹配
        result = []
        remaining = pinyin_text
        
        while remaining:
            # 从最长到最短尝试匹配
            matched = False
            
            for length in range(min(len(remaining), 6), 0, -1):
                candidate = remaining[:length]
                
                # 检查是否是有效的音节
                if self._is_valid_syllable(candidate):
                    result.insert(0, candidate)
                    remaining = remaining[length:]
                    matched = True
                    break
            
            if not matched:
                # 无法匹配，作为整体保留
                result.insert(0, remaining)
                break
        
        return result

    def _is_valid_syllable(self, text: str) -> bool:
        """
        检查是否是有效的拼音音节
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否有效
        """
        if not text:
            return False
            
        # 基本拼音模式：声母+韵母
        pattern = r'^[bpmfdtnlgkhjqxzcsryw]?(a|ai|an|ang|ao|e|ei|en|eng|o|ou|i|ia|ie|iao|iu|ian|in|iang|ing|iong|u|ua|ue|uo|ui|uan|un|uang|ueng|v|ve|vn)?(n|ng)?$'
        
        # 简单版本：只检查是否在常见音节中
        if text in self.single_syllables:
            return True
            
        # 或匹配拼音模式
        return bool(re.match(pattern, text.lower()))

    def generate_candidate_combinations(self, pinyin_parts: List[str], max_words: int = 5) -> List[List[str]]:
        """
        生成候选词组合（用于多音节输入）
        
        策略：
        1. 先尝试全匹配（所有音节）
        2. 再尝试匹配前N-1个音节
        3. 再尝试匹配前N-2个音节
        ...以此类推
        
        Args:
            pinyin_parts: 分词后的拼音列表（如 ["zhang", "wan", "yu"]）
            max_words: 每次返回的最大候选词数
            
        Returns:
            候选词组合列表（按优先级排序）
        """
        if not pinyin_parts:
            return []
            
        combinations = []
        
        # 策略1：尝试全匹配（所有音节）
        full_match = ' '.join(pinyin_parts)
        combinations.append({
            'pinyin': full_match,
            'parts': pinyin_parts,
            'length': len(pinyin_parts)
        })
        
        # 策略2：依次减少音节数
        for i in range(len(pinyin_parts) - 1, 0, -1):
            partial_parts = pinyin_parts[:i]
            partial_pinyin = ' '.join(partial_parts)
            
            combinations.append({
                'pinyin': partial_pinyin,
                'parts': partial_parts,
                'length': i
            })
        
        # 按长度排序（长的优先）
        combinations.sort(key=lambda x: x['length'], reverse=True)
        
        return combinations

    def is_manual_split(self, pinyin_text: str) -> bool:
        """
        检查是否是手动分词（包含'分隔符）
        
        Args:
            pinyin_text: 拼音文本
            
        Returns:
            是否是手动分词
        """
        return "'" in pinyin_text

    def to_pinyin(self, text, style=Style.NORMAL, separator=' '):
        """
        将中文转换为拼音
        
        Args:
            text: 中文文本
            style: 拼音风格
            separator: 拼音分隔符
            
        Returns:
            拼音字符串
        """
        if not text:
            return ""
            
        result = pinyin(text, style=style, heteronym=False)
        pinyin_list = [item[0] for item in result if item[0]]
        return separator.join(pinyin_list)

    def get_pinyin_list(self, text):
        """
        获取拼音列表
        
        Args:
            text: 中文文本
            
        Returns:
            拼音列表
        """
        if not text:
            return []
            
        result = pinyin(text, style=Style.NORMAL, heteronym=False)
        return [item[0] for item in result if item[0]]

    def is_pinyin(self, text):
        """
        判断输入是否为纯拼音
        
        Args:
            text: 输入文本
            
        Returns:
            是否为拼音
        """
        if not text:
            return False
            
        # 允许拼音、数字、空格、分词符
        pattern = r'^[a-zA-Z0-9\s\']+$'
        return bool(re.match(pattern, text))


# 创建全局实例
pinyin_engine_enhanced = PinyinEngineEnhanced()
