import pytest
from unittest.mock import patch, MagicMock
from collections.abc import Generator

import fitz

from src.extractors.hybrid_extractor import extract_pages_hybrid, PageExtractionResult
from src.models.document_model import OcrBlock, TableResult

def test_extract_pages_hybrid_native(simple_pdf):
    # simple_pdf has native text, should use "native" mode
    results = list(extract_pages_hybrid(simple_pdf, verbose=False))
    
    assert len(results) == 1
    page_res = results[0]
    assert isinstance(page_res, PageExtractionResult)
    assert page_res.page_number == 1
    assert page_res.mode == "native"
    assert len(page_res.blocks) > 0

@patch("src.extractors.hybrid_extractor.extract_native_tables")
@patch("src.extractors.hybrid_extractor.extract_native_blocks")
@patch("src.extractors.hybrid_extractor.detect_page_mode")
def test_hybrid_table_filtering(mock_detect, mock_blocks, mock_tables, simple_pdf):
    # Simulate native mode
    mock_detect.return_value = "native"
    
    # 3 blocks: 1 outside table, 2 inside table
    b_out = OcrBlock(text="Outside", confidence=100.0, page_number=1, x=10, y=10, width=50, height=20)
    b_in1 = OcrBlock(text="Cell 1", confidence=100.0, page_number=1, x=105, y=105, width=40, height=20)
    b_in2 = OcrBlock(text="Cell 2", confidence=100.0, page_number=1, x=155, y=105, width=40, height=20)
    
    mock_blocks.return_value = [b_out, b_in1, b_in2]
    
    # 1 table covering (100, 100) to (200, 200)
    mock_tables.return_value = [
        TableResult(index=0, rows=[["Cell 1", "Cell 2"]], bbox=(100.0, 100.0, 200.0, 200.0))
    ]
    
    results = list(extract_pages_hybrid(simple_pdf, verbose=False))
    page_res = results[0]
    
    # After filtering and injection:
    # 1. b_out remains
    # 2. b_in1 and b_in2 are discarded (centers inside table bbox)
    # 3. 1 injected block representing the table plain text
    assert len(page_res.blocks) == 2
    
    texts = [b.text for b in page_res.blocks]
    assert "Outside" in texts
    
    # Check if table was injected
    table_str = mock_tables.return_value[0].to_plain_text()
    assert table_str in texts
    
    # The injected block should have the table's coordinates
    injected_block = next(b for b in page_res.blocks if b.text == table_str)
    assert injected_block.x == 100
    assert injected_block.y == 100
    assert injected_block.width == 100
    assert injected_block.height == 100

@patch("src.extractors.hybrid_extractor.extract_ocr_blocks")
@patch("src.extractors.hybrid_extractor.detect_page_mode")
def test_hybrid_ocr_fallback(mock_detect, mock_ocr, simple_pdf):
    # Force OCR mode detection
    mock_detect.return_value = "ocr"
    mock_ocr.return_value = ([OcrBlock(text="OCR text", confidence=90.0, page_number=1, x=0,y=0,width=10,height=10)], 3)
    
    results = list(extract_pages_hybrid(simple_pdf, verbose=False))
    page_res = results[0]
    
    assert page_res.mode == "ocr"
    assert len(page_res.blocks) == 1
    assert page_res.blocks[0].text == "OCR text"
    assert len(page_res.tables) == 0
