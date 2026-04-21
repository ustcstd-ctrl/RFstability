import numpy as np


class ModulatorModel:
    def __init__(self, droop_pct: float, inter_amp_pct: float, alpha_kly: float = 2.0):
        self.droop = droop_pct / 100.0
        self.inter_amp = inter_amp_pct / 100.0
        self.alpha_kly = alpha_kly

    def rf_power_perturbation(self):
        """返回 (脉冲内ΔP/P, 脉冲间ΔP/P)，已乘以速调管电压-功率灵敏度"""
        intra = self.alpha_kly * self.droop
        inter = self.alpha_kly * self.inter_amp
        return intra, inter
