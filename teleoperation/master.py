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

- 主端从通信通道收到的"反向信号" sig_to_master, 形式视通信通道而定:
      * 无补偿 / 纯时延通道:   sig = N2(t-T) = C2·Fe(t-T) + C4·Vs(t-T)
      * 改进波变换通道:        sig = N1(t)  = N2(t-T) + b·M1(t)   (论文式 31)

关于 Fh 的获取
--------------
论文中的 Fh 是操作者作用到主端的物理力, 与"主端电机输出力"是两回事.
本模块给出三种方式拿到 Fh, 供仿真 / 真实硬件挑选:

  (i)  仿真理想情况: 直接把 Fh 作为已知信号传入 ``update``;
  (ii) 真实硬件有力传感器: 用传感器读数代入 ``update``;
  (iii) 真实硬件没有力传感器, 但电机能读电流 (例如 BLDC + FOC 下的 I_q):
       使用 ``CurrentBasedFhObserver`` (Murakami 风格的反应力观测器, RFOB).

   ★ 用户场景就是 (iii). 详细推导见 ``CurrentBasedFhObserver`` 的 docstring.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional


# ======================================================================
# 主端动力学 / 控制器参数
# ======================================================================
@dataclass
class MasterParams:
    """主端参数 (论文动力学和四通道控制器)."""

    Mm: float = 1.0                   # 主端等效惯量
    Bm: float = 2.0                   # 主端阻尼   (Cm 的 B 项, 含本地控制器虚拟黏滞)
    Km: float = 0.0                   # 主端刚度   (Cm 的 K 项)

    # 四通道增益 (透明性条件 (36): C2 = 1+C6, C3 = 1+C5)
    C1_gain: float = 2.0              # 主→从 速度通道 (≈ Zce 中频)
    C3_gain: float = 0.5              # 主→从 操作力通道 (= 1+C5)
    C2_gain: float = 0.5              # 从→主 环境力通道 (= 1+C6)
    C6_gain: float = -0.5             # 主端本地力反馈


# ======================================================================
# 基于电机电流的 Fh 反应力观测器
# ======================================================================
@dataclass
class FhObserverParams:
    """基于电机电流的 Fh 反应力观测器参数.

    BLDC + FOC 控制下, q 轴电流 I_q 与电机输出力矩成正比:
        τ_motor = Kt · I_q          (旋转关节, 单位 N·m)
    或线性执行器:
        F_motor = Kt · I            (单位 N)
    Kt 是力矩常数 (motor torque constant, 厂家手册可查).

    关键点
    ------
    这里的 ``M_phys`` 和 ``B_phys`` 必须是主端机械的"物理"惯量和黏滞, 不是
    论文 Master 闭环里的 Mm / Bm. 论文 Bm 是控制器 Cm = Bm + Km/s 的一部分,
    那是 motor 自己产生的"虚拟阻尼", 已经被算进 F_motor = Kt·I_q 里了, 不能
    再当成机械本体阻尼.

    omega_cutoff (rad/s) 是 RFOB 的低通截止. 越高响应越快, 噪声越大.
    工程经验: 取 2π·(20~100 Hz), 与编码器采样率/电流环带宽匹配.
    """

    M_phys: float = 1.0               # 主端机械物理惯量
    B_phys: float = 0.05              # 主端机械物理黏滞 (本体, 不含控制器)
    Kt: float = 0.05                  # 电机力矩常数 (N·m/A 或 N/A)
    omega_cutoff: float = 200.0       # RFOB 低通截止角频率 (rad/s, ≈32 Hz)


class CurrentBasedFhObserver:
    """用 BLDC q 轴电流估计操作者作用力 Fh 的反应力观测器 (Murakami RFOB).

    推导
    ----
    主端机械的物理动力学 (无外部刚度, 自由握把):
        M·V̇ = Fh - F_motor - B·V
        => Fh = M·V̇ + F_motor + B·V                            (1)

    其中 ``F_motor = Kt·I_q`` 由电流测量得到, ``V`` 由编码器微分得到, 但
    式 (1) 需要对 V 再求一次导数 (即 V̇), 噪声大. 用 Murakami 技巧绕开:

    引入辅助状态 ``w`` 满足
        ẇ = -ω·w + ω·(B·V - F_motor - ω·M·V)                   (2)

    并定义
        F̂h ≜ w + ω·M·V                                         (3)

    可证明 ``F̂h(s) = ω / (s + ω) · Fh(s)``, 即 RFOB 的输出就是 Fh 经过一个
    一阶低通滤波器, 不再含 V̇.

    验证 (代入 w = F̂h - ω·M·V 进 (2)):
        d(F̂h - ω·M·V)/dt = -ω·(F̂h - ω·M·V) + ω·(B·V - F_motor - ω·M·V)
        F̂h_dot - ω·M·V̇  = -ω·F̂h + ω²·M·V + ω·B·V - ω·F_motor - ω²·M·V
        F̂h_dot           = ω·M·V̇ + ω·B·V - ω·F_motor - ω·F̂h
                         = ω·(M·V̇ + B·V - F_motor) - ω·F̂h
                         = ω·Fh - ω·F̂h                          [代入 (1)]
        => F̂h_dot + ω·F̂h = ω·Fh   ✓

    使用
    ----
    >>> obs = CurrentBasedFhObserver(FhObserverParams(M_phys=0.05, B_phys=0.02,
    ...                                               Kt=0.04, omega_cutoff=200.0),
    ...                              dt=1e-4)
    >>> Fh_hat = obs.update(V=current_velocity, I_q=read_motor_current_q())
    """

    def __init__(self, params: FhObserverParams | None = None, dt: float = 1e-4):
        self.p = params if params is not None else FhObserverParams()
        self.dt = float(dt)
        self.w: float = 0.0           # 辅助状态 (式 2)
        self.Fh_hat: float = 0.0      # 上一次估计值

    def update(self, V: float, I_q: float) -> float:
        """推进观测器一步.

        Parameters
        ----------
        V : float
            主端关节/线性速度 (从编码器计算).
        I_q : float
            BLDC 的 q 轴电流测量值 (FOC 下与转矩成正比).

        Returns
        -------
        Fh_hat : float
            操作者作用力的低通估计.
        """
        p = self.p
        F_motor = p.Kt * I_q
        # 式 (2): ẇ = -ω·w + ω·(B·V - F_motor - ω·M·V)
        # 用半隐式离散保证大 omega 下也无偏:
        #   (w_new - w_old)/dt = -ω·w_new + ω·(B·V - F_motor - ω·M·V)
        omega = p.omega_cutoff
        rhs = omega * (p.B_phys * V - F_motor - omega * p.M_phys * V)
        self.w = (self.w + self.dt * rhs) / (1.0 + self.dt * omega)
        # 式 (3): F̂h = w + ω·M·V
        self.Fh_hat = self.w + omega * p.M_phys * V
        return self.Fh_hat

    def reset(self) -> None:
        self.w = 0.0
        self.Fh_hat = 0.0


# ======================================================================
# 主端
# ======================================================================
class Master:
    """主端机械结构 + 本地控制器 + 四通道控制器(主端侧).

    可选地挂载一个 ``CurrentBasedFhObserver``, 让没有力传感器的硬件
    (例如 Phantom Touch / 自研 BLDC 主端) 直接从电机电流估计 Fh.
    """

    def __init__(
        self,
        params: MasterParams | None = None,
        dt: float = 1e-4,
        fh_observer: Optional[CurrentBasedFhObserver] = None,
        read_current: Optional[Callable[[], float]] = None,
    ):
        self.p = params if params is not None else MasterParams()
        self.dt = float(dt)
        self.Xm: float = 0.0
        self.Vm: float = 0.0
        self.am: float = 0.0
        self.M1_last: float = 0.0
        self.F_motor_last: float = 0.0

        self.fh_obs = fh_observer
        self.read_current = read_current  # 用户提供的电流读取函数 (无参数, 返回 I_q)
        self.Fh_hat_last: float = 0.0

    # ------------------------------------------------------------------
    def compute_M1(self, Fh: float) -> float:
        """计算主端送进通信通道的前向信号 M1 (论文式 18).

        M1 = C3·Fh + C1·Vm
        """
        M1 = self.p.C3_gain * Fh + self.p.C1_gain * self.Vm
        self.M1_last = M1
        return M1

    # ------------------------------------------------------------------
    # Fh 估计 (基于电机电流的 RFOB)
    # ------------------------------------------------------------------
    def estimate_Fh_from_current(self, I_q: float | None = None) -> float:
        """用挂载的 RFOB 估计 Fh.

        Parameters
        ----------
        I_q : float, optional
            BLDC 的 q 轴电流测量值. 如果不传, 则尝试调用构造时给的
            ``read_current`` 回调.
        """
        if self.fh_obs is None:
            raise RuntimeError(
                "Master 未挂载 fh_observer; 请在构造时传入 "
                "CurrentBasedFhObserver(...) 实例."
            )
        if I_q is None:
            if self.read_current is None:
                raise RuntimeError(
                    "未提供 I_q 参数, 也未在构造时设置 read_current 回调."
                )
            I_q = float(self.read_current())
        Fh_hat = self.fh_obs.update(self.Vm, I_q)
        self.Fh_hat_last = Fh_hat
        return Fh_hat

    # ------------------------------------------------------------------
    def update(
        self,
        Fh: float,
        sig_from_channel: float,
        d_sig_dVm: float = 0.0,
    ) -> tuple[float, float]:
        """根据操作者力 Fh (或其估计值) 和通信通道反向信号推进一个时间步.

        Parameters
        ----------
        Fh : float
            操作者作用到主端的力. 可以是:
              * 仿真里的真值;
              * 力传感器读数;
              * ``estimate_Fh_from_current(I_q)`` 的返回值 (RFOB 估计).
        sig_from_channel : float
            通信通道的反向输出 sig_to_master.
        d_sig_dVm : float
            sig 中 ∝ Vm 那部分的总增益 (隐式离散用).
        """
        p = self.p

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

        # 主端电机实际施加给操作者的反作用力 (= Kt·I_q, 重构, 用于绘图 / RFOB 注入)
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
        self.Fh_hat_last = 0.0
        if self.fh_obs is not None:
            self.fh_obs.reset()

    def state(self) -> dict:
        return dict(
            Xm=self.Xm, Vm=self.Vm, am=self.am,
            M1=self.M1_last, F_motor=self.F_motor_last,
            Fh_hat=self.Fh_hat_last,
        )


# ======================================================================
# 单独运行: RFOB 数值演示
# ======================================================================
def _demo_rfob() -> None:
    """RFOB 自检 / 演示.

    构造一个最小化的"自由握把"主端 (无通信通道, 无环境), 仿真 ground-truth
    的 Fh 推动主端, 把它产生的 motor 反作用力折算成"假想电流" I_q 喂给
    RFOB, 然后比较 F̂h 与 Fh 真值. 跑两次:
      (a) 理想电流测量;
      (b) I_q 上叠加 5% 高斯噪声 (模拟 ADC 量化和 EMI).
    """
    import numpy as np

    rng = np.random.default_rng(0)

    dt = 1e-4
    duration = 3.0
    n = int(duration / dt)
    t = np.arange(n) * dt

    Fh_true = 1.0 * np.sin(2 * np.pi * 0.5 * t) + 0.3 * np.sin(2 * np.pi * 3.0 * t)

    # 自由握把: 论文里的 Bm 是控制器项, 已经包含在 motor 命令里; 这里把
    # 它设为 0 让 master.update 中的 F_motor 正好就是"motor 物理输出力",
    # 与硬件 RFOB 看到的电流·Kt 一致. 真实硬件如果带本体黏滞, 应在
    # FhObserverParams.B_phys 里填本体值, 而不是控制器值.
    mp = MasterParams(
        Mm=0.05, Bm=0.0, Km=0.0,
        C1_gain=0.0, C3_gain=0.0, C2_gain=0.0, C6_gain=0.0,
    )
    obs_p = FhObserverParams(
        M_phys=0.05, B_phys=0.0, Kt=0.04, omega_cutoff=1000.0,
    )

    print("== CurrentBasedFhObserver demo ==")
    print(f"  duration     : {duration:.2f} s, dt = {dt*1e6:.0f} µs")
    print(f"  Kt           : {obs_p.Kt} N·m/A")
    print(f"  omega_cutoff : {obs_p.omega_cutoff} rad/s "
          f"(≈ {obs_p.omega_cutoff / (2*3.14159):.1f} Hz)")

    # I_q 数量级 ≈ Fh / Kt ≈ 0.7 / 0.04 ≈ 17 A; 把噪声 std 取 0.5 A (≈ 3%)
    for noise_label, noise_std in [("ideal", 0.0), ("noisy I_q (sigma=0.5A)", 0.5)]:
        obs = CurrentBasedFhObserver(obs_p, dt=dt)
        master = Master(mp, dt=dt, fh_observer=obs)

        Fh_hat_seq = np.zeros(n)
        for k in range(n):
            Fh_k = float(Fh_true[k])
            master.compute_M1(Fh_k)
            master.update(Fh_k, sig_from_channel=0.0)
            # 由 master.update 重构出的 F_motor 即是电机当前真实输出力,
            # 折算成 q 轴电流, 再叠上测量噪声后送进 RFOB
            I_q = master.F_motor_last / obs_p.Kt
            if noise_std:
                I_q = I_q + rng.normal(0.0, noise_std)
            Fh_hat_seq[k] = master.estimate_Fh_from_current(I_q)

        skip = int(0.5 / dt)
        err = Fh_true[skip:] - Fh_hat_seq[skip:]
        rmse = float(np.sqrt(np.mean(err**2)))
        rel = rmse / float(np.sqrt(np.mean(Fh_true[skip:] ** 2)))
        print(f"  -- {noise_label} --")
        print(f"     Fh true RMS    : {np.sqrt(np.mean(Fh_true**2)):.4f}")
        print(f"     F̂h estimate RMS: {np.sqrt(np.mean(Fh_hat_seq**2)):.4f}")
        print(f"     RMSE           : {rmse:.4f}  ({rel*100:.2f} %)")


if __name__ == "__main__":
    _demo_rfob()
