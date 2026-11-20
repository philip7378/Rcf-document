"""PR-LINK-1 EXECUTION — per the frozen pr_link1_sheet.txt.

CHK-1 closure-at-3 on the certified corner (N=6, regs (0,2,4),
stubs (1,3,5)): stub correlation profiles Phi_mu as functions on
(1) the 8D bare edge kernel V_8 and (2) the 32D forbid-J=3 corner
kernel; Gram/isotropy; displacement-profile rank; the H_vtx-coupled
frame (M + 0.01 H_vtx kernel).

CHK-2 preservation: GATE-P (Tr + idempotency of every projector in
use), GATE-G (active sites), frustration-free residual, leak
spectrum non-negative.

CHK-3 cocycle: (a) on-axis |c(n)| = (1/3)^n exact multiplicative
decay at L = 2..6 (signed alternation reported); (b) junction
triangle defect from the profile-inferred log-distances;
(c) Thm-8 channel-rate object reported, fenced.

CHK-4: guards; ambiguity fires INCONCLUSIVE.
"""
import json
import time

import numpy as np
from scipy.linalg import null_space

t0 = time.time()
R = {}

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]

gs = max(float(np.linalg.norm(a @ b - b @ a - 1j * c))
         for a, b, c in ((Sx, Sy, Sz), (Sy, Sz, Sx), (Sz, Sx, Sy)))
cas = float(np.linalg.norm(Sx @ Sx + Sy @ Sy + Sz @ Sz - 2 * np.eye(3)))
R["GATE_S"] = {"max_comm": gs, "casimir": cas,
               "verdict": "PASS" if max(gs, cas) < 1e-14 else "FAIL"}

def so(op, site, N):
    out = np.eye(1, dtype=complex)
    for k in range(N):
        out = np.kron(out, op if k == site else np.eye(3, dtype=complex))
    return out

def SS(i, j, N):
    return sum(so(SVEC[q], i, N) @ so(SVEC[q], j, N) for q in range(3))

def P2_general(i, j, N):
    S = SS(i, j, N)
    I = np.eye(3 ** N, dtype=complex)
    return (S + I) @ (S + 2 * I) / 6.0

def sector_P(J, N, pair=(0, 1)):
    """Correct projector onto the pair's J sector; SS nodes {-2,-1,+1}.
    P0 = (SS+I)(SS-I)/3; P1 = -1/2 (SS-I)(SS+2I); P2 = (SS+I)(SS+2I)/6.
    GATE-P rides: Tr and idempotency returned with the projector."""
    SSij = SS(pair[0], pair[1], N)
    I = np.eye(3 ** N, dtype=complex)
    nodes = [-2.0, -1.0, 1.0]
    target = nodes[J]
    poly = np.array([0.0, 0.0, 0.0])
    for k in range(3):
        num = np.array([1.0]); den = 1.0
        for m in range(3):
            if m == k:
                continue
            num = np.convolve(num, [-nodes[m], 1.0])
            den *= (nodes[k] - nodes[m])
        if abs(nodes[k] - target) < 1e-12:
            poly = poly + num / den
    P = poly[0] * I + poly[1] * SSij + poly[2] * (SSij @ SSij)
    tr = float(np.real(np.trace(P)))
    idem = float(np.linalg.norm(P @ P - P))
    return P, tr, idem

# ---------------- certified corner layout ---------------------------
NC = 6
BONDS_C = [(0, 1), (2, 3), (4, 5)]
REGS_C = [0, 2, 4]
STUBS = [1, 3, 5]
M_corner = P2_general(*BONDS_C[0], NC)
for (i, j) in BONDS_C[1:]:
    M_corner = M_corner + P2_general(i, j, NC)
H_vtx_c = SS(0, 2, NC) + SS(2, 4, NC) + SS(4, 0, NC)

def axis_kernel(L):
    bonds = [(i, i + 1) for i in range(L - 1)]
    M = P2_general(*bonds[0], L)
    for (i, j) in bonds[1:]:
        M = M + P2_general(i, j, L)
    return null_space(M, rcond=1e-11)

K2 = axis_kernel(2)
V8 = np.kron(np.kron(K2, K2), K2)
res_ff = max(float(np.linalg.norm(M_corner @ V8[:, k])) for k in range(8))

def Pvtx_corner(J):
    J2 = None
    for q in range(3):
        f = sum(so(SVEC[q], s, NC) for s in REGS_C)
        J2 = (f @ f) if J2 is None else (J2 + f @ f)
    I = np.eye(3 ** NC, dtype=complex)
    NODES = [0.0, 2.0, 6.0, 12.0]
    x = J * (J + 1)
    coeffs = np.zeros(4)
    for k in range(4):
        num = np.array([1.0]); den = 1.0
        for m in range(4):
            if m == k:
                continue
            num = np.convolve(num, [-NODES[m], 1.0])
            den *= (NODES[k] - NODES[m])
        if abs(NODES[k] - x) < 1e-12:
            coeffs = coeffs + num / den
    out = np.zeros_like(J2)
    tk = I
    for k in range(4):
        if coeffs[k] != 0.0:
            out = out + coeffs[k] * tk
        tk = tk @ J2
    return out

# ---------------- CHK-2: preservation gates -------------------------
gp = {}
for J in (0, 1, 2):
    P, tr, idem = sector_P(J, NC, (0, 1))
    gp[J] = {"Tr": tr, "idempotency": idem}
P3c = Pvtx_corner(3)
gp["Pvtx3"] = {"Tr": float(np.real(np.trace(P3c))),
               "idempotency": float(np.linalg.norm(P3c @ P3c - P3c))}
R["CHK2_GATE_P"] = {k: (v | {"verdict": "PASS" if v["idempotency"] < 1e-12 else "FAIL"})
                     for k, v in gp.items()}

def active_sites(P, N, tol=1e-10):
    act = []
    for k in range(N):
        Sk = so(Sz, k, N)
        C = P @ Sk - Sk @ P
        n2 = float(np.real(np.trace(C @ C.conj().T)))
        if n2 > tol:
            act.append(k)
    return act

R["CHK2_GATE_G"] = {
    "Pvtx3_active_sites": active_sites(P3c, NC),
    "verdict": "PASS" if active_sites(P3c, NC) == REGS_C else "FIRE",
}
# leak non-negative spectrum re-witness on the corner
W_leak = (np.eye(3 ** NC) - V8 @ V8.conj().T) @ H_vtx_c @ V8
lw = np.sort(np.linalg.eigvalsh(W_leak.conj().T @ W_leak).real)
R["CHK2_leak"] = {"min": round(float(lw[0]), 6),
                  "max": round(float(lw[-1]), 6),
                  "verdict": "PASS" if lw[0] > 0 else "FAIL"}
R["CHK2_frustration_free"] = {"residual": res_ff,
                              "verdict": "PASS" if res_ff < 1e-12 else "FAIL"}

# ---------------- CHK-1: the stub profile frame ---------------------
# kernels: (1) bare edge kernel V_8; (2) forbid-J=3 corner kernel 32D
ker32 = null_space(M_corner + P3c, rcond=1e-11)
KERS = {"V8": V8, "K32": ker32}
frames = {}
for kname, K in KERS.items():
    rho = K @ K.conj().T / K.shape[1]
    # profile functions: Phi_mu(X) = <S_z^{stub mu} S_z^X>_K for X in
    # all 6 sites; and center anchors via register correlations
    Phi = {}
    for mu, stub in enumerate(STUBS):
        Phi[mu] = np.array([float(np.real(np.trace(
            rho @ (so(Sz, stub, NC) @ so(Sz, x, NC))))) for x in range(NC)])
    PhiC = np.array([float(np.real(np.trace(
        rho @ (so(Sz, 0, NC) + so(Sz, 2, NC) + so(Sz, 4, NC)) @ so(Sz, x, NC))))
        for x in range(NC)])
    # the 3 profiles as 6-dim vectors; Gram of the triple
    Gm = np.array([[float(Phi[a] @ Phi[b]) for b in range(3)] for a in range(3)])
    wG = np.sort(np.linalg.eigvalsh(Gm).real)
    # displacement profiles Delta_mu = Phi_mu - Phi_center, 6-dim
    Dm = np.array([Phi[mu] - PhiC for mu in range(3)])
    rD = int(np.linalg.matrix_rank(Dm, tol=1e-9))
    sv = np.linalg.svd(Dm, compute_uv=False)
    # center-anchored stub Gram (isotropy of the stub triple)
    Gs = np.array([[float(Phi[a] @ Phi[b]) for b in range(3)] for a in range(3)])
    ws = np.sort(np.linalg.eigvalsh(Gs).real)
    frames[kname] = {
        "kernel_dim": K.shape[1],
        "stub_Gram_eigs": [round(float(x), 9) for x in ws],
        "stub_Gram_isotropy_ratio": round(float(ws[-1] / max(ws[0], 1e-18)), 12),
        "displacement_rank": rD,
        "displacement_svs": [round(float(s), 9) for s in sv],
    }
R["CHK1_static"] = frames

# coupled frame: kernel of M + eps H_vtx (eps = 0.01)
EPS = 0.01
Mc = M_corner + EPS * H_vtx_c
# eigen-ground space of the 0.01*H_vtx-lifted corner: take the lowest
# 40 eigenvalues, keep those within 1e-9 of the minimum... the coupled
# kernel is the low-energy subspace; the profile frame on the LOWEST
# 32 states (matching ker32's dimension)
wA, vA = np.linalg.eigh(Mc)
low = vA[:, :32]
rho_c = low @ low.conj().T / low.shape[1]
Phi = {}
for mu, stub in enumerate(STUBS):
    Phi[mu] = np.array([float(np.real(np.trace(
        rho_c @ (so(Sz, stub, NC) @ so(Sz, x, NC))))) for x in range(NC)])
PhiC = np.array([float(np.real(np.trace(
    rho_c @ (so(Sz, 0, NC) + so(Sz, 2, NC) + so(Sz, 4, NC)) @ so(Sz, x, NC))))
    for x in range(NC)])
Dm = np.array([Phi[mu] - PhiC for mu in range(3)])
rD = int(np.linalg.matrix_rank(Dm, tol=1e-9))
sv = np.linalg.svd(Dm, compute_uv=False)
Gs = np.array([[float(Phi[a] @ Phi[b]) for b in range(3)] for a in range(3)])
ws = np.sort(np.linalg.eigvalsh(Gs).real)
R["CHK1_coupled_eps0.01"] = {
    "gap_low": round(float(wA[32]), 9),
    "stub_Gram_eigs": [round(float(x), 9) for x in ws],
    "stub_Gram_isotropy_ratio": round(float(ws[-1] / max(ws[0], 1e-18)), 12),
    "displacement_rank": rD,
    "displacement_svs": [round(float(s), 9) for s in sv],
}

# ---------------- CHK-3: cocycle -------------------------------------
# (a) on-axis exact multiplicative decay: |c(n)| = (1/3)^n, L = 2..6
on_axis = {}
for L in (2, 3, 4, 5, 6):
    K = axis_kernel(L)
    rho = K @ K.conj().T / K.shape[1]
    cvals = {}
    for n in range(1, L):
        cvals[n] = float(np.real(np.trace(
            rho @ (so(Sz, 0, L) @ so(Sz, n, L)))))
    on_axis[L] = {"kernel_dim": K.shape[1],
                  "c": {n: round(v, 9) for n, v in cvals.items()},
                  "abs_ratio_c1": {n: round(abs(cvals[n]) / ((1 / 3) ** n), 9)
                                   for n in cvals}}
R["CHK3a_on_axis"] = on_axis

# (b) junction triangle defect from profile-inferred log-distances:
# d(mu, nu) = -ln |corr(stub mu, stub nu)| via the register-bonded
# chain center; triangle over (stub x -> center -> stub y -> stub x)
# The honest object: |corr(stub_mu, stub_nu)| on the corner kernel
rho32 = ker32 @ ker32.conj().T / ker32.shape[1]
stub_corr = {}
for a in range(3):
    for b in range(a, 3):
        c = float(np.real(np.trace(rho32 @ (so(Sz, STUBS[a], NC)
                                           @ so(Sz, STUBS[b], NC)))))
        stub_corr[(a, b)] = c
d_stubs = {(a, b): (-np.log(abs(stub_corr[(a, b)])) if abs(stub_corr[(a, b)]) > 1e-12 else np.inf)
           for (a, b) in stub_corr}
# register-to-stub distances (the three "center -> stub" legs)
d_regstub = {}
for mu, stub in enumerate(STUBS):
    c = float(np.real(np.trace(rho32 @ (so(Sz, 0, NC) @ so(Sz, stub, NC)))))
    d_regstub[(0, mu)] = -np.log(abs(c)) if abs(c) > 1e-12 else np.inf
# triangle defect: d(x,y) vs d(x,center)+d(center,y) inferred
tri = {}
for (a, b) in [(0, 1), (0, 2), (1, 2)]:
    direct = d_stubs[(a, b)] if (a, b) in d_stubs else d_stubs[(b, a)]
    via = d_regstub[(0, a)] + d_regstub[(0, b)]
    tri[f"{a}{b}"] = {"direct": round(direct, 9), "via_center": round(via, 9),
                      "defect": round(via - direct, 9)}
R["CHK3b_triangle"] = {"stub_corr": {f"{a},{b}": round(v, 9)
                                     for (a, b), v in stub_corr.items()},
                       "reg_stub_corr": {f"0,{mu}": round(v, 9)
                                         for (s, mu), v in d_regstub.items()},
                       "triangles": tri}
# 2-link reference for the defect comparison: the on-axis two-bond
# violation registered at r5.1d (registered constant 0.4896 spread /
# B2 fail 0.20) — for THIS sheet the reference is the via-vs-direct
# mismatch magnitude; reported as its own number.

# (c) Thm-8 channel-rate object: r = 2/3 per locality; log-distance
# per locality ln(3/2). Reported, fenced as the RATE object (not the
# static correlation); the closure question is NOT asked of it here.
R["CHK3c_channel_object"] = {
    "r_dipole_channel": 2 / 3, "log_distance_per_locality": float(np.log(3 / 2)),
    "fence": "extension-map eigen-rate (Paper I Thm 8), not a static "
             "kernel correlation; reported for the register's D-b "
             "distance convention only",
}

# ---------------- CHK-4 guards --------------------------------------
amb = []
for kname, fr in frames.items():
    ws_ = fr["stub_Gram_eigs"]
    if ws_[0] <= 1e-12:
        amb.append(f"{kname}: stub Gram near-degenerate")
    if fr["displacement_rank"] != 3:
        amb.append(f"{kname}: displacement rank {fr['displacement_rank']} != 3")
if R["CHK1_coupled_eps0.01"]["displacement_rank"] != 3:
    amb.append("coupled frame rank != 3")
R["CHK4_guards"] = {"ambiguities": amb,
                    "verdict": "CLEAN" if not amb else "INCONCLUSIVE-FIRE"}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r61_link1.json", "w") as f:
    json.dump(R, f, indent=2, default=str)
print(json.dumps(R, indent=1, default=str))
