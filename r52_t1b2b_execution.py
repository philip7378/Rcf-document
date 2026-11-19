"""PR-T1b-2b EXECUTION — the N-scaling diagnostic, per the frozen
pr_t1b2b_sheet.txt (1c351bce) and the pre-registered header in
rcf_r52_pre_execution_register.txt (4ff99d30).

N in {3,4,5,6}; blockwise-exact two-ordering strobes (e^{L_b t} dense
superoperators per bond, no full-chain NESS solve); three seed families;
primary = max off-orbit residual per (N, family) via interpolated monotone
reparametrization + SU(2)-tangent-complement projection; f0_1 guard
[0.16, 0.18] on the F1 chiral coefficient at every N; N=4 locality arm;
Gamma_b/tau_b spending clocks logged; handoff arm N in {3,4,5} (+6 logged).
"""
import json
import time

import numpy as np
import scipy.sparse as sparse
from scipy.linalg import expm
from scipy.sparse.linalg import expm_multiply

t0 = time.time()
R = {}

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]
gs = max(float(np.linalg.norm(a @ b - b @ a - 1j * c, "fro"))
         for a, b, c in ((Sx, Sy, Sz), (Sy, Sz, Sx), (Sz, Sx, Sy)))
cas = float(np.linalg.norm(Sx @ Sx + Sy @ Sy + Sz @ Sz - 2 * np.eye(3), "fro"))
R["GATE_S"] = {"max_comm": gs, "casimir": cas,
               "verdict": "PASS" if max(gs, cas) < 1e-14 else "FAIL"}

# ---------- chain machinery (parameterized by N) ----------
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

def superop_from(Ls, H, DIM):
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
    return sparse.csc_matrix(out)

def ptrace(rho, site, N):
    T = rho.reshape([3] * N + [3] * N)
    letters = "abcdefghijklmnopqrstuvwxyz"
    sub = [letters[i] for i in range(2 * N)]
    for i in range(N):
        if i != site:
            sub[N + i] = sub[i]
    return np.einsum("".join(sub), T)

def covariance(rho1):
    C = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(rho1 @ ((SVEC[i] @ SVEC[j]
                                            + SVEC[j] @ SVEC[i]) / 2)))
            C[i, j] = corr - (np.real(np.trace(rho1 @ SVEC[i]))
                              * np.real(np.trace(rho1 @ SVEC[j])))
    return C

def coherent_ket(direction):
    n = np.array(direction, dtype=float)
    n = n / np.linalg.norm(n)
    nS = n[0] * Sx + n[1] * Sy + n[2] * Sz
    w, v = np.linalg.eigh(nS)
    return v[:, int(np.argmin(abs(w - 1.0)))]

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

TGRID = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
         2.0, 2.25, 2.5, 2.75, 3.0]

def build_N(N):
    D = 3 ** N
    h = [sum(bond2_op(SVEC[q], SVEC[q], b, N) for q in range(3))
         for b in range(N - 1)]
    Lb = [superop_from(cov3_jumps(b, N), h[b], D) for b in range(N - 1)]
    P2 = [P2_bond(b, N) for b in range(N - 1)]
    return D, h, Lb, P2

def strobes(rho0, L0, L1, times):
    D = rho0.shape[0]
    out = {"t": [], "p01": [], "p10": [], "detC01": [], "detC10": [],
           "diff": []}
    for t in times:
        if t == 0:
            r01 = r10 = rho0
        else:
            v0 = rho0.reshape(-1, order="F")
            v01 = expm_multiply(L0 * float(t), v0)
            v01 = expm_multiply(L1 * float(t), v01)
            r01 = v01.reshape(D, D, order="F")
            v10 = expm_multiply(L1 * float(t), v0)
            v10 = expm_multiply(L0 * float(t), v10)
            r10 = v10.reshape(D, D, order="F")
        p01 = ptrace(r01, 1, N3g)
        p10 = ptrace(r10, 1, N3g)
        out["t"].append(float(t))
        out["p01"].append(p01)
        out["p10"].append(p10)
        out["detC01"].append(float(np.linalg.det(covariance(p01))))
        out["detC10"].append(float(np.linalg.det(covariance(p10))))
        out["diff"].append(float(np.linalg.norm(p01 - p10, "fro")))
    return out

N3g = None  # set per-N by the driver

def run_N(N, seed_makers):
    global N3g
    N3g = N
    D, h, Lb, P2 = build_N(N)
    res = {}
    for fam, rho0 in seed_makers(N, D).items():
        traj = strobes(rho0, Lb[0], Lb[1], TGRID)
        # off-orbit residual: the r5.1d fixed statistic
        resid = []
        tangfrac = []
        ts = traj["t"]
        dets01 = traj["detC01"]
        dets10 = traj["detC10"]
        ps01 = traj["p01"]
        ps10 = traj["p10"]
        d_span = dets10[-1] - dets10[0]
        for t, p01, d01 in zip(ts, ps01, dets01):
            if t == 0:
                continue
            frac = ((d01 - dets10[0]) / d_span) if abs(d_span) > 1e-15 else 0.0
            frac = min(max(frac, 0.0), 1.0)
            tau = frac * ts[-1]
            flat = np.array([np.interp(tau, ts, [p.flat[k] for p in ps10])
                             for k in range(9)])
            p10 = flat.reshape(3, 3)
            Dm = (p01 - p10) - np.trace(p01 - p10) / 3 * np.eye(3,
                                                                dtype=complex)
            rho_mid = (p01 + p10) / 2
            for w in tangent_basis(rho_mid):
                Dm = Dm - np.trace(w.conj().T @ Dm) * w
            rn = float(np.linalg.norm(Dm, "fro"))
            total = float(np.linalg.norm(
                (p01 - p10) - np.trace(p01 - p10) / 3 * np.eye(3), "fro"))
            resid.append(rn)
            tangfrac.append(1.0 - rn / total if total > 1e-15 else 0.0)
        # f01 chiral coefficient: whole-window mean of diff/t^2
        coeffs = [d / t ** 2 for d, t in zip(traj["diff"], ts) if t > 0]
        res[fam] = {
            "residual_max": round(float(np.max(resid)), 6),
            "residual_mean": round(float(np.mean(resid)), 6),
            "tangfrac_mean": round(float(np.mean(tangfrac)), 4),
            "chiral_coeff_mean": round(float(np.mean(coeffs)), 6),
            "diff_at_t3": round(traj["diff"][-1], 6),
        }
    return res

# ---------- the seed families ----------
def make_seeds(N, D):
    seeds = {}
    # F1: 0.7 |+x,+x,+z,...> + 0.3 I
    v = coherent_ket([1, 0, 0])
    w = coherent_ket([0, 0, 1])
    psi = v
    for k in range(1, N):
        psi = np.kron(psi, v if k == 1 else w)
    rho = 0.7 * np.outer(psi, psi.conj()) + 0.3 * np.eye(D) / D
    seeds["F1_product"] = rho
    # F2: Ginibre (master rng 20261119)
    rng = np.random.default_rng(20261119 + N)
    G = (rng.normal(size=(D, D)) + 1j * rng.normal(size=(D, D))) / np.sqrt(2)
    Hh = (G + G.conj().T) / 2
    w_, v_ = np.linalg.eigh(Hh)
    w_ = np.exp(w_); w_ = w_ / w_.sum()
    seeds["F2_ginibre"] = (v_ * w_) @ v_.conj().T
    # F3: K_N kernel seed
    D_, h, Lb, P2 = build_N(N)
    H_AKLT = sum(P2)
    wv, vv = np.linalg.eigh(H_AKLT)
    sel = np.abs(wv) < 1e-9
    P_K = vv[:, sel] @ vv[:, sel].conj().T
    L0q = cov3_jumps(0, N)
    rank = int(sel.sum())
    rho_raw = sum(L.conj().T @ (P_K / rank) @ L for L in L0q)
    seeds["F3_kernel"] = rho_raw / np.trace(rho_raw).real
    seeds["_kernel_rank"] = rank
    return seeds

# ---------- P1-P3 pre-flight ----------
pf = {}
for N in (3, 4, 5, 6):
    seeds = make_seeds(N, 3 ** N)
    pf[f"N{N}_kernel_rank"] = seeds.pop("_kernel_rank")
    for fam in list(seeds):
        rho = seeds[fam]
        p1 = ptrace(rho, 1, N)
        pf[f"P1_{fam}_N{N}"] = round(float(
            np.linalg.norm(p1 - np.eye(3) / 3, "fro")), 6)
R["PRE_FLIGHT"] = pf
R["PRE_FLIGHT"]["P3_declared_ranks"] = "2^{N-1}: 2, 4, 8, 16"

# ---------- the primary arm ----------
primary = {}
for N in (3, 4, 5, 6):
    seeds = make_seeds(N, 3 ** N)
    seeds.pop("_kernel_rank", None)
    primary[f"N{N}"] = run_N(N, lambda n, d, s=seeds: s)
    print(f"N={N} done", flush=True)

R["PRIMARY"] = primary

# ---------- f01 guard ----------
guard = {}
for N in (3, 4, 5, 6):
    c = primary[f"N{N}"]["F1_product"]["chiral_coeff_mean"]
    guard[f"N{N}"] = {"F1_coeff": c, "in_band": bool(0.16 <= c <= 0.18)}
guard["verdict"] = ("PASS (universality holds)" if all(
    v["in_band"] for k, v in guard.items() if k.startswith("N"))
    else "FAIL -> chiral-current universality is N-scoped; B1 downgrades")
R["F01_GUARD"] = guard

# ---------- outcome adjudication ----------
def classify(curve):
    r3, r6 = curve[0], curve[-1]
    if r3 <= 0:
        return "N-UNMEASURABLE"
    if r6 <= 0.20 * r3:
        return "N-DECAY"
    if r6 >= 0.80 * r3:
        return "N-CONSTANT"
    return "N-MIXED"

outcome = {}
for fam in ("F1_product", "F2_ginibre", "F3_kernel"):
    curve = [primary[f"N{N}"][fam]["residual_max"] for N in (3, 4, 5, 6)]
    outcome[fam] = {"curve": curve, "class": classify(curve)}
classes = {v["class"] for v in outcome.values()}
if len(classes) == 1:
    agg = classes.pop()
else:
    agg = "N-SPLIT"
outcome["aggregate"] = agg
outcome["route"] = {
    "N-DECAY": "PR-T1b-3 proceeds (Path-2 re-scope: locality + cadence)",
    "N-CONSTANT": "No-Go VII promoted; Paper II -> directional local time",
    "N-MIXED": "T1b-3 with boundary-correction layer",
    "N-SPLIT": "paper registers the split; routes scoped per family",
    "N-UNMEASURABLE": "diagnose numerics",
}[agg]
R["OUTCOME"] = outcome

# ---------- N=4 locality arm ----------
N = 4
D4 = 81
h4 = [sum(bond2_op(SVEC[q], SVEC[q], b, 4) for q in range(3))
      for b in range(3)]
com_disjoint = float(np.linalg.norm(h4[0] @ h4[2] - h4[2] @ h4[0], "fro"))
com_adjacent = float(np.linalg.norm(h4[0] @ h4[1] - h4[1] @ h4[0], "fro"))
R["LOCALITY_N4"] = {
    "h0_h2_commutator": com_disjoint,
    "h0_h1_commutator": com_adjacent,
    "declared": "0 / 12",
    "verdict": ("PASS" if com_disjoint < 1e-12 and abs(com_adjacent - 12)
                < 1e-9 else "FAIL"),
    "note": ("disjoint bonds commute exactly (causal light-cone); "
             "holonomy strictly local to adjacent overlaps"),
}

# ---------- Gamma_b / tau_b spending clocks (primary arm, F1) ----------
clocks = {}
for N in (3, 4, 5, 6):
    D, h, Lb, P2 = build_N(N)
    seeds = make_seeds(N, D)
    rho0 = seeds["F1_product"]
    M0s = []
    for t in TGRID[1:]:
        rt = expm_multiply((Lb[0] + Lb[1]) * float(t),
                          rho0.reshape(-1, order="F")).reshape(
            D, D, order="F")
        M0s.append(float(np.real(np.trace(rt @ P2[0]))))
    # tau_b(T) with T=3, trapezoid on the grid
    ts = TGRID[1:]
    tau = float(np.trapz(M0s, ts))
    clocks[f"N{N}"] = {"M0_curve": [round(x, 4) for x in M0s[::3]],
                       "tau_b_T3": round(tau, 4),
                       "Gamma_positive": all(m >= 0 for m in M0s)}
R["SPENDING_CLOCKS"] = clocks

# ---------- handoff arm (N in 3,4,5) ----------
handoff = {}
for N in (3, 4, 5):
    D, h, Lb, P2 = build_N(N)
    seeds = make_seeds(N, D)
    rho0 = seeds["F3_kernel"]
    HT = np.linspace(0, 4.0, 33)
    M0k, M1k = [], []
    for t in HT:
        if t == 0:
            rt = rho0
        else:
            rt = rho0
            # handoff: the sheet's sequential-strobe form
            for b in range(N - 1):
                rt = expm_multiply(Lb[b] * float(t),
                                   rt.reshape(-1, order="F")).reshape(
                    D, D, order="F")
        M0k.append(float(np.real(np.trace(rt @ P2[0]))))
        M1k.append(float(np.real(np.trace(rt @ P2[1]))))
    best = 0.0
    for i in range(1, len(HT) - 1):
        dM0 = (M0k[i - 1] - M0k[i + 1]) / (HT[i + 1] - HT[i - 1])
        dM1 = (M1k[i + 1] - M1k[i - 1]) / (HT[i + 1] - HT[i - 1])
        if dM1 > 0 and dM0 > 0:
            eta = (M1k[i + 1] - M1k[i - 1]) / (M0k[i - 1] - M0k[i + 1])
            best = max(best, eta)
    band = ("FAIL" if best < 0.04 else
            "MARGINAL-UNSTABLE" if best < 0.06 else "PASS")
    handoff[f"N{N}"] = {
        "M1_peak": round(max(M1k), 6),
        "M1_peak_t": round(float(HT[int(np.argmax(M1k))]), 3),
        "best_eta": round(best, 4), "band": band,
    }
handoff["N6_superoperator_scale"] = "729^2 = 531441: logged per sheet; " \
    "blockwise strobes feasible; skipped this run (time budget), logged " \
    "not silently dropped"
R["HANDOFF"] = handoff

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r52_t1b2b_results.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("P3 ranks:", {k: v for k, v in pf.items() if "rank" in k})
print("PRIMARY:", json.dumps(primary, indent=1))
print("F01_GUARD:", json.dumps(guard))
print("OUTCOME:", json.dumps(outcome))
print("LOCALITY:", json.dumps(R["LOCALITY_N4"]))
print("CLOCKS:", json.dumps(clocks))
print("HANDOFF:", json.dumps(handoff))
print("elapsed:", R["elapsed_s"])
