"""PR-VTX-1c ARM C — cross-axis propagation preview with the baseline
control, per the frozen pr_vtx1c_sheet.txt (6aba7cff).

Corner junction dim 729, layout (0,1) x, (2,3) y, (4,5) z; registers
(0,2,4). L = -i[H_vtx, .] + gamma (D_x + D_y + D_z), gamma = 1;
H_vtx = S_0.S_2 + S_2.S_4 + S_4.S_0; D_mu = cov3 dissipator on the
mu-axis bond (jumps (X_q - P2 X_q) P2 / sqrt(2), the standing
r5.1d/r5.2 formula). RK4, dt = 0.075, window [0, 1.5].

Paired seeds:
  x-defect:  rho_def(0) = (P2_{01}/5) x P_K2_{23} x P_K2_{45}
             (P2 on the x bond /5, reconciled kernel on y, z);
  baseline:  rho_bg(0)  = P_K2_{01} x P_K2_{23} x P_K2_{45}
             (reconciled kernel everywhere).
Read M_mu(t) = Tr(rho P2_{mu-bond}); report Delta M_y = M_y^def -
M_y^bg (and Delta M_z identically). Isotropy |M_y - M_z| <= 1e-9;
Tr rho = 1.00000000; positivity min eig >= -1e-9.
Targets: Delta M_y(0.15) = -0.000134, (0.375) = -0.001363,
(0.75) = -0.003196, (1.50) = +0.004920.
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

gs = max(float(np.linalg.norm(a @ b - b @ a - 1j * c))
         for a, b, c in ((Sx, Sy, Sz), (Sy, Sz, Sx), (Sz, Sx, Sy)))
R["GATE_S"] = {"max_comm": gs,
               "verdict": "PASS" if gs < 1e-14 else "FAIL"}

NC = 6
D = 3 ** NC          # 729

def so(op, site):
    out = np.eye(1, dtype=complex)
    for k in range(NC):
        block = op if k == site else np.eye(3, dtype=complex)
        out = np.kron(out, block)
    return out

def SS_ij(i, j):
    return sum(so(SVEC[q], i) @ so(SVEC[q], j) for q in range(3))

def P2_pair(i, j):
    SS = SS_ij(i, j)
    I = np.eye(D, dtype=complex)
    return (SS + I) @ (SS + 2 * I) / 6.0

BONDS = [(0, 1), (2, 3), (4, 5)]
P2 = {b: P2_pair(*b) for b in BONDS}

# ---- reconciled kernel per axis: the J<=1 subspace projector of the
# pair, i.e. 1 - P2 (the "P_K2" of the sheet: kernel of M_edges is the
# J<=1 triple sector; reconciled-kernel seed = projector onto ker).
P_K2 = {b: np.eye(D, dtype=complex) - P2[b] for b in BONDS}

# ---- H_vtx on registers (0,2,4): component-form Casimir route is for
# projectors; here H_vtx = sum of pair dot products:
H_vtx = SS_ij(0, 2) + SS_ij(2, 4) + SS_ij(4, 0)

# ---- cov3 dissipator per bond (standing formula) ----
def cov3_jumps(b):
    P2b = P2[b]
    out = []
    for q in range(3):
        Xq = so(SVEC[q], b[0]) - so(SVEC[q], b[1])
        out.append((Xq - P2b @ Xq) @ P2b / np.sqrt(2))
    return out

# ---- generator as a MAP on the density matrix (no vec, no
# 729^2 x 729^2 superoperator — that is 4 TiB dense; instead
# apply each piece by left/right matrix products, 729x729):
def Lmap(rho):
    out = -1j * (H_vtx @ rho - rho @ H_vtx)
    for b in BONDS:
        for L in cov3_jumps(b):
            LdL = L.conj().T @ L
            out = out + (L @ rho @ L.conj().T
                         - 0.5 * (LdL @ rho + rho @ LdL))
    return out

# ---- seeds ----
def kron3(A, B, C):
    return np.kron(np.kron(A, B), C)

# pair-space 9x9 blocks for the seeds: P2/5 on x, kernel projectors
# elsewhere. Build full 729x729 seeds via kron of the three 9x9 pair
# blocks (each pair block acts on its two sites — matches the site
# layout (0,1)(2,3)(4,5)).
def pair_blocks(bond):
    P2_9 = P2[bond][:9, :9] if False else None
    # build the 9x9 pair operators directly
    S1 = [np.kron(SVEC[q], np.eye(3, dtype=complex)) for q in range(3)]
    S2 = [np.kron(np.eye(3, dtype=complex), SVEC[q]) for q in range(3)]
    SS9 = sum(S1[q] @ S2[q] for q in range(3))
    I9 = np.eye(9, dtype=complex)
    P2_9 = (SS9 + I9) @ (SS9 + 2 * I9) / 6.0
    P_K2_9 = I9 - P2_9
    return P2_9, P_K2_9

P2_9 = {b: pair_blocks(b)[0] for b in BONDS}
PK2_9 = {b: pair_blocks(b)[1] for b in BONDS}

bx, by, bz = BONDS
rho_def = kron3(P2_9[bx] / 5.0, PK2_9[by], PK2_9[bz])
rho_def = rho_def / np.trace(rho_def).real
rho_bg = kron3(PK2_9[bx], PK2_9[by], PK2_9[bz])
rho_bg = rho_bg / np.trace(rho_bg).real
R["seeds"] = {
    "x_defect_trace": round(float(np.trace(rho_def).real), 9),
    "baseline_trace": round(float(np.trace(rho_bg).real), 9),
    "x_defect_Mx0": round(float(np.real(np.trace(rho_def @ P2[bx]))), 6),
    "baseline_M0": round(float(np.real(np.trace(rho_bg @ P2[bx]))), 6),
}

# ---- RK4 integration on the density matrix directly ----
DT = 0.075
T_END = 1.5
STEPS = int(round(T_END / DT))
READ_STEPS = [0, 2, 5, 10, 20]     # t = 0, 0.15, 0.375, 0.75, 1.5

def integrate(rho0):
    rho = rho0.copy()
    out = {0: rho.copy()}
    for s in range(STEPS):
        k1 = Lmap(rho)
        k2 = Lmap(rho + DT / 2 * k1)
        k3 = Lmap(rho + DT / 2 * k2)
        k4 = Lmap(rho + DT * k3)
        rho = rho + DT / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        out[s + 1] = rho.copy()
    return out

traj_def = integrate(rho_def)
traj_bg = integrate(rho_bg)

def readMs(rho):
    Mx = float(np.real(np.trace(rho @ P2[bx])))
    My = float(np.real(np.trace(rho @ P2[by])))
    Mz = float(np.real(np.trace(rho @ P2[bz])))
    tr = float(np.real(np.trace(rho)))
    rh = (rho + rho.conj().T) / 2
    mineig = float(np.linalg.eigvalsh(rh)[0])
    return Mx, My, Mz, tr, mineig

rows = []
for s in READ_STEPS:
    Mxd, Myd, Mzd, trd, med = readMs(traj_def[s])
    Mxb, Myb, Mzb, trb, meb = readMs(traj_bg[s])
    rows.append({
        "step": s, "t": round(s * DT, 3),
        "defect": {"Mx": round(Mxd, 6), "My": round(Myd, 6),
                   "Mz": round(Mzd, 6), "tr": round(trd, 8),
                   "min_eig": round(med, 9)},
        "baseline": {"Mx": round(Mxb, 6), "My": round(Myb, 6),
                     "Mz": round(Mzb, 6), "tr": round(trb, 8),
                     "min_eig": round(meb, 9)},
        "DeltaMy": round(Myd - Myb, 6),
        "DeltaMz": round(Mzd - Mzb, 6),
        "isotropy_def": abs(Myd - Mzd),
        "isotropy_bg": abs(Myb - Mzb),
    })

R["trajectories"] = rows
R["targets"] = {0.15: -0.000134, 0.375: -0.001363, 0.75: -0.003196,
                1.5: 0.004920}
R["target_check"] = {}
for row in rows:
    tgt = R["targets"].get(row["t"])
    if tgt is not None:
        R["target_check"][row["t"]] = {
            "DeltaMy": row["DeltaMy"], "target": tgt,
            "dev": round(abs(row["DeltaMy"] - tgt), 6),
        }
R["checks"] = {
    "max_isotropy_def": max(r["isotropy_def"] for r in rows),
    "max_isotropy_bg": max(r["isotropy_bg"] for r in rows),
    "trace_def_min": min(r["defect"]["tr"] for r in rows),
    "trace_def_max": max(r["defect"]["tr"] for r in rows),
    "positivity_min": min(min(r["defect"]["min_eig"],
                              r["baseline"]["min_eig"]) for r in rows),
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r53c_armC.json", "w") as f:
    json.dump(R, f, indent=2, default=str)

print("GATE_S:", R["GATE_S"]["verdict"])
print("seeds:", R["seeds"])
for r in rows:
    print(f"t={r['t']}: def (Mx={r['defect']['Mx']}, My={r['defect']['My']})"
          f" bg My={r['baseline']['My']} dMy={r['DeltaMy']}"
          f" dMz={r['DeltaMz']} iso={r['isotropy_def']:.1e}")
print("target_check:", json.dumps(R["target_check"], indent=1))
print("checks:", json.dumps(R["checks"], indent=1))
print("elapsed:", R["elapsed_s"])
