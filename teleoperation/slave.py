"""
从端模块 (Slave)
================

复现论文 Chen et al. (2018) "An Improved Wave-Variable Based Four-Channel
Control Design in Bilateral Teleoperation System for Time-Delay Compensation"
中的从端 (slave) + 简化的工作环境 (墙壁 / 弹簧-阻尼).

论文映射
--------
- 物理模型 (论文式 5):
      C1·Vm - Zce·Vs = (1+C5)·Fe - C3·Fh
      => Ms·a_s + Bs·Vs + Ks·Xs = sig_to_slave - (1+C5)·Fe
  其中 sig_to_slave 在不同通信通道形式下:
      * 纯时延:           sig = M1(t-T) = C3·Fh(t-T) + C1·Vm(t-T)
      * 改进波变换 (本论文): sig = M2(t)  = M1(t-T) + (N2(t-2T)-N2(t))/b
        (论文式 30)

- 从端发出到通信通道的"反向信号" (论文式 19):
      N2 = C2·Fe + C4·Vs
  ``C4·Vs`` 在论文里取 -Zcm·Vs (中频段 ≈ -Bm·Vs), 把从端速度反馈给主端,
  让操作者能从主端"感觉到"从端的运动状态.

环境 Fe
-------
单边软墙 (弹簧+阻尼). 与论文 Section IV 实验中"操作者带动从端碰到工作环
境"的场景定性一致.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SlaveParams:
    """从端 + 环境参数."""

    Ms: float = 1.0
    Bs: float = 2.0
    Ks: float = 0.0

    # 四通道增益 (按论文透明性条件 (36) 配)
    C2_gain: float = 0.5              # 从→主 环境力通道 (= 1+C6)
    C4_gain: float = -2.0             # 从→主 速度通道   (≈ -Zcm 中频)
    C5_gain: float = -0.5             # 从端本地力反馈

    # 单边软墙
    x_wall: float = 0.5
    K_env: float = 20.0
    B_env: float = 1.0


class Slave:
    """从端机械结构 + 本地控制器 + 四通道控制器(从端侧) + 环境."""

    def __init__(self, params: SlaveParams | None = None, dt: float = 1e-4):
        self.p = params if params is not None else SlaveParams()
        self.dt = float(dt)
        self.Xs: float = 0.0
        self.Vs: float = 0.0
        self.as_: float = 0.0
        self.N2_last: float = 0.0
        self.Fe_last: float = 0.0

    # ------------------------------------------------------------------
    def env_force(self) -> float:
        """单边软墙环境力 Fe(Xs, Vs)."""
        p = self.p
        if self.Xs <= p.x_wall:
            return 0.0
        Fe = p.K_env * (self.Xs - p.x_wall) + p.B_env * self.Vs
        return max(Fe, 0.0)

    def compute_N2(self, Fe: float) -> float:
        """计算从端送进通信通道的反向信号 N2 (论文式 19).

        N2 = C2·Fe + C4·Vs
        """
        N2 = self.p.C2_gain * Fe + self.p.C4_gain * self.Vs
        self.N2_last = N2
        return N2

    def update(
        self,
        sig_from_channel: float,
        d_sig_dVs: float = 0.0,
    ) -> tuple[float, float, float]:
        """根据通信通道送来的前向信号推进一个时间步.

        从端动力学 (论文式 5 改写):
            Ms·V' + Bs·V + Ks·X = sig_from_channel - (1+C5)·Fe

        Parameters
        ----------
        sig_from_channel : float
            通信通道前向输出 sig_to_slave.
        d_sig_dVs : float, optional
            sig 中 ∝ Vs 那部分的总增益, 用于隐式离散.
        """
        p = self.p
        Fe = self.env_force()
        self.Fe_last = Fe

        in_contact = self.Xs > p.x_wall
        env_damping = p.B_env if in_contact else 0.0
        env_spring = p.K_env * (self.Xs - p.x_wall) if in_contact else 0.0

        sig_explicit = sig_from_channel - d_sig_dVs * self.Vs
        rhs = (
            sig_explicit
            - p.Ks * self.Xs
            - (1.0 + p.C5_gain) * env_spring
        )
        denom = (
            p.Ms / self.dt
            + p.Bs
            - d_sig_dVs
            + (1.0 + p.C5_gain) * env_damping
        )
        V_new = (p.Ms / self.dt * self.Vs + rhs) / denom

        self.as_ = (V_new - self.Vs) / self.dt
        self.Vs = V_new
        self.Xs = self.Xs + self.Vs * self.dt
        return self.Xs, self.Vs, Fe

    # ------------------------------------------------------------------
    def reset(self) -> None:
        self.Xs = 0.0
        self.Vs = 0.0
        self.as_ = 0.0
        self.N2_last = 0.0
        self.Fe_last = 0.0

    def state(self) -> dict:
        return dict(
            Xs=self.Xs, Vs=self.Vs, as_=self.as_,
            N2=self.N2_last, Fe=self.Fe_last,
        )
