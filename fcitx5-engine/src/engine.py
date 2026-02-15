"""
Fcitx5中文输入法引擎
基于Python实现，通过DBus与Fcitx5通信
"""

import dbus
import dbus.service
import logging
from pathlib import Path
import sys
import json
from typing import List, Tuple, Optional

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from word_database import WordDatabase
from pinyin_engine import PinyinEngine
from candidate_manager import CandidateManager
from config import DB_PATH, MAX_CANDIDATES

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/fcitx5-chinese-engine.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChineseInputEngine(dbus.service.Object):
    """中文输入法引擎DBus服务"""

    BUS_NAME = 'org.fcitx.ChineseEngine'
    OBJECT_PATH = '/org/fcitx/ChineseEngine'
    INTERFACE = 'org.fcitx.ChineseEngine'

    def __init__(self):
        """初始化引擎"""
        self.bus_name = dbus.service.BusName(self.BUS_NAME, bus=dbus.SessionBus())
        super().__init__(self.bus_name, self.OBJECT_PATH)

        logger.info("Initializing Chinese Input Engine...")

        # 初始化核心组件
        self.db = WordDatabase()
        self.pinyin_engine = PinyinEngine()
        self.candidate_manager = CandidateManager(self.db)

        # 当前输入状态
        self.current_input = ""
        self.current_candidates: List[Tuple[str, int]] = []
        self.composing = False
        self.candidate_page = 0
        self.candidate_window_visible = False

        # 配置
        self.config = self._load_config()

        logger.info("Chinese Input Engine initialized successfully")

    def _load_config(self) -> dict:
        """加载配置"""
        config_path = Path.home() / '.config' / 'fcitx5-chinese' / 'config.json'
        default_config = {
            'max_candidates': 10,
            'page_size': 5,
            'auto_select': True,
            'show_pinyin': True,
            'fuzzy_match': True
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
        获取候选词

        Args:
            pinyin: 拼音输入

        Returns:
            候选词列表，每个候选词是字典类型
        """
        try:
            logger.info(f"Getting candidates for: {pinyin}")

            # 标准化拼音
            normalized = self.pinyin_engine.normalize_pinyin(pinyin)
            self.current_input = normalized

            # 生成候选词
            candidates = self.candidate_manager.generate_candidates(normalized)
            self.current_candidates = candidates

            # 转换为DBus字典格式
            result = []
            for idx, (word, freq) in enumerate(candidates):
                candidate = {
                    'index': idx,
                    'word': word,
                    'pinyin': normalized,
                    'frequency': freq
                }
                result.append(dbus.Dictionary(candidate, signature='sv'))

            logger.info(f"Generated {len(result)} candidates")
            return result

        except Exception as e:
            logger.error(f"Error getting candidates: {e}", exc_info=True)
            return []

    @dbus.service.method(INTERFACE, in_signature='i', out_signature='s')
    def SelectCandidate(self, index: int) -> str:
        """
        选择候选词

        Args:
            index: 候选词索引

        Returns:
            选中的词
        """
        try:
            logger.info(f"Selecting candidate at index: {index}")

            if index < 0 or index >= len(self.current_candidates):
                logger.warning(f"Invalid index: {index}")
                return ""

            # 选择候选词（会自动更新词频）
            word = self.candidate_manager.select_candidate(index)

            # 清空当前输入
            self.current_input = ""
            self.composing = False

            logger.info(f"Selected: {word}")
            return word

        except Exception as e:
            logger.error(f"Error selecting candidate: {e}", exc_info=True)
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

            # 如果当前正在输入，刷新候选词
            if self.current_input:
                self.candidate_manager.generate_candidates(self.current_input)

            logger.info(f"Added word: {word} with pinyin: {pinyin}")
            return pinyin or ""

        except Exception as e:
            logger.error(f"Error adding word: {e}", exc_info=True)
            return ""

    @dbus.service.method(INTERFACE, in_signature='s', out_signature='b')
    def SetComposing(self, pinyin: str) -> bool:
        """
        设置组合状态（正在输入）

        Args:
            pinyin: 当前拼音

        Returns:
            是否成功
        """
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
        """
        清空当前输入

        Returns:
            是否成功
        """
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
    def GetPage(self) -> List[dbus.Dictionary]:
        """
        获取当前页候选词

        Returns:
            当前页候选词列表
        """
        try:
            page_size = self.config['page_size']
            candidates = self.candidate_manager.get_current_page(page_size)

            result = []
            for idx, (word, freq) in enumerate(candidates):
                candidate = {
                    'index': idx + (self.candidate_page * page_size),
                    'word': word,
                    'pinyin': self.current_input,
                    'frequency': freq
                }
                result.append(dbus.Dictionary(candidate, signature='sv'))

            return result

        except Exception as e:
            logger.error(f"Error getting page: {e}", exc_info=True)
            return []

    @dbus.service.method(INTERFACE, in_signature='', out_signature='b')
    def NextPage(self) -> bool:
        """
        翻到下一页

        Returns:
            是否成功翻页
        """
        try:
            page_size = self.config['page_size']
            success = self.candidate_manager.next_page(page_size)
            if success:
                self.candidate_page += 1
                logger.info(f"Next page: {self.candidate_page}")
            return success

        except Exception as e:
            logger.error(f"Error next page: {e}", exc_info=True)
            return False

    @dbus.service.method(INTERFACE, in_signature='', out_signature='b')
    def PrevPage(self) -> bool:
        """
        翻到上一页

        Returns:
            是否成功翻页
        """
        try:
            page_size = self.config['page_size']
            success = self.candidate_manager.prev_page(page_size)
            if success:
                self.candidate_page -= 1
                logger.info(f"Prev page: {self.candidate_page}")
            return success

        except Exception as e:
            logger.error(f"Error prev page: {e}", exc_info=True)
            return False

    @dbus.service.method(INTERFACE, in_signature='', out_signature='aa{sv}')
    def GetStatus(self) -> List[dbus.Dictionary]:
        """
        获取引擎状态

        Returns:
            状态信息
        """
        try:
            page_size = self.config['page_size']
            current_page, total_pages = self.candidate_manager.get_page_info(page_size)

            status = [
                {'composing': self.composing},
                {'current_input': self.current_input},
                {'candidate_count': len(self.current_candidates)},
                {'current_page': current_page},
                {'total_pages': total_pages},
                {'database_word_count': self.db.get_word_count()}
            ]

            return [dbus.Dictionary(s, signature='sv') for s in status]

        except Exception as e:
            logger.error(f"Error getting status: {e}", exc_info=True)
            return []

    @dbus.service.method(INTERFACE, in_signature='', out_signature='b')
    def ReloadConfig(self) -> bool:
        """
        重新加载配置

        Returns:
            是否成功
        """
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
        engine = ChineseInputEngine()

        logger.info("Chinese Input Engine is running...")
        logger.info("DBus service:")
        logger.info(f"  Bus Name: {ChineseInputEngine.BUS_NAME}")
        logger.info(f"  Object Path: {ChineseInputEngine.OBJECT_PATH}")
        logger.info(f"  Interface: {ChineseInputEngine.INTERFACE}")

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
