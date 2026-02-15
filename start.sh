#!/bin/bash
# 中文输入法启动脚本

# 进入项目目录
cd "$(dirname "$0")"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查pypinyin是否安装
if ! python3 -c "import pypinyin" 2>/dev/null; then
    echo "正在安装依赖..."
    pip install pypinyin==0.49.0 --break-system-packages -q
    if [ $? -ne 0 ]; then
        echo "错误: 依赖安装失败"
        exit 1
    fi
fi

# 运行输入法
echo "启动中文输入法..."
python3 main.py
