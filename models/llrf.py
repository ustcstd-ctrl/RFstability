import numpy as np


class LLRFModel:
    def __init__(
        self,
        closed_loop: bool,
        gain_db: float,
        bandwidth_khz: float,
        amp_noise_pct: float,
        phi_noise_deg: float,
        cl_amp_stability_pct: float,
        cl_phi_stability_deg: float,
    ):
        self.closed_loop = closed_loop
        self.gain_linear = 10 ** (gain_db / 20.0)
        self.bandwidth_hz = bandwidth_khz * 1e3
        # LLRF 自身残差（不被环路抑制）
        self.amp_noise = amp_noise_pct / 100.0
        self.phi_noise = phi_noise_deg
        # 闭环后综合幅度/相位稳定性（含脉冲内+脉冲间）
        self.cl_amp = cl_amp_stability_pct / 100.0
        self.cl_phi = cl_phi_stability_deg

    def suppression(self) -> float:
        """闭环抑制因子 S = 1/(1+G)，开环时 S=1"""
        if self.closed_loop:
            return 1.0 / (1.0 + self.gain_linear)
        return 1.0

    def suppression_for_freq(self, f_perturbation: float) -> float:
        """仅当扰动频率在 LLRF 带宽内时才抑制"""
        if not self.closed_loop:
            return 1.0
        if f_perturbation <= self.bandwidth_hz:
            return self.suppression()
        return 1.0
