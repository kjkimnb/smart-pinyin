"""
候选词管理模块（增强版）
支持分词、多音节智能分词
负责候选词的生成、排序和管理
"""

from word_database import WordDatabase
from pinyin_engine_enhanced import PinyinEngineEnhanced
from config import MAX_CANDIDATES, PAGE_SIZE, FREQUENCY_INCREMENT, FREQUENCY_DECAY

class CandidateManager:
    """候选词管理器类"""

    def __init__(self, db=None):
        """初始化候选词管理器"""
        self.db = db or WordDatabase()
        self.pinyin_engine = PinyinEngineEnhanced()
        self.current_pinyin = ""
        self.current_candidates = []
        self.current_page = 0
        self.is_manual_split = False  # 是否是手动分词

    def generate_candidates(self, pinyin_text):
        """
        生成候选词（支持分词和多音节输入）

        优先级：
        1. 更长的组合（更多音节）
        2. 更高的词频

        Args:
            pinyin_text: 拼音输入

        Returns:
            候选词列表 [(word, frequency), ...]
        """
        if not pinyin_text:
            return []

        # 标准化拼音（保留分词符）
        normalized = self.pinyin_engine.normalize_pinyin(pinyin_text)
        self.current_pinyin = normalized

        # 检查是否手动分词
        self.is_manual_split = self.pinyin_engine.is_manual_split(pinyin_text)

        # 智能分词
        pinyin_parts = self.pinyin_engine.smart_split_pinyin(normalized)
        
        # 生成候选词组合
        all_candidates = []
        
        if len(pinyin_parts) > 1:
            # 多音节：生成候选词组合
            combinations = self.pinyin_engine.generate_candidate_combinations(
                pinyin_parts, max_words=MAX_CANDIDATES
            )
            
            # 按优先级查询数据库
            for combo in combinations:
                combo_pinyin = combo['pinyin']
                candidates = self.db.get_candidates(combo_pinyin, limit=10)
                
                # 添加到总候选词列表
                for word, freq in candidates:
                    all_candidates.append((word, freq, combo['length']))
                    
                # 如果已经找到足够的候选词，停止查询更短的组合
                if len(all_candidates) >= MAX_CANDIDATES:
                    break
        else:
            # 单音节或自动分词后的结果
            candidates = self.db.get_candidates(normalized, limit=MAX_CANDIDATES)
            for word, freq in candidates:
                all_candidates.append((word, freq, 1))

        # 去重并排序
        unique_candidates = {}
        for word, freq, length in all_candidates:
            if word not in unique_candidates:
                unique_candidates[word] = (freq, length)
            else:
                # 优先保留更长的组合
                if length > unique_candidates[word][1]:
                    unique_candidates[word] = (freq, length)

        # 修正排序逻辑：
        # 1. 长度优先（更长的词排在前面）
        # 2. 词频其次（同长度按词频降序）
        sorted_candidates = sorted(
            unique_candidates.items(),
            key=lambda x: (-x[1][1], -x[1][0])
        )[:MAX_CANDIDATES]

        # 只返回(word, frequency)，去掉length信息
        self.current_candidates = [(word, freq) for word, (freq, _) in sorted_candidates]
        self.current_page = 0

        return self.current_candidates

    def _generate_fallback_candidates(self, pinyin_text):
        """
        生成后备候选词（当数据库中没有时）
        基于拼音规则生成一些可能的选择

        Args:
            pinyin_text: 拼音输入

        Returns:
            后备候选词列表
        """
        candidates = []

        # 这里可以添加更复杂的拼音转汉字逻辑
        # 暂时返回空列表，让用户手动添加词汇
        return candidates

    def select_candidate(self, index, record=True):
        """
        选择候选词

        Args:
            index: 候选词索引
            record: 是否记录到历史

        Returns:
            选中的词，如果索引无效返回None
        """
        if index < 0 or index >= len(self.current_candidates):
            return None

        word, frequency = self.current_candidates[index]

        # 更新词频
        if record:
            self._update_word_frequency(word)

        return word

    def _update_word_frequency(self, word):
        """
        更新词频并衰减其他词

        Args:
            word: 选中的词
        """
        # 增加选中词的词频
        self.db.update_frequency(word, self.current_pinyin, FREQUENCY_INCREMENT)

        # 记录选择历史
        self.db.record_selection(word, self.current_pinyin)

        # 衰减其他词频（避免高频词一直占据首位）
        # 这里可以选择是否衰减，为了简单暂时不衰减

    def add_custom_word(self, word, pinyin=None):
        """
        添加自定义词汇

        Args:
            word: 汉字词汇
            pinyin: 拼音（如果不提供则自动生成）
        """
        if pinyin is None:
            pinyin = self.pinyin_engine.to_pinyin(word, separator=' ')

        if pinyin:
            self.db.add_word(word, pinyin, frequency=5)
            # 刷新当前候选词列表
            if self.current_pinyin == pinyin:
                self.generate_candidates(self.current_pinyin)

        return pinyin

    def get_current_page(self, page_size=PAGE_SIZE):
        """
        获取当前页的候选词

        Args:
            page_size: 每页显示数量

        Returns:
            当前页候选词 [(word, frequency), ...]
        """
        start = self.current_page * page_size
        end = start + page_size
        return self.current_candidates[start:end]

    def next_page(self, page_size=PAGE_SIZE):
        """翻到下一页"""
        total_pages = (len(self.current_candidates) + page_size - 1) // page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            return True
        return False

    def prev_page(self, page_size=PAGE_SIZE):
        """翻到上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            return True
        return False

    def get_page_info(self, page_size=PAGE_SIZE):
        """
        获取分页信息

        Args:
            page_size: 每页显示数量

        Returns:
            (当前页, 总页数)
        """
        total_pages = (len(self.current_candidates) + page_size - 1) // page_size
        return (self.current_page + 1, total_pages)

    def clear(self):
        """清空当前状态"""
        self.current_pinyin = ""
        self.current_candidates = []
        self.current_page = 0
