#!/usr/bin/env python3
"""r8.3b — merge cover + body into the final Paper II PDF (A4-normalized)."""
from pypdf import PdfReader, PdfWriter

A4_W, A4_H = 595.28, 841.89

def normalize_page_to_a4(page):
    box = page.mediabox
    w, h = float(box.width), float(box.height)
    if abs(w - A4_W) > 2 or abs(h - A4_H) > 2:
        page.scale_to(A4_W, A4_H)
    return page

writer = PdfWriter()
cover_page = normalize_page_to_a4(PdfReader("paper2_cover.pdf").pages[0])
writer.add_page(cover_page)
for page in PdfReader("paper2.pdf").pages:
    writer.add_page(page)
with open("paper2_final.pdf", "wb") as f:
    writer.write(f)
print("merged:", len(writer.pages), "pages")
