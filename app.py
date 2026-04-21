import streamlit as st
import numpy as np
import pandas as pd
import copy

from ui.sidebar import render_sidebar
from ui.plots import (
    plot_contributions,
    plot_sensitivity_heatmap,
    plot_param_scan,
    plot_cavity_response,
)
from models.system import compute, sensitivity_matrix
from models.llrf import LLRFModel

st.set_page_config(
    page_title="RF系统束流稳定性分析",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ 电子直线加速器 RF 系统束流稳定性分析工具")
st.caption("定性 + 定量评估各环节对束流能量/相位稳定性的影响")

mod, ssa, kly, cav, llrf, pulse_width = render_sidebar()

# 计算开环结果（强制开环）
llrf_open = LLRFModel(
    closed_loop=False,
    gain_db=0.0,
    bandwidth_khz=llrf.bandwidth_hz / 1e3,
    amp_noise_pct=llrf.amp_noise * 100.0,
    phi_noise_deg=llrf.phi_noise,
    cl_amp_stability_pct=llrf.cl_amp * 100.0,
    cl_phi_stability_deg=llrf.cl_phi,
)
result_open = compute(mod, ssa, kly, cav, llrf_open, pulse_width)
result_current = compute(mod, ssa, kly, cav, llrf, pulse_width)

tab1, tab2, tab3, tab4 = st.tabs(["📊 影响程度对比", "🔥 灵敏度矩阵", "📈 参数扫描", "🔬 腔体响应"])

# ── Tab 1：影响程度对比 ──
with tab1:
    mode_label = "闭环" if llrf.closed_loop else "开环"
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("当前模式", mode_label)
    col2.metric("ΔE/E RSS (开环)", f"{result_open.energy_rss():.4f} %")
    col3.metric(f"ΔE/E RSS ({mode_label})", f"{result_current.energy_rss():.4f} %")
    col4.metric(f"Δφ RSS ({mode_label})", f"{result_current.phase_rss():.4f} °")

    fig_e, fig_phi = plot_contributions(result_open, result_current)
    st.plotly_chart(fig_e, use_container_width=True)
    st.plotly_chart(fig_phi, use_container_width=True)

    with st.expander("查看数值明细"):
        df_e = pd.DataFrame({
            "环节": list(result_open.energy_dict().keys()),
            "开环 ΔE/E (%)": list(result_open.energy_dict().values()),
            f"{mode_label} ΔE/E (%)": list(result_current.energy_dict().values()),
        })
        df_phi = pd.DataFrame({
            "环节": list(result_open.phase_dict().keys()),
            "开环 Δφ (°)": list(result_open.phase_dict().values()),
            f"{mode_label} Δφ (°)": list(result_current.phase_dict().values()),
        })
        st.dataframe(df_e.set_index("环节").style.format("{:.5f}"), use_container_width=True)
        st.dataframe(df_phi.set_index("环节").style.format("{:.5f}"), use_container_width=True)

# ── Tab 2：灵敏度矩阵 ──
with tab2:
    st.info("灵敏度 = 各输入参数增加1个单位时，RSS总稳定性的变化量（数值偏导数）")
    matrix = sensitivity_matrix(mod, ssa, kly, cav, llrf, pulse_width)
    fig_hm = plot_sensitivity_heatmap(matrix)
    st.plotly_chart(fig_hm, use_container_width=True)

    df_sens = pd.DataFrame(matrix).T
    st.dataframe(df_sens.style.format("{:.6f}").background_gradient(cmap="RdYlGn_r", axis=None),
                 use_container_width=True)

# ── Tab 3：参数扫描 ──
with tab3:
    scan_options = {
        "调制器顶降 (%)": ("mod", "droop", 0.001, 1.0, mod.droop * 100),
        "调制器脉冲间 (%)": ("mod", "inter_amp", 0.001, 1.0, mod.inter_amp * 100),
        "SSA幅度脉冲内 (%)": ("ssa", "intra_amp", 0.001, 1.0, ssa.intra_amp * 100),
        "SSA相位脉冲内 (°)": ("ssa", "intra_phi", 0.001, 2.0, ssa.intra_phi),
        "SSA幅度脉冲间 (%)": ("ssa", "inter_amp", 0.001, 1.0, ssa.inter_amp * 100),
        "SSA相位脉冲间 (°)": ("ssa", "inter_phi", 0.001, 2.0, ssa.inter_phi),
        "LLRF幅度底噪 (%)": ("llrf", "amp_noise", 0.0001, 0.5, llrf.amp_noise * 100),
        "LLRF相位底噪 (°)": ("llrf", "phi_noise", 0.0001, 0.5, llrf.phi_noise),
        "LLRF闭环幅度稳定性 (%)": ("llrf", "cl_amp", 0.0001, 0.5, llrf.cl_amp * 100),
        "LLRF闭环相位稳定性 (°)": ("llrf", "cl_phi", 0.0001, 0.5, llrf.cl_phi),
        "AM-PM系数 (°/%)": ("kly", "ampm_coeff", 0.0, 2.0, kly.ampm_coeff),
        "环路增益 (dB)": ("llrf_gain_db", None, 0.0, 60.0, 20 * np.log10(llrf.gain_linear)),
        "腔体 QL": ("cav", "QL", 1e3, 1e6, cav.QL),
    }

    col_sel, col_range = st.columns([1, 2])
    with col_sel:
        param_name = st.selectbox("选择扫描参数", list(scan_options.keys()))
    obj_key, attr, vmin, vmax, vdef = scan_options[param_name]
    with col_range:
        scan_range = st.slider(
            "扫描范围",
            min_value=float(vmin), max_value=float(vmax),
            value=(float(vmin), float(vmax)),
            step=float((vmax - vmin) / 100),
        )

    scan_vals = np.linspace(scan_range[0], scan_range[1], 60)
    energy_scan, phase_scan = [], []

    for v in scan_vals:
        # 临时修改对应参数
        if obj_key == "mod":
            orig = getattr(mod, attr)
            setattr(mod, attr, v / 100.0 if "%" in param_name else v)
            r = compute(mod, ssa, kly, cav, llrf, pulse_width)
            setattr(mod, attr, orig)
        elif obj_key == "ssa":
            orig = getattr(ssa, attr)
            setattr(ssa, attr, v / 100.0 if "%" in param_name else v)
            r = compute(mod, ssa, kly, cav, llrf, pulse_width)
            setattr(ssa, attr, orig)
        elif obj_key == "kly":
            orig = getattr(kly, attr)
            setattr(kly, attr, v)
            r = compute(mod, ssa, kly, cav, llrf, pulse_width)
            setattr(kly, attr, orig)
        elif obj_key == "cav":
            orig = getattr(cav, attr)
            setattr(cav, attr, v)
            cav.f_half = cav.f0 / (2.0 * cav.QL)
            r = compute(mod, ssa, kly, cav, llrf, pulse_width)
            setattr(cav, attr, orig)
            cav.f_half = cav.f0 / (2.0 * cav.QL)
        elif obj_key == "llrf":
            orig = getattr(llrf, attr)
            setattr(llrf, attr, v / 100.0 if "%" in param_name else v)
            r = compute(mod, ssa, kly, cav, llrf, pulse_width)
            setattr(llrf, attr, orig)
        elif obj_key == "llrf_gain_db":
            orig_gain = llrf.gain_linear
            llrf.gain_linear = 10 ** (v / 20.0)
            r = compute(mod, ssa, kly, cav, llrf, pulse_width)
            llrf.gain_linear = orig_gain
        else:
            r = result_current
        energy_scan.append(r.energy_rss())
        phase_scan.append(r.phase_rss())

    fig_scan = plot_param_scan(scan_vals, energy_scan, phase_scan, param_name)
    st.plotly_chart(fig_scan, use_container_width=True)

# ── Tab 4：腔体响应 ──
with tab4:
    f_intra = 1.0 / (2.0 * pulse_width * 1e-6)
    st.info(f"腔体半带宽 = {cav.f_half:.2f} Hz　|　脉冲内扰动特征频率 = {f_intra:.0f} Hz　|　"
            f"腔体滤波系数 H = {cav.transfer(f_intra):.4f}")
    fig_cav = plot_cavity_response(cav.f0 / 1e6, cav.QL, f_intra)
    st.plotly_chart(fig_cav, use_container_width=True)
