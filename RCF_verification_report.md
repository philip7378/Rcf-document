# RCF Reconciliation Check — Independent Verification Report

**Date:** 2026-08-11
**Scope:** Independent reproduction of the 1-qubit tilted-Pauli and 2-qubit computations
claimed in a prior session, checked against the definitions in
`RCF_Review_Addendum_Variance_Retraction.pdf` (Def. 3.1, §4) and the v3.0 canonical rewrite.
**Scripts:** `rcf_check_1qubit.py`, `rcf_check_2qubit.py`, `rcf_make_figure.py`
**Figure:** `rcf_reconciliation_verification.png`

All computations use F̂_MM = Σ_{α,β} ω(J²_αβ) · Δ†_αβ Δ_αβ with J_αβ = Ĉα∘Ĉβ,
Δ_αβ = [Ĉα, Ĉβ], ω(·) = Tr(ρ ·), summed over all ordered pairs including α=β.

---

## Part 1 — 1-qubit tilted-Pauli (Ĉα = cosθ σα + sinθ 1)

| # | Claim | Verdict | Measured |
|---|-------|---------|----------|
| 1 | Leibniz: Lie derives Jordan, converse fails | **CONFIRMED** | forward residual ≤ 1.2×10⁻¹⁴; converse mean residual ≈ 19.9 (nonzero) |
| 2 | Pauli-zero: F_MM(θ=0) = 0 for all states | **CONFIRMED** | exactly 0.0 over 8 random states |
| 3 | Split F_MM = 24s²c⁴(1+c²) + 32s³c⁵(r₁+r₂+r₃) | **CONFIRMED** | worst deviation 2.7×10⁻¹⁵ vs direct matrix computation, random Bloch vectors, 4 values of θ; F_MM ∝ 1 exactly |
| 4 | Driver factorizes Lie×Jordan, zero at θ=0 and θ=π/2 | **CONFIRMED** | W(0)=0, W(π/2)=0; peak at tan²θ=3/5 → **37.76°** |
| 5 | Flow → r = −(1,1,1)/√3; B∈[2.53, 9.28] at θ=30° | **CONFIRMED** | B_min = 2.53125, B_max = 9.28125 (ratio 3.67×); numerical gradient flow converges to (−0.577,−0.577,−0.577) |
| — | F⁰_MM floor peak ≈ 6 at θ ≈ 32.8° (addendum) | **CONFIRMED** | 6.0000 at 32.76° |

**Note on the prior session's numbers.** The specific table values (e.g. F_MM = 2.9427943647
at θ=0.2618) depend on the random Bloch vector used and cannot be reproduced without the seed;
what is verified is that the split formula matches direct computation to machine precision for
*any* state, which is the substantive claim. The claimed peak "38.2°" is slightly off: the exact
peak of W(θ) is at tan²θ = 3/5, i.e. **37.76°**. (Minor; possibly a rounding or grid artifact
in the original.)

## Part 2 — 2-qubit case (Ĉα = cosθ σα⊗1 + sinθ 1⊗σα)

| # | Claim | Verdict | Measured |
|---|-------|---------|----------|
| F1 | Δ†Δ = 4[(c⁴+s⁴) 1⊗1 + 2c²s² σγ⊗σγ] | **CONFIRMED** | max error 1.9×10⁻¹⁵ |
| F2 | J² = 2c²s²(1⊗1 + σγ⊗σγ) (α≠β) | **CONFIRMED** | max error 3.1×10⁻¹⁶ |
| F3 | F_MM = 16c²s² Σγ(1+tγ)[(c⁴+s⁴)1 + 2c²s² σγ⊗σγ] | **CONFIRMED** | max error 5.2×10⁻¹⁵ |
| F4 | B_MM = 16c²s² Σγ(1+tγ)[(c⁴+s⁴) + 2c²s² tγ] | **CONFIRMED** | max error 3.1×10⁻¹⁵ |
| P1 | Pauli-zero at θ=0 AND θ=π/2 | **CONFIRMED** | 0.0 and 3.9×10⁻³¹ over 5 random states |
| P2 | Spectra at θ=π/4: mixed [0,8,8,8]; Φ⁺ [0,8,8,16]; singlet all-zero | **CONFIRMED** | exact match |
| P3 | Driver weights: (c⁴+s⁴) vs 2c²s², equal at 45°, ratio 7 at 15°/75° | **CONFIRMED** | 7.00 / 1.67 / 1.00 / 1.67 / 7.00 |
| P4 | Leibniz survives in M₄(ℂ) | **CONFIRMED** | max residual 4.4×10⁻¹⁶ |
| — | Gradient ∂B/∂tγ = 16c²s²(1+4c²s² tγ) | **CONFIRMED** | vs numerical diff: 5×10⁻¹⁰ |
| — | Singlet fixed point t* = (−1,−1,−1) at θ=π/4 | **CONFIRMED** | F_MM(singlet) = 0 exactly |

## Part 3 — Two corrections to the prior session's claims

### Correction 1: the singlet is NOT a state-independent zero mode at general θ
The prior session claimed *"the singlet direction |Ψ⁻⟩ is always a zero mode of F_MM
regardless of the state ρ — it's built into the operator's structure."*

**This is true only at θ = π/4.** Measured:

| θ | ‖F_MM · ψ⁻‖ (random ρ) |
|---|---|
| 0.400 | 2.711 (nonzero) |
| π/4 | 0.000 |
| 1.000 | 2.015 (nonzero) |

The exact law: the singlet eigenvalue of F_MM is
**λ_singlet = 16c²s² cos²(2θ) · Σγ(1+tγ)** — it vanishes identically only when cos2θ = 0
(θ=π/4). So "c = ℓ₀√λ_min = 0 everywhere" is a **θ=π/4 degeneracy**, not a generic
structural failure of the speed-limit formula. Away from the symmetric point the spectral
gap is nonzero and state-dependent, and the formula is not trivially broken.

### Correction 2: the gap does NOT "stay at 8 then drop abruptly"
The prior session claimed the spectral gap *"stays at 8 until the state is the singlet, then
drops to 0 abruptly."* Along the Werner line ρ(p) = (1−p)𝟙/4 + p|Ψ⁻⟩⟨Ψ⁻| at θ=π/4:

| p | eig(F_MM) |
|---|---|
| 0.00 | [0, 8, 8, 8] |
| 0.50 | [0, 4, 4, 4] |
| 0.90 | [0, 0.8, 0.8, 0.8] |
| 1.00 | [0, 0, 0, 0] |

The nonzero eigenvalues decrease **linearly and continuously** (8(1−p)), exactly in step with
the gradient magnitude. There is no abrupt drop. The flow slows smoothly as the state
approaches the singlet — spectrum and gradient tell the same story, which is *cleaner* than
the prior session suggested.

## Part 4 — What this settles about driver/driven

- **Algebraic level:** Lie is a derivation of Jordan (residual ~10⁻¹⁵); the converse fails
  (residual ~20). The "causality drives" intuition holds *at this level only*.
- **Dynamical level:** the driver is the product of a Lie factor and a Jordan factor —
  1-qubit: 32sin³θ·cos⁵θ; 2-qubit: 16c²s²(1+tγ)·[(c⁴+s⁴)+2c²s²tγ]. Either factor
  zero ⇒ no flow. Neither link "pushes" the other; their **incompatibility** is the engine
  and reconciliation removes it.
- **Pauli-zero** is exact, state-independent, and (per the addendum §5.2) robust under
  multi-sector extension — it is the "fully reconciled limit," a physical prediction.
- **Consistency with the addendum:** everything above matches the restored ω(J²)
  construction (Option a). Nothing computed here touches T-2/T-3, the multi-sector
  cross-channel, or the hierarchical principle — those remain OPEN per the addendum
  scorecard, and these finite-dimensional checks cannot close them.
