"""
Fixtures compartilhadas entre todos os testes do PDF OCR Reader.

Gera PDFs simples programaticamente via PyMuPDF para que os testes
de integração rodem sem precisar de arquivos externos em tests/samples/.

Os arquivos gerados ficam em tests/generated/ (ignorado pelo .gitignore).
"""

import pytest
from pathlib import Path
import fitz  # PyMuPDF

GENERATED_DIR = Path(__file__).parent / "generated"


def _ensure_generated_dir() -> Path:
    GENERATED_DIR.mkdir(exist_ok=True)
    return GENERATED_DIR


@pytest.fixture(scope="session")
def simple_pdf(tmp_path_factory) -> str:
    """
    PDF de uma página com texto simples em fundo branco.
    Ideal para testes de extração de texto e layout.
    """
    out_dir = _ensure_generated_dir()
    pdf_path = out_dir / "simple_test.pdf"

    if pdf_path.exists():
        return str(pdf_path)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Cabeçalho (y ~ 30-50px = top ~4-6%)
    page.insert_text((50, 40), "Cabecalho do Documento", fontsize=12, color=(0, 0, 0))

    # Corpo central
    body_lines = [
        "Este e um documento de teste para o PDF OCR Reader.",
        "Linha dois do corpo principal com mais texto.",
        "Terceira linha com palavras: Python, OCR, Tesseract.",
        "Email de contato: teste@exemplo.com.br",
        "Data: 10/03/2026",
    ]
    for i, line in enumerate(body_lines):
        page.insert_text((50, 200 + i * 30), line, fontsize=11, color=(0, 0, 0))

    # Rodapé (y ~ 800-820px = bottom ~95-97%)
    page.insert_text((50, 810), "Pagina 1 de 1 - Documento de Teste", fontsize=9, color=(0.4, 0.4, 0.4))

    doc.save(str(pdf_path))
    doc.close()

    return str(pdf_path)


@pytest.fixture(scope="session")
def two_page_pdf() -> str:
    """
    PDF de duas páginas para testar processamento de múltiplas páginas.
    """
    out_dir = _ensure_generated_dir()
    pdf_path = out_dir / "two_page_test.pdf"

    if pdf_path.exists():
        return str(pdf_path)

    doc = fitz.open()

    for page_num in range(1, 3):
        page = doc.new_page(width=595, height=842)
        page.insert_text(
            (50, 40),
            f"Cabecalho - Pagina {page_num}",
            fontsize=12,
        )
        page.insert_text(
            (50, 300),
            f"Conteudo principal da pagina {page_num}. Texto de exemplo para OCR.",
            fontsize=11,
        )
        page.insert_text(
            (50, 810),
            f"Rodape - Pagina {page_num} de 2",
            fontsize=9,
            color=(0.4, 0.4, 0.4),
        )

    doc.save(str(pdf_path))
    doc.close()

    return str(pdf_path)


@pytest.fixture(scope="session")
def real_sample_pdf() -> str | None:
    """
    Retorna o caminho do primeiro PDF real em tests/samples/, ou None se não houver.
    Use para testes que precisam de documentos reais (currículos, manuais).
    """
    samples_dir = Path(__file__).parent / "samples"
    pdfs = list(samples_dir.glob("*.pdf"))
    return str(pdfs[0]) if pdfs else None
