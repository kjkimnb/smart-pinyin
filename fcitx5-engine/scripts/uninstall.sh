#!/bin/bash
#
# Fcitx5中文输入法引擎卸载脚本
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 安装目录
INSTALL_DIR="$HOME/.local/share/fcitx5-chinese"
CONFIG_DIR="$HOME/.config/fcitx5-chinese"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Fcitx5中文输入法引擎 卸载程序${NC}"
echo -e "${YELLOW}========================================${NC}"

# 停止运行中的引擎
echo -e "\n${YELLOW}停止运行中的引擎...${NC}"
pkill -f "smart_engine.py" 2>/dev/null || true
pkill -f "engine.py" 2>/dev/null || true

# 删除安装文件
echo -e "\n${YELLOW}删除安装文件...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}已删除: $INSTALL_DIR${NC}"
else
    echo -e "目录不存在: $INSTALL_DIR"
fi

# 删除配置文件
echo -e "\n${YELLOW}删除配置文件...${NC}"
if [ -d "$CONFIG_DIR" ]; then
    echo -e "${YELLOW}配置目录: $CONFIG_DIR${NC}"
    read -p "是否删除配置文件? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        echo -e "${GREEN}已删除配置文件${NC}"
    else
        echo -e "保留配置文件"
    fi
else
    echo -e "配置目录不存在"
fi

# 删除桌面快捷方式
echo -e "\n${YELLOW}删除桌面快捷方式...${NC}"
if [ -f "$DESKTOP_DIR/fcitx5-chinese-engine.desktop" ]; then
    rm -f "$DESKTOP_DIR/fcitx5-chinese-engine.desktop"
    echo -e "${GREEN}已删除桌面快捷方式${NC}"
fi

# 删除自启动文件
echo -e "\n${YELLOW}删除自启动配置...${NC}"
if [ -f "$AUTOSTART_DIR/fcitx5-chinese-engine.desktop" ]; then
    rm -f "$AUTOSTART_DIR/fcitx5-chinese-engine.desktop"
    echo -e "${GREEN}已删除自启动配置${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  卸载完成！${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}提示：${NC}"
echo -e "- Fcitx5主程序不会被卸载"
echo -e "- 如需卸载Fcitx5，请运行: sudo apt-get remove fcitx5 fcitx5-chinese-addons"
echo -e "- 环境变量配置保留在 ~/.pam_environment 中"
