"""r5.1 certificate battery — executes the pre-registered checks in
pr_r51_certificates_sheet.txt. Exact arithmetic (Fraction) throughout the
PR-SCALE / PR-DIM / PR-T1b algebra; float only where declared (logs,
boundary approach, NESS solve). Results frozen to r51_certificates.json
and compared line-by-line against the sheet.

Blocks:
  PR-SCALE-1  two-frame cubic invariant certificate (8 sign frames)
  PR-SCALE-2  log-volume Hessian: PSD grid, boundary degeneration, strata
  PR-DIM-1    tier-3 structural vs frame-rank state-dependence
  PR-T1b      Lie-on-Jordan derivation / automorphism / non-inverse
  PR-NOGO-RAW N=4 cov3 NESS raw-clock probe dependence (XXX vs XY)
"""
import json
import time
from fractions import Fraction as F

import numpy as np

t0 = time.time()
R = {}

# =====================================================================
# PR-SCALE-1 — 8 sign frames at magnitude (1/2,1/2,1/2)
# =====================================================================
frames = []
for sa in (1, -1):
    for sb in (1, -1):
        for sc in (1, -1):
            a, b, c = F(sa, 2), F(sb, 2), F(sc, 2)
            C = [[F(1), a, b], [a, F(1), c], [b, c, F(1)]]
            frames.append((a, b, c, C))

def det3(C):
    (a11, a12, a13), (a21, a22, a23), (a31, a32, a33) = C
    return (a11 * (a22 * a33 - a23 * a32)
            - a12 * (a21 * a33 - a23 * a31)
            + a13 * (a21 * a32 - a22 * a31))

def exact_rank(C, det):
    """Rank by exact Gaussian elimination on Fractions."""
    M = [row[:] for row in C]
    n, rank, piv = 3, 0, 0
    for col in range(n):
        # find pivot
        piv_row = None
        for r_ in range(piv, n):
            if M[r_][col] != 0:
                piv_row = r_
                break
        if piv_row is None:
            continue
        M[piv], M[piv_row] = M[piv_row], M[piv]
        inv = M[piv][col]
        M[piv] = [x / inv for x in M[piv]]
        for r_ in range(n):
            if r_ != piv and M[r_][col] != 0:
                f = M[r_][col]
                M[r_] = [x - f * y for x, y in zip(M[r_], M[piv])]
        piv += 1
        rank += 1
    return rank

s1 = []
kmultisets = set()
for a, b, c, C in frames:
    d = det3(C)
    rk = exact_rank(C, d)
    K = sorted([a * a, b * b, c * c])  # K_ij = c_ij^2
    kmultisets.add(tuple(K))
    s1.append({
        "frame": f"({a} {b} {c})",
        "K_multiset": [str(x) for x in K],
        "det": str(d),
        "rank": rk,
    })
dets = {det3(C) for (_a, _b, _c, C) in frames}
ranks = {e["rank"] for e in s1}
S1_PASS = (len(kmultisets) == 1 and dets == {F(1, 2), F(0)}
           and ranks == {3, 2})
R["PR-SCALE-1"] = {
    "frames": s1,
    "unique_K_multiset": len(kmultisets) == 1,
    "det_values": sorted(str(x) for x in dets),
    "rank_values": sorted(ranks),
    "verdict": "PASS" if S1_PASS else "FAIL",
}

# =====================================================================
# PR-SCALE-2 — log-volume Hessian on the affine slice
# =====================================================================
def hessian_exact(a, b, c):
    """Exact H_ij = (D_i D_j - D D_ij) / D^2 of Phi = -ln det C."""
    D = 1 - (a * a + b * b + c * c) + 2 * a * b * c
    Da, Db, Dc = 2 * (b * c - a), 2 * (a * c - b), 2 * (a * b - c)
    Dg = {"a": Da, "b": Db, "c": Dc}
    H2 = {("a", "a"): F(-2), ("a", "b"): F(2) * c, ("a", "c"): F(2) * b,
          ("b", "a"): F(2) * c, ("b", "b"): F(-2), ("b", "c"): F(2) * a,
          ("c", "a"): F(2) * b, ("c", "b"): F(2) * a, ("c", "c"): F(-2)}
    keys = ("a", "b", "c")
    H = {}
    for i in keys:
        for j in keys:
            H[(i, j)] = (Dg[i] * Dg[j] - D * H2[(i, j)]) / (D * D)
    return D, H

def sylvester_psd(H):
    """All principal minors (Sylvester) > 0 -> SPD. Exact."""
    keys = ("a", "b", "c")
    m1 = [H[(i, i)] for i in keys]
    m2 = [H[(i, i)] * H[(j, j)] - H[(i, j)] * H[(j, i)]
          for i, j in ((("a", "b")), (("a", "c")), (("b", "c")))]
    m3 = (H[("a", "a")] * (H[("b", "b")] * H[("c", "c")] - H[("b", "c")] ** 2)
          - H[("a", "b")] * (H[("a", "b")] * H[("c", "c")] - H[("b", "c")] * H[("a", "c")])
          + H[("a", "c")] * (H[("a", "b")] * H[("b", "c")] - H[("b", "b")] * H[("a", "c")]))
    return all(x > 0 for x in m1) and all(x > 0 for x in m2) and m3 > 0

GRID = [(F(1, 4), F(1, 4), F(1, 4)), (F(1, 2), F(1, 2), F(1, 2)),
        (F(1, 2), F(1, 3), F(1, 4)), (F(2, 5), F(1, 5), F(1, 10)),
        (F(3, 10), F(1, 5), F(1, 10))]
grid_report = []
all_spd = True
for (a, b, c) in GRID:
    # certify the frame itself SPD: 1-a^2>0 etc. and det>0
    spd_frame = (1 - a * a > 0 and 1 - b * b > 0 and 1 - c * c > 0)
    D, H = hessian_exact(a, b, c)
    spd_frame = spd_frame and D > 0
    spd_H = sylvester_psd(H)
    all_spd = all_spd and spd_frame and spd_H
    grid_report.append({
        "point": f"({a},{b},{c})",
        "det": str(D),
        "frame_spd": bool(spd_frame),
        "H_spd": bool(spd_H),
    })
R["PR-SCALE-2_i_PSD_grid"] = {
    "grid": grid_report, "all_spd": bool(all_spd),
    "verdict": "PASS" if all_spd else "FAIL",
}

# ---- boundary degeneration along (t, t, -t)
path = [F(2, 5), F(9, 20), F(49, 100), F(499, 1000)]
bdry = []
phi_prev, lam_prev = None, None
mono_phi, mono_lam = True, True
for t in path:
    D, H = hessian_exact(t, t, -t)
    phi = float(-np.log(float(D)))
    Hf = np.array([[float(H[(i, j)]) for j in ("a", "b", "c")]
                   for i in ("a", "b", "c")], dtype=float)
    lam = float(np.linalg.eigvalsh(Hf)[-1])
    if phi_prev is not None:
        mono_phi = mono_phi and (phi > phi_prev)
        mono_lam = mono_lam and (lam > lam_prev)
    bdry.append({"t": str(t), "D": str(D), "Phi": round(phi, 6),
                 "lambda_max": round(lam, 6)})
    phi_prev, lam_prev = phi, lam
D_declared = [F(49, 125), F(841, 4000), F(44402, 1000000), F(4494002, 1000000000)]
D_actual = [F(e["D"]) for e in bdry]
R["PR-SCALE-2_ii_boundary"] = {
    "path": bdry,
    "D_matches_declared": D_actual == D_declared,
    "Phi_monotone_up": bool(mono_phi),
    "lambda_max_monotone_up": bool(mono_lam),
    "verdict": "PASS" if (D_actual == D_declared and mono_phi and mono_lam) else "FAIL",
}

# ---- strata complementarity
Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SP = [Sx, Sy, Sz]

def frame_of(rho):
    cov = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(rho @ (SP[i] @ SP[j] + SP[j] @ SP[i]) / 2))
            means = np.real(np.trace(rho @ SP[i])) * np.real(np.trace(rho @ SP[j]))
            cov[i, j] = corr - means
    return cov

def rank_det(cov):
    """Rank + non-zero-eigenvalue product of the frame matrix."""
    ev = np.linalg.eigvalsh(cov)
    pos = ev[ev > 1e-12]
    rk = int(len(pos))
    det = float(np.prod(pos)) if rk else 0.0
    return rk, det

strata = {}
# qubit: Pauli matrices, 2x2
sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
P = [sx, sy, sz]
def q_frame(rho):
    cov = np.zeros((3, 3))
    for i in range(3):
        for j in range(3):
            corr = np.real(np.trace(rho @ (P[i] @ P[j] + P[j] @ P[i]) / 2))
            means = np.real(np.trace(rho @ P[i])) * np.real(np.trace(rho @ P[j]))
            cov[i, j] = corr - means
    return cov
def to_zero_complex(v):
    v = np.array(v, dtype=complex)
    v[np.abs(v) < 1e-12] = 0
    return v

qubit = {}
ket0 = np.array([1, 0], dtype=complex)
ketp = np.array([1, 1], dtype=complex) / np.sqrt(2)
ketq = np.array([1, 1j], dtype=complex) / np.sqrt(2)
for name, k in (("|0>", ket0), ("|+x>", ketp), ("|+y>", ketq)):
    rho = np.outer(k, k.conj())
    rk, det = rank_det(q_frame(rho))
    qubit["pure " + name] = {"rank": rk, "det": round(det, 12)}
rho = np.diag([F(3, 4).__float__(), 0.25]).astype(complex)
rk, det = rank_det(q_frame(rho))
qubit["mixed diag(3/4,1/4)"] = {"rank": rk, "det": round(det, 12)}
rho = np.eye(2, dtype=complex) / 2
rk, det = rank_det(q_frame(rho))
qubit["fully mixed I/2"] = {"rank": rk, "det": round(det, 12)}

spin1 = {}
for m, name in ((0, "|m=+1>"), (1, "|m=0>"), (2, "|m=-1>")):
    k = np.zeros(3, dtype=complex)
    k[m] = 1
    rho = np.outer(k, k.conj())
    rk, det = rank_det(frame_of(rho))
    spin1["coherent " + name] = {"rank": rk, "det": round(det, 12)}
rho = np.eye(3, dtype=complex) / 3
rk, det = rank_det(frame_of(rho))
spin1["fully mixed I/3"] = {"rank": rk, "det": round(det, 12)}

pure_ok = all(v["rank"] == 2
              for k, v in {**qubit, **spin1}.items() if "pure" in k or "coherent" in k)
mixed_ok = (qubit["mixed diag(3/4,1/4)"]["det"] == 0.75
            and abs(spin1["fully mixed I/3"]["det"] - 8 / 27) < 1e-12
            and qubit["fully mixed I/2"]["det"] == 1.0)
R["PR-SCALE-2_iii_strata"] = {
    "qubit": qubit, "spin1": spin1,
    "pure_stratum_rank2_det0": pure_ok,
    "mixed_strata_full_rank": mixed_ok,
    "verdict": "PASS" if (pure_ok and mixed_ok) else "FAIL",
}

# =====================================================================
# PR-DIM-1 — frame rank per axial state; mixed state det 8/27
# =====================================================================
dim1 = {}
for m, name in ((0, "|+1>"), (1, "|0>"), (2, "|-1>")):
    k = np.zeros(3, dtype=complex)
    k[m] = 1
    rho = np.outer(k, k.conj())
    rk, det = rank_det(frame_of(rho))
    dim1["coherent " + name] = {"rank": rk, "det": round(det, 12)}
rho = np.eye(3, dtype=complex) / 3
rk, det = rank_det(frame_of(rho))
dim1["fully mixed I/3"] = {"rank": rk, "det": round(det, 12)}
R["PR-DIM-1"] = {
    "frames": dim1,
    "coherent_all_rank2": all(v["rank"] == 2 for k, v in dim1.items() if "coherent" in k),
    "mixed_rank3_det_8_27": abs(dim1["fully mixed I/3"]["det"] - 8 / 27) < 1e-12,
}
R["PR-DIM-1"]["verdict"] = ("PASS" if R["PR-DIM-1"]["coherent_all_rank2"]
                             and R["PR-DIM-1"]["mixed_rank3_det_8_27"] else "FAIL")

# =====================================================================
# PR-T1b — Lie-on-Jordan derivation / automorphism / non-inverse
# =====================================================================
import itertools

def jprod(X, Y):
    return (X @ Y + Y @ X) / 2

def lbr(X, Y):
    return X @ Y - Y @ X

TEST = [Sx, Sy, Sz, Sx @ Sy, Sz @ Sx, Sx @ Sy @ Sy @ Sz]
names = ["Sx", "Sy", "Sz", "SxSy", "SzSx", "SxSySySz"]
# hermitize products so the space is the self-adjoint algebra
TEST = [(X + X.conj().T) / 2 for X in TEST]

max_dev = 0.0
for A, B, C in itertools.combinations(TEST, 3):
    lhs = lbr(A, jprod(B, C))
    rhs = jprod(lbr(A, B), C) + jprod(B, lbr(A, C))
    max_dev = max(max_dev, float(np.abs(lhs - rhs).max()))
R["PR-T1b_a_derivation"] = {
    "residual": max_dev, "tolerance": 1e-12,
    "verdict": "PASS" if max_dev <= 1e-12 else "FAIL",
}

max_auto = 0.0
from scipy.linalg import expm
for theta in (0.3, 0.7, 1.1):
    u = expm(1j * theta * Sx)
    for B, C in itertools.combinations(TEST, 2):
        aB, aC = u @ B @ u.conj().T, u @ C @ u.conj().T
        lhs = jprod(aB, aC)
        rhs = u @ jprod(B, C) @ u.conj().T
        max_auto = max(max_auto, float(np.abs(lhs - rhs).max()))
R["PR-T1b_b_automorphism"] = {
    "residual": max_auto, "tolerance": 1e-12,
    "verdict": "PASS" if max_auto <= 1e-12 else "FAIL",
}

noninv = 0.0
for A, B, C in itertools.combinations(TEST, 3):
    lhs = jprod(A, lbr(B, C)) - lbr(jprod(A, B), C) - lbr(B, jprod(A, C))
    noninv = max(noninv, float(np.abs(lhs).max()))
R["PR-T1b_c_non_inverse"] = {
    "max_residual": noninv,
    "verdict": "PASS (nonzero as declared)" if noninv > 1e-9 else "FAIL",
}

# =====================================================================
# PR-NOGO-RAW — N=4 cov3 NESS, H_XXX vs H_XY raw clock
# =====================================================================
import scipy.sparse as sparse
import scipy.sparse.linalg as spla

N = 4
DIM = 3 ** N
I3 = np.eye(3, dtype=complex)

def kron_at(op, site, N):
    out = sparse.identity(1, dtype=complex, format="csr")
    for i in range(N):
        out = sparse.kron(out, sparse.csr_matrix(op if i == site else I3), format="csr")
    return out

def bond_op(A, B, b, N):
    out = sparse.identity(1, dtype=complex, format="csr")
    for i in range(N):
        m = sparse.csr_matrix(I3)
        if i == b:
            m = sparse.csr_matrix(A)
        elif i == b + 1:
            m = sparse.csr_matrix(B)
        out = sparse.kron(out, m, format="csr")
    return out

# --- dyads (canonical Def 3.5, as gate-checked last round)
def site_cg_states():
    def sitem(m):
        v = np.zeros(3, dtype=complex)
        v[m + 1] = 1.0
        return v
    def two(m1, m2):
        return np.kron(sitem(m1), sitem(m2))
    J2 = {}
    J2[(2, +2)] = two(+1, +1)
    J2[(2, +1)] = (two(+1, 0) + two(0, +1)) / np.sqrt(2)
    J2[(2, 0)] = (two(+1, -1) + two(-1, +1) + 2 * two(0, 0)) / np.sqrt(6)
    J2[(2, -1)] = (two(-1, 0) + two(0, -1)) / np.sqrt(2)
    J2[(2, -2)] = two(-1, -1)
    J1 = {}
    J1[(1, +1)] = (two(+1, 0) - two(0, +1)) / np.sqrt(2)
    J1[(1, 0)] = (two(+1, -1) - two(-1, +1)) / np.sqrt(2)
    J1[(1, -1)] = (two(0, -1) - two(-1, 0)) / np.sqrt(2)
    return J2, J1

J2S, J1S = site_cg_states()
DYADS_9 = []
for M in (-1, 0, +1):
    L9 = np.outer(J1S[(1, M)], J2S[(2, M)].conj())
    DYADS_9.append(L9)
for M in (+2, -2):
    L9 = np.outer(J1S[(1, int(np.sign(M)))], J2S[(2, M)].conj())
    DYADS_9.append(L9)
P2_9 = sum(np.outer(v, v.conj()) for v in J2S.values())

def embed_pair_op(op9, b, N):
    left = sparse.identity(3 ** b, dtype=complex, format="csr")
    right = sparse.identity(3 ** (N - b - 2), dtype=complex, format="csr")
    return sparse.kron(sparse.kron(left, sparse.csr_matrix(op9), format="csr"),
                       right, format="csr")

GAMMA = 1.0

# Column-stacking convention throughout: vec(AXB) = (B^T kron A) vec(X),
# vec(X) = X.reshape(-1, order='F').
def build_channel():
    Ls = []
    for b in range(N - 1):
        for L9 in DYADS_9:
            Ls.append(np.sqrt(GAMMA) * embed_pair_op(L9, b, N))
    return Ls

def superop(Ls, H):
    """Lindblad superoperator as a matrix acting on vec(rho) (column stacking).

    L(rho) = sum_k L_k rho L_k^dag - 1/2 {L_k^dag L_k, rho} - i [H, rho]
    vec forms:
      L rho L^dag            -> conj(L) kron L
      L^dag L rho            -> I kron (L^dag L)
      rho L^dag L            -> (L^dag L)^T kron I   [Hermitian: = conj(LdL)]
      -i H rho               -> -i (I kron H)
      +i rho H               -> +i (H^T kron I)
    """
    DIM = 3 ** N
    I = sparse.identity(DIM, dtype=complex, format="csr")
    out = sparse.csr_matrix((DIM * DIM, DIM * DIM), dtype=complex)
    for L in Ls:
        Lf = L.toarray()
        LdL = Lf.conj().T @ Lf
        out = out + (sparse.kron(sparse.csr_matrix(Lf.conj()), sparse.csr_matrix(Lf))
                     - 0.5 * sparse.kron(I, sparse.csr_matrix(LdL))
                     - 0.5 * sparse.kron(sparse.csr_matrix(LdL.conj().T), I))
    Hf = H.toarray() if sparse.issparse(H) else np.asarray(H)
    out = out + (-1j * sparse.kron(I, sparse.csr_matrix(Hf))
                 + 1j * sparse.kron(sparse.csr_matrix(Hf.T), I))
    return out.tocsc()

Ls = build_channel()
NESS_REPORT = {}
for tag in ("H_XXX", "H_XY"):
    if tag == "H_XXX":
        Hb = sparse.csr_matrix((DIM, DIM), dtype=complex)
        for b in range(N - 1):
            Hb = Hb + bond_op(Sx, Sx, b, N) + bond_op(Sy, Sy, b, N) + bond_op(Sz, Sz, b, N)
    else:
        Hb = sparse.csr_matrix((DIM, DIM), dtype=complex)
        for b in range(N - 1):
            Hb = Hb + bond_op(Sx, Sx, b, N) + bond_op(Sy, Sy, b, N)
    A = superop(Ls, Hb)
    vals, vecs = spla.eigs(A, k=2, sigma=0, which="LM", tol=1e-11,
                           v0=np.ones(DIM * DIM, dtype=complex))
    # take the eigenpair closest to zero
    pick = int(np.argmin(np.abs(vals)))
    rho_vec = vecs[:, pick]
    rho = rho_vec.reshape(DIM, DIM, order="F")
    rho = (rho + rho.conj().T) / 2
    rho = rho / np.trace(rho)
    rho_vec = rho.reshape(-1, order="F")
    resid = float(np.linalg.norm(A @ rho_vec))
    pos = float(np.linalg.eigvalsh(rho).min())
    Hf = Hb.toarray()
    Mb, Gb = [], []
    for b in range(N - 1):
        P2f = embed_pair_op(P2_9, b, N).toarray()
        Mb.append(float(np.real(np.trace(rho @ P2f))))
        Gb.append(float(np.real(-1j * np.trace(rho @ (P2f @ Hf - Hf @ P2f)))))
    omega = [g / (2 * m) for g, m in zip(Gb, Mb)]
    NESS_REPORT[tag] = {
        "M_b": [round(x, 6) for x in Mb],
        "G_Hb": [round(x, 6) for x in Gb],
        "omega_raw": [round(x, 6) for x in omega],
        "interior_vs_boundary_omega": round(omega[1] / omega[0], 3),
        "stationarity_residual": round(resid, 9),
        "rho_min_eig": round(pos, 12),
        "eigs_picked": float(np.abs(vals[pick])),
        "eigs_other": float(np.abs(vals[1 - pick])),
    }
R["PR-NOGO-RAW"] = NESS_REPORT
exp = {
    "H_XXX": {"M_b": [0.061203, 0.128182, 0.061203],
              "G_Hb": [0.015795, 0.075528, 0.015795],
              "omega_raw": [0.129041, 0.294609, 0.129041]},
    "H_XY": {"M_b": [0.120796, 0.156567, 0.120796],
             "G_Hb": [0.065959, 0.065874, 0.065959],
             "omega_raw": [0.273019, 0.210370, 0.273019]},
}
match = True
for tag, fields in exp.items():
    for k, want in fields.items():
        got = NESS_REPORT[tag][k]
        if any(abs(w - g) > 5e-3 for w, g in zip(want, got)):
            match = False
flip = (NESS_REPORT["H_XXX"]["omega_raw"][1] > NESS_REPORT["H_XXX"]["omega_raw"][0]
        and NESS_REPORT["H_XY"]["omega_raw"][1] < NESS_REPORT["H_XY"]["omega_raw"][0])
R["PR-NOGO-RAW"]["declared_match"] = bool(match)
R["PR-NOGO-RAW"]["sign_flip_confirmed"] = bool(flip)
R["PR-NOGO-RAW"]["verdict"] = "PASS" if (match and flip) else "FAIL"

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r51_certificates.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

# console summary
for k, v in R.items():
    if isinstance(v, dict) and "verdict" in v:
        print(f"{k:32} {v['verdict']}")
print("PR-NOGO-RAW:")
print(json.dumps(NESS_REPORT, indent=2, default=str))
