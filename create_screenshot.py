#!/usr/bin/env python3
"""
创建输入法界面截图
模拟Fcitx5候选词窗口在Ubuntu桌面上的样子
"""

from PIL import Image, ImageDraw, ImageFont
import os

# 创建画布
width, height = 800, 500
img = Image.new('RGB', (width, height), color='#f5f5f5')
draw = ImageDraw.Draw(img)

# 尝试加载中文字体，如果失败则使用默认字体
try:
    # 尝试常见的中文字体路径
    font_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    title_font = None
    content_font = None
    small_font = None

    for path in font_paths:
        if os.path.exists(path):
            if title_font is None:
                title_font = ImageFont.truetype(path, 24)
            elif content_font is None:
                content_font = ImageFont.truetype(path, 18)
            elif small_font is None:
                small_font = ImageFont.truetype(path, 14)

    if title_font is None:
        title_font = ImageFont.load_default()
    if content_font is None:
        content_font = ImageFont.load_default()
    if small_font is None:
        small_font = ImageFont.load_default()
except:
    title_font = ImageFont.load_default()
    content_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

# 绘制标题
draw.text((50, 40), 'Smart Pinyin - 智能中文输入法', fill='#333', font=title_font)
draw.text((50, 70), 'Ubuntu桌面版演示', fill='#666', font=small_font)

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

# 绘制候选词窗口
candidate_box = (220, 300, 500, 520)
draw.rectangle(candidate_box, fill='white', outline='#ddd', width=1)

# 绘制候选词标题栏
title_bar = (220, 300, 500, 335)
draw.rectangle(title_bar, fill='#667eea')
draw.text((235, 312), 'zhang', fill='white', font=content_font)
draw.text((420, 312), '1/2页', fill='white', font=small_font)

# 绘制候选词列表
candidates = [
    ('张', 'zhāng', '1'),
    ('长', 'cháng', '2'),
    ('章', 'zhāng', '3'),
    ('涨', 'zhǎng', '4'),
    ('掌', 'zhǎng', '5'),
]

y_offset = 350
for idx, (word, pinyin, num) in enumerate(candidates):
    # 选中第一个
    if idx == 0:
        draw.rectangle([222, y_offset-2, 498, y_offset+35], fill='#E3F2FD')
        draw.rectangle([222, y_offset-2, 222+3, y_offset+35], fill='#2196F3')

    # 数字圆圈
    circle_color = '#667eea' if idx == 0 else '#999'
    draw.ellipse([235, y_offset+5, 255, y_offset+25], fill=circle_color)
    draw.text((240, y_offset+6), num, fill='white', font=small_font)

    # 候选词
    draw.text((265, y_offset+6), word, fill='#333', font=content_font)

    # 拼音
    draw.text((400, y_offset+8), pinyin, fill='#999', font=small_font)

    y_offset += 40

# 绘制状态栏
status_bar = (50, 540, 750, 570)
draw.rectangle(status_bar, fill='#f9f9f9')
draw.text((70, 555), '🟢 引擎运行中', fill='#666', font=small_font)
draw.text((250, 555), '总词汇: 1,234', fill='#666', font=small_font)
draw.text((400, 555), '今日选择: 89次', fill='#666', font=small_font)
draw.text((550, 555), '上下文: 今天', fill='#666', font=small_font)

# 保存图片
img.save('/root/dev/input-method/screenshot.png', 'PNG')
print('截图已保存: /root/dev/input-method/screenshot.png')
