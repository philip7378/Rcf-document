"""r8.5 — PRE-FLIGHT VERIFICATION, CONSOLIDATED (r85_preflight.py).

Replaces the first draft (which was OOM-killed building dense 3^8
operators — the memory lesson re-registered: at N=8 use the sparse
product-operator route, each SS(i,j) has only 3*3^N nonzeros).

WHAT IS REPRODUCED EXACTLY (machine, this file):
  CELL A (C8 ring of 8 P2 bonds, N=8, sparse eigsh):
    - dim 6561, kernel dim 1, gap 0.349849 — EXACT match to the
      auditor's claims (ker=1, gap 0.349849).
    - <Jx^2> = 0 to machine zero: the state is a J=0 singlet.
  TRAP-2 (the sqrt(2) tautology) — CONFIRMED TWO INDEPENDENT WAYS:
    (i) algebraically from the auditor's OWN published triple
        (G00=0.443632, G01=-0.199878, G02=-0.043876): the sum rule
        G00 + 2G01 + G02 holds to 2.8e-17 and the staggered ratio
        sqrt((G00-G02)/(G00+G01)) = 1.414213562 EXACTLY = sqrt(2);
    (ii) structurally: the identity G00 - G02 = 2(G00 + G01) follows
        from the sum rule alone, so the ratio sqrt(2) is pinned for
        EVERY C4-symmetric J=0 singlet regardless of dynamics.
  TRAP-1 (Néel inversion) — CONFIRMED from the auditor's numbers:
    G01 < 0 (adjacent corners anti-aligned); unstaggered chord
    adj 1.1345 > chord diag 0.9874 — adjacency INVERTED vs diagonal.
    Every bipartite chord comparison must declare (-1)^(x+y)
    staggering. (My ring state: corr(0,2) = +0.1499 vs corr(0,4) =
    +0.0329 with corr(0,1) = -0.4444 — the same anti-alternation.)

WHAT IS HONESTLY NOT REPRODUCED (construction-level divergence,
recorded per the r5.3a root-cause rule):
  The auditor's specific |c_adj|/|c_diag| values (open 0.444444/
  0.049375; closed 0.450549/0.098901, 2.003x amplification) come
  from THEIR pre-flight script's composite-vertex construction
  (4 intact external edges + 4 intra-vertex bonds + J=3-forbidden
  corners), which cannot be fully reconstructed from prose. My plain
  C8 ring gives: open (0,1) 0.444389 / (0,3) 0.048368 / (0,4)
  0.013399; closed (0,1) 0.444851 / (0,3) 0.054845 / (0,4) 0.032907
  (2.456x amplification at the true diagonal (0,4), defect drop
  -0.896 vs their -0.667). QUALITATIVE AGREEMENT, exact-value
  divergence. DISPOSITION: the PR-LAT-1 frozen sheet defines the
  cells PRECISELY (sites, bonds, forbidden sectors, measured pairs)
  so its executor is unambiguous; the auditor's pre-flight stands as
  the design input, this ring reproduction as the certified seed.
  No claim from either number-set enters the manuscript without the
  construction named.

CELL B (2-vertex dumbbell, N=6): deferred to the PR-LAT-1 executor
  (same sparse route; dim 729 trivially feasible dense — the r84
  machinery already handles it).
"""
import json
import time

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

t0 = time.time()
R = {}

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)

gs = max(float(np.linalg.norm(a @ b - b @ a - 1j * c))
         for a, b, c in ((Sx, Sy, Sz), (Sy, Sz, Sx), (Sz, Sx, Sy)))
R["GATE_S"] = {"max_comm": gs, "verdict": "PASS" if gs < 1e-14 else "FAIL"}

def SS_sparse(i, j, N):
    out = None
    for q, Sq in ((0, Sx), (1, Sy), (2, Sz)):
        A = sp.csr_matrix(np.array([[1.0 + 0j]]))
        for k in range(N):
            m = Sq if k in (i, j) else np.eye(3)
            A = sp.kron(A, sp.csr_matrix(m), format="csr")
        out = A if out is None else out + A
    return out.tocsr()

def P2_sparse(i, j, N):
    S = SS_sparse(i, j, N)
    I = sp.identity(3 ** N, dtype=complex, format="csr")
    return ((S @ S + 3 * S + 2 * I) / 6.0).tocsr()

N = 8
M_closed = sum((P2_sparse(i, (i + 1) % N, N) for i in range(N)),
               sp.csr_matrix((3 ** N, 3 ** N), dtype=complex)).real
M_open = sum((P2_sparse(i, i + 1, N) for i in range(7)),
             sp.csr_matrix((3 ** N, 3 ** N), dtype=complex)).real

def kstate(M):
    val, vec = eigsh(M, k=3, which="SA", maxiter=30000)
    x = np.asarray(vec)[:, 0].ravel().real
    return x / np.linalg.norm(x), np.asarray(val).tolist()

vc, evals_c = kstate(M_closed)
vo, evals_o = kstate(M_open)

R["cell_A_ring"] = {
    "construction": "C8 ring, 8 P2 bonds (closed) / 7 (open control), "
                    "sparse product-operator route (memory lesson: "
                    "dense 3^8 OOM-killed; each SS(i,j) has 3*3^N nnz)",
    "dim": 3 ** N,
    "closed": {"ker_dim_at_least": int(np.sum(np.array(evals_c) < 1e-9)),
               "gap": round(float(np.sort(np.array(evals_c))[1]), 9),
               "evals": [round(float(e), 9) for e in evals_c]},
    "open": {"evals": [round(float(e), 9) for e in evals_o]},
    "claims_reproduced": {"dim": 6561, "ker": 1, "gap": 0.349849},
    "gap_match": bool(abs(np.sort(np.array(evals_c))[1] - 0.349849) < 1e-4),
}

# J=0 singlet check on the closed state:
Jx = None
for i in range(N):
    A = sp.csr_matrix(np.array([[1.0 + 0j]]))
    for k in range(N):
        m = Sx if k == i else np.eye(3)
        A = sp.kron(A, sp.csr_matrix(m), format="csr")
    Jx = A if Jx is None else Jx + A
Jx = Jx.real
R["cell_A_ring"]["J0_singlet"] = {
    "Jx2": round(float(vc @ (Jx @ (Jx @ vc))), 12),
    "verdict": "PASS (J=0 singlet)" if abs(float(vc @ (Jx @ (Jx @ vc)))) < 1e-10 else "CHECK",
}

def Sz_at(i, n):
    A = sp.csr_matrix(np.array([[1.0 + 0j]]))
    for k in range(n):
        m = Sz if k == i else np.eye(3)
        A = sp.kron(A, sp.csr_matrix(m), format="csr")
    return A.tocsr().real

Szs = [Sz_at(i, N) for i in range(N)]
def corr(v, i, j):
    return float(v @ (Szs[i] @ (Szs[j] @ v)))

R["cell_A_ring"]["correlations"] = {
    "open": {"(0,1)": round(corr(vo, 0, 1), 9), "(0,2)": round(corr(vo, 0, 2), 9),
             "(0,3)": round(corr(vo, 0, 3), 9), "(0,4)": round(corr(vo, 0, 4), 9)},
    "closed": {"(0,1)": round(corr(vc, 0, 1), 9), "(0,2)": round(corr(vc, 0, 2), 9),
               "(0,3)": round(corr(vc, 0, 3), 9), "(0,4)": round(corr(vc, 0, 4), 9)},
    "diag_amplification_(0,4)": round(abs(corr(vc, 0, 4) / corr(vo, 0, 4)), 6),
    "defect_drop_(0,4)": round(float(
        (-np.log(abs(corr(vc, 0, 4))) - 2 * (-np.log(abs(corr(vc, 0, 1)))))
        - (-np.log(abs(corr(vo, 0, 4))) - 2 * (-np.log(abs(corr(vo, 0, 1)))))), 9),
    "auditor_values": {"open": [0.444444, 0.049375],
                       "closed": [0.450549, 0.098901],
                       "amplification": 2.003},
    "divergence_note": "auditor's composite-vertex construction not "
                       "reconstructible from prose; qualitative "
                       "agreement (two-path amplification ~2-2.5x, "
                       "defect drop ~ -ln2), exact values differ; "
                       "sheet must define cells precisely",
}

# ---- Trap-2 tautology (algebraic, from the auditor's own triple) --
G00, G01, G02 = 0.443632, -0.199878, -0.043876
R["trap2_sqrt2_tautology"] = {
    "auditor_triple": [G00, G01, G02],
    "sum_rule_G00_plus_2G01_plus_G02": round(G00 + 2 * G01 + G02, 15),
    "sum_rule_holds": bool(abs(G00 + 2 * G01 + G02) < 1e-12),
    "staggered_ratio": round(float(np.sqrt((G00 - G02) / (G00 + G01))), 9),
    "sqrt2": round(float(np.sqrt(2)), 9),
    "identity": "G00 - G02 = 2(G00 + G01) follows from the sum rule "
                "alone -> ratio = sqrt(2) for EVERY C4-symmetric J=0 "
                "singlet, regardless of dynamics",
    "verdict": ("CONFIRMED ALGEBRAICALLY AND STRUCTURALLY: the ratio "
                "carries NO dynamical information on a single C4 ring; "
                "EXCLUDED as evidence in PR-LAT-1 (frozen-sheet guard)"),
}

# ---- Trap-1 Néel inversion (from the auditor's triple + my ring) ----
R["trap1_neel_inversion"] = {
    "auditor_unstaggered_chord_adj": round(float(np.sqrt(2 * (G00 - G01))), 6),
    "auditor_unstaggered_chord_diag": round(float(np.sqrt(2 * (G00 - G02))), 6),
    "inversion_confirmed": bool(np.sqrt(2 * (G00 - G02)) < np.sqrt(2 * (G00 - G01))),
    "my_ring_same_pattern": {"corr(0,1)": round(corr(vc, 0, 1), 9),
                             "corr(0,2)": round(corr(vc, 0, 2), 9),
                             "corr(0,4)": round(corr(vc, 0, 4), 9),
                             "note": "adjacent anti-aligned (-0.4449), "
                                     "next-nearest positive: the same "
                                     "bipartite alternation"},
    "verdict": ("CONFIRMED: unstaggered chord INVERTS adjacency vs "
                "diagonal on bipartite antiferromagnetic lattices; "
                "(-1)^(x+y) Néel staggering DECLARED mandatory in "
                "PR-LAT-1's frozen sheet"),
}

R["elapsed_s"] = round(time.time() - t0, 2)
json.dump(R, open("/home/z/my-project/scripts/r85_preflight.json", "w"),
          indent=1, default=float)
A = R["cell_A_ring"]
print("ker/gap:", A["closed"]["ker_dim_at_least"], A["closed"]["gap"],
      "| gap match:", A["gap_match"], "| J0:", A["J0_singlet"]["verdict"])
print("corrs closed:", A["correlations"]["closed"])
print("amplification (0,4):", A["correlations"]["diag_amplification_(0,4)"],
      "| defect drop:", A["correlations"]["defect_drop_(0,4)"])
print("trap2 sum rule:", R["trap2_sqrt2_tautology"]["sum_rule_G00_plus_2G01_plus_G02"],
      "| ratio:", R["trap2_sqrt2_tautology"]["staggered_ratio"])
print("trap1 inversion:", R["trap1_neel_inversion"]["inversion_confirmed"])
