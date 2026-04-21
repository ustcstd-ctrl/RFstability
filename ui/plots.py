import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from models.system import ContributionResult


COLORS = px.colors.qualitative.Set2


def plot_contributions(result_open: ContributionResult, result_closed: ContributionResult):
    """分组柱状图：各环节对 ΔE/E 和 Δφ 的贡献（开环 vs 闭环）"""
    fig_e = go.Figure()
    fig_phi = go.Figure()

    labels = list(result_open.energy_dict().keys())
    vals_open_e = list(result_open.energy_dict().values())
    vals_closed_e = list(result_closed.energy_dict().values())
    vals_open_phi = list(result_open.phase_dict().values())
    vals_closed_phi = list(result_closed.phase_dict().values())

    fig_e.add_trace(go.Bar(name="开环", x=labels, y=vals_open_e, marker_color="#EF553B"))
    fig_e.add_trace(go.Bar(name="闭环", x=labels, y=vals_closed_e, marker_color="#636EFA"))
    fig_e.add_hline(y=result_open.energy_rss(), line_dash="dot", line_color="#EF553B",
                    annotation_text=f"开环RSS={result_open.energy_rss():.4f}%")
    fig_e.add_hline(y=result_closed.energy_rss(), line_dash="dot", line_color="#636EFA",
                    annotation_text=f"闭环RSS={result_closed.energy_rss():.4f}%")
    fig_e.update_layout(
        title="各环节对束流能量稳定性 ΔE/E 的贡献",
        yaxis_title="ΔE/E (%)",
        barmode="group",
        legend=dict(orientation="h", y=1.1),
        height=420,
    )

    phi_labels = list(result_open.phase_dict().keys())
    fig_phi.add_trace(go.Bar(name="开环", x=phi_labels, y=vals_open_phi, marker_color="#EF553B"))
    fig_phi.add_trace(go.Bar(name="闭环", x=phi_labels, y=vals_closed_phi, marker_color="#636EFA"))
    fig_phi.add_hline(y=result_open.phase_rss(), line_dash="dot", line_color="#EF553B",
                      annotation_text=f"开环RSS={result_open.phase_rss():.4f}°")
    fig_phi.add_hline(y=result_closed.phase_rss(), line_dash="dot", line_color="#636EFA",
                      annotation_text=f"闭环RSS={result_closed.phase_rss():.4f}°")
    fig_phi.update_layout(
        title="各环节对束流相位稳定性 Δφ 的贡献",
        yaxis_title="Δφ (°)",
        barmode="group",
        legend=dict(orientation="h", y=1.1),
        height=420,
    )

    return fig_e, fig_phi


def plot_sensitivity_heatmap(matrix: dict):
    """灵敏度矩阵热力图"""
    params = list(matrix.keys())
    outputs = list(next(iter(matrix.values())).keys())
    z = [[matrix[p][o] for o in outputs] for p in params]

    fig = go.Figure(go.Heatmap(
        z=z, x=outputs, y=params,
        colorscale="RdYlGn_r",
        text=[[f"{v:.4f}" for v in row] for row in z],
        texttemplate="%{text}",
        colorbar=dict(title="灵敏度"),
    ))
    fig.update_layout(
        title="灵敏度矩阵（各输入参数对输出的偏导数）",
        height=500,
        margin=dict(l=160),
    )
    return fig


def plot_param_scan(scan_values, energy_vals, phase_vals, param_name: str):
    """参数扫描折线图"""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=scan_values, y=energy_vals, name="ΔE/E (%)",
                             mode="lines+markers", line=dict(color="#EF553B")))
    fig.add_trace(go.Scatter(x=scan_values, y=phase_vals, name="Δφ (°)",
                             mode="lines+markers", line=dict(color="#636EFA"),
                             yaxis="y2"))
    fig.update_layout(
        title=f"参数扫描：{param_name}",
        xaxis_title=param_name,
        yaxis=dict(title="ΔE/E (%)", color="#EF553B"),
        yaxis2=dict(title="Δφ (°)", overlaying="y", side="right", color="#636EFA"),
        legend=dict(orientation="h", y=1.1),
        height=420,
    )
    return fig


def plot_cavity_response(cav_f0_mhz: float, cav_QL: float, f_intra: float):
    """腔体幅频响应曲线"""
    f0 = cav_f0_mhz * 1e6
    f_half = f0 / (2.0 * cav_QL)
    f_range = np.logspace(np.log10(max(f_half * 0.01, 1.0)), np.log10(f_half * 200), 500)
    H = 1.0 / np.sqrt(1.0 + (f_range / f_half) ** 2)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=f_range, y=20 * np.log10(H), name="|H_cav(f)|",
                             line=dict(color="#00CC96")))
    fig.add_vline(x=f_half, line_dash="dash", line_color="orange",
                  annotation_text=f"半带宽 {f_half:.1f} Hz", annotation_position="top right")
    fig.add_vline(x=f_intra, line_dash="dot", line_color="#AB63FA",
                  annotation_text=f"脉冲内扰动 {f_intra:.0f} Hz", annotation_position="top left")
    fig.update_layout(
        title="射频腔体幅频响应",
        xaxis_title="频率 (Hz)",
        yaxis_title="幅度 (dB)",
        xaxis_type="log",
        height=400,
    )
    return fig
