"""
主端模块 (Master)
=================

复现论文 Chen et al. (2018) "An Improved Wave-Variable Based Four-Channel
Control Design in Bilateral Teleoperation System for Time-Delay Compensation"
(IEEE Access, 2018) 中的主端 (master).

论文映射
--------
- 物理模型 (论文式 4):
      Zcm·Vm + C4·Vs = (1+C6)·Fh - C2·Fe
      => Mm·a_m + Bm·Vm + Km·Xm = (1+C6)·Fh - sig_to_master

- 主端发出到通信通道的"前向信号" (论文式 18):
      M1 = C3·Fh + C1·Vm
  ``C1·Vm`` 在论文里取 ``Zce·Vm`` (中频段 ≈ Bs·Vm), 其语义是给从端
  一个"想让从端跟到的速度参考 / 阻抗匹配信号".

- 主端从通信通道收到的"反向信号" sig_to_master, 形式视通信通道而定:
      * 无补偿 / 纯时延通道:   sig = N2(t-T) = C2·Fe(t-T) + C4·Vs(t-T)
      * 改进波变换通道:        sig = N1(t)  = N2(t-T) + b·M1(t)   (论文式 31)
  这里 -C4·Vs(t-T) 项是论文里"从端速度反馈到主端"形成力觉感的核心,
  也是时延一来就会与环境接触力 Fe 形成振荡的根源.

关于 Fh
-------
本仿真把 Fh 作为外部已知信号传入. 在没有主端力传感器的真实硬件 (例如
Phantom Touch) 上, Fh 通常需要靠扰动观测器 / 反应力观测器 (RFOB) 或主
端动力学反算 ( Fh ≈ Mm·a_m + Bm·Vm + F_motor ) 来估计; 论文本身没有给
出具体估计实现.

数值实现
--------
``update`` 接口允许调用方把 sig_to_master 中"与当前主端速度 Vm 成正比"
的部分 ``d_sig_dVm`` 单独传入, 该部分会被放到隐式侧, 保证波变换 b 较大
时也能稳定离散.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MasterParams:
    """主端参数."""

    Mm: float = 1.0                   # 主端等效惯量
    Bm: float = 2.0                   # 主端本地阻尼 (Cm 的 B 项, 含本体黏滞)
    Km: float = 0.0                   # 主端本地刚度 (Cm 的 K 项, 自由握把通常为 0)

    # 四通道增益 (与论文 (36) 透明性条件一致地设置: C2 = 1+C6, C3 = 1+C5)
    C1_gain: float = 2.0              # 主→从 速度通道 (≈ Zce 中频)
    C3_gain: float = 0.5              # 主→从 操作力通道 (= 1+C5)
    C2_gain: float = 0.5              # 从→主 环境力通道 (= 1+C6)
    C6_gain: float = -0.5             # 主端本地力反馈


class Master:
    """主端机械结构 + 本地控制器 + 四通道控制器(主端侧)."""

    def __init__(self, params: MasterParams | None = None, dt: float = 1e-4):
        self.p = params if params is not None else MasterParams()
        self.dt = float(dt)
        self.Xm: float = 0.0
        self.Vm: float = 0.0
        self.am: float = 0.0
        self.M1_last: float = 0.0
        self.F_motor_last: float = 0.0

    # ------------------------------------------------------------------
    def compute_M1(self, Fh: float) -> float:
        """计算主端送进通信通道的前向信号 M1 (论文式 18).

        M1 = C3·Fh + C1·Vm
        """
        M1 = self.p.C3_gain * Fh + self.p.C1_gain * self.Vm
        self.M1_last = M1
        return M1

    def update(
        self,
        Fh: float,
        sig_from_channel: float,
        d_sig_dVm: float = 0.0,
    ) -> tuple[float, float]:
        """根据操作者力 Fh 和通信通道反向信号推进一个时间步.

        Parameters
        ----------
        Fh : float
            操作者作用到主端的力.
        sig_from_channel : float
            通信通道的反向输出 sig_to_master.
        d_sig_dVm : float
            sig 中 ∝ Vm 那部分的总增益 (隐式离散用).
        """
        p = self.p

        # 半隐式: 把 Bm·Vm 与 d_sig_dVm·Vm 放到隐式侧
        sig_explicit = sig_from_channel - d_sig_dVm * self.Vm
        rhs = (
            (1.0 + p.C6_gain) * Fh
            - p.Km * self.Xm
            - sig_explicit
        )
        denom = p.Mm / self.dt + p.Bm + d_sig_dVm
        V_new = (p.Mm / self.dt * self.Vm + rhs) / denom

        self.am = (V_new - self.Vm) / self.dt
        self.Vm = V_new
        self.Xm = self.Xm + self.Vm * self.dt

        # 主端电机实际施加给操作者的反作用力 (重构, 仅用于绘图)
        # F_motor = Bm·Vm + Km·Xm + sig - C6·Fh
        self.F_motor_last = (
            p.Bm * self.Vm + p.Km * self.Xm
            + sig_from_channel
            - p.C6_gain * Fh
        )
        return self.Xm, self.Vm

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self.Xm = 0.0
        self.Vm = 0.0
        self.am = 0.0
        self.M1_last = 0.0
        self.F_motor_last = 0.0

    def state(self) -> dict:
        return dict(
            Xm=self.Xm, Vm=self.Vm, am=self.am,
            M1=self.M1_last, F_motor=self.F_motor_last,
        )
