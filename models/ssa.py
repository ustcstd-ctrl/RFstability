class SSAModel:
    def __init__(
        self,
        intra_amp_pct: float,
        intra_phi_deg: float,
        inter_amp_pct: float,
        inter_phi_deg: float,
    ):
        self.intra_amp = intra_amp_pct / 100.0
        self.intra_phi = intra_phi_deg
        self.inter_amp = inter_amp_pct / 100.0
        self.inter_phi = inter_phi_deg
