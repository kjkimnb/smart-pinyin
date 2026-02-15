"""
词频数据库管理模块
使用SQLite存储词汇和词频
"""

import sqlite3
import os
from config import DB_PATH, INITIAL_FREQUENCY

class WordDatabase:
    """词频数据库类"""

    def __init__(self, db_path=None):
        """初始化数据库连接"""
        self.db_path = db_path or DB_PATH
        self._ensure_db_exists()
        self._init_db()

    def _ensure_db_exists(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_db(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 创建词汇表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    pinyin TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(word, pinyin)
                )
            ''')
            # 创建用户选择历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS selection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    pinyin TEXT NOT NULL,
                    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pinyin ON words(pinyin)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_frequency ON words(frequency DESC)')
            conn.commit()

    def add_word(self, word, pinyin, frequency=None):
        """添加词汇或更新词频"""
        if frequency is None:
            frequency = INITIAL_FREQUENCY

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                # 尝试插入新词
                cursor.execute(
                    'INSERT INTO words (word, pinyin, frequency) VALUES (?, ?, ?)',
                    (word, pinyin, frequency)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # 词已存在，更新词频
                cursor.execute(
                    'UPDATE words SET frequency = frequency + ? WHERE word = ? AND pinyin = ?',
                    (frequency, word, pinyin)
                )
                conn.commit()
                return False

    def get_candidates(self, pinyin, limit=10):
        """获取候选词（按词频排序）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT word, frequency FROM words
                WHERE pinyin = ?
                ORDER BY frequency DESC, word ASC
                LIMIT ?
            ''', (pinyin, limit))
            return cursor.fetchall()

    def update_frequency(self, word, pinyin, increment=1):
        """更新词频"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE words SET frequency = frequency + ? WHERE word = ? AND pinyin = ?',
                (increment, word, pinyin)
            )
            conn.commit()
            return cursor.rowcount > 0

    def record_selection(self, word, pinyin):
        """记录用户选择"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO selection_history (word, pinyin) VALUES (?, ?)',
                (word, pinyin)
            )
            conn.commit()

    def get_word_count(self):
        """获取词汇总数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM words')
            return cursor.fetchone()[0]

    def initialize_common_words(self):
        """初始化常用词库"""
        common_words = [
            # 常用单字
            ("我", "wo"), ("你", "ni"), ("他", "ta"), ("她", "ta"), ("它", "ta"),
            ("是", "shi"), ("的", "de"), ("在", "zai"), ("了", "le"), ("不", "bu"),
            ("有", "you"), ("和", "he"), ("就", "jiu"), ("都", "dou"), ("也", "ye"),
            ("人", "ren"), ("好", "hao"), ("这", "zhe"), ("那", "na"), ("吗", "ma"),
            # 常用词
            ("我们", "wo men"), ("你们", "ni men"), ("他们", "ta men"),
            ("什么", "shen me"), ("怎么", "zen me"), ("可以", "ke yi"),
            ("因为", "yin wei"), ("所以", "suo yi"), ("但是", "dan shi"),
            ("工作", "gong zuo"), ("学习", "xue xi"), ("时间", "shi jian"),
            ("今天", "jin tian"), ("明天", "ming tian"), ("昨天", "zuo tian"),
            ("开始", "kai shi"), ("结束", "jie shu"), ("完成", "wan cheng"),
            ("问题", "wen ti"), ("答案", "da an"), ("方法", "fang fa"),
            ("非常", "fei chang"), ("真的", "zhen de"), ("应该", "ying gai"),
            ("程序", "cheng xu"), ("代码", "dai ma"), ("开发", "kai fa"),
            ("输入", "shu ru"), ("输出", "shu chu"), ("数据", "shu ju"),
        ]

        added_count = 0
        for word, pinyin in common_words:
            if self.add_word(word, pinyin, frequency=10):
                added_count += 1

        return added_count

    def decay_frequencies(self, decay_factor=0.9):
        """衰减所有词频（避免高频词一直占据首位）"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 使用INTEGER类型，需要转换
            cursor.execute('UPDATE words SET frequency = CAST(frequency * ? AS INTEGER) WHERE frequency > 1',
                          (decay_factor,))
            conn.commit()
            return cursor.rowcount
