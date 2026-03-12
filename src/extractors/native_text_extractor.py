"""
Extrator de texto nativo de páginas PDF via PyMuPDF.

Para PDFs com texto digital (gerados por Word, LibreOffice, etc.),
a leitura direta da camada de texto é 100% fiel ao original —
sem confusão de caracteres (O vs 0), sem artefatos de compressão.

O módulo também detecta e estrutura tabelas usando page.find_tables().
"""

from __future__ import annotations

import fitz  # PyMuPDF
from src.models.document_model import OcrBlock, TableResult


# Número mínimo de palavras nativas para considerar a página como "digital".
# Páginas com menos palavras são tratadas como escaneadas (fallback para OCR).
_NATIVE_WORD_THRESHOLD = 20


def detect_page_mode(page: fitz.Page) -> str:
    """
    Detecta automaticamente como a página deve ser extraída.

    Conta as palavras no camada de texto nativa do PDF.
    Se houver palavras suficientes, o texto veio de um editor digital
    e pode ser lido diretamente. Caso contrário, a página é provavelmente
    uma imagem escaneada e precisa de OCR.

    Returns:
        "native"  — leitura direta (Word, InDesign, PDFs digitais)
        "ocr"     — página escaneada, requer Tesseract
    """
    words = page.get_text("words")
    return "native" if len(words) >= _NATIVE_WORD_THRESHOLD else "ocr"


def extract_native_blocks(page: fitz.Page, page_number: int) -> list[OcrBlock]:
    """
    Extrai blocos de texto da camada nativa do PDF.

    Usa page.get_text("blocks") que retorna parágrafos com coordenadas.
    Cada bloco é convertido para OcrBlock com confidence=100.0
    (texto nativo não tem imprecisão de reconhecimento).

    Args:
        page: Página PyMuPDF.
        page_number: Número da página (1-indexado).

    Returns:
        Lista de OcrBlock com texto e posição exatos.
    """
    blocks = []
    for b in page.get_text("blocks"):
        # b = (x0, y0, x1, y1, text, block_no, block_type)
        # block_type: 0 = text, 1 = image
        x0, y0, x1, y1, text, _, block_type = b

        if block_type != 0:  # ignora blocos de imagem
            continue

        text = text.strip()
        if not text:
            continue

        blocks.append(OcrBlock(
            text=text,
            confidence=100.0,   # texto nativo = certeza total
            page_number=page_number,
            x=int(x0),
            y=int(y0),
            width=int(x1 - x0),
            height=int(y1 - y0),
        ))

    return blocks


def extract_native_tables(page: fitz.Page) -> list[TableResult]:
    """
    Detecta e extrai tabelas da página usando PyMuPDF.

    page.find_tables() detecta linhas de grade e agrupa células
    automaticamente. Cada célula é lida como texto nativo (exato).

    Args:
        page: Página PyMuPDF.

    Returns:
        Lista de TableResult. Vazia se não houver tabelas na página.
    """
    tables: list[TableResult] = []

    try:
        found = page.find_tables()
    except Exception:
        return tables   # versão do PyMuPDF sem suporte a find_tables

    for i, table in enumerate(found.tables):
        try:
            raw = table.extract()   # list[list[str | None]]
        except Exception:
            continue

        # Limpa células None e linhas completamente vazias
        rows = []
        for raw_row in raw:
            row = [str(cell).strip() if cell is not None else "" for cell in raw_row]
            if any(cell for cell in row):   # descarta linhas 100% vazias
                rows.append(row)

        if rows:
            tables.append(TableResult(index=i, rows=rows))

    return tables
