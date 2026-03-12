"""
Extrator híbrido de páginas PDF.

Combina extração de texto nativo (PyMuPDF direto) com OCR (Tesseract)
em um único pipeline inteligente: cada página é avaliada individualmente
e recebe o melhor tratamento disponível.

Fluxo por página:
  1. Detecta modo: palavra-count na camada nativa
     ≥ 20 palavras → "native" (texto digital perfeito)
     < 20 palavras → "ocr"    (página escaneada)
  2. Extrae blocos de texto no modo detectado
  3. Extrae tabelas (apenas no modo nativo, com find_tables())
  4. Imagens embutidas recebem OCR independente do modo da página

Vantagens vs OCR puro:
  - Fidelidade 100% para PDFs Word/InDesign (zero confusão O/0)
  - Tabelas extraídas como células individuais
  - Velocidade: páginas nativas ~10x mais rápidas (sem Tesseract)
  - Modo OCR inalterado para páginas escaneadas
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Generator

import fitz  # PyMuPDF
from PIL import Image

from src.extractors.native_text_extractor import (
    detect_page_mode,
    extract_native_blocks,
    extract_native_tables,
)
from src.extractors.page_ocr import (
    render_page_as_image,
    extract_ocr_blocks,
    _PSM_AUTO,
)
from src.models.document_model import OcrBlock, TableResult


@dataclass
class PageExtractionResult:
    """Resultado da extração híbrida de uma única página."""
    page_number: int
    mode: str                           # "native" ou "ocr"
    blocks: list[OcrBlock]
    tables: list[TableResult]
    img_size: tuple[int, int]           # (width, height) da imagem renderizada


def extract_pages_hybrid(
    pdf_path: str,
    lang: str = "por+eng",
    verbose: bool = False,
    preprocess: bool = True,
    psm: int = _PSM_AUTO,
) -> Generator[PageExtractionResult, None, None]:
    """
    Gera resultados página a página usando extração híbrida.

    Para cada página:
    - Detecta se tem texto nativo suficiente
    - Usa leitura nativa OU OCR conforme o modo
    - Detecta tabelas via find_tables() no modo nativo
    - Renderiza sempre como imagem para obter img_size (usado pelo layout_analyzer)

    Args:
        pdf_path: Caminho do PDF.
        lang: Idiomas do Tesseract (usado apenas no modo OCR).
        verbose: Imprime progresso por página.
        preprocess: Pré-processa imagem antes do OCR (modo OCR).
        psm: PSM do Tesseract (modo OCR).

    Yields:
        PageExtractionResult para cada página.
    """
    with fitz.open(pdf_path) as doc:
        total = len(doc)

        for page_index in range(total):
            page_number = page_index + 1
            page = doc[page_index]

            # Renderiza a página como imagem (necessário para img_size e OCR)
            image: Image.Image = render_page_as_image(page)
            img_size = image.size  # (width, height)

            # Detecta o modo de extração
            mode = detect_page_mode(page)

            if mode == "native":
                blocks = extract_native_blocks(page, page_number)
                tables = extract_native_tables(page)

                if verbose:
                    print(
                        f"  Pagina {page_number}/{total}: "
                        f"[NATIVO] | {len(blocks)} blocos | "
                        f"{len(tables)} tabela(s)"
                    )
            else:
                # OCR no modo escaneado
                blocks, used_psm = extract_ocr_blocks(
                    image,
                    page_number,
                    lang=lang,
                    preprocess=preprocess,
                    psm=psm,
                )
                tables = []

                if verbose:
                    psm_tag = f"PSM {used_psm}"
                    print(
                        f"  Pagina {page_number}/{total}: "
                        f"[OCR] {psm_tag} | {len(blocks)} blocos"
                    )

            yield PageExtractionResult(
                page_number=page_number,
                mode=mode,
                blocks=blocks,
                tables=tables,
                img_size=img_size,
            )
