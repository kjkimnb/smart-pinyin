"""
自适应词频管理模块
实现比谷歌输入法更好的智能词频算法
"""

import sqlite3
import logging
from typing import List, Tuple, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import math
import hashlib

logger = logging.getLogger(__name__)


class AdaptiveFrequencyManager:
    """自适应词频管理器"""

    def __init__(self, db_path: str):
        """
        初始化词频管理器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self._init_frequency_db()

        # 缓存
        self.frequency_cache: Dict[str, float] = {}

        # 配置参数
        self.decay_rate = 0.99  # 日衰减率
        self.time_window_days = 30  # 时间窗口（天）
        self.min_frequency = 1.0  # 最小频率
        self.max_frequency = 1000.0  # 最大频率

        logger.info("Adaptive Frequency Manager initialized")

    def _init_frequency_db(self):
        """初始化词频数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 创建增强的词频表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS word_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    pinyin TEXT NOT NULL,
                    base_frequency REAL DEFAULT 1.0,
                    total_selections INTEGER DEFAULT 0,
                    last_selected TIMESTAMP,
                    first_selected TIMESTAMP,
                    selection_times TEXT,
                    UNIQUE(word, pinyin)
                )
            ''')

            # 创建时间序列表（记录每次选择的时间）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS selection_timeline (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    pinyin TEXT NOT NULL,
                    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    hour_of_day INTEGER,
                    day_of_week INTEGER
                )
            ''')

            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON word_stats(word)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pinyin ON word_stats(pinyin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_word_pinyin ON word_stats(word, pinyin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_word ON selection_timeline(word, pinyin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_time ON selection_timeline(selected_at)')

            conn.commit()

            logger.info("Frequency database initialized")

    def record_selection(self, word: str, pinyin: str):
        """
        记录用户选择

        Args:
            word: 选中的词
            pinyin: 拼音
        """
        now = datetime.now()
        hour = now.hour
        day_of_week = now.weekday()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 更新主统计表
            cursor.execute('''
                INSERT INTO word_stats (word, pinyin, base_frequency, total_selections,
                                        last_selected, first_selected)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(word, pinyin) DO UPDATE SET
                    base_frequency = base_frequency + 1,
                    total_selections = total_selections + 1,
                    last_selected = excluded.last_selected,
                    selection_times = selection_times || ',' || ?
            ''', (word, pinyin, 1.0, now, now, str(int(now.timestamp()))))

            # 插入时间序列
            cursor.execute('''
                INSERT INTO selection_timeline (word, pinyin, selected_at, hour_of_day, day_of_week)
                VALUES (?, ?, ?, ?, ?)
            ''', (word, pinyin, now, hour, day_of_week))

            conn.commit()

            # 更新缓存
            cache_key = self._get_cache_key(word, pinyin)
            self.frequency_cache[cache_key] = self._calculate_adaptive_frequency(word, pinyin)

        logger.debug(f"Recorded selection: {word} ({pinyin})")

    def get_adaptive_frequency(self, word: str, pinyin: str) -> float:
        """
        获取自适应词频分数

        Args:
            word: 词汇
            pinyin: 拼音

        Returns:
            自适应频率分数
        """
        cache_key = self._get_cache_key(word, pinyin)

        if cache_key in self.frequency_cache:
            return self.frequency_cache[cache_key]

        frequency = self._calculate_adaptive_frequency(word, pinyin)
        self.frequency_cache[cache_key] = frequency

        return frequency

    def _calculate_adaptive_frequency(self, word: str, pinyin: str) -> float:
        """
        计算自适应频率

        综合考虑以下因素：
        1. 历史选择次数
        2. 时间衰减（近期选择权重更高）
        3. 时间模式（小时、星期）
        4. 选择间隔（避免过于频繁）

        Returns:
            自适应频率分数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 获取基础统计
            cursor.execute('''
                SELECT base_frequency, total_selections, last_selected, first_selected
                FROM word_stats
                WHERE word = ? AND pinyin = ?
            ''', (word, pinyin))

            result = cursor.fetchone()
            if not result:
                return self.min_frequency

            base_freq, total_selections, last_selected, first_selected = result

            # 获取近期选择记录（时间窗口内）
            window_start = datetime.now() - timedelta(days=self.time_window_days)
            cursor.execute('''
                SELECT COUNT(*) FROM selection_timeline
                WHERE word = ? AND pinyin = ? AND selected_at >= ?
            ''', (word, pinyin, window_start))

            recent_selections = cursor.fetchone()[0]

            # 计算时间衰减分数
            if last_selected:
                last_time = datetime.fromisoformat(last_selected)
                days_since = (datetime.now() - last_time).days
                time_factor = math.pow(self.decay_rate, days_since)
            else:
                time_factor = 1.0

            # 计算趋势分数（近期选择相对于总选择的比例）
            trend_factor = 1.0
            if total_selections > 0:
                trend_factor = 1.0 + (recent_selections / total_selections)

            # 计算时间模式分数（考虑当前时间和历史选择时间）
            current_hour = datetime.now().hour
            current_dow = datetime.now().weekday()

            cursor.execute('''
                SELECT COUNT(*) FROM selection_timeline
                WHERE word = ? AND pinyin = ?
                AND hour_of_day = ? AND day_of_week = ?
            ''', (word, pinyin, current_hour, current_dow))

            pattern_matches = cursor.fetchone()[0]
            pattern_factor = 1.0
            if pattern_matches > 0:
                pattern_factor = 1.0 + (pattern_matches / 10.0)

            # 综合计算自适应频率
            adaptive_freq = base_freq * time_factor * trend_factor * pattern_factor

            # 限制在合理范围内
            adaptive_freq = max(self.min_frequency, min(self.max_frequency, adaptive_freq))

            return adaptive_freq

    def get_ranked_candidates(
        self, candidates: List[Tuple[str, int]], pinyin: str
    ) -> List[Tuple[str, float]]:
        """
        根据自适应频率重新排序候选词

        Args:
            candidates: 原始候选词列表 [(word, base_freq), ...]
            pinyin: 拼音

        Returns:
            排序后的候选词列表 [(word, adaptive_freq), ...]
        """
        ranked = []

        for word, base_freq in candidates:
            adaptive_freq = self.get_adaptive_frequency(word, pinyin)
            ranked.append((word, adaptive_freq))

        # 按自适应频率降序排序
        ranked.sort(key=lambda x: x[1], reverse=True)

        return ranked

    def decay_all_frequencies(self):
        """
        对所有词汇执行时间衰减
        定期调用以保持词频的新鲜度
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 对每个词汇应用衰减
            cursor.execute('''
                UPDATE word_stats
                SET base_frequency = base_frequency * ?
                WHERE base_frequency > ?
            ''', (self.decay_rate, self.min_frequency))

            conn.commit()

        # 清空缓存，下次访问时会重新计算
        self.frequency_cache.clear()

        logger.info("Applied time decay to all frequencies")

    def get_top_words(self, limit: int = 20) -> List[Dict]:
        """
        获取高频词汇列表

        Args:
            limit: 返回数量

        Returns:
            词汇信息列表
        """
        ranked_words = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT word, pinyin, base_frequency, total_selections
                FROM word_stats
                ORDER BY base_frequency DESC
                LIMIT ?
            ''', (limit,))

            for word, pinyin, base_freq, total_sel in cursor.fetchall():
                adaptive_freq = self.get_adaptive_frequency(word, pinyin)
                ranked_words.append({
                    'word': word,
                    'pinyin': pinyin,
                    'base_frequency': base_freq,
                    'total_selections': total_sel,
                    'adaptive_frequency': adaptive_freq
                })

        return ranked_words

    def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 总词数
            cursor.execute('SELECT COUNT(*) FROM word_stats')
            total_words = cursor.fetchone()[0]

            # 总选择次数
            cursor.execute('SELECT SUM(total_selections) FROM word_stats')
            total_selections = cursor.fetchone()[0] or 0

            # 最近活动时间
            cursor.execute('''
                SELECT MAX(last_selected) FROM word_stats WHERE last_selected IS NOT NULL
            ''')
            last_activity = cursor.fetchone()[0]

            # 今日选择次数
            today = datetime.now().date()
            cursor.execute('''
                SELECT COUNT(*) FROM selection_timeline
                WHERE DATE(selected_at) = ?
            ''', (today,))
            today_selections = cursor.fetchone()[0]

        return {
            'total_words': total_words,
            'total_selections': total_selections,
            'last_activity': last_activity,
            'today_selections': today_selections,
            'cache_size': len(self.frequency_cache)
        }

    def _get_cache_key(self, word: str, pinyin: str) -> str:
        """生成缓存键"""
        return f"{word}:{pinyin}"

    def clear_cache(self):
        """清空缓存"""
        self.frequency_cache.clear()
        logger.info("Frequency cache cleared")
