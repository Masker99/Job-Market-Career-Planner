from __future__ import annotations

from pathlib import Path

SUPPORTED_RESUME_SUFFIXES = {".txt", ".md", ".markdown", ".pdf"}
TEXT_RESUME_SUFFIXES = {".txt", ".md", ".markdown"}


def _read_text_resume(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Resume file is empty: {path}")
    return text


def _pdf_to_markdown(pdf_path: Path) -> Path:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ValueError(
            "PDF resume parsing requires pypdf. "
            "Please run: pip install -r requirements.txt"
        ) from exc

    reader = PdfReader(str(pdf_path))
    page_sections: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            page_sections.append(f"## Page {index}\n\n{page_text}")

    if not page_sections:
        raise ValueError(
            f"No text could be extracted from PDF resume: {pdf_path}. "
            "If this is a scanned PDF, please export it as text/Markdown first."
        )

    markdown_path = pdf_path.with_suffix(".md")
    markdown = f"# Resume\n\nSource PDF: {pdf_path.name}\n\n" + "\n\n".join(page_sections)
    markdown_path.write_text(markdown, encoding="utf-8")
    return markdown_path


def read_resume_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Resume file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Resume path is not a file: {path}")

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_RESUME_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_RESUME_SUFFIXES))
        raise ValueError(f"Unsupported resume file type: {suffix}. Supported: {supported}")

    if suffix == ".pdf":
        markdown_path = _pdf_to_markdown(path)
        return _read_text_resume(markdown_path)

    if suffix in TEXT_RESUME_SUFFIXES:
        return _read_text_resume(path)

    raise ValueError(f"Unsupported resume file type: {suffix}")
