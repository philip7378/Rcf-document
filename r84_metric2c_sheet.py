"""r8.4 — PR-METRIC-2c FROZEN SHEET (written BEFORE the executor;
md5 recorded in the sheet itself; the executor may read but not
modify this file).

The re-execution of PR-METRIC-2b under the r8.3-declared spec. The
r7.0/r8.0 SPEC-INCOMPLETE outcome was caused by the SHEET (missing
common space + missing normalization declaration); this sheet
declares both, so SPEC-INCOMPLETE would now be a real result, not a
spec gap.

DECLARED SPEC (binding):
 1. COMMON SPACE: route (i) — the certified profile span. Link-graph
    sites embed as displacement profile vectors Phi_mu in R^6 via the
    r6.1/r70 certified construction: Phi_mu[x] = <S^z_stub(mu)
    S^z_x> on the K32 corner kernel (sites 0-5, bonds (0,1),(2,3),
    (4,5), registers {0,2,4}, stubs {1,3,5}, J_vtx=3-forbidden
    kernel). All three metric families evaluated on this one space.
 2. K-NORMALIZATION (per the r8.3 §5.3 declaration): RAW correlation
    K(i,j) = <S^z_i S^z_j> is the default; the Pearson form
    (divided by the rms variances sqrt(<S_i^2><S_j^2>)) is computed
    alongside and every value carries its formula. The M formula
    M(A,C;O) = -ln|K(A,C)| + ln|K(A,O)| + ln|K(O,C)| is printed
    beside every M value.
 3. FAMILIES ON THE COMMON SPACE (each with formula):
    (F1) d_int — path-infimum over the site-graph with edge weights
         w(i,j) = -ln|K(i,j)| (raw). Theorem-S2 family.
    (F2) d_chord — Euclidean chord ||Phi_a - Phi_b|| on the profile
         image (the route-(i) embedding metric).
    (F3) d_scaling — the Theorem-A/B log-volume family restricted to
         the frame: -ln[det C(u,v) / (||u||^2 ||v||^2)] with C the
         2x2 Gram of the profile pair.
 4. OUTCOME SPACE (four outcomes, non-vacuous):
    EQUAL        — the families agree on all three stub pairs at
                   tol 1e-2 relative.
    ENVELOPE     — one family's distances are bounded by another's on
                   every pair (d_a <= d_b for all pairs, strict on
                   at least one, with the ratio bounded).
    IMPOSSIBLE   — a family violates metricity (triangle inequality
                   or identity of indiscernibles) on the frame.
    SPEC-INCOMPLETE — none of the above holds. Since the sheet now
                   declares space + normalization, this would be a
                   REAL result (the frame genuinely does not
                   adjudicate), not a spec gap.
 5. PRODUCT-SEED GUARD (non-vacuous): a separable classical product
    seed on the same 6 sites must give M = 0 under BOTH
    normalizations (raw and Pearson) — verifying the guard actually
    fires, unlike r7.0's vacuous guard.
 6. INCIRCLE SECONDARY (pre-declared): if EQUAL fires, the chord
    defect at the tripod must be sub-additive; if ENVELOPE fires,
    sub-additive-strict; if neither fires, the tripod reading is
    adjudicated from the certified E_tripod geometry (chord_defect
    -0.421155) without upgrading any E-grade.

REPRODUCTION GATES (mandatory before any verdict):
  RG1. The K32 construction reproduces r70_metric2.json's certified
       correlations to <= 1e-6 (stub-stub and register-stub).
  RG2. d_int, d_chord (via r80's B_route_i), d_scaling reproduce the
       certified 3.6225122 / 1.168930314 / 0.00655857 to <= 1e-6.
  RG3. The profile Gram reproduces a = 0.632092823,
       b = -0.051106217 (r80 E_tripod) to <= 1e-6.
Failure of any gate = no verdict, defect logged.
"""
import hashlib
import json

SHEET = {
    "round": "r8.4",
    "task": "PR-METRIC-2c re-execution (PR-METRIC-2b under the "
            "r8.3-declared spec)",
    "common_space": "route (i): certified profile span; Phi_mu in R^6 "
                    "from the K32 corner kernel (sites 0-5, bonds "
                    "(0,1),(2,3),(4,5), registers {0,2,4}, stubs "
                    "{1,3,5}, J=3-forbidden kernel)",
    "k_normalization": "RAW default (K = <S^z_i S^z_j>); Pearson "
                       "alongside; formulas beside every value",
    "families": {
        "F1_d_int": "path-infimum, edges -ln|K_raw(i,j)| (Theorem S2)",
        "F2_d_chord": "||Phi_a - Phi_b|| on the profile image",
        "F3_d_scaling": "-ln[det C(u,v)/(||u||^2||v||^2)] "
                        "(Theorem A/B family)",
    },
    "outcome_space": ["EQUAL", "ENVELOPE", "IMPOSSIBLE",
                      "SPEC-INCOMPLETE (now a real result — the sheet "
                      "declares space + normalization)"],
    "tolerance": {"EQUAL rel tol": 1e-2},
    "product_seed_guard": "separable classical product seed on the same "
                          "6 sites: M = 0 under BOTH normalizations "
                          "(non-vacuous)",
    "incircle_secondary": "EQUAL -> chord defect sub-additive; "
                           "ENVELOPE -> sub-additive-strict; neither -> "
                           "adjudicate from certified E_tripod without "
                           "grade upgrade",
    "reproduction_gates": {
        "RG1": "K32 correlations reproduce r70_metric2.json <= 1e-6",
        "RG2": "d_int/d_chord/d_scaling reproduce 3.6225122 / "
               "1.168930314 / 0.00655857 <= 1e-6",
        "RG3": "profile Gram a=0.632092823, b=-0.051106217 <= 1e-6",
    },
    "pre_declared_targets": {
        "d_int": 3.6225122, "d_chord": 1.168930314,
        "d_scaling": 0.00655857,
        "Gram_a": 0.632092823, "Gram_b": -0.051106217,
    },
    "sheet_frozen_before_executor": True,
}

path = "/home/z/my-project/scripts/r84_metric2c_sheet.json"
with open(path, "w") as f:
    json.dump(SHEET, f, indent=1)
md5 = hashlib.md5(open(path, "rb").read()).hexdigest()
SHEET["sheet_md5"] = md5
with open(path, "w") as f:
    json.dump(SHEET, f, indent=1)
print("sheet frozen:", md5)
