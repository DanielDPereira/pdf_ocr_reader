"""
Rotas da API do PDF OCR Reader.

Endpoints disponíveis:
  GET  /health   → verifica se a API está em funcionamento
  POST /process  → recebe um PDF e retorna a extração estruturada

Uso (após iniciar com `python run_api.py`):

  curl http://localhost:8000/health

  curl -X POST http://localhost:8000/process \\
       -F "file=@documento.pdf"

  curl -X POST "http://localhost:8000/process?format=txt&lang=por" \\
       -F "file=@documento.pdf"
"""

import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

from src.api.schemas import HealthResponse
from src.core.pipeline import run_pipeline
from src.extractors.page_ocr import _PSM_AUTO

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica se a API está em funcionamento.",
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post(
    "/process",
    summary="Processar PDF",
    description=(
        "Recebe um arquivo PDF via multipart/form-data e retorna "
        "o texto extraído com estrutura de páginas, cabeçalhos, "
        "rodapés e tabelas."
    ),
)
async def process_pdf(
    file: UploadFile = File(..., description="Arquivo PDF a ser processado."),
    lang: str = Query("por+eng", description="Idiomas do Tesseract, ex: 'por+eng'."),
    psm: Optional[int] = Query(
        None,
        description=(
            "PSM do Tesseract (Tesseract Page Segmentation Mode). "
            "None = auto, 3 = estruturado, 11 = esparso."
        ),
    ),
    preprocess: bool = Query(True, description="Pré-processar a imagem antes do OCR."),
    hybrid: bool = Query(True, description="Usar extração nativa onde possível."),
    format: str = Query("json", description="Formato de retorno: 'json' ou 'txt'."),
):
    # Valida content-type
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        # alguns clientes enviam como octet-stream — tentamos verificar pela extensão
        if not (file.filename or "").lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="O arquivo enviado não é um PDF. Envie um arquivo .pdf.",
            )

    # Valida formato de saída
    if format not in ("json", "txt"):
        raise HTTPException(
            status_code=400,
            detail="Parâmetro 'format' inválido. Use 'json' ou 'txt'.",
        )

    # Salva o PDF em arquivo temporário (necessário pois PyMuPDF precisa de path)
    suffix = Path(file.filename or "upload.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        psm_value = psm if psm is not None else _PSM_AUTO
        document = run_pipeline(
            pdf_path=tmp_path,
            lang=lang,
            psm=psm_value,
            preprocess=preprocess,
            hybrid=hybrid,
            verbose=False,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {e}")
    finally:
        # Remove o arquivo temporário
        Path(tmp_path).unlink(missing_ok=True)

    # Retorna conforme o formato solicitado
    if format == "txt":
        return PlainTextResponse(content=document.to_plain_text())

    return JSONResponse(content=document.to_dict())
