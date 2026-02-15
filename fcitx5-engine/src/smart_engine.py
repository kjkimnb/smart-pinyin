"""
智能输入法引擎
集成自适应词频和上下文关联的高级版本
"""

import dbus
import dbus.service
import logging
from pathlib import Path
import sys
import json
from typing import List, Tuple, Optional, Dict

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from word_database import WordDatabase
from pinyin_engine import PinyinEngine
from candidate_manager import CandidateManager
from config import DB_PATH
from context_engine import ContextEngine
from adaptive_frequency import AdaptiveFrequencyManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/fcitx5-chinese-smart-engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SmartChineseInputEngine(dbus.service.Object):
    """智能中文输入法引擎"""

    BUS_NAME = 'org.fcitx.SmartChineseEngine'
    OBJECT_PATH = '/org/fcitx/SmartChineseEngine'
    INTERFACE = 'org.fcitx.SmartChineseEngine'

    def __init__(self):
        """初始化智能引擎"""
        self.bus_name = dbus.service.BusName(self.BUS_NAME, bus=dbus.SessionBus())
        super().__init__(self.bus_name, self.OBJECT_PATH)

        logger.info("Initializing Smart Chinese Input Engine...")

        # 初始化核心组件
        self.db = WordDatabase()
        self.pinyin_engine = PinyinEngine()
        self.candidate_manager = CandidateManager(self.db)

        # 初始化智能组件
        self.context_engine = ContextEngine(DB_PATH)
        self.frequency_manager = AdaptiveFrequencyManager(DB_PATH)

        # 当前输入状态
        self.current_input = ""
        self.current_candidates: List[Tuple[str, float]] = []
        self.composing = False
        self.candidate_page = 0

        # 配置
        self.config = self._load_config()

        logger.info("Smart Chinese Input Engine initialized successfully")

    def _load_config(self) -> dict:
        """加载配置"""
        config_path = Path.home() / '.config' / 'fcitx5-chinese' / 'config.json'
        default_config = {
            'max_candidates': 10,
            'page_size': 5,
            'enable_context': True,  # 启用上下文关联
            'enable_adaptive': True,  # 启用自适应词频
            'context_weight': 1.5,  # 上下文关联权重
            'adaptive_weight': 1.0,  # 自适应词频权重
            'base_weight': 0.5,  # 基础词频权重
        }

        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Failed to load config: {e}, using defaults")

        return default_config

    @dbus.service.method(INTERFACE, in_signature='s', out_signature='aa{sv}')
    def GetCandidates(self, pinyin: str) -> List[dbus.Dictionary]:
        """
        获取智能候选词

        综合考虑：
        1. 基础词频
        2. 自适应学习（时间衰减、时间模式）
        3. 上下文关联（N-gram）

        Args:
            pinyin: 拼音输入

        Returns:
            候选词列表，每个候选词是字典类型
        """
        try:
            logger.info(f"Getting smart candidates for: {pinyin}")

            # 标准化拼音
            normalized = self.pinyin_engine.normalize_pinyin(pinyin)
            self.current_input = normalized

            # 获取基础候选词
            base_candidates = self.candidate_manager.generate_candidates(normalized)

            # 获取上下文关联候选词
            context_candidates = []
            if self.config['enable_context']:
                context_candidates = self.context_engine.get_contextual_candidates(
                    normalized, limit=5
                )

            # 合并候选词并计算综合分数
            merged_candidates = self._merge_and_score_candidates(
                base_candidates, context_candidates
            )

            # 排序并限制数量
            merged_candidates.sort(key=lambda x: x[1], reverse=True)
            merged_candidates = merged_candidates[:self.config['max_candidates']]

            self.current_candidates = merged_candidates

            # 转换为DBus字典格式
            result = []
            for idx, (word, score) in enumerate(merged_candidates):
                candidate = {
                    'index': idx,
                    'word': word,
                    'pinyin': normalized,
                    'score': round(score, 4)
                }
                result.append(dbus.Dictionary(candidate, signature='sv'))

            logger.info(f"Generated {len(result)} smart candidates")
            return result

        except Exception as e:
            logger.error(f"Error getting smart candidates: {e}", exc_info=True)
            return []

    def _merge_and_score_candidates(
        self,
        base_candidates: List[Tuple[str, int]],
        context_candidates: List[Tuple[str, float]]
    ) -> List[Tuple[str, float]]:
        """
        合并候选词并计算综合分数

        Args:
            base_candidates: 基础候选词 [(word, base_freq), ...]
            context_candidates: 上下文候选词 [(word, context_score), ...]

        Returns:
            合并后的候选词 [(word, combined_score), ...]
        """
        merged = {}

        # 处理基础候选词
        for word, base_freq in base_candidates:
            # 计算自适应分数
            adaptive_score = 0
            if self.config['enable_adaptive']:
                adaptive_score = self.frequency_manager.get_adaptive_frequency(
                    word, self.current_input
                )

            # 综合分数 = 基础分数 * 自适应权重
            combined = base_freq * self.config['base_weight'] + adaptive_score * self.config['adaptive_weight']
            merged[word] = combined

        # 处理上下文候选词
        for word, context_score in context_candidates:
            if word in merged:
                # 已存在，增加上下文加分
                merged[word] += context_score * self.config['context_weight']
            else:
                # 不存在，直接使用上下文分数
                merged[word] = context_score * self.config['context_weight']

        # 转换为列表
        return [(word, score) for word, score in merged.items()]

    @dbus.service.method(INTERFACE, in_signature='i', out_signature='s')
    def SelectCandidate(self, index: int) -> str:
        """
        选择候选词（智能学习）

        Args:
            index: 候选词索引

        Returns:
            选中的词
        """
        try:
            logger.info(f"Selecting smart candidate at index: {index}")

            if index < 0 or index >= len(self.current_candidates):
                logger.warning(f"Invalid index: {index}")
                return ""

            word, score = self.current_candidates[index]

            # 更新基础词频
            self.candidate_manager.select_candidate(index, record=False)

            # 记录到自适应频率管理器
            if self.config['enable_adaptive']:
                self.frequency_manager.record_selection(word, self.current_input)

            # 更新上下文引擎
            if self.config['enable_context']:
                self.context_engine.update_context(word)

            # 清空当前输入
            self.current_input = ""
            self.composing = False

            logger.info(f"Selected: {word}")
            return word

        except Exception as e:
            logger.error(f"Error selecting smart candidate: {e}", exc_info=True)
            return ""

    @dbus.service.method(INTERFACE, in_signature='s', out_signature='s')
    def AddWord(self, word: str) -> str:
        """
        添加自定义词汇

        Args:
            word: 要添加的词汇

        Returns:
            添加的词汇的拼音
        """
        try:
            logger.info(f"Adding custom word: {word}")

            # 添加到数据库
            pinyin = self.candidate_manager.add_custom_word(word)

            # 记录到自适应管理器（初始频率）
            if pinyin and self.config['enable_adaptive']:
                self.frequency_manager.record_selection(word, pinyin)

            # 如果当前正在输入，刷新候选词
            if self.current_input:
                self.GetCandidates(self.current_input)

            logger.info(f"Added word: {word} with pinyin: {pinyin}")
            return pinyin or ""

        except Exception as e:
            logger.error(f"Error adding word: {e}", exc_info=True)
            return ""

    @dbus.service.method(INTERFACE, in_signature='s', out_signature='b')
    def SetComposing(self, pinyin: str) -> bool:
        """设置组合状态"""
        try:
            self.current_input = pinyin
            self.composing = bool(pinyin)
            logger.debug(f"Composing: {self.composing}, input: {pinyin}")
            return True

        except Exception as e:
            logger.error(f"Error setting composing: {e}", exc_info=True)
            return False

    @dbus.service.method(INTERFACE, in_signature='', out_signature='b')
    def Clear(self) -> bool:
        """清空当前输入"""
        try:
            self.current_input = ""
            self.current_candidates = []
            self.composing = False
            self.candidate_page = 0
            logger.info("Cleared current input")
            return True

        except Exception as e:
            logger.error(f"Error clearing: {e}", exc_info=True)
            return False

    @dbus.service.method(INTERFACE, in_signature='', out_signature='aa{sv}')
    def GetStatus(self) -> List[dbus.Dictionary]:
        """获取引擎状态"""
        try:
            context_string = self.context_engine.get_context_string()
            freq_stats = self.frequency_manager.get_statistics()

            status = [
                {'composing': self.composing},
                {'current_input': self.current_input},
                {'candidate_count': len(self.current_candidates)},
                {'context_string': context_string},
                {'total_words': freq_stats['total_words']},
                {'total_selections': freq_stats['total_selections']},
                {'today_selections': freq_stats['today_selections']},
                {'cache_size': freq_stats['cache_size']}
            ]

            return [dbus.Dictionary(s, signature='sv') for s in status]

        except Exception as e:
            logger.error(f"Error getting status: {e}", exc_info=True)
            return []

    @dbus.service.method(INTERFACE, in_signature='', out_signature='aa{sv}')
    def GetTopWords(self, limit: int = 20) -> List[dbus.Dictionary]:
        """获取高频词汇"""
        try:
            top_words = self.frequency_manager.get_top_words(limit)
            return [dbus.Dictionary(word, signature='sv') for word in top_words]
        except Exception as e:
            logger.error(f"Error getting top words: {e}", exc_info=True)
            return []

    @dbus.service.method(INTERFACE, in_signature='', out_signature='aa{sv}')
    def GetContextStats(self, n: int = 2, limit: int = 10) -> List[dbus.Dictionary]:
        """获取上下文统计"""
        try:
            stats = self.context_engine.get_ngram_stats(n, limit)
            return [dbus.Dictionary(s, signature='sv') for s in stats]
        except Exception as e:
            logger.error(f"Error getting context stats: {e}", exc_info=True)
            return []

    @dbus.service.method(INTERFACE, in_signature='', out_signature='b')
    def ClearContext(self) -> bool:
        """清空上下文"""
        try:
            self.context_engine.clear_context()
            logger.info("Context cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing context: {e}", exc_info=True)
            return False

    @dbus.service.method(INTERFACE, in_signature='', out_signature='b')
    def DecayFrequencies(self) -> bool:
        """执行词频衰减"""
        try:
            self.frequency_manager.decay_all_frequencies()
            self.frequency_manager.clear_cache()
            logger.info("Frequencies decayed")
            return True
        except Exception as e:
            logger.error(f"Error decaying frequencies: {e}", exc_info=True)
            return False

    @dbus.service.method(INTERFACE, in_signature='', out_signature='b')
    def ReloadConfig(self) -> bool:
        """重新加载配置"""
        try:
            self.config = self._load_config()
            logger.info("Configuration reloaded")
            return True
        except Exception as e:
            logger.error(f"Error reloading config: {e}", exc_info=True)
            return False


def main():
    """主函数"""
    try:
        from dbus.mainloop.glib import DBusGMainLoop
        from gi.repository import GLib

        # 设置DBus主循环
        DBusGMainLoop(set_as_default=True)

        # 创建引擎实例
        engine = SmartChineseInputEngine()

        logger.info("Smart Chinese Input Engine is running...")
        logger.info("DBus service:")
        logger.info(f"  Bus Name: {SmartChineseInputEngine.BUS_NAME}")
        logger.info(f"  Object Path: {SmartChineseInputEngine.OBJECT_PATH}")
        logger.info(f"  Interface: {SmartChineseInputEngine.INTERFACE}")

        # 运行主循环
        loop = GLib.MainLoop()
        loop.run()

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
