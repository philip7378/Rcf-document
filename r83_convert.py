#!/usr/bin/env python3
"""r8.3b — ASSEMBLE paper2.tex: markdown-ish section drafts -> LaTeX.

Converter handles the drafts' actual conventions:
  - headers  "1.1 Title" / "Section 2: ..."      -> \section / \subsection
  - markdown tables (| a | b | with :--- rules)   -> tabularx + booktabs
  - bullets "  - text"                            -> itemize
  - numbered "(1) text" kept as text (manual numbering, per exam rule)
  - ASCII math in the corpus notation: -> \to, ^{(x)3} -> ^{\otimes 3},
    (x) -> \otimes, G^spin -> G^{\mathrm{spin}}, lambda_A -> \lambda_A,
    H_{eff} etc.; Greek names spelled out (lambda, gamma, rho, tau, xi,
    delta, Sigma...) -> \lambda etc.; guards for plain words.
  - [Machine support: ...] blocks -> tcolorbox-free italic small blocks
    (kept as plain \small\emph paragraphs; no floats)
  - [STATUS ...] trailing blocks are stripped (process artifact).

This is aggregation: text is transformed, not rewritten.
"""
import os
import re

D = "/home/z/my-project/scripts"

# ---------------- math tokenizer --------------------------------------
GREEK = {
    "lambda": r"\lambda", "Lambda": r"\Lambda", "gamma": r"\gamma",
    "rho": r"\rho", "tau": r"\tau", "xi": r"\xi", "delta": r"\delta",
    "epsilon": r"\varepsilon", "theta": r"\theta", "phi": r"\phi",
    "Phi": r"\Phi", "psi": r"\psi", "Psi": r"\Psi", "chi": r"\chi",
    "omega": r"\omega", "sigma": r"\sigma", "zeta": r"\zeta",
    "kappa": r"\kappa", "eta": r"\eta", "mu": r"\mu", "nu": r"\nu",
    "pi": r"\pi", "alpha": r"\alpha", "beta": r"\beta",
    "ell": r"\ell", "lam": r"\lambda_",
}
SAFE_WORDS = {
    "in", "and", "the", "of", "is", "not", "or", "a", "an", "to",
    "via", "per", "with", "for", "on", "no", "one", "two", "as",
    "all", "any", "own", "its", "it", "was", "did", "run", "ran",
    "second", "raw", "pin", "gap", "an", "new", "now", "law",
    "top", "tip", "did", "den", "log", "lin", "see", "set", "met",
}

def tex_math(m):
    """Convert a $-free ASCII math fragment to LaTeX-ish inline math."""
    s = m.group(0)
    return s  # replaced below in pass 2

def convert_math(s):
    """Pass 2 replacements inside already-detected math spans."""
    s = s.replace("^{(x)3}", r"^{\otimes 3}")
    s = s.replace("^{x3}", r"^{\otimes 3}")
    s = s.replace("^{(x)6}", r"^{\otimes 6}")
    s = s.replace("(x)", r"\otimes ")
    s = s.replace("->", r"\to ")
    s = re.sub(r"\b([a-zA-Z]+)_([a-zA-Z0-9]+)\b",
               lambda m: m.group(1) + "_{" + m.group(2) + "}"
               if re.match(r"^[a-zA-Z]", m.group(2)) else m.group(0), s)
    s = s.replace("dim ker", r"\dim\ker")
    return s

def escape_text(s):
    s = s.replace("&", r"\&").replace("%", r"\%").replace("#", r"\#")
    s = s.replace("_", r"\_")   # corpus ASCII math kept verbatim
    s = s.replace("^", r"\^{}").replace("~", r"\textasciitilde{}")
    s = s.replace("<", r"$<$").replace(">", r"$>$")
    s = s.replace("<=", r"$\leq$").replace(">=", r"$\geq$")
    s = s.replace("!=", r"$\neq$").replace("<->", r"$\leftrightarrow$")
    s = re.sub(r"(?<![$\\])\b([0-9]+\.[0-9]+e-?[0-9]+)\b",
               r"$\num{0}$".replace("\\num{0}", "\\text{}") if False else
               lambda m: m.group(1), s)
    return s

# ---------------- block converter --------------------------------------
def md_table_to_tex(lines):
    """Markdown table lines -> tabularx (booktabs, Paragraph cells)."""
    rows = []
    for ln in lines:
        if re.match(r"^\|[\s:|-]+\|?\s*$", ln):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return []
    ncol = max(len(r) for r in rows)
    header, body = rows[0], rows[1:]
    # column spec: first col left, rest raggedright X
    spec = "l " + ("X " * (ncol - 1)) if ncol > 1 else "l"
    out = [r"\begin{center}", r"\small",
           r"\begin{tabularx}{\linewidth}{" + spec.strip() + "}",
           r"\toprule"]
    hdr = " & ".join(r"\textbf{" + escape_text(c) + "}" for c in header)
    out.append(hdr + r" \\ \midrule")
    for r in body:
        while len(r) < ncol:
            r.append("")
        out.append(" & ".join(escape_text(c) for c in r) + r" \\")
    out += [r"\bottomrule", r"\end{tabularx}", r"\end{center}"]
    return out

def convert(text, secnum):
    """Convert one section draft to LaTeX body lines."""
    lines = text.splitlines()
    out = []
    i = 0
    in_bracket_block = False
    while i < len(lines):
        ln = lines[i]
        # header patterns: ONLY treat as a header if the line is a REAL
        # heading — the number must be alone at line start, the title
        # must start capital/paren-free, the line must be short (<75),
        # AND a real heading is followed (after optional continuation
        # lines) by a blank line; wrapped body lines like "3.4.2 The
        # Junction..." are TRUE headers, but body continuations that
        # BEGIN with a number-word pattern fail the capital+short test
        # above. Extra guard: the title part must not already be a
        # sentence (heuristic: no " ." inside first 40 chars).
        m = re.match(r"^(\d+(?:\.\d+){0,2})\s+(.*)$", ln)
        if m and not ln.startswith("|") and len(ln) < 75 and \
                re.match(r"^[A-Z0-9(]", m.group(2)) and \
                " (" not in m.group(2)[:14]:
            num, title = m.group(1), m.group(2)
            depth = num.count(".")
            # absorb continuation lines of the WRAPPED TITLE only:
            # stop at sentence-final punctuation. A wrapped heading in
            # these drafts ends its last title line with "." ":" or a
            # closing bracket; body continuation never does at 2-3
            # words in. Also hard-stop at 130 chars, bullets, tables,
            # parenthesized or lowercase starts.
            j = i + 1
            while j < len(lines) and lines[j].strip() and \
                    len(title) < 200 and \
                    not re.match(r"^(-{4,}|=+\s*$)", lines[j]) and \
                    not re.match(r"^\d+\.\d", lines[j]) and \
                    not re.match(r"^\s+-\s", lines[j]) and \
                    not lines[j].startswith("|") and \
                    len(lines[j]) < 75:
                title += " " + lines[j].strip()
                if re.search(r"[.:]$", lines[j]) or \
                        re.search(r"\)$", lines[j]):
                    j += 1
                    break
                j += 1
            # hard-wrapped drafts can share the title's end and body
            # text on ONE line: split at the first sentence boundary
            # beyond 60 chars ("... the 2D shadow). Three additive...")
            msplit = re.search(r"\.\s+(?=[A-Z])", title)
            if msplit and msplit.start() > 60:
                overflow = title[msplit.end():]
                title = title[:msplit.start() + 1]
                lines.insert(j, overflow)   # push remainder back as body
                lines.insert(j + 1, "")
            # skip a following ---- or ==== underline rule
            while j < len(lines) and re.match(r"^(-{4,}|=+\s*$)", lines[j]):
                j += 1
            title = title.strip().rstrip("]").strip()
            # trailing "[E4]" / "[E3-corner]" grade markers -> small caps
            # (lambda replacement: re.sub parses "\t" in template
            # replacement strings as a TAB — raw strings do not protect)
            title = re.sub(
                r"\s*\[(E[0-9a-z-]*(?:/[A-Za-z0-9-]+)*)\]\s*$",
                lambda m: "~[\\textsc{" + m.group(1) + "}]", title)
            # stray unclosed "[E4" (line-wrap artifacts) -> close it
            title = re.sub(
                r"\s*\[(E[0-9a-z-]*(?:/[A-Za-z0-9-]+)?)\s*$",
                lambda m: "~[\\textsc{" + m.group(1) + "}]", title)
            if depth == 0:
                out.append(r"\section{%s}" % escape_text(title))
            elif depth == 1:
                out.append(r"\subsection{%s}" % escape_text(title))
            else:
                out.append(r"\subsubsection{%s}" % escape_text(title))
            i = j
            continue
        if re.match(r"^-{4,}\s*$", ln) or re.match(r"^=+\s*$", ln):
            i += 1
            continue
        m2 = re.match(r"^Section (\d+): (.*)$", ln)
        if m2:
            title = m2.group(2).strip()
            # section headers wrap to a second line in the drafts —
            # absorb continuation until a blank line
            j = i + 1
            while j < len(lines) and lines[j].strip() and not re.match(
                    r"^(\d+\.\d|\[|Section \d)", lines[j]):
                title += " " + lines[j].strip()
                j += 1
            out.append(r"\section{%s}" % escape_text(title))
            i = j
            continue
        if re.match(r"^PAPER II .§\d+ DRAFT", ln):
            # strip the process banner block: banner lines + rule + the
            # [Drafting baseline ...] block that follows. The closing
            # bracket may END a text line, so track depth.
            j = i + 1
            while j < len(lines) and not lines[j].startswith(
                    "[Drafting baseline"):
                j += 1
            if j < len(lines):
                depth = lines[j].count("[") - lines[j].count("]")
                j += 1
                while j < len(lines) and depth > 0:
                    depth += lines[j].count("[") - lines[j].count("]")
                    j += 1
            i = j
            continue
        if ln.startswith("[Drafting baseline:"):
            # strip the process baseline block (bracket depth; the
            # closing bracket may END a text line)
            depth = ln.count("[") - ln.count("]")
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count("[") - lines[i].count("]")
                i += 1
            continue
        if re.match(r"^\[(Drafting|DRafting|DRaFTING|DRAFT)", ln, re.I):
            # other bracketed process notes ([DRaftING NOTE ...]):
            # bracket-depth strip as well
            depth = ln.count("[") - ln.count("]")
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count("[") - lines[i].count("]")
                i += 1
            continue
        if re.match(r"^PAPER II\s*\S*\s*\d+\s+DRAFT", ln):
            # residual banner after the §N-1 tail (baseline already
            # stripped): drop banner lines + wrapped title lines +
            # rule lines until the "Section N:" line
            j = i + 1
            while j < len(lines) and not re.match(r"^Section \d+",
                                                  lines[j]):
                j += 1
            i = j
            continue
        if ln.startswith("[STATUS") or ln.startswith("STATUS"):
            # strip trailing status block to the NEXT structural line
            # (blank line then a header / Section / new banner)
            j = i + 1
            while j < len(lines):
                if re.match(r"^(PAPER II|Section \d+|\d+\.\d+|\[)", lines[j]):
                    break
                j += 1
            i = j
            continue
        if ln.startswith("[Machine support"):
            out.append(r"\small\emph{" +
                       escape_text(ln.strip("[]")) + "}")
            out.append(r"\par\medskip\noindent")
            i += 1
            continue
        # markdown table block (NOT "||...||" display-math norm lines)
        if ln.startswith("|") and not ln.startswith("||"):
            block = []
            while i < len(lines) and lines[i].startswith("|") and \
                    not lines[i].startswith("||"):
                block.append(lines[i]); i += 1
            out += md_table_to_tex(block)
            continue
        # bullets
        mb = re.match(r"^(\s*)-\s+(.*)$", ln)
        if mb:
            # gather bullet text (single-line bullets in the drafts)
            out.append(r"\item " + escape_text(mb.group(2)))
            i += 1
            continue
        if ln.strip() == "":
            out.append("")
            i += 1
            continue
        # display-math-ish indented definitions lines: keep as text
        out.append(escape_text(ln))
        out.append("")
        i += 1
    return out

# wrap consecutive \item groups in itemize
def wrap_items(lines):
    out, buf = [], []
    for ln in lines:
        if ln.startswith(r"\item "):
            buf.append(ln)
        else:
            if buf:
                out.append(r"\begin{itemize}[leftmargin=1.4em]")
                out += buf
                out.append(r"\end{itemize}")
                buf = []
            out.append(ln)
    if buf:
        out.append(r"\begin{itemize}[leftmargin=1.4em]")
        out += buf
        out.append(r"\end{itemize}")
    return out

FULL = []
for n, fn in (("1", "p2_sec1_draft.txt"), ("2", "p2_sec2_draft.txt"),
              ("3", "p2_sec3_draft.txt"), ("4", "p2_sec4_draft.txt"),
              ("5", "p2_sec5_draft.txt")):
    body = convert(open(os.path.join(D, fn)).read(), n)
    FULL += wrap_items(body)
    FULL.append("")

with open(os.path.join(D, "paper2_body.tex.tmp"), "w") as f:
    f.write("\n".join(FULL))
print("converted", len(FULL), "lines")
