"""
Configuração e detecção automática do Tesseract-OCR.

No Windows, o Tesseract frequentemente não é adicionado ao PATH do sistema
automaticamente. Este módulo detecta o caminho padrão de instalação
e configura o pytesseract antes do primeiro uso.
"""

import os
import sys
import shutil
import pytesseract


# Caminhos padrão de instalação do Tesseract no Windows
_WINDOWS_DEFAULT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(
        os.environ.get("USERNAME", "")
    ),
]


def _find_tesseract_windows() -> str | None:
    """Tenta encontrar o executável do Tesseract em locais padrão do Windows."""
    for path in _WINDOWS_DEFAULT_PATHS:
        if os.path.isfile(path):
            return path
    return None


def configure_tesseract(tesseract_path: str | None = None) -> str:
    """
    Configura o pytesseract com o caminho correto do executável Tesseract.

    A ordem de busca é:
    1. Parâmetro explícito `tesseract_path`
    2. Variável de ambiente TESSERACT_CMD
    3. Detecção automática nos caminhos padrão do Windows
    4. Assume que está no PATH do sistema

    Args:
        tesseract_path: Caminho explícito para o executável (opcional).

    Returns:
        Caminho configurado do executável.

    Raises:
        FileNotFoundError: Se o Tesseract não for encontrado em lugar algum.
    """
    # 1. Parâmetro explícito
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        return tesseract_path

    # 2. Variável de ambiente
    env_path = os.environ.get("TESSERACT_CMD")
    if env_path and os.path.isfile(env_path):
        pytesseract.pytesseract.tesseract_cmd = env_path
        return env_path

    # 3. Detecção automática no Windows
    if sys.platform == "win32":
        auto_path = _find_tesseract_windows()
        if auto_path:
            pytesseract.pytesseract.tesseract_cmd = auto_path
            return auto_path

    # 4. Assume que está no PATH
    if shutil.which("tesseract"):
        return "tesseract"

    raise FileNotFoundError(
        "Tesseract-OCR não encontrado. Instale em https://github.com/UB-Mannheim/tesseract/wiki "
        "ou defina a variável de ambiente TESSERACT_CMD com o caminho do executável."
    )


# Configura automaticamente ao importar o módulo
try:
    _configured_path = configure_tesseract()
except FileNotFoundError:
    _configured_path = None
