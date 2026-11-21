"""r8.5 — PR-LAT-1 FROZEN SHEET (written and md5-stamped BEFORE the
executor; the executor may read but not modify this file).

THE MINIMAL MULTI-VERTEX LATTICE GATE — first real attack on the E0
spatial fence. Three precisely-defined cells, three pre-registered
tests, guards from both the audit round (ENVELOPE downgrade, honest
metric comparison) and the pre-flight (two traps caught).

CELLS (precise — sites, bonds, forbidden sectors, measured pairs;
sparse product-operator route mandatory at N=8 after the OOM lesson):
  CELL A (closed plaquette): C8 ring, N=8 sites 0..7, bonds
    (i,i+1 mod 8) all P2; NO additional forbidden sectors (the
    certified pre-flight seed: ker=1, gap 0.349849, J=0 singlet).
    OPEN CONTROL: same ring, bond (7,0) removed (7 bonds).
    MEASURED PAIRS: (0,1) adjacent, (0,2) next-nearest, (0,3)
    two-bond-path, (0,4) true diagonal (two symmetric 2-perimeter-
    hop paths in the closed ring).
  CELL B (2-vertex 3D dumbbell): N=6; vertex A = sites {0,1,2},
    vertex B = {3,4,5}; J=3 forbidden at both vertex triples
    (P3 projector on each triple's J^2); intact welding bond
    P2(1,3). MEASURED: vertex-A 3x3 spin Gram on Sz pairs; the
    6x6 full Gram rank; eigenvalues of both.
  CELL C (open 1D control): 8-site open chain (Cell A's open
    control doubles as this).

DECLARED NORMALIZATIONS AND GUARDS (binding):
  G1. K-NORMALIZATION: raw K = <S^z_i S^z_j> default; Pearson
      alongside; every value carries its formula.
  G2. TRAP-1 GUARD (Néel): every bipartite chord/Gram comparison
      DECLARES the (-1)^(x+y) staggering; unstaggered chords are
      reported only with the inversion flag set (adjacent corners
      anti-aligned: G01 < 0 while |G01| > |G02|).
  G3. TRAP-2 GUARD (singlet tautology): the staggered chord ratio on
      ANY single C4-symmetric J=0 singlet cell is EXCLUDED as
      evidence — it is pinned at sqrt(2) by the sum rule
      G00 + 2G01 + G02 = 0 identically (machine-confirmed 2.8e-17 on
      the audit triple). Family-selection evidence must come from
      non-singlet, open, or >= 2-plaquette / 3D cells only.
  G4. GATE F standing: any functional calculus on a compressed
      subspace is assembled V^dag f(A) V; reproduction gate at a
      certified cell mandatory before any new-cell number.
  G5. NO-GO VIII: bond valence z <= 2 per spin-1 register
      (satisfied: Cell A ring sites z=2; Cell B outer sites z=1,
      welded sites z=2).
  G6. SCALE-INVARIANT RATIOS ONLY for family comparison (d_diag/
      d_adj across the metric candidates; never raw magnitudes at
      a single symmetry-pinned point — the ENVELOPE downgrade
      lesson).
  G7. METRIC CANDIDATES under test (the r8.5 locked set):
      - D_scale (the principal's Spatial Scaling Metric:
        D_scale = sqrt(sum_ab Gamma_ab dd_a dd_b), with V_k =
        sqrt(det S^(k)), S_ij = d_i d_j Gamma_ij)
      - d_int (Theorem-S2 path-infimum over -ln|K| edges)
      - d_chord_staggered (Gram chord with (-1)^(x+y) declared)
      - g_cov is NOT a candidate (renamed internal state metric).

THREE PRE-REGISTERED TESTS (outcomes adjudicated against explicit
pre-declared thresholds):
  T1 (closed-loop transport law): on Cell A closed vs open control,
      the raw multiplicativity defect M = -ln|c_diag| - 2(-ln|c_adj|)
      DROPS by ~ln 2 per added parallel plaquette path (pre-flight
      certified: 1.964x amplification, drop -0.6732 vs -ln2 = -0.6931).
      THRESHOLD: |drop + ln 2| < 0.1 -> LAW CONFIRMED; |drop| < 0.05
      -> NO-EFFECT; else MEASURED-AS-FOUND.
      Secondary: the defect STAYS POSITIVE on one plaquette
      (sub-additive not yet achieved — the positive-defect fence).
  T2 (non-planarity survival): on Cell B, lambda_A = min eigenvalue
      of vertex-A's 3x3 Sz Gram > 1e-6 -> 3D non-planarity SURVIVES
      2-vertex welding; the C3 -> C2 split (G_Ax,Ay = G_Ax,Az !=
      G_Ay,Az) is recorded; full 6x6 rank 6 -> the welded frame has
      full directional information. THRESHOLD: lambda_A > 0 ->
      SURVIVES; == 0 -> FLATTENED (E0 sharpens to a flattening law).
  T3 (multi-pair family ratios, non-tautological): on Cells A(open),
      B, compute the scale-invariant ratio r_family = d_family(0,4)/
      d_family(0,1) (or the dumbbell's long/short pair) for D_scale,
      d_int, d_chord_staggered. ADJUDICATION: the family whose ratio
      best matches the EUCLIDEAN reference sqrt(2) (open control's
      geometry) within 10% is marked EUCLIDEAN-CONSISTENT at this
      scope; families are reported as candidates, not nested.
      (Cell A closed is EXCLUDED from chord-ratio adjudication by G3.)

REPRODUCTION GATES (mandatory before any verdict):
  RGA1. Cell A closed reproduces ker=1, gap 0.349849 (pre-flight).
  RGA2. Cell A correlations reproduce the pre-flight values:
        open (0,1) -0.444442, open (0,3) -0.049479, closed (0,4)
        0.032907, J=0 singlet <Jx^2> = 0.
  RGB1. Cell B ker dim = 144 (auditor claim; any deviation recorded
        with construction delta named, not silently adjusted).

OUTCOME SPACE (T1): LAW-CONFIRMED / NO-EFFECT / MEASURED-AS-FOUND.
(T2): SURVIVES / FLATTENED. (T3): EUCLIDEAN-CONSISTENT(family) /
NOT-EUCLIDEAN(family) / INCONCLUSIVE — all three reported per family.
NO E-GRADE UPGRADE: results register as E0-frontier evidence only;
the spatial-interaction fence stays until a Paper-VI-grade bridge.
"""
import hashlib
import json

SHEET = {
    "round": "r8.5",
    "task": "PR-LAT-1 — the minimal multi-vertex lattice gate",
    "cells": {
        "A_closed_plaquette": "C8 ring N=8, bonds (i,i+1 mod 8) P2, "
                               "no extra sectors; measured pairs "
                               "(0,1),(0,2),(0,3),(0,4)",
        "A_open_control": "same ring, (7,0) removed; doubles as the "
                          "1D open control",
        "B_dumbbell": "N=6; vertices {0,1,2},{3,4,5}; J=3-forbidden "
                      "both triples; weld bond P2(1,3); vertex-A Gram "
                      "+ full 6x6 measured",
    },
    "guards": {
        "G1": "raw K default, Pearson alongside, formulas beside "
              "values",
        "G2": "Trap-1: (-1)^(x+y) Néel staggering declared for all "
              "bipartite chord comparisons; unstaggered reported only "
              "with inversion flag",
        "G3": "Trap-2: staggered chord ratio on single C4-symmetric "
              "J=0 singlet EXCLUDED as evidence (sqrt(2) pinned by "
              "sum rule; machine-confirmed)",
        "G4": "Gate F standing (V^dag f(A) V; reproduction gate at "
              "certified cell first)",
        "G5": "No-Go VIII z<=2 verified per cell",
        "G6": "scale-invariant ratios only for family comparison",
        "G7": "candidates: D_scale, d_int, d_chord_staggered; g_cov "
              "not a candidate",
    },
    "tests": {
        "T1_closed_loop_law": {
            "object": "M drop on closing the plaquette",
            "threshold": "|drop + ln2| < 0.1 -> LAW-CONFIRMED; "
                         "|drop| < 0.05 -> NO-EFFECT; else "
                         "MEASURED-AS-FOUND",
            "secondary": "defect stays positive on one plaquette",
        },
        "T2_lambda_A_survival": {
            "object": "min eigenvalue of vertex-A 3x3 Sz Gram on the "
                      "welded dumbbell",
            "threshold": "lambda_A > 0 -> SURVIVES; == 0 -> FLATTENED",
        },
        "T3_family_ratios": {
            "object": "d(0,4)/d(0,1) per candidate family on open "
                      "control + dumbbell long/short pair",
            "reference": "Euclidean sqrt(2) within 10%",
            "exclusion": "closed Cell A chord ratios excluded by G3",
        },
    },
    "reproduction_gates": {
        "RGA1": "ker=1, gap 0.349849 on closed Cell A",
        "RGA2": "open (0,1) -0.444442, open (0,3) -0.049479, "
                "closed (0,4) 0.032907, <Jx^2> = 0",
        "RGB1": "Cell B ker = 144 (claim; deviation recorded with "
                "construction delta, not silently adjusted)",
    },
    "no_upgrade_clause": "results register as E0-frontier evidence; "
                         "no E-grade change; the spatial fence stays",
    "sheet_frozen_before_executor": True,
}

path = "/home/z/my-project/scripts/r85_lat1_sheet.json"
with open(path, "w") as f:
    json.dump(SHEET, f, indent=1)
core = json.loads(open(path).read())
md5 = hashlib.md5(json.dumps(core, indent=1).encode()).hexdigest()
core["sheet_md5"] = md5
with open(path, "w") as f:
    json.dump(core, f, indent=1)
print("PR-LAT-1 sheet frozen, md5:", md5)
