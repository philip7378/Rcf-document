"""r5.3e VERIFY SCRIPT — the audit's NEW claims on 5ce7601 are
machine-verified BEFORE adoption (standing discipline: no number
enters the register unchecked).

Claims under test:
  T1  Tier-1 Lorentz identity (the audit's E4 tier):
      (a) det(x0*I + s.sig) = x0^2 - |s|^2 on H_2(C);
      (b) X >= 0 cone <=> det >= 0 & x0 >= 0 (forward light cone);
      (c) A in SL(2,C): det(A X A^dag) = det(X) — the SO^+(1,3)
          action, EXACT;
      (d) SU(2) orbit fixes x0 (SO(3) rotations; Rodrigues already
          certified r5.3);
      (e) Hermitian positive A = exp((eta/2) n.sig): the induced
          (x0, s) transform is the exact Lorentz boost of rapidity
          eta along n: ||v' - Lambda(eta) v|| ~ 1e-16 (the audit's
          declared 6.30e-16).
  T2  Bug #11d restated as an operator identity: (SS+I)/2 =
      P^(2) - (1/2) P^(0), with defect (3/2 P^(0))... audit text:
      "spectrum {1, 0, -1/2} = P^(2) - 1/2 P^(0)". Verify the
      identity numerically and the audit's 6.75 form:
      WHICH norm gives 6.75? Candidates:
        (i)  || (3/4) P^(0) ||_F^2 with Tr P^(0) = 12  -> (9/16)*12
             = 6.75  (audit text's own formula)
        (ii) || P_wrong^2 - P_wrong ||_F UNSQUARED with Tr P0 = 81?
             sqrt(81*(9/16)*... )
      My r5.3d machine value: idempotency defect ||P^2-P||_F = 6.75
      on the PAIR (dim 9, Tr P^(0) = 1): ||3/2 P^(0)||_F... no —
      P^2 - P = -(3/4) P^(0) on the 9D pair: ||.||_F^2 = (9/16)*1
      = 0.5625; UNSQUARED = 0.75. On N=6: Tr P^(0) = 81 ->
      unsquared ||.||_F = (3/4)*sqrt(81) = 6.75 EXACT.
      So 6.75 = ||P^2 - P||_F (UNSQUARED) at Tr P^(0) = 81; the
      audit's "(9/16)Tr = 6.75 at Tr 12" is a different object
      (squared norm, wrong trace). REGISTER the disambiguation:
      the AUDIT NUMBER is right only under my reading; under the
      audit's own formula it is 6.75 only if Tr P^(0) = 12 AND
      squared — both cannot hold with the pair projector. Slip
      registered; no load-bearing consequence (the projector
      verdict is unchanged either way).
  T3  112/45 = 2*5*(7/15)*(1-7/15)? audit: "2*5*(7/15)(1-7/15)
      exact for P_{01}^(0)". Check: 2*5*(7/15)*(8/15) = 112/45?
      = 560/225 = 2.4888... = 112/45 = 2.4888... VERIFY.
  T4  Paper I Thm 8 exact decay: <S_z^0 S_z^n>_K = (2/3)^n on the
      AKLT chain (the d_omega distance input PR-LINK-1 will use).
"""
import json
import time

import numpy as np

t0 = time.time()
R = {}

sig1 = np.array([[0, 1], [1, 0]], dtype=complex)
sig2 = np.array([[0, -1j], [1j, 0]], dtype=complex)
sig3 = np.array([[1, 0], [0, -1]], dtype=complex)
SIG = [sig1, sig2, sig3]

rng = np.random.default_rng(7331)

# ---------------- T1: the (1,3) cone inside H_2(C) ------------------
dets, cones, sl2s, su2_fix, boost_err = [], [], [], [], []
for _ in range(200):
    x0 = rng.normal()
    s = rng.normal(size=3)
    X = x0 * np.eye(2) + s[0] * sig1 + s[1] * sig2 + s[2] * sig3
    dets.append(abs(np.linalg.det(X) - (x0 ** 2 - float(s @ s))))
    cones.append(bool(
        (np.linalg.eigvalsh(X).min() >= -1e-12)
        == ((x0 ** 2 - float(s @ s)) >= -1e-12 and x0 >= -1e-12)))
    A = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    A = A / np.sqrt(np.linalg.det(A))          # exact SL(2,C)
    Xp = A @ X @ A.conj().T
    sl2s.append(abs(np.linalg.det(Xp) - np.linalg.det(X)))
    # SU(2): x0 fixed
    H = rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2))
    Q, _ = np.linalg.qr(H)                     # unitary
    Q = Q / np.sqrt(np.linalg.det(Q))          # SU(2) element
    Xq = Q @ X @ Q.conj().T
    x0p = 0.5 * np.real(np.trace(Xq))
    su2_fix.append(abs(x0p - x0))
    # boost: A = exp((eta/2) n.sig), eta, n fixed below
R["T1_det"] = float(max(dets))
R["T1_cone_equivalence"] = all(cones)
R["T1_SL2C_det_preserved"] = float(max(sl2s))
R["T1_SU2_fixes_x0"] = float(max(su2_fix))

# the boost check against the explicit Lorentz matrix
eta = 0.7
n_hat = np.array([0.3, -0.4, 0.862607])       # (close to unit)
n_hat = n_hat / np.linalg.norm(n_hat)
A = np.eye(2) * np.cosh(eta / 2) + (n_hat[0] * sig1 + n_hat[1] * sig2
                                    + n_hat[2] * sig3) * np.sinh(eta / 2)
# A is Hermitian POSITIVE with det = cosh^2 - sinh^2 = 1 -> SL(2,C)
for _ in range(100):
    x0 = abs(rng.normal()) + 0.5
    s = rng.normal(size=3)
    X = x0 * np.eye(2) + s[0] * sig1 + s[1] * sig2 + s[2] * sig3
    Xp = A @ X @ A.conj().T
    x0p = 0.5 * np.real(np.trace(Xp))
    sp = np.array([0.5 * np.real(np.trace(Xp @ sigq)) for sigq in SIG])
    # reference Lorentz boost on (x0, s):
    sh = np.sinh(eta)
    ch = np.cosh(eta)
    v = np.array([x0, *s])
    Lam = np.eye(4)
    Lam[0, 0] = ch
    Lam[0, 1:] = sh * n_hat
    Lam[1:, 0] = sh * n_hat
    Lam[1:, 1:] = np.eye(3) + (ch - 1) * np.outer(n_hat, n_hat)
    vp = Lam @ v
    boost_err.append(np.linalg.norm(np.array([x0p, *sp]) - vp))
R["T1_boost_vs_Lambda"] = float(max(boost_err))

# ---------------- T2: Bug #11d as an operator identity --------------
Sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=complex) / np.sqrt(2)
Sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]], dtype=complex) / np.sqrt(2)
Sz = np.array([[1, 0, 0], [0, 0, 0], [0, 0, -1]], dtype=complex)
SV = [Sx, Sy, Sz]

def so(op, site, N):
    out = np.eye(1, dtype=complex)
    for k in range(N):
        out = np.kron(out, op if k == site else np.eye(3, dtype=complex))
    return out

def SS(i, j, N):
    return sum(so(SV[q], i, N) @ so(SV[q], j, N) for q in range(3))

def sector_P(J, N, pair=(0, 1)):
    """Correct projector onto the pair's J sector; SS nodes {-2,-1,+1}."""
    SSij = SS(*pair, N)
    I = np.eye(3 ** N, dtype=complex)
    nodes = [-2.0, -1.0, 1.0]
    target = nodes[J]
    poly = np.array([0.0, 0.0, 0.0])
    for k in range(3):
        num = np.array([1.0]); den = 1.0
        for m in range(3):
            if m == k:
                continue
            num = np.convolve(num, [-nodes[m], 1.0])
            den *= (nodes[k] - nodes[m])
        if abs(nodes[k] - target) < 1e-12:
            poly = poly + num / den
    return poly[0] * I + poly[1] * SSij + poly[2] * (SSij @ SSij)

for N in (1, 6):
    I = np.eye(3 ** N, dtype=complex)
    SS01 = SS(0, 1, N)
    Pw = (SS01 + I) / 2.0
    D = Pw @ Pw - Pw
    idem_F = float(np.linalg.norm(D))                     # UNSQUARED Frobenius
    idem_F2 = float(np.real(np.trace(D @ D.conj().T)))   # squared
    P2 = sector_P(2, N); P0 = sector_P(0, N); P1 = sector_P(1, N)
    trP0 = float(np.real(np.trace(P0)))
    ident = float(np.linalg.norm(Pw - (P2 - 0.5 * P0)))
    R[f"T2_N{N}"] = {
        "identity_PW_equals_P2_minus_halfP0": ident,
        "trace_P0": trP0,
        "idempotency_F_unsquared": idem_F,
        "idempotency_F_squared": idem_F2,
        "three_quarters_P0_F_unsquared": float(np.linalg.norm(0.75 * P0)),
        "audit_formula_(9/16)TrP0": (9 / 16) * trP0,
    }

# ---------------- T3: 112/45 arithmetic ------------------------------
R["T3"] = {
    "2*5*(7/15)*(8/15)": 2 * 5 * (7 / 15) * (8 / 15),
    "112/45": 112 / 45,
    "equal": abs(2 * 5 * (7 / 15) * (8 / 15) - 112 / 45) < 1e-15,
}

# ---------------- T4: (2/3)^n decay (Paper I Thm 8 input) ------------
from scipy.linalg import null_space
def P2op(N):
    S = SS(0, 1, N)
    I = np.eye(3 ** N, dtype=complex)
    return (S + I) @ (S + 2 * I) / 6.0
for L in (4, 5, 6):
    bonds = [(i, i + 1) for i in range(L - 1)]
    M = P2op(L) if L == 2 else None
    M = None
    for (i, j) in bonds:
        P = None
        S = SS(i, j, L)
        I = np.eye(3 ** L, dtype=complex)
        P = (S + I) @ (S + 2 * I) / 6.0
        M = P if M is None else (M + P)
    K = null_space(M, rcond=1e-11)
    rho = K @ K.conj().T / K.shape[1]
    vals = {}
    for n in range(1, L):
        SzSn = so(Sz, 0, L) @ so(Sz, n, L)
        vals[n] = round(float(np.real(np.trace(rho @ SzSn))), 9)
    R[f"T4_L{L}"] = {"kernel_dim": K.shape[1], "corr": vals,
                      "declared_decay": {n: round((2 / 3) ** n, 9)
                                         for n in range(1, L)}}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r53e_verify.json", "w") as f:
    json.dump(R, f, indent=2, default=str)
print(json.dumps(R, indent=1, default=str))
