import streamlit as st
from models.modulator import ModulatorModel
from models.ssa import SSAModel
from models.klystron import KlystronModel
from models.cavity import CavityModel
from models.llrf import LLRFModel


def _tip(label, help_text, **kwargs):
    """带 help 提示的 number_input 封装"""
    return st.sidebar.number_input(label, help=help_text, **kwargs)


def render_sidebar():
    st.sidebar.title("参数输入")

    # ── 调制器 ──
    st.sidebar.header("🔌 高压脉冲调制器")
    mod_droop = _tip(
        "脉冲内顶降 (%)",
        "单个脉冲内高压电压从脉冲顶部到末尾的幅度下降量（相对值）。"
        "顶降通过速调管电压-功率灵敏度 α 转化为 RF 功率的脉冲内变化。"
        "典型范围：0.01% ~ 1%。",
        value=0.1, min_value=0.0, max_value=5.0, step=0.01, format="%.3f",
    )
    mod_inter = _tip(
        "脉冲间幅度稳定度 (%)",
        "相邻脉冲之间高压幅度的长期漂移或抖动（RMS 或峰峰值的一半）。"
        "反映调制器的长期重复性，直接影响束流能量的脉冲间一致性。"
        "典型范围：0.005% ~ 0.5%。",
        value=0.05, min_value=0.0, max_value=5.0, step=0.01, format="%.3f",
    )

    # ── SSA ──
    st.sidebar.header("📡 前级固态放大器 (SSA)")
    ssa_intra_amp = _tip(
        "脉冲内幅度稳定性 (%)",
        "单个脉冲内 SSA 输出功率的幅度波动（RMS）。"
        "该扰动经腔体一阶低通滤波后影响腔压，进而影响束流能量。"
        "典型范围：0.01% ~ 0.5%。",
        value=0.1, min_value=0.0, max_value=5.0, step=0.01, format="%.3f",
    )
    ssa_intra_phi = _tip(
        "脉冲内相位稳定性 (°)",
        "单个脉冲内 SSA 输出信号的相位抖动（RMS）。"
        "直接传递到腔体，影响束流相位稳定性。"
        "典型范围：0.01° ~ 1°。",
        value=0.1, min_value=0.0, max_value=10.0, step=0.01, format="%.3f",
    )
    ssa_inter_amp = _tip(
        "脉冲间幅度稳定性 (%)",
        "相邻脉冲之间 SSA 输出功率的幅度变化（RMS）。"
        "反映 SSA 的热漂移、电源波动等低频效应。"
        "典型范围：0.005% ~ 0.3%。",
        value=0.05, min_value=0.0, max_value=5.0, step=0.01, format="%.3f",
    )
    ssa_inter_phi = _tip(
        "脉冲间相位稳定性 (°)",
        "相邻脉冲之间 SSA 输出信号的相位变化（RMS）。"
        "低频相位漂移，影响束流相位的长期稳定性。"
        "典型范围：0.005° ~ 0.5°。",
        value=0.05, min_value=0.0, max_value=10.0, step=0.01, format="%.3f",
    )

    # ── 速调管 ──
    st.sidebar.header("⚡ 速调管")
    kly_ampm = _tip(
        "AM-PM 转换系数 (°/%)",
        "速调管的幅度-相位转换非线性系数：输入功率变化 1% 时，"
        "输出相位的变化量（度）。工作点越接近饱和，该系数越大。"
        "典型范围：0.1 ~ 2 °/%。",
        value=0.5, min_value=0.0, max_value=5.0, step=0.05, format="%.3f",
    )
    kly_alpha = _tip(
        "电压-功率灵敏度 α",
        "速调管输出 RF 功率对阴极电压的灵敏度指数：ΔP/P = α × ΔV/V。"
        "对于速调管，α ≈ 2（功率正比于电压平方）；"
        "实际值因工作点不同略有差异。典型范围：1.5 ~ 3。",
        value=2.0, min_value=0.5, max_value=5.0, step=0.1, format="%.2f",
    )

    # ── 腔体 ──
    st.sidebar.header("🔬 射频腔体")
    cav_f0 = _tip(
        "谐振频率 f₀ (MHz)",
        "射频腔体的谐振频率。常见加速器频率：S波段 2856 MHz、"
        "C波段 5712 MHz、L波段 1300 MHz。"
        "典型范围：100 ~ 12000 MHz。",
        value=2856.0, min_value=100.0, max_value=12000.0, step=1.0, format="%.1f",
    )
    cav_QL = _tip(
        "Loaded Q 值 (QL)",
        "腔体有载品质因数，决定腔体半带宽 f½ = f₀/(2QL)。"
        "QL 越大，腔体带宽越窄，对脉冲内扰动的滤波效果越强，"
        "但对失谐更敏感。典型范围：1×10³（行波腔）~ 1×10⁷（超导腔）。",
        value=1e5, min_value=1e3, max_value=1e7, step=1e4, format="%.0f",
    )

    # ── LLRF ──
    st.sidebar.header("🎛️ LLRF 低电平射频")
    closed_loop = st.sidebar.toggle(
        "闭环模式",
        value=True,
        help="开启后 LLRF 对各环节扰动进行主动抑制，抑制因子 S = 1/(1+G)。"
             "关闭则为开环，各扰动直接传递到束流。",
    )
    llrf_gain = _tip(
        "环路增益 (dB)",
        "LLRF 闭环的开环增益。增益越高，对扰动的抑制能力越强（S = 1/(1+G)）。"
        "但过高增益会降低相位裕度，影响稳定性。"
        "典型范围：20 ~ 60 dB。",
        value=40.0, min_value=0.0, max_value=80.0, step=1.0, format="%.1f",
    )
    llrf_bw = _tip(
        "闭环带宽 (kHz)",
        "LLRF 闭环系统的 -3dB 带宽。只有频率低于此带宽的扰动才能被有效抑制。"
        "脉冲内扰动频率 f ≈ 1/(2×脉冲宽度)，若超过带宽则无法抑制。"
        "典型范围：10 ~ 500 kHz。",
        value=100.0, min_value=1.0, max_value=2000.0, step=10.0, format="%.1f",
    )
    llrf_amp_noise = _tip(
        "幅度测量底噪 (%)",
        "LLRF 幅度检测通道的本底噪声（RMS），代表系统能分辨的最小幅度变化。"
        "该噪声作为残差直接注入输出，不被环路自身抑制。"
        "典型范围：0.001% ~ 0.05%。",
        value=0.01, min_value=0.0, max_value=1.0, step=0.001, format="%.4f",
    )
    llrf_phi_noise = _tip(
        "相位测量底噪 (°)",
        "LLRF 相位检测通道的本底噪声（RMS），代表系统能分辨的最小相位变化。"
        "该噪声作为残差直接注入输出，不被环路自身抑制。"
        "典型范围：0.001° ~ 0.05°。",
        value=0.01, min_value=0.0, max_value=1.0, step=0.001, format="%.4f",
    )
    llrf_cl_amp = _tip(
        "闭环幅度稳定性 (%)",
        "LLRF 闭环后系统综合幅度稳定性指标（含脉冲内+脉冲间，RMS）。"
        "这是 LLRF 控制器自身引入的残余幅度误差，已是闭环后的剩余量，"
        "不再被环路增益进一步抑制。典型范围：0.005% ~ 0.1%。",
        value=0.02, min_value=0.0, max_value=1.0, step=0.001, format="%.4f",
    )
    llrf_cl_phi = _tip(
        "闭环相位稳定性 (°)",
        "LLRF 闭环后系统综合相位稳定性指标（含脉冲内+脉冲间，RMS）。"
        "这是 LLRF 控制器自身引入的残余相位误差，已是闭环后的剩余量，"
        "不再被环路增益进一步抑制。典型范围：0.005° ~ 0.1°。",
        value=0.02, min_value=0.0, max_value=1.0, step=0.001, format="%.4f",
    )

    # ── 脉冲参数 ──
    st.sidebar.header("⏱️ 脉冲参数")
    pulse_width = _tip(
        "脉冲宽度 (μs)",
        "RF 脉冲的平顶宽度。用于估算脉冲内扰动的特征频率 f ≈ 1/(2×τ)，"
        "进而判断腔体滤波效果和 LLRF 带宽是否覆盖该扰动。"
        "典型范围：0.5 ~ 10 μs（常规加速器）。",
        value=3.0, min_value=0.1, max_value=100.0, step=0.1, format="%.1f",
    )

    mod  = ModulatorModel(mod_droop, mod_inter, alpha_kly=kly_alpha)
    ssa  = SSAModel(ssa_intra_amp, ssa_intra_phi, ssa_inter_amp, ssa_inter_phi)
    kly  = KlystronModel(kly_ampm, kly_alpha)
    cav  = CavityModel(cav_f0, cav_QL)
    llrf = LLRFModel(
        closed_loop=closed_loop,
        gain_db=llrf_gain,
        bandwidth_khz=llrf_bw,
        amp_noise_pct=llrf_amp_noise,
        phi_noise_deg=llrf_phi_noise,
        cl_amp_stability_pct=llrf_cl_amp,
        cl_phi_stability_deg=llrf_cl_phi,
    )

    return mod, ssa, kly, cav, llrf, pulse_width
