"""
Extração de metadados do PDF.

Lê os metadados nativos do PDF (título, autor, etc.) via PyMuPDF.
Esses dados vêm dos campos Info do arquivo e podem estar vazios
para PDFs criados sem configurar metadados.
"""

import fitz  # PyMuPDF
from src.models.document_model import PdfMetadata


def _clean(value: str | None) -> str | None:
    """Remove espaços, strings vazias e valores D: de data inválidos."""
    if not value:
        return None
    value = value.strip()
    return value if value else None


def _format_pdf_date(raw: str | None) -> str | None:
    """
    Converte data no formato PDF (D:20260310183000-03'00')
    para o formato legível (2026-03-10 18:30:00 -03:00).
    """
    if not raw or not raw.startswith("D:"):
        return _clean(raw)
    try:
        # D:YYYYMMDDHHmmSSOHH'mm'
        s = raw[2:]  # remove "D:"
        year = s[0:4]
        month = s[4:6]
        day = s[6:8]
        hour = s[8:10] if len(s) > 8 else "00"
        minute = s[10:12] if len(s) > 10 else "00"
        second = s[12:14] if len(s) > 12 else "00"
        tz = s[14:] if len(s) > 14 else ""
        tz = tz.replace("'", ":").rstrip(":")
        return f"{year}-{month}-{day} {hour}:{minute}:{second} {tz}".strip()
    except Exception:
        return _clean(raw)


def extract_pdf_metadata(pdf_path: str) -> PdfMetadata:
    """
    Extrai metadados nativos do PDF via PyMuPDF.

    Args:
        pdf_path: Caminho para o arquivo PDF.

    Returns:
        PdfMetadata com os campos disponíveis preenchidos.
        Campos ausentes no PDF ficam como None.
    """
    with fitz.open(pdf_path) as doc:
        meta = doc.metadata or {}

    return PdfMetadata(
        title=_clean(meta.get("title")),
        author=_clean(meta.get("author")),
        creator=_clean(meta.get("creator")),
        producer=_clean(meta.get("producer")),
        subject=_clean(meta.get("subject")),
        creation_date=_format_pdf_date(meta.get("creationDate")),
        modification_date=_format_pdf_date(meta.get("modDate")),
    )
