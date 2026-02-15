"""
中文输入法配置文件
"""

# 数据库配置
DB_PATH = "data/input_method.db"

# 候选词显示数量
MAX_CANDIDATES = 10

# 词频初始值
INITIAL_FREQUENCY = 1

# 词频增量
FREQUENCY_INCREMENT = 1

# 词频衰减（每次选择后的衰减系数，0.9表示衰减10%）
FREQUENCY_DECAY = 0.9

# 候选词分页显示数量
PAGE_SIZE = 5
