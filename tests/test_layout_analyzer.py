"""
Testes para o analisador de layout (src/processors/layout_analyzer.py).

Testa agrupamento de blocos em linhas e separação header/body/footer.
Não requer Tesseract nem PDF real — usa OcrBlock sintéticos.
"""

import pytest
from src.models.document_model import OcrBlock
from src.processors.layout_analyzer import (
    _group_into_lines,
    _blocks_to_text,
    analyze_page_layout,
    LINE_MERGE_THRESHOLD,
)


def make_block(text: str, x: int, y: int, w: int = 60, h: int = 20, page: int = 1) -> OcrBlock:
    """Helper: cria um OcrBlock sintético."""
    return OcrBlock(text=text, confidence=90.0, page_number=page, x=x, y=y, width=w, height=h)


class TestGroupIntoLines:
    """Testes do agrupamento de blocos em linhas."""

    def test_empty_input(self):
        assert _group_into_lines([]) == []

    def test_single_block(self):
        block = make_block("word", x=10, y=10)
        lines = _group_into_lines([block])
        assert len(lines) == 1
        assert lines[0][0].text == "word"

    def test_two_blocks_same_line(self):
        """Blocos com Y próximo devem ficar na mesma linha."""
        b1 = make_block("Hello", x=10, y=50)
        b2 = make_block("World", x=100, y=52)  # diferença de 2px < threshold
        lines = _group_into_lines([b1, b2])
        assert len(lines) == 1
        # Devem ser ordenados por X
        assert lines[0][0].text == "Hello"
        assert lines[0][1].text == "World"

    def test_two_blocks_different_lines(self):
        """Blocos com Y muito diferente devem ficar em linhas separadas."""
        b1 = make_block("Linha1", x=10, y=50)
        b2 = make_block("Linha2", x=10, y=150)  # diferença de 100px > threshold
        lines = _group_into_lines([b1, b2])
        assert len(lines) == 2

    def test_x_ordering_within_line(self):
        """Blocos na mesma linha devem ser ordenados por X."""
        b1 = make_block("B", x=200, y=50)
        b2 = make_block("A", x=50, y=50)
        b3 = make_block("C", x=350, y=50)
        lines = _group_into_lines([b1, b2, b3])
        assert len(lines) == 1
        assert [b.text for b in lines[0]] == ["A", "B", "C"]

    def test_multiple_lines_y_ordering(self):
        """Linhas devem aparecer de cima para baixo."""
        b_bottom = make_block("Rodape", x=50, y=800)
        b_top = make_block("Cabecalho", x=50, y=30)
        b_mid = make_block("Corpo", x=50, y=400)
        lines = _group_into_lines([b_bottom, b_top, b_mid])
        assert len(lines) == 3
        assert lines[0][0].text == "Cabecalho"
        assert lines[1][0].text == "Corpo"
        assert lines[2][0].text == "Rodape"

    def test_threshold_boundary(self):
        """Blocos com diferença exatamente igual ao threshold ficam na mesma linha."""
        b1 = make_block("A", x=10, y=50, h=20)   # centro Y = 60
        b2 = make_block("B", x=100, y=60, h=20)   # centro Y = 70 → diferença = 10 < 12
        lines = _group_into_lines([b1, b2])
        assert len(lines) == 1


class TestBlocksToText:
    """Testes da função de consolidação de texto."""

    def test_single_line(self):
        blocks = [
            make_block("Hello", x=10, y=50),
            make_block("World", x=100, y=50),
        ]
        text = _blocks_to_text(blocks)
        assert text == "Hello World"

    def test_two_lines_with_newline(self):
        blocks = [
            make_block("Linha1", x=10, y=50),
            make_block("Linha2", x=10, y=200),
        ]
        text = _blocks_to_text(blocks)
        assert "Linha1" in text
        assert "Linha2" in text
        assert "\n" in text

    def test_empty_blocks(self):
        assert _blocks_to_text([]) == ""

    def test_column_layout_preserved(self):
        """Simula duas colunas na mesma linha (y próximo, x diferentes)."""
        b1 = make_block("Esquerda", x=10, y=100)
        b2 = make_block("Direita", x=400, y=102)
        text = _blocks_to_text([b2, b1])  # ordem invertida de entrada
        # Esquerda deve vir antes de Direita (ordenado por X)
        assert text.index("Esquerda") < text.index("Direita")


class TestAnalyzePageLayout:
    """Testes da separação de regiões da página."""

    def test_header_region(self):
        """Bloco no topo 10% vai para header."""
        img_height = 1000
        block = make_block("Header Text", x=50, y=40, h=20)  # centro Y=50 < 100
        result = analyze_page_layout(1, [block], img_height)
        assert "Header Text" in result.header.text
        assert result.body.text == ""
        assert result.footer.text == ""

    def test_body_region(self):
        """Bloco no meio vai para body."""
        img_height = 1000
        block = make_block("Body Text", x=50, y=490, h=20)  # centro Y=500
        result = analyze_page_layout(1, [block], img_height)
        assert "Body Text" in result.body.text
        assert result.header.text == ""
        assert result.footer.text == ""

    def test_footer_region(self):
        """Bloco no bottom 10% vai para footer."""
        img_height = 1000
        block = make_block("Footer Text", x=50, y=920, h=20)  # centro Y=930 > 900
        result = analyze_page_layout(1, [block], img_height)
        assert "Footer Text" in result.footer.text
        assert result.header.text == ""
        assert result.body.text == ""

    def test_page_number_preserved(self):
        result = analyze_page_layout(3, [], img_height=1000)
        assert result.page_number == 3

    def test_empty_blocks(self):
        result = analyze_page_layout(1, [], img_height=1000)
        assert result.header.text == ""
        assert result.body.text == ""
        assert result.footer.text == ""

    def test_mixed_regions(self):
        """Blocos em regiões diferentes são separados corretamente."""
        img_height = 1000
        blocks = [
            make_block("H", x=50, y=40, h=20),    # header: centro=50
            make_block("B", x=50, y=490, h=20),   # body:   centro=500
            make_block("F", x=50, y=920, h=20),   # footer: centro=930
        ]
        result = analyze_page_layout(1, blocks, img_height)
        assert "H" in result.header.text
        assert "B" in result.body.text
        assert "F" in result.footer.text
