# Fcitx5 中文输入法引擎

一个基于 Python 的智能中文输入法引擎，专为 Ubuntu 22.04/24.04 的 Fcitx5 框架设计。

## 特性

### 🚀 核心功能
- ✅ **拼音输入**：完整支持全拼、简拼
- ✅ **候选词窗口**：美观的候选词显示
- ✅ **智能选词**：基于多种算法的智能排序

### 🧠 智能推荐算法（超越谷歌输入法）
- ✅ **自适应词频学习**：
  - 时间衰减机制（近期选择权重更高）
  - 时间模式识别（考虑使用时间和星期）
  - 动态调整词频（避免高频词占据首位）

- ✅ **上下文关联推荐**：
  - N-gram 模型（Bigram、Trigram）
  - 智能联想（根据上下文推荐下一个词）
  - 语境感知（理解用户的表达习惯）

- ✅ **用户历史分析**：
  - 完整的选择历史记录
  - 统计分析（总选择次数、今日使用等）
  - 个性化优化

### 🛡️ 稳定性保障
- ✅ **用户空间运行**：完全在用户空间，避免系统级崩溃
- ✅ **异常处理**：完善的错误捕获和日志记录
- ✅ **优雅降级**：组件故障不影响基本功能
- ✅ **DBus 通信**：稳定的进程间通信机制

## 系统要求

- 操作系统：Ubuntu 22.04 或 24.04
- Python：3.8 或更高版本
- 框架：Fcitx5（如果未安装，安装脚本会自动安装）
- 依赖：python3-dbus, python3-gi, pypinyin

## 安装

### 方法一：自动安装（推荐）

1. 克隆或下载项目
```bash
cd ~/dev/input-method/
```

2. 运行安装脚本
```bash
chmod +x fcitx5-engine/scripts/install.sh
./fcitx5-engine/scripts/install.sh
```

3. 注销或重启系统（应用环境变量）

4. 启动 Fcitx5
```bash
fcitx5 -d
```

5. 启动中文引擎
```bash
~/.local/share/fcitx5-chinese/start.sh
```

### 方法二：手动安装

#### 1. 安装系统依赖
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-dbus python3-gi fcitx5 fcitx5-chinese-addons fcitx5-config-qt
```

#### 2. 安装 Python 依赖
```bash
cd ~/dev/input-method/
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pypinyin dbus-python PyGObject
```

#### 3. 初始化数据库
```bash
python3 -c "
import sys
sys.path.insert(0, '.')
from word_database import WordDatabase

db = WordDatabase()
count = db.initialize_common_words()
print(f'初始化了 {count} 个常用词')
"
```

#### 4. 配置环境变量

编辑 `~/.pam_environment`，添加以下内容：
```
GTK_IM_MODULE DEFAULT=fcitx
QT_IM_MODULE  DEFAULT=fcitx
XMODIFIERS    DEFAULT=@im=fcitx
INPUT_METHOD  DEFAULT=fcitx
```

#### 5. 启动引擎
```bash
cd fcitx5-engine/src
python3 smart_engine.py &
```

## 使用说明

### 基本操作

1. **切换输入法**：按 `Ctrl + Space` 或 `Super + Space`

2. **输入拼音**：
   - 全拼：`nihao` → 你好
   - 简拼：`nh` → 你好

3. **选择候选词**：
   - 按数字键选择（1, 2, 3...）
   - 使用 `-` `=` 翻页
   - 或使用鼠标点击

4. **提交输出**：
   - 空格：选择第一个候选词
   - 回车：提交当前拼音组合
   - 标点符号：自动提交并输入标点

### 高级功能

#### 添加自定义词汇

输入法会自动学习您使用的词汇。如果需要手动添加：

```python
# 使用 DBus 接口
import dbus
bus = dbus.SessionBus()
engine = bus.get_object('org.fcitx.SmartChineseEngine', '/org/fcitx/SmartChineseEngine')
engine.AddWord('新词汇')
```

#### 查看词频统计

```python
import dbus
bus = dbus.SessionBus()
engine = bus.get_object('org.fcitx.SmartChineseEngine', '/org/fcitx/SmartChineseEngine')
top_words = engine.GetTopWords(20)
```

#### 调整配置

编辑配置文件 `~/.config/fcitx5-chinese/config.json`：

```json
{
  "max_candidates": 10,          // 最大候选词数量
  "page_size": 5,                // 每页显示数量
  "enable_context": true,        // 启用上下文关联
  "enable_adaptive": true,       // 启用自适应词频
  "context_weight": 1.5,         // 上下文关联权重
  "adaptive_weight": 1.0,        // 自适应词频权重
  "base_weight": 0.5             // 基础词频权重
}
```

修改后需要重启引擎以应用配置。

## 配置 Fcitx5

### 使用图形界面

1. 打开 Fcitx5 配置工具
```bash
fcitx5-config-qt
```

2. 点击 "添加输入法"
3. 选择 "拼音" 输入法
4. 点击 "确定"

### 手动配置

编辑 `~/.config/fcitx5/profile`：

```
[Groups/0]
Name=Default
DefaultLayout=us
DefaultIM=

[Groups/0/Items/0]
Name=keyboard-us
LangCode=en
Enabled=true

[Groups/0/Items/1]
Name=pinyin
LangCode=zh_CN
Enabled=true
```

## 故障排除

### 引擎无法启动

1. 检查日志：
```bash
tail -f /tmp/fcitx5-chinese-smart-engine.log
```

2. 检查 DBus 服务：
```bash
busctl --user list | grep fcitx
```

3. 手动运行并查看错误：
```bash
cd fcitx5-engine/src
python3 smart_engine.py
```

### 候选词不显示

1. 确认引擎正在运行：
```bash
ps aux | grep smart_engine
```

2. 重新加载 Fcitx5：
```bash
fcitx5-remote -r
```

### 环境变量不生效

1. 检查环境变量：
```bash
echo $GTK_IM_MODULE
echo $QT_IM_MODULE
echo $XMODIFIERS
```

2. 注销或重启系统

### 性能问题

1. 清空频率缓存：
```python
import dbus
bus = dbus.SessionBus()
engine = bus.get_object('org.fcitx.SmartChineseEngine', '/org/fcitx/SmartChineseEngine')
engine.DecayFrequencies()
```

2. 执行词频衰减（定期执行）：
```python
engine.DecayFrequencies()
```

## 卸载

运行卸载脚本：

```bash
chmod +x fcitx5-engine/scripts/uninstall.sh
./fcitx5-engine/scripts/uninstall.sh
```

或手动删除：

```bash
rm -rf ~/.local/share/fcitx5-chinese
rm -rf ~/.config/fcitx5-chinese
rm ~/.local/share/applications/fcitx5-chinese-engine.desktop
rm ~/.config/autostart/fcitx5-chinese-engine.desktop
```

## 项目结构

```
fcitx5-engine/
├── src/
│   ├── engine.py              # 基础引擎（DBus 服务）
│   ├── smart_engine.py        # 智能引擎（集成上下文和自适应）
│   ├── context_engine.py      # 上下文关联推荐引擎
│   ├── adaptive_frequency.py  # 自适应词频管理
│   ├── pinyin_engine.py       # 拼音转换引擎（来自原项目）
│   ├── word_database.py       # 词频数据库（来自原项目）
│   └── candidate_manager.py   # 候选词管理（来自原项目）
├── config/
│   └── config.json            # 默认配置
├── scripts/
│   ├── install.sh             # 安装脚本
│   └── uninstall.sh           # 卸载脚本
├── docs/
│   ├── API.md                 # API 文档
│   └── ARCHITECTURE.md        # 架构文档
└── README.md                  # 本文件
```

## 技术架构

### 架构设计

```
┌─────────────────────────────────────┐
│         Fcitx5 框架                 │
└──────────────┬──────────────────────┘
               │ DBus
┌──────────────▼──────────────────────┐
│     SmartChineseInputEngine         │
│   (DBus 服务 / 主入口)              │
└───┬──────────────┬──────────────────┘
    │              │
┌───▼──────┐  ┌────▼──────────┐
│ Context  │  │   Adaptive    │
│  Engine  │  │   Frequency   │
│ (上下文) │  │  Manager      │
└──────────┘  └───────────────┘
    │              │
    └──────┬───────┘
           │
    ┌──────▼──────────────┐
    │ Candidate Manager   │
    │  + Pinyin Engine    │
    │  + Word Database     │
    └─────────────────────┘
```

### 核心算法

#### 1. 自适应词频算法

综合考虑以下因素计算词频分数：

```
AdaptiveScore = BaseFreq × TimeFactor × TrendFactor × PatternFactor
```

- **BaseFreq**：基础词频（历史选择次数）
- **TimeFactor**：时间衰减（`decay_rate ^ days_since`）
- **TrendFactor**：趋势因子（近期选择比例）
- **PatternFactor**：时间模式（匹配当前使用时间）

#### 2. 上下文关联算法

使用 N-gram 模型进行关联推荐：

```
ContextScore = Log(NgramCount) × N × Weight
```

- **NgramCount**：N-gram 计数
- **N**：N-gram 的 N 值（2 或 3）
- **Weight**：权重（可配置）

#### 3. 综合排序

合并多种得分进行排序：

```
CombinedScore = BaseScore × BaseWeight +
                AdaptiveScore × AdaptiveWeight +
                ContextScore × ContextWeight
```

## 性能优化

- ✅ **数据库索引**：关键字段建立索引
- ✅ **内存缓存**：词频计算结果缓存
- ✅ **异步处理**：DBus 通信异步化
- ✅ **延迟加载**：按需加载模块

## 安全性

- ✅ **用户空间运行**：无需 root 权限
- ✅ **沙盒隔离**：独立进程，不影响系统
- ✅ **输入验证**：所有输入经过验证
- ✅ **异常处理**：完善的错误捕获

## 开发

### 运行测试

```bash
cd ~/dev/input-method/
python3 test.py
```

### 查看 DBus 接口

```bash
busctl --user introspect org.fcitx.SmartChineseEngine /org/fcitx/SmartChineseEngine
```

### 调试

```bash
# 启动时启用详细日志
cd fcitx5-engine/src
python3 smart_engine.py

# 查看实时日志
tail -f /tmp/fcitx5-chinese-smart-engine.log
```

## 已知问题

1. **Fcitx5 版本兼容性**：某些旧版本可能有兼容性问题
2. **DBus 权限**：某些环境下可能需要额外配置
3. **内存占用**：大量词汇时内存占用较高

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 作者

- 开发时间：2026 年
- 技术栈：Python + Fcitx5 + DBus + SQLite

## 致谢

- Fcitx5 社区
- pypinyin 项目
- 所有贡献者
