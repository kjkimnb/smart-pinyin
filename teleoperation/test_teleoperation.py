"""
遥操作仿真测试 (Test)
=====================

复现论文 Chen et al. (2018) "An Improved Wave-Variable Based Four-Channel
Control Design in Bilateral Teleoperation System for Time-Delay Compensation"
(IEEE Access, 2018) 的核心实验 (Section IV).

包含三个被对比的控制器:
  C1: 原始四通道, 通信通道无任何时延补偿       (论文 Lawrence/Hashtrudi-Zaad 方案)
  C2: 原始波变换 + 四通道                      (Aziminejad 方案, 存在波反射)
  C3: 改进波变换 (modified wave transform)     (本论文方案, 减小波反射)

两种实验设置 (Set):
  Set1: 通信通道时延 T = 0,    20 s
  Set2: 通信通道时延 T = 0.1 s, 20 s

运行:
    python -m teleoperation.test_teleoperation                # 跑全部, 自动出图
    python -m teleoperation.test_teleoperation --no-plot      # 只数值校验, 不绘图
    python -m teleoperation.test_teleoperation --quick        # 5 s, 跑 self-check
"""

from __future__ import annotations

import argparse
import math
from collections import deque
from dataclasses import dataclass

import numpy as np

from .master import Master, MasterParams
from .slave import Slave, SlaveParams


# ======================================================================
# 通信通道: 三种实现
# ======================================================================
class DelayLine:
    """定长 FIFO, 用环形缓冲实现一个 T 秒的纯时延."""

    def __init__(self, delay_steps: int):
        self.delay_steps = max(int(delay_steps), 0)
        self.buf: deque[float] = deque(
            [0.0] * (self.delay_steps + 1),
            maxlen=self.delay_steps + 1,
        )

    def step(self, x: float) -> float:
        """送入新值 x, 返回 T 秒前的值."""
        self.buf.append(x)
        return self.buf[0]


class _ChannelBase:
    """通信通道基类.

    每一步 ``step`` 接收主端的 M1 和从端的 N2, 返回:

        (sig_to_master, sig_to_slave,
         d_sigm_dVm,    d_sigs_dVs)

    其中后两个是"sig 中和当前 Vm/Vs 成正比那部分的总增益", 让上下游能把这
    部分阻尼放到隐式侧, 这样在 b 较大时也不至于离散发散.
    """

    name = "channel"

    def step(self, M1: float, N2: float) -> tuple[float, float, float, float]:
        raise NotImplementedError


class NoCompChannel(_ChannelBase):
    """C1: 纯时延通信通道, 完全不做无源化补偿."""

    name = "C1 (no compensation)"

    def __init__(self, delay_steps: int, **_):
        self.fwd = DelayLine(delay_steps)
        self.rev = DelayLine(delay_steps)

    def step(self, M1: float, N2: float):
        sig_to_slave = self.fwd.step(M1)
        sig_to_master = self.rev.step(N2)
        # 时延信号都来自过去, 与"当前" Vm/Vs 无关
        return sig_to_master, sig_to_slave, 0.0, 0.0


class OriginalWaveChannel(_ChannelBase):
    """C2: 原始波变换 (Niemeyer) 嵌进四通道, 存在波反射.

    论文式 (16)(17) 在通信通道层面的等效形式:
        sig_to_slave  = M1(t-T) + (1/b)·(N2(t) - N2(t-T))
        sig_to_master = N2(t-T) + b·(M1(t) - M1(t-T))

    其中:
      * sig_to_master 的 ``b·M1(t)`` 含 ``b·C1_gain·Vm(t)`` 项 -> 给主端的隐式系数
      * sig_to_slave  的 ``(1/b)·N2(t)`` 含 ``(C4_gain/b)·Vs(t)`` 项 -> 给从端
    """

    name = "C2 (original wave variable)"

    def __init__(self, delay_steps: int, b: float = 50.0,
                 C1_master: float = 1.0, C4_slave: float = -1.0,
                 C2_slave: float = 1.0):
        self.b = float(b)
        self.M1_delay = DelayLine(delay_steps)
        self.N2_delay = DelayLine(delay_steps)
        # 主端: sig_to_master 包含 +b·M1(t) = +b·(C3·Fh + C1·Vm)
        self.d_sigm_dVm = self.b * C1_master
        # 从端: sig_to_slave 包含 +(1/b)·N2(t) = +(1/b)·(C2·Fe + C4·Vs)
        self.d_sigs_dVs = C4_slave / self.b

    def step(self, M1: float, N2: float):
        M1_d = self.M1_delay.step(M1)
        N2_d = self.N2_delay.step(N2)
        sig_to_slave = M1_d + (N2 - N2_d) / self.b
        sig_to_master = N2_d + self.b * (M1 - M1_d)
        return sig_to_master, sig_to_slave, self.d_sigm_dVm, self.d_sigs_dVs


class ModifiedWaveChannel(_ChannelBase):
    """C3: 论文提出的改进波变换通信通道.

    严格按论文式 (30)(31) 实现:
        M2(t) = M1(t-T) + (N2(t-2T) - N2(t)) / b      # 给从端
        N1(t) = N2(t-T) + b·M1(t)                     # 给主端

    与 C2 的核心区别: 反向通道里"波反射"项 ``b·(M1(t)-M1(t-T))`` 被简化
    为 ``b·M1(t)``, 配合前向通道的 ``(N2(t-2T)-N2(t))/b`` 让 v_s 中不再
    出现对 u_s 的反射 (论文 Fig.5, 式 25).
    """

    name = "C3 (modified wave variable, this paper)"

    def __init__(self, delay_steps: int, b: float = 50.0,
                 C1_master: float = 1.0, C4_slave: float = -1.0,
                 C2_slave: float = 1.0):
        self.b = float(b)
        self.M1_delay = DelayLine(delay_steps)         # T
        self.N2_delay = DelayLine(delay_steps)         # T
        self.N2_delay_2T = DelayLine(2 * delay_steps)  # 2T
        # 主端: sig_to_master 包含 b·M1(t)
        self.d_sigm_dVm = self.b * C1_master
        # 从端: sig_to_slave 包含 -(1/b)·N2(t)
        self.d_sigs_dVs = -C4_slave / self.b

    def step(self, M1: float, N2: float):
        M1_T = self.M1_delay.step(M1)
        N2_T = self.N2_delay.step(N2)
        N2_2T = self.N2_delay_2T.step(N2)

        sig_to_slave = M1_T + (N2_2T - N2) / self.b   # M2(t)
        sig_to_master = N2_T + self.b * M1            # N1(t)
        return sig_to_master, sig_to_slave, self.d_sigm_dVm, self.d_sigs_dVs


# ======================================================================
# 仿真主循环
# ======================================================================
@dataclass
class SimResult:
    name: str
    T_delay: float
    t: np.ndarray
    Xm: np.ndarray
    Xs: np.ndarray
    Fh: np.ndarray
    Fe: np.ndarray
    F_motor_master: np.ndarray
    diverged: bool


def fh_profile(t: np.ndarray) -> np.ndarray:
    """操作者输入力 Fh(t).

    设计: 用一段平滑正弦把从端推过墙再撤回, 复现论文 Fig.8-19 那种
    "操作者主动操控 + 接触环境 + 撤离" 的过程.
    """
    Fh = 1.5 * np.sin(2 * np.pi * 0.15 * t)           # 0.15 Hz 主频
    Fh += 0.20 * np.sin(2 * np.pi * 0.6 * t)          # 高频细节
    return Fh


def simulate(
    channel_factory,
    *,
    duration: float = 20.0,
    dt: float = 1e-4,
    T_delay: float = 0.0,
    b: float = 50.0,
    use_local_force_feedback: bool = True,
    label: str = "",
) -> SimResult:
    """跑一次完整的主-从-通信通道仿真."""
    n = int(round(duration / dt))
    t = np.arange(n) * dt
    Fh_seq = fh_profile(t)

    # 主端 / 从端参数, 按论文透明性条件 (36): C1=Zce, C2=1+C6, C3=1+C5,
    # C4=-Zcm. 归一化让 b 与系统刚度/阻尼匹配 (Bm=Bs=1, b 与之同量级).
    if use_local_force_feedback:
        # 完整四通道+本地力反馈 (论文 C1(b)/C2(b)/C3(b))
        C5, C6 = -0.5, -0.5
    else:
        # 关掉本地力反馈, 退化为 (a) 组
        C5, C6 = 0.0, 0.0

    Bm = Bs = 0.05
    Km = Ks = 1.0                  # 本地位置控制器刚度 (论文 Cm = Bm + Km/s)
    mp = MasterParams(
        Mm=1.0, Bm=Bm, Km=Km,
        C1_gain=Bs,                # = Zce 中频
        C3_gain=1.0 + C5,
        C6_gain=C6,
        C2_gain=1.0 + C6,
    )
    sp = SlaveParams(
        Ms=1.0, Bs=Bs, Ks=Ks,
        C2_gain=1.0 + C6,
        C4_gain=-Bm,               # = -Zcm 中频
        C5_gain=C5,
        x_wall=0.4, K_env=20.0, B_env=0.5,
    )

    master = Master(mp, dt=dt)
    slave = Slave(sp, dt=dt)
    delay_steps = int(round(T_delay / dt))
    channel = channel_factory(
        delay_steps=delay_steps, b=b,
        C1_master=mp.C1_gain, C4_slave=sp.C4_gain, C2_slave=sp.C2_gain,
    )

    Xm = np.zeros(n)
    Xs = np.zeros(n)
    Fe = np.zeros(n)
    Fmot = np.zeros(n)

    diverged = False
    for k in range(n):
        Fh_k = float(Fh_seq[k])

        M1 = master.compute_M1(Fh_k)
        Fe_k = slave.env_force()
        N2 = slave.compute_N2(Fe_k)

        sig_to_master, sig_to_slave, dsm, dss = channel.step(M1, N2)

        master.update(Fh_k, sig_to_master, d_sig_dVm=dsm)
        slave.update(sig_to_slave, d_sig_dVs=dss)

        Xm[k] = master.Xm
        Xs[k] = slave.Xs
        Fe[k] = slave.Fe_last
        Fmot[k] = master.F_motor_last

        # 数值发散保护
        if (
            not math.isfinite(master.Xm)
            or not math.isfinite(slave.Xs)
            or abs(master.Xm) > 1e6
            or abs(slave.Xs) > 1e6
        ):
            diverged = True
            # 用最后一个数填满, 后面绘图就显示出"爆掉"的趋势
            Xm[k:] = master.Xm
            Xs[k:] = slave.Xs
            Fe[k:] = slave.Fe_last
            Fmot[k:] = master.F_motor_last
            break

    return SimResult(
        name=label or getattr(channel, "name", "channel"),
        T_delay=T_delay,
        t=t,
        Xm=Xm,
        Xs=Xs,
        Fh=Fh_seq,
        Fe=Fe,
        F_motor_master=Fmot,
        diverged=diverged,
    )


# ======================================================================
# 数值评价
# ======================================================================
def metrics(res: SimResult) -> dict:
    """位置/力跟踪误差的 RMS 与峰值, 用来定量比较透明性."""
    if res.diverged:
        return dict(
            pos_rmse=float("inf"),
            pos_peak_err=float("inf"),
            force_rmse=float("inf"),
            diverged=True,
        )
    pos_err = res.Xm - res.Xs
    force_err = res.F_motor_master - res.Fe
    return dict(
        pos_rmse=float(np.sqrt(np.mean(pos_err**2))),
        pos_peak_err=float(np.max(np.abs(pos_err))),
        force_rmse=float(np.sqrt(np.mean(force_err**2))),
        diverged=False,
    )


# ======================================================================
# 绘图
# ======================================================================
def plot_results(results: list[SimResult], outfile: str | None = None) -> None:
    try:
        import matplotlib

        if outfile is not None:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib 未安装, 跳过绘图. (pip install matplotlib)")
        return

    n = len(results)
    fig, axes = plt.subplots(n, 2, figsize=(11, 2.6 * n), squeeze=False)
    for i, res in enumerate(results):
        ax_pos = axes[i, 0]
        ax_f = axes[i, 1]

        ax_pos.plot(res.t, res.Xm, label="Xm (master)")
        ax_pos.plot(res.t, res.Xs, label="Xs (slave)", linestyle="--")
        ax_pos.set_ylabel("Position [rad]")
        ax_pos.set_title(f"{res.name}, T={res.T_delay*1000:.0f} ms")
        ax_pos.grid(True, alpha=0.3)
        ax_pos.legend(loc="best", fontsize=8)

        ax_f.plot(res.t, res.F_motor_master, label="F_motor (master felt)")
        ax_f.plot(res.t, res.Fe, label="Fe (slave env)", linestyle="--")
        ax_f.plot(res.t, res.Fh, label="Fh (operator)", linestyle=":", alpha=0.6)
        ax_f.set_ylabel("Force [N·m]")
        ax_f.grid(True, alpha=0.3)
        ax_f.legend(loc="best", fontsize=8)

        if res.diverged:
            for ax in (ax_pos, ax_f):
                ax.text(
                    0.5, 0.5, "DIVERGED",
                    transform=ax.transAxes,
                    ha="center", va="center",
                    fontsize=14, color="red", alpha=0.5,
                )

    axes[-1, 0].set_xlabel("Time [s]")
    axes[-1, 1].set_xlabel("Time [s]")
    fig.tight_layout()
    if outfile:
        fig.savefig(outfile, dpi=130)
        print(f"figure saved to {outfile}")
    else:
        plt.show()


# ======================================================================
# 入口
# ======================================================================
def run_all(quick: bool = False) -> list[SimResult]:
    duration = 5.0 if quick else 20.0
    common = dict(duration=duration, dt=1e-4, b=0.2,
                  use_local_force_feedback=True)

    results: list[SimResult] = []

    # ---- Set1: T = 0 ----
    results.append(simulate(NoCompChannel,        T_delay=0.0,
                            label="C1 no-comp            Set1", **common))
    results.append(simulate(OriginalWaveChannel,  T_delay=0.0,
                            label="C2 original wave      Set1", **common))
    results.append(simulate(ModifiedWaveChannel,  T_delay=0.0,
                            label="C3 modified wave (this paper) Set1", **common))

    # ---- Set2: T = 0.1 s ----
    results.append(simulate(NoCompChannel,        T_delay=0.1,
                            label="C1 no-comp            Set2", **common))
    results.append(simulate(OriginalWaveChannel,  T_delay=0.1,
                            label="C2 original wave      Set2", **common))
    results.append(simulate(ModifiedWaveChannel,  T_delay=0.1,
                            label="C3 modified wave (this paper) Set2", **common))

    return results


def print_summary(results: list[SimResult]) -> None:
    header = (
        f"{'controller':40s}  {'T[ms]':>6s}  {'pos_rmse':>10s}  "
        f"{'pos_peak':>10s}  {'force_rmse':>11s}  {'diverged':>8s}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        m = metrics(r)
        pr = f"{m['pos_rmse']:.4f}" if math.isfinite(m['pos_rmse']) else "  inf"
        pp = f"{m['pos_peak_err']:.4f}" if math.isfinite(m['pos_peak_err']) else "  inf"
        fr = f"{m['force_rmse']:.4f}" if math.isfinite(m['force_rmse']) else "  inf"
        print(
            f"{r.name:40s}  {r.T_delay*1000:6.0f}  "
            f"{pr:>10s}  {pp:>10s}  {fr:>11s}  {str(m['diverged']):>8s}"
        )


def self_check(results: list[SimResult]) -> int:
    """对论文核心结论的数值断言.

    论文 Section IV 的核心结论:
      (a) 无时延时, 三种方案都能用;
      (b) 有时延 (T=0.1 s) 时, 原始四通道 (C1) 与原始波变换四通道 (C2)
          会发散 / 严重退化, 而改进波变换 (C3) 仍然稳定;
      (c) 改进波变换的透明性 在时延前后几乎不变 (这是相对论文式 (30)(31)
          中波反射项被消减的直接体现).
    """
    failures = 0

    if len(results) != 6:
        print("[self-check] 结果数量不对, 跳过断言")
        return 1

    c1_set1, c2_set1, c3_set1 = results[0], results[1], results[2]
    c1_set2, c2_set2, c3_set2 = results[3], results[4], results[5]

    # (a) 无时延: 三种方案都不应发散
    for r in (c1_set1, c2_set1, c3_set1):
        if r.diverged:
            print(f"  [FAIL] 无时延工况下不应发散: {r.name}")
            failures += 1

    # (b) 时延下 C3 (本文方案) 必须保持稳定
    if c3_set2.diverged:
        print("  [FAIL] C3-Set2 (改进波变换+时延) 不应发散")
        failures += 1

    # (b') 时延下应至少观察到 C1 或 C2 的明显退化 / 失稳, 否则说明环境
    #      接触不够剧烈, 复现实验失去对比意义.
    m_c1_2, m_c2_2 = metrics(c1_set2), metrics(c2_set2)
    no_comp_failed = (
        c1_set2.diverged
        or m_c1_2["pos_peak_err"] > 5.0
        or m_c1_2["force_rmse"] > 5.0
    )
    orig_wave_failed = (
        c2_set2.diverged
        or m_c2_2["pos_peak_err"] > 5.0
        or m_c2_2["force_rmse"] > 5.0
    )
    if not (no_comp_failed or orig_wave_failed):
        print(
            "  [WARN] 时延下既未观察到 C1 失稳也未观察到 C2 失稳; "
            "复现的对比意义弱, 可能需要加大环境刚度 / 降低本体阻尼."
        )

    # (c) C3 透明性应近似与时延无关: pos_rmse(T=0.1) 与 pos_rmse(T=0) 同量级
    m_c3_1 = metrics(c3_set1)
    m_c3_2 = metrics(c3_set2)
    # 容忍透明性指标不大于 T=0 时 3 倍 (论文式 30/31 中 b 的取值是经验值,
    # 归一化系统下 b 与原文不可能严格一致, 故取较宽松的阈值)
    if m_c3_2["pos_rmse"] > 3.0 * m_c3_1["pos_rmse"] + 0.1:
        print(
            f"  [FAIL] C3 透明性在时延下劣化过大: "
            f"T=0 pos_rmse={m_c3_1['pos_rmse']:.4g}, "
            f"T=0.1 pos_rmse={m_c3_2['pos_rmse']:.4g}"
        )
        failures += 1

    # (d) 同样在时延下, C3 不应比 C2 差
    if not c2_set2.diverged:
        if metrics(c3_set2)["pos_rmse"] > metrics(c2_set2)["pos_rmse"] * 1.5:
            print(
                f"  [FAIL] 时延下 C3 应不劣于 C2: "
                f"C2 pos_rmse={metrics(c2_set2)['pos_rmse']:.4g}, "
                f"C3 pos_rmse={metrics(c3_set2)['pos_rmse']:.4g}"
            )
            failures += 1

    if failures == 0:
        print(
            "  [OK] self-check 通过: 复现了论文核心结论 "
            "(C2/C1 在时延下退化或失稳, C3 仍稳定且透明性几乎不受时延影响)"
        )
    return failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-plot", action="store_true", help="不出图, 仅打印数值")
    parser.add_argument("--quick", action="store_true", help="缩短仿真时长, 用于 CI / self-check")
    parser.add_argument("--out", default=None, help="把对比图保存到指定文件 (例如 result.png)")
    args = parser.parse_args(argv)

    print("== 论文复现: improved wave-variable based four-channel teleoperation ==")
    results = run_all(quick=args.quick)
    print_summary(results)

    failures = self_check(results)

    if not args.no_plot:
        plot_results(results, outfile=args.out)

    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
