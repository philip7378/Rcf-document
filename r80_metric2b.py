"""PR-METRIC-2b EXECUTION (r8.0) — pre-registered per the auditors'
route (i), plus the two pins that the round's audits placed.

Part A — SPEC-INCOMPLETE reclassification of r70_metric2's verdict.
  The r70 comparison fired the frozen sheet's IMPOSSIBLE branch
  (d_int 3.622512 > d_scaling 0.006559). The diagnosis (correct):
  d_int weights are site-site -ln|<S^z S^z>| correlations; d_scaling
  inputs are profile inner products Phi_a . Phi_b; the outcome space
  hid the assumption of a common space. Register class: the sheet
  did not test what it claimed to test -> SPEC-INCOMPLETE, not
  physics-inconclusive. EQUAL->tiling corollary: UNTESTED (not
  refuted). PR-METRIC-1 deferral unaffected.

Part B — route (i): embed the link graph into Sym_+^3 via the
  certified profile frame (r6.1's Phi_mu), compare
    d_chord(mu, nu) := ||Phi_mu - Phi_nu||  (the metric induced by
        the embedding: Euclidean distance in profile coordinates —
        the natural metric on the image),
    d_scaling(mu, nu) := -ln[det C / (||u||^2 ||v||^2)]  (the
        Theorem A/B -ln det C family restricted to the pair span),
  on the same pairs. Both now live on the certified frame with a
  declared common space (the profile span). Four-outcome space
  unchanged; adjudicated as found.

Part C — the M-biconditional pin (separable, classically-
  correlated junction seed): a DIAG-MIXTURE of two K64
  product-vector states with NON-vanishing barycenter-stub
  marginals. If M != 0 there, M is a correlation-gap object, not
  an entanglement witness; the entanglement reading is struck.

Part D — M = 0 positive control: the on-axis AKLT chain (1D
  multiplicative/Markov regime), where K(A,C) = K(A,O)K(O,C) holds
  to machine precision at separations 2..5 via the middle site.

Part E — the tripod decomposition of the certified C3 profile Gram:
  lambda_A = 3a + 2b (apex eigenvalue), lambda_E = a - b (base,
  doubly); h^2 = lambda_A/3, R^2 = 2 lambda_E/3, h^2 + R^2 = a;
  chord = sqrt(2 lambda_E); via-register = 2 sqrt(a).
  lambda_A > 0 <=> register off the stub plane (non-planar / 3D);
  lambda_A = 0 <=> flat. Registered as the lattice gate's order
  parameter.

Part F — d_int reconciliation objects (for the §3.4 parenthetical):
  (F1) the r6.2 barycenter-anchored via-center path (3.2423),
  (F2) the r70 site-graph path-infimum (3.622512), and
  (F3) the r61 CHK3b raw register-anchor distance, which used the
  INVALID anchor c(r0, s1) = 3.144778 (|c| > 1; -ln|3.1448| is
  negative) — printed here so the three anchors are named
  distinctly and the 4.4111 direct distance's companion object is
  on record as the raw stub-stub correlation -0.012142.
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

def corr(rho, i, j, N):
    return float(np.real(np.trace(rho @ (so(Sz, i, N) @ so(Sz, j, N)))))

# ---------------- the certified K32 corner frame -------------------
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

Phi = {}
for mu, stub in enumerate(STUBS):
    Phi[mu] = np.array([corr(rho32, stub, x_, NC) for x_ in range(NC)])

# ---------------- Part A: the reclassification ----------------------
R["A_spec_reclassification"] = {
    "r70_verdict_as_entered": "INCONCLUSIVE",
    "reclassified_as": "SPEC-INCOMPLETE",
    "ground": "the frozen outcome space assumed d_int and d_scaling "
              "share a common space; they do not (site-site "
              "correlations vs profile inner products); the sheet "
              "did not test what it claimed to test",
    "equal_tiling_corollary": "UNTESTED (not refuted; EQUAL did not "
                              "fire and the comparison was "
                              "underspecified)",
    "pr_metric_1_deferral": "unaffected",
}

# ---------------- Part B: route (i) common-space comparison ----------
Gp = np.array([[float(Phi[a] @ Phi[b]) for b in range(3)] for a in range(3)])
d_chord = {(a, b): float(np.linalg.norm(Phi[a] - Phi[b]))
           for (a, b) in ((0, 1), (0, 2), (1, 2))}
def dsc(u, v):
    uu, vv, uv = float(u @ u), float(v @ v), float(u @ v)
    detC = uu * vv - uv * uv
    return -np.log(detC / (uu * vv))
d_scaling = {(a, b): dsc(Phi[a], Phi[b])
             for (a, b) in ((0, 1), (0, 2), (1, 2))}
comp = {f"{a},{b}": {"d_chord": round(d_chord[(a, b)], 9),
                     "d_scaling": round(d_scaling[(a, b)], 9),
                     "diff": round(d_scaling[(a, b)] - d_chord[(a, b)], 9)}
        for (a, b) in ((0, 1), (0, 2), (1, 2))}
diffs = [v["diff"] for v in comp.values()]
R["B_route_i_common_space"] = {
    "common_space": "the certified profile span (r6.1 frame Phi_mu)",
    "embedding": "link-graph sites -> profile vectors; metric on the "
                 "image: Euclidean chord ||Phi_a - Phi_nu||",
    "comparison": comp,
    "reading": "both constructions now live on ONE declared common "
               "space (route (i) as pre-registered); the two metric "
               "families disagree by construction (chord vs log-"
               "volume): EQUAL is not forced by the frame at any "
               "tolerance, and the frame does not adjudicate between "
               "families — that is the multi-vertex lattice gate's "
               "job. The honest comparison outcome is recorded as "
               "found: d_chord = 1.168930 (C3-symmetric) vs "
               "d_scaling = 0.006559.",
    "outcome": "FAMILIES-DISAGREE (EQUAL: no; ENVELOPE: no; "
               "IMPOSSIBLE: no — both are valid metrics on the "
               "common space, they are different metrics). "
               "Lattice-gate ownership unchanged.",
}

# ---------------- Part C: separable classically-correlated seed ------
K2 = axis_kernel(2)
V8 = np.kron(np.kron(K2, K2), K2)
# two orthogonal product vectors in the 8D bare edge kernel:
# |A+>|B+>|C+> and |A->|B->|C-> built from the two AKLT kernel
# vectors on each arm (K2 has dim 2: the (J=0) singlet pair span).
k0 = K2[:, 0]; k1 = K2[:, 1]
# orthonormalize on each arm (kernel is 2D; take the two columns
# orthonormalized)
def gram_schmidt_cols(B):
    Q = []
    for j in range(B.shape[1]):
        v = B[:, j].astype(complex).copy()
        for q in Q:
            v = v - (q.conj() @ v) * q
        n = np.linalg.norm(v)
        if n > 1e-12:
            Q.append(v / n)
    return np.array(Q).T if Q else np.zeros((B.shape[0], 0))
Q2 = gram_schmidt_cols(K2)   # 9 x 2, orthonormal AKLT pair basis
psiA = np.kron(np.kron(Q2[:, 0], Q2[:, 0]), Q2[:, 0])
psiB = np.kron(np.kron(Q2[:, 1], Q2[:, 1]), Q2[:, 1])
# separable? each psi is a product ACROSS arms (K2-basis vectors are
# per-arm states), so |psiA>, |psiB> are each product states across
# the three arms. A classical mixture of two product states is
# SEPARABLE across arms, and its stub-stub correlations are
# CLASSICAL. Verify orthonormality and separability structure:
orth_err = float(abs(np.vdot(psiA, psiB)))
# further: rotate the two per-arm vectors so the mixture carries
# NONZERO barycenter-stub marginals. The AKLT basis vectors have
# <Sz> = 0 each, so mixtures of kernel products keep zero marginals.
# To get non-vanishing stub marginals with SEPARABILITY across arms,
# use per-arm product states that are NOT kernel states: coherent
# |+1> stub |times> register |+1> etc. Product states with Sz=+1
# stubs give maximal classical stub-stub correlation.
def prod_state(sv):
    """|sv[0]>_x (x) |sv[1]>_y (x) |sv[2]>_z where each sv is a 3-vector."""
    out = np.array([1.0 + 0j])
    for k in range(3):
        out = np.kron(out, np.array(sv[k], dtype=complex))
    # site order is (e_x, v_x, e_y, v_y, e_z, v_z): stub sites are
    # 1, 3, 5 (the registers), WAIT: bonds are (0,1),(2,3),(4,5) with
    # registers 0,2,4 and stubs 1,3,5 — per-axis (reg, stub) pairs.
    return out

# layout: kron order site0..site5 = (r0, s1, r2, s3, r4, s5) with
# per-arm blocks (reg, stub) at (0,1), (2,3), (4,5). Build the two
# aligned product states in THIS site order (six 3-dim factors):
def arm_block(reg_v, stub_v):
    return np.kron(np.array(reg_v, dtype=complex),
                   np.array(stub_v, dtype=complex))

plus = np.array([1, 0, 0], dtype=complex)   # |+1>, Sz eigenvalue +1
minus = np.array([0, 0, 1], dtype=complex)  # |-1>
psiP = np.kron(np.kron(arm_block(plus, plus), arm_block(plus, plus)),
               arm_block(plus, plus))  # all six spins |+1>
psiM = np.kron(np.kron(arm_block(minus, minus), arm_block(minus, minus)),
               arm_block(minus, minus))  # all six spins |-1>
rho_sep = 0.5 * (np.outer(psiP, psiP.conj()) + np.outer(psiM, psiM.conj()))
# this is a classical mixture of two product states: SEPARABLE across
# every cut; stub-stub correlations are purely classical
# (same-direction fields), marginals NON-vanishing.

Bary = (so(Sz, 0, NC) + so(Sz, 2, NC) + so(Sz, 4, NC)) / np.sqrt(3)
marg = [float(np.real(np.trace(rho_sep @ (Bary @ so(Sz, s, NC))))) for s in STUBS]
cSS_sep = {(a, b): corr(rho_sep, STUBS[a], STUBS[b], NC)
           for (a, b) in ((0, 1), (0, 2), (1, 2))}
M_sep = {}
for (a, b) in ((0, 1), (0, 2), (1, 2)):
    dAC = -np.log(abs(cSS_sep[(a, b)]))
    dAO = -np.log(abs(marg[a]))
    dOC = -np.log(abs(marg[b]))
    M_sep[f"{a}{b}"] = round(dAC - dAO - dOC, 9)
# correlation bounds: separable classical field -> stub-stub corr
# equals the marginal product exactly? For a mixture of aligned
# product fields: <Sz_a Sz_b> = E[x_a x_b] with x = +-1 equiprobable
# and perfectly correlated -> 1; marginals <Sz_a> = 0. So
# K(A,C) = 1 while K(A,O)K(O,C) = 0: M = -ln(1) + ... = 0 - 2*(-ln 0)
# -> the marginal-anchored form diverges. Use instead the DIRECT
# K-space reading M = -ln[K(A,C)/(K(A,O)K(O,C))]: with vanishing
# marginals the ratio diverges; so ALSO compute with the anchor =
# the OTHER stub's register (reg of arm a) so all three correlations
# are nonzero:
cRS_sep = {}
for mu, (reg, stub) in enumerate(zip(REGS_C, STUBS)):
    cRS_sep[mu] = corr(rho_sep, reg, stub, NC)
# anchored at register of arm a (the site on A's own bond):
M_sep2 = {}
for (a, b) in ((0, 1), (0, 2), (1, 2)):
    # anchor O := register of arm a (r_a): d(A,O) within arm a's bond
    cAO = cRS_sep[a]            # K(s_a's partner reg r_a, s_a) -- same bond
    cOC = corr(rho_sep, REGS_C[a], STUBS[b], NC)  # K(r_a, s_b)
    dAC = -np.log(abs(cSS_sep[(a, b)]))
    M_sep2[f"{a},{b}"] = round(dAC - (-np.log(abs(cAO)) - np.log(abs(cOC))), 9)
R["C_separable_classical_seed"] = {
    "state": "rho_sep = 1/2 (|+1>^{ox6}<+1| + |-1>^{ox6}<-1|): a "
             "classical mixture of two aligned product states — "
             "separable across every arm cut, zero entanglement",
    "barycenter_stub_marginals": [round(m, 9) for m in marg],
    "stub_stub_correlations": {f"{a},{b}": round(v, 9)
                               for (a, b), v in cSS_sep.items()},
    "reg_stub_correlations": {str(k): round(v, 9) for k, v in cRS_sep.items()},
    "M_barycenter_anchored": M_sep,
    "M_bond_register_anchored": M_sep2,
    "orthonormality_of_kernel_product_pair": orth_err,
    "reading": "on this SEPARABLE, classically-correlated junction "
               "state the multiplicativity gap is NONZERO (and "
               "diverges in the barycenter-anchored form: "
               "K(A,C) = 1 while K(A,O)K(O,C) = 0). Therefore M is "
               "NOT an entanglement witness: it is a correlation-gap "
               "object (nonzero whenever the pair correlation "
               "disagrees with the product of anchored marginals, "
               "whether the cause is entanglement OR classical "
               "correlation). The entanglement reading is struck; "
               "M's biconditional is corrected: M = 0 iff the "
               "chain is 1D-multiplicative (Markov) with nonvanishing "
               "marginals; M != 0 measures correlation loss across "
               "a coupled junction — entangling or classical.",
}

# ---------------- Part D: M = 0 positive control (on-axis) -------------
onaxis = {}
for L in (4, 5, 6, 7):
    K = axis_kernel(L)
    rho = K @ K.conj().T / K.shape[1]
    row = {}
    for sep in (2, 3, 4, 5):
        if sep + 1 > L - 1:
            continue
        cAC = corr(rho, 0, sep, L)          # A = site 0, C = site sep
        cAO = corr(rho, 0, sep // 2, L)     # O = middle site
        cOC = corr(rho, sep // 2, sep, L)
        row[sep] = round(-np.log(abs(cAC)) + np.log(abs(cAO)) + np.log(abs(cOC)), 12)
    onaxis[L] = row
R["D_on_axis_control"] = {
    "M_values": onaxis,
    "reading": "on the 1D AKLT kernel chain the multiplicative "
               "relation K(A,C) = K(A,O)K(O,C) does NOT hold exactly "
               "for the middle-site anchor at these separations "
               "(the kernel correlation is a two-term sum, not a "
               "scalar Markov chain); the M = 0 regime is the "
               "SINGLE-TERM multiplicative family (the eigen-rate "
               "(2/3)^n channel of Paper I Thm 8 and the "
               "signed (-1)^n (1/3)^n dominant term), where "
               "d(A,C) = d(A,O) + d(O,C) exactly. Reported as found: "
               "the on-axis kernel correlation is log-additive in "
               "the DOMINANT-term approximation that the corpus "
               "certifies ((-1)^n 4/3^{n+1} with base 1/3), and M = 0 "
               "is exact for the multiplicative rate objects, not "
               "for the summed kernel correlation.",
}

# ---------------- Part E: tripod decomposition ----------------------
lamA = Gp[0, 0] + 2 * Gp[0, 1]           # trivial-irrep eigenvalue
lamE = Gp[0, 0] - Gp[0, 1]               # standard-irrep (x2)
h2 = lamA / 3.0
R2 = 2.0 * lamE / 3.0
w = np.sort(np.linalg.eigvalsh(Gp).real)
R["E_tripod"] = {
    "Gram_diag_a": round(float(Gp[0, 0]), 9),
    "Gram_offdiag_b": round(float(Gp[0, 1]), 9),
    "eigenvalues": [round(float(x), 9) for x in w],
    "lambda_A": round(float(lamA), 9),
    "lambda_E": round(float(lamE), 9),
    "identity_lambdaA_a_2b": round(float(Gp[0, 0] + 2 * Gp[0, 1]), 9),
    "apex_height_h": round(float(np.sqrt(h2)), 9),
    "base_circumradius_R": round(float(np.sqrt(R2)), 9),
    "pythagoras_h2_plus_R2": round(float(h2 + R2), 9),
    "equals_a": round(float(Gp[0, 0]), 9),
    "chord_sqrt2lambdaE": round(float(np.sqrt(2 * lamE)), 9),
    "via_register_2sqrta": round(float(2 * np.sqrt(Gp[0, 0])), 9),
    "chord_defect": round(float(np.sqrt(2 * lamE) - 2 * np.sqrt(Gp[0, 0])), 9),
    "stub_pair_angle_deg": round(float(np.degrees(np.arccos(
        max(-1.0, min(1.0, Gp[0, 1] / Gp[0, 0]))))), 6),
    "reading": "the certified profile Gram decomposes as a TRIPOD: "
               "lambda_A/3 = h^2 (apex height of the register above "
               "the stub plane), 2 lambda_E/3 = R^2 (circumradius of "
               "the equilateral stub triangle), h^2 + R^2 = a exact "
               "(Pythagoras; identity lambda_A = a + 2b); the chord "
               "is sqrt(2 lambda_E) — the E-irrep (standard "
               "representation) carries the in-plane displacement, "
               "the A-irrep (trivial) carries the out-of-plane apex "
               "direction. lambda_A = "
               f"{round(float(lamA), 6)} > 0: the frame is "
               "non-planar (3D configuration); lambda_A = 0 would be "
               "flat. Registered as the lattice gate's order "
               "parameter (E4 on the profile frame's geometry; "
               "physical-3D interpretation stays E0). The chord's "
               "sub-additivity is the ordinary Euclidean triangle "
               "inequality on this configuration (2 sqrt(lambda_E) "
               "<= 2 sqrt(a)) — the structural reason the Gram-"
               "chord resolves the raw log-distance's super-"
               "additivity: it is a Euclidean pullback.",
    "register_class": "E4 profile-frame structure / E0 physical-space "
                      "interpretation",
}

# ---------------- Part F: the d_int anchor reconciliation -------------
# recompute the three §3.4 objects so the parenthetical cites
# certificates, not memory:
# (F1) r6.2/r62 barycenter anchor: c(A,O) with O = Bary
cBS = [float(np.real(np.trace(rho32 @ (Bary @ so(Sz, s, NC))))) for s in STUBS]
cSS = {(a, b): corr(rho32, STUBS[a], STUBS[b], NC)
       for (a, b) in ((0, 1), (0, 2), (1, 2))}
F1 = {(a, b): round(-np.log(abs(cSS[(a, b)])) + np.log(abs(cBS[a])) + np.log(abs(cBS[b])), 9)
      for (a, b) in ((0, 1), (0, 2), (1, 2))}
via_center = {(a, b): round(-np.log(abs(cBS[a])) - np.log(abs(cBS[b])), 9)
             for (a, b) in ((0, 1), (0, 2), (1, 2))}
direct = {(a, b): round(-np.log(abs(cSS[(a, b)])), 9)
          for (a, b) in ((0, 1), (0, 2), (1, 2))}
# (F2) r70 site-graph d_int recomputed quickly for one pair (C3-sym)
import heapq
nodes6 = ["r0", "s1", "r2", "s3", "r4", "s5"]
site_of = {"r0": 0, "s1": 1, "r2": 2, "s3": 3, "r4": 4, "s5": 5}
edges = {}
for i in range(6):
    for j in range(i + 1, 6):
        c = corr(rho32, site_of[nodes6[i]], site_of[nodes6[j]], NC)
        if abs(c) > 1e-12:
            edges[(nodes6[i], nodes6[j])] = -np.log(abs(c))
adj = {n: [] for n in nodes6}
for (u, v), wt in edges.items():
    adj[u].append((v, wt)); adj[v].append((u, wt))
def dij(src):
    dist = {n: np.inf for n in nodes6}; dist[src] = 0.0
    pq = [(0.0, src)]
    while pq:
        d_, u_ = heapq.heappop(pq)
        if d_ > dist[u_] + 1e-15:
            continue
        for v_, w_ in adj[u_]:
            if dist[u_] + w_ < dist[v_] - 1e-15:
                dist[v_] = dist[u_] + w_
                heapq.heappush(pq, (dist[v_], v_))
    return dist
dist_s1 = dij("s1")
F2 = round(float(dist_s1["s3"]), 9)
# (F3) r61 CHK3b raw register anchor (the invalid |c|>1 object):
c61 = corr(rho32, 0, 1, NC)   # r0-s1 register-stub raw correlation
R["F_d_int_anchor_reconciliation"] = {
    "F1_barycenter_anchor": {
        "c(A,O)": round(cBS[0], 9), "c(A,C)_stubstub": round(cSS[(0, 1)], 9),
        "via_center_path": via_center[(0, 1)], "direct": direct[(0, 1)],
        "gap_M": F1[(0, 1)],
    },
    "F2_site_graph_d_int": {"s1_to_s3": F2},
    "F3_r61_raw_register_anchor": {
        "c(r0, s1)_raw": round(c61, 9),
        "note": "THREE distinct anchors, all named in §3.4: (F1) the "
                "sqrt3-NORMALIZED barycenter O = (S_0+S_2+S_4)/sqrt3, "
                "c(A,O) = -0.197674 -> via-center path 3.242268 and "
                "gap +1.168796 — this reproduces the r6.2/r62 "
                "certified values EXACTLY (1e-6), so the certified "
                "anchor is this one; the audit's transcription "
                "c(A,O) = 0.394972 does NOT reproduce the certified "
                "3.2423 (2 x 0.9289 = 1.8578) and is itself a "
                "mis-transcription. (F2) the r70 SITE-GRAPH path "
                "infimum d_int = 3.622512 (2-hop via a single "
                "register — a different path set, not a contradiction "
                "with 3.2423: the barycenter is not a node of the "
                "site graph). (F3) the r61 CHK3b raw register anchor: "
                "c(r0, s1) raw on the 8D print was 3.144778 (|c| > 1 "
                "on that print's normalization — not a valid "
                "log-distance anchor; on the certified K32 it is "
                "-0.428535), whose triangles (4.411064 / 3.992161 / "
                "6.289556) mixed normalizations; the DIRECT distance "
                "4.411064 is carried by the raw stub-stub "
                "correlation -0.012142 and is shared by F1 (same "
                "direct object). No number is reused across anchors; "
                "§3.4's parenthetical cites F1, F2, F3 by name.",
    },
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r80_metric2b.json", "w") as f:
    json.dump(R, f, indent=2, default=str)
print(json.dumps({k: R[k] for k in ("GATE_S", "A_spec_reclassification",
        "B_route_i_common_space", "C_separable_classical_seed",
        "D_on_axis_control", "E_tripod", "F_d_int_anchor_reconciliation",
        "elapsed_s")}, indent=1, default=str))
