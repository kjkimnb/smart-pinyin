#!/bin/bash
#
# Fcitx5中文输入法引擎安装脚本
# 适用于Ubuntu 22.04/24.04
#

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 安装目录
INSTALL_DIR="$HOME/.local/share/fcitx5-chinese"
CONFIG_DIR="$HOME/.config/fcitx5-chinese"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Fcitx5中文输入法引擎 安装程序${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}请不要使用root用户运行此脚本${NC}"
    exit 1
fi

# 检查操作系统
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}无法检测操作系统版本${NC}"
    exit 1
fi

. /etc/os-release
echo -e "检测到操作系统: $PRETTY_NAME"

# 检查Python版本
echo -e "\n${YELLOW}检查Python版本...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3未安装，请先安装Python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo -e "Python版本: $PYTHON_VERSION"

# 安装系统依赖
echo -e "\n${YELLOW}安装系统依赖...${NC}"

# 更新包列表
sudo apt-get update

# 安装必要的包
echo "安装Python依赖..."
sudo apt-get install -y python3-pip python3-venv

# 安装DBus和GLib依赖
echo "安装DBus和GLib依赖..."
sudo apt-get install -y \
    python3-dbus \
    python3-gi \
    gir1.2-glib-2.0 \
    libglib2.0-0

# 安装Fcitx5（如果未安装）
if ! command -v fcitx5 &> /dev/null; then
    echo -e "${YELLOW}Fcitx5未安装，正在安装...${NC}"
    sudo apt-get install -y fcitx5 fcitx5-chinese-addons fcitx5-config-qt
else
    echo -e "${GREEN}Fcitx5已安装${NC}"
fi

# 创建虚拟环境
echo -e "\n${YELLOW}创建Python虚拟环境...${NC}"
VENV_DIR="$PROJECT_ROOT/venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}虚拟环境创建成功${NC}"
else
    echo -e "${GREEN}虚拟环境已存在${NC}"
fi

# 激活虚拟环境并安装依赖
echo -e "\n${YELLOW}安装Python依赖...${NC}"
source "$VENV_DIR/bin/activate"

# 升级pip
pip install --upgrade pip

# 安装必要的Python包
pip install -r "$PROJECT_ROOT/requirements.txt"

# 安装额外的依赖
pip install \
    pypinyin \
    dbus-python \
    PyGObject

# 初始化数据库
echo -e "\n${YELLOW}初始化词频数据库...${NC}"
cd "$PROJECT_ROOT"

if [ ! -f "data/input_method.db" ]; then
    python3 -c "
import sys
sys.path.insert(0, '.')
from word_database import WordDatabase

db = WordDatabase()
count = db.initialize_common_words()
print(f'初始化了 {count} 个常用词')
"
else
    echo -e "${GREEN}数据库已存在${NC}"
fi

# 创建安装目录
echo -e "\n${YELLOW}创建安装目录...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$AUTOSTART_DIR"

# 复制文件
echo -e "\n${YELLOW}安装文件...${NC}"

# 复制源代码
cp -r "$PROJECT_ROOT/src"/*.py "$INSTALL_DIR/"

# 复制配置文件
cat > "$CONFIG_DIR/config.json" << EOF
{
  "max_candidates": 10,
  "page_size": 5,
  "enable_context": true,
  "enable_adaptive": true,
  "context_weight": 1.5,
  "adaptive_weight": 1.0,
  "base_weight": 0.5
}
EOF

# 创建启动脚本
cat > "$INSTALL_DIR/start.sh" << 'EOF'
#!/bin/bash
# 启动Fcitx5中文输入法引擎

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source "$SCRIPT_DIR/venv/bin/activate"

# 启动引擎
python3 smart_engine.py &
EOF

chmod +x "$INSTALL_DIR/start.sh"

# 创建桌面快捷方式（用于手动启动）
cat > "$DESKTOP_DIR/fcitx5-chinese-engine.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Fcitx5 Chinese Engine
Comment=Smart Chinese Input Engine for Fcitx5
Exec=$INSTALL_DIR/start.sh
Icon=input-keyboard
Terminal=false
Categories=Utility;
EOF

# 创建自启动文件
cat > "$AUTOSTART_DIR/fcitx5-chinese-engine.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Fcitx5 Chinese Engine
Comment=Smart Chinese Input Engine for Fcitx5
Exec=$INSTALL_DIR/start.sh
Icon=input-keyboard
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
EOF

# 创建Fcitx5配置
echo -e "\n${YELLOW}配置Fcitx5...${NC}"

FCITX5_CONFIG_DIR="$HOME/.config/fcitx5"
mkdir -p "$FCITX5_CONFIG_DIR"

# 创建profile配置（添加输入法）
if [ -f "$FCITX5_CONFIG_DIR/profile" ]; then
    echo -e "${YELLOW}Fcitx5 profile已存在，请手动配置${NC}"
else
    cat > "$FCITX5_CONFIG_DIR/profile" << EOF
[Groups/0]
# Group Name
Name=Default
# Layout
DefaultLayout=us
# Default InputMethod
DefaultIM=

[Groups/0/Items/0]
# Name
Name=keyboard-us
# Lang
LangCode=en
# Enabled
Enabled=true

[Groups/0/Items/1]
# Name
Name=pinyin
# Lang
LangCode=zh_CN
# Enabled
Enabled=true
EOF
fi

# 设置环境变量
echo -e "\n${YELLOW}设置环境变量...${NC}"

ENV_FILE="$HOME/.pam_environment"
if [ ! -f "$ENV_FILE" ]; then
    touch "$ENV_FILE"
fi

if ! grep -q "GTK_IM_MODULE=fcitx" "$ENV_FILE"; then
    cat >> "$ENV_FILE" << EOF

GTK_IM_MODULE DEFAULT=fcitx
QT_IM_MODULE  DEFAULT=fcitx
XMODIFIERS    DEFAULT=@im=fcitx
INPUT_METHOD  DEFAULT=fcitx
EOF
    echo -e "${GREEN}环境变量已添加到 ~/.pam_environment${NC}"
else
    echo -e "${GREEN}环境变量已配置${NC}"
fi

# 完成安装
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}后续步骤：${NC}"
echo -e "1. 注销或重启系统以应用环境变量"
echo -e "2. 启动Fcitx5: ${GREEN}fcitx5 -d${NC}"
echo -e "3. 启动中文引擎: ${GREEN}$INSTALL_DIR/start.sh${NC}"
echo -e "4. 使用 ${GREEN}fcitx5-config-qt${NC} 配置输入法"
echo -e "5. 使用 ${GREEN}Ctrl+Space${NC} 切换输入法"

echo -e "\n${YELLOW}故障排除：${NC}"
echo -e "- 查看日志: ${GREEN}tail -f /tmp/fcitx5-chinese-smart-engine.log${NC}"
echo -e "- 重新加载配置: ${GREEN}fcitx5-remote -r${NC}"
echo -e "- 检查DBus服务: ${GREEN}busctl --user list | grep fcitx${NC}"

echo -e "\n${GREEN}安装成功！${NC}"
