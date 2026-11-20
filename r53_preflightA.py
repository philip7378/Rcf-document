"""r5.3 pre-flight A — machine-verification of the Exact Partial-Trace
Locality Theorem (the E4 shortcut the seat proposes for closing
PR-T1b-2c without a run).

The theorem: the two-bond strobe channel E = e^{t L1} e^{t L0} acts
only on sites {0,1,2} and as identity on sites B = {3..N-1}; partial
trace over B commutes with E, so the site-1 output depends ONLY on
rho_012 = Tr_B(rho), for EVERY state (entangled included).

Machine certificate targets:
  A1  ||Tr_3(L0(rho)) - L0(Tr_3(rho))||_F ~ 1.63e-16 on a random
      maximally-entangled N=4 pure state (the seat's spot check).
  A2  the strobe version at finite t: ||Tr_3(E(rho)) -
      E(Tr_3(rho))||_F, several t.
  A3  THE DECISIVE NO-GO VII CERTIFICATE: for entangled N=4 states,
      the FULL site-1 output of the N=4 strobe equals the N=3 strobe
      applied to rho_012 (computed through the N=3 and N=4 machinery
      independently). If this holds on entangled states with nonzero
      3-site marginal deviation, then the two-bond statistic is
      STRICTLY N-independent for ALL states — No-Go VII promotes to
      E4 on the fixed-marginal class, and PR-T1b-2c is vacated BY
      THEOREM (pinned seeds still feed a 3-site marginal into a
      3-site map).
  A4  sanity: the certificate runs on seeds with genuinely entangled
      3-site marginals (Schmidt rank > 1 across the {012}|{3} cut and
      across {01}|{23}), and a Ginibre-style entangled state so the
      F2 family's situation is covered.
"""
import json
import time

import numpy as np
from scipy.sparse.linalg import expm_multiply

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

def superop_from(Ls, H, DIM):
    import scipy.sparse as sparse
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
    return sparse.csc_matrix(out)

def ptrace_all_but_first3(rho, N):
    """Trace out sites 3..N-1, keep sites {0,1,2} -> 27x27."""
    T = rho.reshape([3] * N + [3] * N)
    letters = "abcdefghijklmnopqrstuvwxy"
    sub = [letters[i] for i in range(2 * N)]
    for i in range(3, N):
        sub[N + i] = sub[i]
    return np.einsum("".join(sub), T).reshape(27, 27)

def ptrace_site1(rho, N):
    T = rho.reshape([3] * N + [3] * N)
    letters = "abcdefghijklmnopqrstuvwxy"
    sub = [letters[i] for i in range(2 * N)]
    for i in range(N):
        if i != 1:
            sub[N + i] = sub[i]
    return np.einsum("".join(sub), T).reshape(3, 3)

# ---- build N=4 and N=3 machinery ------------------------------------
N4, D4 = 4, 81
h4 = [sum(bond2_op(SVEC[q], SVEC[q], b, 4) for q in range(3))
      for b in range(3)]
Lb4 = [superop_from(cov3_jumps(b, 4), h4[b], D4) for b in range(3)]

N3, D3 = 3, 27
h3 = [sum(bond2_op(SVEC[q], SVEC[q], b, 3) for q in range(3))
      for b in range(2)]
Lb3 = [superop_from(cov3_jumps(b, 3), h3[b], D3) for b in range(2)]

def strobe_apply(Lb, rho, t):
    D = rho.shape[0]
    v = rho.reshape(-1, order="F")
    v = expm_multiply(Lb[0] * float(t), v)
    v = expm_multiply(Lb[1] * float(t), v)
    return v.reshape(D, D, order="F")

def L0_apply(Lb, rho):
    D = rho.shape[0]
    v = rho.reshape(-1, order="F")
    out = Lb[0] @ v
    return np.asarray(out).reshape(D, D, order="F")

# ---- the test seeds (all ENTANGLED across 3|rest and 01|23) ---------
rng = np.random.default_rng(20261120)

def haar_pure(N):
    D = 3 ** N
    z = (rng.normal(size=(D,)) + 1j * rng.normal(size=(D,))) / np.sqrt(2)
    z = z / np.linalg.norm(z)
    return np.outer(z, z.conj())

seeds = {
    "haar_N4": haar_pure(4),
    "haar_N4_b": haar_pure(4),
    "ginibre_N4": None,
}
G = (rng.normal(size=(D4, D4)) + 1j * rng.normal(size=(D4, D4))) / np.sqrt(2)
Hh = (G + G.conj().T) / 2
w_, v_ = np.linalg.eigh(Hh)
w_ = np.exp(w_); w_ = w_ / w_.sum()
seeds["ginibre_N4"] = (v_ * w_) @ v_.conj().T

# a dedicated maximally-entangled (012)|(3) state for A1: Schmidt rank 3
def max_entangled_0123():
    # maximally entangled across the (012)|(3) cut: rank 3, Schmidt
    # coefficients all 1/sqrt(3)
    out = np.zeros((27, 3), dtype=complex)
    for k in range(3):
        out[9 * k, k] = 1.0
    out = out / np.sqrt(3)
    psi = out.reshape(-1)
    return np.outer(psi, psi.conj())

seeds["maxent_0123"] = max_entangled_0123()

# ---- A1: single-generator commutation with partial trace ------------
a1 = {}
for name, rho in seeds.items():
    lhs = ptrace_all_but_first3(L0_apply(Lb4, rho), 4)
    rhs = L0_apply(Lb3, ptrace_all_but_first3(rho, 4))
    a1[name] = float(np.linalg.norm(lhs - rhs, "fro"))
R["A1_single_generator"] = {
    "errors": {k: f"{v:.3e}" for k, v in a1.items()},
    "declared_haar": 1.63e-16,
    "verdict": "PASS" if max(a1.values()) < 1e-13 else "FAIL",
}

# ---- A2: finite-t strobe version -------------------------------------
a2 = {}
for t in (0.25, 0.5, 1.0, 2.0):
    row = {}
    for name in ("haar_N4", "maxent_0123", "ginibre_N4"):
        rho = seeds[name]
        lhs = ptrace_all_but_first3(strobe_apply(Lb4, rho, t), 4)
        rhs = strobe_apply(Lb3, ptrace_all_but_first3(rho, 4), t)
        row[name] = float(np.linalg.norm(lhs - rhs, "fro"))
    a2[f"t={t}"] = {k: f"{v:.3e}" for k, v in row.items()}
R["A2_strobe_version"] = {
    "errors": a2,
    "verdict": "PASS" if all(
        float(v) < 1e-12 for row in a2.values() for v in row.values()
    ) else "FAIL",
}

# ---- A3: THE DECISIVE CERTIFICATE -------------------------------------
# site-1 output of the N=4 strobe == N=3 strobe on rho_012, entangled seeds
a3 = {}
for t in (0.5, 1.0, 2.0, 3.0):
    row = {}
    for name in ("haar_N4", "haar_N4_b", "maxent_0123", "ginibre_N4"):
        rho = seeds[name]
        lhs = ptrace_site1(strobe_apply(Lb4, rho, t), 4)
        rhs = ptrace_site1(strobe_apply(Lb3, ptrace_all_but_first3(rho, 4), t), 3)
        row[name] = float(np.linalg.norm(lhs - rhs, "fro"))
    a3[f"t={t}"] = {k: f"{v:.3e}" for k, v in row.items()}
R["A3_decisive_certificate"] = {
    "errors": a3,
    "meaning": ("site-1 output of the N=4 two-bond strobe == the N=3 "
                "strobe on rho_012, on ENTANGLED inputs: the two-bond "
                "statistic is strictly N-independent for ALL states"),
    "verdict": "PASS" if all(
        float(v) < 1e-12 for row in a3.values() for v in row.values()
    ) else "FAIL",
}

# ---- A4: the seeds really are entangled where it matters -------------
def schmidt_rank(rho, cut):
    N = 4
    T = rho.reshape([3] * N + [3] * N)
    # cut = number of sites on the left block
    letters = "abcdefghijklmnopqrstuvwxy"
    sub = [letters[i] for i in range(2 * N)]
    # trace out nothing; reshape to (3^cut x 3^{N-cut})^2 via einsum to
    # a bipartite matrix: rows = left indices, cols = right indices
    left_r = sub[:cut]; right_r = sub[cut:N]
    left_c = sub[N:N + cut]; right_c = sub[N + cut:]
    # rho as operator: reshape to (3^N, 3^N); view as block matrix
    M = rho.reshape(3 ** cut, 3 ** (N - cut), 3 ** cut, 3 ** (N - cut))
    M = M.transpose(0, 2, 1, 3).reshape(3 ** cut * 3 ** cut,
                                        3 ** (N - cut) * 3 ** (N - cut))
    s = np.linalg.svd(M, compute_uv=False)
    return int((s > 1e-10).sum())

a4 = {}
for name in ("haar_N4", "haar_N4_b", "maxent_0123", "ginibre_N4"):
    rho = seeds[name]
    r03 = schmidt_rank(rho, 3)   # cut (012)|(3)
    r02 = schmidt_rank(rho, 2)   # cut (01)|(23)
    p012 = ptrace_all_but_first3(rho, 4)
    dev = float(np.linalg.norm(ptrace_site1(p012, 3) - np.eye(3) / 3, "fro"))
    a4[name] = {"schmidt_012_3": r03, "schmidt_01_23": r02,
                "site1_deviation": round(dev, 6)}
R["A4_seed_entanglement"] = a4

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r53_preflightA.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("A1:", json.dumps(R["A1_single_generator"], indent=1))
print("A2:", json.dumps(R["A2_strobe_version"], indent=1))
print("A3:", json.dumps(R["A3_decisive_certificate"], indent=1))
print("A4:", json.dumps(a4, indent=1))
print("elapsed:", R["elapsed_s"])
