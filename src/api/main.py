"""
Aplicação FastAPI do PDF OCR Reader.

Inicializa o app e registra as rotas da API.

Para iniciar o servidor, use o script da raiz:
    python run_api.py

Ou diretamente com uvicorn:
    uvicorn src.api.main:app --reload --port 8000

Documentação interativa disponível em:
    http://localhost:8000/docs        (Swagger UI)
    http://localhost:8000/redoc       (ReDoc)
"""

from fastapi import FastAPI

from src.api.routes import router

app = FastAPI(
    title="PDF OCR Reader API",
    description=(
        "API para extração de texto de arquivos PDF usando extração "
        "híbrida: leitura nativa para PDFs digitais e OCR (Tesseract) "
        "para páginas escaneadas."
    ),
    version="1.0.0",
    contact={
        "name": "PDF OCR Reader",
    },
    license_info={
        "name": "MIT",
    },
)

app.include_router(router)
