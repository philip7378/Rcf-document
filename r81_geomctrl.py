"""r8.1 GEOMETRIC CONTROLS — machine verification of the user's
three experiments BEFORE they enter the manuscript.

Cells: 3 edge-sharing equilateral triangles T1=(A,B,C),
T2=(B,C,D) sharing edge B-C, T3=(C,D,E) sharing edge C-D
(D = B+C-A = (1.5, sqrt3/2), E = C+D-B = (1.0, sqrt3)).
Welded union = convex quadrilateral A,B,D,E with C the midpoint
of side E-A.

Claims under test (reported AS FOUND):
  G1  inside bare T1: 1A Hilbert cross-ratio, 1B log-barrier l2,
      1C l1-of-logs are exact metrics; boundary evaluation
      diverges.
  G2  directed sides cancel interior edges exactly; Hilbert on
      the welded trapezoid is a metric; log-barrier l2 also.
  G3  isotropy: 1A/1C anisotropic at the centroid; 1B ~isotropic
      in a single cell; glued barrier anisotropic; inscribed-disk
      Klein exactly isotropic. Tangency welding: exact tangency
      sits at +infinity under the log family (honest divergence);
      delta-interior transfer makes cross-cell metricity an
      EXACT INHERITANCE from per-cell metricity.
  G4  C(D,2)=D only at D=3; octonion associator = 2 on Fano
      witnesses (D=7 fails Jacobi by machine).
"""
import json
import math
import time

import numpy as np

t0 = time.time()
R = {}

SQ3 = math.sqrt(3.0)
A = np.array([0.0, 0.0]); B = np.array([1.0, 0.0]); C = np.array([0.5, SQ3 / 2])
Dv = B + C - A
E = C + Dv - B
TRIS = [(A, B, C), (B, C, Dv), (C, Dv, E)]
HULL = [A, B, Dv, E]

# ---------------- geometry + welding -------------------------------
def hull_convex(pts):
    P = np.array(pts); cen = P.mean(0)
    ang = np.argsort(np.arctan2(P[:, 1] - cen[1], P[:, 0] - cen[0]))
    P = P[ang]; n = len(P); signs = []
    for i in range(n):
        u = P[(i + 1) % n] - P[i]; v = P[(i + 2) % n] - P[(i + 1) % n]
        signs.append(u[0] * v[1] - u[1] * v[0])
    return all(s > 0 for s in signs) or all(s < 0 for s in signs)

def ccw_order(T):
    T = np.array(T); c = T.mean(0)
    ang = np.argsort(np.arctan2(T[:, 1] - c[1], T[:, 0] - c[0]))
    return [tuple(np.round(T[i], 12)) for i in ang]

T1o, T2o, T3o = (ccw_order(t) for t in TRIS)
def edge_dir(To, p, q):
    key = {tuple(np.round(x, 12)) for x in (p, q)}
    for i in range(3):
        a, b = np.array(To[i]), np.array(To[(i + 1) % 3])
        if tuple(np.round(a, 12)) in key and tuple(np.round(b, 12)) in key:
            return b - a
    return None

d12a = edge_dir(T1o, B, C); d12b = edge_dir(T2o, B, C)
d23a = edge_dir(T2o, C, Dv); d23b = edge_dir(T3o, C, Dv)
R["G2_geometry"] = {
    "welded_union_convex": hull_convex(HULL),
    "C_is_midpoint_of_EA": float(np.linalg.norm(A + E - 2 * C)),
    "shared_edge_12_dir_cancel": float(np.linalg.norm(d12a + d12b)),
    "shared_edge_23_dir_cancel": float(np.linalg.norm(d23a + d23b)),
    "mechanism": "CCW orientation traverses a shared edge in opposite "
                 "senses; direction vectors cancel exactly; interior "
                 "walls drop from the boundary",
}

# ---------------- barycentric machinery (bare T1) -------------------
def bary(p, T):
    T = np.array(T); v0, v1, v2 = T[1] - T[0], T[2] - T[0], np.array(p) - T[0]
    d00, d01, d11 = v0 @ v0, v0 @ v1, v1 @ v1
    d20, d21 = v2 @ v0, v2 @ v1
    den = d00 * d11 - d01 * d01
    l1 = (d11 * d20 - d01 * d21) / den
    l2 = (d00 * d21 - d01 * d20) / den
    return np.array([1 - l1 - l2, l1, l2])

def d_1A(p, q, T=TRIS[0]):
    bp, bq = bary(p, T), bary(q, T)
    r = np.log(bp / bq)
    return 0.5 * (r.max() - r.min())

def d_1B(p, q, T=TRIS[0]):
    bp, bq = bary(p, T), bary(q, T)
    return float(np.linalg.norm(np.log(bp) - np.log(bq)))

def d_1C(p, q, T=TRIS[0]):
    bp, bq = bary(p, T), bary(q, T)
    return float(np.sum(np.abs(np.log(bp) - np.log(bq))))

rng = np.random.default_rng(7)
def in_tri(T, n):
    T = np.array(T)
    acc = []
    while sum(len(x) for x in acc) < n:
        u = rng.random((int(n * 1.5) + 100, 2))
        acc.append(u[u.sum(1) < 1])
    u = np.vstack(acc)[:n]
    return T[0] + u @ (T[1:3] - T[0])

O1 = np.array([0.5, SQ3 / 6.0])

# G1: 10,000 inside-T1 triples
g1 = {}
for name, fn in (("1A_Hilbert", d_1A), ("1B_logbarrier_l2", d_1B), ("1C_l1_logs", d_1C)):
    P = in_tri(TRIS[0], 10000)
    viol = -1e18; mdef = 1e18
    for _ in range(10000):
        i, j, k = rng.integers(0, len(P), 3)
        dij, djk, dik = fn(P[i], P[j]), fn(P[j], P[k]), fn(P[i], P[k])
        viol = max(viol, dik - dij - djk); mdef = min(mdef, dij + djk - dik)
    g1[name] = {"max_violation": float(viol), "min_defect": float(mdef)}
lad = {}
for name, fn in (("1A", d_1A), ("1B", d_1B), ("1C", d_1C)):
    lad[name] = [float(fn(np.array([0.5, SQ3 / 6.0 * (1 - x)]), O1))
                 for x in (1e-1, 1e-3, 1e-6)]
R["G1_inside_bare_T1"] = {
    "triangle_ineq_10000": g1, "boundary_ladders": lad,
    "reading": "all three additive-log constructions are exact metrics "
               "inside one bare triangle; boundary evaluation diverges "
               "on every ladder (the ln(1/x) law)",
}

# ---------------- welded-union metrics (convex trapezoid) ----------
def chord_params(p, q, hull):
    p, q = np.array(p, float), np.array(q, float)
    u = q - p; L = np.linalg.norm(u); u = u / L
    ts = []
    H = np.array(hull); n = len(H)
    for i in range(n):
        a, b = H[i], H[(i + 1) % n]
        v = b - a
        cr = u[0] * v[1] - u[1] * v[0]
        if abs(cr) < 1e-13:
            continue
        w = a - p
        t = (w[0] * v[1] - w[1] * v[0]) / cr
        s = (w[0] * u[1] - w[1] * u[0]) / cr
        if -1e-12 <= s <= 1 + 1e-12:
            ts.append(t)
    ts_neg = [t for t in ts if t < 0]
    ts_pos = [t for t in ts if t > 1]
    if not ts_neg or not ts_pos:
        return 0.0, 1.0        # segment parallel-interior fallback (no
                               # boundary crossing on that side; the
                               # p,q pair then needs the chord through
                               # the LINE, not the segment — handled by
                               # caller as degenerate)
    return max(ts_neg), min(ts_pos)

def d_hilbert_hull(p, q, hull=HULL):
    ts = []
    # intersect the LINE through p,q with every hull edge, collect hits
    p, q = np.array(p, float), np.array(q, float)
    u = q - p; L = np.linalg.norm(u)
    if L < 1e-15:
        return 0.0
    u = u / L
    H = np.array(hull); n = len(H)
    for i in range(n):
        a, b = H[i], H[(i + 1) % n]
        v = b - a
        cr = u[0] * v[1] - u[1] * v[0]
        if abs(cr) < 1e-13:
            continue
        w = a - p
        t = (w[0] * v[1] - w[1] * v[0]) / cr
        s = (w[0] * u[1] - w[1] * u[0]) / cr
        if -1e-12 <= s <= 1 + 1e-12:
            ts.append(t)
    ts_neg = [t for t in ts if t < -1e-15]
    ts_pos = [t for t in ts if t > 1 + 1e-15]
    if not ts_neg or not ts_pos:
        return 0.0        # degenerate: line misses hull on one side —
                         # p,q interior so this cannot happen for the
                         # convex hull; guarded anyway
    tm, tp = max(ts_neg), min(ts_pos)
    return 0.5 * math.log(((1 - tm) * tp) / ((-tm) * (tp - 1)))

def facet_dists(p, hull=HULL):
    H = np.array(hull); out = []
    for i in range(len(H)):
        a, b = H[i], H[(i + 1) % len(H)]
        e = b - a; nrm = np.array([-e[1], e[0]])
        out.append(float((np.array(p) - a) @ nrm / np.linalg.norm(nrm)))
    return np.array(out)

def d_barrier_welded(p, q):
    return float(np.linalg.norm(np.log(facet_dists(p)) - np.log(facet_dists(q))))

P1 = in_tri(TRIS[0], 5000); P2 = in_tri(TRIS[1], 5000); P3 = in_tri(TRIS[2], 5000)
vh, mdefh = -1e18, 1e18
vb, mdefb = -1e18, 1e18
for i in range(5000):
    a_, b_, c_ = P1[i], P2[i], P3[i]
    for fn, acc in ((d_hilbert_hull, "h"), (d_barrier_welded, "b")):
        dij, djk, dik = fn(a_, b_), fn(b_, c_), fn(a_, c_)
        if acc == "h":
            vh = max(vh, dik - dij - djk); mdefh = min(mdefh, dij + djk - dik)
        else:
            vb = max(vb, dik - dij - djk); mdefb = min(mdefb, dij + djk - dik)
R["G2_welded_metrics"] = {
    "n_cross_triples": 5000,
    "hilbert_max_violation": float(vh), "hilbert_min_defect": float(mdefh),
    "logbarrier_max_violation": float(vb), "logbarrier_min_defect": float(mdefb),
    "reading": "on the welded convex union, the Hilbert cross-ratio is a "
               "metric across all three cells simultaneously (classic "
               "convex-domain result, reproduced); the log-barrier l2 is a "
               "norm-of-coordinate-difference and is a metric by structure",
}

# ---------------- G3: isotropy --------------------------------------
def step(fn, base, eps, degs):
    return np.array([fn(base, base + eps * np.array(
        [math.cos(math.radians(t)), math.sin(math.radians(t))]))
        for t in degs])

angs4 = [0.0, 15.0, 30.0, 90.0]
angsF = list(range(0, 360, 1))
tA4 = step(d_1A, O1, 0.01, angs4); tB4 = step(d_1B, O1, 0.01, angs4)
tC4 = step(d_1C, O1, 0.01, angs4)
fA = step(d_1A, O1, 0.01, angsF); fB = step(d_1B, O1, 0.01, angsF)
fC = step(d_1C, O1, 0.01, angsF)
aniso = lambda v: float((v.max() - v.min()) / v.mean() * 100.0)

# glued log-barrier Hessian at O1 (4-facet hull) vs bare T1 (3-facet)
def logsum_hess(p, hull):
    eps = 1e-6
    J = np.zeros((2, 2))
    for i in range(2):
        for j in range(2):
            e_i, e_j = np.eye(2)[i], np.eye(2)[j]
            f = lambda x: float(np.sum(np.log(facet_dists(x, hull))))
            J[i, j] = (f(p + eps * (e_i + e_j)) - f(p + eps * (e_i - e_j))
                       - f(p + eps * (-e_i + e_j)) + f(p + eps * (-e_i - e_j))) / (4 * eps * eps)
    return J

Jg = logsum_hess(O1, HULL)
Jb = logsum_hess(O1, [A, B, C])
evg, evb = np.linalg.eigvalsh(Jg), np.linalg.eigvalsh(Jb)

# clean Beltrami-Klein on a disk
def d_bk(p, q, O, r):
    p, q = np.array(p, float), np.array(q, float)
    u = q - p; L = np.linalg.norm(u)
    if L < 1e-15:
        return 0.0
    u = u / L
    w = p - O
    b = 2 * (w @ u); c = w @ w - r * r
    disc = b * b - 4 * c
    if disc <= 0:
        return float("inf")
    s1 = (-b - math.sqrt(disc)) / 2.0
    s2 = (-b + math.sqrt(disc)) / 2.0
    if s2 - L <= 0 or s1 >= 0:
        return float("inf")          # endpoint on/outside the boundary
    return 0.5 * math.log(((L - s1) * s2) / ((-s1) * (s2 - L)))

r_in = SQ3 / 6.0
O2 = np.array(TRIS[1]).mean(0); O3 = np.array(TRIS[2]).mean(0)
bk_iso = step(lambda p, q: d_bk(p, q, O1, r_in), O1, 0.01, angsF)

# tangency finding: transfer at exact tangency = boundary = infinite
M12 = (B + C) / 2.0; M23 = (C + Dv) / 2.0
d_to_tangent = d_bk(O1, M12, O1, r_in)   # O1 -> tangency point (on boundary)
# delta-interior transfer construction
def dweld(delta):
    def nhat(O, M):
        v = O - M; return v / np.linalg.norm(v)
    A12 = M12 + delta * nhat(O1, M12); B12 = M12 + delta * nhat(O2, M12)
    A23 = M23 + delta * nhat(O2, M23); B23 = M23 + delta * nhat(O3, M23)
    def d12(p, q_): return d_bk(p, A12, O1, r_in) + d_bk(B12, q_, O2, r_in)
    def d23(p, q_): return d_bk(p, A23, O2, r_in) + d_bk(B23, q_, O3, r_in)
    def d13(p, q_): return (d_bk(p, A12, O1, r_in) + d_bk(B12, A23, O2, r_in)
                            + d_bk(B23, q_, O3, r_in))
    return d12, d23, d13

deltas = {}
for delta in (1e-1, 1e-2, 1e-3):
    d12f, d23f, d13f = dweld(delta)
    xfer = d_bk(O1, M12 + delta * (O1 - M12) / np.linalg.norm(O1 - M12), O1, r_in)
    deltas[delta] = {"single_transfer_cost_from_O1": xfer}
vt2 = -1e18
for i in range(5000):
    d12f, d23f, d13f = dweld(1e-2)
    a_, b_, c_ = P1[i], P2[i], P3[i]
    vt2 = max(vt2, d13f(a_, c_) - d12f(a_, b_) - d23f(b_, c_))

R["G3_isotropy"] = {
    "table_eps0.01_deg_0_15_30_90": {
        "1A": [round(float(x), 6) for x in tA4],
        "1B": [round(float(x), 6) for x in tB4],
        "1C": [round(float(x), 6) for x in tC4],
    },
    "full_sweep_aniso_pct": {"1A": round(aniso(fA), 3), "1B": round(aniso(fB), 4),
                             "1C": round(aniso(fC), 3)},
    "BK_disk_aniso_pct_exact": float(aniso(bk_iso)),
    "BK_isotropy_spread": float(bk_iso.max() - bk_iso.min()),
    "bare_T1_barrier_hess_eigs": [round(float(x), 6) for x in evb],
    "glued_4facet_barrier_hess_eigs": [round(float(x), 6) for x in evg],
    "glued_barrier_aniso_pct": round(float((evg[-1] - evg[0]) / evg.mean() * 100.0), 3),
    "bare_barrier_aniso_pct": round(float((evb[-1] - evb[0]) / evb.mean() * 100.0), 4),
    "tangency_finding": {
        "dist_O1_to_tangency_point": d_to_tangent,
        "delta_transfer_costs": deltas,
        "welded_delta0.01_max_violation_5000": float(vt2),
        "reading": "EXACT tangency puts the transfer point ON both "
                   "boundaries: the Klein/log distance to it is +infinity "
                   "(machine: inf), so a finite 'welded-disk' number at "
                   "exact tangency is not reproducible under the log "
                   "family — welding requires a delta-interior transfer "
                   "(finite edge correlation K > 0). With the "
                   "delta-transfer, cross-cell triangle inequality is an "
                   "EXACT INHERITANCE: d13 = d1(p1,A12) + d2(B12,A23) + "
                   "d3(B23,p3) <= d1 + [d2(B12,p2)+d2(p2,A23)] + d3 = "
                   "d12 + d23 reduces to the per-cell metricity; the "
                   "transfer cost diverges like ln(1/delta) as delta -> 0 "
                   "(ladder above).",
    },
    "reading_G3": "the circle buys ROTATIONAL ISOTROPY: 1A/1C are "
                  "anisotropic at the centroid (hexagonal unit balls); "
                  "1B is isotropic at the single-cell centroid but the "
                  "GLUED barrier inherits the trapezoid's global shape "
                  "(anisotropy above); the inscribed-disk Klein metric "
                  "is exactly isotropic (spread 0 to machine precision) "
                  "and stays isotropic under gluing",
}

# ---------------- G4: dimension sweep -------------------------------
# octonion multiplication table, indices 0..7 (e0 = 1)
TRIP = [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)]
def e_mul(i, j):
    if i == 0:
        return (1, j)
    if j == 0:
        return (1, i)
    if i == j:
        return (-1, 0)
    for (a, b, c) in TRIP:
        s = {a, b, c}
        if i in s and j in s and i != j:
            if (i, j) in ((a, b), (b, c), (c, a)):
                return (1, c if (i, j) == (a, b) else (a if (i, j) == (b, c) else b))
            return (-1, c if (j, i) == (a, b) else (a if (j, i) == (b, c) else b))
    raise AssertionError

def oct_mul(x, y):
    out = [0.0] * 8
    for i in range(8):
        if x[i] == 0: continue
        for j in range(8):
            if y[j] == 0: continue
            sgn, k = e_mul(i, j)
            out[k] += x[i] * y[j] * sgn
    return out

def assoc_defect(i, j, k):
    x = [0.0] * 8; x[i] = 1.0
    y = [0.0] * 8; y[j] = 1.0
    z = [0.0] * 8; z[k] = 1.0
    lhs = oct_mul(oct_mul(x, y), z)
    rhs = oct_mul(x, oct_mul(y, z))
    return max(abs(a - b) for a, b in zip(lhs, rhs))

oct_as = {}
worst = (None, -1.0)
for i in range(1, 8):
    for j in range(1, 8):
        for k in range(1, 8):
            v = assoc_defect(i, j, k)
            if v > worst[1]:
                worst = ((i, j, k), v)
for trip in ((1, 2, 3), (1, 2, 4), (1, 4, 2), (2, 5, 7)):
    oct_as[str(trip)] = assoc_defect(*trip)

sweep = {}
for D in (1, 2, 3, 4, 5, 7):
    nc2 = math.comb(D, 2)
    n2 = next((n for n in range(1, 12) if n * n == D + 1), None)
    sweep[D] = {"C(D,2)": nc2, "C(D,2)==D": nc2 == D, "D+1_sq_n": n2}
R["G4_dimension_sweep"] = {
    "sweep": sweep,
    "octonion_associator_witnesses": oct_as,
    "octonion_worst_associator": {"triple": worst[0], "value": worst[1]},
    "J3_H2C_closure_cited": "r53c C3_D3_construction closure 6.28e-16 "
                            "(certified earlier; cited)",
    "reading": "C(D,2) = D holds ONLY at D = 3 among 1,2,3,4,5,7; the "
               "octonion route (D = 7) fails associativity by machine "
               "witness (associator = 2 on the Fano triples, e.g. "
               "(e1 e2) e4 = +e7 while e1 (e2 e4) = -e7). Geometry alone "
               "(directed simplices + inscribed spheres + log metrics) "
               "exists in EVERY dimension; the algebraic direction "
               "closure (Theorem II.1) is what selects D = 3 uniquely.",
}

R["elapsed_s"] = round(time.time() - t0, 2)
with open("/home/z/my-project/scripts/r81_geomctrl.json", "w") as f:
    json.dump(R, f, indent=2, default=str)
for k in R:
    print("###", k)
    print(json.dumps(R[k], indent=1, default=str)[:1500])
