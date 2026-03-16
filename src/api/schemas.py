"""
Schemas Pydantic da API do PDF OCR Reader.

Define os modelos de dados usados nas respostas dos endpoints.
"""

from pydantic import BaseModel
from typing import Optional


class HealthResponse(BaseModel):
    """Resposta do endpoint de health check."""
    status: str


class ProcessQueryParams(BaseModel):
    """Parâmetros de query aceitos pelo endpoint /process."""
    lang: str = "por+eng"
    psm: int = -1          # -1 = auto-detecção (mapeia para _PSM_AUTO internamente)
    preprocess: bool = True
    hybrid: bool = True
    format: str = "json"   # "json" ou "txt"
