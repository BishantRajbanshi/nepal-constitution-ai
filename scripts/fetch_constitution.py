"""
Downloads (or reads) the Constitution of Nepal PDF and splits
Part 3 (Articles 16-48, Fundamental Rights) into one markdown
file per article: data/articles/article_16.md ... article_48.md

Usage:
    python scripts/fetch_constitution.py <url-or-path-to-pdf>
"""
import re
import sys
from pathlib import Path

import requests
from pypdf import PdfReader

RAW_PDF = Path("data/raw/constitution.pdf")
OUT_DIR = Path("data/articles")
FIRST, LAST = 16, 48   # Part 3: Fundamental Rights


def get_pdf(source: str) -> Path:
    """Download if source is a URL; otherwise treat as local path."""
    if source.startswith("http"):
        print(f"Downloading {source} ...")
        resp = requests.get(source, timeout=60)
        resp.raise_for_status()
        RAW_PDF.parent.mkdir(parents=True, exist_ok=True)
        RAW_PDF.write_bytes(resp.content)
        return RAW_PDF
    return Path(source)


def extract_text(pdf_path: Path) -> str:
    """Pull raw text from every page and join it."""
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    # PDFs are messy: collapse repeated whitespace but keep line breaks
    text = re.sub(r"[ \t]+", " ", text)
    return text


def split_articles(text: str) -> dict[int, str]:
    """
    Find headings like '16. Right to live with dignity:' and slice the
    text between consecutive article numbers.
    """
    # matches: start of line, number, dot, space, Title text, colon
    pattern = re.compile(r"^\s*(\d{1,3})\.\s+([A-Z][^\n:]{3,100}):", re.MULTILINE)
    matches = list(pattern.finditer(text))

    articles: dict[int, str] = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        if not (FIRST <= num <= LAST):
            continue
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        # keep the first occurrence only (numbers repeat in schedules/TOC)
        if num not in articles:
            articles[num] = body
    return articles


def write_files(articles: dict[int, str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for num, body in sorted(articles.items()):
        # first line is 'NN. Title:' — reuse as markdown heading
        title_line, _, rest = body.partition("\n")
        path = OUT_DIR / f"article_{num}.md"
        path.write_text(f"# Article {title_line}\n\n{rest.strip()}\n", encoding="utf-8")
        print(f"wrote {path} ({len(body)} chars)")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/fetch_constitution.py <url-or-pdf-path>")
    pdf = get_pdf(sys.argv[1])
    text = extract_text(pdf)
    articles = split_articles(text)
    print(f"\nFound {len(articles)} articles in range {FIRST}-{LAST}")
    missing = [n for n in range(FIRST, LAST + 1) if n not in articles]
    if missing:
        print(f"⚠ Missing: {missing} — check the PDF/regex")
    write_files(articles)


if __name__ == "__main__":
    main()
