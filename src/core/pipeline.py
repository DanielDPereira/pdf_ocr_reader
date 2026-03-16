"""
Pipeline central de processamento de PDF.

Módulo compartilhado entre CLI, GUI e API.
Encapsula toda a lógica de extração em uma única função reutilizável,
sem depender de qualquer interface específica (argparse, tkinter, FastAPI...).

Uso:
    from src.core.pipeline import run_pipeline

    result = run_pipeline("documento.pdf", lang="por+eng")
    print(result.to_json())
"""

from pathlib import Path

import fitz  # PyMuPDF

from src.extractors.hybrid_extractor import extract_pages_hybrid
from src.extractors.page_ocr import _PSM_AUTO
from src.extractors.image_extractor import extract_embedded_images
from src.extractors.metadata_extractor import extract_pdf_metadata
from src.processors.layout_analyzer import analyze_page_layout
from src.models.document_model import DocumentResult


def run_pipeline(
    pdf_path: str,
    lang: str = "por+eng",
    psm: int = _PSM_AUTO,
    preprocess: bool = True,
    hybrid: bool = True,
    verbose: bool = False,
) -> DocumentResult:
    """
    Processa um PDF e retorna o DocumentResult estruturado.

    Esta função é o núcleo do sistema: pode ser chamada pela CLI,
    pela GUI, pela API HTTP ou por qualquer outro consumidor.

    Args:
        pdf_path: Caminho absoluto ou relativo para o arquivo PDF.
        lang: Idiomas do Tesseract (padrão: "por+eng").
        psm: PSM do Tesseract; use _PSM_AUTO para detecção automática.
        preprocess: Se True, aplica pré-processamento de imagem antes do OCR.
        hybrid: Se True, usa extração nativa onde possível (recomendado).
                Se False, força OCR puro em todas as páginas.
        verbose: Se True, imprime progresso no stdout (útil para CLI).

    Returns:
        DocumentResult com metadados, páginas e imagens embutidas.

    Raises:
        FileNotFoundError: Se o arquivo PDF não existir.
        ValueError: Se o arquivo não for um PDF válido.
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    if verbose:
        mode_label = "híbrido (nativo + OCR fallback)" if hybrid else "OCR puro"
        print(f"Processando : {pdf.name}")
        print(f"Modo        : {mode_label}")
        print(f"Idioma OCR  : {lang}")

    # 1. Metadados
    if verbose:
        print("\n[1/4] Lendo metadados do PDF...")
    metadata = extract_pdf_metadata(str(pdf))
    if verbose:
        for k, v in metadata.to_dict().items():
            print(f"       {k}: {v}")

    # 2. Contagem de páginas
    with fitz.open(str(pdf)) as doc:
        total_pages = len(doc)

    document = DocumentResult(
        file_path=str(pdf),
        total_pages=total_pages,
        metadata=metadata,
    )

    # 3. Extração híbrida página a página
    if verbose:
        print(f"\n[2/4] Extraindo texto das páginas ({total_pages} pág.)...")

    for page_data in extract_pages_hybrid(
        str(pdf),
        lang=lang,
        verbose=verbose,
        preprocess=preprocess,
        psm=psm,
    ):
        page_result = analyze_page_layout(
            page_data.page_number,
            page_data.blocks,
            page_data.img_size[1],  # height
        )
        page_result.extraction_mode = page_data.mode
        page_result.tables = page_data.tables
        document.pages.append(page_result)

    # 4. Imagens embutidas
    if verbose:
        print("\n[3/4] Extraindo imagens embutidas...")
    images_by_page = extract_embedded_images(str(pdf), lang=lang)
    for page_result in document.pages:
        page_result.embedded_images = images_by_page.get(page_result.page_number, [])

    if verbose:
        print("\n[4/4] Concluído.")

    return document
