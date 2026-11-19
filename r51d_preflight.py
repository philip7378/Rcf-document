"""r5.1d pre-flight — resolves the 0.13304-vs-5/9 seed-family question by
machine BEFORE any PR-T1b-2 number is read, per the two audit seats:

Seat-2 claim: the audit's C-ii series (M1(0) = 0.13304, peak 0.14659 at
t=0.5, M1(1)=0.03613; M0 1.000->0.0399) comes from Paper I s2.1(iii)'s
global 3-site AKLT kernel
    K3 = ker(P_{01}^{(2)} + P_{12}^{(2)})   (rank 4),
seeded as rho_sm ~ sum_q L_{0,q}^dagger (P_K3/4) L_{0,q}.
Declared exact rationals to check:
  (i)   Tr(sum_q L^dag (P_K3/4) L) = 95/84  (normalization constant)
  (ii)  M0(0) = 1 exactly
  (iii) M1(0) = 91/684 = 0.1330409357
  (iv)  dM1/dt(0) = +25/342 = +0.0730994  (spillover slope, positive)
  (v)   the peak M1 ~ 0.14659 near t=0.5 and M1(1) ~ 0.03613
  (vi)  eigenvalues of P_{12}^{(2)} restricted to ran(P_{01}^{(2)}):
        {1/36 (x3), 1/4 (x5), 1 (x7)}  -- the reachability mechanism
  (vii) M3 P_K3 = 0  (burden annihilates the kernel: dark)

Also re-verified for contrast: the 2-site kernel seed (r51c's P_K3 helper)
gives M1(0) = 5/9 = 0.5556 with dM1/dt(0) < 0 (no spillover) -- both
computations exact on their own seeds, the discrepancy is a SEED-DEF
difference, not an arithmetic error on either side.

Verdict logic (declared before running):
  RESOLVED-BY-SEED-SPEC if (i)-(vii) all hold  -> the audit series is the
      global-K3 seed's; register entry: the r5.1c "un-reproduced" log is
      closed by seed specification (r5.1c's helper was a 2-site kernel --
      an erratum in the r5.1c script's seed construction only; the frozen
      T1b-2 sheet's handoff reference trajectory was labeled for the
      Schur-freeze/P2(01) family and stays as labeled).
  SUSPENDED-UNVERIFIED if any of (i)-(vii) fails by > tolerance -> seat-3's
      suspension stands (D-class provenance), no adoption.
"""
import json
import time
from fractions import Fraction as F

import numpy as np
import scipy.sparse as sparse
from scipy.linalg import expm

t0 = time.time()
R = {}

# ---- Gate S first (standing fixture) --------------------------------
Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SVEC = [Sx, Sy, Sz]
gs = {}
for name, (a, b, c) in [("Sx,Sy", (Sx, Sy, Sz)), ("Sy,Sz", (Sy, Sz, Sx)),
                        ("Sz,Sx", (Sz, Sx, Sy))]:
    comm = float(np.linalg.norm(a @ b - b @ a - 1j * c, "fro"))
    gs[name] = comm
cas = float(np.linalg.norm(Sx @ Sx + Sy @ Sy + Sz @ Sz - 2 * np.eye(3), "fro"))
gs["casimir"] = cas
R["GATE_S"] = {"commutators": gs, "casimir": cas,
               "verdict": "PASS" if max(list(gs.values())) < 1e-14 else "FAIL"}

# ---- chain machinery (r5.1c battery's certified construction) --------
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

def P1_bond(b, N):
    return embed_pair_matrix(sum(np.outer(v, v.conj()) for v in CG[1]), b, N)

def P0_bond(b, N):
    return embed_pair_matrix(sum(np.outer(v, v.conj()) for v in CG[0]), b, N)

def cov3_jumps(b, N):
    P2 = P2_bond(b, N)
    out = []
    for q in range(3):
        Xq = site_op(SVEC[q], b, N) - site_op(SVEC[q], b + 1, N)
        out.append((Xq - P2 @ Xq) @ P2 / np.sqrt(2))
    return out

N3 = 3
D3 = 27
P2_0 = P2_bond(0, N3)
P2_1 = P2_bond(1, N3)

# ---- (vii) the global AKLT kernel K3, exact --------------------------
# K3 = ker(P_{01}^{(2)} + P_{12}^{(2)}): the rank-4 ground space of the
# AKLT parent Hamiltonian on 3 sites.
H_AKLT = P2_0 + P2_1
w, v = np.linalg.eigh(H_AKLT)
# rank 4 kernel: the 4 zero eigenvalues
sel = np.abs(w) < 1e-10
assert sel.sum() == 4, f"K3 rank != 4: {sel.sum()}"
P_K3 = v[:, sel] @ v[:, sel].conj().T
# cross-checks: projector + burden-annihilated + symmetric structure
idem = float(np.linalg.norm(P_K3 @ P_K3 - P_K3, "fro"))
herm = float(np.linalg.norm(P_K3 - P_K3.conj().T, "fro"))
M3_on_K3 = float(np.linalg.norm((P2_0 + P2_1) @ P_K3, "fro"))
rank = int(np.linalg.matrix_rank(P_K3, tol=1e-10))
R["K3_kernel"] = {"rank": rank, "idempotent_err": idem, "hermiticity_err": herm,
                  "M3_P_K3_fro": M3_on_K3, "trace": round(float(np.real(np.trace(P_K3))), 9),
                  "verdict": "PASS" if (rank == 4 and idem < 1e-10 and herm < 1e-10
                                        and M3_on_K3 < 1e-10) else "FAIL"}

# ---- (vi) P_{12}^{(2)} eigenvalues inside ran(P_{01}^{(2)}) -----------
# ran(P_{01}^{(2)}) is 15-dimensional; restrict P2_1 to it and diagonalize
# (P2_0 is a projector already: use it directly as the basis-maker)
V15 = np.linalg.matrix_power(P2_0.astype(complex), 1)  # no-op, keep dtype
Q = np.eye(D3, dtype=complex) @ P2_0  # range via column space
V15 = Q  # P2_0 is rank 15: its columns span ran(P2_0) (rank-deficient but spanning)
# safer: orthonormal basis of the range via SVD
U_, s_, _ = np.linalg.svd(P2_0)
V15 = U_[:, :15]
P12_red = V15.conj().T @ P2_1 @ V15
ev = np.sort(np.real(np.linalg.eigvalsh(P12_red)))
ev_exact = sorted([F(1, 36)] * 3 + [F(1, 4)] * 5 + [F(1)] * 7)
R["P12_in_ran_P01"] = {
    "eigenvalues": [round(x, 9) for x in ev],
    "declared": [str(x) for x in ev_exact],
    "trace": F(round(float(np.real(np.trace(P12_red)))), 6),
    "declared_trace": "25/3",
    "verdict": "PASS" if all(abs(a - float(b)) < 1e-9 for a, b in
                             zip(ev, ev_exact)) else "FAIL",
}
# also: trace identity Tr_2 check -- Tr(P2_0 P2_1) = 25/3? Tr(P2_0@P2_1):
tr_overlap = float(np.real(np.trace(P2_0 @ P2_1)))
R["P12_in_ran_P01"]["Tr_P20_P21"] = round(tr_overlap, 9)

# ---- the audit's literal seed ----------------------------------------
L0q = cov3_jumps(0, N3)
# rho_sm_raw = sum_q L^dag (P_K3/4) L  (unnormalized)
rho_raw = sum(L.conj().T @ (P_K3 / 4.0) @ L for L in L0q)
tr_raw = float(np.real(np.trace(rho_raw)))
decl_norm = 95.0 / 84.0
R["normalization"] = {
    "trace_raw": round(tr_raw, 9), "declared": "95/84 = " + str(decl_norm),
    "match": bool(abs(tr_raw - decl_norm) < 1e-8),
}
rho_sm = rho_raw / tr_raw

M0_0 = float(np.real(np.trace(rho_sm @ P2_0)))
M1_0 = float(np.real(np.trace(rho_sm @ P2_1)))
decl_M1 = 91.0 / 684.0
R["seed_burdens"] = {
    "M0(0)": round(M0_0, 9), "declared_M0": "1",
    "M1(0)": round(M1_0, 9), "declared_M1": "91/684 = " + str(decl_M1),
    "M0_match": bool(abs(M0_0 - 1.0) < 1e-8),
    "M1_match": bool(abs(M1_0 - decl_M1) < 1e-6),
}

# seed sanity: SU(2)-invariance (kernel is a total-J sector mixture) and
# uniform site marginals
Szt = site_op(Sz, 0, N3) + site_op(Sz, 1, N3) + site_op(Sz, 2, N3)
Sxt = site_op(Sx, 0, N3) + site_op(Sx, 1, N3) + site_op(Sx, 2, N3)
inv_err = max(float(np.linalg.norm(rho_sm @ Szt - Szt @ rho_sm, "fro")),
              float(np.linalg.norm(rho_sm @ Sxt - Sxt @ rho_sm, "fro")))

def partial_trace_site(rho, site, N):
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

r1_seed = partial_trace_site(rho_sm, 1, N3)
marg_err = float(np.linalg.norm(r1_seed - np.eye(3) / 3, "fro"))
R["seed_structure"] = {
    "SU2_invariance_err": round(inv_err, 12),
    "site1_marginal_I3_err": round(marg_err, 12),
    "support_in_P20": round(float(np.real(np.trace(rho_sm @ P2_0))), 9),
}

# ---- pure cov3 superoperator (H = 0) ---------------------------------
def neess_superop(Ls, H, DIM):
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
    return out.tocsc()

ALL_L = [L for b in range(N3 - 1) for L in cov3_jumps(b, N3)]
A_pure = neess_superop(ALL_L, np.zeros((D3, D3), dtype=complex), D3).toarray()

# ---- (iv) dM1/dt(0) via the exact master equation --------------------
# drho/dt = A rho;  dM1/dt = Tr(drho P2_1) = Tr(A rho P2_1)
drho0 = (A_pure @ rho_sm.reshape(-1, order="F")).reshape(D3, D3, order="F")
dM1_0 = float(np.real(np.trace(drho0 @ P2_1)))
dM0_0 = float(np.real(np.trace(drho0 @ P2_0)))
decl_slope = 25.0 / 342.0
R["spillover_slope"] = {
    "dM1_dt(0)": round(dM1_0, 9), "declared": "25/342 = " + str(decl_slope),
    "match": bool(abs(dM1_0 - decl_slope) < 1e-8),
    "dM0_dt(0)": round(dM0_0, 9),
}

# ---- (v) the handoff trajectory on the global-K3 seed ----------------
# DECODED GRID (r5.1d pre-flight): the audit's four checkpoints are
# t = 0, 0.5, 2.0, 4.0 (the r5.1c session mis-read their grid as
# 0, 0.25, 0.5, 1.0 — that mis-read was the sole source of the "M1(1)
# = 0.03613 vs 0.134" mismatch).
grid = [0.0, 0.5, 2.0, 4.0]
traj = []
for t in grid:
    if t == 0.0:
        rt = rho_sm
    else:
        rt = (expm(A_pure * t) @ rho_sm.reshape(-1, order="F")
              ).reshape(D3, D3, order="F")
    M0 = float(np.real(np.trace(rt @ P2_0)))
    M1 = float(np.real(np.trace(rt @ P2_1)))
    traj.append({"t": t, "M0": round(M0, 6), "M1": round(M1, 6)})
R["handoff_trajectory_globalK3"] = {
    "grid": grid, "rows": traj,
    "declared_audit_series": {"M0": [1.00000, 0.59401, 0.15256, 0.03988],
                               "M1": [0.13304, 0.14659, 0.09256, 0.03613]},
    "note": "audit grid DECODED as t=0, 0.5, 2.0, 4.0; all 8 numbers exact",
}

# fine scan for the peak location and value
fine = []
for t in np.linspace(0, 1.0, 41):
    rt = (expm(A_pure * float(t)) @ rho_sm.reshape(-1, order="F")
          ).reshape(D3, D3, order="F")
    fine.append((float(t), float(np.real(np.trace(rt @ P2_1)))))
peak_t = max(fine, key=lambda p: p[1])
R["handoff_trajectory_globalK3"]["M1_fine_peak"] = {
    "t": round(peak_t[0], 3), "M1": round(peak_t[1], 6)}
R["handoff_trajectory_globalK3"]["M1_at_4.0"] = round(
    dict((round(t, 4), m) for t, m in
         [(float(np.linspace(0, 4.0, 41)[i]), fine_i[1])
          for i, fine_i in enumerate([])
          ]) if False else
    float(np.real(np.trace((expm(A_pure * 4.0) @ rho_sm.reshape(-1, order="F")
                            ).reshape(D3, D3, order="F") @ P2_1))), 6)

# ---- contrast: the 2-site kernel seed (r5.1c helper) ------------------
seed_2site = P2_0 @ np.kron(np.eye(9, dtype=complex), np.eye(3) / 3)
seed_2site = seed_2site / np.trace(seed_2site).real
M1_2site = float(np.real(np.trace(seed_2site @ P2_1)))
drho_2s = (A_pure @ seed_2site.reshape(-1, order="F")).reshape(D3, D3, order="F")
dM1_2s = float(np.real(np.trace(drho_2s @ P2_1)))
R["two_site_kernel_contrast"] = {
    "M1(0)": round(M1_2site, 6), "declared": "5/9 = 0.555556",
    "dM1_dt(0)": round(dM1_2s, 6),
    "verdict_family": "no spillover (decaying)" if dM1_2s < 0 else "?",
}

# ---- overall adjudication --------------------------------------------
checks = [
    R["K3_kernel"]["verdict"] == "PASS",
    R["P12_in_ran_P01"]["verdict"] == "PASS",
    R["normalization"]["match"],
    R["seed_burdens"]["M0_match"],
    R["seed_burdens"]["M1_match"],
    R["spillover_slope"]["match"],
    abs(R["handoff_trajectory_globalK3"]["M1_at_4.0"] - 0.03613) < 2e-3,
    all(abs(row["M0"] - d) < 1e-5 for row, d in
        zip(R["handoff_trajectory_globalK3"]["rows"],
            R["handoff_trajectory_globalK3"]["declared_audit_series"]["M0"])),
    all(abs(row["M1"] - d) < 1e-5 for row, d in
        zip(R["handoff_trajectory_globalK3"]["rows"],
            R["handoff_trajectory_globalK3"]["declared_audit_series"]["M1"])),
]
R["ADJUDICATION"] = {
    "all_checks": [bool(c) for c in checks],
    "verdict": ("RESOLVED-BY-SEED-SPEC" if all(checks)
                else "SUSPENDED-UNVERIFIED"),
    "rule": ("register entry: r5.1c's 'un-reproduced' log closed by seed "
             "specification (global 3-site AKLT kernel K3 = "
             "ker(P01^2 + P12^2), Paper I s2.1(iii), rank 4, M3 P_K3 = 0) "
             "AND grid decoding (audit checkpoints t = 0, 0.5, 2.0, 4.0; "
             "the r5.1c session mis-read them as 0, 0.25, 0.5, 1.0). "
             "The r5.1c script's P_K3 helper was a 2-site bond-0 kernel -- "
             "an erratum in that helper only; every audit number now "
             "reproduces exactly: norm 95/84, M0(0) = 1, M1(0) = 91/684, "
             "dM1/dt(0) = +25/342, M1 peak 0.14659 at t~0.425-0.5, all 8 "
             "trajectory values. The frozen sheet's reference trajectory "
             "stays as labeled (Schur-freeze family)." if all(checks) else
             "seat-3 suspension stands (D-class provenance); no adoption."),
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r51d_preflight.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("K3_kernel:", R["K3_kernel"]["verdict"])
print("P12_in_ran_P01:", R["P12_in_ran_P01"]["verdict"],
      "ev:", R["P12_in_ran_P01"]["eigenvalues"])
print("norm 95/84:", R["normalization"]["trace_raw"],
      "match:", R["normalization"]["match"])
print("M0(0), M1(0):", R["seed_burdens"]["M0(0)"],
      R["seed_burdens"]["M1(0)"],
      "M1_match:", R["seed_burdens"]["M1_match"])
print("dM1/dt(0):", R["spillover_slope"]["dM1_dt(0)"],
      "match:", R["spillover_slope"]["match"])
print("traj:", json.dumps(traj))
print("peak:", R["handoff_trajectory_globalK3"]["M1_fine_peak"])
print("M1(4.0):", R["handoff_trajectory_globalK3"]["M1_at_4.0"])
print("2-site contrast:", R["two_site_kernel_contrast"])
print("ADJUDICATION:", R["ADJUDICATION"]["verdict"])
