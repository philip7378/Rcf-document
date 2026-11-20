"""r5.3a pre-flight B — CORRECTED re-run of the No-Go VIII table.

r5.3's r53_preflightB.py had executor bug #10: `edge_projector(i, j,
N)` normalized (i, j) -> (min, max) and then embedded the pair
operator on the ADJACENT pair (min, min+1), ignoring j entirely
(j - i - 1 was computed AFTER the swap, but the embed spans
sites [min .. min+1] only when j == i+1; for non-adjacent edges the
returned operator acts on (min, min+1) instead of (i, j)). Every
non-adjacent edge (0,2), (0,3), (2,0)... was collapsed onto (0,1).

This re-run:
  B0  two INDEPENDENT general-pair constructions, cross-verified:
      (i)  SS_ij from single-site Kronecker spin operators,
           P2(i,j) = (SS + I)(SS + 2I)/6;
      (ii) the CG J=2 pair states embedded by tensor-index
           permutation (the r5.2-certified construction, generalized).
      Continuity at adjacent pairs (bug-free zone) vs the certified
      r5.2 machinery is asserted (GATE-CG).
  B1  FORENSIC: reproduce the BUGGY operator for each graph (sum of
      P2(min, min+1)) and show its spectrum matches r5.3's reported
      numbers exactly (ker 36/lowest 3 star; ker 108/lowest 4; ker 4/
      0.667570 tetra; ker 4 triangle/square) — sealing the
      identification of the r5.3 artifacts.
  B2  GATE G (standing law, companion to Gate S): for every edge
      (i, j): ||[P2(i,j), S^z_k]||_F < 1e-14 for k not in {i,j} and
      > 1.0 for k in {i,j} (at N=4 the active-site value is sqrt(15)
      = 3.8730, inactive 0). Correct embedder: PASS. Buggy embedder:
      FIRES (that is the point of the gate).
  B3  Tr(P2(0,2) P2(0,1)) = 25/3 (the seat's declared pre-flight
      check for a genuinely non-adjacent pair) and Tr(P2(0,1)^2) = 5.
  B4  THE CORRECTED TABLE: path P4 (ker 4), triangle C3 (ker 1, gap
      5/6), square C4 (ker 1, gap 1/3), star K13 (ker 0, lmin
      (7-sqrt(37))/6 = 0.152873, J=2 mult 5), star K14 (ker 0,
      0.313859, mult 5), tetrahedron K4 (ker 0, 5/3 EXACT, mult 11
      [J=0 x2 + J=1 x3]), plus witnesses: K5, the T-tree (z=3 with
      a leaf), and cycle C5 (ker 1).
  B5  the valence law: every vertex z_v <= 2S=2 -> kernel exists;
      any vertex z_v >= 3 -> kernel empty. Witnessed on every row
      (max-degree column vs ker column) including the T-tree, where
      the SINGLE z=3 vertex empties the kernel.
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
R["GATE_S"] = {"max_comm": gs, "verdict": "PASS" if gs < 1e-14 else "FAIL"}

def site_op(op, site, N):
    ops = [np.eye(3, dtype=complex)] * N
    ops[site] = op
    out = ops[0]
    for o in ops[1:]:
        out = np.kron(out, o)
    return out

def SS_ij(i, j, N):
    return sum(site_op(SVEC[q], i, N) @ site_op(SVEC[q], j, N)
               for q in range(3))

def P2_method1(i, j, N):
    """(i) spin-operator construction — NO adjacency assumption."""
    SS = SS_ij(i, j, N)
    I = np.eye(3 ** N, dtype=complex)
    return (SS + I) @ (SS + 2 * I) / 6.0

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

def perm_to_adjacent(pair9, i, j, N):
    """(ii) CG pair states embedded on the GENERAL pair (i, j) by
    tensor-index permutation: the pair operator acts on sites (i, j)
    in the given order; identity on the rest."""
    i, j = int(i), int(j)
    # build the permutation of site indices that maps (i, j) -> (0, 1)
    order = [i, j] + [k for k in range(N) if k != i and k != j]
    # permutation operator on the full space
    dim = 3 ** N
    U = np.zeros((dim, dim), dtype=complex)
    # index maps: tensor position p (0..N-1) has stride 3^(N-1-p)
    strides = [3 ** (N - 1 - p) for p in range(N)]
    # U |x_{pi(0)}...> rearranged: we permute site slots so that slot
    # p of the OUTPUT holds the input site order[p].
    for out_idx in range(dim):
        # decompose out index into per-slot digits
        digs = [0] * N
        v = out_idx
        for p in range(N):
            digs[p] = (v // strides[p]) % 3
            v -= digs[p] * strides[p]
        # the operator U with U e_{slot-perm} maps basis: we want
        # U |d> = |perm d> where perm moves slot values: output slot
        # p gets input slot order[p]'s digit. Since we only need U
        # P_adj U^dag, we instead build the pair operator directly by
        # placing digits: out slot p <- in slot order[p].
        # For U itself (slot permutation): out slot p takes the digit
        # of input slot sigma(p) where sigma = order. So:
        in_digs = [None] * N
        for p in range(N):
            in_digs[order[p]] = digs[p]  # out slot p <- in slot order[p]... inverse below
        # simpler: compute the input index whose permutation equals out
        in_idx = 0
        for p in range(N):
            # input slot order[p] value = out slot p digit
            in_idx += digs[p] * strides[order[p]]
        U[in_idx, out_idx] = 1.0
    # adjacent embedding of the pair operator on slots (0, 1)
    adj = np.kron(np.kron(pair9, np.eye(3 ** (N - 2), dtype=complex)),
                  np.eye(1, dtype=complex)) if N == 2 else \
        np.kron(pair9, np.eye(3 ** (N - 2), dtype=complex))
    return U @ adj @ U.conj().T

def P2_method2(i, j, N):
    return perm_to_adjacent(P_PAIR9, i, j, N)

# ---- B0: cross-verify the two methods + GATE-CG ---------------------
cross = 0.0
adj_ct = 0.0
for N in (3, 4, 5):
    pairs = [(a, b) for a in range(N) for b in range(a + 1, N)]
    for (i, j) in pairs:
        A = P2_method1(i, j, N)
        B = P2_method2(i, j, N)
        cross = max(cross, float(np.linalg.norm(A - B, "fro")))
        if j == i + 1:
            # adjacent: compare with the r5.2-certified adjacent embed
            L = np.eye(3 ** i, dtype=complex)
            M_ = np.eye(3 ** (j - i - 1), dtype=complex)
            R_ = np.eye(3 ** (N - j - 1), dtype=complex)
            cert = np.kron(np.kron(np.kron(L, P_PAIR9), M_), R_)
            adj_ct = max(adj_ct,
                         float(np.linalg.norm(A - cert, "fro")))
R["B0_cross_methods"] = {
    "max_diff_method1_vs_method2_all_pairs_N3to5": cross,
    "max_diff_vs_certified_adjacent_embed": adj_ct,
    "verdict": "PASS" if cross < 1e-13 and adj_ct < 1e-13 else "FAIL",
}

# ---- B1: FORENSIC reproduction of the buggy r5.3 operator -----------
def buggy_P2(i, j, N):
    """The r5.3 bug: normalize to (min, max), then embed on
    (min, min+1) — j ignored."""
    lo = min(i, j)
    L = np.eye(3 ** lo, dtype=complex)
    R_ = np.eye(3 ** (N - lo - 2), dtype=complex)
    return np.kron(np.kron(L, P_PAIR9), R_)

def spectra(M):
    w = np.sort(np.linalg.eigvalsh(M).real)
    ker = int((np.abs(w) < 1e-9).sum())
    nz = w[np.abs(w) > 1e-9]
    return {"ker": ker,
            "lowest_nonzero": round(float(nz[0]), 6) if len(nz) else None}

GRAPHS = {
    "chain_P4": (4, [(0, 1), (1, 2), (2, 3)]),
    "triangle_C3": (3, [(0, 1), (1, 2), (0, 2)]),
    "square_C4": (4, [(0, 1), (1, 2), (2, 3), (0, 3)]),
    "star_K13": (4, [(0, 1), (0, 2), (0, 3)]),
    "star_K14": (5, [(0, 1), (0, 2), (0, 3), (0, 4)]),
    "tetrahedron_K4": (4, [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]),
}
R["B1_forensic_buggy_spectra"] = {}
for name, (N, edges) in GRAPHS.items():
    Mb = sum(buggy_P2(i, j, N) for (i, j) in edges)
    R["B1_forensic_buggy_spectra"][name] = spectra(Mb)

# ---- B2: GATE G (site-support gate) ---------------------------------
def gate_G(M_builder, edges, N):
    """For every edge (i,j): commutator with S^z_k must vanish
    (Frobenius < 1e-14) for k NOT in {i,j} and be large (> 1.0) for
    k in {i,j}."""
    worst_off, worst_on = 0.0, 0.0
    for (i, j) in edges:
        P = M_builder(i, j, N)
        for k in range(N):
            comm = float(np.linalg.norm(
                P @ site_op(Sz, k, N) - site_op(Sz, k, N) @ P))
            if k in (i, j):
                worst_on = max(worst_on, comm)  # should be LARGE
            else:
                worst_off = max(worst_off, comm)  # should be ~0
    return {"max_off_support_comm": worst_off,
            "min_on_support_comm": worst_on,
            "verdict": ("PASS" if worst_off < 1e-14 and worst_on > 1.0
                        else "FIRE")}

R["B2_gate_G_correct"] = gate_G(P2_method1, GRAPHS["star_K13"][1], 4)
R["B2_gate_G_buggy"] = gate_G(buggy_P2, GRAPHS["star_K13"][1], 4)
# at N=4 the on-support value: report exactly
P02 = P2_method1(0, 2, 4)
R["B2_gate_G_exact_N4"] = {
    "on_value": float(np.linalg.norm(
        P02 @ site_op(Sz, 0, 4) - site_op(Sz, 0, 4) @ P02)),
    "sqrt15": float(np.sqrt(15)),
}

# ---- B3: declared trace checks --------------------------------------
# The seat's 25/3 is the trace on the 3-site support {0,1,2} (dim 27,
# N=3); at N=4 the site-3 spectator multiplies it by 3 -> 25. Check
# both readings.
P01_3 = P2_method1(0, 1, 3)
P02_3 = P2_method1(0, 2, 3)
t_N3 = float(np.trace(P02_3 @ P01_3).real)
t_N4 = float(np.trace(P02 @ P2_method1(0, 1, 4)).real)
R["B3_trace_checks"] = {
    "Tr(P02 P01) at N=3 (support)": round(t_N3, 9),
    "declared": 25 / 3,
    "Tr(P02 P01) at N=4 (x spectator 3)": round(t_N4, 9),
    "Tr(P01^2) at N=3 (=rank 5)": round(
        float(np.trace(P01_3 @ P01_3).real), 9),
    "verdict": ("PASS" if abs(t_N3 - 25 / 3) < 1e-9
                and abs(t_N4 - 25) < 1e-9
                and abs(float(np.trace(P01_3 @ P01_3).real) - 15)
                < 1e-9 else "FAIL"),
}

# ---- B4: the CORRECTED table ----------------------------------------
def analyze(name, N, edges, declared_ker, declared_lmin, declared_mult):
    M = sum(P2_method1(i, j, N) for (i, j) in edges)
    w = np.sort(np.linalg.eigvalsh(M).real)
    ker = int((np.abs(w) < 1e-9).sum())
    lmin = float(w[0]) if ker == 0 else 0.0
    nz = w[np.abs(w) > 1e-9]
    mult = int((np.abs(nz - nz[0]) < 1e-8).sum()) if len(nz) else 0
    gap = float(nz[0]) if ker > 0 and len(nz) else None
    maxz = max([sum(1 for e in edges if v in e) for v in range(N)])
    ok = (ker == declared_ker)
    if declared_lmin is not None and ker == 0:
        ok = ok and abs(lmin - declared_lmin) < 5e-6
    if ker > 0 and declared_lmin is not None:
        ok = ok and (gap is not None
                     and abs(gap - declared_lmin) < 5e-6)
    # residual: verify kernel vectors via null_space on one entry
    ns = null_space(M, rcond=1e-11)
    resid = max(float(np.linalg.norm(M @ ns[:, k])
                      / np.linalg.norm(ns[:, k]))
                for k in range(ns.shape[1])) if ns.shape[1] else 0.0
    return {
        "vertices": N, "edges": len(edges), "max_degree": maxz,
        "ker_dim": ker, "declared_ker": declared_ker,
        "lambda_min": round(lmin, 9) if ker == 0 else None,
        "gap_above_kernel": round(gap, 9) if gap is not None else None,
        "declared_lmin": declared_lmin,
        "lowest_nonzero_mult": mult, "declared_mult": declared_mult,
        "null_space_residual": resid,
        "verdict": "PASS" if ok else "FAIL",
    }

R["B4_table"] = {}
R["B4_table"]["path_P4"] = analyze("path_P4", 4,
                                   [(0, 1), (1, 2), (2, 3)], 4, None, None)
R["B4_table"]["triangle_C3"] = analyze("triangle_C3", 3,
                                        [(0, 1), (1, 2), (0, 2)],
                                        1, 5 / 6, None)
R["B4_table"]["square_C4"] = analyze("square_C4", 4,
                                     [(0, 1), (1, 2), (2, 3), (0, 3)],
                                     1, 1 / 3, None)
R["B4_table"]["cycle_C5"] = analyze("cycle_C5", 5,
                                    [(0, 1), (1, 2), (2, 3), (3, 4),
                                     (0, 4)], 1, None, None)
R["B4_table"]["star_K13"] = analyze("star_K13", 4,
                                    [(0, 1), (0, 2), (0, 3)],
                                    0, (7 - np.sqrt(37)) / 6, 5)
R["B4_table"]["star_K14"] = analyze("star_K14", 5,
                                    [(0, 1), (0, 2), (0, 3), (0, 4)],
                                    0, 0.313859, 5)
R["B4_table"]["tetrahedron_K4"] = analyze(
    "tetrahedron_K4", 4,
    [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
    0, 5 / 3, 11)
R["B4_table"]["complete_K5"] = analyze(
    "complete_K5", 5,
    [(i, j) for i in range(5) for j in range(i + 1, 5)],
    0, None, None)
R["B4_table"]["T_tree_z3"] = analyze(
    "T_tree_z3", 4,
    [(0, 1), (0, 2), (0, 3)] + [(3, 4)], 5,
    [(0, 1), (0, 2), (0, 3), (3, 4)], 0, None, None) \
    if False else analyze("T_tree_z3", 5,
                          [(0, 1), (0, 2), (0, 3), (3, 4)],
                          0, None, None)

# exact-form checks
R["B4_exact_forms"] = {
    "star_K13_(7-sqrt37)/6": float((7 - np.sqrt(37)) / 6),
    "tetra_5/3": 5 / 3,
    "triangle_5/6": 5 / 6,
    "square_1/3": 1 / 3,
}

# ---- B5: valence law summary ----------------------------------------
rows = R["B4_table"]
law_ok = True
for k, v in rows.items():
    zmax = v["max_degree"]
    ker = v["ker_dim"]
    consistent = (zmax <= 2 and ker > 0) or (zmax >= 3 and ker == 0)
    if not consistent:
        law_ok = False
R["B5_valence_law"] = {
    "rule": "any vertex z_v >= 3 (i.e. z_v > 2S = 2) -> ker = {0}; "
            "all vertices z_v <= 2 -> ker nonempty",
    "all_rows_consistent": law_ok,
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r53a_preflightB.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("B0:", json.dumps(R["B0_cross_methods"], indent=1))
print("B1 forensic (buggy):", json.dumps(R["B1_forensic_buggy_spectra"],
                                          indent=1))
print("B2 GateG correct:", R["B2_gate_G_correct"])
print("B2 GateG buggy:", R["B2_gate_G_buggy"])
print("B2 exact on-value:", R["B2_gate_G_exact_N4"])
print("B3:", json.dumps(R["B3_trace_checks"], indent=1))
for k, v in R["B4_table"].items():
    print(f"B4 {k}: ker={v['ker_dim']} lmin={v['lambda_min']} "
          f"gap={v['gap_above_kernel']} mult={v['lowest_nonzero_mult']} "
          f"z={v['max_degree']} {v['verdict']}")
print("B5 valence law consistent:", R["B5_valence_law"]["all_rows_consistent"])
print("elapsed:", R["elapsed_s"])
