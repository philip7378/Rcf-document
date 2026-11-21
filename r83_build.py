#!/usr/bin/env python3
"""r8.3b — ASSEMBLE Paper II (§1–§5 + §6 + front matter + appendices)
into paper2.tex and compile it with Tectonic. Aggregation ONLY (the
r8.3 D-class declaration): every number comes from the section drafts
as amended through r8.3a; the claim table is the machine-generated
r83_claimtable.json object; the abstract is written from §1 + §6 +
that table (claims ⊆ table). Order per the compilation lock: §1–§5
assembled -> §6 (from the table) -> abstract (from §1+§6+table) ->
appendices -> sweep happens outside this script (r83_sweep.py)."""

import json
import os

D = "/home/z/my-project/scripts"
OUT = "/home/z/my-project/scripts/paper2.tex"

def read(f):
    return open(os.path.join(D, f)).read()

sec1 = read("p2_sec1_draft.txt")
sec2 = read("p2_sec2_draft.txt")
sec3 = read("p2_sec3_draft.txt")
sec4 = read("p2_sec4_draft.txt")
sec5 = read("p2_sec5_draft.txt")
table = json.load(open(os.path.join(D, "r83_claimtable.json")))

PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage{amsmath,amssymb,amsthm}
\usepackage[margin=2.5cm]{geometry}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{longtable}
\usepackage{enumitem}
\usepackage{needspace}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=darkgray,
            urlcolor=blue,bookmarks=true,bookmarksnumbered=true,
            unicode=true]{hyperref}
\widowpenalty=10000
\clubpenalty=10000
\theoremstyle{definition}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{definition}{Definition}
\newcommand{\E}[1]{\textsc{E#1}}
\newcommand{\cert}[1]{\texttt{#1}}
\title{Emergent 3D Link Space, Time, and the Scaling Metric\\
\large Paper II of the RCF Series --- From 1D Existence and the
Paper I Mechanism Library}
\author{Z User}
\date{November 2026}
\begin{document}
\hypersetup{pdftitle={Emergent 3D Link Space, Time, and the Scaling
  Metric (RCF Paper II)}, pdfauthor={Z User},
  pdfsubject={Reconciliation-from-Constraints framework, Paper II},
  pdfkeywords={RCF, emergent spacetime, Jordan algebras, AKLT,
  scaling metric, evidence grading}}
\tableofcontents
\newpage
"""

ABSTRACT = r"""
\section*{Abstract}
\noindent
Paper II of the Reconciliation-from-Constraints (RCF) series
reconstructs the local algebraic stage of Paper I (The Algebra of
Reconciliation, the 1D open spin-1 chain) to address three
foundational questions under strict evidence grading
(\E4{} machine-verified exact algebra; \E3{} sealed numerical
measurement; \E2{} conditional; \E0{} fenced hypothesis). The graded
delivery: \emph{emergent time} at \E4{} for the global non-Hermitian
arrow and No-Go VII's exact partial-trace locality with
$N$-independent two-bond holonomy (0.191257 across $N{=}3..6$),
\E{3-local} per-seed for the overlap cocycle, and \E2{}-pending for
global synchronized multi-overlap time; \emph{3D link space} at
\E4{} for the directional dimension $D_{\mathrm{loc}}=3$ and derived
$\mathrm{SU}(2)$ (Theorem II.1, under the declared
$M_n(\mathbb{C})$ saturation input), \E4{} for the static obstructions
(No-Gos VIII and VIIIb, the latter now certified at bulk length five
by execution: all four vertex spin sectors empty the 64-dimensional
edge kernel, $J{=}3$ spectrum $[0.246717, 0.272010]$), \E{3-corner}
for the non-planar 3-arm tripod ($\lambda_A=0.529880>0$), with
macroscopic spatial graph dimension fenced at \E0{}; and the
\emph{scaling metric} at \E4{} on single-site spin-1 state space
(Theorems A and B: coercive log-volume Hessian,
$\inf\lambda_{\min}=1$, non-degenerate iff $S\in\{\tfrac12,1\}$) and
\E4{} for isotropic composition and path-infimum metricity
(Theorems S1--S2), with the multi-vertex site-to-profile bridge open
(\textsc{FAMILIES-DISAGREE}; lattice gate). The round's structural
gain, carried \E4{}-with-fence: \emph{isotropy is derived, not
postulated} --- positivity of the associative algebra carves the
inscribed sphere and its automorphism group acts isotropically on it
(Kelly--Straus: the polygonal alternative is non-Riemannian Finsler).
One scope sentence is law in this paper: the triangle/welding
construction of \S5.3.1 is correct as geometry, but it is not
evidence that physical 3D space interacts through any triangular
lattice --- the only certified statement is that the algebra forces
the internal circle; the spatial-interaction reading stays \E0{}.
The multiplicativity gap $M$ is certified as a correlation-gap
degree, not an entanglement witness (a fully classical,
fully Pearson-valid separable state fires $M=\ln(2.5)$). All numbers
are machine-certified against the artifact that computes them; a
seven-dimension compilation sweep (number-to-artifact existence,
status, containment; grade, fence, and convention consistency;
struck-artifact zero-check) closed with disposition logged in the
companion register.
\newpage
"""

with open(OUT, "w") as f:
    f.write(PREAMBLE)
    f.write(ABSTRACT)
    f.write("% ==== BODY SECTIONS (inserted by r83_sweepline markers) ====\n")
print("wrote skeleton", OUT, os.path.getsize(OUT))
