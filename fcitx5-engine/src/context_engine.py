"""
上下文关联推荐引擎
实现类似搜狗输入法的智能联想功能
"""

import sqlite3
import logging
from typing import List, Tuple, Dict
from pathlib import Path
import json
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


class ContextEngine:
    """上下文关联推荐引擎"""

    def __init__(self, db_path: str):
        """
        初始化上下文引擎

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_context_db()

        # 上下文窗口大小（保留最近的N个词）
        self.context_window = 3

        # 当前上下文
        self.current_context: List[str] = []

        # N-gram模型缓存
        self.bigram_cache: Dict[Tuple[str, str], int] = {}
        self.trigram_cache: Dict[Tuple[str, str, str], int] = {}

        logger.info("Context Engine initialized")

    def _init_context_db(self):
        """初始化上下文数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建N-gram统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ngram_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context TEXT NOT NULL,
                    next_word TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    n INTEGER NOT NULL,
                    UNIQUE(context, next_word, n)
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_context ON ngram_stats(context)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_next_word ON ngram_stats(next_word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_n ON ngram_stats(n)')

            conn.commit()

            logger.info("Context database initialized")

    def update_context(self, selected_word: str):
        """
        更新上下文并学习关联

        Args:
            selected_word: 用户选择的词汇
        """
        # 添加到上下文
        self.current_context.append(selected_word)

        # 限制上下文窗口大小
        if len(self.current_context) > self.context_window:
            self.current_context.pop(0)

        # 学习N-gram关联
        self._learn_ngrams()

    def _learn_ngrams(self):
        """学习N-gram关联"""
        if len(self.current_context) < 2:
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 学习bigram（前一个词 -> 当前词）
            if len(self.current_context) >= 2:
                prev_word = self.current_context[-2]
                current_word = self.current_context[-1]
                self._update_ngram_count(cursor, prev_word, current_word, n=2)

                # 更新缓存
                self.bigram_cache[(prev_word, current_word)] = \
                    self.bigram_cache.get((prev_word, current_word), 0) + 1

            # 学习trigram（前两个词 -> 当前词）
            if len(self.current_context) >= 3:
                prev_prev = self.current_context[-3]
                prev_word = self.current_context[-2]
                current_word = self.current_context[-1]
                context = f"{prev_prev} {prev_word}"

                self._update_ngram_count(cursor, context, current_word, n=3)

                # 更新缓存
                self.trigram_cache[(prev_prev, prev_word, current_word)] = \
                    self.trigram_cache.get((prev_prev, prev_word, current_word), 0) + 1

            conn.commit()

    def _update_ngram_count(self, cursor, context: str, next_word: str, n: int):
        """更新N-gram计数"""
        try:
            cursor.execute('''
                INSERT INTO ngram_stats (context, next_word, count, n)
                VALUES (?, ?, 1, ?)
            ''', (context, next_word, n))
        except sqlite3.IntegrityError:
            cursor.execute('''
                UPDATE ngram_stats
                SET count = count + 1
                WHERE context = ? AND next_word = ? AND n = ?
            ''', (context, next_word, n))

    def get_contextual_candidates(self, pinyin: str, limit: int = 5) -> List[Tuple[str, float]]:
        """
        基于上下文获取推荐候选词

        Args:
            pinyin: 当前拼音
            limit: 最大返回数量

        Returns:
            候选词列表，格式为 (word, score)
        """
        if not self.current_context:
            return []

        candidates = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 优先使用trigram（更准确）
            if len(self.current_context) >= 2:
                context = f"{self.current_context[-2]} {self.current_context[-1]}"
                candidates.extend(
                    self._get_candidates_from_db(cursor, pinyin, context, n=3, weight=3.0)
                )

            # 使用bigram作为备选
            if len(self.current_context) >= 1 and len(candidates) < limit:
                context = self.current_context[-1]
                additional = self._get_candidates_from_db(cursor, pinyin, context, n=2, weight=2.0)

                # 合并并去重
                existing_words = {word for word, _ in candidates}
                for word, score in additional:
                    if word not in existing_words:
                        candidates.append((word, score))

        return candidates[:limit]

    def _get_candidates_from_db(
        self, cursor, pinyin: str, context: str, n: int, weight: float
    ) -> List[Tuple[str, float]]:
        """
        从数据库获取基于N-gram的候选词

        Args:
            cursor: 数据库游标
            pinyin: 拼音
            context: 上下文
            n: N-gram的N值
            weight: 权重

        Returns:
            候选词列表
        """
        # 这里简化处理，实际应该检查候选词的拼音是否匹配
        cursor.execute('''
            SELECT next_word, count
            FROM ngram_stats
            WHERE context = ? AND n = ?
            ORDER BY count DESC
            LIMIT 10
        ''', (context, n))

        results = cursor.fetchall()

        candidates = []
        for word, count in results:
            # 计算分数：使用对数平滑，避免极端值
            score = math.log(count + 1) * weight
            candidates.append((word, score))

        return candidates

    def clear_context(self):
        """清空上下文"""
        self.current_context = []
        logger.debug("Context cleared")

    def get_context_string(self) -> str:
        """获取当前上下文字符串"""
        return " ".join(self.current_context)

    def get_ngram_stats(self, n: int = 2, limit: int = 10) -> List[Dict]:
        """
        获取N-gram统计信息（用于调试）

        Args:
            n: N-gram的N值
            limit: 返回数量

        Returns:
            统计信息列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT context, next_word, count
                FROM ngram_stats
                WHERE n = ?
                ORDER BY count DESC
                LIMIT ?
            ''', (n, limit))

            stats = []
            for context, next_word, count in cursor.fetchall():
                stats.append({
                    'context': context,
                    'next_word': next_word,
                    'count': count
                })

            return stats
