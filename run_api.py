"""
Ponto de entrada da API HTTP do PDF OCR Reader.

Inicia o servidor uvicorn com hot-reload para desenvolvimento.

Uso:
    python run_api.py

O servidor ficará disponível em:
    http://localhost:8000

Documentação interativa:
    http://localhost:8000/docs     (Swagger UI)
    http://localhost:8000/redoc    (ReDoc)

Para produção, use uvicorn diretamente sem --reload:
    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
