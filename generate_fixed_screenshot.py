#!/usr/bin/env python3
"""
重新生成正确的截图 - 展示修复后的排序效果
"""

from PIL import Image, ImageDraw, ImageFont
from word_database import WordDatabase
from pinyin_engine_enhanced import PinyinEngineEnhanced
from candidate_manager import CandidateManager
import sqlite3

# 创建画布
width, height = 900, 600
img = Image.new('RGB', (width, height), color='#f5f5f5')
draw = ImageDraw.Draw(img)

# 使用中文字体
font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'

try:
    title_font = ImageFont.truetype(font_path, 26)
    content_font = ImageFont.truetype(font_path, 20)
    small_font = ImageFont.truetype(font_path, 14)
    number_font = ImageFont.truetype(font_path, 12)
except:
    title_font = ImageFont.load_default()
    content_font = ImageFont.load_default()
    small_font = ImageFont.load_default()
    number_font = ImageFont.load_default()

# 初始化
db = WordDatabase()
engine = PinyinEngineEnhanced()
manager = CandidateManager(db)

# 添加测试词汇（使用更明显的词频差异）
test_words = [
    ("西安", "xi an", 90),      # 2字，词频90
    ("西", "xi", 80),          # 1字，词频80
    ("东南大学", "dong nan da xue", 85),  # 4字，词频85
    ("东南", "dong nan", 88),         # 2字，词频88
    ("东", "dong", 95),          # 1字，词频95
]

for word, pinyin, freq in test_words:
    db.add_word(word, pinyin, freq)

# 绘制标题
draw.text((50, 30), 'Smart Pinyin - 智能中文输入法', fill='#333', font=title_font)
draw.text((50, 65), '排序修复：长度优先 + 词频其次', fill='#666', font=small_font)

# 测试1: xi'an
input_pinyin1 = "xi'an"
candidates1 = manager.generate_candidates(input_pinyin1)

draw.text((50, 110), '测试1: xi\'an (手动分词)', fill='#333', font=content_font)
draw.text((50, 130), f' 分词: {engine.smart_split_pinyin(input_pinyin1)}', fill='#666', font=small_font)
draw.text((50, 150), f' 候选词: {len(candidates1)}个', fill='#666', font=small_font)

# 绘制候选词窗口1
candidate_box1 = (50, 180, 430, 280)
draw.rectangle(candidate_box1, fill='white', outline='#ddd', width=1)

# 第一行：拼音
draw.rectangle([50, 180, 430, 220], fill='#667eea')
draw.text((80, 198), input_pinyin1, fill='white', font=content_font)
draw.text((350, 198), '手动分词', fill='white', font=small_font)

# 第二行：候选字
y_offset1 = 245
x_start1 = 80

for idx, (word, freq) in enumerate(candidates1):
    x_pos = x_start1 + idx * 90
    
    if idx == 0:
        # 选中第一个
        draw.text((x_pos, y_offset1), '1.', fill='#667eea', font=number_font)
        word_font = ImageFont.truetype(font_path, 32)
        draw.text((x_pos + 30, y_offset1 - 8), word, fill='#333', font=word_font)
        draw.rectangle([x_pos - 5, y_offset1 - 12, x_pos + 110, y_offset1 + 45], outline='#667eea', width=2)
    else:
        draw.text((x_pos, y_offset1), f'{idx+1}.', fill='#666', font=number_font)
        draw.text((x_pos + 30, y_offset1 - 8), word, fill='#666', font=content_font)

# 测试2: dongnandaxue
input_pinyin2 = "dongnandaxue"
candidates2 = manager.generate_candidates(input_pinyin2)

draw.text((470, 110), '测试2: dongnandaxue (自动分词)', fill='#333', font=content_font)
draw.text((470, 130), f' 分词: {engine.smart_split_pinyin(input_pinyin2)}', fill='#666', font=small_font)
draw.text((470, 150), f' 候选词: {len(candidates2)}个', fill='#666', font=small_font)

# 绘制候选词窗口2
candidate_box2 = (470, 180, 430, 280)
draw.rectangle(candidate_box2, fill='white', outline='#ddd', width=1)

# 第一行：拼音
draw.rectangle([470, 180, 430, 220], fill='#667eea')
draw.text((500, 198), input_pinyin2, fill='white', font=content_font)
draw.text((770, 198), '自动分词', fill='white', font=small_font)

# 第二行：候选字
y_offset2 = 245
x_start2 = 500

for idx, (word, freq) in enumerate(candidates2[:5]):
    x_pos = x_start2 + idx * 90
    
    if idx == 0:
        # 选中第一个
        draw.text((x_pos, y_offset2), '1.', fill='#667eea', font=number_font)
        word_font = ImageFont.truetype(font_path, 32)
        draw.text((x_pos + 30, y_offset2 - 8), word, fill='#333', font=word_font)
        draw.rectangle([x_pos - 5, y_offset2 - 12, x_pos + 110, y_offset2 + 45], outline='#667eea', width=2)
    else:
        draw.text((x_pos, y_offset2), f'{idx+1}.', fill='#666', font=number_font)
        draw.text((x_pos + 30, y_offset2 - 8), word, fill='#666', font=content_font)

# 绘制状态栏
status_bar = (50, 480, 850, 510)
draw.rectangle(status_bar, fill='#f9f9f9')
draw.text((70, 495), '🟢 排序已修复', fill='#666', font=small_font)
draw.text((200, 495), f'输入1: {input_pinyin1}', fill='#666', font=small_font)
draw.text((400, 495), f'输入2: {input_pinyin2}', fill='#666', font=small_font)
draw.text((600, 495), '优先级: 长度优先 + 词频其次', fill='#666', font=small_font)

# 保存图片
img.save('/root/dev/input-method/screenshot-fixed.png', 'PNG', quality=95)
print('✅ 修复后截图已生成')
print(f'   输入1: {input_pinyin1}')
print(f'   候选词1: {[(word, freq) for word, freq in candidates1]}')
print(f'   输入2: {input_pinyin2}')
print(f'   候选词2: {[(word, freq) for word, freq in candidates2]}')
