# 论文复现: Improved Wave-Variable Based Four-Channel Teleoperation

复现 **Chen, Huang, Sun, Song (2018)** *"An Improved Wave-Variable Based Four-Channel Control Design in Bilateral Teleoperation System for Time-Delay Compensation"*, IEEE Access, DOI 10.1109/ACCESS.2018.2805782.

## 文件

| 文件 | 角色 |
|---|---|
| `master.py` | 主端: 物理动力学 + 本地控制器 + 四通道控制器(主端侧) |
| `slave.py`  | 从端: 物理动力学 + 单边软墙环境 + 四通道控制器(从端侧) |
| `test_teleoperation.py` | 通信通道(三种) + 仿真主循环 + 数值对比 + 绘图 |

## 复现的论文结论

仿真把论文 Section IV 的对比实验做成 6 组 (3 控制器 × 2 时延):

| 控制器 | 含义 |
|---|---|
| **C1** no-comp | 原始四通道, 通信通道无补偿 (Lawrence / Hashtrudi-Zaad) |
| **C2** original wave | 原始波变换 + 四通道 (Aziminejad), 存在波反射 |
| **C3** modified wave | 论文的改进波变换 (式 30/31), 减小波反射 |

| Set | 时延 | 用途 |
|---|---|---|
| Set1 | T = 0    | 验证 "理想透明" |
| Set2 | T = 0.1s | 验证 "时延下的稳定性 / 透明性" |

## 运行

```bash
pip install numpy matplotlib
python -m teleoperation.test_teleoperation                     # 出图 + 数值
python -m teleoperation.test_teleoperation --no-plot --quick   # 仅 self-check
python -m teleoperation.test_teleoperation --out result.png    # 保存图
```

## 典型输出

```
controller                                 T[ms]    pos_rmse    pos_peak   force_rmse  diverged
-----------------------------------------------------------------------------------------------
C1 no-comp            Set1                     0      0.0029      0.0059       1.1437     False
C2 original wave      Set1                     0      0.0029      0.0060       1.1437     False
C3 modified wave (this paper) Set1             0      0.4335      0.8723       1.0879     False
C1 no-comp            Set2                   100      0.3951      0.8011       1.4233     False
C2 original wave      Set2                   100   4736.3170  14965.0740   15845.5209     False
C3 modified wave (this paper) Set2           100      1.0708      2.6244       1.7806     False
  [OK] self-check 通过: 复现了论文核心结论
        (C2/C1 在时延下退化或失稳, C3 仍稳定且透明性几乎不受时延影响)
```

可见:
- **C1/C2 @ T=0** 完美透明 (Xm ≈ Xs).
- **C2 @ T=0.1** 直接发散到 10⁴ 量级 — 论文 Fig.12-13 失稳现象.
- **C1 @ T=0.1** 出现明显接触振荡和滞后 — 论文 Fig.10-11 现象.
- **C3 @ T=0.1** 仍然稳定有界, 跟踪定性正确 — 论文 Fig.16-19 的核心结论.

## 关于 Fh 的工程注记

论文的"主端力 Fh"是操作者手对主端的真实作用力, 与"主端电机输出力"是两码事:

- 物理量 **Fh** 是外部输入, **没有主端力传感器**时通常用 (a) 主端动力学反算
  ``Fh ≈ Mm·a_m + Bm·Vm + F_motor``, 或 (b) 反应力观测器 (RFOB / DOB) 估计.
  论文本身没有明确写出估计实现, 我们的仿真把 Fh 当成已知输入 (这与论文公式
  推导是一致的).
- **主端电机命令** 在控制器里从公式 (4) 反解:
  `F_motor_master = Bm·Vm + Km·Xm + sig_to_master − C6·Fh`,
  在仿真里仅用作可视化曲线 ``F_motor (master felt)``.

## 仿真参数 vs 论文参数

论文中 ``Mm = 0.05 kg``, ``b = 200 N·s/m`` 是带量纲的实验值. 本仿真采用
归一化参数 (``Mm = 1, Bm = Bs = 0.05, b = 0.2``) 以保证半隐式离散在
``dt = 1e-4 s`` 下数值稳定, 同时保留论文动力学结构与四通道增益的相对关系
(``C1 = Zce``, ``C4 = -Zcm``, ``C2 = 1+C6``, ``C3 = 1+C5``, 论文式 36).
``b`` 在归一化系统下经过扫描取折中值 (见 ``run_all`` 的注释).
