"""Document text extraction helpers for Phase 2 multi-format uploads."""
import io
from typing import Dict, Callable


def _parse_text(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")


def _parse_pdf(file_bytes: bytes) -> str:
    import pymupdf as fitz
    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n\n".join(text_parts).strip()


def _parse_docx(file_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text).strip()


def _parse_html(file_bytes: bytes) -> str:
    from bs4 import BeautifulSoup
    html = file_bytes.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    # Remove script/style elements
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _parse_csv(file_bytes: bytes) -> str:
    import pandas as pd
    df = pd.read_csv(io.BytesIO(file_bytes))
    return df.to_string(index=False)


PARSERS: Dict[str, Callable[[bytes], str]] = {
    ".txt": _parse_text,
    ".md": _parse_text,
    ".json": _parse_text,
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".html": _parse_html,
    ".htm": _parse_html,
    ".csv": _parse_csv,
}


def extract_text(file_bytes: bytes, file_extension: str) -> str:
    """
    Extract plain text from supported file bytes.
    Raises ValueError for unsupported formats.
    """
    ext = file_extension.lower()
    parser = PARSERS.get(ext)
    if not parser:
        supported = ", ".join(sorted(PARSERS.keys()))
        raise ValueError(f"Unsupported file format '{ext}'. Supported: {supported}")

    text = parser(file_bytes)
    if not text or not text.strip():
        raise ValueError("The uploaded file is empty or could not be parsed.")

    return text.strip()
