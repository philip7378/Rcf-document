"""r5.1d pre-flight part 2 — the seat-1 channel decomposition, verified by
machine BEFORE PR-T1b-2 execution, so the B1 adjudication is not
blindsided (and the off-orbit C-criterion uses the SU(2)-orbit-tangent
projection the seat specified, not raw quadrupole projection).

Seat-1 claims to verify (exact O(t^2) decomposition of the holonomy on
the 0.7|+1,+1,0><+1,+1,0| + 0.3 I/27 seed):
  (C1) pure chiral [L_H1, L_H0] contribution to the site-1 channel:
        0.000000 identically (because <S_2> = 0 on |0>_2 makes
        <S_0> x <S_2> = 0).
  (C2) cross Lie-Jordan [L_H, D] contribution: 0.000000 at O(t^2).
  (C3) pure dissipative [D_1, D_0] contribution: 0.147915 = 100% of the
        t->0 limit (growing to 0.176 at t=0.25 via O(t^3) cross terms),
        su(3) breakdown 0.76% dipole / 99.24% quadrupole.
  (C4) on the |+x,+x,+z> seed (chiral-active): pure chiral 0.700000
        (50.00% dipole, 50.00% quadrupole, ZERO off-orbit residual);
        pure dissipative 0.128689 (25.76/74.24); cross 0.430888
        (0.06/99.94); total 0.886454 (39.96/60.04).
  (C5) the identity Tr_{0,2}([L_H1, L_H0] rho) = i[S_1 . (<S_0> x
        <S_2>), rho^{(1)}] on product states (the mechanism behind C1).

Method: expand the two-ordering difference to O(t^2) analytically:
  rho(0->1) - rho(1->0) = (t^2/2) [L_1, L_0] rho_0 + O(t^3)
so the O(t^2) site-1 displacement is (t^2/2) Tr_{0,2}([L_1, L_0] rho_0),
decomposed over the superoperator pieces
  [L_1, L_0] = [L_H1, L_H0] + ([L_H1, D_0] + [D_1, L_H0]) + [D_1, D_0].
The su(3) dipole/quadrupole split: expand the 3x3 site-1 displacement in
the orthonormal Gell-Mann basis; dipole = the 3 spin (antisymmetric)
directions, quadrupole = the 5 remaining (symmetric-traceless) directions.
Off-orbit residual: component orthogonal to the SU(2) orbit tangent space
T_SU(2)(rho_1) = span{i[S_q, rho_1]}_q.
Norm convention (seat-1's numbers): Frobenius norm of each channel's
site-1 displacement matrix, at t=1 (i.e. the coefficient of t^2/2 --
checked below against the seats' magnitudes).
"""
import json
import time

import numpy as np
import scipy.sparse as sparse

t0 = time.time()
R = {}

Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]

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
    J0 = [(t(1, -1) - t(0, 0) + t(-1, 1)) / np.sqrt(3)]
    return {0: J0, 1: J1, 2: J2}

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

N3, D3 = 3, 27

def superop_from(Ls, H, DIM=D3):
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
    return out.toarray()

h0 = sum(bond2_op(SVEC[q], SVEC[q], 0, N3) for q in range(3))
h1 = sum(bond2_op(SVEC[q], SVEC[q], 1, N3) for q in range(3))
LH0 = superop_from([], h0)
LH1 = superop_from([], h1)
D0 = superop_from([L for L in cov3_jumps(0, N3)],
                  np.zeros((D3, D3), dtype=complex))
D1 = superop_from([L for L in cov3_jumps(1, N3)],
                  np.zeros((D3, D3), dtype=complex))

def partial_trace_site(rho, site, N=N3):
    out = np.zeros((3, 3), dtype=complex)
    for a in range(3):
        for b in range(3):
            tot = 0.0
            for rest in np.ndindex(*([3] * (N - 1))):
                ii = [0] * N; jj = [0] * N; k = 0
                for s in range(N):
                    if s == site:
                        ii[s] = a; jj[s] = b
                    else:
                        ii[s] = rest[k]; jj[s] = rest[k]; k += 1
                r = sum(ii[s] * 3 ** (N - 1 - s) for s in range(N))
                c = sum(jj[s] * 3 ** (N - 1 - s) for s in range(N))
                tot += rho[r, c]
            out[a, b] = tot
    return out

def channel_pieces(rho0):
    """Site-1 O(t^2) displacement (coefficient of t^2/2 in
    rho(0->1)-rho(1->0)) split into the three channels."""
    def site1_of(A, rho):
        # A acts on vec(rho) column-stacking; result site-1 marginal
        v = (A @ rho.reshape(-1, order="F")).reshape(D3, D3, order="F")
        return partial_trace_site(v, 1)

    chi = site1_of(LH1 @ LH0 - LH0 @ LH1, rho0)
    dis = site1_of(D1 @ D0 - D0 @ D1, rho0)
    cross = site1_of((LH1 @ D0 - D0 @ LH1) + (D1 @ LH0 - LH0 @ D1), rho0)
    tot = site1_of((LH0 + D0) @ (LH1 + D1) - (LH1 + D1) @ (LH0 + D0), rho0)
    return chi, cross, dis, tot

# su(3) decomposition of a 3x3 (Hermitian, traceless) displacement
LAM = []
for i in range(3):
    for j in range(i + 1, 3):
        A = np.zeros((3, 3), dtype=complex); A[i, j] = 1; A[j, i] = 1
        LAM.append(A / np.sqrt(2))
        B = np.zeros((3, 3), dtype=complex); B[i, j] = -1j; B[j, i] = 1j
        LAM.append(B / np.sqrt(2))
LAM.append(np.diag([1, -1, 0]).astype(complex) / np.sqrt(2))
LAM.append(np.diag([1, 1, -2]).astype(complex) / np.sqrt(6))
# dipole (spin) directions: the antisymmetric generators (indices 1,3,5)
DIP_IDX = [1, 3, 5]

def su3_split(M, rho1=None):
    """Frobenius shares of M (3x3 complex) over dipole vs quadrupole
    directions, AFTER removing the trace. If rho1 is given, the split is
    the seat-1 convention: dipole = the SU(2)-reachable subspace
    span{i[S_q, rho_1]} (the orbit tangent at the CURRENT state -- so a
    pure SU(2) rotation of rho1 is 100% dipole, matching the seat's
    'a pure rotation still carries quadrupole moments' caution when rho1
    is not the fixed-axis basis state); quadrupole = the orthogonal
    complement. Without rho1, the fixed global Gell-Mann split (3
    antisymmetric = dipole) is used and reported under a separate key."""
    T = M - np.trace(M) / 3 * np.eye(3, dtype=complex)
    tot = float(np.linalg.norm(T, "fro"))
    out = {"total": round(tot, 6)}
    if rho1 is None:
        coeffs = [float(np.real(np.trace(L.conj().T @ T))) for L in LAM]
        dip = float(np.sqrt(sum(coeffs[i] ** 2 for i in DIP_IDX)))
        quad = float(np.sqrt(sum(c ** 2 for i, c in enumerate(coeffs)
                                  if i not in DIP_IDX)))
        out.update({"dipole": round(dip, 6), "quadrupole": round(quad, 6),
                    "basis": "global-GellMann"})
    else:
        tangents = [1j * (SVEC[q] @ rho1 - rho1 @ SVEC[q]) for q in range(3)]
        A = np.stack([t.reshape(-1) for t in tangents], axis=1)
        coef, *_ = np.linalg.lstsq(A, T.reshape(-1), rcond=None)
        proj = (A @ coef).reshape(3, 3)
        resid = T - proj
        dip = float(np.linalg.norm(proj, "fro"))
        quad = float(np.linalg.norm(resid, "fro"))
        out.update({"dipole": round(dip, 6), "quadrupole": round(quad, 6),
                    "basis": "rho1-orbit-tangent (seat-1 convention)"})
    if tot > 1e-12:
        out["dipole_pct"] = round(100 * out["dipole"] / tot, 2)
        out["quadrupole_pct"] = round(100 * out["quadrupole"] / tot, 2)
    return out

def off_orbit_residual(M, rho1):
    """Component of the site-1 displacement M orthogonal to the SU(2)
    orbit tangent space T = span{i[S_q, rho_1]} (seat-1's caution: a pure
    SU(2) rotation carries 50% quadrupole share but ZERO off-orbit
    residual; project against the tangent, not against quadrupole)."""
    T = M - np.trace(M) / 3 * np.eye(3, dtype=complex)
    tangents = [1j * (SVEC[q] @ rho1 - rho1 @ SVEC[q]) for q in range(3)]
    # Gram-Schmidt the tangent basis
    orth = []
    for v in tangents:
        for w in orth:
            v = v - (np.trace(w.conj().T @ v) / np.trace(w.conj().T @ w)) * w \
                if abs(np.trace(w.conj().T @ w)) > 1e-14 else v
        n = float(np.linalg.norm(v, "fro"))
        if n > 1e-14:
            orth.append(v / n)
    resid = T.copy()
    for w in orth:
        resid = resid - np.trace(w.conj().T @ resid) * w
    return float(np.linalg.norm(resid, "fro")), [float(np.linalg.norm(w, 'fro')) for w in orth]

def ket3(m0, m1, m2):
    v = lambda m: np.eye(3)[m + 1]
    return np.kron(np.kron(v(m0), v(m1)), v(m2)).astype(complex)

def coherent_ket(direction, site):
    """|+n> spin-1 coherent state on one site: eigenvector of n.S with
    eigenvalue +1."""
    n = np.array(direction, dtype=float)
    n = n / np.linalg.norm(n)
    nS = n[0] * Sx + n[1] * Sy + n[2] * Sz
    w, v = np.linalg.eigh(nS)
    return v[:, int(np.argmin(abs(w - 1.0)))]

I27 = np.eye(27, dtype=complex) / 27

# ---- Seed A: 0.7|+1,+1,0><+1,+1,0| + 0.3 I/27 ------------------------
psiA = ket3(1, 1, 0)
rhoA = 0.7 * np.outer(psiA, psiA.conj()) + 0.3 * I27
chiA, crossA, disA, totA = channel_pieces(rhoA)
rho1A = partial_trace_site(rhoA, 1)

R["seed_A_+1+10"] = {
    "chiral_F": round(float(np.linalg.norm(chiA, "fro")), 9),
    "cross_F": round(float(np.linalg.norm(crossA, "fro")), 9),
    "dissipative_F": round(float(np.linalg.norm(disA, "fro")), 9),
    "total_F": round(float(np.linalg.norm(totA, "fro")), 9),
    "declared": {"chiral": 0.0, "cross": 0.0, "dissipative": 0.147915},
    "dissipative_su3": su3_split(disA, rho1A),
    "chiral_su3": su3_split(chiA, rho1A),
    "verdict_C1": "PASS" if np.linalg.norm(chiA, "fro") < 1e-9 else "FAIL",
    "verdict_C2": "PASS" if np.linalg.norm(crossA, "fro") < 1e-9 else "CHECK",
    "verdict_C3": ("PASS" if abs(np.linalg.norm(disA, "fro") - 0.147915)
                   < 5e-3 else "CHECK"),
}

# ---- (C5) the product-state identity --------------------------------
# Tr_{0,2}([L_H1, L_H0] rho) = i [S_1 . (<S_0> x <S_2>), rho^{(1)}]
rng = np.random.default_rng(5)
max_err = 0.0
for trial in range(6):
    # random product state rho0 (x) rho1 (x) rho2
    def rand_rho():
        G = (rng.normal(size=(3, 3)) + 1j * rng.normal(size=(3, 3))) / np.sqrt(2)
        Hh = (G + G.conj().T) / 2
        w, v = np.linalg.eigh(Hh)
        w = np.exp(w); w = w / w.sum()
        return (v * w) @ v.conj().T
    r0, r1, r2 = rand_rho(), rand_rho(), rand_rho()
    rho_prod = np.kron(np.kron(r0, r1), r2)
    lhs = partial_trace_site(
        ((LH1 @ LH0 - LH0 @ LH1) @ rho_prod.reshape(-1, order="F")
         ).reshape(D3, D3, order="F"), 1)
    s0 = np.array([np.real(np.trace(r0 @ SVEC[q])) for q in range(3)])
    s1 = np.array([np.real(np.trace(r1 @ SVEC[q])) for q in range(3)])
    s2 = np.array([np.real(np.trace(r2 @ SVEC[q])) for q in range(3)])
    nvec = np.cross(s0, s2)
    Sn = sum(nvec[q] * SVEC[q] for q in range(3))
    rhs = 1j * (Sn @ r1 - r1 @ Sn)
    max_err = max(max_err, float(np.linalg.norm(lhs - rhs, "fro")))
R["identity_C5_product"] = {
    "max_err_over_6_trials": round(max_err, 12),
    "verdict": "PASS" if max_err < 1e-9 else "FAIL",
}

# ---- Seed B: 0.7|+x,+x,+z> + 0.3 I/27 -------------------------------
px = coherent_ket([1, 0, 0], 1)
pz = coherent_ket([0, 0, 1], 1)
psiB = np.kron(np.kron(px, px), pz)
rhoB = 0.7 * np.outer(psiB, psiB.conj()) + 0.3 * I27
chiB, crossB, disB, totB = channel_pieces(rhoB)
rho1B = partial_trace_site(rhoB, 1)

resid_chi, tang_chi = off_orbit_residual(chiB, rho1B)
resid_tot, _ = off_orbit_residual(totB, rho1B)

R["seed_B_+x+x+z"] = {
    "chiral_F": round(float(np.linalg.norm(chiB, "fro")), 6),
    "cross_F": round(float(np.linalg.norm(crossB, "fro")), 6),
    "dissipative_F": round(float(np.linalg.norm(disB, "fro")), 6),
    "total_F": round(float(np.linalg.norm(totB, "fro")), 6),
    "declared": {"chiral": 0.700000, "dissipative": 0.128689,
                 "cross": 0.430888, "total": 0.886454},
    "chiral_su3": su3_split(chiB, rho1B),
    "dissipative_su3": su3_split(disB, rho1B),
    "cross_su3": su3_split(crossB, rho1B),
    "total_su3": su3_split(totB, rho1B),
    "chiral_off_orbit_residual": round(resid_chi, 9),
    "total_off_orbit_residual": round(resid_tot, 9),
    "verdicts": {
        "chiral_0.700": bool(abs(np.linalg.norm(chiB, "fro") - 0.700) < 5e-3),
        "dissipative_0.128689": bool(abs(np.linalg.norm(disB, "fro") - 0.128689) < 5e-3),
        "cross_0.430888": bool(abs(np.linalg.norm(crossB, "fro") - 0.430888) < 5e-3),
        "total_0.886454": bool(abs(np.linalg.norm(totB, "fro") - 0.886454) < 5e-3),
        "chiral_zero_off_orbit": bool(resid_chi < 1e-9),
    },
}

# the growing 0.176 at t=0.25: total O(t^2)-only coefficient vs the
# full finite-t difference/t^2 -- quick check at t=0.25
from scipy.linalg import expm
L0f = LH0 + D0
L1f = LH1 + D1
t = 0.25
r01 = (expm(L0f * t) @ rhoA.reshape(-1, order="F")).reshape(D3, D3, order="F")
r01 = (expm(L1f * t) @ r01.reshape(-1, order="F")).reshape(D3, D3, order="F")
r10 = (expm(L1f * t) @ rhoA.reshape(-1, order="F")).reshape(D3, D3, order="F")
r10 = (expm(L0f * t) @ r10.reshape(-1, order="F")).reshape(D3, D3, order="F")
d01 = partial_trace_site(r01 - r10, 1)
R["seed_A_t0.25_diff_over_t2"] = {
    "site1_diff_over_t2_F": round(float(np.linalg.norm(d01, "fro")) / t ** 2, 6),
    "declared": 0.176,
    "verdict": "PASS" if abs(float(np.linalg.norm(d01, "fro")) / t ** 2
                             - 0.176) < 5e-3 else "CHECK",
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r51d_preflight2.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("seed A |+1,+1,0>: chiral", R["seed_A_+1+10"]["chiral_F"],
      "cross", R["seed_A_+1+10"]["cross_F"],
      "diss", R["seed_A_+1+10"]["dissipative_F"],
      "decl", 0.147915)
print("  diss su3:", R["seed_A_+1+10"]["dissipative_su3"])
print("seed A t=0.25 diff/t^2:", R["seed_A_t0.25_diff_over_t2"])
print("identity C5 err:", R["identity_C5_product"]["max_err_over_6_trials"])
print("seed B |+x,+x,+z>:", json.dumps(R["seed_B_+x+x+z"]["verdicts"]))
print("  chiral su3:", R["seed_B_+x+x+z"]["chiral_su3"])
print("  diss su3:", R["seed_B_+x+x+z"]["dissipative_su3"])
print("  cross su3:", R["seed_B_+x+x+z"]["cross_su3"])
print("  total su3:", R["seed_B_+x+x+z"]["total_su3"])
print("  chiral off-orbit residual:", R["seed_B_+x+x+z"]["chiral_off_orbit_residual"])
