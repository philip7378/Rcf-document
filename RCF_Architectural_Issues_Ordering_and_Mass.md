# RCF: Two Architectural Issues in the Current (SOE/MOE) Rewrite

Raised by the author, checked against the source text. Both confirmed. Companion to `RCF_Version_Analysis_and_Best_Selections.md` and `RCF_Legacy_to_Current_Migration_Map.md`.

---

## Issue 1 — The physical sub-algebra is used before it's earned

### The claim
Sub-algebras should fall out of the reconciliation principle once it has something (causality, relational correlation) to operate on. Introducing them before that makes them an input to the emergence ladder instead of an output of it.

### The evidence
Section 0, §0.4.1 (SOE flow), current draft — formal equation:
> dρ/dt|SOE^spec = i[√(F̂ + δF̂(E_new)), ρ]

"E_new" (a **new event**) is used here as a primitive input to the foundational dynamics. But "event" has no formal definition in Section 0. Its only formal definition anywhere is:

Section 1, Definition 1.1.1:
> E ∈ A_phy such that π_kin(E) ker(M̂) ⊆ ker(M̂) and [E, P̂_0] = 0

which requires **A_phy**, defined in Section 0, §0.6:
> A_phy = {A ∈ 𝒜 : π_kin(A) ker(M̂) ⊆ ker(M̂)}

— itself built from ker(M̂), i.e. from R_t's own output (§0.4–0.5). So the dependency chain is:

**§0.4 (uses "event") → §1.1.1 (defines "event", needs A_phy) → §0.6 (defines A_phy, needs ker(M̂)) → §0.4/0.5 (produces ker(M̂))**

That's a loop, not a chain. Section 0 reaches forward into Section 1 for a concept, and Section 1 reaches back into Section 0 for the algebra to define it — before Sections 1 (causality) or 2 (correlation) have contributed anything of their own to what "physical" should mean.

### Corroborating find
Both older drafts (`.docx` and `unnumbered`) carry:
> Theorem 0.6.3 (Fixed-Point Characterization). [A, R_∞] = 0 iff A ∈ A_phy and A restricted... [Theorem Target]

This is the theorem that would prove A_phy really is the fixed-point/Dirac-observable algebra — i.e., that it deserves the load-bearing role Sections 1–2 give it. **It does not appear in the current SOE/MOE draft.** It wasn't resolved; it was dropped, along with the honest flag that the question was still open.

### Proposed fix
1. In §0.4, replace "incorporation of a new event E_new" with something that doesn't borrow Section 1's vocabulary — e.g. a raw perturbation δĈ to the primitive constraint set. Purely algebraic, no forward reference.
2. Split §0.6 into two things:
   - Keep a *thin* version early (spectral compatibility with ker(M̂) only) — call it a candidate set, not "the physical sector sub-algebra."
   - Move the *full* definition — A_phy as the operators compatible with ker(M̂) **and** the causal order ≺ (Section 1) **and** the correlation kernel K_ω (Section 2) — to after Section 2. This is the version that deserves the name, and it's genuinely derived rather than assumed.
3. Section 1's Definition 1.1.1 then needs a lighter-weight notion of "event" that only needs the thin candidate set from step 2, not the full A_phy. This is very likely doable, since d(E) (reconciliation depth) and ker(M̂)-compatibility don't obviously need the full closure property to be well-defined.
4. Re-derive (or re-flag) Theorem 0.6.3 once A_phy's full definition is in its new location — this is the theorem that certifies the restructuring actually worked.

This is a real rewrite of Section 0's back half and Section 1's opening, not a relabeling. Worth doing before further sections are built on top of the current ordering.

---

## Issue 2 — Mass should be a resistance, not a static rest-frame number

### The claim
Mass = a configuration's resistance to reconciliation. This should explain: (a) rest mass existing at all, (b) mass increasing with speed, (c) clocks slowing with speed, and (d) mass/energy being the same kind of quantity in GR — all from one mechanism.

### Where the current draft stands
Section 4, Theorem 4.2.2 (current, "Derived"):
> Rest mass m is the spectral gap of F̂ within the particle's extension: m = λ_min(F̂_excited)... The maintenance burden B_0 = Tr(ρ_ground F̂_E).

No velocity term anywhere in Section 4, in any of the three drafts.

Section 3, Corollary 3.3.3 (current) — unresolved in **all three** drafts:
> Objects in relative motion belong to different open extensions — their interaction increases the cross-extension burden I_k. The standard Lorentz factor dτ = dσ√(1−v²/c²) is the leading-order term of the cross-extension MOE descent cost bounded by the SOE propagation speed c. [Theorem Target] — explicit derivation from the causal speed bound required.

These two are never connected. Section 3 already names the exact channel (I_k, interaction/cross-extension burden) that ought to carry velocity-dependence, and already expects it to produce a Lorentz factor — it just hasn't been derived, and nobody has pointed it at Section 4's mass definition.

### Why the reframing is the right move
- **At rest:** resistance-to-reconciliation should reduce to the existing λ_min(F̂) result. Nothing currently derived is lost.
- **In motion:** the same I_k channel Section 3 already flags should carry the increase — giving mass increase and time dilation as two readouts of one quantity, rather than two separate unresolved claims in two different sections.
- **Mass/energy unification:** Section 5's burden tensor already splits into mode / interaction / relational channels that jointly source gravity (§5.1.2). If mass is resistance-to-reconciliation, it's just the mode-channel's contribution to the same tensor that energy, in general, is built from — mass and energy end up the same *kind* of thing by construction, which is the point E=mc² is making in GR.

### The honest gap
Getting an *increasing-with-v* quantity out of I_k is plausible and probably not hard. Getting the *exact* γ = 1/√(1−v²/c²) out of it — rather than some other monotonic function — is precisely the derivation Section 3 already flags as missing. This reframing is a strong argument for *where* to look, not a completed proof.

### One refinement worth adopting
Modern SR deliberately avoids "relativistic mass" as the primary concept, keeping rest mass invariant and putting velocity-dependence into momentum/energy instead — because "mass increases with speed" historically caused real confusion (e.g., the false idea that fast objects approach becoming black holes). Worth mirroring here: keep **mass** as the invariant, v = 0 value of resistance-to-reconciliation, and introduce a separate, explicitly velocity-dependent quantity — I_k itself is the natural candidate — for the general case. Same physics, cleaner concepts, and it matches how the framework already separates "rest burden" from "interaction burden" in Section 5.

---

## Bottom line

Both issues are genuine, both are checkable against the text (not just plausible-sounding), and both point at the same kind of gap the migration-map document already flagged: the current draft sometimes keeps a conclusion (a sub-algebra, a mass-burden proportionality) while the machinery that would justify it — or the connection to a mechanism that's sitting right next door — hasn't been carried over or built yet.
