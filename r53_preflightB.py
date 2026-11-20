"""r5.3 pre-flight B — machine-verification of No-Go VIII (The Spin-1
Graph-Valence Obstruction, claimed E4).

Evaluate M_G = sum_{(i,j) in E(G)} P_ij^{(2)} on spin-1 sites
(C^3)^{otimes |V|} for each graph; check dim ker and lambda_min:

  1D open chain N=4 (z=2)         : ker 4,  lambda_min 0            (FF)
  Triangle K3 (z=2)               : ker 1,  lambda_min 0            (FF)
  Square C4 (z=2)                 : ker 1,  lambda_min 0            (FF)
  Star K_{1,3} (z=3)              : ker 0,  lambda_min 0.152873 (5x) (EMPTY)
  Star K_{1,4} (z=4)              : ker 0,  lambda_min 0.313859 (5x) (EMPTY)
  Tetrahedron K4 (z=3, 6 edges)   : ker 0,  lambda_min 5/3 exact     (EMPTY)

Structural claim: a single spin-1 site (Sym^2(C^2) = C^3) carries only
2 virtual spin-1/2 valence legs; the moment one vertex has z = 3
(the bare minimum to leave 1D), the frustration-free kernel collapses
to {0}.
Also machine-check the valence mechanism itself: the on-site pairing
argument — the kernel condition requires each site's two neighbors to
pair their virtual legs into singlets; a z=3 site cannot satisfy
3 legs with 2-valence spin-1/2 pairs. This is verified indirectly via
the lambda_min table (kernel empty for all z>=3 graphs, including the
minimal ones), plus one extra witness: the complete graph K5 (z=4,
5 sites) also empty.
"""
import json
import time

import numpy as np

t0 = time.time()
R = {}

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]
gs = max(float(np.linalg.norm(a @ b - b @ a - 1j * c, "fro"))
         for a, b, c in ((Sx, Sy, Sz), (Sy, Sz, Sx), (Sz, Sx, Sy)))
R["GATE_S"] = {"max_comm": gs, "verdict": "PASS" if gs < 1e-14 else "FAIL"}

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
    return {2: J2}

CG = cg_pair_states()
P_PAIR = sum(np.outer(v, v.conj()) for v in CG[2])

def edge_projector(i, j, N):
    i, j = int(i), int(j)
    if j < i:
        i, j = j, i   # P_ij = P_ji: all J=2 pair states are swap-symmetric
    left = np.eye(3 ** i, dtype=complex)
    mid = np.eye(3 ** (j - i - 1), dtype=complex)
    right = np.eye(3 ** (N - j - 1), dtype=complex)
    return np.kron(np.kron(np.kron(left, P_PAIR), mid), right)

def M_G(edges, N):
    M = np.zeros((3 ** N, 3 ** N), dtype=complex)
    for (i, j) in edges:
        M = M + edge_projector(int(i), int(j), int(N))
    return M

def analyze(name, edges, N, declared_ker, declared_lmin):
    M = M_G(edges, N)
    w = np.linalg.eigvalsh(M).real
    w = np.sort(w)
    ker = int((np.abs(w) < 1e-9).sum())
    lmin = float(w[0]) if ker == 0 else 0.0
    # multiplicity of the lowest nonzero eigenvalue
    nz = w[np.abs(w) > 1e-9]
    mult = int((np.abs(nz - nz[0]) < 1e-8).sum()) if len(nz) else 0
    ok_ker = (ker == declared_ker)
    ok_lmin = (ker > 0 or abs(lmin - declared_lmin) < 5e-6)
    R[name] = {
        "vertices": N, "edges": len(edges),
        "max_degree": max([sum(1 for e in edges if v in e)
                            for v in range(N)]),
        "ker_dim": ker, "declared_ker": declared_ker,
        "lambda_min": round(lmin, 6), "declared_lmin": declared_lmin,
        "lowest_nonzero_mult": mult,
        "verdict": "PASS" if (ok_ker and ok_lmin) else "FAIL",
    }
    return R[name]

analyze("chain_N4", [(0, 1), (1, 2), (2, 3)], 4, 4, 0.0)
analyze("triangle_K3", [(0, 1), (1, 2), (2, 0)], 3, 1, 0.0)
analyze("square_C4", [(0, 1), (1, 2), (2, 3), (3, 0)], 4, 1, 0.0)
analyze("star_K13", [(0, 1), (0, 2), (0, 3)], 4, 0, 0.152873)
analyze("star_K14", [(0, 1), (0, 2), (0, 3), (0, 4)], 5, 0, 0.313859)
analyze("tetrahedron_K4", [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)],
        4, 0, 5 / 3)
analyze("complete_K5", [(i, j) for i in range(5) for j in range(i + 1, 5)],
        5, 0, None)

# K5's declared lmin is None (not declared by the seat): report only.
R["complete_K5"]["declared_lmin"] = "not declared (extra witness)"
R["complete_K5"]["verdict"] = "REPORT-ONLY"

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r53_preflightB.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

for k in ("GATE_S", "chain_N4", "triangle_K3", "square_C4", "star_K13",
          "star_K14", "tetrahedron_K4", "complete_K5"):
    print(k, "->", json.dumps(R[k]))
print("elapsed:", R["elapsed_s"])
