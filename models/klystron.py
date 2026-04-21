class KlystronModel:
    def __init__(self, ampm_coeff: float, alpha_kly: float = 2.0):
        """
        ampm_coeff: AM-PM 转换系数 (°/%)
        alpha_kly:  电压-功率灵敏度（速调管功率 ∝ V^alpha）
        """
        self.ampm_coeff = ampm_coeff
        self.alpha_kly = alpha_kly

    def phase_from_amp_perturbation(self, delta_p_over_p: float) -> float:
        """ΔP/P (分数) → 相位扰动 (°)"""
        return self.ampm_coeff * (delta_p_over_p * 100.0)
