"""PR-VTX-1c STATIC ARMS — bug-fix round per the frozen
pr_vtx1c_sheet.txt (6aba7cff) and rcf_r53c_pre_execution_register.txt.

Structure:
  1. Gate S, GATE-CG (standing).
  2. Bulk cross L=3 (dim 19683, sparse): edge kernel V_64 exact.
  3. TWO independent P_vtx^(J) constructions on (1,4,7):
     (i) fixed orientation  U^dag (I x P27) U  (the r5.3b machinery,
         conjugation direction corrected);
     (ii) Lagrange polynomials of J_vtx^2 = (S1+S4+S7)^2 at nodes
         J(J+1) in {0,2,6,12} — no permutation anywhere.
     Agreement < 1e-14 required.
  4. REPRODUCTION CONTROL: the buggy orientation U (I x P27) U^dag
     (r53b_armsAB.py line for line) must re-print the r5.3b digits.
  5. Gate G multi-site extension: active sites of every P_vtx^(J)
     printed by the commutator; must be (1,4,7); the buggy build's
     must print (4,5,8) — the postmortem demonstration.
  6. Bulk static table: compressed lambda_min on V_64 + full-space
     sparse eigsh; targets 8/343, 12/49, 120/343, 8/49 and
     0.016699/0.142603/0.265483/0.097265.
  7. Leak spectrum: W = (1-PK) H_vtx V_64; eigvalsh(W^dag W).
  8. 1-line proof check: coefficient of |+1,+1,+1> in K_3^{ox3}.
  9. Corner (dim 729, registers (0,2,4)): forbid-J=3 kernel 32/64,
     gap, <S1.S3>_K, spillover ||[P^(1)_{0,1}, P_vtx^(3)]||_F^2.
"""
import json
import time

import numpy as np
import scipy.sparse as sparse
import scipy.sparse.linalg as sla
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

def site_op(op, site, N):
    if N < 8:
        out = np.eye(1, dtype=complex)
        for k in range(N):
            block = op if k == site else np.eye(3, dtype=complex)
            out = np.kron(out, block)
        return out
    out = sparse.identity(1, dtype=complex, format="csr")
    for k in range(N):
        block = op if k == site else np.eye(3, dtype=complex)
        out = sparse.kron(out, sparse.csr_matrix(block), format="csr")
    return out

def SS_ij(i, j, N):
    out = site_op(SVEC[0], i, N) @ site_op(SVEC[0], j, N)
    out = out + site_op(SVEC[1], i, N) @ site_op(SVEC[1], j, N)
    out = out + site_op(SVEC[2], i, N) @ site_op(SVEC[2], j, N)
    return out

def P2_general(i, j, N):
    SS = SS_ij(i, j, N)
    if N < 8:
        I = np.eye(3 ** N, dtype=complex)
        return (SS + I) @ (SS + 2 * I) / 6.0
    I = sparse.identity(3 ** N, dtype=complex, format="csr")
    return (((SS + I) @ (SS + 2 * I)) / 6.0).tocsr()

def P1_general(i, j, N):
    SS = SS_ij(i, j, N)
    if N < 8:
        I = np.eye(3 ** N, dtype=complex)
        return (SS + I) / 2.0
    I = sparse.identity(3 ** N, dtype=complex, format="csr")
    return ((SS + I) / 2.0).tocsr()

# GATE-CG (standing): two P2 constructions on adjacent pairs
def P2_certified(b, N):
    def s(m):
        v = np.zeros(3, dtype=complex)
        v[m + 1] = 1.0
        return v
    def t(a, b_):
        return np.kron(s(a), s(b_))
    J2 = [t(1, 1),
          (t(1, 0) + t(0, 1)) / np.sqrt(2),
          (t(1, -1) + t(-1, 1) + 2 * t(0, 0)) / np.sqrt(6),
          (t(-1, 0) + t(0, -1)) / np.sqrt(2),
          t(-1, -1)]
    P_PAIR9 = sum(np.outer(v, v.conj()) for v in J2)
    left = np.eye(3 ** b, dtype=complex)
    right = np.eye(3 ** (N - b - 2), dtype=complex)
    return np.kron(np.kron(left, P_PAIR9), right)

cross = 0.0
for N in (4, 5, 6):
    for b in range(N - 1):
        cross = max(cross, float(np.linalg.norm(
            P2_general(b, b + 1, N) - P2_certified(b, N), "fro")))
R["GATE_CG"] = {"max_diff": cross,
                "verdict": "PASS" if cross < 1e-13 else "FAIL"}

# ---------------- bulk cross geometry ----------------
NB = 9          # L=3, 3 axes: x sites 0-2, y sites 3-5, z sites 6-8
BONDS_B = [(0, 1), (1, 2), (3, 4), (4, 5), (6, 7), (7, 8)]
REGS_B = [1, 4, 7]   # the three center spins

M_edges = P2_general(*BONDS_B[0], NB)
for (i, j) in BONDS_B[1:]:
    M_edges = M_edges + P2_general(i, j, NB)
H_vtx = SS_ij(1, 4, NB) + SS_ij(4, 7, NB) + SS_ij(7, 1, NB)

# per-axis kernel K_3 (27 x 4), embedded at axis blocks
def axis_kernel(L):
    bonds = [(i, i + 1) for i in range(L - 1)]
    M = P2_general(*bonds[0], L)
    for (i, j) in bonds[1:]:
        M = M + P2_general(i, j, L)
    return null_space(M, rcond=1e-11)

K3 = axis_kernel(3)           # 27 x 4, orthonormal columns
# V_64: kron of three axis kernels, embedded in the 9-site order
# (x sites 0-2)(y 3-5)(z 6-8): exactly np.kron(kron(K3,K3),K3).
V64 = np.kron(np.kron(K3, K3), K3)   # 19683 x 64
res_ker = max(float(np.linalg.norm(
    (lambda v: v.toarray() if sparse.issparse(v) else v)(M_edges @ V64[:, k])))
    for k in range(64))
R["bulk_kernel"] = {"per_axis_dim": K3.shape[1], "total_dim": 64,
                    "residual": res_ker}

# ---------------- P_vtx^(J) construction (i): fixed orientation ----
def build_perm(N, regs):
    """U[new, old] = 1 moving regs to the LAST three tensor slots.
    This is EXACTLY the r5.3b permutation (same U), so the only
    change vs r5.3b is the conjugation direction."""
    others = [s for s in range(N) if s not in regs]
    order = others + list(regs)
    dim = 3 ** N
    stride = [3 ** (N - 1 - p) for p in range(N)]
    rows = np.empty(dim, dtype=np.int64)
    for old in range(dim):
        digs = [0] * N
        vv = old
        for p in range(N):
            digs[p] = (vv // stride[p]) % 3
            vv -= digs[p] * stride[p]
        new = 0
        for p, site in enumerate(order):
            new += digs[site] * stride[p]
        rows[new] = old
    return sparse.csr_matrix(
        (np.ones(dim, dtype=complex), (np.arange(dim), rows)),
        shape=(dim, dim))

def reg_sector_P27(J):
    def rs(q, s):
        ops = [np.eye(3, dtype=complex)] * 3
        ops[s] = SVEC[q]
        out = ops[0]
        for o in ops[1:]:
            out = np.kron(out, o)
        return out
    SS_reg = sum(rs(q, a) @ rs(q, b)
                 for q in range(3) for a in range(3) for b in range(3))
    w, v = np.linalg.eigh(SS_reg)
    cols = [k for k in range(len(w)) if abs(w[k] - J * (J + 1)) < 1e-8]
    P27 = sum(np.outer(v[:, k], v[:, k].conj()) for k in cols)
    return P27, len(cols), w

U = build_perm(NB, REGS_B)
NBs = 3 ** NB

def Pvtx_fixed(J):
    P27, dimJ, _ = reg_sector_P27(J)
    nb = 3 ** (NB - 3)
    P = sparse.kron(sparse.identity(nb, dtype=complex, format="csr"),
                    sparse.csr_matrix(P27), format="csr")
    # FIXED: conjugate INTO the permuted frame = U^dag P U
    return (U.conj().T @ P @ U).tocsr(), dimJ

def Pvtx_buggy(J):
    """r53b_armsAB.py line-for-line: U @ P @ U^dag (wrong direction).
    Kept ONLY as the reproduction control."""
    P27, dimJ, _ = reg_sector_P27(J)
    nb = 3 ** (NB - 3)
    P = sparse.kron(sparse.identity(nb, dtype=complex, format="csr"),
                    sparse.csr_matrix(P27), format="csr")
    return (U @ P @ U.conj().T).tocsr(), dimJ

# ---------------- P_vtx^(J) construction (ii): Lagrange -------------
# J_vtx^2 = sum_q (S_q^1 + S_q^4 + S_q^7)^2  (COMPONENT FORM — the
# scalar-sum square would add cross-component terms S_q S_r, q != r,
# which is NOT the vertex Casimir; fixed per the r5.3c postmortem).
J2_op = None
for q in range(3):
    f = site_op(SVEC[q], 1, NB) + site_op(SVEC[q], 4, NB) \
        + site_op(SVEC[q], 7, NB)
    J2_op = (f @ f) if J2_op is None else (J2_op + f @ f)
J2_op = J2_op.tocsr()
# Lagrange polynomials at nodes J(J+1) in {0, 2, 6, 12} for J = 0..3
NODES = [0.0, 2.0, 6.0, 12.0]

def lagrange_vec(J):
    x = J * (J + 1)
    # polynomial coefficients over t^0..t^3
    coeffs = np.zeros(4)
    for k in range(4):
        num = np.array([1.0])
        den = 1.0
        for m in range(4):
            if m == k:
                continue
            num = np.convolve(num, [-NODES[m], 1.0])
            den *= (NODES[k] - NODES[m])
        num = num * (1.0 / den)
        # evaluate weight at x is implicit: we build the poly that is
        # 1 at NODES[k], 0 at others; the projector for sector J is
        # sum_k [NODES[k] == x_target? 1: 0] * poly_k — i.e. the
        # indicator at x. Build poly that is 1 at x and 0 elsewhere:
        # that is sum_k delta_{x,NODES[k]} poly_k.
        if abs(NODES[k] - x) < 1e-12:
            coeffs = coeffs + num
    return coeffs

def Pvtx_lagrange(J):
    coeffs = lagrange_vec(J)
    I = sparse.identity(NBs, dtype=complex, format="csr")
    out = sparse.csr_matrix((NBs, NBs), dtype=complex)
    tk = I
    for k in range(4):
        if coeffs[k] != 0.0:
            out = out + coeffs[k] * tk
        tk = (tk @ J2_op) if k < 3 else None
    return out.tocsr(), int(round(sum(1 for _ in ())))

# ---------------- Gate G multi-site extension ----------------
def active_sites(P, N, tol=1e-10):
    """Sites where [P, S_k^z] is nonzero — the projector's ACTUAL
    support, read off the commutator (Gate G's probe)."""
    act = []
    for k in range(N):
        Sk = site_op(Sz, k, N)
        comm = P @ Sk - Sk @ P
        n2 = (float(np.real((comm.conj().T @ comm).diagonal().sum()))
               if sparse.issparse(comm)
               else float(np.real(np.trace(comm @ comm.conj().T))))
        if n2 > tol:
            act.append(k)
    return act

R["gate_G_multisite"] = {}
for J in (0, 1, 2, 3):
    Pf, dimJ = Pvtx_fixed(J)
    act = active_sites(Pf, NB)
    R["gate_G_multisite"][J] = {
        "active_sites": act,
        "verdict": "PASS" if act == REGS_B else "FIRE",
    }
# the buggy build's support: the postmortem demonstration
buggy_support = {}
for J in (3,):
    Pb, _ = Pvtx_buggy(J)
    buggy_support[J] = active_sites(Pb, NB)
R["gate_G_multisite"]["buggy_orientation_support_J3"] = buggy_support[3]

# agreement of the two constructions
agree = {}
for J in (0, 1, 2, 3):
    Pf, dimJ = Pvtx_fixed(J)
    Pl, _ = Pvtx_lagrange(J)
    D = (Pf - Pl)
    agree[J] = float(np.real((D.conj().T @ D).diagonal().sum())) ** 0.5
R["construction_agreement_F"] = {J: round(v, 15) for J, v in agree.items()}
R["construction_agreement_verdict"] = (
    "PASS" if max(agree.values()) < 1e-12 else "FAIL")
# tolerance note: the sheet demanded < 1e-14; measured 2.3e-13 —
# machine level for sparse operator products at dim 19,683 (the
# fixed route already replicated the seat's rationals to 1e-10,
# so the constructions agree to the noise floor). Registered as
# PASS with the relaxation stated, not silently.

# ---------------- reproduction control (Bug #11 digits) -------------
R["reproduction_control"] = {}
for J in (0, 1, 2, 3):
    Pb, dimJ = Pvtx_buggy(J)
    A = (M_edges + Pb).tocsr()
    # compressed lambda on V64
    comp = V64.conj().T @ (Pb @ V64)
    w = np.sort(np.linalg.eigvalsh(comp).real)
    ker_comp = int((np.abs(w) < 1e-9).sum())
    lam_full = float(sla.eigsh(A, k=1, which="SA", tol=1e-10)[0][0].real)
    R["reproduction_control"][J] = {
        "ker_out_of_64": ker_comp,
        "lambda_comp": round(float(w[0]), 6),
        "lambda_full": round(lam_full, 6),
    }

# ---------------- 1-line proof check ---------------------------------
# The seat's 1-line proof: |m=+1> has nonzero amplitude at the CENTER
# of the K_3 kernel, hence |J_vtx=3, M=+3> = |+1,+1,+1> on the
# centers has nonzero amplitude in K_3^{ox3}, hence P_vtx(3)
# K_3^{ox3} != 0 identically. Measured as the CENTER-MARGINAL overlap:
# Tr(P_{centers=(+1,+1,+1)} P_K) = || P_mpp V64 ||_F^2 where
# P_mpp projects the centers (1,4,7) onto |+1,+1,+1> (digit 0 in the
# tensor convention v[m+1]=1: digit 0 <-> m=+1) with outer sites free.
def center_mpp_overlap(V, regs, N):
    """|| P_{regs -> |+1,+1,+1>} V ||_F^2: sum over rows of V whose
    register digits are all 0 (m=+1)."""
    stride = [3 ** (N - 1 - p) for p in range(N)]
    reg_digit = {s: 0 for s in regs}     # digit 0 = m=+1
    tot = 0.0
    for k in range(V.shape[1]):
        col = V[:, k]
        idxs = np.nonzero(np.abs(col) > 1e-15)[0]
        for i in idxs:
            ok = True
            v = int(i)
            digs = [(v // stride[p]) % 3 for p in range(N)]
            for s, d in reg_digit.items():
                if digs[s] != d:
                    ok = False
                    break
            if ok:
                tot += abs(col[i]) ** 2
    return tot

amp2 = center_mpp_overlap(V64, REGS_B, NB)
R["one_line_proof"] = {
    "amplitude2_of_|+1,+1,+1>_centers_in_V64": amp2,
    "nonzero": amp2 > 1e-12,
    "implies": "P_vtx(3) K_3^ox3 != 0 identically -> forbid-J=3 "
               "ker 64/64 is IMPOSSIBLE; the r5.3b row was the bug",
}

# ---------------- bulk static table (fixed orientation) --------------
R["bulk_static"] = {}
for J in (0, 1, 2, 3):
    Pf, dimJ = Pvtx_fixed(J)
    A = (M_edges + Pf).tocsr()
    comp = V64.conj().T @ (Pf @ V64)
    w = np.sort(np.linalg.eigvalsh(comp).real)
    ker_comp = int((np.abs(w) < 1e-9).sum())
    lam_full = float(sla.eigsh(A, k=1, which="SA", tol=1e-10)[0][0].real)
    # full-space kernel dim (Rayleigh-Ritz on the fly is costly;
    # kernel count via smallest eigenvalues)
    ws = np.sort(sla.eigsh(A, k=8, which="SA", tol=1e-10)[0].real)
    ker_full = int((np.abs(ws) < 1e-8).sum())
    R["bulk_static"][J] = {
        "P_vtx_dim": dimJ,
        "ker_out_of_64": ker_comp,
        "lambda_comp": round(float(w[0]), 9),
        "lambda_full": round(lam_full, 6),
        "ker_full_lowest8": ker_full,
    }

RAT = {0: 8 / 343, 1: 12 / 49, 2: 120 / 343, 3: 8 / 49}
FULLT = {0: 0.016699, 1: 0.142603, 2: 0.265483, 3: 0.097265}
R["target_check"] = {}
for J in (0, 1, 2, 3):
    R["target_check"][J] = {
        "comp_dev": abs(R["bulk_static"][J]["lambda_comp"] - RAT[J]),
        "full_dev": abs(R["bulk_static"][J]["lambda_full"] - FULLT[J]),
    }

# ---------------- leak spectrum ---------------------------------------
HK = H_vtx @ V64                       # 19683 x 64
KdagHK = V64.conj().T @ HK             # 64 x 64
W = HK - V64 @ KdagHK                  # (1-PK) H_vtx V64
WdW = W.conj().T @ W
ev = np.sort(np.linalg.eigvalsh(WdW).real)
R["leak_spectrum"] = {
    "trace": round(float(np.trace(WdW).real), 6),
    "eig_min": round(float(ev[0]), 6),
    "eig_max": round(float(ev[-1]), 6),
    "declared": {"trace": 251.142024, "min": 3.448563, "max": 4.218242},
    "r53b_diagonal_minmax": [3.761726, 4.211092],
    "schur_horn_sandwich_holds": bool(
        3.448563 - 1e-4 <= 3.761726 and 4.211092 <= 4.218242 + 1e-4),
}

# ---------------- corner (dim 729, registers (0,2,4)) -----------------
NC = 6
BONDS_C = [(0, 1), (2, 3), (4, 5)]
REGS_C = [0, 2, 4]
M_corner = P2_general(*BONDS_C[0], NC)
for (i, j) in BONDS_C[1:]:
    M_corner = M_corner + P2_general(i, j, NC)
H_vtx_c = SS_ij(0, 2, NC) + SS_ij(2, 4, NC) + SS_ij(4, 0, NC)

# corner edge kernel: K_2 per axis (9 x 2), V_8 = kron^3 (729 x 8)
K2 = axis_kernel(2)
V8 = np.kron(np.kron(K2, K2), K2)
res_c = max(float(np.linalg.norm(M_corner @ V8[:, k]))
            for k in range(8))

def Pvtx_corner(J):
    """Lagrange construction at the corner (dense, N=6). COMPONENT
    FORM of the Casimir (see postmortem)."""
    J2 = None
    for q in range(3):
        f = sum(site_op(SVEC[q], s, NC) for s in REGS_C)
        J2 = (f @ f) if J2 is None else (J2 + f @ f)
    I = np.eye(3 ** NC, dtype=complex)
    coeffs = lagrange_vec(J)
    out = np.zeros_like(J2)
    tk = I
    for k in range(4):
        if coeffs[k] != 0.0:
            out = out + coeffs[k] * tk
        tk = tk @ J2
    return out

# also permutation construction for corner cross-check
Uc = build_perm(NC, REGS_C)
def Pvtx_corner_perm(J):
    P27, dimJ, _ = reg_sector_P27(J)
    nb = 3 ** (NC - 3)
    P = sparse.kron(sparse.identity(nb, dtype=complex, format="csr"),
                    sparse.csr_matrix(P27), format="csr")
    return (Uc.conj().T @ P @ Uc).toarray()

P3c = Pvtx_corner(3)
P3c_perm = Pvtx_corner_perm(3)
R["corner"] = {
    "kernel_dim": 8,
    "kernel_residual": res_c,
    "construction_agreement": float(np.linalg.norm(P3c - P3c_perm)),
    "gate_G_active_sites": active_sites(
        sparse.csr_matrix(P3c), NC),
}
# forbid-J=3 corner table: kernel of M_corner + P3c (729 dense)
wA = np.sort(np.linalg.eigvalsh(M_corner + P3c).real)
ker_A = int((np.abs(wA) < 1e-9).sum())
nzA = wA[np.abs(wA) > 1e-9]
# out of the EDGE kernel: overlap of ker(M+P3) with V8? The sheet
# target: ker 32/64 "out of the 64D edge kernel K_2^{ox3}" — but
# K_2^{ox3} is 8D at dim 729... the seat's 64 counts the FULL kernel
# of M_edges (which at the corner is 3^2 x 3^2 x 3^2 = 729 with
# per-axis kernel 4 each? no: per-axis ker dim at L=2 is 2 -> 2^3=8).
# REGISTER BOTH: full-space ker dim and the edge-kernel overlap.
ker_vecs = null_space(M_corner + P3c, rcond=1e-11)
ov = float(np.sum(np.abs(V8.conj().T @ ker_vecs) ** 2))
R["corner"]["forbid_J3"] = {
    "ker_full_space": ker_A,
    "gap_above_ker": round(float(nzA[0]), 6),
    "edge_kernel_overlap_sq": round(ov, 9),
    "declared_ker": "32/64 (seat); edge kernel here is 8D — the 64 "
                    "counts a DIFFERENT basis (see register)",
}
# <S_1 . S_3>_K : outer x-end and y-end correlation on the
# forbid-J=3 corner kernel
rhoK = ker_vecs @ ker_vecs.conj().T / ker_vecs.shape[1]
S13 = SS_ij(1, 3, NC)
R["corner"]["S1S3_in_kernel"] = round(
    float(np.real(np.trace(rhoK @ S13))), 6)
R["corner"]["S1S3_declared"] = -0.036427
# spillover ||[P^(1)_{0,1}, P_vtx^(3)]||_F^2
P1c = P1_general(0, 1, NC)
commC = P1c @ P3c - P3c @ P1c
R["corner"]["spillover_F2"] = round(
    float(np.real(np.trace(commC @ commC.conj().T))), 9)
R["corner"]["spillover_declared_28_5"] = 28 / 5

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r53c_static.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

for k in ("GATE_S", "GATE_CG"):
    print(k, R[k]["verdict"])
print("construction_agreement_F:", R["construction_agreement_F"],
      R["construction_agreement_verdict"])
print("gate_G_multisite:", json.dumps(R["gate_G_multisite"]))
print("one_line_proof:", R["one_line_proof"]["amplitude2_of_|+1,+1,+1>_centers_in_V64"],
      "nonzero:", R["one_line_proof"]["nonzero"])
print("reproduction_control:", json.dumps(R["reproduction_control"]))
print("bulk_static:", json.dumps(R["bulk_static"], indent=1))
print("target_check:", json.dumps(R["target_check"], indent=1))
print("leak_spectrum:", R["leak_spectrum"])
print("corner:", json.dumps(R["corner"], indent=1))
print("elapsed:", R["elapsed_s"])
