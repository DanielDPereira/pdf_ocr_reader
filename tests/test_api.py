"""
Testes dos endpoints da API FastAPI do PDF OCR Reader.

Usa o TestClient do FastAPI (síncrono, sem servidor real).
Aproveita os PDFs gerados pelas fixtures do conftest.py para
rodar sem precisar de arquivos externos em tests/samples/.

Para rodar:
    pytest tests/test_api.py -v
"""

import io
import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


# ─── /health ─────────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    """Testes do endpoint GET /health."""

    def test_returns_200(self):
        """Deve retornar HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_body(self):
        """Deve retornar {'status': 'ok'}."""
        response = client.get("/health")
        assert response.json() == {"status": "ok"}

    def test_content_type_is_json(self):
        """Deve retornar Content-Type application/json."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]


# ─── /process — validações de entrada ────────────────────────────────────────

class TestProcessEndpointValidation:
    """Testes de validação de entrada do endpoint POST /process."""

    def test_no_file_returns_422(self):
        """Requisição sem arquivo deve retornar 422 Unprocessable Entity."""
        response = client.post("/process")
        assert response.status_code == 422

    def test_invalid_format_returns_400(self):
        """Parâmetro format inválido deve retornar 400."""
        pdf_bytes = _make_minimal_pdf()
        response = client.post(
            "/process",
            params={"format": "xml"},
            files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 400
        assert "format" in response.json()["detail"].lower()

    def test_non_pdf_file_returns_400(self):
        """Envio de arquivo não-PDF deve retornar 400."""
        response = client.post(
            "/process",
            files={"file": ("notes.txt", b"apenas texto", "text/plain")},
        )
        assert response.status_code == 400

    def test_corrupted_pdf_returns_500(self):
        """Arquivo com bytes inválidos mas extensão .pdf deve retornar 500."""
        response = client.post(
            "/process",
            files={"file": ("fake.pdf", b"nao sou um pdf valido", "application/pdf")},
        )
        assert response.status_code == 500


# ─── /process — sucesso com PDF gerado em memória ────────────────────────────

class TestProcessEndpointSuccess:
    """Testes de sucesso do endpoint POST /process.

    Usa as fixtures simple_pdf e two_page_pdf do conftest.py,
    que geram PDFs nativos programaticamente via PyMuPDF.
    """

    def test_valid_pdf_returns_200(self, simple_pdf):
        """PDF nativo válido deve retornar HTTP 200."""
        assert _post_pdf(simple_pdf).status_code == 200

    def test_response_is_json_by_default(self, simple_pdf):
        """Formato padrão deve ser JSON."""
        response = _post_pdf(simple_pdf)
        assert "application/json" in response.headers["content-type"]

    def test_json_has_required_keys(self, simple_pdf):
        """JSON deve conter as chaves: file, total_pages, pages."""
        body = _post_pdf(simple_pdf).json()
        for key in ("file", "total_pages", "pages"):
            assert key in body, f"Chave ausente no response: '{key}'"

    def test_json_pages_have_structure(self, simple_pdf):
        """Cada página deve ter page_number, full_text, header, body, footer."""
        pages = _post_pdf(simple_pdf).json()["pages"]
        assert len(pages) >= 1
        for page in pages:
            for key in ("page_number", "full_text", "header", "body", "footer"):
                assert key in page, f"Chave ausente na página: '{key}'"

    def test_total_pages_matches_pages_list(self, simple_pdf):
        """total_pages deve ser igual ao número de itens em pages."""
        body = _post_pdf(simple_pdf).json()
        assert body["total_pages"] == len(body["pages"])

    def test_single_page_pdf_has_one_page(self, simple_pdf):
        """PDF de uma página deve retornar total_pages == 1."""
        assert _post_pdf(simple_pdf).json()["total_pages"] == 1

    def test_two_page_pdf_has_two_pages(self, two_page_pdf):
        """PDF de duas páginas deve retornar total_pages == 2."""
        assert _post_pdf(two_page_pdf).json()["total_pages"] == 2

    def test_format_txt_returns_plain_text(self, simple_pdf):
        """Com format=txt deve retornar Content-Type text/plain."""
        response = _post_pdf(simple_pdf, format="txt")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_format_txt_contains_page_marker(self, simple_pdf):
        """Saída TXT deve conter o marcador de página."""
        response = _post_pdf(simple_pdf, format="txt")
        assert "Página 1" in response.text

    def test_extraction_mode_is_present(self, simple_pdf):
        """Cada página deve ter o campo extraction_mode."""
        pages = _post_pdf(simple_pdf).json()["pages"]
        for page in pages:
            assert page.get("extraction_mode") in ("native", "ocr")

    def test_native_pdf_uses_native_mode(self, simple_pdf):
        """PDF com texto nativo deve ter ao menos uma página em modo native."""
        modes = [p["extraction_mode"] for p in _post_pdf(simple_pdf).json()["pages"]]
        assert "native" in modes

    def test_lang_parameter_accepted(self, simple_pdf):
        """Parâmetro lang deve ser aceito sem erro."""
        assert _post_pdf(simple_pdf, params={"lang": "eng"}).status_code == 200

    def test_preprocess_false_accepted(self, simple_pdf):
        """preprocess=false deve ser aceito e retornar 200."""
        assert _post_pdf(simple_pdf, params={"preprocess": "false"}).status_code == 200

    def test_hybrid_false_forces_ocr(self, simple_pdf):
        """hybrid=false deve retornar 200 (forçando OCR puro)."""
        assert _post_pdf(simple_pdf, params={"hybrid": "false"}).status_code == 200


# ─── Auxiliares ──────────────────────────────────────────────────────────────

def _post_pdf(pdf_path: str, format: str = "json", params: dict | None = None):
    """Abre o PDF do disco e envia ao endpoint /process."""
    query = {"format": format}
    if params:
        query.update(params)
    with open(pdf_path, "rb") as f:
        return client.post(
            "/process",
            params=query,
            files={"file": ("documento.pdf", f, "application/pdf")},
        )


def _make_minimal_pdf() -> bytes:
    """Gera um PDF mínimo válido em memória via PyMuPDF."""
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Teste", fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()
