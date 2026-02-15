#!/usr/bin/env python3
"""
创建输入法界面截图（最终版）
横向布局，候选字不显示拼音
"""

from PIL import Image, ImageDraw, ImageFont

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

# 绘制标题
draw.text((50, 40), 'Smart Pinyin - 智能中文输入法', fill='#333', font=title_font)
draw.text((50, 70), 'Ubuntu桌面版演示（最终版）', fill='#666', font=small_font)

# 绘制编辑框（模拟文本编辑器）
edit_box = (50, 120, 750, 280)
draw.rectangle(edit_box, outline='#e0e0e0', width=2)
draw.rectangle([edit_box[0]+2, edit_box[1]+2, edit_box[2]-2, edit_box[3]-2], fill='#ffffff')

# 绘制文本
draw.text((70, 145), '今天', fill='#333', font=content_font)
draw.rectangle([210, 142, 290, 165], outline='#2196F3', width=2)
draw.text((220, 145), 'zhang', fill='#2196F3', font=content_font)

# 绘制光标
draw.rectangle([290, 145, 292, 165], fill='#2196F3')

# 绘制候选词窗口（横向布局，候选字不显示拼音）
candidate_box = (100, 300, 700, 380)
draw.rectangle(candidate_box, fill='white', outline='#ddd', width=1)

# 第一行：拼音（居中）
draw.rectangle([100, 300, 700, 340], fill='#667eea')
draw.text((350, 318), 'zhang', fill='white', font=content_font)

# 第二行：候选字（横向排列，不显示拼音）
candidates = ['张', '长', '章', '涨', '掌']

y_offset = 360
x_start = 130
spacing = 110

for idx, word in enumerate(candidates):
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
status_bar = (50, 400, 750, 430)
draw.rectangle(status_bar, fill='#f9f9f9')
draw.text((70, 415), '🟢 引擎运行中', fill='#666', font=small_font)
draw.text((250, 415), '分词: zhang', fill='#666', font=small_font)
draw.text((400, 415), '总词汇: 1,234', fill='#666', font=small_font)
draw.text((550, 415), '今日选择: 89次', fill='#666', font=small_font)

# 保存图片
img.save('/root/dev/input-method/screenshot-final.png', 'PNG', quality=95)
print('✅ 最终版截图已生成: /root/dev/input-method/screenshot-final.png')
print('   - 候选字不显示拼音')
print('   - 横向布局')
print('   - 光标旁显示候选窗口')
