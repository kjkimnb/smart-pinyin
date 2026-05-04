# Teleoperation Paper Reproduction

复现论文 **Chen, Huang, Sun, Song (2018)** *"An Improved Wave-Variable Based Four-Channel Control Design in Bilateral Teleoperation System for Time-Delay Compensation"*, IEEE Access, DOI [10.1109/ACCESS.2018.2805782](https://doi.org/10.1109/ACCESS.2018.2805782).

代码在 [`teleoperation/`](teleoperation/) 目录, 三个独立模块:

| 文件 | 职责 |
|---|---|
| `teleoperation/master.py` | 主端动力学 (论文式 4) + 四通道前向信号 `M1 = C3·Fh + C1·Vm` (式 18) + 基于 BLDC 电流的 Fh 反应力观测器 (RFOB) |
| `teleoperation/slave.py` | 从端动力学 (论文式 5) + 单边软墙环境 + 四通道反向信号 `N2 = C2·Fe + C4·Vs` (式 19) |
| `teleoperation/test_teleoperation.py` | 三种通信通道 (NoComp / OriginalWave / ModifiedWave) + 仿真主循环 + 数值自检 + 绘图 |

详细说明见 [`teleoperation/README.md`](teleoperation/README.md).

## 快速开始

```bash
pip install -r requirements.txt

# 论文主流程: 复现 6 组对比实验 (3 控制器 × 2 时延) + 出图 + self-check
python -m teleoperation.test_teleoperation

# 仅快速 self-check (5 s 仿真, CI 用)
python -m teleoperation.test_teleoperation --no-plot --quick

# RFOB (基于 BLDC 电流的 Fh 估计) 自检 demo
python -m teleoperation.master
```

## 复现的论文核心结论

| 控制器 | T = 0 | T = 100 ms |
|---|---|---|
| **C1** no-comp (Lawrence) | 完美透明 | 接触振荡, 跟踪滞后 |
| **C2** original wave (Aziminejad) | 完美透明 | **发散** |
| **C3** modified wave (本文) | 略有相位差 | **稳定有界** |
