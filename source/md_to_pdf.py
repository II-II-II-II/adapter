#!/usr/bin/env python3
"""
Convert a resume markdown file into a styled, ATS-safe PDF.

Markdown file format:
  ---
  name: Jordan Avery
  title: Solutions Architect | Platform Engineering & Applied AI
  contact: Columbus, OH | 555-010-0100 | jordan.avery@example.com | linkedin.com/in/example
  ---
  > Optional pitch line as a blockquote. Use this when the application has no
  > cover-letter field — it is the first thing a human reads.

  ## Summary
  ...

  ## What Maps to This Role
  - **Bolded lead-in**: the evidence, in a sentence.

  ## Professional Experience

  ### COMPANY NAME | City, ST
  *Job Title* | Jan 2020 - Apr 2026
  - bullet
  - bullet

  ## Projects
  ## Education

Usage:
  python3 md_to_pdf.py resume.md [output.pdf]
"""
import re
import subprocess
import sys
from pathlib import Path

import markdown

SCRIPT_DIR = Path(__file__).resolve().parent
CSS_PATH = SCRIPT_DIR / "resume_style.css"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def parse_front_matter(text: str):
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not match:
        raise ValueError(
            "Markdown file must start with a --- front matter block containing "
            "name / title / contact fields."
        )
    raw_fields, body = match.groups()
    fields = {}
    for line in raw_fields.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields, body


def build_html(fields: dict, body_html: str, css: str) -> str:
    name = fields.get("name", "")
    title = fields.get("title", "")
    contact = fields.get("contact", "")
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>{name} - Resume</title>
<style>{css}</style>
</head>
<body>
<h1>{name}</h1>
<div class="title-line">{title}</div>
<div class="contact-line">{contact}</div>
{body_html}
</body>
</html>
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 md_to_pdf.py resume.md [output.pdf]")
        sys.exit(1)

    md_path = Path(sys.argv[1]).resolve()
    if not md_path.exists():
        print(f"File not found: {md_path}")
        sys.exit(1)

    pdf_path = (
        Path(sys.argv[2]).resolve()
        if len(sys.argv) > 2
        else md_path.with_suffix(".pdf")
    )
    html_path = md_path.with_suffix(".render.html")

    text = md_path.read_text()
    fields, body_md = parse_front_matter(text)

    body_html = markdown.markdown(
        body_md, extensions=["extra", "sane_lists"]
    )
    css = CSS_PATH.read_text()
    full_html = build_html(fields, body_html, css)
    html_path.write_text(full_html)

    result = subprocess.run(
        [
            CHROME,
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path}",
            f"file://{html_path}",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stderr)
        sys.exit(1)

    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
