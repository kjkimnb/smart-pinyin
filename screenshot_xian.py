#!/usr/bin/env python3
"""
生成输入法界面截图 - 演示 xian 和 xi'an
"""

from PIL import Image, ImageDraw, ImageFont
from word_database import WordDatabase
from pinyin_engine_enhanced import PinyinEngineEnhanced
from candidate_manager import CandidateManager

# 创建画布
width, height = 800, 500
img = Image.new('RGB', (width, height), color='#f5f5f5')
draw = ImageDraw.Draw(img)

# 使用中文字体
font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'

try:
    title_font = ImageFont.truetype(font_path, 24)
    content_font = ImageFont.truetype(font_path, 18)
    small_font = ImageFont.truetype(font_path, 14)
    number_font = ImageFont.truetype(font_path, 12)
except:
    title_font = ImageFont.load_default()
    content_font = ImageFont.load_default()
    small_font = ImageFont.load_default()
    number_font = ImageFont.load_default()

# 添加测试词汇
db = WordDatabase()
test_words = [
    ("西", "xi", 90),
    ("先", "xian", 85),
    ("西安", "xi an", 80),
    ("仙", "xian", 75),
    ("县", "xian", 70),
    ("显", "xian", 65),
    ("线", "xian", 60),
    ("现", "xian", 55),
]

for word, pinyin, freq in test_words:
    db.add_word(word, pinyin, freq)

print("已添加测试词汇")

# 绘制标题
draw.text((50, 40), 'Smart Pinyin - 智能中文输入法', fill='#333', font=title_font)
draw.text((50, 70), '分词功能演示：xian vs xi\'an', fill='#666', font=small_font)

# 绘制编辑框（模拟文本编辑器）
edit_box = (50, 120, 750, 280)
draw.rectangle(edit_box, outline='#e0e0e0', width=2)
draw.rectangle([edit_box[0]+2, edit_box[1]+2, edit_box[2]-2, edit_box[3]-2], fill='#ffffff')

# 绘制文本
draw.text((70, 145), '今天', fill='#333', font=content_font)
draw.rectangle([210, 142, 290, 165], outline='#2196F3', width=2)
draw.text((220, 145), "xi'an", fill='#2196F3', font=content_font)

# 绘制光标
draw.rectangle([298, 145, 300, 165], fill='#2196F3')

# 获取候选词
engine = PinyinEngineEnhanced()
manager = CandidateManager(db)

# 测试 xi'an (手动分词）
input_pinyin = "xi'an"
candidates = manager.generate_candidates(input_pinyin)

print(f"输入: {input_pinyin}")
print(f"候选词数量: {len(candidates)}")
for idx, (word, freq) in enumerate(candidates[:5], 1):
    print(f"  {idx}. {word} - 词频: {freq}")

# 绘制候选词窗口
candidate_box = (100, 300, 700, 420)
draw.rectangle(candidate_box, fill='white', outline='#ddd', width=1)

# 第一行：拼音
draw.rectangle([100, 300, 700, 340], fill='#667eea')
draw.text((130, 318), input_pinyin, fill='white', font=content_font)
draw.text((620, 318), '手动分词', fill='white', font=small_font)

# 第二行：候选字（横向排列，不显示拼音）
y_offset = 360
x_start = 130
spacing = 110

# 如果没有候选词，显示提示
if not candidates:
    draw.text((x_start, y_offset), "暂无候选词", fill='#999', font=content_font)
else:
    for idx, (word, freq) in enumerate(candidates[:5]):
        x_pos = x_start + idx * spacing
        
        # 选中第一个
        if idx == 0:
            # 数字标号
            draw.text((x_pos, y_offset), '1.', fill='#2196F3', font=small_font)
            # 候选字（更大）
            word_font = ImageFont.truetype(font_path, 28)
            draw.text((x_pos + 25, y_offset - 5), word, fill='#333', font=word_font)
            # 选中标识
            draw.rectangle([x_pos - 5, y_offset - 10, x_pos + 85, y_offset + 40], outline='#2196F3', width=2)
        else:
            # 数字标号
            draw.text((x_pos, y_offset), f'{idx+1}.', fill='#666', font=small_font)
            # 候选字
            draw.text((x_pos + 25, y_offset - 5), word, fill='#666', font=content_font)

# 绘制状态栏
status_bar = (50, 440, 750, 470)
draw.rectangle(status_bar, fill='#f9f9f9')
draw.text((70, 455), '🟢 引擎运行中', fill='#666', font=small_font)
draw.text((250, 455), f'输入: {input_pinyin}', fill='#666', font=small_font)
draw.text((450, 455), f'分词: {engine.smart_split_pinyin(input_pinyin)}', fill='#666', font=small_font)
draw.text((650, 455), f'候选词: {len(candidates)}个', fill='#666', font=small_font)

# 保存图片
img.save('/root/dev/input-method/screenshot-xian.png', 'PNG', quality=95)
print('\n✅ 截图已生成: /root/dev/input-method/screenshot-xian.png')
print(f'   输入: {input_pinyin}')
print(f'   候选词: {len(candidates)}个')
