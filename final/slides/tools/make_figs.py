#!/usr/bin/env python3
"""Rasterize the report figures for the slides:
  ER / schema PDFs  → img/er.png, img/schema.png
  FD tikz figures   → img/fd/<TABLE>.png and img/fd/after_<TABLE>.png
                      (tikzpictures extracted from phase4/fd_before.tex / fd_after.tex, compiled with tectonic)

    python3 final/slides/tools/make_figs.py
"""
import re

import subprocess
import tempfile
from pathlib import Path

import pymupdf as fitz

ROOT = Path(__file__).resolve().parents[3]
P4 = ROOT / "phase4"
IMG = ROOT / "final" / "slides" / "img"

PRE = r"""\documentclass[tikz,border=6pt]{standalone}
\usetikzlibrary{positioning,arrows.meta,fit,backgrounds,calc}
\usepackage{xeCJK}\setCJKmainfont{NotoSansTC-Medium.ttf}[Path=/Users/frank/Library/Fonts/]
\begin{document}
"""


def pdf_pages_to_png(pdf, outs, zoom=4.0):
    doc = fitz.open(pdf)
    for page, out in zip(doc, outs):
        page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).save(out)


def fd_figs(src, prefix):
    tex = src.read_text()
    pics = re.findall(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", tex, re.S)
    names = [re.search(r"\\bfseries\\sffamily\] at \([^)]*\) \{([^}]*)\}", p).group(1).replace("\\_", "_").split("\\quad")[0]
             for p in pics]
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "fd.tex"
        f.write_text(PRE + "\n".join(pics) + "\n\\end{document}\n")
        subprocess.run(["tectonic", "-X", "compile", "--outdir", d, str(f)], check=True, capture_output=True)
        (IMG / "fd").mkdir(parents=True, exist_ok=True)
        pdf_pages_to_png(Path(d) / "fd.pdf", [IMG / "fd" / f"{prefix}{n}.png" for n in names], zoom=5)
    return names


if __name__ == "__main__":
    IMG.mkdir(parents=True, exist_ok=True)
    pdf_pages_to_png(P4 / "ER圖" / "ER_drawio.pdf", [IMG / "er.png"], zoom=3)
    pdf_pages_to_png(P4 / "schema圖" / "schema_diagram.pdf", [IMG / "schema.png"], zoom=3)
    print("before:", fd_figs(P4 / "fd_before.tex", ""))
    print("after: ", fd_figs(P4 / "fd_after.tex", "after_"))
    for p in sorted(IMG.rglob("*.png")):
        print(f"  {p.relative_to(IMG)}")
