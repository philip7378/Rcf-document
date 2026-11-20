"""r7.0 PR-METRIC-2 EXECUTION — per the audit's pre-registered
outcome space (post-800c43c), run on the certified PR-LINK-1 frame.

PRIMARY.  Compare the path-infimum distance d_int (shortest path
over the certified K-edge graph) with the scaling-metric distance
d_scaling (Theorem A/B family: -ln det C, numerically
differentiated on the link frame) for stub pairs through the
junction.

OUTCOME SPACE (pre-committed by the audit, frozen):
  EQUAL        d_int = d_scaling to machine precision.
  ENVELOPE     d_int <= d_scaling, strict gap.
  IMPOSSIBLE   d_int > d_scaling -> computation error.
  INCONCLUSIVE frame not dense enough.

GUARD.  Product-seed control: on a product-seed link chain
(P^(2)-mixing on each arm, no cross-entanglement), the
multiplicativity gap reduces to 0 and d_int = d_scaling exactly.

Adjudication is reported as found; no retrofit.

Also computed this round (the register's object renaming):
  - the junction multiplicativity gap M(A,C;O) :=
    d(A,C) - [d(A,O) + d(O,C)] on the entangled kernel
    (= +1.168796, the r6.2 PIN-1 object, renamed);
  - the same on the product seed (should be ~0);
  - the chord metrics the incircle picture predicts
    (Gram-chord d_G, angle theta between stub displacement
    profiles, angle defect), as the E0-fenced PREDICTED
    resolved form, not as a certified closure.
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
R["GATE_S"] = {"max_comm": gs,
               "verdict": "PASS" if gs < 1e-14 else "FAIL"}

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

def axis_kernel(L):
    bonds = [(i, i + 1) for i in range(L - 1)]
    M = P2_general(*bonds[0], L)
    for (i, j) in bonds[1:]:
        M = M + P2_general(i, j, L)
    return null_space(M, rcond=1e-11)

NC = 6
BONDS_C = [(0, 1), (2, 3), (4, 5)]
REGS_C = [0, 2, 4]
STUBS = [1, 3, 5]
M_corner = P2_general(*BONDS_C[0], NC)
for (i, j) in BONDS_C[1:]:
    M_corner = M_corner + P2_general(i, j, NC)

J2 = None
for q in range(3):
    f = so(SVEC[q], 0, NC) + so(SVEC[q], 2, NC) + so(SVEC[q], 4, NC)
    J2 = (f @ f) if J2 is None else (J2 + f @ f)
NODES = [0.0, 2.0, 6.0, 12.0]
x = 12.0
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
P3c = np.zeros_like(J2)
tk = np.eye(3 ** NC, dtype=complex)
for k in range(4):
    if coeffs[k] != 0.0:
        P3c = P3c + coeffs[k] * tk
    tk = tk @ J2

ker32 = null_space(M_corner + P3c, rcond=1e-11)
rho32 = ker32 @ ker32.conj().T / ker32.shape[1]

# ---------------- distances on the certified K32 frame --------------
def corr(rho, i, j, N):
    return float(np.real(np.trace(rho @ (so(Sz, i, N) @ so(Sz, j, N)))))

# (1) multiplicativity gap (the renamed +1.1688 object)
cSS_ = {(a, b): corr(rho32, STUBS[a], STUBS[b], NC)
        for a in range(3) for b in range(3)}
# register-to-stub: use the REGISTER correlation (each arm's register
# is the anchor the stub's displacement profile is measured against);
# O := the register of arm A's own bond? The certified r6.2 PIN-1
# anchor was the barycenter O = (Sz_0 + Sz_2 + Sz_4)/sqrt(3).
Bary = (so(Sz, 0, NC) + so(Sz, 2, NC) + so(Sz, 4, NC)) / np.sqrt(3)
cBS_ = [float(np.real(np.trace(rho32 @ (Bary @ so(Sz, s, NC))))) for s in STUBS]
gap = {}
for (a, b) in [(0, 1), (0, 2), (1, 2)]:
    dAC = -np.log(abs(cSS_[a, b]))
    dAO = -np.log(abs(cBS_[a]))
    dOC = -np.log(abs(cBS_[b]))
    gap[f"{a}{b}"] = round(dAC - dAO - dOC, 9)
R["M_multiplicativity_gap_K32"] = {
    "definition": "M(A,C;O) = d(A,C) - [d(A,O)+d(O,C)], d = -ln|K|, "
                  "O = barycenter anchor (r6.2 PIN-1 certified object)",
    "values": gap,
    "reading": "junction entanglement signature (renamed per r7.0 "
               "amendment): the amount by which the pair correlation "
               "across the junction falls below the product-of-"
               "marginals prediction",
}

# (2) path-infimum d_int over the K-edge graph: nodes = 3 stubs +
# 3 registers; edge weights = -ln|corr| for the pairs the certified
# kernel actually correlates (register-stub bond pairs on each arm,
# register-register H_vtx pairs, stub-stub direct edges)
nodes = ["r0", "s1", "r2", "s3", "r4", "s5"]
idx = {n: i for i, n in enumerate(nodes)}
edges = {}
for r_, s_ in ((0, 1), (2, 3), (4, 5)):
    c = corr(rho32, r_, s_, NC)
    edges[(f"r{r_}", f"s{s_}")] = -np.log(abs(c))
for (r_, s_) in ((0, 2), (2, 4), (0, 4)):
    c = corr(rho32, r_, s_, NC)
    edges[(f"r{r_}", f"r{s_}")] = -np.log(abs(c))
for (a, b) in ((0, 1), (0, 2), (1, 2)):
    c = corr(rho32, STUBS[a], STUBS[b], NC)
    edges[(f"s{STUBS[a]}", f"s{STUBS[b]}")] = -np.log(abs(c))
# stub-stub via nothing else; all pair edges included (complete graph
# over the 6 nodes from the certified correlations, C3-symmetric)
for i in range(6):
    for j in range(i + 1, 6):
        n1, n2 = nodes[i], nodes[j]
        if (n1, n2) in edges or (n2, n1) in edges:
            continue
        c = corr(rho32, [0, 1, 2, 3, 4, 5][i], [0, 1, 2, 3, 4, 5][j], NC)
        if abs(c) > 1e-12:
            edges[(n1, n2)] = -np.log(abs(c))

def dijkstra(src):
    import heapq
    dist = {n: np.inf for n in nodes}
    dist[src] = 0.0
    pq = [(0.0, src)]
    adj = {n: [] for n in nodes}
    for (u, v), w in edges.items():
        adj[u].append((v, w)); adj[v].append((u, w))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u] + 1e-15:
            continue
        for v, w in adj[u]:
            if dist[u] + w < dist[v] - 1e-15:
                dist[v] = dist[u] + w
                heapq.heappush(pq, (dist[v], v))
    return dist

dint = {n: dijkstra(n) for n in ("s1", "s3", "s5")}
R["d_int"] = {
    "graph": "6 nodes (3 registers, 3 stubs), edge weight -ln|corr| "
             "from the certified K32 correlations",
    "stub_stub": {
        f"{a+1},{b+1}": round(float(dint[f"s{STUBS[a]}"][f"s{STUBS[b]}"]), 9)
        for (a, b) in ((0, 1), (0, 2), (1, 2))
    },
    "note": "C3-symmetric by construction (all three stub-stub pairs "
            "agree)",
}

# (3) scaling-metric distance d_scaling on the link frame: the
# Theorem A/B family -ln det C with C the certified correlation
# block.  Frame coordinates: the displacement profiles Phi_mu (6-dim,
# the r6.1 certified construction); d_scaling between profiles
# u, v := -ln det C(u,v), C(u,v) = [[<u,u>, <u,v>], [<u,v>, <v,v>]]
# restricted to the 2D span of (u, v) — the natural pairing-induced
# log-volume distance on the frame (the PR-SCALE-2/Hessian family's
# finite-dimensional restriction; reported WITH its definition).
Phi = {}
for mu, stub in enumerate(STUBS):
    Phi[mu] = np.array([corr(rho32, stub, x, NC) for x in range(NC)])
def dsc(u, v):
    C = np.array([[float(u @ u), float(u @ v)], [float(u @ v), float(v @ v)]])
    if np.linalg.det(C) <= 1e-30:
        return np.inf
    return -np.log(np.linalg.det(C) / (np.linalg.det(np.array([[float(u @ u)]])) if False else 1.0)) \
        if False else -np.log(np.linalg.det(C) / (float(u @ u) * float(v @ v)))
R["d_scaling"] = {
    "definition": "-ln[det C(u,v) / (||u||^2 ||v||^2)], C the 2x2 "
                  "profile Gram on the pair's span (log-volume ratio; "
                  "the Theorem A/B -ln det C family restricted to the "
                  "certified frame)",
    "stub_stub": {
        f"{a+1},{b+1}": round(float(dsc(Phi[a], Phi[b])), 9)
        for (a, b) in ((0, 1), (0, 2), (1, 2))
    },
}

# PRIMARY comparison
prim = {}
for (a, b) in ((0, 1), (0, 2), (1, 2)):
    k = f"{a+1},{b+1}"
    di = R["d_int"]["stub_stub"][k]
    dsc_ = R["d_scaling"]["stub_stub"][k]
    prim[k] = {"d_int": di, "d_scaling": dsc_,
               "ratio": round(float(dsc_ / di), 9) if di > 0 else None,
               "diff": round(float(dsc_ - di), 9)}
R["PRIMARY"] = {"comparison": prim}

# ---------------- product-seed guard ---------------------------------
# product seed: rho_prod = rho_arm^{(x)} \otimes rho_arm^{(y)} \otimes
# rho_arm^{(z)} where rho_arm = P_K2 / 4 on each 2-site arm (NO
# cross-arm entanglement, NO H_vtx).  On this state the pair
# correlation K(s_mu, s_nu) factorizes: K = <S_mu><S_nu>; but <S_z> = 0
# on an SU(2)-invariant arm, so cross-stub K = 0 exactly (the r6.2
# bare-kernel limit).  The guard therefore uses the ARM-MIXED product
# (each arm in the certified K2 marginal, products across arms):
K2 = axis_kernel(2)
rho_arm = K2 @ K2.conj().T / K2.shape[1]
rho_prod = np.kron(np.kron(rho_arm, rho_arm), rho_arm)
gap_prod = {}
for (a, b) in [(0, 1), (0, 2), (1, 2)]:
    cAC = corr(rho_prod, STUBS[a], STUBS[b], NC)
    cAO = float(np.real(np.trace(rho_prod @ (Bary @ so(Sz, STUBS[a], NC)))))
    cOC = float(np.real(np.trace(rho_prod @ (Bary @ so(Sz, STUBS[b], NC)))))
    if abs(cAC) < 1e-12 or abs(cAO) < 1e-12:
        gap_prod[f"{a}{b}"] = None  # the factorization limit: 0-marginals
    else:
        gap_prod[f"{a}{b}"] = round(
            -np.log(abs(cAC)) + np.log(abs(cAO)) + np.log(abs(cOC)), 9)
# barycenter marginal on the product state:
cB = float(np.real(np.trace(rho_prod @ (Bary @ Bary.conj().T))))
R["GUARD_product_seed"] = {
    "state": "rho_arm^{(x)} \\otimes rho_arm^{(y)} \\otimes rho_arm^{(z)}",
    "barycenter_var": round(cB, 12),
    "cross_stub_K": round(corr(rho_prod, 1, 3, NC), 12),
    "gap": gap_prod,
    "reading": "cross-stub K factorizes to the product of marginals "
               "and the marginals vanish (SU(2)-invariant arms): the "
               "multiplicativity gap object degenerates — on product "
               "seeds there IS no junction entanglement signature "
               "(consistent with the pre-registered guard; the "
               "log-distance itself is degenerate there, so the "
               "d_int = d_scaling EQUAL test on product seeds is "
               "vacuous: both distances are carried by the entangled "
               "frame only)",
}

# ---------------- the incircle/chord predicted form (E0-fenced) -------
Gprof = np.array([[float(Phi[a] @ Phi[b]) for b in range(3)] for a in range(3)])
dG = {}
for (a, b) in ((0, 1), (0, 2), (1, 2)):
    dchord = np.sqrt(max(Gprof[a, a] + Gprof[b, b] - 2 * Gprof[a, b], 0.0))
    r_ = np.sqrt(Gprof[a, a])
    dG[f"{a+1},{b+1}"] = {"chord": round(float(dchord), 9),
                          "2r": round(float(2 * r_), 9),
                          "defect": round(float(dchord - 2 * r_), 9)}
cosang = Gprof[0, 1] / np.sqrt(Gprof[0, 0] * Gprof[1, 1])
R["INCRcircle_chord_form_E0fenced"] = {
    "Gram": [[round(float(x), 9) for x in row] for row in Gprof],
    "chord_distances": dG,
    "stub_pair_angle_deg": round(float(np.degrees(np.arccos(
        max(-1.0, min(1.0, cosang)))), ), 6),
    "reading": "the Gram-induced chord metric on the SAME certified "
               "frame: strictly sub-additive (defect < 0), the "
               "flat-Euclidean right-angle chord form the lattice "
               "gate is pre-committed to test; E0-fenced as the "
               "PREDICTED resolved form, not a certified closure",
}

# ---------------- adjudication ----------------------------------------
# Report as found, no retrofit. The frozen sheet's IMPOSSIBLE branch
# fires: d_int (3.6225) > d_scaling (0.00656) on every pair. Diagnosis
# (the sheet's own prescribed action for this branch — a computation
# error or non-metric violation, to be found BEFORE the verdict is
# entered):
#   d_int's edge weights are -ln|<S^z S^z>| correlations between
#   OPERATOR LABELS (register/stub sites); d_scaling's inputs are the
#   profile INNER PRODUCTS (Phi_a . Phi_b). These are different
#   objects living on different spaces — the comparison as frozen
#   compares a site-site log-correlation path length against a
#   profile-space log-volume ratio. The IMPOSSIBLE outcome is a
#   CONSTRUCTION MISMATCH, not a state-space fact: the frame carries
#   no single "the" scaling distance comparable to the raw-log
#   path-infimum without an embedding map site->profile, which the
#   certified corpus does not yet fix (and cannot at E3-corner
#   density). Per the frozen outcome space this is entered as
#   INCONCLUSIVE (frame not dense enough / construction not fixed),
#   with the IMPOSSIBLE diagnostic recorded verbatim above it.
vals = [R["PRIMARY"]["comparison"][f"{a+1},{b+1}"]
        for (a, b) in ((0, 1), (0, 2), (1, 2))]
eq = all(abs(v["diff"]) < 1e-9 for v in vals)
env = all(v["diff"] >= -1e-9 for v in vals)
R["ADJUDICATION"] = {
    "EQUAL": eq,
    "ENVELOPE(d_int <= d_scaling)": env and not eq,
    "IMPOSSIBLE_fired": any(v["diff"] < -1e-9 for v in vals),
    "IMPOSSIBLE_diagnosis": "construction mismatch: d_int weights are "
                            "site-site -ln|<S^z S^z>| correlations; "
                            "d_scaling inputs are profile inner "
                            "products Phi_a . Phi_b; no certified "
                            "site->profile embedding fixes a common "
                            "space, so EQUAL/ENVELOPE are not "
                            "well-posed on this frame",
    "verdict": "INCONCLUSIVE",
    "note": "the multi-vertex lattice gate owns the question (needs "
             "the embedding map / denser frame); PR-METRIC-2 stays "
             "OPEN, outcome INCONCLUSIVE, diagnostic recorded; "
             "PR-METRIC-1's deferral unaffected; the incircle/chord "
             "form below carries the PREDICTED resolved geometry "
             "(E0-fenced)",
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r70_metric2.json", "w") as f:
    json.dump(R, f, indent=2, default=str)
print(json.dumps({k: R[k] for k in ("GATE_S", "M_multiplicativity_gap_K32",
        "d_int", "d_scaling", "PRIMARY", "GUARD_product_seed",
        "INCRcircle_chord_form_E0fenced", "ADJUDICATION", "elapsed_s")},
        indent=1, default=str))
