#!/usr/bin/env python3
"""
生成输入法界面截图 - 修复后的正确排序
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
    ("西安", "xi an", 200),
    ("西", "xi", 250),
    ("东南大学", "dong nan da xue", 180),
    ("东南", "dong nan", 220),
    ("东", "dong", 280),
]

for word, pinyin, freq in test_words:
    db.add_word(word, pinyin, freq)

# 初始化
engine = PinyinEngineEnhanced()
manager = CandidateManager(db)

# 绘制标题
draw.text((50, 40), 'Smart Pinyin - 智能中文输入法', fill='#333', font=title_font)
draw.text((50, 70), '修复后：长度优先 + 词频其次', fill='#666', font=small_font)

# 绘制说明
draw.text((50, 100), '测试1: xi\'an (手动分词)', fill='#333', font=content_font)
draw.text((50, 120), '测试2: dongnandaxue (自动分词)', fill='#333', font=content_font)

# 测试 xi'an
input_pinyin1 = "xi'an"
candidates1 = manager.generate_candidates(input_pinyin1)

# 绘制候选词窗口1
candidate_box1 = (100, 140, 700, 220)
draw.rectangle(candidate_box1, fill='white', outline='#ddd', width=1)

# 第一行：拼音
draw.rectangle([100, 140, 700, 180], fill='#667eea')
draw.text((130, 158), input_pinyin1, fill='white', font=content_font)
draw.text((620, 158), '手动分词', fill='white', font=small_font)

# 第二行：候选字（横向排列，不显示拼音）
y_offset1 = 200
x_start1 = 130
spacing1 = 150

for idx, (word, freq) in enumerate(candidates1):
    x_pos = x_start1 + idx * spacing1
    
    # 选中第一个
    if idx == 0:
        # 数字标号
        draw.text((x_pos, y_offset1), '1.', fill='#667eea', font=number_font)
        # 候选字（更大）
        word_font = ImageFont.truetype(font_path, 28)
        draw.text((x_pos + 25, y_offset1 - 5), word, fill='#333', font=word_font)
        # 选中标识
        draw.rectangle([x_pos - 5, y_offset1 - 10, x_pos + 115, y_offset + 40], outline='#667eea', width=2)
    else:
        # 数字标号
        draw.text((x_pos, y_offset1), f'{idx+1}.', fill='#666', font=number_font)
        # 候选字
        draw.text((x_pos + 25, y_offset1 - 5), word, fill='#666', font=content_font)

# 测试 dongnandaxue
input_pinyin2 = "dongnandaxue"
candidates2 = manager.generate_candidates(input_pinyin2)

# 绘制候选词窗口2
candidate_box2 = (100, 240, 700, 320)
draw.rectangle(candidate_box2, fill='white', outline='#ddd', width=1)

# 第一行：拼音
draw.rectangle([100, 240, 700, 280], fill='#667eea')
draw.text((130, 258), input_pinyin2, fill='white', font=content_font)
draw.text((620, 258), '自动分词', fill='white', font=small_font)

# 第二行：候选字（横向排列，不显示拼音）
y_offset2 = 300
x_start2 = 130
spacing2 = 150

for idx, (word, freq) in enumerate(candidates2):
    x_pos = x_start2 + idx * spacing2
    
    # 选中第一个
    if idx == 0:
        # 数字标号
        draw.text((x_pos, y_offset2), '1.', fill='#667eea', font=number_font)
        # 候选字（更大）
        word_font = ImageFont.truetype(font_path, 28)
        draw.text((x_pos + 25, y_offset2 - 5), word, fill='#333', font=word_font)
        # 选中标识
        draw.rectangle([x_pos - 5, y_offset2 - 10, x_pos + 115, y_offset + 40], outline='#667eea', width=2)
    else:
        # 数字标号
        draw.text((x_pos, y_offset2), f'{idx+1}.', fill='#666', font=number_font)
        # 候选字
        draw.text((x_pos + 25, y_offset2 - 5), word, fill='#666', font=content_font)

# 绘制状态栏
status_bar = (50, 340, 750, 370)
draw.rectangle(status_bar, fill='#f9f9f9')
draw.text((70, 355), '🟢 排序已修复', fill='#666', font=small_font)
draw.text((200, 355), f'输入1: {input_pinyin1}', fill='#666', font=small_font)
draw.text((400, 355), f'候选词1: {len(candidates1)}个', fill='#666', font=small_font)
draw.text((550, 355), f'输入2: {input_pinyin2}', fill='#666', font=small_font)
draw.text((680, 355), f'候选词2: {len(candidates2)}个', fill='#666', font=small_font)

# 保存图片
img.save('/root/dev/input-method/screenshot-fixed.png', 'PNG', quality=95)
print('✅ 修复后截图已生成: /root/dev/input-method/screenshot-fixed.png')
print(f'   输入1: {input_pinyin1}')
print(f'   候选词1: {[(word, freq) for word, freq in candidates1]}')
print(f'   输入2: {input_pinyin2}')
print(f'   候选词2: {[(word, freq) for word, freq in candidates2]}')
