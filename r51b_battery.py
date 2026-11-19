"""r5.1b reversal battery — executes pr_r51b_reversal_sheet.txt:
Gate S pre-flight, forensic reproduction of 0cbc1e7's erroneous numbers
from the buggy generator + r5.1a's non-orthonormal diagonal basis, then
the repaired A2'/A3'/A4'/B'/INJ' verifications on the fixed algebra with
an orthonormal basis.

Bug reproduced DELIBERATELY in the forensic block only; every repaired
number uses the fixed spin_ops and a Gram-Schmidt-orthonormalized basis.
"""
import json
import time

import numpy as np

t0 = time.time()
R = {}

# =====================================================================
# Generator constructors: buggy (r5.1a line 233) and fixed
# =====================================================================
def spin_ops_buggy(S):
    """The r5.1a constructor verbatim: m = S - i (BRA index) in
    sqrt(S(S+1) - m(m+1)). Zeroes the [0,1] ladder entry for every S;
    NOT an SU(2) representation for d >= 2."""
    d = int(round(2 * S)) + 1
    Jz = np.diag([S - i for i in range(d)]).astype(complex)
    Jp = np.zeros((d, d), dtype=complex)
    for i in range(d - 1):
        m = S - i
        Jp[i, i + 1] = np.sqrt(S * (S + 1) - m * (m + 1))
    Jm = Jp.conj().T
    return [(Jp + Jm) / 2, (Jp - Jm) / (2j), Jz]

def spin_ops(S):
    """Fixed: the KET index m_ket = S - (i+1) in the SAME formula
    sqrt(S(S+1) - m_ket(m_ket+1))  (the audit's m[i+1] prescription):
    <S, m_ket+1|S_+|S, m_ket> = sqrt(S(S+1) - m_ket(m_ket+1))."""
    d = int(round(2 * S)) + 1
    Jz = np.diag([S - i for i in range(d)]).astype(complex)
    Jp = np.zeros((d, d), dtype=complex)
    for i in range(d - 1):
        m_ket = S - (i + 1)  # m of the KET (column i+1)
        Jp[i, i + 1] = np.sqrt(S * (S + 1) - m_ket * (m_ket + 1))
    Jm = Jp.conj().T
    return [(Jp + Jm) / 2, (Jp - Jm) / (2j), Jz]

# explicit S=1 matrices used by Gate 0 / trap anchors in r5.1a (correct)
Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]

# =====================================================================
# Tangent bases
# =====================================================================
def tangent_basis_r51a(d):
    """The r5.1a original: NON-orthonormal diagonal pair (audit Bug #2).
    Used ONLY in the forensic block to reproduce 0cbc1e7's numbers."""
    E = []
    for i in range(d):
        for j in range(i + 1, d):
            A = np.zeros((d, d), dtype=complex); A[i, j] = 1; A[j, i] = 1
            E.append(A / np.sqrt(2))
            B = np.zeros((d, d), dtype=complex); B[i, j] = -1j; B[j, i] = 1j
            E.append(B / np.sqrt(2))
    for i in range(d - 1):
        D = np.zeros((d, d), dtype=complex); D[i, i] = 1; D[i + 1, i + 1] = -1
        E.append(D / np.sqrt(2))
    return E

def tangent_basis_orthonorm(d):
    """Orthonormal traceless Hermitian basis: off-diagonal symmetric /
    antisymmetric pairs, then Gram-Schmidt on the diagonal traceless
    candidates e_j - e_{j+1} (generalized Gell-Mann)."""
    E = []
    for i in range(d):
        for j in range(i + 1, d):
            A = np.zeros((d, d), dtype=complex); A[i, j] = 1; A[j, i] = 1
            E.append(A / np.sqrt(2))
            B = np.zeros((d, d), dtype=complex); B[i, j] = -1j; B[j, i] = 1j
            E.append(B / np.sqrt(2))
    # diagonal traceless, Gram-Schmidt
    cands = []
    for j in range(d - 1):
        v = np.zeros(d); v[j] = 1; v[j + 1] = -1
        cands.append(v)
    basis = []
    for v in cands:
        w = v.copy()
        for b in basis:
            w = w - (w @ b) * b
        if np.linalg.norm(w) > 1e-12:
            w = w / np.linalg.norm(w)
            basis.append(w)
    for w in basis:
        D = np.diag(w).astype(complex)
        E.append(D)
    return E

def gram_norm(B):
    n = len(B)
    G = np.array([[np.trace(B[a] @ B[b]) for b in range(n)] for a in range(n)])
    return float(np.linalg.norm(G - np.eye(n)))

# =====================================================================
# GATE S — pre-flight for every constructor used downstream
# =====================================================================
def gate_s(gen, S):
    Sx_, Sy_, Sz_ = gen(S)
    comm = np.linalg.norm(Sx_ @ Sy_ - Sy_ @ Sx_ - 1j * Sz_, "fro")
    cas = np.linalg.norm(Sx_ @ Sx_ + Sy_ @ Sy_ + Sz_ @ Sz_
                        - S * (S + 1) * np.eye(Sz_.shape[0]), "fro")
    return comm, cas

gs = {}
for S in (0.5, 1.0, 1.5):
    c_f, k_f = gate_s(spin_ops, S)
    c_b, k_b = gate_s(spin_ops_buggy, S)
    gs[f"S={S}"] = {
        "fixed_comm_norm": float(c_f), "fixed_casimir_norm": float(k_f),
        "buggy_comm_norm": float(c_b), "buggy_casimir_norm": float(k_b),
        "fixed_ok": bool(c_f < 1e-14 and k_f < 1e-14),
        "buggy_ok": bool(c_b < 1e-14 and k_b < 1e-14),
    }
c_v, k_v = gate_s(lambda s: SVEC, 1.0)
gs["SVEC_S=1"] = {"comm_norm": float(c_v), "casimir_norm": float(k_v),
                  "ok": bool(c_v < 1e-14 and k_v < 1e-14)}
basis_gram = {}
for d in (2, 3, 4):
    basis_gram[f"d={d}"] = gram_norm(tangent_basis_orthonorm(d))
gs["orthonormal_basis_gram"] = basis_gram
gs["verdict"] = "PASS" if (all(gs[f"S={S}"]["fixed_ok"] for S in (0.5, 1.0, 1.5))
                           and gs["SVEC_S=1"]["ok"]
                           and all(v < 1e-14 for v in basis_gram.values())
                           and not any(gs[f"S={S}"]["buggy_ok"]
                                       for S in (0.5, 1.0, 1.5))) else "FAIL"
R["GATE_S"] = gs

# =====================================================================
# shared machinery (covariance, closed forms)
# =====================================================================
def covariance(rho, sops):
    C = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(rho @ ((sops[i] @ sops[j] + sops[j] @ sops[i]) / 2)))
            C[i, j] = corr - (np.real(np.trace(rho @ sops[i]))
                              * np.real(np.trace(rho @ sops[j])))
    return C

def dCmat(rho, d, sops):
    m = np.array([np.real(np.trace(rho @ s)) for s in sops])
    dm = np.array([np.real(np.trace(d @ s)) for s in sops])
    dC = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(d @ ((sops[i] @ sops[j] + sops[j] @ sops[i]) / 2)))
            dC[i, j] = corr - dm[i] * m[j] - m[i] * dm[j]
    return dC, dm

def g_bilinear(rho, d, e, sops):
    C = covariance(rho, sops)
    Ci = np.linalg.inv(C)
    dC, dm = dCmat(rho, d, sops)
    eC, em = dCmat(rho, e, sops)
    return (np.trace(Ci @ dC @ Ci @ eC) + dm @ Ci @ em + em @ Ci @ dm)

def g_closed(rho, d, sops):
    C = covariance(rho, sops)
    Ci = np.linalg.inv(C)
    dC, dm = dCmat(rho, d, sops)
    return float(np.trace(Ci @ dC @ Ci @ dC) + 2 * dm @ Ci @ dm)

S1 = spin_ops(1.0)
TB_orth = tangent_basis_orthonorm(3)
TB_r51a = tangent_basis_r51a(3)
rho0 = np.eye(3, dtype=complex) / 3

# =====================================================================
# FORENSIC BLOCK — reproduce 0cbc1e7's numbers: buggy generators +
# r5.1a's non-orthonormal diagonal basis (audit Bugs #1 + #2 together)
# =====================================================================
B1 = spin_ops_buggy(1.0)

F3_SxoSy_norm = float(np.linalg.norm((B1[0] @ B1[1] + B1[1] @ B1[0]) / 2, "fro"))
Sx_block = np.zeros((3, 3), dtype=complex)
Sx_block[1, 2] = 1 / np.sqrt(2); Sx_block[2, 1] = 1 / np.sqrt(2)
F3_block_match = float(np.linalg.norm(B1[0] - Sx_block, "fro"))

B32 = spin_ops_buggy(1.5)
cas32 = (B32[0] @ B32[0] + B32[1] @ B32[1] + B32[2] @ B32[2]).real
F5_diag = [round(float(x), 6) for x in np.diag(cas32)]

G8_bug = np.zeros((8, 8))
for a in range(8):
    for b_ in range(8):
        G8_bug[a, b_] = g_bilinear(rho0, TB_r51a[a], TB_r51a[b_], B1)
G8_bug = (G8_bug + G8_bug.T) / 2
ev_bug = np.sort(np.linalg.eigvalsh(G8_bug))
F1_spectrum = [round(float(x), 6) for x in ev_bug]

def corr_rank(sops, d, basis):
    TBd = basis(d)
    rows = []
    for sm in sops:
        rows.append([np.trace(sm @ Tb) for Tb in TBd])
    for i in range(3):
        for j in range(i, 3):
            O = (sops[i] @ sops[j] + sops[j] @ sops[i]) / 2
            rows.append([np.trace(O @ Tb) for Tb in TBd])
    M = np.array(rows)
    return int(np.linalg.matrix_rank(M, tol=1e-10)), M.shape[1]

# buggy kernel identification (on the r5.1a basis, matching 0cbc1e7)
rows = []
for O in B1:
    rows.append([np.trace(O @ Tb) for Tb in TB_r51a])
for i in range(3):
    for j in range(i, 3):
        O = (B1[i] @ B1[j] + B1[j] @ B1[i]) / 2
        rows.append([np.trace(O @ Tb) for Tb in TB_r51a])
Mbug = np.array(rows)
U, s_, Vt = np.linalg.svd(Mbug)
rk_bug = int((s_ > 1e-10 * s_.max()).sum())
null_bug = Vt[rk_bug:]
ker_labels = []
LAM = {"lam1": np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=complex) / np.sqrt(2),
       "lam2": np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]], dtype=complex) / np.sqrt(2),
       "lam4": np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]], dtype=complex) / np.sqrt(2),
       "lam5": np.array([[0, 0, -1j], [0, 0, 0], [1j, 0, 0]], dtype=complex) / np.sqrt(2)}
for v in null_bug:
    K = sum(c * Tb for c, Tb in zip(v, TB_r51a))
    K = K / np.linalg.norm(K, "fro")
    best, bname = -1, None
    for nm, L in LAM.items():
        ov = abs(np.trace(K.conj().T @ L))
        if ov > best:
            best, bname = ov, nm
    ker_labels.append((bname, round(float(best), 6)))

def ray(ket, sops):
    out = []
    proj = np.outer(ket, ket.conj())
    d = proj - np.eye(3, dtype=complex) / 3
    for p in (0.9, 0.99, 0.999, 0.9999):
        rho_p = (1 - p) * rho0 + p * proj
        g = g_closed(rho_p, d, sops)
        out.append(round((1 - p) ** 2 * g, 6))
    return out
ket_p1 = np.array([1, 0, 0], dtype=complex)
ket_0 = np.array([0, 1, 0], dtype=complex)
F2_coherent = ray(ket_p1, B1)
F2_nematic = ray(ket_0, B1)

F4_ranks = {}
for S, dim in ((0.5, 2), (1.0, 3), (1.5, 4)):
    rk, td = corr_rank(spin_ops_buggy(S), dim, tangent_basis_r51a)
    F4_ranks[f"S={S}"] = {"rank": rk, "tangent_dim": td}

R["FORENSIC"] = {
    "F1_buggy_spectrum": F1_spectrum,
    "F1_buggy_rank": rk_bug,
    "F1_buggy_kernel_labels": ker_labels,
    "F2_buggy_ray_coherent": F2_coherent,
    "F2_buggy_ray_nematic": F2_nematic,
    "F3_buggy_SxoSy_norm": F3_SxoSy_norm,
    "F3_buggy_Sx_block_match": F3_block_match,
    "F5_buggy_casimir_3half_diag": F5_diag,
    "F4_buggy_ranks": F4_ranks,
    "declared_match": {
        "F1": bool(F1_spectrum == [0, 0, 0, 0, 2.564146, 4.935854, 8.25, 8.25]
                   and rk_bug == 4),
        "F2": bool(F2_coherent[-1] == 3.0 and F2_nematic[-1] == 1.0),
        "F3": bool(F3_SxoSy_norm < 1e-12 and F3_block_match < 1e-12),
        "F4": bool(F4_ranks["S=0.5"]["rank"] == 1 and F4_ranks["S=1.0"]["rank"] == 4
                   and F4_ranks["S=1.5"]["rank"] == 9),
        "F5": bool(F5_diag == [2.25, 1.75, 3.75, 4.25]),
    },
}
R["FORENSIC"]["verdict"] = ("PASS" if all(R["FORENSIC"]["declared_match"].values())
                            else "FAIL")

# =====================================================================
# REPAIR BLOCK — fixed generators + orthonormal basis
# =====================================================================
G8 = np.zeros((8, 8))
for a in range(8):
    for b_ in range(8):
        G8[a, b_] = g_bilinear(rho0, TB_orth[a], TB_orth[b_], S1)
G8 = (G8 + G8.T) / 2
ev = np.sort(np.linalg.eigvalsh(G8))
n_9q4 = int(sum(abs(x - 2.25) < 1e-9 for x in ev))
n_6 = int(sum(abs(x - 6.0) < 1e-9 for x in ev))
R["A2_true_spectrum_I3"] = {
    "eigenvalues": [round(float(x), 8) for x in ev],
    "count_9/4": n_9q4, "count_6": n_6,
    "declared": "{9/4 x5, 6 x3}",
    "verdict": "PASS" if (n_9q4 == 5 and n_6 == 3) else "FAIL",
}

Ph = lambda X: -np.log(np.linalg.det(covariance(X, S1)))
eps = 1e-4
fd_cross = []
for k in (0, 7):
    fd = (Ph(rho0 + eps * TB_orth[k]) - 2 * Ph(rho0)
          + Ph(rho0 - eps * TB_orth[k])) / eps ** 2
    fd_cross.append((float(fd), float(g_closed(rho0, TB_orth[k], S1))))
R["A2_FD_crosscheck"] = {
    "pairs_fd_vs_closed": [(round(a, 6), round(b, 6)) for a, b in fd_cross],
    "verdict": "PASS" if all(abs(a - b) < 1e-4 for a, b in fd_cross) else "FAIL",
}

rng = np.random.default_rng(413)
def random_state(DIM):
    G = (rng.normal(size=(DIM, DIM)) + 1j * rng.normal(size=(DIM, DIM))) / np.sqrt(2)
    Hh = (G + G.conj().T) / 2
    w, v = np.linalg.eigh(Hh)
    w = np.exp(w); w = w / w.sum()
    return (v * w) @ v.conj().T

mins = []
kept = 0
for _ in range(500):
    rho = random_state(3)
    if np.linalg.det(covariance(rho, S1)) <= 1e-8:
        continue
    kept += 1
    M = np.zeros((8, 8))
    for a in range(8):
        for b_ in range(8):
            M[a, b_] = g_bilinear(rho, TB_orth[a], TB_orth[b_], S1)
    M = (M + M.T) / 2
    mins.append(float(np.linalg.eigvalsh(M).min()))
R["A3_true_PSD_500"] = {
    "kept": kept, "min_eig": round(float(np.min(mins)), 6),
    "declared_ginibre_min": 1.0366,
    "verdict": "PASS" if (np.min(mins) > 1.0) else "FAIL",
}

bseries = []
for eps_ in (1e-1, 1e-2, 1e-3, 1e-4):
    rho_eps = np.diag([eps_ / 2, 1 - eps_, eps_ / 2]).astype(complex)
    M = np.zeros((8, 8))
    for a in range(8):
        for b_ in range(8):
            M[a, b_] = g_bilinear(rho_eps, TB_orth[a], TB_orth[b_], S1)
    M = (M + M.T) / 2
    bseries.append({"eps": eps_, "lambda_min": round(float(np.linalg.eigvalsh(M).min()), 6)})
conv_ok = all(abs(d["lambda_min"] - 1.0) < 2 * d["eps"] for d in bseries)
R["A3_true_boundary_scan"] = {
    "points": bseries, "declared": "1.1080 -> 1.0001",
    "verdict": "PASS" if conv_ok else "FAIL",
}

true_coherent = ray(ket_p1, S1)
true_nematic = ray(ket_0, S1)
R["A4_true_rays"] = {
    "coherent": true_coherent, "nematic": true_nematic,
    "verdict": "PASS" if (abs(true_coherent[-1] - 1.0) < 5e-3
                          and abs(true_nematic[-1] - 1.0) < 5e-3) else "FAIL",
}

true_ranks = {}
for S, dim in ((0.5, 2), (1.0, 3), (1.5, 4)):
    rk, td = corr_rank(spin_ops(S), dim, tangent_basis_orthonorm)
    true_ranks[f"S={S}"] = {"rank": rk, "tangent_dim": td}
R["B_true_ranks"] = {
    "rows": true_ranks,
    "declared": "3/3, 8/8, 8/15",
    "S=3/2_kernel_dim": true_ranks["S=1.5"]["tangent_dim"] - true_ranks["S=1.5"]["rank"],
    "verdict": "PASS" if (true_ranks["S=0.5"]["rank"] == 3
                          and true_ranks["S=1.0"]["rank"] == 8
                          and true_ranks["S=1.5"]["rank"] == 8) else "FAIL",
}

# INJ': injectivity / diffeomorphism at S=1
rows = []
for sm in S1:
    rows.append([np.trace(sm @ Tb) for Tb in TB_orth])
for i in range(3):
    for j in range(i, 3):
        O = (S1[i] @ S1[j] + S1[j] @ S1[i]) / 2
        rows.append([np.trace(O @ Tb) for Tb in TB_orth])
MQ = np.array(rows)
rk_mq = int(np.linalg.matrix_rank(MQ, tol=1e-10))

var_min = np.inf
n_checked = 0
for _ in range(200):
    rho = random_state(3)
    w = np.linalg.eigvalsh(rho)
    if w[-2] < 1e-6:
        continue
    n_checked += 1
    C = covariance(rho, S1)
    ev = np.linalg.eigvalsh(C)
    if ev.min() < var_min:
        var_min = float(ev.min())
    if var_min < 1e-6:
        break

rr_resid = 0.0
for _ in range(50):
    rho = random_state(3)
    m = np.array([np.real(np.trace(rho @ s)) for s in S1])
    Q = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            Q[i, j] = np.real(np.trace(rho @ (S1[i] @ S1[j] + S1[j] @ S1[i]) / 2))
    C = Q - np.outer(m, m)
    Q2 = C + np.outer(m, m)
    rr_resid = max(rr_resid, float(np.linalg.norm(Q - Q2)))

R["INJ_S1"] = {
    "rank_mQ_on_tangent": rk_mq,
    "trivial_kernel": bool(rk_mq == 8),
    "n_rank2_states_checked": n_checked,
    "variance_min": round(var_min, 8),
    "variance_strictly_positive": bool(var_min > 1e-6),
    "roundtrip_residual": float(rr_resid),
    "verdict": "PASS" if (rk_mq == 8 and var_min > 1e-6 and rr_resid < 1e-12) else "FAIL",
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r51b_results.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

for k, v in R.items():
    if isinstance(v, dict) and "verdict" in v:
        print(f"{k:28} {v['verdict']}")
print("FORENSIC match details:", json.dumps(R["FORENSIC"]["declared_match"]))
