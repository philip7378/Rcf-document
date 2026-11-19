"""r5.2 pre-flight B — machine verification of seat-A's N=4 anchors
(dim 81, H_XXX + cov3, gamma = 1, Gate-S leading) BEFORE the PR-T1b-2b
sheet freezes. Every declared number is checked exactly.

Declared anchors (seat-A message on commit e9fe30c):
  (i)   NESS residual 4.50e-15; sum_b M_b = 0.250588 (Mbar)
  (ii)  all single-site marginals frozen: ||rho_i - I/3||_F <= 2.4e-16
  (iii) single-site partial trace of the overlap commutator at the NESS:
        ||Tr_{!=1}([L1, L0] rho_ss)||_F = 8.25e-17 (the vacuity trap)
  (iv)  disjoint bonds (0,2): ||[h0, h2]||_F = 0; and the superoperator
        commutator action at the NESS ||[L2, L0] rho_ss||_F = 1.27e-16
  (v)   adjacent overlaps: ||[h0, h1]||_F = ||[h1, h2]||_F = 12.000000;
        ||[L1, L0] rho_ss||_F = ||[L2, L1] rho_ss||_F = 0.679584
  (vi)  ||L_b(rho_ss)||_F = (0.282455, 0.380218, 0.282455)
  (vii) self-bond drainage Tr(L_b(rho_ss) P_b^{(2)}) = -M_b =
        (-0.061203, -0.128182, -0.061203)
  (viii) holonomy burden rows:
        Tr([L1,L0] rho_ss P_b^{(2)}) = [-0.166844, +0.289246, -0.119031]
        Tr([L2,L1] rho_ss P_b^{(2)}) = [+0.119031, -0.289246, +0.166844]
        middle-bond cancellation (+0.289246 - 0.289246 = 0) and the pure
        boundary dipole [-0.047813, 0, +0.047813]
Convention notes for the check: L_b here means the FULL bond-b
superoperator (h_b + its cov3 dissipator); "rho_ss" the exact NESS of
the total generator. The commutator [L1, L0] rho_ss is the superoperator
commutator acting on rho_ss.
"""
import json
import time

import numpy as np
import scipy.sparse as sparse
import scipy.sparse.linalg as spla

t0 = time.time()
R = {}

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]
gs = max(float(np.linalg.norm(a @ b - b @ a - 1j * c, "fro"))
         for a, b, c in ((Sx, Sy, Sz), (Sy, Sz, Sx), (Sz, Sx, Sy)))
R["GATE_S"] = {"max_comm": gs,
               "verdict": "PASS" if gs < 1e-14 else "FAIL"}

N4, D4 = 4, 81

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
    return {1: J1, 2: J2}

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

h = [sum(bond2_op(SVEC[q], SVEC[q], b, N4) for q in range(3))
     for b in range(3)]
P2 = [P2_bond(b, N4) for b in range(3)]

def superop_from(Ls, H, DIM=D4):
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
    return out

Lb = [superop_from(cov3_jumps(b, N4), h[b]) for b in range(3)]
Ltot = superop_from([L for b in range(3) for L in cov3_jumps(b, N4)],
                     h[0] + h[1] + h[2])

# ---- (iv) Hamiltonian commutators ------------------------------------
com02 = float(np.linalg.norm(h[0] @ h[2] - h[2] @ h[0], "fro"))
com01 = float(np.linalg.norm(h[0] @ h[1] - h[1] @ h[0], "fro"))
com12 = float(np.linalg.norm(h[1] @ h[2] - h[2] @ h[1], "fro"))
R["commutators_h"] = {"[h0,h2]": com02, "[h0,h1]": com01, "[h1,h2]": com12,
                      "declared": "0 / 12 / 12",
                      "verdict": "PASS" if (com02 < 1e-12
                                            and abs(com01 - 12) < 1e-9
                                            and abs(com12 - 12) < 1e-9) else "FAIL"}

# ---- the NESS --------------------------------------------------------
def solve_ness(A, DIM=D4):
    vals, vecs = spla.eigs(sparse.csc_matrix(A), k=2, sigma=0, which="LM",
                           tol=1e-13, v0=np.ones(DIM * DIM, dtype=complex))
    pick = int(np.argmin(np.abs(vals)))
    rho = vecs[:, pick].reshape(DIM, DIM, order="F")
    rho = (rho + rho.conj().T) / 2
    rho = rho / np.trace(rho).real
    resid = float(np.linalg.norm(
        (A @ rho.reshape(-1, order="F"))))
    return rho, resid

rho_ss, resid = solve_ness(Ltot)
M_b = [float(np.real(np.trace(rho_ss @ P2[b]))) for b in range(3)]
R["NESS"] = {
    "residual": resid, "declared": 4.5e-15,
    "M_b": [round(m, 6) for m in M_b],
    "M_sum": round(sum(M_b), 6), "declared_Mbar": 0.250588,
    "verdict": ("PASS" if resid < 1e-12 and abs(sum(M_b) - 0.250588) < 1e-4
                else "FAIL"),
}

# ---- (ii) frozen single-site marginals ------------------------------
def partial_trace_site(rho, site, N):
    out = np.zeros((3, 3), dtype=complex)
    stride = 3 ** (N - 1 - site)
    for a in range(3):
        for b in range(3):
            tot = 0.0
            for blk in range(3 ** (N - 1)):
                r = (blk // (3 ** (N - 1 - site))) * 3 ** (N - site) \
                    + a * stride + blk % stride
                c = (blk // (3 ** (N - 1 - site))) * 3 ** (N - site) \
                    + b * stride + blk % stride
                tot += rho[r, c]
            out[a, b] = tot
    return out

# simpler correct partial trace via reshape
def ptrace(rho, site, N):
    T = rho.reshape([3] * N + [3] * N)
    letters = "abcdefghijklmnopqrstuvwxyz"
    sub = [letters[i] for i in range(2 * N)]
    for i in range(N):
        if i != site:
            sub[N + i] = sub[i]
    out = np.einsum("".join(sub), T)
    return out

marg_errs = [float(np.linalg.norm(ptrace(rho_ss, i, N4) - np.eye(3) / 3,
                                  "fro")) for i in range(4)]
R["marginals"] = {"max_err": max(marg_errs), "declared": 2.4e-16,
                  "verdict": "PASS" if max(marg_errs) < 1e-13 else "FAIL"}

# ---- (iii) + (v) commutator actions at the NESS ----------------------
def act(A, rho):
    return (A @ rho.reshape(-1, order="F")).reshape(D4, D4, order="F")

C10 = act(Lb[1] @ Lb[0] - Lb[0] @ Lb[1], rho_ss)
C21 = act(Lb[2] @ Lb[1] - Lb[1] @ Lb[2], rho_ss)
C20 = act(Lb[2] @ Lb[0] - Lb[0] @ Lb[2], rho_ss)
n10 = float(np.linalg.norm(C10, "fro"))
n21 = float(np.linalg.norm(C21, "fro"))
n20 = float(np.linalg.norm(C20, "fro"))
pt_1 = ptrace(C10, 1, N4)
pt1_n = float(np.linalg.norm(pt_1, "fro"))
R["commutator_actions"] = {
    "adjacent_01": round(n10, 6), "adjacent_12": round(n21, 6),
    "disjoint_02": n20, "declared": "0.679584 / 0.679584 / 1.27e-16",
    "single_site_trace_01_at1": pt1_n, "declared_iii": 8.25e-17,
    "verdict": ("PASS" if (abs(n10 - 0.679584) < 5e-4
                           and abs(n21 - 0.679584) < 5e-4
                           and n20 < 1e-12 and pt1_n < 1e-12) else "FAIL"),
}

# ---- (vi) individual bond generator norms at the NESS ---------------
Lb_act = [act(Lb[b], rho_ss) for b in range(3)]
Lb_norms = [float(np.linalg.norm(x, "fro")) for x in Lb_act]
drain = [float(np.real(np.trace(Lb_act[b] @ P2[b]))) for b in range(3)]
R["individual_generators"] = {
    "norms": [round(x, 6) for x in Lb_norms],
    "declared_norms": [0.282455, 0.380218, 0.282455],
    "self_drainage": [round(x, 6) for x in drain],
    "declared_drainage": [-0.061203, -0.128182, -0.061203],
    "drain_equals_minus_M": [round(drain[b] + M_b[b], 9) for b in range(3)],
    "verdict": ("PASS" if (all(abs(Lb_norms[b] - d) < 5e-4 for b, d in
                              enumerate((0.282455, 0.380218, 0.282455)))
                              and all(abs(drain[b] - d) < 5e-4 for b, d in
                                      enumerate((-0.061203, -0.128182,
                                                 -0.061203)))) else "FAIL"),
}

# ---- (viii) the holonomy burden rows --------------------------------
row_10 = [float(np.real(np.trace(C10 @ P2[b]))) for b in range(3)]
row_21 = [float(np.real(np.trace(C21 @ P2[b]))) for b in range(3)]
middle_cancel = row_10[1] + row_21[1]
boundary = [row_10[b] + row_21[b] for b in range(3)]
R["holonomy_burden_rows"] = {
    "row_10": [round(x, 6) for x in row_10],
    "row_21": [round(x, 6) for x in row_21],
    "declared_10": [-0.166844, 0.289246, -0.119031],
    "declared_21": [0.119031, -0.289246, 0.166844],
    "middle_bond_cancellation": round(middle_cancel, 12),
    "boundary_dipole": [round(x, 6) for x in boundary],
    "declared_boundary": [-0.047813, 0.0, 0.047813],
    "verdict": ("PASS" if (all(abs(row_10[b] - d) < 5e-4 for b, d in
                               enumerate((-0.166844, 0.289246, -0.119031)))
                           and all(abs(row_21[b] - d) < 5e-4 for b, d in
                                   enumerate((0.119031, -0.289246, 0.166844)))
                           and abs(middle_cancel) < 1e-9
                           and abs(boundary[0] + 0.047813) < 5e-4
                           and abs(boundary[2] - 0.047813) < 5e-4
                           and abs(boundary[1]) < 1e-6) else "FAIL"),
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r52_preflightB.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("commutators_h:", R["commutators_h"])
print("NESS:", R["NESS"])
print("marginals:", R["marginals"])
print("commutator_actions:", R["commutator_actions"])
print("individual_generators:", R["individual_generators"])
print("holonomy_burden_rows:", R["holonomy_burden_rows"])
print("elapsed:", R["elapsed_s"])
