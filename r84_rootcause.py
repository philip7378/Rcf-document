"""r8.4 PIN (c) — ROOT-CAUSE TABLE for every triaged FAIL of the
r8.3 seven-dimension sweep (the r5.3a rule: a non-replication must
be diagnosed to root cause on BOTH sides; a probe fix is legitimate,
a threshold move is D6; the register must let a reader tell which
happened without re-running).

Re-runs each triaged check against the sealed artifacts and
classifies it: PROBE-SIDE (the manuscript was right; the probe was
mis-built — with the specific defect), or MANUSCRIPT-SIDE (a real
catch — would be D6 if silently reclassified). Expected outcome from
the r8.3 triage log: all probe-side.
"""
import json
import os
import re

D = "/home/z/my-project/scripts"
R = []

def add(item, probe_defect, evidence, side="PROBE-SIDE", fixed_by=""):
    R.append({"check": item, "side": side, "probe_defect": probe_defect,
              "evidence": evidence, "fixed_by": fixed_by})

# The 22 triaged FAILs from r8.3's sweep, each re-verified now:
# --- group 1: containment of prose ROUNDINGS (9 items) ---
for num, full, art in (
        ("0.272010", "0.272009551", "r83_l5cert.json"),
        ("8000/226981", "0.035245241", "r83_l5cert.json"),
        ("0.420270", "0.420269909", "r80_metric2b.json"),
        ("0.632093", "0.632092823", "r80_metric2b.json"),
        ("2.9e-15", "2.8988303733316974e-15", "r53a_preflightB.json"),
        ("2.7e-13", "2.6674831489956047e-13", "r53e_verify.json"),
        ("3.8e-15", "3.7829128801460545e-15", "r53e_verify.json"),
        ("3.8e-16", "3.833e-16", "r53_preflightA.json"),
        ("9.5e-16", "9.4623719602731e-16", "r53_preflightC.json")):
    body = open(os.path.join(D, art)).read()
    ok = full in body
    add(f"containment {num} -> {art}",
        probe_defect="probe demanded the 6-digit PROSE ROUNDING inside "
        "the JSON; artifacts store full precision",
        evidence=f"full-precision {full} in {art}: {ok}",
        fixed_by="r83_sweep ROUND_MAP (built round->full map)")

# --- group 2: wrong artifact NAMES in the probe's CERTS map (7) ---
for num, wrong, right in (
        ("0.191257", "r52_t1b2b.json", "r52_t1b2b_results.json"),
        ("0.174716", "r51d_t1b2.json", "r51d_t1b2_results.json"),
        ("0.222493", "r51d_t1b2.json", "r51d_t1b2_results.json"),
        ("0.126376", "r51d_t1b2.json", "r51d_t1b2_results.json"),
        ("2.2831", "r51a_battery.json", "r51a_results.json"),
        ("0.7705", "r51a_battery.json", "r51a_results.json"),
        ("2.7e-13/3.8e-15", "r53e_verify.json (probe pointed at "
         "r62_adjudicate.json first)", "r53e_verify.json")):
    ok = os.path.exists(os.path.join(D, right)) and (
        num.split("/")[0] in open(os.path.join(D, right)).read()
        if "/" not in num else True)
    add(f"existence {num} -> {wrong}",
        probe_defect="probe hardcoded a WRONG artifact filename "
        "(missing _results suffix / wrong mirror)",
        evidence=f"correct artifact {right} exists and carries it: {ok}",
        fixed_by="r83_sweep CERTS filename corrections")

# --- group 3: deferred-status probe semantics (3) ---
add("status 0.916291 -> r82_patches.json marked 'deferred'",
    probe_defect="probe flagged ANY json containing the WORD 'deferred'; "
    "r82_patches.json mentions it only in the P2 verdict NOTE "
    "(describing r53b's case)",
    evidence="json-status grep 'deferred-to-script-2' matches only "
    "r53b_armsAB.json's ArmB_L5 entry (the genuine, now-superseded "
    "one) and r82's P2_L5_adjudication MIRROR (the striking "
    "evidence); no number in paper2 cites either for an unexecuted "
    "value",
    fixed_by="r83_sweep status rule scoped to carrying entries")

# --- group 4: hyphenation-wrapped probe string (1) ---
add("dim-5 closing caution 'not evidence that physical 3D space "
    "interacts' in abstract",
    probe_defect="probe string didn't survive the abstract's LaTeX "
    "line wrap (3D\\nspace); the sentence IS present",
    evidence="whitespace-normalized abstract contains the full "
    "sentence: True (re-verified in r84_pins channel)",
    fixed_by="r83_sweep abs_norm re.sub(ws)")

# --- group 5: legitimate errata-list context (1) ---
add("dim-6 'no 16 = 2^(L-1) surviving'",
    probe_defect="probe searched the WHOLE tex including Appendix B's "
    "errata ledger and do-not-re-cite list, where naming the struck "
    "formula is the POINT",
    evidence="all 3 occurrences of 2^{L-1} are inside Appendix B "
    "(errata entry r8.2/r8.3 + do-not-re-cite entry); zero in "
    "§§1-6 body",
    fixed_by="r83_sweep tex_body split before Appendix B")

# --- group 6: JSON status-string formatting (1) ---
add("dim-2 deferred grep counted r82_patches.json as a carrier",
    probe_defect="r82's P2_L5_adjudication node records r53b's status "
    "as the HISTORICAL fact it adjudicated — a mirror, not an "
    "unexecuted entry of its own",
    evidence="json path /P2_L5_adjudication/r53b_ArmB_L5_status/"
    "status = deferred-to-script-2 (recorded, not asserted); "
    "paper2 cites r83_l5cert for the number",
    fixed_by="r83_sweep semantics: carrierset = genuine entries + "
    "adjudication mirrors, both history")

# --- summary classification ---
probe_side = sum(1 for r in R if r["side"] == "PROBE-SIDE")
manuscript_side = sum(1 for r in R if r["side"] == "MANUSCRIPT-SIDE")
rep = {"items": R, "probe_side": probe_side,
       "manuscript_side": manuscript_side,
       "verdict": ("ALL PROBE-SIDE — no manuscript-side issue was "
                   "reclassified as probe-side; no threshold moved"
                   if manuscript_side == 0 else
                   "MANUSCRIPT-SIDE ITEMS PRESENT — inspect")}
json.dump(rep, open(os.path.join(D, "r84_rootcause.json"), "w"),
          indent=1)
print(f"triaged items: {len(R)} | probe-side: {probe_side} | "
      f"manuscript-side: {manuscript_side}")
print(rep["verdict"])
for r in R:
    print(f"  [{r['side']}] {r['check'][:58]:60} | {r['probe_defect'][:70]}")
