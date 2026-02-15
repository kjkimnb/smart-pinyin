"""
命令行界面模块
处理用户交互和输入输出
"""

from candidate_manager import CandidateManager
from word_database import WordDatabase
from pinyin_engine import PinyinEngine
from config import PAGE_SIZE
import sys
import time

class InputMethodCLI:
    """输入法命令行界面"""

    def __init__(self):
        """初始化CLI"""
        self.db = WordDatabase()
        self.manager = CandidateManager(self.db)
        self.pinyin_engine = PinyinEngine()
        self.output_buffer = []

        # 初始化词库
        print("正在初始化词库...")
        word_count = self.db.initialize_common_words()
        print(f"已初始化 {word_count} 个常用词汇\n")

    def print_welcome(self):
        """打印欢迎信息"""
        print("=" * 50)
        print("    中文输入法 - 命令行版")
        print("=" * 50)
        print("\n使用说明:")
        print("  输入拼音：直接输入拼音（如：wo men）")
        print("  选择词汇：输入数字选择候选词")
        print("  添加词汇：输入 +汉字 添加新词（如：+你好）")
        print("  翻页：使用 < (上一页) 和 > (下一页)")
        print("  确认：输入 Enter 或 . 提交当前输入")
        print("  退格：输入 Backspace 或删除最后的拼音")
        print("  清空：输入 ! 清空当前输入")
        print("  退出：输入 q 或 quit 退出")
        print("\n" + "=" * 50 + "\n")

    def print_candidates(self, show_all=False):
        """
        显示候选词

        Args:
            show_all: 是否显示所有候选词
        """
        if not self.manager.current_candidates:
            return

        if show_all:
            candidates = self.manager.current_candidates
            start = 0
            end = len(candidates)
        else:
            candidates = self.manager.get_current_page(PAGE_SIZE)
            start = self.manager.current_page * PAGE_SIZE + 1
            end = start + len(candidates)

        print("\n候选词:")
        for i, (word, freq) in enumerate(candidates, start=start):
            print(f"  {i}. {word} (词频: {freq})")

        # 显示分页信息
        if not show_all:
            current_page, total_pages = self.manager.get_page_info(PAGE_SIZE)
            if total_pages > 1:
                print(f"\n  第 {current_page}/{total_pages} 页 (使用 < > 翻页)")

    def run(self):
        """运行主循环"""
        self.print_welcome()

        input_pinyin = ""
        selected_words = []

        try:
            while True:
                # 显示当前状态
                if selected_words:
                    print(f"\n已选: {' '.join(selected_words)}", end='')
                if input_pinyin:
                    print(f" | 拼音: {input_pinyin}", end='')
                print()

                # 显示候选词
                self.print_candidates()

                # 获取用户输入
                try:
                    user_input = input("\n>>> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n\n再见！")
                    break

                if not user_input:
                    # 空输入，提交当前选择
                    if selected_words:
                        result = ''.join(selected_words)
                        print(f"\n输出: {result}")
                        selected_words = []
                        input_pinyin = ""
                        self.manager.clear()
                    continue

                # 处理命令
                if user_input.lower() in ['q', 'quit', 'exit']:
                    print("\n再见！")
                    break

                elif user_input == '!':
                    # 清空当前输入
                    input_pinyin = ""
                    selected_words = []
                    self.manager.clear()

                elif user_input == '.':
                    # 提交当前选择
                    if selected_words:
                        result = ''.join(selected_words)
                        print(f"\n输出: {result}")
                        selected_words = []
                        input_pinyin = ""
                        self.manager.clear()

                elif user_input == '<':
                    # 上一页
                    if self.manager.prev_page(PAGE_SIZE):
                        continue
                    print("已经是第一页了")

                elif user_input == '>':
                    # 下一页
                    if self.manager.next_page(PAGE_SIZE):
                        continue
                    print("已经是最后一页了")

                elif user_input.startswith('+'):
                    # 添加自定义词汇
                    word = user_input[1:].strip()
                    if word:
                        if self.pinyin_engine.is_pinyin(word):
                            # 用户输入的是拼音，提示需要汉字
                            print("请输入要添加的汉字，不是拼音")
                        else:
                            pinyin = self.manager.add_custom_word(word)
                            print(f"已添加词汇: {word} (拼音: {pinyin})")
                            # 重新生成候选词
                            self.manager.generate_candidates(input_pinyin)

                elif user_input.isdigit():
                    # 选择候选词
                    index = int(user_input) - 1
                    selected = self.manager.select_candidate(index)
                    if selected:
                        selected_words.append(selected)
                        input_pinyin = ""
                        self.manager.clear()
                    else:
                        print("无效的选择")

                elif user_input.lower() == 'back' or user_input == 'bs':
                    # 退格
                    if input_pinyin:
                        input_pinyin = input_pinyin[:-1]
                        if input_pinyin:
                            self.manager.generate_candidates(input_pinyin)
                        else:
                            self.manager.clear()
                    elif selected_words:
                        # 如果拼音为空，退格删除已选的词
                        selected_words.pop()

                else:
                    # 处理拼音输入
                    if self.pinyin_engine.is_pinyin(user_input):
                        # 添加空格分隔（如果是连续输入）
                        if input_pinyin:
                            input_pinyin += ' '
                        input_pinyin += user_input

                        # 生成候选词
                        candidates = self.manager.generate_candidates(input_pinyin)

                        if not candidates:
                            print(f"\n没有找到拼音 '{input_pinyin}' 的候选词")
                            print(f"提示：使用 +汉字 添加新词，或使用 ! 清空输入")
                    else:
                        # 不是拼音，直接输出
                        print(f"\n直接输出: {user_input}")
                        if selected_words:
                            print(f"已选: {''.join(selected_words)}")
                        selected_words = []
                        input_pinyin = ""
                        self.manager.clear()

        except KeyboardInterrupt:
            print("\n\n程序已中断")
        except Exception as e:
            print(f"\n发生错误: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    cli = InputMethodCLI()
    cli.run()

if __name__ == "__main__":
    main()
