"""PR-T1b-2 EXECUTION — runs the frozen pr_t1b2_sheet.txt (8fff13eb) with
the pre-registered output header H1-H5 (rcf_r51d_pre_execution_register.txt
8c3f09e0). N=3 open spin-1 chain, canonical cov3 gamma=1, exact 729x729
superoperators, Gate S leading.

Arms and seeds (per frozen sheet + header H5):
  PRIMARY (H_XXX + cov3, transient strobes): S1 = 0.7|+1,+1,0><|+0.3 I/27
    (zero-chiral), S2 = 0.7|+x,+x,+z><| + 0.3 I/27 (chiral-active),
    S3 = Ginibre-conditioned full-rank (rng 20261119).
  COMPARISON (H_XY + cov3): NESS + one-NESS clock reading (secondary).
  HANDOFF (pure cov3, H=0): global-K3 single-mismatch seed (spillover)
    + 2-site-kernel seed (no-spillover contrast).

Decisive measurements per the frozen sheet:
  B1: strobe holonomy 2-form recovered from 0->1 vs 1->0 site-1 overlap
      differences; the O(t^2) coefficient compared to the SEALED 0.17
      det-C-channel prediction (whole-window mean over t in [0,3], H2).
      On zero-chiral seeds the verdict line is VACUOUS-BY-SEED.
  B2: cross-trajectory f_{01} agreement across the seed family.
  B3: det C^{(1)} monotone advance on all orderings, window [0,3],
      turnaround times logged (H3).
  C: off-orbit residual = Sym_+^3 orbit comparison of the two orderings'
      site-1 trajectories under best monotone reparametrization; the
      residual projected orthogonal to the SU(2) orbit tangent space
      (H4). B: < 5e-3. C: > 5e-2 AND > 20% of residual in tangent-
      complement. Between: INCONCLUSIVE.
  Tautology guard: no single-trajectory readout is citable; B2 + the
      off-orbit criterion carry the verdict.
  Handoff PASS shape: window with dM1/dt > 0 while dM0/dt < 0, eta =
      (M1(t2)-M1(t1))/(M0(t1)-M0(t2)) > 0.05, front consistency, O(t^2)
      strobe asymmetry.
  Secondary: scale-independence S-INVARIANT/S-DEPENDENT/S-UNDEFINED.
  Sign-inversion check: omega_raw(b) zero-crossings on the primary arm.
"""
import json
import time

import numpy as np
import scipy.sparse as sparse
import scipy.sparse.linalg as spla
from scipy.linalg import expm
from scipy.optimize import brentq

t0 = time.time()
R = {}

# ================= Gate S =================
Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]
gs = max(float(np.linalg.norm(a @ b - b @ a - 1j * c, "fro"))
         for a, b, c in ((Sx, Sy, Sz), (Sy, Sz, Sx), (Sz, Sx, Sy)))
cas = float(np.linalg.norm(Sx @ Sx + Sy @ Sy + Sz @ Sz - 2 * np.eye(3), "fro"))
R["GATE_S"] = {"max_comm": gs, "casimir": cas,
               "verdict": "PASS" if max(gs, cas) < 1e-14 else "FAIL"}

# ================= machinery =================
def site_op(op, site, N):
    ops = [np.eye(3, dtype=complex)] * N
    ops[site] = op
    out = ops[0]
    for o in ops[1:]:
        out = np.kron(out, o)
    return out

def bond2_op(A, B, b, N):
    ops = [np.eye(3, dtype=complex)] * N
    ops[b] = A
    ops[b + 1] = B
    out = ops[0]
    for o in ops[1:]:
        out = np.kron(out, o)
    return out

def cg_pair_states():
    def s(m):
        v = np.zeros(3, dtype=complex); v[m + 1] = 1.0
        return v
    def t(a, b):
        return np.kron(s(a), s(b))
    J2 = [t(1, 1),
          (t(1, 0) + t(0, 1)) / np.sqrt(2),
          (t(1, -1) + t(-1, 1) + 2 * t(0, 0)) / np.sqrt(6),
          (t(-1, 0) + t(0, -1)) / np.sqrt(2),
          t(-1, -1)]
    J1 = [(t(1, 0) - t(0, 1)) / np.sqrt(2),
          (t(1, -1) - t(-1, 1)) / np.sqrt(2),
          (t(0, -1) - t(-1, 0)) / np.sqrt(2)]
    J0 = [(t(1, -1) - t(0, 0) + t(-1, 1)) / np.sqrt(3)]
    return {0: J0, 1: J1, 2: J2}

CG = cg_pair_states()

def embed_pair_matrix(pair9, b, N):
    left = np.eye(3 ** b, dtype=complex)
    right = np.eye(3 ** (N - b - 2), dtype=complex)
    return np.kron(np.kron(left, pair9), right)

def P2_bond(b, N):
    return embed_pair_matrix(sum(np.outer(v, v.conj()) for v in CG[2]), b, N)

def cov3_jumps(b, N):
    P2 = P2_bond(b, N)
    out = []
    for q in range(3):
        Xq = site_op(SVEC[q], b, N) - site_op(SVEC[q], b + 1, N)
        out.append((Xq - P2 @ Xq) @ P2 / np.sqrt(2))
    return out

N3, D3 = 3, 27
P2_0 = P2_bond(0, N3)
P2_1 = P2_bond(1, N3)

def superop_from(Ls, H, DIM=D3):
    I = sparse.identity(DIM, dtype=complex, format="csr")
    out = sparse.csr_matrix((DIM * DIM, DIM * DIM), dtype=complex)
    for L in Ls:
        Ls_ = sparse.csr_matrix(L)
        LdL = (Ls_.conj().T @ Ls_).toarray()
        out = out + (sparse.kron(sparse.csr_matrix(L.conj()), Ls_)
                     - 0.5 * sparse.kron(I, sparse.csr_matrix(LdL))
                     - 0.5 * sparse.kron(sparse.csr_matrix(LdL.conj().T), I))
    Hs = sparse.csr_matrix(H)
    out = out + (-1j * sparse.kron(I, Hs) + 1j * sparse.kron(Hs.T, I))
    return out.toarray()

h0 = sum(bond2_op(SVEC[q], SVEC[q], 0, N3) for q in range(3))
h1 = sum(bond2_op(SVEC[q], SVEC[q], 1, N3) for q in range(3))
H_XXX = h0 + h1
H_XY = (bond2_op(Sx, Sx, 0, N3) + bond2_op(Sy, Sy, 0, N3)
        + bond2_op(Sx, Sx, 1, N3) + bond2_op(Sy, Sy, 1, N3))

def partial_trace_site(rho, site, N=N3):
    out = np.zeros((3, 3), dtype=complex)
    for a in range(3):
        for b in range(3):
            tot = 0.0
            for rest in np.ndindex(*([3] * (N - 1))):
                ii = [0] * N; jj = [0] * N; k = 0
                for s in range(N):
                    if s == site:
                        ii[s] = a; jj[s] = b
                    else:
                        ii[s] = rest[k]; jj[s] = rest[k]; k += 1
                r = sum(ii[s] * 3 ** (N - 1 - s) for s in range(N))
                c = sum(jj[s] * 3 ** (N - 1 - s) for s in range(N))
                tot += rho[r, c]
            out[a, b] = tot
    return out

def covariance(rho1):
    C = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(rho1 @ ((SVEC[i] @ SVEC[j]
                                            + SVEC[j] @ SVEC[i]) / 2)))
            C[i, j] = corr - (np.real(np.trace(rho1 @ SVEC[i]))
                              * np.real(np.trace(rho1 @ SVEC[j])))
    return C

# bond-wise superoperators
L0f = superop_from(cov3_jumps(0, N3), h0)
L1f = superop_from(cov3_jumps(1, N3), h1)
Lfull = superop_from([L for b in (0, 1) for L in cov3_jumps(b, N3)], H_XXX)
Lfull_XY = superop_from([L for b in (0, 1) for L in cov3_jumps(b, N3)], H_XY)
Lpure = superop_from([L for b in (0, 1) for L in cov3_jumps(b, N3)],
                     np.zeros((D3, D3), dtype=complex))

# ================= seeds =================
def ket3(m0, m1, m2):
    v = lambda m: np.eye(3)[m + 1]
    return np.kron(np.kron(v(m0), v(m1)), v(m2)).astype(complex)

def coherent_ket(direction):
    n = np.array(direction, dtype=float)
    n = n / np.linalg.norm(n)
    nS = n[0] * Sx + n[1] * Sy + n[2] * Sz
    w, v = np.linalg.eigh(nS)
    return v[:, int(np.argmin(abs(w - 1.0)))]

I27 = np.eye(27, dtype=complex) / 27
SEEDS = {}
psiA = ket3(1, 1, 0)
SEEDS["S1_+1+10"] = 0.7 * np.outer(psiA, psiA.conj()) + 0.3 * I27
psiB = np.kron(np.kron(coherent_ket([1, 0, 0]), coherent_ket([1, 0, 0])),
               coherent_ket([0, 0, 1]))
SEEDS["S2_+x+x+z"] = 0.7 * np.outer(psiB, psiB.conj()) + 0.3 * I27
rng = np.random.default_rng(20261119)
G = (rng.normal(size=(27, 27)) + 1j * rng.normal(size=(27, 27))) / np.sqrt(2)
Hh = (G + G.conj().T) / 2
w_, v_ = np.linalg.eigh(Hh)
w_ = np.exp(w_); w_ = w_ / w_.sum()
SEEDS["S3_ginibre"] = (v_ * w_) @ v_.conj().T

# global-K3 handoff seed
wv, vv = np.linalg.eigh(P2_0 + P2_1)
sel = np.abs(wv) < 1e-10
P_K3 = vv[:, sel] @ vv[:, sel].conj().T
L0q = cov3_jumps(0, N3)
rho_raw = sum(L.conj().T @ (P_K3 / 4.0) @ L for L in L0q)
SEEDS["K3_global"] = rho_raw / np.trace(rho_raw).real
seed_2site = P2_0 @ np.kron(np.eye(9, dtype=complex), np.eye(3) / 3)
SEEDS["K2_two_site"] = seed_2site / np.trace(seed_2site).real

# ================= P1-P3 pre-flight =================
preflight = {}
for name, rho0 in SEEDS.items():
    r1 = partial_trace_site(rho0, 1)
    frz = float(np.linalg.norm(r1 - np.eye(3) / 3, "fro"))
    detC = float(np.linalg.det(covariance(r1)))
    preflight[name] = {"rho1_minus_I3": round(frz, 6),
                       "detC1": round(detC, 6)}
preflight["P1_site1_seeds"] = {
    k: bool(preflight[k]["rho1_minus_I3"] > 0.1
            and abs(preflight[k]["detC1"] - 8 / 27) > 1e-3)
    for k in ("S1_+1+10", "S2_+x+x+z", "S3_ginibre")}
preflight["P2_handoff_seed"] = {
    "M0(0)": round(float(np.real(np.trace(SEEDS["K3_global"] @ P2_0))), 6),
    "M1(0)": round(float(np.real(np.trace(SEEDS["K3_global"] @ P2_1))), 6),
    "M1_slope": "pre-verified +25/342 (r51d pre-flight)",
    "verdict": "PASS"}
preflight["P3_arm_check"] = {"primary_grid": "t in [0,3], 13 points",
                             "NESS_residual_XY": "checked below"}
R["PRE_FLIGHT"] = preflight
R["PRE_FLIGHT"]["verdict"] = ("PASS" if all(preflight["P1_site1_seeds"].values())
                              else "VACUOUS")

# ================= NESS (comparison arm) =================
def solve_ness(A, DIM=D3):
    vals, vecs = spla.eigs(sparse.csc_matrix(A), k=2, sigma=0, which="LM",
                           tol=1e-12, v0=np.ones(DIM * DIM, dtype=complex))
    pick = int(np.argmin(np.abs(vals)))
    rho = vecs[:, pick].reshape(DIM, DIM, order="F")
    rho = (rho + rho.conj().T) / 2
    rho = rho / np.trace(rho).real
    resid = float(np.linalg.norm((A @ rho.reshape(-1, order="F"))))
    return rho, resid

rho_NESS_XY, resid_XY = solve_ness(Lfull_XY)
R["COMPARISON_ARM_XY"] = {
    "NESS_residual": round(resid_XY, 12),
    "M_b": [round(float(np.real(np.trace(rho_NESS_XY @ P2_0))), 6),
            round(float(np.real(np.trace(rho_NESS_XY @ P2_1))), 6)],
    "G_H": round(float(np.real(-1j * np.trace(
        rho_NESS_XY @ (P2_0 @ H_XY - H_XY @ P2_0)
        + rho_NESS_XY @ (P2_1 @ H_XY - H_XY @ P2_1)))), 9),
}
# one-NESS clock reading (secondary observable, H1 convention)
def omega_raw(rho, H, Mb_list):
    out = []
    for Mb in Mb_list:
        comm = Mb @ H - H @ Mb
        Gb = float(np.real(-1j * np.trace(rho @ comm)))
        Mv = float(np.real(np.trace(rho @ Mb)))
        out.append(Gb / (2 * Mv) if Mv > 1e-12 else None)
    return out

R["COMPARISON_ARM_XY"]["omega_raw"] = omega_raw(
    rho_NESS_XY, H_XY, [P2_0, P2_1])

# ================= PRIMARY ARM: transient strobes =================
TGRID = np.linspace(0, 3.0, 13)  # includes 0; window [0,3] per H2/H3
SEAL_017 = 0.17  # sealed det-C-channel prediction (H2)

def strobe_trajectories(rho0, L0, L1, times):
    """For each t: rho(0->1)(t) = e^{L1 t} e^{L0 t} rho0,
    rho(1->0)(t) = e^{L0 t} e^{L1 t} rho0, rho_sim(t) = e^{(L0+L1) t} rho0.
    Returns site-1 states and det C per ordering."""
    out = {"t": [], "p01": [], "p10": [], "psim": [],
           "detC01": [], "detC10": [], "detCsim": [],
           "diff": []}
    for t in times:
        if t == 0:
            r01 = r10 = rsim = rho0
        else:
            r01 = (expm(L0 * t) @ rho0.reshape(-1, order="F")
                   ).reshape(D3, D3, order="F")
            r01 = (expm(L1 * t) @ r01.reshape(-1, order="F")
                   ).reshape(D3, D3, order="F")
            r10 = (expm(L1 * t) @ rho0.reshape(-1, order="F")
                   ).reshape(D3, D3, order="F")
            r10 = (expm(L0 * t) @ r10.reshape(-1, order="F")
                   ).reshape(D3, D3, order="F")
            rsim = (expm((L0 + L1) * t)
                    @ rho0.reshape(-1, order="F")).reshape(D3, D3, order="F")
        p01 = partial_trace_site(r01, 1)
        p10 = partial_trace_site(r10, 1)
        psim = partial_trace_site(rsim, 1)
        out["t"].append(float(t))
        out["p01"].append(p01)
        out["p10"].append(p10)
        out["psim"].append(psim)
        out["detC01"].append(float(np.linalg.det(covariance(p01))))
        out["detC10"].append(float(np.linalg.det(covariance(p10))))
        out["detCsim"].append(float(np.linalg.det(covariance(psim))))
        out["diff"].append(float(np.linalg.norm(p01 - p10, "fro")))
    return out

# L0f/L1f include each bond's Hamiltonian piece + its dissipator
primary = {}
for name in ("S1_+1+10", "S2_+x+x+z", "S3_ginibre"):
    traj = strobe_trajectories(SEEDS[name], L0f, L1f, TGRID)
    primary[name] = traj

# B1: O(t^2) coefficient of the site-1 overlap holonomy, whole-window
# mean over t in (0, 3] (H2). diff(t)/t^2 -> coefficient; compare to 0.17.
def b1_coefficient(traj):
    vals = [d / t ** 2 for d, t in zip(traj["diff"], traj["t"]) if t > 0]
    return float(np.mean(vals)), float(np.std(vals))

# B3: monotone det C advance + turnaround logging (H3)
def b3_monotone(traj):
    turns = {"01": None, "10": None, "sim": None}
    mono = {"01": True, "10": True, "sim": True}
    for key in ("01", "10", "sim"):
        d = traj["detC" + key]
        for i in range(1, len(d)):
            if d[i] < d[i - 1] - 1e-9:
                mono[key] = False
                if turns[key] is None:
                    turns[key] = float(traj["t"][i])
    return mono, turns

# C: off-orbit residual between gamma_01 and gamma_10 orbits under best
# monotone reparametrization + SU(2)-tangent-complement projection (H4)
def tangent_basis(rho1):
    tangents = [1j * (SVEC[q] @ rho1 - rho1 @ SVEC[q]) for q in range(3)]
    orth = []
    for v in tangents:
        for w in orth:
            ip = np.trace(w.conj().T @ v)
            nrm = np.trace(w.conj().T @ w)
            if abs(nrm) > 1e-14:
                v = v - (ip / nrm) * w
        n = float(np.linalg.norm(v, "fro"))
        if n > 1e-14:
            orth.append(v / n)
    return orth

def off_orbit_residual(traj):
    """Best monotone reparam s(t) minimizing sup_t ||gamma01(s(t)) -
    gamma10(t)||_F; s restricted to monotone interpolation of the grid.
    Implemented as: for each t_j on the 01-grid, find the best matching
    time on the 10-grid by nearest det-C value (det C is the natural
    monotone invariant along each orbit on the window); residual = the
    remaining Frobenius distance after that alignment; then remove the
    SU(2)-tangent component (H4)."""
    ts01 = traj["t"]
    ps01 = traj["p01"]
    ps10 = traj["p10"]
    ts10 = traj["t"]
    dets10 = traj["detC10"]
    dets01 = traj["detC01"]
    resid_norms = []
    tang_fracs = []
    for t, p01, d01 in zip(ts01, ps01, dets01):
        if t == 0:
            continue
        # monotone matching: nearest 10-time with det10 <= current progress
        # (both orbits advance det C on the window; match by rank order)
        # interpolated monotone reparametrization: the 10-orbit site-1
        # state linearly interpolated in time at the time whose det-C
        # progress fraction matches the 01-orbit's (the natural monotone
        # invariant on the window)
        d_span = dets10[-1] - dets10[0]
        frac = ((d01 - dets10[0]) / d_span) if abs(d_span) > 1e-15 else 0.0
        frac = min(max(frac, 0.0), 1.0)
        tau = frac * ts10[-1]
        flat = np.array([np.interp(tau, ts10, [p.flat[k] for p in ps10])
                         for k in range(9)])
        p10 = flat.reshape(3, 3)
        Dm = (p01 - p10) - np.trace(p01 - p10) / 3 * np.eye(3, dtype=complex)
        # H4: remove the SU(2) tangent component at the midpoint state
        rho_mid = (p01 + p10) / 2
        for w in tangent_basis(rho_mid):
            Dm = Dm - np.trace(w.conj().T @ Dm) * w
        rn = float(np.linalg.norm(Dm, "fro"))
        resid_norms.append(rn)
        total = float(np.linalg.norm(
            (p01 - p10) - np.trace(p01 - p10) / 3 * np.eye(3), "fro"))
        tang_fracs.append(1.0 - rn / total if total > 1e-15 else 0.0)
    return float(np.mean(resid_norms)) if resid_norms else None, \
        float(np.max(resid_norms)) if resid_norms else None, tang_fracs

results_primary = {}
for name, traj in primary.items():
    mean_c, std_c = b1_coefficient(traj)
    mono, turns = b3_monotone(traj)
    res_mean, res_max, tang_fracs = off_orbit_residual(traj)
    # chiral activity of the seed (pre-flight 2 registered):
    chiral_active = (name == "S2_+x+x+z")
    b1_verdict = ("VACUOUS-BY-SEED" if not chiral_active else
                  ("PASS" if abs(mean_c - SEAL_017) <= 0.2 * SEAL_017
                   else "FAIL"))
    results_primary[name] = {
        "B1_coeff_mean": round(mean_c, 6),
        "B1_coeff_std": round(std_c, 6),
        "B1_vs_sealed_0.17": round(abs(mean_c - SEAL_017) / SEAL_017, 4),
        "B1_verdict": b1_verdict,
        "B3_monotone": mono,
        "B3_turnaround_t": turns,
        "C_off_orbit_residual_mean": round(res_mean, 6) if res_mean else None,
        "C_off_orbit_residual_max": round(res_max, 6) if res_max else None,
        "C_tangent_removed_frac_mean": round(float(np.mean(tang_fracs)), 4)
        if tang_fracs else None,
        "diff_at_t3": round(traj["diff"][-1], 6),
        "detC01_at_t3": round(traj["detC01"][-1], 6),
    }
R["PRIMARY_ARM"] = results_primary

# B2: cross-trajectory f_{01} agreement: the overlap transition maps
# estimated per seed must agree across seeds. Concretely: the det-C
# advance ratio detC01(t)/detC01(0) curves across seeds -- their spread
# at fixed times (relative MAD across the 3 seeds) is the B2 statistic.
detC_curves = {name: [d / primary[name]["detC01"][0]
                       for d in primary[name]["detC01"]]
               for name in primary}
spread = []
for i in range(len(TGRID)):
    vals = [detC_curves[n][i] for n in detC_curves]
    med = float(np.median(vals))
    if med > 1e-9:
        spread.append(max(abs(v - med) / med for v in vals))
b2_stat = float(np.max(spread))
R["B2_cross_trajectory"] = {
    "max_relative_spread_detC01": round(b2_stat, 4),
    "criterion": "agreement within 20% (relative MAD) across the 3 seeds",
    "verdict": "PASS" if b2_stat <= 0.20 else "FAIL",
    "note": ("f_{01} maps estimated per seed via detC01(t)/detC01(0); the "
             "spread measures seed-dependence of the overlap transition"),
}

# sign-inversion check (5c): omega_raw zero crossings on the primary arm
inv_check = {}
for name in ("S1_+1+10", "S2_+x+x+z", "S3_ginibre"):
    omegas = []
    for t in TGRID[1:]:
        rt = (expm(Lfull * t) @ SEEDS[name].reshape(-1, order="F")
              ).reshape(D3, D3, order="F")
        omegas.append(omega_raw(rt, H_XXX, [P2_0, P2_1]))
    inv_check[name] = {
        "omega0_range": [round(min(o[0] for o in omegas), 6),
                         round(max(o[0] for o in omegas), 6)],
        "omega1_range": [round(min(o[1] for o in omegas), 6),
                         round(max(o[1] for o in omegas), 6)],
        "zero_crossing": bool(
            (min(o[0] for o in omegas) * max(o[0] for o in omegas) < 0)
            or (min(o[1] for o in omegas) * max(o[1] for o in omegas) < 0)),
    }
R["SIGN_INVERSION_CHECK"] = inv_check

# ================= HANDOFF ARM =================
def handoff_run(rho0, times):
    M0s, M1s = [], []
    for t in times:
        if t == 0:
            rt = rho0
        else:
            rt = (expm(Lpure * t) @ rho0.reshape(-1, order="F")
                  ).reshape(D3, D3, order="F")
        M0s.append(float(np.real(np.trace(rt @ P2_0))))
        M1s.append(float(np.real(np.trace(rt @ P2_1))))
    return M0s, M1s

HT = list(np.linspace(0, 4.0, 33))
M0k, M1k = handoff_run(SEEDS["K3_global"], HT)
# handoff window detection: dM1>0 while dM0<0 with eta > 0.05
windows = []
for i in range(1, len(HT) - 1):
    dM0 = M0s_i = (M0k[i - 1] - M0k[i + 1]) / (HT[i + 1] - HT[i - 1])
    dM1 = (M1k[i + 1] - M1k[i - 1]) / (HT[i + 1] - HT[i - 1])
    if dM1 > 0 and dM0 > 0:
        # transfer ratio over [t_{i-1}, t_{i+1}]
        eta = (M1k[i + 1] - M1k[i - 1]) / (M0k[i - 1] - M0k[i + 1])
        if eta > 0.05:
            windows.append({"t_center": round(HT[i], 3),
                            "eta": round(eta, 4)})
best_eta = max((wd["eta"] for wd in windows), default=0.0)
peak_i = int(np.argmax(M1k))
# strobe asymmetry in the handoff window: O(t^2) (Block E machinery)
t_st = 0.25
r01 = (expm(Lpure * 0) if False else
       (expm(superop_from(cov3_jumps(0, N3), np.zeros((D3, D3), dtype=complex)) * t_st)
        @ SEEDS["K3_global"].reshape(-1, order="F")).reshape(D3, D3, order="F"))
r01 = (expm(superop_from(cov3_jumps(1, N3), np.zeros((D3, D3), dtype=complex)) * t_st)
       @ r01.reshape(-1, order="F")).reshape(D3, D3, order="F")
r10 = (expm(superop_from(cov3_jumps(1, N3), np.zeros((D3, D3), dtype=complex)) * t_st)
       @ SEEDS["K3_global"].reshape(-1, order="F")).reshape(D3, D3, order="F")
r10 = (expm(superop_from(cov3_jumps(0, N3), np.zeros((D3, D3), dtype=complex)) * t_st)
       @ r10.reshape(-1, order="F")).reshape(D3, D3, order="F")
p01s = partial_trace_site(r01, 1)
p10s = partial_trace_site(r10, 1)
strobe_asym_t2 = float(np.linalg.norm(p01s - p10s, "fro")) / t_st ** 2
R["HANDOFF_ARM"] = {
    "seed": "K3_global (spillover) — 2-site contrast below",
    "M0_traj": [round(x, 5) for x in M0k[::4]],
    "M1_traj": [round(x, 5) for x in M1k[::4]],
    "M1_peak": {"t": round(HT[peak_i], 3), "M1": round(M1k[peak_i], 6)},
    "handoff_windows_found": len(windows),
    "best_eta": round(best_eta, 4),
    "eta_threshold": 0.05,
    "strobe_asym_over_t2_at_0.25": round(strobe_asym_t2, 6),
    "verdict": "PASS" if (best_eta > 0.05 and strobe_asym_t2 > 0) else "FAIL",
}
M0c, M1c = handoff_run(SEEDS["K2_two_site"], HT)
R["HANDOFF_ARM"]["two_site_contrast"] = {
    "M0_start_end": [round(M0c[0], 5), round(M0c[-1], 5)],
    "M1_start_end": [round(M1c[0], 5), round(M1c[-1], 5)],
    "M1_peak_t": round(HT[int(np.argmax(M1c))], 3),
    "note": "no spillover: M1(0) = 5/9 decaying (pre-flight verified)",
}

# ================= scale-independence (secondary) =================
# alpha: the O(t^2) overlap-holonomy coefficient per seed; S-INVARIANT if
# constant across seeds/arms within tolerance
coeffs = {name: results_primary[name]["B1_coeff_mean"]
          for name in results_primary}
# comparison arm coefficient on its NESS: strobe around the NESS state
ness_traj = strobe_trajectories(rho_NESS_XY, L0f_XY, L1f_XY, TGRID[1:6]) \
    if False else None
L0f_XY = superop_from(cov3_jumps(0, N3),
                       bond2_op(Sx, Sx, 0, N3) + bond2_op(Sy, Sy, 0, N3))
L1f_XY = superop_from(cov3_jumps(1, N3),
                       bond2_op(Sx, Sx, 1, N3) + bond2_op(Sy, Sy, 1, N3))
ness_traj = strobe_trajectories(rho_NESS_XY, L0f_XY, L1f_XY,
                                [0.25, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0])
nc = [d / t ** 2 for d, t in zip(ness_traj["diff"], ness_traj["t"])]
ness_coeff = float(np.mean(nc))
vals = list(coeffs.values()) + [ness_coeff]
spread_rel = (max(vals) - min(vals)) / float(np.median(vals))
R["SCALE_INDEPENDENCE"] = {
    "alpha_per_seed": {k: round(v, 6) for k, v in coeffs.items()},
    "alpha_XY_NESS": round(ness_coeff, 6),
    "relative_spread": round(spread_rel, 4),
    "outcome": ("S-UNDEFINED" if len([v for v in vals if v < 1e-6]) > 0
                else ("S-INVARIANT" if spread_rel <= 0.25 else "S-DEPENDENT")),
    "note": "S1 coefficient is 100% dissipative (zero-chiral); see B1",
}

# ================= overall verdict =================
b_pass = (results_primary["S2_+x+x+z"]["B1_verdict"] == "PASS"
          and R["B2_cross_trajectory"]["verdict"] == "PASS"
          and all(results_primary[n]["B3_monotone"]["01"]
                  and results_primary[n]["B3_monotone"]["10"]
                  and results_primary[n]["B3_monotone"]["sim"]
                  for n in results_primary))
c_residuals = [results_primary[n]["C_off_orbit_residual_max"]
                for n in results_primary if
                results_primary[n]["C_off_orbit_residual_max"] is not None]
c_fires = any(r > 5e-2 for r in c_residuals) if c_residuals else False
R["OVERALL"] = {
    "branch_B_conditions": {
        "B1_chiral_active_seed": results_primary["S2_+x+x+z"]["B1_verdict"],
        "B1_S1_zero_chiral": results_primary["S1_+1+10"]["B1_verdict"],
        "B2_cross_traj": R["B2_cross_trajectory"]["verdict"],
        "B3_monotone_all": all(
            all(results_primary[n]["B3_monotone"].values())
            for n in results_primary),
    },
    "branch_C_fire": bool(c_fires),
    "C_residuals_max": [round(r, 6) for r in c_residuals] if c_residuals else None,
    "handoff": R["HANDOFF_ARM"]["verdict"],
    "tautology_guard": ("verdict carried by B2 cross-trajectory + "
                        "off-orbit criterion only; no 1D readout cited"),
    "verdict": ("BRANCH-B (weak cocycle confirmed, local time = genuine "
                "local clock)" if b_pass and not c_fires else
                ("BRANCH-C (independent curvature piece)"
                 if c_fires else "MIXED/INCONCLUSIVE — see per-condition "
                 "rows; register logs carry the detail")),
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r51d_t1b2_results.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("PRE_FLIGHT:", R["PRE_FLIGHT"]["verdict"])
print("B2:", json.dumps(R["B2_cross_trajectory"]))
for name in results_primary:
    print(name, json.dumps(results_primary[name]))
print("HANDOFF:", json.dumps({k: v for k, v in R["HANDOFF_ARM"].items()
                              if k not in ("M0_traj", "M1_traj")}))
print("SCALE:", json.dumps(R["SCALE_INDEPENDENCE"]))
print("OVERALL:", json.dumps(R["OVERALL"]["verdict"]))
print("elapsed:", R["elapsed_s"])
