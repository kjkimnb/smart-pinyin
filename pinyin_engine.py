"""
拼音转换引擎模块
使用pypinyin库进行拼音转换
"""

from pypinyin import pinyin, Style, load_phrases_dict
import re

class PinyinEngine:
    """拼音引擎类"""

    def __init__(self):
        """初始化拼音引擎"""
        self._load_custom_phrases()

    def _load_custom_phrases(self):
        """加载自定义词组，提高转换准确率"""
        custom_phrases = {
            # 添加一些常用但pypinyin可能转换不准确的词
            "我们": [["wo", "men"]],
            "你们": [["ni", "men"]],
            "他们": [["ta", "men"]],
            "工作": [["gong", "zuo"]],
            "学习": [["xue", "xi"]],
        }
        load_phrases_dict(custom_phrases)

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
        # 将二维列表转换为一维字符串
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
        # 允许拼音、数字、空格
        pattern = r'^[a-zA-Z0-9\s]+$'
        return bool(re.match(pattern, text))

    def normalize_pinyin(self, pinyin_text):
        """
        标准化拼音（统一格式）

        Args:
            pinyin_text: 拼音文本

        Returns:
            标准化后的拼音
        """
        if not pinyin_text:
            return ""

        # 转小写
        pinyin_text = pinyin_text.lower()
        # 移除多余空格
        pinyin_text = ' '.join(pinyin_text.split())
        # 替换特殊分隔符
        pinyin_text = pinyin_text.replace('-', ' ')
        pinyin_text = pinyin_text.replace('_', ' ')

        return pinyin_text

    def split_pinyin(self, pinyin_text):
        """
        分割拼音字符串

        Args:
            pinyin_text: 拼音字符串

        Returns:
            拼音列表
        """
        if not pinyin_text:
            return []

        normalized = self.normalize_pinyin(pinyin_text)
        if not normalized:
            return []

        return normalized.split()

    def match_fuzzy(self, input_pinyin, target_pinyin):
        """
        模糊匹配拼音（用于处理输入不完整的情况）

        Args:
            input_pinyin: 用户输入的拼音
            target_pinyin: 目标拼音

        Returns:
            匹配得分
        """
        if not input_pinyin or not target_pinyin:
            return 0

        input_parts = self.split_pinyin(input_pinyin)
        target_parts = self.split_pinyin(target_pinyin)

        # 简单匹配：检查是否是前缀
        score = 0
        for i in range(min(len(input_parts), len(target_parts))):
            if target_parts[i].startswith(input_parts[i]):
                score += 1

        return score
