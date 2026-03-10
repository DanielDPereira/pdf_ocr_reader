"""
Testes para o extrator de OCR de páginas completas.

Para rodar: pytest tests/test_page_ocr.py -v
Requer: Tesseract-OCR instalado e um PDF de exemplo em tests/samples/
"""

import pytest
from pathlib import Path
from PIL import Image, ImageDraw

import src.config  # garante detecção automática do Tesseract
from src.extractors.page_ocr import extract_ocr_blocks, extract_pages_ocr
from src.models.document_model import OcrBlock


SAMPLES_DIR = Path(__file__).parent / "samples"

# Verifica se o Tesseract está disponível para uso nos testes
_tesseract_available = src.config._configured_path is not None
_skip_if_no_tesseract = pytest.mark.skipif(
    not _tesseract_available,
    reason="Tesseract não encontrado. Instale o Tesseract-OCR para rodar estes testes.",
)


def create_test_image_with_text(text: str, size=(800, 200)) -> Image.Image:
    """Cria uma imagem simples com texto para testar o OCR."""
    img = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 80), text, fill="black")
    return img


class TestExtractOcrBlocks:
    """Testes unitários do extract_ocr_blocks com imagem sintética."""

    @_skip_if_no_tesseract
    def test_returns_list_of_ocr_blocks(self):
        """Deve retornar uma lista de OcrBlock."""
        image = create_test_image_with_text("Hello World")
        blocks, _ = extract_ocr_blocks(image, page_number=1, lang="eng")
        assert isinstance(blocks, list)

    @_skip_if_no_tesseract
    def test_blocks_have_required_fields(self):
        """Cada bloco deve ter texto, confiança e página."""
        image = create_test_image_with_text("Testing OCR")
        blocks, _ = extract_ocr_blocks(image, page_number=1, lang="eng")
        if blocks:
            block = blocks[0]
            assert isinstance(block, OcrBlock)
            assert isinstance(block.text, str)
            assert isinstance(block.confidence, float)
            assert block.page_number == 1
            assert block.x >= 0
            assert block.y >= 0

    @_skip_if_no_tesseract
    def test_confidence_filter(self):
        """Nenhum bloco deve ter confiança abaixo de 20."""
        image = create_test_image_with_text("PDF OCR Reader")
        blocks, _ = extract_ocr_blocks(image, page_number=1, lang="eng")
        for block in blocks:
            assert block.confidence >= 20.0

    @_skip_if_no_tesseract
    def test_no_empty_text_blocks(self):
        """Nenhum bloco deve ter texto vazio."""
        image = create_test_image_with_text("Sample Text")
        blocks, _ = extract_ocr_blocks(image, page_number=1, lang="eng")
        for block in blocks:
            assert block.text.strip() != ""


class TestExtractPagesOcr:
    """Testes de integração com arquivo PDF real (necessita samples/)."""

    @pytest.fixture
    def sample_pdf(self):
        """Verifica se existe um PDF de amostra para testes de integração."""
        pdfs = list(SAMPLES_DIR.glob("*.pdf"))
        if not pdfs:
            pytest.skip(
                "Nenhum PDF encontrado em tests/samples/. "
                "Adicione um PDF de exemplo para rodar testes de integração."
            )
        return str(pdfs[0])

    @_skip_if_no_tesseract
    def test_returns_all_pages(self, sample_pdf):
        """Deve retornar um resultado para cada página do PDF."""
        import fitz
        with fitz.open(sample_pdf) as doc:
            total_pages = len(doc)

        results = extract_pages_ocr(sample_pdf, lang="por+eng")
        assert len(results) == total_pages

    @_skip_if_no_tesseract
    def test_result_tuple_structure(self, sample_pdf):
        """Cada resultado deve ser (page_number, blocks, (width, height))."""
        results = extract_pages_ocr(sample_pdf, lang="por+eng")
        for page_num, blocks, (w, h) in results:
            assert isinstance(page_num, int)
            assert page_num >= 1
            assert isinstance(blocks, list)
            assert isinstance(w, int) and w > 0
            assert isinstance(h, int) and h > 0

    @_skip_if_no_tesseract
    def test_extracts_text_from_pdf(self, sample_pdf):
        """Deve extrair ao menos algum texto do PDF."""
        results = extract_pages_ocr(sample_pdf, lang="por+eng")
        all_text = " ".join(
            block.text
            for _, blocks, _ in results
            for block in blocks
        )
        assert len(all_text.strip()) > 0, "Nenhum texto extraído do PDF"
