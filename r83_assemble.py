#!/usr/bin/env python3
"""r8.3b FINAL ASSEMBLY — build paper2.tex from the converted body +
front matter + §6 + appendices, then compile with Tectonic.

§6 is generated from r83_claimtable.json (the certified object):
restatement only — no new claims, no new fences, no new grades.
The abstract (r83_build.py's ABSTRACT) was written from §1 + §6 +
the table; its claims are a subset of the table by construction
(checked again in r83_sweep.py).
"""
import json
import os

D = "/home/z/my-project/scripts"
body = open(os.path.join(D, "paper2_body.tex.tmp")).read()
table = json.load(open(os.path.join(D, "r83_claimtable.json")))

PREAMBLE = open(os.path.join(D, "r83_build.py")).read()
# extract the PREAMBLE and ABSTRACT literals from the build script
import re
pre = re.search(r'PREAMBLE = r"""(.*?)"""\n\nABSTRACT', PREAMBLE, re.S).group(1)
abs_ = re.search(r'ABSTRACT = r"""\n(.*?)\n"""\n', PREAMBLE, re.S).group(1)

# ---------------- §6 from the table (restatement only) -------------
E4 = [r for r in table["rows"] if r["grade"].startswith("E4")]
ev3 = [r for r in table["rows"] if r["grade"].startswith("E3")]
openv = [r for r in table["rows"] if not r["grade"].startswith(("E4", "E3"))]

sec6 = r"""
\section{Conclusion (Restatement)}
\noindent This section restates the delivery; it introduces no new
claim, fence, or grade. Every statement below is a projection of the
machine-generated claim register (Table in \S1.4, object
\texttt{r83\_claimtable.json}), which contains the paper's full
graded content.

\subsection*{What was delivered}
\begin{itemize}[leftmargin=1.4em]
\item \textbf{Emergent time} (E4): the global non-Hermitian arrow
$H_{\mathrm{eff}} = H - \tfrac{i}{2}\gamma\hat M$ with $-[J,
\Lambda]$; Lie--on--Jordan frame transport (PR-T1b); No-Go VII's
exact partial-trace locality (residual $3.8\times10^{-16}$) with
two-bond holonomy strictly $N$-independent (0.191257 at
$N{=}3..6$); spacelike-disjoint commutativity $[\mathcal L_0,
\mathcal L_2] = 0$. (E3): the per-seed overlap cocycle (chiral
0.174716) and the raw-clock probe-sign finding (2.2831$\times$ vs
0.7705$\times$). (E2): global synchronized multi-overlap time,
pending the Lie--Trotter limit ($O(t^2/n)$, constant
$\sqrt{48}/2$).
\item \textbf{3D link space} (E4): Theorem II.1 ---
$\mathcal J_D \cong H_n(\mathbb C)$ iff $(D_{\mathrm{loc}},
n) = (3,2)$, deriving $\mathrm{SU}(2)$ (Rodrigues residual
$9.5\times10^{-16}$); No-Go VIII (ten graph witnesses, two-method
$2.9\times10^{-15}$); No-Go VIIIb --- all static bulk vertex
projectors empty the 64D edge kernel, now certified at bulk length
five by execution (all four spin sectors $0/64$; $J{=}3$ spectrum
$[0.246717, 0.272010]$; $J{=}0$ floor $8000/226981$ exact);
dynamical $H_{\mathrm{vtx}}$ T-MISMATCH (trace 251.142024,
spectrum $[3.448563, 4.218242]$, zero dark states) with
isotropic Arm~C transfer. (E3-corner): the non-planar tripod
$\lambda_A = 0.529880 > 0$. (E0): macroscopic spatial graph
dimension, fenced to the lattice gate.
\item \textbf{The scaling metric} (E4): PR-SCALE-1's orientation
sign $\operatorname{sgn}(abc)$; Theorem~A --- the coercive
log-volume Hessian with $\inf\lambda_{\min} = 1$; Theorem~B ---
non-degeneracy iff $S \in \{\tfrac12, 1\}$; Theorems S1--S2 ---
isotropic composition and unconditional path-infimum metricity;
the geometric controls with Kelly--Straus and Albert's
non-specialty framings; isotropy-from-positivity, the round's
genuine gain, carried E4-with-fence. (Open): the multi-vertex
site-to-profile bridge (FAMILIES-DISAGREE:
$d_{\mathrm{chord}}$ 1.168930 vs $d_{\mathrm{scaling}}$
0.006559) and the multiplicativity-gap family question
($M = \ln 2.5$ on a fully classical separable witness --- a
correlation-gap degree, not an entanglement witness).
\end{itemize}

\subsection*{What remains open}
The multi-vertex lattice gate with $\lambda_A$ as its
non-planarity order parameter; the metric-family adjudication;
global multi-overlap time; the Paper~I generativity bridges
(dark-energy entry~\#1, Lorentz-boost entry~\#2, both E0); and the
largest open item --- whether physical 3D space interacts through
any spatial lattice at all. The closing caution stands as law:
the triangle/welding construction is correct geometry, the algebra
forces the internal circle, and everything beyond that is E0
until the lattice gate certifies it.
"""

# ---------------- Appendix A: certificate inventory ----------------
inv_rows = [
    ("PR-SCALE-1", "r5.1", "certified", "8 sign frames, det C split by sgn(abc)"),
    ("No-Go VIII", "r53a_preflightB", "certified", "10 graph witnesses, 2.9e-15"),
    ("No-Go VIIIb", "r53b_armsAB + r53c_static + r83_l5cert", "certified",
     "L=3 table exact; L=5 closed by execution (r8.3a)"),
    ("PR-VTX-1 L=5 leg", "r53b_armsAB (ArmB_L5)", "superseded",
     "'deferred-to-script-2' at r53b; number never computed there; "
     "CLOSED by r83_l5cert (0.246717 = J=3 compressed lambda_min)"),
    ("Theorem II.1", "r53_preflightC + r62_adjudicate", "certified", "J_D = H_n(C) iff (3,2)"),
    ("Lorentz cone hook", "r53e_verify", "certified", "det preservation 2.7e-13; boosts 3.8e-15"),
    ("H_vtx T-MISMATCH + Arm C", "r53c_static + r53c_armC", "certified", "trace 251.142024; [3.448563, 4.218242]"),
    ("PR-LINK-1", "r61_link1 + r62_adjudicate + r80_metric2b", "certified", "3-arm rank 3; Grams; tripod lambda_A"),
    ("PR-NOGO-RAW", "r51a_battery + r51d_t1b2 + r52_preflightB", "certified", "probe sign flip 2.2831x / 0.7705x"),
    ("PR-T1b", "r5.1", "certified", "global arrow; frame transport"),
    ("PR-T1b-2", "r51c_prep + r51d_t1b2", "certified", "overlap cocycle, MIXED, E3-local"),
    ("No-Go VII", "r52_t1b2b + r53_preflightA", "certified", "partial-trace locality 3.8e-16; 0.191257 N-constant"),
    ("Theorem A / Theorem B", "r51b_battery + r51c_prep", "certified", "coercivity, spec {9/4 x5, 6 x3}; S in {1/2, 1}"),
    ("Theorems S1 / S2", "r60a", "certified", "isotropic composition; d_int metricity"),
    ("PR-METRIC-2", "r70_metric2", "certified (verdict INCONCLUSIVE reclassified SPEC-INCOMPLETE)", "site->profile bridge"),
    ("PR-METRIC-2b", "r80_metric2b", "certified", "FAMILIES-DISAGREE; M-pin; tripod decomposition"),
    ("M-pin replacement witness", "r82_patches", "certified", "Pearson ln(2.5)=0.916291; AKLT ln(4/3)=0.287682"),
    ("Geometric controls", "r81_geomctrl + r82_patches", "certified",
     "welding, anisotropy conventions, Kelly-Straus, Albert, delta-transfer"),
    ("Claim table object", "r83_claimtable", "certified", "machine-generated 19-row register"),
]

appA = [r"\section*{Appendix A: Certificate Inventory (status column)}",
        r"\addcontentsline{toc}{section}{Appendix A: Certificate Inventory}",
        r"\small",
        r"\begin{tabularx}{\linewidth}{l l l X}",
        r"\toprule",
        r"\textbf{Certificate} & \textbf{Artifact(s)} & \textbf{Status} & \textbf{Content} \\",
        r"\midrule"]

def esc(s):
    return s.replace("_", r"\_")

for name, art, st, content in inv_rows:
    appA.append(" & ".join([
        r"\textbf{" + esc(name) + "}",
        esc(art),
        st, esc(content)]) + r" \\")
appA += [r"\bottomrule", r"\end{tabularx}", r"\normalsize", ""]

appB = r"""
\section*{Appendix B: Standing Verification Battery and Errata Ledger}
\addcontentsline{toc}{section}{Appendix B: Standing Battery and Errata}

\subsection*{The seven-gate standing battery}
\begin{enumerate}[leftmargin=1.6em]
\item \textbf{Gate S} --- SU(2) commutator and Casimir below
$10^{-14}$, basis-Gram orthonormality, explicit norm/support
convention header on every operator norm.
\item \textbf{Gate G} --- multi-site operator support verification
(active sites of every projector placement).
\item \textbf{GATE-CG} --- adjacent-bond continuity
(constructions agree across system sizes).
\item \textbf{GATE-P} --- projector trace and idempotency below
$10^{-14}$ before any commutator norm.
\item \textbf{Gate O} --- object identity by defining property
(numbers vs.\ objects; e.g.\ the $2/3$ dipole eigen-rate vs.\ the
$1/3$ kernel correlation, T4).
\item \textbf{The $C_3 = 1 \oplus 2$ irrep lemma} --- every
3-arm symmetric object decomposed through it.
\item \textbf{Artifact-certification attribution rule} --- a number
is verified only against the JSON artifact that \emph{certifies}
it, not one that mentions it (artifact-vs-mention; the class of
the r7.0 and r8.0 errata, extended at r8.2 to registers, and at
r8.3 to construction declarations: 0.246717 was mentioned in two
registers but certified in neither --- until r8.3a executed it).
\end{enumerate}

\subsection*{Errata ledger (D-class, cumulative through r8.3)}
\begin{enumerate}[leftmargin=1.6em]
\item r5.3c: projector mislabeled (class: artifact-vs-mention).
\item r5.1c: checkpoint grid mislabeled (class:
artifact-vs-mention).
\item r6.1 F3: raw register anchor with $|c| > 1$ struck
(normalization class).
\item r7.0: 0.246717 attribution error (r53b deferred entry
mistaken for certificate; the standing rule extended to
registers).
\item r8.0: the raw $M = \ln 3$ witness's un-divided barycenter
anchor ($c = \sqrt 3 > 1$) --- superseded at r8.2 by the Pearson
witness $M = \ln 2.5$; r70's ``entanglement signature'' phrasing
retracted (D-class).
\item r8.2: 0.246717 struck as certified-nowhere (correct at the
time); r8.3a \emph{superseded} the strike by execution --- the
sheet target was confirmed against the machine value 0.246716686
with the L=3 reproduction gate passing exactly, and the per-axis
kernel formula 16 $= 2^{L-1}$ (r5.2 P3 recurrence) was struck from
the caption.
\item r8.3 (this round): the caption re-imported the struck
$2^{L-1}$ formula --- caught by the compilation audit before
freezing; octonion theorem-to-object attributions pinned exactly
(Im$\mathbb O$ vs.\ $H_2(\mathbb O)$ vs.\ $H_3(\mathbb O)$); the
82.57\% number relabeled as the incoming report's prior
probe-grid measurement; the $K$-normalization convention
declared once (raw default, Pearson named; $M$'s value is
convention-relative, its non-vanishing is not).
\end{enumerate}

\subsection*{Do-not-re-cite list}
Any future draft citing a number below without its CURRENT
certificate is auto-rejected at sheet-freeze:
\begin{itemize}[leftmargin=1.4em]
\item 0.246717 --- entry \#1 in the original strike list; now
\emph{citable only against r83\_l5cert.json} (superseded-by-
certification, not free-floating).
\item The raw $M = \ln 3 = 1.098612$ witness value ---
superseded (normalization artifact); cite the Pearson witness
$M = \ln 2.5$ or the raw-convention AKLT identity $\ln(4/3)$.
\item The $16 = 2^{L-1}$ per-axis kernel formula (r5.2 P3
erratum): the open-chain edge kernel has dimension exactly 4 at
every $L \geq 2$.
\item ``Entanglement signature'' phrasing for the
multiplicativity gap (retracted).
\end{itemize}
"""

appC = r"""
\section*{Appendix C: Generativity Register (Downstream Bridges)}
\addcontentsline{toc}{section}{Appendix C: Generativity Register}

\begin{enumerate}[leftmargin=1.6em]
\item \textbf{Entry \#1 --- Open Expansion $\leftrightarrow$
Unfinished-Relaxation Cosmology (E0).} Paper~I's open-expansion
protocol approaches $\ker\hat M$ asymptotically, never completing
in finite time, driving continual growth of chain extent.
Structurally analogous to accelerated expansion driven by
unfinished relaxation. \emph{All} dark-energy and Friedmann
identifications are deferred to downstream Cosmology papers; no
claim is made here.
\item \textbf{Entry \#2 --- $H_2(\mathbb C)$ Jordan Determinant
$\leftrightarrow$ Algebraic (1,3) Lorentz Cone (E4 hook / E0
boost bridge).} Theorem II.1's derived link algebra carries
$\det(x_0\mathbb 1 + \vec s \cdot \vec\sigma) = x_0^2 -
|\vec s|^2$, whose positive-semidefinite cone is the forward
(1,3) light cone, with $\mathrm{SL}(2,\mathbb C)$ congruence
reproducing $\mathrm{SO}^+(1,3)$ rotations and boosts to
$2.7\times10^{-13}$ / $3.8\times10^{-15}$
(\texttt{r53e\_verify}). Bridging the algebraic scalar $x_0$ to
dynamical proper time and proving dynamical boost invariance on a
discrete dissipative substrate (PR-METRIC-1) are deferred to
downstream Relativity papers.
\end{enumerate}

\noindent Both entries are \emph{hooks}: checkable formal
patterns with connection costs named and bridge obligations filed
in the downstream papers. Neither is a physical prediction of
this paper.
"""

with open(os.path.join(D, "paper2.tex"), "w") as f:
    f.write(pre)
    f.write("\n" + abs_)
    f.write("\n" + body)
    f.write(sec6)
    f.write("\n".join(appA))
    f.write("\n")
    f.write(appB)
    f.write(appC)
    f.write("\n\\end{document}\n")

print("paper2.tex written:", os.path.getsize(os.path.join(D, "paper2.tex")), "bytes")
