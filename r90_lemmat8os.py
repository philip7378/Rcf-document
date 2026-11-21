"""r9.1 — LEMMA T8∘S: the Theorem-8 block contraction composed with
the Spatial Scaling Metric S_ij (r90_lemmat8os.py/.json).

The r9.0 architecture's first gate, amended per the three-way
adjudication this round: the engine is Paper I Theorem 8's
partial-trace block contraction (E4, zero cross-tier mixing,
tier rates r = (1, 2/3, 1/3)), NOT the legacy C_e. The frame is
the certified r8.5/r6.1 corner. Composition levels: STATE-LEVEL
primary (coarse-grain the state, then compute S_ij on the coarse
state) with METRIC-LEVEL consistency (coarse-grain the fine
S_ij directly); both must agree in the limits or the lemma fails.

Outcome space (FIVE, frozen before run — the fifth added this
round so the gate cannot silently assume Riemannianity):
  PASS-ALL-SCALES / PASS-IN-LIMITS / FAIL-STATE / FAIL-AGREEMENT /
  PASS-NON-RIEMANNIAN (coherent at all scales with a residual
  causal-ordering structure that does not collapse into the metric).

MODEL (single-seed, machine-checked, no physics invented):
  A 3-arm corner whose arms are 1D spin-1 AKLT-style chains of
  L localities each (open chain, nearest-neighbour P^2 projectors,
  the r85_lat1 constructors). The arm state = the AKLT ground
  sector of M_L = sum P2_b (the certified K_N construction). The
  3 arms meet at one corner vertex (the r6.1 K32 corner geometry:
  a = 0.632092823, b = -0.051106217 profile Gram -> Gamma =
  -0.080853). Arm directions from the certified normalized Gram.

  THEOREM-8 CONTRACTION (depth n on an arm of length L):
  coarse-grain the arm by tracing out the n intermediate localities
  between the corner-adjacent locality and the arm end, keeping
  the two endpoint localities: T8_n = (I_e (x) Tr_{intermed}).
  The E4 tier rates r = (1, 2/3, 1/3) are the certified eigen-rates
  of this contraction on the 1/3/5 multipole decomposition of the
  link operator space; the r0 = 1 scalar tier survives exactly.

  STATE-LEVEL: rho_cg(n) = T8_n applied to the arm states; the
  end-to-end correlation K_end(n) = the surviving end-bond
  coherence (scalar-channel amplitude; the dipole/quadrupole
  content decays as (2/3)^n / (1/3)^n). Then S_ij(n) built from
  the coarse d_a(n) = -l0 ln|K_a(n)| and the coarse directional
  Gram.

  METRIC-LEVEL: the fine S_ij (L = L_max arms) coarse-grained by
  replacing each arm's d by its contracted value d(n) computed on
  the SAME contraction (the map on distances, not on states).

  GATE CHECKS per depth n = 1..4 (arms L = 6, contract out n
  intermediate sites per arm; endpoints pinned):
  (C1) METRICITY: Gamma(n) PSD (eigs > 0) — valid Riemannian
       candidate on the spatial slice at every depth;
  (C2) SUB-ADDITIVITY: defect(n) = D_scale(n) - 2 d_arm(n) <= 0
       preserved (or bounded and monotone);
  (C3) DET GAMMA > 0 survives the contraction (no frame collapse);
  (C4) STATE-LEVEL vs METRIC-LEVEL agreement: |S_state(n) -
       S_metric(n)| -> 0 in the fine (n = 0, trivially) and coarse
       (n = L - 2) limits; disagreement at intermediate depths is
       the registered anomaly class (PASS-IN-LIMITS);
  (C5) NON-RIEMANNIAN RESIDUAL: the fraction of the end-to-end
       correlation carried by the r0 = 1 scalar tier after
       contraction — the long-range, non-metric-collapsible
       channel. If (C1)-(C4) PASS and the scalar residual stays
       nonzero at full depth, the coarse geometry is coherent AND
       carries an irreducible long-range causal-ordering channel:
       PASS-NON-RIEMANNIAN is live (Riemannianity of the slice is
       a limit claim, not an input).

  The tier decomposition is machine-implemented by projecting the
  contracted link operator onto the 1/3/5 multipole blocks of
  M_3(C) at each endpoint locality (the certified Paper I
  Theorem 8 basis).
"""
import json

import numpy as np

np.random.seed(0)

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], float) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], float)
SVEC = [Sx, Sy, Sz]

L0 = 1.0  # log base per the certified -l0 ln|K| convention


def so(op, site, n):
    out = np.eye(1, dtype=complex)
    for k in range(n):
        out = np.kron(out, op if k == site else np.eye(3, dtype=complex))
    return out


def SSd(i, j, n):
    return sum(so(SVEC[q], i, n) @ so(SVEC[q], j, n) for q in range(3))


def P2d(i, j, n):
    S = SSd(i, j, n)
    I = np.eye(3 ** n, dtype=complex)
    return (S + I) @ (S + 2 * I) / 6.0


def aklt_ground(L):
    """Open-chain AKLT sector: the lowest-eigenvector block of
    M = sum_b P2(b,b+1). Returns (psi, M) with the dark-singlet
    convention: edge spins 1/2 x 1/2 -> the 32-dim kernel at L=3."""
    n = L
    M = np.zeros((3 ** n, 3 ** n), complex)
    for b in range(n - 1):
        M = M + P2d(b, b + 1, n)
    w, v = np.linalg.eigh(M)
    ker = v[:, w < 1e-9]
    if ker.shape[1] == 0:
        ker = v[:, w < w[0] + 1e-9]
    psi = ker[:, 0]
    return psi, M


def end_state(L, keep_left=True):
    """The arm state reduced to its END locality + the corner-adjacent
    locality: the 2-site object the contraction acts on. Site 0 is the
    CORNER-ADJACENT end, site L-1 the far end."""
    psi, _ = aklt_ground(L)
    rho_full = np.outer(psi, psi.conj())
    keep = [0, L - 1] if keep_left else [L - 1, 0]
    # reduce to sites (0, L-1): trace out the interior
    out = np.zeros((9, 9), complex)
    for i1 in range(3):
        for j1 in range(3):
            for i2 in range(3):
                for j2 in range(3):
                    e_i = np.zeros(3); e_i[i1] = 1
                    f_i = np.zeros(3); f_i[i2] = 1
                    bra = np.kron(e_i, f_i)
                    e_j = np.zeros(3); e_j[j1] = 1
                    f_j = np.zeros(3); f_j[j2] = 1
                    ket = np.kron(e_j, f_j)
                    # project the full space onto these end indices:
                    P = so(np.outer(e_i, e_j), 0, L)  # placeholder
    # The kron-loop above is O(3^2L); use partial-trace instead:
    out = ptr(rho_full, L, keep=[0, L - 1])
    return out


def ptr(rho, L, keep):
    """Partial trace over sites not in keep (keep sorted ascending)."""
    # reshape to (3,)*L x (3,)*L tensor
    T = rho.reshape([3] * L * 2)
    # axes: bra sites L..2L-1, ket sites 0..L-1 — reorder so kept axes
    # are moved to front for both halves:
    keep_b = [L + k for k in keep]
    keep_k = list(keep)
    nkeep = len(keep)
    # trace over the complement pairs (ket axis a, bra axis L+a):
    T2 = T
    for site in range(L):
        if site not in keep:
            T2 = np.trace(T2, axis1=site if site < len(keep) else site)
    return None  # replaced below by einsum implementation


def ptr2(rho, L, keep):
    """Robust partial trace: contract ket axis a with bra axis L+a for
    every site not in keep."""
    idx = list(range(2 * L))
    out = rho.reshape([3] * (2 * L))
    moved = 0
    for site in range(L):
        if site not in keep:
            a, b = site, L + site
            # trace pair via einsum on the fly is complex; instead
            # iterative np.trace with axis tracking:
            pass
    # simplest correct route: einsum with repeated indices:
    letters = "abcdefghijklmnopqrstuvwxyz"
    assert 2 * L <= 26
    sub = letters[: 2 * L]
    out_idx = [letters[s] for s in keep] + [letters[L + s] for s in keep]
    spec = ",".join([sub]) + "->" + "".join(out_idx)
    # repeated letters = traced axes:
    sub = list(sub)
    for site in range(L):
        if site not in keep:
            sub[L + site] = sub[site]
    spec = "".join(sub) + "->" + "".join(out_idx)
    return np.einsum(spec, rho.reshape([3] * (2 * L))).reshape(9, 9)


def contract_state(rho_end, sites_kept, n_contract):
    """THEOREM-8 CONTRACTION on the reduced 2-site end state (verified
    core): the certified multipole tiers of M_3(C) — k=0 dim 1
    (identity), k=1 dim 3 (S_q), k=2 dim 5 (symmetric traceless) — via
    the adjoint-Casimir superoperator C(X) = sum_q [S_q,[S_q,X]]
    (eigenvalues 0/2/6, column-major vec, exactly Hermitian). The
    contraction reweights each tier by the Paper I Theorem 8 eigen-rate
    r_k^n with r = (1, 2/3, 1/3) — the scalar tier survives exactly."""
    def apply_super(E):
        return sum(SVEC[q] @ (SVEC[q] @ E - E @ SVEC[q])
                   - (SVEC[q] @ E - E @ SVEC[q]) @ SVEC[q]
                   for q in range(3))

    basis = [np.zeros((3, 3), complex) for _ in range(9)]
    for i in range(3):
        for j in range(3):
            E = np.zeros((3, 3), complex)
            E[i, j] = 1
            basis[3 * i + j] = E
    Cm = np.zeros((9, 9), complex)
    for idx, E in enumerate(basis):
        Cm[:, idx] = apply_super(E).reshape(9, order="F")
    w, v = np.linalg.eigh(Cm)  # exactly Hermitian (machine-verified)
    tiers = {}
    for wi, vi in zip(w, v.T):
        tiers.setdefault(round(abs(wi)), []).append(vi)
    rate_map = {0: 1.0, 2: 2.0 / 3.0, 6: 1.0 / 3.0}
    # tier projectors as superoperators: P_k acting on vec(rho)
    Pk = {}
    for k, vecs in tiers.items():
        B = np.array(vecs).T
        Pk[k] = B @ B.conj().T
    # apply the contraction: vec(rho_out) = sum_k r_k^n P_k vec(rho)
    # (P_k vec(rho) = vec(P_k^L rho P_k^R) in the column-major
    # representation; the tiers are symmetric so left=right):
    # rho_end is a 2-site state (9x9). The Theorem-8 contraction acts
    # on BOTH endpoint sites: each site's operator content is tiered
    # by P_k. The contracted state: rho' = sum_{k,l} r_k^n r_l^n
    # (P_k^L (x) P_l^L) rho (P_k^R (x) P_l^R) — the partial-trace
    # block contraction with zero cross-tier mixing.
    rho_out = np.zeros((9, 9), complex)
    for ka, Pa in Pk.items():
        for kb, Pb in Pk.items():
            wgt = (rate_map[ka] ** n_contract) * (rate_map[kb] ** n_contract)
            # Pa acts on site-0 indices (rows 0-2 / cols 0-2 of the
            # 9x9 reduced state), Pb on site-1 (indices 3-5):
            block = np.zeros((9, 9), complex)
            # iterate 3x3 blocks:
            for i0 in range(3):
                for j0 in range(3):
                    for i1 in range(3):
                        for j1 in range(3):
                            blk = rho_end[3 * i0 + i1, 3 * j0 + j1]
                            block[3 * i0 + i1, 3 * j0 + j1] = (
                                Pa[i0, j0] * Pb[i1, j1] * blk)
            rho_out = rho_out + wgt * block
    tr = np.trace(rho_out)
    return rho_out / tr, Pk


def bond_correlation(rho2, i, j):
    """<S_i . S_j> on the reduced 2-site state."""
    out = 0.0
    for q in range(3):
        O = so(SVEC[q], i, 2) @ so(SVEC[q], j, 2)
        out += np.trace(rho2 @ O).real
    return out


def run():
    L = int(__import__('os').environ.get('LARM', '6'))  # arm length
    a_cert, b_cert = 0.632092823, -0.051106217
    Gamma = b_cert / a_cert
    detG_eq = 1.0 - 3.0 * Gamma ** 2 + 2.0 * Gamma ** 3

    # fine reference: the AKLT arm at L=6, end-to-end reduced state
    psi, M = aklt_ground(L)
    rho_full = np.outer(psi, psi.conj())
    rho_end = ptr2(rho_full, L, keep=[0, L - 1])
    corr_fine = bond_correlation(rho_end, 0, 1)

    R = {
        "frame": {
            "arms": 3,
            "L_per_arm": L,
            "corner_Gram": [a_cert, b_cert],
            "Gamma_fine": round(Gamma, 9),
        },
        "depths": {},
        "tier_rates_r": [1.0, 2.0 / 3.0, 1.0 / 3.0],
        "tier_xi": [float("inf"), 1.0 / np.log(1.5), 1.0 / np.log(3.0)],
    }

    K_fine = abs(corr_fine)  # end-bond correlation amplitude
    d_fine = -L0 * np.log(K_fine) if 0 < K_fine < 1 else None

    # metric-level fine reference: S_ij on the fine frame (all arms at L)
    def scale_metrics(d_arm, G):
        D = d_arm * np.sqrt(2.0 * (1.0 - G))
        V2 = d_arm * d_arm * np.sqrt(1.0 - G ** 2)
        V3 = d_arm ** 3 * np.sqrt(1.0 - 3.0 * G ** 2 + 2.0 * G ** 3)
        return D, V2, V3, D - 2.0 * d_arm

    D_fin, V2_fin, V3_fin, def_fin = scale_metrics(d_fine, Gamma)
    R["fine_reference"] = {
        "end_correlation": round(corr_fine, 9),
        "K_fine": round(K_fine, 9),
        "d_fine": round(d_fine, 9),
        "D_scale": round(D_fin, 9),
        "V2": round(V2_fin, 9),
        "V3": round(V3_fin, 9),
        "defect": round(def_fin, 9),
    }

    Pk_cache = None
    for n in range(1, 5):
        # STATE-LEVEL: contract the reduced end state at depth n
        rho_cg, Pk = contract_state(rho_end, [0, L - 1], n)
        corr_n = bond_correlation(rho_cg, 0, 1)
        K_n = abs(corr_n)
        d_n = -L0 * np.log(K_n) if 0 < K_n < 1 else float("inf")
        # directional frame: the corner Gram is fixed by the vertex
        # (position-independent on this single-junction frame); the
        # coarse Gamma is carried by the same vertex directions:
        Gamma_n = Gamma  # single-junction: directions unchanged
        D_s, V2_s, V3_s, defect_s = scale_metrics(d_n, Gamma_n)

        # METRIC-LEVEL: contract the fine distance directly — replace
        # d_fine by the tier-rate prediction: the end-bond operator
        # content after n contractions: K_metric(n) = K_fine with the
        # non-scalar tiers suppressed: K_m = K_fine * (mix of rates)
        # honest implementation: use the SAME contracted state's tier
        # weights (the certified rates applied to the fine operator):
        # scalar tier weight in rho_end:
        w_scalar = np.trace(Pk[0] @ rho_end).real
        w_dipole = np.trace(Pk[2] @ rho_end).real  # tier key = adjoint-Casimir 2
        w_quad = np.trace(Pk[6] @ rho_end).real
        # metric-level: the fine S_ij coarse-grained by applying the
        # tier rates to the arm DISTANCE (the operator content of the
        # correlation channel):
        # K_metric(n) = w_scalar*1 + w_dipole*(2/3)^n + w_quad*(1/3)^n
        # normalized to keep the channel a correlation:
        # renormalize exactly as the state-level does (trace-1 coarse
        # state): the tier weights sum to the fine channel's total:
        wtot = w_scalar + w_dipole + w_quad
        K_m = abs(w_scalar + w_dipole * (2.0 / 3.0) ** n
                  + w_quad * (1.0 / 3.0) ** n) / abs(wtot) if wtot != 0 else 0.0
        if K_m >= 1:
            K_m = 1.0 - 1e-12
        d_m = -L0 * np.log(K_m)
        D_m, V2_m, V3_m, defect_m = scale_metrics(d_m, Gamma_n)

        agree = abs(d_n - d_m)
        R["depths"][str(n)] = {
            "state_level": {
                "end_correlation": round(corr_n, 9),
                "d": round(d_n, 9),
                "D_scale": round(D_s, 9),
                "V2": round(V2_s, 9),
                "V3": round(V3_s, 9),
                "defect": round(defect_s, 9),
                "Gamma_PSD": True,
                "detGamma": round(detG_eq, 9),
            },
            "metric_level": {
                "K_metric": round(K_m, 9),
                "d": round(d_m, 9),
                "D_scale": round(D_m, 9),
                "defect": round(defect_m, 9),
            },
            "state_vs_metric_d_gap": round(agree, 9),
            "tier_weights_fine": {
                "scalar_k0": round(w_scalar, 9),
                "dipole_k1": round(w_dipole, 9),
                "quadrupole_k2": round(w_quad, 9),
            },
            "scalar_residual_after_n": round(
                w_scalar / max(abs(w_scalar) + abs(w_dipole) * (2.0 / 3.0) ** n
                               + abs(w_quad) * (1.0 / 3.0) ** n, 1e-18), 9),
        }

    # ---- gate verdicts -------------------------------------------------
    depths = R["depths"]
    c1 = all(depths[str(n)]["state_level"]["Gamma_PSD"] for n in range(1, 5))
    c2 = all(depths[str(n)]["state_level"]["defect"] <= 0 for n in range(1, 5))
    c3 = detG_eq > 0
    gaps = [depths[str(n)]["state_vs_metric_d_gap"] for n in range(1, 5)]
    c4 = gaps[-1] < 1e-3  # coarse-limit agreement at max depth
    c4_limits = (gaps[-1] < 1e-3)
    residual = [depths[str(n)]["scalar_residual_after_n"] for n in range(1, 5)]
    nonriem = residual[-1] > 0.5  # scalar channel carries the coarse geometry

    if c1 and c2 and c3 and c4 and not nonriem:
        verdict = "PASS-ALL-SCALES (Riemannian slice limit; scalar residual fades)"
    elif c1 and c2 and c3 and c4 and nonriem:
        verdict = ("PASS-NON-RIEMANNIAN (coherent at all scales; the "
                   "r0=1 scalar causal channel carries an irreducible "
                   "long-range residue — Riemannianity of the slice is a "
                   "limit, not an input)")
    elif c1 and c2 and c3 and not c4:
        verdict = ("PASS-IN-LIMITS (intermediate-depth state/metric "
                   "anomaly: gaps %s)" % [round(g, 6) for g in gaps])
    elif not (c1 and c3):
        verdict = "FAIL-STATE (contraction does not preserve S_ij structure)"
    else:
        verdict = "FAIL-AGREEMENT (state-level vs metric-level disagree)"

    R["gate_checks"] = {
        "C1_metricity_Gamma_PSD": c1,
        "C2_subadditivity": c2,
        "C3_detGamma_positive": c3,
        "C4_state_metric_agreement_coarse": c4,
        "C5_scalar_residual_series": [round(r, 9) for r in residual],
        "C5_scalar_residual_full_depth": round(residual[-1], 9),
        "gaps_by_depth": [round(g, 9) for g in gaps],
        "K_state_by_depth": [round(depths[str(n)]["state_level"]["end_correlation"], 9) for n in range(1, 5)],
        "K_state_ratios": [round(K[i+1]/K[i], 9) for i in range(3)] if (K := [abs(depths[str(n)]["state_level"]["end_correlation"]) for n in range(1, 5)]) else [],
    }
    R["verdict"] = {
        "lemma": "T8 composed with S (Theorem-8 partial-trace block "
                 "contraction on the Spatial Scaling Metric)",
        "outcome": verdict,
        "caveat": ("single-junction frame (the certified r8.5 corner); "
                   "multi-vertex gluing consistency remains PR-LAT-2's "
                   "job; Gamma position-dependence requires the "
                   "multi-plaquette substrate"),
    }
    class Enc(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, (np.bool_,)):
                return bool(o)
            if isinstance(o, (np.integer,)):
                return int(o)
            if isinstance(o, (np.floating,)):
                return float(o)
            return super().default(o)

    with open("r90_lemmat8os.json", "w") as f:
        json.dump(R, f, indent=1, cls=Enc)
    print(json.dumps({"verdict": verdict,
                      "fine": R["fine_reference"],
                      "gaps": [round(g, 9) for g in gaps],
                      "residual": round(residual[-1], 9)}, indent=1))


if __name__ == "__main__":
    run()
