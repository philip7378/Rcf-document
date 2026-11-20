"""r5.3 pre-flight B part 2 — structural characterization of the graph
kernels (triangle / star / tetrahedron) to adjudicate the seat's No-Go
VIII table against my replication failure.

My pre-flight B (r53_preflightB.py, cross-checked by eigvalsh AND
scipy null_space with per-vector residuals ~5e-15) found:
  triangle K3 ker 4 (seat: 1); square C4 ker 4 (seat: 1);
  star K13 ker 36 (seat: 0, lmin 0.152873); star K14 ker 108 (seat: 0);
  tetra K4 ker 4 (seat: 0, lmin 5/3).
The open-chain N=4 row AGREES (ker 4), and that same P_PAIR reproduces
the certified r5.1d/r5.2 kernel. So the construction is sound where
the seat agrees, and the disagreement is on the z>=2 loop / z>=3 rows.

This script characterizes MY kernels structurally:
  T1  triangle kernel: total-J^2 decomposition (expect the global
      singlet + a J=1 multiplet -> dim 4 = 1 + 3).
  T2  star K13 kernel: site-0 support rank (expect rank 3 -> the
      kernel is NOT visible to a single-site constraint: the center
      site stays mixed; the kernel is an entangled sector).
  T3  the seat's lambda_min values (0.152873, 0.313859): search MY
      spectra for these numbers (maybe they are the lowest NONZERO
      eigenvalue of MY M_G — i.e., the seat reported lambda_min of
      the kernel COMPLEMENT, or of a different operator).
  T4  the 5/3 for the tetrahedron: search my tetra spectrum for 5/3
      (my lowest nonzero was 0.66757; is 5/3 present anywhere?).
"""
import json

import numpy as np
from scipy.linalg import null_space

R = {}

def cg():
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

CG = cg()
P2 = sum(np.outer(v, v.conj()) for v in CG[2])
S1 = [np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2),
      np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2),
      np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)]

def emb(pair9, i, j, N):
    if j < i:
        i, j = j, i
    L = np.eye(3 ** i, dtype=complex)
    M_ = np.eye(3 ** (j - i - 1), dtype=complex)
    R_ = np.eye(3 ** (N - j - 1), dtype=complex)
    return np.kron(np.kron(np.kron(L, pair9), M_), R_)

def tot(op, site, N):
    ops = [np.eye(3, dtype=complex)] * N
    ops[site] = op
    out = ops[0]
    for o in ops[1:]:
        out = np.kron(out, o)
    return out

# ---- T1: triangle kernel total-J decomposition ----------------------
N = 3
Mt = emb(P2, 0, 1, N) + emb(P2, 1, 2, N) + emb(P2, 2, 0, N)
ns = null_space(Mt, rcond=1e-12)
J2tot = sum(sum(tot(S1[q], s, N) @ tot(S1[q], s2, N)
                for q in range(3)) for s in range(N) for s2 in range(N))
Jker = ns.conj().T @ J2tot @ ns
ev = np.sort(np.round(np.linalg.eigvalsh(Jker).real, 9))
resid = max(float(np.linalg.norm(Mt @ ns[:, k])
                  / np.linalg.norm(ns[:, k])) for k in range(ns.shape[1]))
R["T1_triangle"] = {
    "kernel_dim": int(ns.shape[1]),
    "total_J2_eigenvalues": ev.tolist(),
    "reading": "J(J+1) in {0,2,6,12}: " + ", ".join(
        f"J={jj}" for jj, v in {0: 0, 1: 2, 2: 6, 3: 12}.items()
        if any(abs(x - v) < 1e-6 for x in [float(y) for y in ev])),
    "max_residual": resid,
}

# ---- T2: star K13 kernel, site-0 support ----------------------------
N = 4
Mst = emb(P2, 0, 1, N) + emb(P2, 0, 2, N) + emb(P2, 0, 3, N)
nss = null_space(Mst, rcond=1e-12)
rho_sum = sum(np.outer(nss[:, k], nss[:, k].conj())
              for k in range(nss.shape[1]))
T2m = rho_sum.reshape(3, 27, 3, 27)  # (site0, sites123 | site0', sites123')
rho_s0 = np.einsum("abac->bc", T2m)
w0 = np.linalg.eigvalsh(rho_s0).real
R["T2_star_K13"] = {
    "kernel_dim": int(nss.shape[1]),
    "site0_support_eigs": np.round(w0, 6).tolist(),
    "site0_rank": int((w0 > 1e-10).sum()),
    "note": ("the star kernel is an entangled sector; the center site "
             "stays full-rank mixed — no single-site obstruction"),
}

# ---- T3: search my spectra for the seat's lambda_min values ---------
def spectrum_search(name, M, targets):
    w = np.sort(np.linalg.eigvalsh(M).real)
    out = {}
    for tgt in targets:
        near = w[np.abs(w - tgt) < 5e-6]
        out[str(tgt)] = {"count": int(len(near)),
                         "closest": float(w[np.argmin(np.abs(w - tgt))])}
    return {"dim": M.shape[0], "ker": int((np.abs(w) < 1e-9).sum()),
            "lowest_nonzero": float(w[np.abs(w) > 1e-9][0]) if (np.abs(w) > 1e-9).any() else None,
            "target_hits": out}

N = 4
Mst = emb(P2, 0, 1, N) + emb(P2, 0, 2, N) + emb(P2, 0, 3, N)
R["T3_star_K13_spectrum"] = spectrum_search("star13", Mst, [0.152873])
N = 5
Mst4 = emb(P2, 0, 1, N) + emb(P2, 0, 2, N) + emb(P2, 0, 3, N) + emb(P2, 0, 4, N)
R["T3_star_K14_spectrum"] = spectrum_search("star14", Mst4, [0.313859])
N = 4
Mt4 = sum(emb(P2, i, j, N)
          for i, j in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
R["T3_tetra_spectrum"] = spectrum_search("tetra", Mt4, [5 / 3])

# ---- T4: what ARE the seat's numbers? -------------------------------
# 0.152873 and 0.313859: ratio test
if R["T3_star_K13_spectrum"]["target_hits"]["0.152873"]["count"] == 0:
    # not in the star spectrum; test the hypothesis that the seat used
    # P^(2) = the J=2 projector on a DIFFERENT embedding: e.g. their
    # pair projector REPLACED by S_i . S_j (whose eigenvalues are
    # {1, 0, -2} on J = {2, 1, 0}): M_G = sum (S_i . S_j + 2)/3 ->
    # same kernel as mine. Or S_i.S_j itself: spectrum shifts.
    def pair_ss(i, j, N):
        SS = sum(np.kron(S1[q], S1[q]) for q in range(3))
        return emb(SS, i, j, N)
    Ms = pair_ss(0, 1, 4) + pair_ss(0, 2, 4) + pair_ss(0, 3, 4)
    w = np.sort(np.linalg.eigvalsh(Ms).real)
    R["T4_alt_SdotS_star13"] = {
        "lowest": float(w[0]),
        "hits_0.152873": int(np.sum(np.abs(w - 0.152873) < 5e-6)),
        "ker(dim of S.S eigenvalue -2 space? count of w<-1.999)": int(np.sum(w < -1.999)),
    }
    # S.S + 2*Id scale/3: eigenvalues of S.S on J sectors: J=2 -> 1,
    # J=1 -> 0... wait S_i.S_j eigs: J=2: 1, J=1: 0, J=0: -2. So
    # (S.S+2)/3 has eigs {1, 2/3, 0}: kernel = J=0 pair sector only —
    # STRICTER than mine (J<=1). THAT could be the seat's constraint:
    # singlet-only pair projector! Test ker dim for star under it.
    Mss = sum(pair_ss(0, k, 4) for k in (1, 2, 3)) + 2 * np.eye(81)
    wss = np.sort(np.linalg.eigvalsh(Mss).real)
    R["T4_singlet_only_star13"] = {
        "ker(S.S+2 = 0 <=> all pairs J=0)": int(np.sum(np.abs(wss) < 1e-9)),
    }

with open("/home/z/my-project/scripts/r53_preflightB2.json", "w") as f:
    json.dump(R, f, indent=2, default=str)
print(json.dumps(R, indent=1))
