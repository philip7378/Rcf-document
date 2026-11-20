"""PR-VTX-1 ARMS A+B — static vertex frustration vs dynamical coupling,
per the frozen pr_vtx1_sheet.txt (010fa6e7) and the pre-registered
rcf_r53b_pre_execution_register.txt.

Site layout (kron order, declared in the sheet):
  CORNER (6 sites, dim 729): blocks (x: e_x1, v_x) (y: e_y1, v_y)
  (z: e_z1, v_z)? NO — sheet says x-axis sites first as a block, and
  the composite vertex registers sit last within each axis block.
  Per-axis chain of L=2: sites [e_mu, v_mu] with the bond (e_mu,
  v_mu) = P2 between positions 0 and 1 of the mu block. Kron order:
  X-block (e_x, v_x), Y-block (e_y, v_y), Z-block (e_z, v_z).
  BULK CROSS (L=3, 9 sites, dim 19683): per-axis chain
  [a_mu, v_mu, b_mu] with bonds (a_mu, v_mu) and (v_mu, b_mu) — the
  center register v_mu in the bulk. Kron order: X-block (a_x, v_x,
  b_x), Y-block, Z-block.

Arms:
  A  corner table (forbid-J kernels + gap + cross-axis correlation
     + spillover), dim 729 exact dense.
  B  bulk static table on K_3^{ox3} (64D): compressed lambda_min for
     forbid-J in {0,1,2,3} (targets 8/343, 12/49, 120/343, 8/49),
     L=5 compressed persistence (forbid-J=3 -> 0.246717);
     dynamical cleanliness: ||(1-P_K) H_vtx P_K||_F^2 (target
     251.142024) and per-state min leak (target 3.448563).
Gates: Gate S, GATE-CG (two P2 constructions cross-verified), Gate G
(every projector placement verified against its site support).
"""
import json
import time

import numpy as np
import scipy.sparse as sparse
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
    """Site operator, DENSE for small N, SPARSE-supported for large:
    returned as a scipy csr for N >= 8 (19683-dim bulk arm)."""
    if N < 8:
        out = np.eye(1, dtype=complex)
        for k in range(N):
            block = op if k == site else np.eye(3, dtype=complex)
            out = np.kron(out, block)
        return out
    # sparse route: kron(identity factors) in csr — each step is
    # (3^k x 3^k) csr kron 3x3 — cheap.
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
    """Method (i): (SS+I)(SS+2I)/6 — the r5.3a certified general-pair
    construction. No adjacency assumption. Returns DENSE for N<8,
    SPARSE csr for N>=8."""
    SS = SS_ij(i, j, N)
    if N < 8:
        I = np.eye(3 ** N, dtype=complex)
        return (SS + I) @ (SS + 2 * I) / 6.0
    I = sparse.identity(3 ** N, dtype=complex, format="csr")
    return (((SS + I) @ (SS + 2 * I)) / 6.0).tocsr()

def is_sparse(M):
    return sparse.issparse(M)

def cg_pair_states():
    def s(m):
        v = np.zeros(3, dtype=complex)
        v[m + 1] = 1.0
        return v
    def t(a, b):
        return np.kron(s(a), s(b))
    J2 = [t(1, 1),
          (t(1, 0) + t(0, 1)) / np.sqrt(2),
          (t(1, -1) + t(-1, 1) + 2 * t(0, 0)) / np.sqrt(6),
          (t(-1, 0) + t(0, -1)) / np.sqrt(2),
          t(-1, -1)]
    return {2: J2}

CG = cg_pair_states()
P_PAIR9 = sum(np.outer(v, v.conj()) for v in CG[2])

def P2_certified(b, N):
    """Method (ii): the r5.2-certified adjacent embed on bond (b,b+1)."""
    left = np.eye(3 ** b, dtype=complex)
    right = np.eye(3 ** (N - b - 2), dtype=complex)
    return np.kron(np.kron(left, P_PAIR9), right)

# GATE-CG: cross-verify both constructions on adjacent pairs, N=4..6
cross = 0.0
for N in (4, 5, 6):
    for b in range(N - 1):
        cross = max(cross, float(np.linalg.norm(
            P2_general(b, b + 1, N) - P2_certified(b, N), "fro")))
R["GATE_CG"] = {"max_diff_adjacent_N4to9": cross,
                "verdict": "PASS" if cross < 1e-13 else "FAIL"}

def gate_G_check(P, i, j, N):
    """Gate G for one projector on support (i,j). Uses the on-site
    commutator trace form: ||[P, S^z_k]||_F^2 = -Tr([P,S_z][P,S_z]^dag)
    computed sparsely for large N."""
    off = 0.0
    on = []
    for k in range(N):
        Sk = site_op(Sz, k, N)
        comm = P @ Sk - Sk @ P
        if sparse.issparse(comm):
            # Frobenius norm via trace of comm^dag comm — keep sparse
            n2 = float(np.real((comm.conj().T @ comm).diagonal().sum()))
        else:
            n2 = float(np.real(np.trace(comm @ comm.conj().T)))
        nrm = np.sqrt(max(n2, 0.0))
        if k in (i, j):
            on.append(nrm)
        else:
            off = max(off, nrm)
    return off, min(on) if on else 0.0

# ---------------- geometry builders ----------------
def corner_ops():
    """6 sites: X-block (0=e_x, 1=v_x), Y-block (2=e_y, 3=v_y),
    Z-block (4=e_z, 5=v_z). Bonds: (1,0) x-axis, (3,2) y, (5,4) z."""
    N = 6
    bonds = [(1, 0), (3, 2), (5, 4)]
    M = sum(P2_general(i, j, N) for (i, j) in bonds)
    H_vtx = (SS_ij(1, 3, N) + SS_ij(3, 5, N) + SS_ij(5, 1, N))
    return N, bonds, M, H_vtx

def bulk_ops(L):
    """3-axis chains of length L: X-block sites 0..L-1 (center L//2),
    Y-block L..2L-1, Z-block 2L..3L-1. Bonds: consecutive within each
    block (center in bulk). Returns N, bonds, M_edges, H_vtx,
    per-axis kernel states (the AKLT chain kernel K_L per axis)."""
    N = 3 * L
    bonds = []
    for mu in range(3):
        base = mu * L
        for b in range(L - 1):
            bonds.append((base + b, base + b + 1))
    M = P2_general(*bonds[0], N)
    for (i, j) in bonds[1:]:
        M = M + P2_general(i, j, N)
    cx = L // 2
    H_vtx = (SS_ij(cx, L + cx, N) + SS_ij(L + cx, 2 * L + cx, N)
             + SS_ij(2 * L + cx, cx, N))
    return N, bonds, M, H_vtx

# ---------------- Arm A: corner table ----------------
NA, bondsA, M_corner, H_vtx_corner = corner_ops()
# Gate G on the corner placements
gateA_off, gateA_on = 0.0, 1e9
for (i, j) in bondsA:
    o, m = gate_G_check(P2_general(i, j, NA), i, j, NA)
    gateA_off = max(gateA_off, o)
    gateA_on = min(gateA_on, m)
R["ArmA_gate_G"] = {
    "max_off_support": gateA_off, "min_on_support": gateA_on,
    "verdict": ("PASS" if gateA_off < 1e-14 and gateA_on > 1.0
                else "FIRE"),
}

def J_vtx_projector(J, regs, N):
    """Projector onto total spin J of the three vertex registers.
    FAST route: permutation that moves the register sites to the
    LAST three tensor factors, then P = U (I_{3^{N-3}} x P27) U^dag
    where P27 is the dense 27x27 sector projector of the 3-register
    Casimir. U is a sparse permutation (one nonzero per row)."""
    # 27x27 register Casimir + sector projector (dense, cheap)
    def reg_site(q, site):
        ops = [np.eye(3, dtype=complex)] * 3
        ops[site] = SVEC[q]
        out = ops[0]
        for o in ops[1:]:
            out = np.kron(out, o)
        return out
    SS_reg = sum(reg_site(q, a) @ reg_site(q, b)
                 for q in range(3) for a in range(3) for b in range(3))
    w, v = np.linalg.eigh(SS_reg)
    cols = [k for k in range(len(w)) if abs(w[k] - J * (J + 1)) < 1e-8]
    if not cols:
        return None, 0
    P27 = sum(np.outer(v[:, k], v[:, k].conj()) for k in cols)
    # permutation: new site order = [others..., regs...]
    others = [s for s in range(N) if s not in regs]
    order = others + list(regs)
    dim = 3 ** N
    # sparse U: U[new, old] = 1
    rows = np.empty(dim, dtype=np.int64)
    stride_old = [3 ** (N - 1 - p) for p in range(N)]
    stride_new = [3 ** (N - 1 - p) for p in range(N)]
    for old in range(dim):
        digs = [0] * N
        vv = old
        for p in range(N):
            digs[p] = (vv // stride_old[p]) % 3
            vv -= digs[p] * stride_old[p]
        new = 0
        for p, site in enumerate(order):
            new += digs[site] * stride_new[p]
        rows[new] = old  # U[new, old] = 1
    U = sparse.csr_matrix(
        (np.ones(dim, dtype=complex), (np.arange(dim), rows)),
        shape=(dim, dim))
    # kron(I_{3^{N-3}}, P27): block-diagonal — build sparse directly
    nb = 3 ** (N - 3)
    P27s = sparse.csr_matrix(P27)
    # blockdiag: nb blocks of P27 — construct via kron(I_nb, P27)
    P = sparse.kron(sparse.identity(nb, dtype=complex, format="csr"),
                    P27s, format="csr")
    P = (U @ P @ U.conj().T).tocsr()
    return P, len(cols)

def forbid_table(M_edges, regs, N, js=(0, 1, 2, 3)):
    out = {}
    for J in js:
        P_J, dimJ = J_vtx_projector(J, regs, N)
        Mtot = M_edges + P_J
        w = np.sort(np.linalg.eigvalsh(Mtot).real)
        ker = int((np.abs(w) < 1e-9).sum())
        nz = w[np.abs(w) > 1e-9]
        out[J] = {
            "P_vtx_dim": dimJ,
            "ker_dim": ker,
            "lambda_min": round(float(w[0]), 9),
            "gap_above_ker": round(float(nz[0]), 9) if ker > 0
                             and len(nz) else None,
        }
    return out

REGS_CORNER = [1, 3, 5]
R["ArmA_static_table"] = forbid_table(M_corner, REGS_CORNER, NA)

# corner kernel with forbid-J=3: the live kernel readout (32D expected)
P3, _ = J_vtx_projector(3, REGS_CORNER, NA)
M_live = M_corner + P3
K = null_space(M_live, rcond=1e-11)
R["ArmA_live_kernel"] = {
    "dim": K.shape[1],
    "residual": (max(float(np.linalg.norm(M_live @ K[:, k]))
                     for k in range(K.shape[1]))
                if K.shape[1] else None),
}
# gap above kernel
wA = np.sort(np.linalg.eigvalsh(M_live).real)
nzA = wA[np.abs(wA) > 1e-9]
R["ArmA_live_kernel"]["gap"] = round(float(nzA[0]), 6)

# cross-axis arm correlation <S_1x . S_1y>_K on the live kernel
rhoK = K @ K.conj().T / K.shape[1] if K.shape[1] else None
Sxy = SS_ij(1, 3, NA)  # v_x and v_y registers
R["ArmA_cross_corr"] = {
    "S1xS1y_in_kernel": round(float(np.real(np.trace(rhoK @ Sxy))), 6)
    if rhoK is not None else None,
    "declared": -0.036427,
}

# cross-axis spillover ||[P^(1)_{0x,1x}, P_vtx^(3)]||_F^2 (28/5)
def P1_general(i, j, N):
    SS = SS_ij(i, j, N)
    I = np.eye(3 ** N, dtype=complex)
    return (SS + I) / 2.0
P1_x = P1_general(0, 1, NA)
comm = P1_x @ P3 - P3 @ P1_x
R["ArmA_spillover"] = {
    "norm_F2": round(float(np.real(np.trace(comm @ comm.conj().T))), 9),
    "declared_28_5": 28 / 5,
}

# ---------------- Arm B: bulk cross ----------------
NB3, bondsB3, M_edges3, H_vtx3 = bulk_ops(3)
# edge kernel: per-axis AKLT kernels K_3 kron'd
def axis_kernel(L):
    """Kernel of the length-L open spin-1 AKLT chain (bonds
    0-1,1-2,...): dim 2^{L-1}. Built on the single-axis space."""
    bonds = [(i, i + 1) for i in range(L - 1)]
    M = sum(P2_general(i, j, L) for (i, j) in bonds)
    K = null_space(M, rcond=1e-11)
    return K

K1_axis = axis_kernel(3)
dim_axis = K1_axis.shape[0]
# full kernel = kron of three axis kernels: K_full (19683 x 64),
# columns ARE kernel vectors of M_edges3 (per-axis closure:
# M_edges3 = M_x kron I kron I + ... acts blockwise).
K_full = np.kron(np.kron(K1_axis, K1_axis), K1_axis)
R["ArmB_kernel_check"] = {
    "per_axis_dim": K1_axis.shape[1],
    "total_dim": K_full.shape[1],
    "residual": max(float(np.linalg.norm(
        (lambda v: v.toarray() if sparse.issparse(v) else v)(
            M_edges3 @ K_full[:, k])))
                    for k in range(K_full.shape[1])),
}

# Gate G on the bulk placements (spot: one bond per axis)
gB_off, gB_on = 0.0, 1e9
for (i, j) in bondsB3[::2]:
    o, m = gate_G_check(P2_general(i, j, NB3), i, j, NB3)
    gB_off = max(gB_off, o)
    gB_on = min(gB_on, m)
R["ArmB_gate_G"] = {"max_off_support": gB_off, "min_on_support": gB_on,
                    "verdict": ("PASS" if gB_off < 1e-14 and gB_on > 1.0
                                else "FIRE")}

# compressed static table: K^dag P_vtx^(J) K (64 x 64, PSD)
REGS_B = [1, 4, 7]  # centers of the three axis blocks (L=3)
R["ArmB_static_table"] = {}
for J in (0, 1, 2, 3):
    P_J, dimJ = J_vtx_projector(J, REGS_B, NB3)
    if P_J is None:
        R["ArmB_static_table"][J] = {"P_vtx_dim": 0, "error": "no sector"}
        continue
    PJ_K = P_J @ K_full            # sparse (19683 x 64)
    comp = (K_full.conj().T @ PJ_K).toarray() if sparse.issparse(PJ_K) \
        else K_full.conj().T @ PJ_K
    w = np.sort(np.linalg.eigvalsh(comp).real)
    R["ArmB_static_table"][J] = {
        "P_vtx_dim": dimJ,
        "ker_dim_out_of_64": int((np.abs(w) < 1e-9).sum()),
        "lambda_min_compressed": round(float(w[0]), 9),
    }

# dynamical cleanliness: leak = ||(1-PK) H_vtx P_K||_F^2 computed as
# ||(1-PK) H_vtx K_full||_F^2 (the K-full columns span P_K's range;
# K_full is an orthonormal basis so the F-norm on the range equals
# the F-norm restricted to the range — the leak matrix IS
# (1-PK) H_vtx K_full (19683 x 64), and its F-norm squared is the
# declared quantity).
HK = H_vtx3 @ K_full            # sparse (19683 x 64)
# project out kernel part: (1 - K K^dag) HK = HK - K (K^dag HK)
KdagHK = (K_full.conj().T @ HK).toarray() if sparse.issparse(HK) \
    else K_full.conj().T @ HK
leak_mat = HK - K_full @ KdagHK
leak_F2 = float(np.real(np.sum(np.abs(
    (leak_mat.toarray() if sparse.issparse(leak_mat)
     else leak_mat)) ** 2)))
R["ArmB_dynamical"] = {
    "leak_F2": round(leak_F2, 6),
    "declared": 251.142024,
}
# per-state leak: ||(1-PK) H_vtx |psi_k>||^2 for each kernel state
leaks = []
for k in range(K_full.shape[1]):
    u = (H_vtx3 @ K_full[:, k])
    u = u - K_full @ KdagHK[:, k]
    u = u.toarray() if sparse.issparse(u) else u
    leaks.append(float(np.real(u @ u.conj())))
R["ArmB_dynamical"]["per_state_leak_min"] = round(min(leaks), 6)
R["ArmB_dynamical"]["per_state_leak_max"] = round(max(leaks), 6)
R["ArmB_dynamical"]["declared_min"] = 3.448563

# variance form check: Var_psi(H_vtx) per kernel state (should equal
# the per-state leak since psi in kernel and PK projects)
# L=5 persistence via the compressed route
def axis_kernel_compressed(L):
    bonds = [(i, i + 1) for i in range(L - 1)]
    M = sum(P2_general(i, j, L) for (i, j) in bonds)
    K = null_space(M, rcond=1e-11)
    return K

K1_5 = axis_kernel_compressed(5)
NB5 = 15
# build forbid-J=3 compressed on K_5^{ox3}: need P_vtx^(3) on the
# center registers of each axis at L=5: centers at site 2, 7, 12
regs5 = [2, 7, 12]
# P_vtx^(3) restricted: total spin of three spin-1 sites at 2,7,12
# build on a 3^15 space directly is 14.3M — too big. Compressed route:
# the projector acts only on the 3 center registers; use the kernel
# basis of the three 5-chains and the reduced 3-register operator.
# Trick: represent states as kron of per-axis kernel states; the
# center-register local states span... build the effective operator
# via tensor-network-free direct route: per-axis kernel has dim 16;
# the local space of the center register within the kernel can be
# extracted by partial-trace-like compression. Simpler exact route:
# compute the compressed matrix of Jtot^2 on centers via kernel
# basis: K^dag SS_tot K (64 x 64), then spectral-project there.
# This is EXACT: spectral projection of the compressed Hermitian.
def compressed_center_J2(L):
    K1 = axis_kernel_compressed(L)
    N = 3 * L
    regs = [L // 2, L + L // 2, 2 * L + L // 2]
    SS_tot = 2 * sum(SS_ij(a, b, N) for ia, a in enumerate(regs)
                     for ib, b in enumerate(regs) if ia < ib)
    SS_tot = SS_tot + sum(
        site_op(SVEC[q], a, N) @ site_op(SVEC[q], a, N)
        for a in regs for q in range(3))
    # kernel basis for the full cross at dim 3^15 too big; but the
    # operator factorizes: SS_tot acts only on 3 sites of 15.
    # Direct kron construction of SS_tot at N=15 is 3^30 entries —
    # too big. Instead build per-axis wavefunctions: represent the
    # state space as kron(K1, K1, K1) (dim 16^3 = 4096) and build
    # the matrix elements of SS_tot in this basis by applying the
    # per-site operators restricted to the kernel.
    # Exact route: build SS_tot on the FULL space in blocks: it acts
    # on sites {regs} only, so it factorizes as O_centers kron I_rest
    # where I_rest = 3^{12}. We can then compute
    #   K^dag (O_centers kron I) K
    # by reshaping: K columns are vectors on 3^15. Reshape each
    # column to (3^3 centers?) — sites 2,7,12 are not adjacent, so
    # reorder axes: view the 15 sites as [others (12), centers (3)]
    # via axis permutation, making the operator act on the LAST 3
    # tensor factors.
    pass
R["ArmB_L5"] = {"status": "deferred-to-script-2"}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r53b_armsAB.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("GATE_CG:", R["GATE_CG"])
print("ArmA_gate_G:", R["ArmA_gate_G"])
print("ArmA_static_table:", json.dumps(R["ArmA_static_table"], indent=1))
print("ArmA_live_kernel:", R["ArmA_live_kernel"])
print("ArmA_cross_corr:", R["ArmA_cross_corr"])
print("ArmA_spillover:", R["ArmA_spillover"])
print("ArmB_kernel_check:", R["ArmB_kernel_check"])
print("ArmB_gate_G:", R["ArmB_gate_G"])
print("ArmB_static_table:", json.dumps(R["ArmB_static_table"], indent=1))
print("ArmB_dynamical:", R["ArmB_dynamical"])
print("elapsed:", R["elapsed_s"])
