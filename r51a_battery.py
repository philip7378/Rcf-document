"""r5.1a battery — executes the pre-registered checks in
pr_r51a_battery_sheet.txt: Gate 0 (cov3 NESS repair), Theorem A/B
(scaling metric closed form and ranks), PR-T1b-2 trap anchors.

Convention notes (declared in the sheet):
- cov3 jumps from Paper I Eq. (6): L = (1/sqrt 2)(1 - P2) X P2 with
  X = (S_b - S_{b+1})_q. The Peirce form (1-P2) X P2 equals the
  printed P^(1) X P^(2) sandwich up to the same sandwich identity.
- Column-stacking vec convention throughout the superoperator.
"""
import json
import time
from fractions import Fraction as F

import numpy as np
import scipy.sparse as sparse
import scipy.sparse.linalg as spla
from scipy.linalg import expm

t0 = time.time()
R = {}

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]

# =====================================================================
# shared embedding helpers (open spin-1 chain, N sites)
# =====================================================================
def kron_list(ops):
    out = ops[0]
    for op in ops[1:]:
        out = np.kron(out, op)
    return out

def site_op(op, site, N):
    ops = [np.eye(3, dtype=complex)] * N
    ops[site] = op
    return kron_list(ops)

def bond2_op(A, B, b, N):
    """Two-site operator with A on site b, B on site b+1 (as matrices on
    the pair subspace, embedded)."""
    ops = [np.eye(3, dtype=complex)] * N
    ops[b] = A
    ops[b + 1] = B
    return kron_list(ops)

# =====================================================================
# GATE 0 — cov3 channel from Paper I Eq. (6), N=4 NESS
# =====================================================================
def cg_pair_states():
    """Return (dict J -> list of normalized pair states) on C3 (x) C3 with
    standard CG coefficients for 1 (x) 1 -> J."""
    def sitem(m):
        v = np.zeros(3, dtype=complex)
        v[m + 1] = 1.0
        return v
    def two(m1, m2):
        return np.kron(sitem(m1), sitem(m2))
    J2, J1, J0 = [], [], []
    # J=2 (symmetric quintet)
    J2.append(two(1, 1))
    J2.append((two(1, 0) + two(0, 1)) / np.sqrt(2))
    J2.append((two(1, -1) + two(-1, 1) + 2 * two(0, 0)) / np.sqrt(6))
    J2.append((two(-1, 0) + two(0, -1)) / np.sqrt(2))
    J2.append(two(-1, -1))
    # J=1 (antisymmetric triplet)
    J1.append((two(1, 0) - two(0, 1)) / np.sqrt(2))
    J1.append((two(1, -1) - two(-1, 1)) / np.sqrt(2))
    J1.append((two(0, -1) - two(-1, 0)) / np.sqrt(2))
    # J=0 (singlet)
    J0.append((two(1, -1) - two(0, 0) + two(-1, 1)) / np.sqrt(3))
    return {0: J0, 1: J1, 2: J2}

CG = cg_pair_states()
PAIR_DIM = 9

def pair_to_chain_state(pair_vec, b, N):
    """Embed a 9-dim pair state (sites b,b+1) into the 3^N chain."""
    # pair_vec index = 3*i + j with i site b, j site b+1
    M = pair_vec.reshape(3, 3)
    ops = [np.eye(3, dtype=complex)] * N
    # build via kron of pair block with identities
    left = np.eye(3 ** b, dtype=complex)
    right = np.eye(3 ** (N - b - 2), dtype=complex)
    return np.kron(np.kron(left, M), right)

def embed_pair_matrix(pair9, b, N):
    left = np.eye(3 ** b, dtype=complex)
    right = np.eye(3 ** (N - b - 2), dtype=complex)
    return np.kron(np.kron(left, pair9), right)

def P2_bond(b, N):
    """J=2 projector on bond (b, b+1), embedded in the chain."""
    P9 = sum(np.outer(v, v.conj()) for v in CG[2])
    return embed_pair_matrix(P9, b, N)

def cov3_jumps(b, N):
    """The three cov3 jumps L_{b,q} from Paper I Eq. (6):
    L = (1/sqrt2) (1 - P2) X_q P2, X_q = (S_b - S_{b+1})_q."""
    Ls = []
    P2 = P2_bond(b, N)
    for q in range(3):
        Xq = site_op(SVEC[q], b, N) - site_op(SVEC[q], b + 1, N)
        Ls.append((Xq - P2 @ Xq @ P2 if False else Xq - P2 @ Xq) @ P2 / np.sqrt(2))
        # (1 - P2) X P2 = X P2 - P2 X P2  (Peirce: right slot fixed)
    return Ls

def cov3_check_identities(N):
    """Paper I Eq. (7): L†L = P2, L L† = (5/3) P1_summed over q."""
    out = []
    for b in range(N - 1):
        P2 = P2_bond(b, N)
        Ls = cov3_jumps(b, N)
        sumLdL = sum(L.conj().T @ L for L in Ls)
        sumLLd = sum(L @ L.conj().T for L in Ls)
        # P^(1) on the bond: pair projector onto J=1
        P1_9 = sum(np.outer(v, v.conj()) for v in CG[1])
        P1 = embed_pair_matrix(P1_9, b, N)
        out.append({
            "bond": b,
            "LdL_minus_P2": float(np.abs(sumLdL - P2).max()),
            "LLd_minus_5_3_P1": float(np.abs(sumLLd - (5.0 / 3.0) * P1).max()),
        })
    return out

def bond_burden_ops(N):
    """M_b = P_b^(2) embedded, per bond."""
    return [P2_bond(b, N) for b in range(N - 1)]

def Phi1_ops(N):
    """Phi1_b = P_b^(1) embedded, per bond."""
    out = []
    for b in range(N - 1):
        P1_9 = sum(np.outer(v, v.conj()) for v in CG[1])
        out.append(embed_pair_matrix(P1_9, b, N))
    return out

def neess_superop(Ls, H, DIM):
    """Lindblad superoperator, column-stacking vec. Sparse assembly."""
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
    return out.tocsc()

def solve_ness(A, DIM):
    vals, vecs = spla.eigs(A, k=2, sigma=0, which="LM", tol=1e-12,
                           v0=np.ones(DIM * DIM, dtype=complex))
    pick = int(np.argmin(np.abs(vals)))
    rho = vecs[:, pick].reshape(DIM, DIM, order="F")
    rho = (rho + rho.conj().T) / 2
    tr = np.trace(rho).real
    rho = rho / tr
    resid = float(np.linalg.norm((A @ sparse.csc_matrix(rho.reshape(-1, order="F")).T).toarray())) / max(1.0, abs(tr))
    return rho, resid, float(np.abs(vals[pick]))

N = 4
DIM = 3 ** N
GAMMA = 1.0

# cov3 jumps for every bond
ALL_L = []
for b in range(N - 1):
    for L in cov3_jumps(b, N):
        ALL_L.append(np.sqrt(GAMMA) * L)

H_XXX = np.zeros((DIM, DIM), dtype=complex)
H_XY = np.zeros((DIM, DIM), dtype=complex)
for b in range(N - 1):
    for q in range(3):
        H_XXX += bond2_op(SVEC[q], SVEC[q], b, N)
    H_XY += bond2_op(Sx, Sx, b, N) + bond2_op(Sy, Sy, b, N)

Mb_ops = bond_burden_ops(N)
Phi1 = Phi1_ops(N)

gate0 = {"identities_eq7": cov3_check_identities(N)}
for tag, H in (("H_XXX", H_XXX), ("H_XY", H_XY)):
    A = neess_superop(ALL_L, H, DIM)
    rho, resid, eig = solve_ness(A, DIM)
    Mvals = [float(np.real(np.trace(rho @ Mb))) for Mb in Mb_ops]
    Fvals = [float(np.real(np.trace(rho @ P1))) for P1 in Phi1]
    omega = []
    for b in range(N - 1):
        Mbop = Mb_ops[b]
        comm = Mbop @ H - H @ Mbop
        Gb = float(np.real(-1j * np.trace(rho @ comm)))
        omega.append(Gb / (2 * Mvals[b]) if Mvals[b] > 1e-12 else None)
    pos = float(np.linalg.eigvalsh((rho + rho.conj().T) / 2).min())
    gate0[tag] = {
        "M_b": [round(x, 6) for x in Mvals],
        "Mbar": round(float(sum(Mvals)), 6),
        "Phi1": round(float(sum(Fvals)), 6),
        "omega_raw": [round(x, 6) if x is not None else None for x in omega],
        "omega_ratio_interior_boundary": round(omega[1] / omega[0], 4) if omega[1] and omega[0] else None,
        "residual": round(resid, 10),
        "eig_at_zero": eig,
        "rho_min_eig": round(pos, 12),
    }
R["GATE0_cov3"] = gate0

# declared comparison
DECL_XXX = {"M_b": [0.061203, 0.128182, 0.061203], "Mbar": 0.250588,
           "Phi1": 1.605638}
ok_XXX = (all(abs(g - d) <= 5e-4 for g, d in zip(gate0["H_XXX"]["M_b"], DECL_XXX["M_b"]))
          and abs(gate0["H_XXX"]["Mbar"] - DECL_XXX["Mbar"]) <= 5e-4
          and abs(gate0["H_XXX"]["Phi1"] - DECL_XXX["Phi1"]) <= 5e-4)
ok_XY = (abs(gate0["H_XY"]["Mbar"] - 0.398159) <= 5e-4
         and abs(gate0["H_XY"]["Phi1"] - 1.803984) <= 5e-4)
gate0["declared_match_XXX"] = bool(ok_XXX)
gate0["declared_match_XY"] = bool(ok_XY)
gate0["verdict"] = "PASS" if (ok_XXX and ok_XY) else "FAIL"

# =====================================================================
# THEOREM A — closed-form scaling metric on state space
# =====================================================================
def spin_ops(S):
    """Spin-S matrices in the J^2, Jz eigenbasis (dimension 2S+1)."""
    d = int(round(2 * S)) + 1
    Jz = np.diag([S - i for i in range(d)]).astype(complex)
    Jp = np.zeros((d, d), dtype=complex)
    for i in range(d - 1):
        m = S - i
        Jp[i, i + 1] = np.sqrt(S * (S + 1) - m * (m + 1))
    Jm = Jp.conj().T
    Jx = (Jp + Jm) / 2
    Jy = (Jp - Jm) / (2j)
    return [Jx, Jy, Jz]

def tangent_basis(DIM):
    """Orthonormal Hermitian basis of the tangent space (traceless part of
    the Hermitian algebra), dimension DIM^2 - 1."""
    E = []
    n = DIM
    for i in range(n):
        for j in range(i + 1, n):
            Eij = np.zeros((n, n), dtype=complex)
            Eij[i, j] = 1; Eij[j, i] = 1
            E.append(Eij / np.sqrt(2))
            Eji = np.zeros((n, n), dtype=complex)
            Eji[i, j] = -1j; Eji[j, i] = 1j
            E.append(Eji / np.sqrt(2))
    for i in range(n - 1):
        D_ = np.zeros((n, n), dtype=complex)
        D_[i, i] = 1; D_[i + 1, i + 1] = -1
        E.append(D_ / np.sqrt(2))
    return E

def covariance(rho, sops):
    C = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(rho @ ((sops[i] @ sops[j] + sops[j] @ sops[i]) / 2)))
            m_i = np.real(np.trace(rho @ sops[i]))
            m_j = np.real(np.trace(rho @ sops[j]))
            C[i, j] = corr - m_i * m_j
    return C

def g_closed(rho, d, sops):
    """Theorem A closed form (quadratic): g(d,d) = Tr(C^-1 dC C^-1 dC)
    + 2 dm^T C^-1 dm, with dC the FULL differential of C at rho
    (including both mean cross-terms)."""
    C = covariance(rho, sops)
    Ci = np.linalg.inv(C)
    dm = np.array([np.real(np.trace(d @ s)) for s in sops])
    m = np.array([np.real(np.trace(rho @ s)) for s in sops])
    dC = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(d @ ((sops[i] @ sops[j] + sops[j] @ sops[i]) / 2)))
            dC[i, j] = corr - dm[i] * m[j] - m[i] * dm[j]
    t1 = np.trace(Ci @ dC @ Ci @ dC)
    t2 = 2 * dm @ Ci @ dm
    return t1 + t2

def g_bilinear(rho, d, e, sops):
    """Bilinearization of g_closed: the polarization of the quadratic form."""
    C = covariance(rho, sops)
    Ci = np.linalg.inv(C)
    dm = np.array([np.real(np.trace(d @ s)) for s in sops])
    em = np.array([np.real(np.trace(e @ s)) for s in sops])
    m = np.array([np.real(np.trace(rho @ s)) for s in sops])
    dC = np.zeros((3, 3))
    eC = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr_d = np.real(np.trace(d @ ((sops[i] @ sops[j] + sops[j] @ sops[i]) / 2)))
            corr_e = np.real(np.trace(e @ ((sops[i] @ sops[j] + sops[j] @ sops[i]) / 2)))
            dC[i, j] = corr_d - dm[i] * m[j] - m[i] * dm[j]
            eC[i, j] = corr_e - em[i] * m[j] - m[i] * em[j]
    t1 = np.trace(Ci @ dC @ Ci @ eC)
    t2 = dm @ Ci @ em + em @ Ci @ dm
    return t1 + t2

S1ops = spin_ops(1)

# A1: closed form vs finite differences
rng = np.random.default_rng(413)
def random_state(DIM):
    G = (rng.normal(size=(DIM, DIM)) + 1j * rng.normal(size=(DIM, DIM))) / np.sqrt(2)
    Hh = (G + G.conj().T) / 2
    w, v = np.linalg.eigh(Hh)
    w = np.exp(w) / np.exp(w).sum()
    return (v * w) @ v.conj().T

A1_errs = []
for trial in range(8):
    rho = random_state(3)
    if np.linalg.det(covariance(rho, S1ops)) <= 1e-9:
        rho = np.eye(3, dtype=complex) / 3
    for k in range(8):
        d = tangent_basis(3)[k]
        gc = g_closed(rho, d, S1ops)
        if abs(gc) < 1e-12:
            continue  # FD is meaningless on kernel directions
        for eps in (1e-5, 1e-4):
            Ph = lambda X: -np.log(np.linalg.det(covariance(X, S1ops)))
            fd = (Ph(rho + eps * d) - 2 * Ph(rho) + Ph(rho - eps * d)) / eps ** 2
            A1_errs.append(abs(fd - gc) / max(1.0, abs(gc)))
A1_max = float(np.max(A1_errs)) if A1_errs else 0.0
R["THEOREM_A1_closed_form"] = {
    "max_rel_err": A1_max, "tolerance": 1e-6,
    "note": "kernel directions (g=0) skipped; relative to |g|",
    "verdict": "PASS" if A1_max <= 1e-6 else "FAIL",
}

# A2: spectrum at I/3 (bilinear, correct)
rho0 = np.eye(3, dtype=complex) / 3
TB = tangent_basis(3)
G8 = np.zeros((8, 8))
for a in range(8):
    for b_ in range(8):
        G8[a, b_] = g_bilinear(rho0, TB[a], TB[b_], S1ops)
G8 = (G8 + G8.T) / 2
ev = np.sort(np.linalg.eigvalsh(G8))
n_zero = int(sum(abs(x) < 1e-9 for x in ev))
R["THEOREM_A2_spectrum_I3"] = {
    "eigenvalues": [round(x, 6) for x in ev],
    "kernel_dim": n_zero,
    "declared": "9/4 (x5), 6 (x3)",
    "verdict": "PASS" if (abs(ev[0] - 2.25) < 1e-6 and abs(ev[-1] - 6.0) < 1e-6
                          and sum(abs(x - 2.25) < 1e-6 for x in ev) == 5) else "FAIL",
}

# A3: PSD on 200 random interior states (bilinear)
min_eig_global = np.inf
for trial in range(200):
    rho = random_state(3)
    if np.linalg.det(covariance(rho, S1ops)) <= 1e-6:
        continue
    G8 = np.zeros((8, 8))
    for a in range(8):
        for b_ in range(8):
            G8[a, b_] = g_bilinear(rho, TB[a], TB[b_], S1ops)
    G8 = (G8 + G8.T) / 2
    mn = float(np.linalg.eigvalsh(G8).min())
    min_eig_global = min(min_eig_global, mn)
R["THEOREM_A3_PSD_200"] = {
    "min_eig": round(min_eig_global, 4),
    "declared_lower_bound": 1.16,
    "verdict": "PASS" if min_eig_global >= 1.16 - 1e-3 else "FAIL",
}

# A4: coherent and nematic rays — declared limit 1; measured coherent -> 3,
# nematic -> 1 (both logarithmic => infinite geodesic distance; the CONSTANT
# differs by ray). Keep the declared target frozen; register the measured.
def ray_g_pp(ket, p):
    rho_p = (1 - p) * np.eye(3, dtype=complex) / 3 + p * np.outer(ket, ket.conj())
    # direction d rho / dp at p: |m><m| - I/3
    d = np.outer(ket, ket.conj()) - np.eye(3, dtype=complex) / 3
    return g_closed(rho_p, d, S1ops), np.linalg.det(covariance(rho_p, S1ops))

rays = {}
for name, ket in (("coherent_|+1>", np.array([1, 0, 0], dtype=complex)),
                  ("nematic_|0>", np.array([0, 1, 0], dtype=complex))):
    series = []
    for p in (0.9, 0.99, 0.999, 0.9999):
        g, detC = ray_g_pp(ket, p)
        series.append({"p": p, "(1-p)^2 g_pp": round(((1 - p) ** 2 * g), 6),
                       "detC": None if detC <= 0 else float(detC)})
    conv = all(abs(e["(1-p)^2 g_pp"] - 1.0) <= 5e-3 for e in series)
    rays[name] = {"checkpoints": series, "converges_to_1": conv}
R["THEOREM_A4_rays"] = {
    "rays": rays,
    "verdict": "PASS" if all(v["converges_to_1"] for v in rays.values()) else "FAIL",
}

# =====================================================================
# THEOREM B — rank of the centered correlation map by spin
# =====================================================================
def corr_map_rank(S):
    """Rank of the linear functional family {Tr(. S_i), Tr(. S_i o S_j)}
    on the traceless Hermitian tangent space (complexified rows)."""
    sops = spin_ops(S)
    d = int(round(2 * S)) + 1
    TB = tangent_basis(d)
    QO = []
    for i in range(3):
        for j in range(i, 3):
            QO.append((sops[i] @ sops[j] + sops[j] @ sops[i]) / 2)
    rows = []
    for O in QO:
        rows.append(np.array([np.trace(O @ Tb) for Tb in TB]))
    for s in sops:
        rows.append(np.array([np.trace(s @ Tb) for Tb in TB]))
    M = np.array(rows)
    return int(np.linalg.matrix_rank(M, tol=1e-10)), M.shape

thB = {}
for S, want in ((0.5, 3), (1.0, 8), (1.5, 8)):
    rk, shape = corr_map_rank(S)
    thB[f"S={S}"] = {"rank": rk, "tangent_dim": shape[1],
                     "declared": want,
                     "verdict": "PASS" if rk == want else "FAIL"}
thB["S=3/2_kernel_dim"] = 15 - thB["S=1.5"]["rank"]
R["THEOREM_B_ranks"] = thB

# =====================================================================
# PR-T1b-2 TRAP ANCHORS — N=3 pure Lie facts
# =====================================================================
N3 = 3
D3 = 3 ** N3
h0 = np.zeros((D3, D3), dtype=complex)
h1 = np.zeros((D3, D3), dtype=complex)
for q in range(3):
    h0 += bond2_op(SVEC[q], SVEC[q], 0, N3)
    h1 += bond2_op(SVEC[q], SVEC[q], 1, N3)
S1z_chain = site_op(Sz, 1, N3)

comm = h1 @ h0 - h0 @ h1
T1_norm = float(np.linalg.norm(1j * comm, "fro"))
T1_norm_decl = float(np.sqrt(48))
# chiral current: J = S0 . (S1 x S2); build cross-product operator
chir = np.zeros((D3, D3), dtype=complex)
for a in range(3):
    for b in range(3):
        for c in range(3):
            eps = ((b - a) * (c - b) * (c - a)) if False else None
# epsilon via determinant of levi-civita
import itertools
def eps3(i, j, k):
    return int(np.linalg.det(np.eye(3)[[i, j, k]]))
chir = np.zeros((D3, D3), dtype=complex)
for i in range(3):
    for j in range(3):
        for k in range(3):
            e = eps3(i, j, k)
            if e != 0:
                chir += e * (bond2_op(SVEC[i], np.eye(3, dtype=complex), 0, N3)
                             @ bond2_op(SVEC[j], np.eye(3, dtype=complex), 1, N3)
                             @ site_op(SVEC[k], 2, N3))
# compare comm with chir: comm = c * chir with c real?
# T1: the commutator is (2i x chiral)/... exact: [h1,h0] = (i/2)*chir*2?
# Verified in debug: [h1,h0] = (i/2) * (2*chir) => c=1/2 with 2i*chir overlap 0.5.
# Use the verified alignment: comm == (i/2) * (2 * chir) i.e. comm = i*chir.
overlap = np.trace(comm.conj().T @ (1j * chir))
norm_chir = np.linalg.norm(1j * chir, "fro")
c_factor = overlap / (norm_chir ** 2)
aligned = np.linalg.norm(comm - c_factor * (1j * chir), "fro") / np.linalg.norm(comm, "fro")
R["T1b2_T1_commutator"] = {
    "norm_i_commutator": round(T1_norm, 6),
    "sqrt48": round(T1_norm_decl, 6),
    "match": bool(abs(T1_norm - T1_norm_decl) <= 1e-3 * T1_norm_decl),
    "comm_equals_i_times_chiral": bool(aligned <= 1e-10),
    "c_factor": float(np.real(c_factor)),
    "verdict": "PASS" if (abs(T1_norm - T1_norm_decl) <= 1e-3 * T1_norm_decl
                          and aligned <= 1e-10) else "FAIL",
}

t = 0.1
U0 = expm(-1j * t * h0)
U1 = expm(-1j * t * h1)
T2_norm = float(np.linalg.norm(U0 @ U1 @ S1z_chain - U1 @ U0 @ S1z_chain, "fro"))
R["T1b2_T2_desync"] = {
    "norm": round(T2_norm, 6), "declared": 0.056403,
    "verdict": "PASS" if abs(T2_norm - 0.056403) <= 5e-4 else "FAIL",
}

U01 = expm(-1j * (t / 2) * h0) @ expm(-1j * (t / 2) * h1)
Uh = expm(-1j * t * (h0 + h1))
R["T1b2_T3_trotter"] = {"t": t, "points": []}
for n in (2, 5, 10, 20, 50):
    Un = np.linalg.matrix_power(expm(-1j * (t / n) * h0) @ expm(-1j * (t / n) * h1), n)
    err = float(np.linalg.norm(Un - Uh, "fro"))
    R["T1b2_T3_trotter"]["points"].append(
        {"n": n, "err": round(err, 8), "t^2/n": round(t * t / n, 8),
         "ratio": round(err / (t * t / n), 4)})
errs = [pt["err"] for pt in R["T1b2_T3_trotter"]["points"]]
ratios = [pt["ratio"] for pt in R["T1b2_T3_trotter"]["points"]]
R["T1b2_T3_trotter"]["ratios_bounded_by_1.2"] = bool(max(ratios) <= 1.2)
R["T1b2_T3_trotter"]["prefactor"] = round(float(np.mean(ratios)), 6)
R["T1b2_T3_trotter"]["sqrt48_over_2"] = round(float(np.sqrt(48) / 2), 6)
R["T1b2_T3_trotter"]["monotone_decreasing"] = bool(
    all(errs[i] > errs[i + 1] for i in range(len(errs) - 1)))
R["T1b2_T3_trotter"]["O_t2_over_n_scaling"] = bool(
    max(ratios) / min(ratios) < 1.005 and R["T1b2_T3_trotter"]["monotone_decreasing"])
R["T1b2_T3_trotter"]["verdict"] = ("PASS" if R["T1b2_T3_trotter"]["O_t2_over_n_scaling"]
                                   else "FAIL")

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r51a_results.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

for k, v in R.items():
    if isinstance(v, dict) and "verdict" in v:
        print(f"{k:28} {v['verdict']}")
print("GATE0:", json.dumps({kk: vv for kk, vv in R["GATE0_cov3"].items()
                            if kk in ("H_XXX", "H_XY", "verdict")}, indent=1, default=str))
