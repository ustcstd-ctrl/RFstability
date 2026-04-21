import numpy as np


class CavityModel:
    def __init__(self, f0_mhz: float, QL: float):
        self.f0 = f0_mhz * 1e6
        self.QL = QL
        self.f_half = self.f0 / (2.0 * QL)  # 半带宽 (Hz)

    def transfer(self, f_perturbation: float) -> float:
        """一阶低通幅度响应 |H_cav(f)|"""
        return 1.0 / np.sqrt(1.0 + (f_perturbation / self.f_half) ** 2)
