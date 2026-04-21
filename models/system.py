import numpy as np
from dataclasses import dataclass
from typing import Dict

from .modulator import ModulatorModel
from .ssa import SSAModel
from .klystron import KlystronModel
from .cavity import CavityModel
from .llrf import LLRFModel


@dataclass
class ContributionResult:
    # 能量稳定性各项贡献 (%)
    dE_mod_intra: float = 0.0
    dE_mod_inter: float = 0.0
    dE_ssa_intra: float = 0.0
    dE_ssa_inter: float = 0.0
    dE_llrf_noise: float = 0.0
    dE_llrf_cl: float = 0.0
    # 相位稳定性各项贡献 (°)
    dphi_mod_ampm: float = 0.0
    dphi_ssa_intra: float = 0.0
    dphi_ssa_inter: float = 0.0
    dphi_ssa_ampm: float = 0.0
    dphi_llrf_noise: float = 0.0
    dphi_llrf_cl: float = 0.0

    def energy_rss(self) -> float:
        vals = [self.dE_mod_intra, self.dE_mod_inter,
                self.dE_ssa_intra, self.dE_ssa_inter,
                self.dE_llrf_noise, self.dE_llrf_cl]
        return float(np.sqrt(sum(v**2 for v in vals)))

    def phase_rss(self) -> float:
        vals = [self.dphi_mod_ampm, self.dphi_ssa_intra, self.dphi_ssa_inter,
                self.dphi_ssa_ampm, self.dphi_llrf_noise, self.dphi_llrf_cl]
        return float(np.sqrt(sum(v**2 for v in vals)))

    def energy_dict(self) -> Dict[str, float]:
        return {
            "调制器(脉冲内)": self.dE_mod_intra,
            "调制器(脉冲间)": self.dE_mod_inter,
            "SSA幅度(脉冲内)": self.dE_ssa_intra,
            "SSA幅度(脉冲间)": self.dE_ssa_inter,
            "LLRF幅度底噪": self.dE_llrf_noise,
            "LLRF闭环幅度稳定性": self.dE_llrf_cl,
        }

    def phase_dict(self) -> Dict[str, float]:
        return {
            "调制器→AM-PM": self.dphi_mod_ampm,
            "SSA相位(脉冲内)": self.dphi_ssa_intra,
            "SSA相位(脉冲间)": self.dphi_ssa_inter,
            "SSA幅度→AM-PM": self.dphi_ssa_ampm,
            "LLRF相位底噪": self.dphi_llrf_noise,
            "LLRF闭环相位稳定性": self.dphi_llrf_cl,
        }


def compute(
    mod: ModulatorModel,
    ssa: SSAModel,
    kly: KlystronModel,
    cav: CavityModel,
    llrf: LLRFModel,
    pulse_width_us: float,
) -> ContributionResult:
    f_intra = 1.0 / (2.0 * pulse_width_us * 1e-6)
    H_cav = cav.transfer(f_intra)
    S_intra = llrf.suppression_for_freq(f_intra)
    S_inter = 1.0  # 脉冲间扰动发生在重复频率，LLRF 脉冲内反馈无法跨脉冲修正
    dp_mod_intra, dp_mod_inter = mod.rf_power_perturbation()

    r = ContributionResult()

    # ── 能量贡献 ──
    r.dE_mod_intra  = 0.5 * dp_mod_intra * H_cav * S_intra * 100.0
    r.dE_mod_inter  = 0.5 * dp_mod_inter * S_inter * 100.0
    r.dE_ssa_intra  = 0.5 * ssa.intra_amp * H_cav * S_intra * 100.0
    r.dE_ssa_inter  = 0.5 * ssa.inter_amp * S_inter * 100.0
    r.dE_llrf_noise = 0.5 * llrf.amp_noise * 100.0
    r.dE_llrf_cl    = 0.5 * llrf.cl_amp * 100.0

    # ── 相位贡献 ──
    r.dphi_mod_ampm  = kly.phase_from_amp_perturbation(dp_mod_intra) * S_intra
    r.dphi_ssa_intra = ssa.intra_phi * S_intra
    r.dphi_ssa_inter = ssa.inter_phi * S_inter
    r.dphi_ssa_ampm  = kly.phase_from_amp_perturbation(ssa.intra_amp) * S_intra
    r.dphi_llrf_noise = llrf.phi_noise
    r.dphi_llrf_cl    = llrf.cl_phi

    return r


def sensitivity_matrix(
    mod: ModulatorModel,
    ssa: SSAModel,
    kly: KlystronModel,
    cav: CavityModel,
    llrf: LLRFModel,
    pulse_width_us: float,
    rel: float = 0.01,
) -> Dict[str, Dict[str, float]]:
    base = compute(mod, ssa, kly, cav, llrf, pulse_width_us)
    base_E = base.energy_rss()
    base_phi = base.phase_rss()

    def perturb_and_compute(attr_path, delta):
        obj, attr = attr_path
        orig = getattr(obj, attr)
        setattr(obj, attr, orig + delta)
        r = compute(mod, ssa, kly, cav, llrf, pulse_width_us)
        setattr(obj, attr, orig)
        dE = (r.energy_rss() - base_E) / delta if delta != 0 else 0.0
        dphi = (r.phase_rss() - base_phi) / delta if delta != 0 else 0.0
        return dE, dphi

    params = [
        ("调制器顶降",       (mod,  "droop"),     mod.droop * rel or rel),
        ("调制器脉冲间",     (mod,  "inter_amp"),  mod.inter_amp * rel or rel),
        ("SSA幅度(脉冲内)", (ssa,  "intra_amp"),  ssa.intra_amp * rel or rel),
        ("SSA相位(脉冲内)", (ssa,  "intra_phi"),  max(abs(ssa.intra_phi) * rel, 0.001)),
        ("SSA幅度(脉冲间)", (ssa,  "inter_amp"),  ssa.inter_amp * rel or rel),
        ("SSA相位(脉冲间)", (ssa,  "inter_phi"),  max(abs(ssa.inter_phi) * rel, 0.001)),
        ("LLRF幅度底噪",    (llrf, "amp_noise"),  llrf.amp_noise * rel or rel),
        ("LLRF相位底噪",    (llrf, "phi_noise"),  max(abs(llrf.phi_noise) * rel, 0.001)),
        ("LLRF闭环幅度稳定性", (llrf, "cl_amp"),  llrf.cl_amp * rel or rel),
        ("LLRF闭环相位稳定性", (llrf, "cl_phi"),  max(abs(llrf.cl_phi) * rel, 0.001)),
    ]

    matrix = {}
    for name, path, delta in params:
        dE, dphi = perturb_and_compute(path, delta)
        matrix[name] = {"ΔE/E (%/单位)": round(dE, 6), "Δφ (°/单位)": round(dphi, 6)}
    return matrix
