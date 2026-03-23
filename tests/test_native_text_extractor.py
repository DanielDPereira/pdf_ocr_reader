import pytest
import fitz
from unittest.mock import MagicMock

from src.extractors.native_text_extractor import (
    detect_page_mode,
    extract_native_blocks,
    extract_native_tables,
    _NATIVE_WORD_THRESHOLD
)
from src.models.document_model import OcrBlock, TableResult

def test_detect_page_mode_native(simple_pdf):
    # simple_pdf has more than 20 words
    with fitz.open(simple_pdf) as doc:
        page = doc[0]
        mode = detect_page_mode(page)
        assert mode == "native"

def test_detect_page_mode_ocr():
    # Mock page with < 20 words
    page_mock = MagicMock(spec=fitz.Page)
    page_mock.get_text.return_value = ["word1", "word2"] # less than threshold
    assert detect_page_mode(page_mock) == "ocr"

def test_extract_native_blocks(simple_pdf):
    with fitz.open(simple_pdf) as doc:
        page = doc[0]
        blocks = extract_native_blocks(page, page_number=1)
        
        assert len(blocks) > 0
        assert all(isinstance(b, OcrBlock) for b in blocks)
        assert all(b.confidence == 100.0 for b in blocks)
        assert any("Cabecalho do Documento" in b.text for b in blocks)

def test_extract_native_tables_empty(simple_pdf):
    # simple_pdf doesn't have vector lines for tables
    with fitz.open(simple_pdf) as doc:
        page = doc[0]
        tables = extract_native_tables(page)
        assert tables == []

def test_extract_native_tables_mock():
    page_mock = MagicMock(spec=fitz.Page)
    table_mock = MagicMock()
    table_mock.bbox = (10.0, 20.0, 100.0, 200.0)
    table_mock.extract.return_value = [
        ["Header1", "Header2"],
        ["Val1", "Val2"],
        [None, "Val3"] # test cleaning none cells
    ]
    
    finder_mock = MagicMock()
    finder_mock.tables = [table_mock]
    page_mock.find_tables.return_value = finder_mock
    
    tables = extract_native_tables(page_mock)
    assert len(tables) == 1
    t = tables[0]
    assert isinstance(t, TableResult)
    assert t.bbox == (10.0, 20.0, 100.0, 200.0)
    assert t.rows[0] == ["Header1", "Header2"]
    assert t.rows[1] == ["Val1", "Val2"]
    assert t.rows[2] == ["", "Val3"]
