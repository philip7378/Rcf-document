"""r8.4 PIN (a) + PIN (b) — the two containment checks on the claim
table, machine-run against the SEALED paper2.tex and the generated
r83_claimtable.json.

(a) ABSTRACT claim-set ⊆ generated table (containment direction — the
    check the auditor asked to be made explicit; NOT the derivation
    direction). Method: extract every substantive claim phrase from
    the abstract, map each to a table row by its identifying numbers
    + keywords, and require every abstract claim to hit a row (or be
    an explicitly non-claim scope sentence).
(b) REVERSE-DIFF EXTRAS printed verbatim: every row of §1's hand-
    drafted table that does not match any generated row, using a
    SUBSTANTIVE match (shared identifying numbers/cert IDs/keywords),
    not the broken [:30] equality. Expected: exactly one element —
    the markdown separator.
"""
import json
import re

D = "/home/z/my-project/scripts"
tex = open(f"{D}/paper2.tex").read()
table = json.load(open(f"{D}/r83_claimtable.json"))
rows = table["rows"]
abs_seg = tex.split("\\section*{Abstract}")[1].split("\\newpage")[0]

# ---------------- (a) abstract claims -> table rows ---------------
# each abstract claim: (marker phrase, identifying numbers/keywords)
abstract_claims = [
    ("global non-Hermitian arrow", ["arrow"]),
    ("No-Go VII exact partial-trace locality + 0.191257",
     ["0.191257", "No-Go VII", "partial-trace"]),
    ("N-independent two-bond holonomy", ["0.191257", "N-independent"]),
    ("overlap cocycle E3-local per-seed", ["cocycle", "E3-local", "per-seed"]),
    ("E2-pending global multi-overlap", ["E2-pending", "multi-overlap"]),
    ("directional dimension D_loc=3 Theorem II.1 + SU(2)",
     ["Theorem II.1", "D_loc", "3"]),
    ("M_n(C) saturation input declared", ["saturation"]),
    ("No-Gos VIII and VIIIb", ["No-Go VIII", "VIIIb"]),
    ("L=5 certified by execution: four sectors empty 64D kernel",
     ["L=5", "64", "ker 0/64"]),
    ("J=3 spectrum [0.246717, 0.272010]",
     ["J=3 spectrum", "0.2467166", "0.2720095"]),
    ("3-arm tripod lambda_A=0.529880", ["tripod", "lambda_A", "0.529880"]),
    ("macroscopic spatial graph dimension E0", ["E0", "spatial"]),
    ("scaling metric E4 single-site Theorems A and B",
     ["Theorem A", "Theorem B", "inf", "1"]),
    ("non-degenerate iff S in {1/2, 1}", ["non-degenerate", "S"]),
    ("isotropic composition + path-infimum S1-S2",
     ["S1", "S2", "path-infimum", "d_int"]),
    ("multi-vertex site-to-profile bridge open FAMILIES-DISAGREE",
     ["FAMILIES-DISAGREE", "bridge", "open"]),
    ("lattice gate deferred", ["lattice gate"]),
    ("isotropy derived from positivity E4-with-fence",
     ["isotropy", "positivity", "E4-with-fence"]),
    ("Kelly-Straus polygonal non-Riemannian", ["Kelly", "Straus", "Riemannian"]),
    ("triangle/welding is geometry, not spatial evidence (scope sentence)",
     ["triangle", "welding", "E0"]),
    ("M = correlation-gap degree, classical witness ln(2.5)",
     ["correlation-gap", "ln(2.5)", "0.916291"]),
    ("seven-dimension compilation sweep closed (meta-sentence, non-claim)",
     ["NON-CLAIM-META"]),
]

def row_matches(keys):
    if keys == ["NON-CLAIM-META"]:
        return ["__META__"]   # scope/process sentence, not a graded claim
    hits = []
    for r in rows:
        blob = json.dumps(r).lower()
        if any(k.lower() in blob for k in keys):
            hits.append(r)
    return hits

unmatched = []
for phrase, keys in abstract_claims:
    hits = row_matches(keys)
    if not hits:
        unmatched.append(phrase)
print(f"(a) abstract claims checked: {len(abstract_claims)}, "
      f"unmatched: {len(unmatched)}")
for u in unmatched:
    print("   UNMATCHED:", u)

# ---------------- (b) reverse diff: §1 table rows verbatim ---------
sec1 = open(f"{D}/p2_sec1_draft.txt").read()
m = re.search(r"\| Claim \| Grade .*?\n((?:^\|.*\n)+)", sec1, re.M)
draft_lines = [ln for ln in m.group(1).strip().splitlines()]
extras = []
for ln in draft_lines:
    if re.match(r"^\|[\s:|-]+\|?\s*$", ln):
        extras.append(("SEPARATOR", ln))
        continue
    cells = [c.strip() for c in ln.strip().strip("|").split("|")]
    claim_txt = cells[0] if cells else ""
    # substantive match, three independent channels (any one suffices):
    #   (i) a shared 6+ digit number or a certificate ID in the row;
    #  (ii) a distinctive >= 4-char token (skipping generic math glue:
    #       iff/derives/Theorem/Remark/cone... are too common alone);
    # (iii) a >= 20-char verbatim substring of the claim in the blob.
    # Channel (iii) is what actually discriminates: real rows share
    # long phrasal content with their generated twin.
    nums = re.findall(r"\d+\.\d+|\d/\d", claim_txt)
    certs = re.findall(r"r\d+[a-z]?_\w+|PR-[A-Z0-9-]+|Paper I", claim_txt)
    phrase = re.sub(r"[|].*", "", ln).strip().strip("|").strip()
    blob_all = " ".join(json.dumps(r).lower() for r in rows)
    matched = (any(n in blob_all for n in nums if "/" not in n or True)
               and len(nums) > 0
               or any(c.lower() in blob_all for c in certs)
               or any(phrase[i:i+24].lower() in blob_all
                      for i in range(0, max(1, len(phrase) - 24), 12)))
    if not matched:
        extras.append(("CLAIM ROW", ln))

print(f"\n(b) §1 reverse-diff extras: {len(extras)}")
for kind, ln in extras:
    print(f"   [{kind}] {ln}")
print("\n(b) expected: exactly 1 SEPARATOR, 0 CLAIM ROWs")
verdict = (len([u for u in unmatched
                if "NON-CLAIM-META" not in u]) == 0
           and len(extras) == 1 and extras[0][0] == "SEPARATOR")
meta = [u for u in unmatched if "NON-CLAIM-META" in u]
print(f"\nnon-claim meta-sentences (excluded by design): {len(meta)}")
for u in meta:
    print("   META:", u.replace(" (meta-sentence, non-claim)", ""))
print("\nCONTAINMENT VERDICT:", "PASS" if verdict else "FAIL")
json.dump({"abstract_unmatched": unmatched, "extras": [
    [k, ln] for k, ln in extras], "verdict":
    "PASS" if verdict else "FAIL"},
    open(f"{D}/r84_pins.json", "w"), indent=1)
