"""
Testes automatizados da API FastAPI do PDF OCR Reader.

Usa o ASGI test client do FastAPI (httpx + anyio) para testar
os endpoints sem precisar subir o servidor.

Executar:
    pytest tests/test_api.py -v
"""

import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

# PDF de amostra disponível nos testes (reutiliza o que já existe no projeto)
SAMPLES_DIR = Path(__file__).parent / "samples"


def _get_sample_pdf() -> Path | None:
    """Retorna o primeiro PDF encontrado em tests/samples/, ou None."""
    pdfs = list(SAMPLES_DIR.glob("*.pdf"))
    return pdfs[0] if pdfs else None


# ─── Testes do /health ────────────────────────────────────────────────────────

def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_ok():
    response = client.get("/health")
    assert response.json() == {"status": "ok"}


# ─── Testes do /process ───────────────────────────────────────────────────────

def test_process_without_file_returns_422():
    """Sem arquivo enviado deve retornar 422 Unprocessable Entity."""
    response = client.post("/process")
    assert response.status_code == 422


def test_process_non_pdf_returns_400():
    """Arquivo que não é PDF deve retornar 400 Bad Request."""
    fake_file = io.BytesIO(b"isso nao e um pdf")
    response = client.post(
        "/process",
        files={"file": ("documento.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400


def test_process_invalid_format_returns_400():
    """Parâmetro format inválido deve retornar 400."""
    sample = _get_sample_pdf()
    if sample is None:
        pytest.skip("Nenhum PDF de amostra encontrado em tests/samples/")

    with open(sample, "rb") as f:
        response = client.post(
            "/process?format=xml",
            files={"file": (sample.name, f, "application/pdf")},
        )
    assert response.status_code == 400


@pytest.mark.skipif(
    _get_sample_pdf() is None,
    reason="Nenhum PDF de amostra encontrado em tests/samples/",
)
def test_process_valid_pdf_returns_200():
    """PDF válido deve retornar 200 com JSON estruturado."""
    sample = _get_sample_pdf()
    with open(sample, "rb") as f:
        response = client.post(
            "/process",
            files={"file": (sample.name, f, "application/pdf")},
        )
    assert response.status_code == 200
    data = response.json()
    assert "pages" in data
    assert "total_pages" in data


@pytest.mark.skipif(
    _get_sample_pdf() is None,
    reason="Nenhum PDF de amostra encontrado em tests/samples/",
)
def test_process_valid_pdf_txt_format():
    """PDF válido com format=txt deve retornar texto plano."""
    sample = _get_sample_pdf()
    with open(sample, "rb") as f:
        response = client.post(
            "/process?format=txt",
            files={"file": (sample.name, f, "application/pdf")},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
