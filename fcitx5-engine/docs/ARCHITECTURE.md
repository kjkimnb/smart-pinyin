# 架构设计文档

## 概述

Fcitx5 中文输入法引擎采用模块化设计，各组件职责清晰，易于维护和扩展。

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Fcitx5 框架                          │
│                  (Input Method Framework)                │
└──────────────────────────┬──────────────────────────────┘
                           │ DBus IPC
┌──────────────────────────▼──────────────────────────────┐
│              SmartChineseInputEngine                      │
│          (DBus 服务 / 主控制器)                           │
│                                                           │
│  - 提供标准 DBus 接口                                    │
│  - 协调各子模块                                           │
│  - 管理输入状态                                           │
└───┬──────────────────┬──────────────────┬────────────────┘
    │                  │                  │
┌───▼──────────┐ ┌────▼─────────────┐ ┌──▼───────────────┐
│ContextEngine │ │AdaptiveFrequency │ │CandidateManager  │
│              │ │    Manager       │ │                  │
│- N-gram模型  │ │- 时间衰减        │ │- 候选词生成      │
│- 上下文关联  │ │- 时间模式        │ │- 词频排序        │
│- 联想推荐    │ │- 自适应学习      │ │- 分页管理        │
└──────────────┘ └──────────────────┘ └──┬───────────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              │                             │
                        ┌─────▼──────┐              ┌──────▼──────┐
                        │PinyinEngine│              │WordDatabase │
                        │            │              │             │
                        │- 拼音转换  │              │- SQLite存储 │
                        │- 模糊匹配  │              │- 词频管理  │
                        │- 标准化    │              │- 历史记录  │
                        └────────────┘              └─────────────┘
```

## 核心组件

### 1. SmartChineseInputEngine（智能引擎）

**职责**：主控制器，DBus 服务

**功能**：
- 提供 DBus 接口供 Fcitx5 调用
- 协调 ContextEngine 和 AdaptiveFrequencyManager
- 管理输入状态（输入中、候选词、页面等）
- 合并多种候选词源并排序

**接口**：
```python
GetCandidates(pinyin: str) -> List[Dict]
SelectCandidate(index: int) -> str
AddWord(word: str) -> str
SetComposing(pinyin: str) -> bool
Clear() -> bool
GetStatus() -> List[Dict]
GetTopWords(limit: int) -> List[Dict]
GetContextStats(n: int, limit: int) -> List[Dict]
ClearContext() -> bool
DecayFrequencies() -> bool
ReloadConfig() -> bool
```

### 2. ContextEngine（上下文引擎）

**职责**：基于 N-gram 的上下文关联推荐

**算法**：
- **Bigram**：`P(next_word | prev_word)`
- **Trigram**：`P(next_word | prev_prev_word, prev_word)`
- 使用对数平滑处理计数

**数据结构**：
```python
ngram_stats 表:
- context: 上下文（"我们" 或 "我 们"）
- next_word: 下一个词
- count: 出现次数
- n: N-gram 的 N 值（2 或 3）
```

**学习机制**：
- 每次选择词汇后更新 N-gram 计数
- 上下文窗口大小：3 个词
- 使用 SQLite 存储所有 N-gram

### 3. AdaptiveFrequencyManager（自适应词频管理器）

**职责**：实现智能词频算法，超越谷歌输入法

**算法组成**：

#### 3.1 时间衰减
```
TimeFactor = decay_rate ^ days_since_last_use
```
- decay_rate: 0.99（日衰减率）
- 近期选择的词汇权重更高

#### 3.2 趋势分析
```
TrendFactor = 1.0 + (recent_selections / total_selections)
```
- 比较近期选择和总选择次数
- 识别上升中的词汇

#### 3.3 时间模式
```
PatternFactor = 1.0 + (pattern_matches / 10.0)
```
- 记录使用的小时和星期
- 匹配当前时间的历史模式
- 例如：工作日白天常用"工作"，晚上常用"休息"

**数据结构**：
```python
word_stats 表:
- word: 词汇
- pinyin: 拼音
- base_frequency: 基础词频
- total_selections: 总选择次数
- last_selected: 最后选择时间
- first_selected: 首次选择时间
- selection_times: 所有选择时间戳（逗号分隔）

selection_timeline 表:
- word: 词汇
- pinyin: 拼音
- selected_at: 选择时间
- hour_of_day: 小时（0-23）
- day_of_week: 星期（0-6）
```

**综合计算**：
```
AdaptiveScore = BaseFreq × TimeFactor × TrendFactor × PatternFactor
```

### 4. CandidateManager（候选词管理器）

**职责**：管理候选词的生成、排序和选择

**功能**：
- 从数据库查询候选词
- 应用基础词频排序
- 处理分页
- 添加自定义词汇
- 记录用户选择

### 5. PinyinEngine（拼音引擎）

**职责**：拼音转换和处理

**功能**：
- 中文转拼音
- 拼音标准化（统一格式）
- 模糊匹配
- 使用 pypinyin 库

### 6. WordDatabase（词数据库）

**职责**：SQLite 数据库管理

**功能**：
- 词汇存储和查询
- 词频更新
- 历史记录
- 数据库初始化

## 数据流

### 输入流程

```
1. 用户输入拼音
   ↓
2. Fcitx5 调用 GetCandidates(pinyin)
   ↓
3. SmartChineseInputEngine 处理：
   - 标准化拼音
   - 调用 CandidateManager 生成基础候选词
   - 调用 ContextEngine 获取上下文关联词
   - 使用 AdaptiveFrequencyManager 计算自适应分数
   - 合并并排序
   ↓
4. 返回候选词列表给 Fcitx5
   ↓
5. Fcitx5 显示候选词窗口
```

### 选择流程

```
1. 用户选择候选词（按数字或鼠标点击）
   ↓
2. Fcitx5 调用 SelectCandidate(index)
   ↓
3. SmartChineseInputEngine 处理：
   - 更新基础词频（WordDatabase）
   - 记录到自适应管理器（AdaptiveFrequencyManager）
   - 更新上下文（ContextEngine）
   - 清空当前输入
   ↓
4. 返回选中的词给 Fcitx5
   ↓
5. Fcitx5 提交到应用程序
```

## 关键设计决策

### 1. 为什么使用 DBus 而不是 Fcitx5 C API？

**原因**：
- 开发效率高（Python vs C++）
- 不需要重新编译 Fcitx5
- 进程隔离，稳定性更好
- 跨平台性更好

**缺点**：
- 轻微的性能开销（可忽略不计）
- 需要额外守护进程

### 2. 为什么使用 SQLite 而不是内存数据库？

**原因**：
- 持久化存储（用户数据不丢失）
- 支持复杂查询
- 索引优化（查询效率高）
- 易于备份和迁移

### 3. 为什么分离 ContextEngine 和 AdaptiveFrequencyManager？

**原因**：
- 职责分离（上下文关联 vs 词频学习）
- 独立配置（可单独启用/禁用）
- 易于测试和维护
- 可扩展性（未来可添加更多特征）

### 4. 为什么使用 N-gram 而不是神经网络？

**原因**：
- N-gram 效果足够好（实用性强）
- 实现简单（可维护）
- 训练快速（实时学习）
- 资源占用低（内存友好）

### 5. 为什么在用户空间运行？

**原因**：
- 安全性（无需 root 权限）
- 稳定性（不影响系统）
- 可移植性（易于安装和卸载）
- 灵活性（用户可自定义）

## 性能考虑

### 1. 数据库优化

- 关键字段建立索引
- 使用预编译语句
- 批量操作
- 连接池

### 2. 内存优化

- 词频计算结果缓存
- N-gram 计数缓存
- 限制上下文窗口大小
- 定期清理旧数据

### 3. 响应优化

- 异步 DBus 通信
- 延迟加载
- 增量更新
- 后台预处理

## 稳定性设计

### 1. 异常处理

- 所有外部操作都有 try-catch
- 详细的错误日志
- 优雅降级（组件故障不影响基本功能）
- 自动恢复机制

### 2. 数据安全

- 事务操作（原子性）
- 定期备份
- 数据验证
- 错误恢复

### 3. 进程隔离

- 独立进程运行
- DBus 通信隔离
- 资源限制
- 超时保护

## 扩展性

### 1. 添加新特征

```python
# 示例：添加地理位置相关推荐
class LocationEngine:
    def get_location_based_candidates(self, pinyin):
        # 基于用户位置推荐
        pass

# 在 SmartChineseInputEngine 中集成
def GetCandidates(self, pinyin):
    base_candidates = self.candidate_manager.generate_candidates(pinyin)
    context_candidates = self.context_engine.get_contextual_candidates(pinyin)
    location_candidates = self.location_engine.get_location_based_candidates(pinyin)
    # 合并...
```

### 2. 添加新接口

```python
@dbus.service.method(INTERFACE, in_signature='', out_signature='s')
def GetVersion(self):
    """获取版本信息"""
    return "1.0.0"
```

### 3. 添加新配置

```python
config = {
    'max_candidates': 10,
    'enable_context': True,
    # 新配置
    'enable_location': False,
    'location_weight': 1.2
}
```

## 测试策略

### 1. 单元测试

- 每个组件独立测试
- Mock 外部依赖
- 边界条件测试

### 2. 集成测试

- 组件间交互测试
- DBus 接口测试
- 完整流程测试

### 3. 性能测试

- 响应时间测试
- 内存占用测试
- 并发测试

## 部署架构

```
用户目录结构:
~/.local/share/fcitx5-chinese/
├── start.sh              # 启动脚本
├── engine.py             # 基础引擎
├── smart_engine.py       # 智能引擎
├── context_engine.py     # 上下文引擎
├── adaptive_frequency.py # 自适应管理器
└── venv/                 # Python 虚拟环境

~/.config/fcitx5-chinese/
└── config.json           # 配置文件

~/.config/fcitx5/
└── profile               # Fcitx5 配置

~/.config/autostart/
└── fcitx5-chinese-engine.desktop  # 自启动配置
```

## 总结

本架构设计遵循以下原则：

1. **模块化**：职责清晰，易于维护
2. **可扩展**：易于添加新功能
3. **稳定性**：多层保护，避免崩溃
4. **性能**：优化关键路径
5. **安全性**：用户空间运行，权限最小化

通过精心设计的组件和数据流，实现了超越谷歌输入法的智能推荐算法，同时保证了系统的稳定性和可维护性。
