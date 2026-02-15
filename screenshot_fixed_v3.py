#!/usr/bin/env python3
"""
重新生成正确的截图 - 展示修复后的排序效果
"""

from PIL import Image, ImageDraw, ImageFont
from word_database import WordDatabase
from pinyin_engine_enhanced import PinyinEngineEnhanced
from candidate_manager import CandidateManager

# 创建画布
width, height = 900, 550
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

# 添加测试词汇（确保对比明显）
test_words = [
    ("西安", "xi an", 90),      # 2字
    ("西", "xi", 80),            # 1字
]

for word, pinyin, freq in test_words:
    db.add_word(word, pinyin, freq)

# 绘制标题
draw.text((50, 30), 'Smart Pinyin - 智能中文输入法', fill='#333', font=title_font)
draw.text((50, 60), '修复验证：长度优先', fill='#666', font=small_font)

# 测试1: xi'an
input_pinyin = "xi'an"
candidates = manager.generate_candidates(input_pinyin)

draw.text((50, 100), f'测试: xi\'an', fill='#333', font=content_font)
draw.text((50, 125), f'输入: {input_pinyin}', fill='#666', font=small_font)
draw.text((50, 145), f'分词: {engine.smart_split_pinyin(input_pinyin)}', fill='#666', font=small_font)
draw.text((50, 165), f'候选词: {len(candidates)}个', fill='#666', font=small_font)

# 候选词窗口
candidate_box = (50, 200, 400, 340)
draw.rectangle(candidate_box, fill='white', outline='#ddd', width=1)
draw.rectangle([50, 200, 400, 240], fill='#667eea')
draw.text((80, 218), input_pinyin, fill='white', font=content_font)

# 候选词列表
y_offset = 250
x_start = 80
spacing = 90

for idx, (word, freq) in enumerate(candidates):
    x_pos = x_start + idx * spacing
    
    if idx == 0:
        draw.text((x_pos, y_offset), '1.', fill='#667eea', font=number_font)
        word_font = ImageFont.truetype(font_path, 30)
        draw.text((x_pos + 30, y_offset - 8), word, fill='#333', font=word_font)
        draw.rectangle([x_pos - 8, y_offset - 15, x_pos + 120, y_offset + 50], outline='#667eea', width=2)
    else:
        draw.text((x_pos, y_offset), f'{idx+1}.', fill='#666', font=number_font)
        draw.text((x_pos + 30, y_offset - 8), word, fill='#666', font=content_font)

# 测试2: dongnandaxue
test_words2 = [
    ("东南大学", "dong nan da xue", 85),  # 4字
    ("东南", "dong nan", 88),          # 2字
    ("东", "dong", 95),            # 1字
]

for word, pinyin, freq in test_words2:
    db.add_word(word, pinyin, freq)

input_pinyin2 = "dongnandaxue"
candidates2 = manager.generate_candidates(input_pinyin2)

draw.text((450, 100), f'测试: dongnandaxue', fill='#333', font=content_font)
draw.text((450, 125), f'输入: {input_pinyin2}', fill='#666', font=small_font)
draw.text((450, 145), f'分词: {engine.smart_split_pinyin(input_pinyin2)}', fill='#666', font=small_font)
draw.text((450, 165), f'候选词: {len(candidates2)}个', fill='#666', font=small_font)

# 候选词窗口2
candidate_box2 = (450, 200, 850, 340)
draw.rectangle(candidate_box2, fill='white', outline='#ddd', width=1)
draw.rectangle([450, 200, 850, 240], fill='#667eea')
draw.text((480, 218), input_pinyin2, fill='white', font=content_font)

# 候选词列表2
y_offset2 = 250
x_start2 = 480

for idx, (word, freq) in enumerate(candidates2):
    x_pos = x_start2 + idx * 90
    
    if idx == 0:
        draw.text((x_pos, y_offset2), '1.', fill='#667eea', font=number_font)
        word_font = ImageFont.truetype(font_path, 30)
        draw.text((x_pos + 30, y_offset2 - 8), word, fill='#333', font=word_font)
        draw.rectangle([x_pos - 8, y_offset2 - 15, x_pos + 110, y_offset2 + 50], outline='#667eea', width=2)
    else:
        draw.text((x_pos, y_offset2), f'{idx+1}.', fill='#666', font=number_font)
        draw.text((x_pos + 30, y_offset2 - 8), word, fill='#666', font=content_font)

# 状态栏
status_bar = (50, 400, 850, 430)
draw.rectangle(status_bar, fill='#f9f9f9')
draw.text((70, 415), '🟢 排序已修复', fill='#666', font=small_font)
draw.text((200, 415), f'xi\'an → {candidates[0][0]}', fill='#666', font=small_font)
draw.text((450, 415), f'dongnandaxue → {candidates2[0][0]}', fill='#666', font=small_font)
draw.text((700, 415), '优先级: 长度 > 词频', fill='#666', font=small_font)

# 保存图片
img.save('/root/dev/input-method/screenshot-fixed.png', 'PNG', quality=95)
print('✅ 修复后截图已生成: /root/dev/input-method/screenshot-fixed.png')
print(f'   输入1: xi\'an')
print(f'   候选词1: {[(word, freq) for word, freq in candidates]}')
print(f'   输入2: dongnandaxue')
print(f'   候选词2: {[(word, freq) for word, freq in candidates2]}')
