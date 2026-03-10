"""
Extrator de texto via OCR de páginas completas do PDF.

Estratégia:
  1. Cada página é renderizada como imagem de alta resolução (DPI 300) via PyMuPDF.
  2. O tipo de página é detectado automaticamente pelo brilho médio da imagem:
       - Fundo escuro (brilho < 110): PSM 11 (sparse text) → certificados, designs
       - Fundo claro  (brilho ≥ 110): PSM 3  (auto-segmentation) → documentos, manuais
  3. A imagem passa por pré-processamento antes do OCR.
  4. pytesseract.image_to_data() extrai texto com coordenadas e confiança.
  5. Blocos com confiança abaixo do limiar mínimo são descartados.
"""

import fitz  # PyMuPDF
import pytesseract
import numpy as np
from PIL import Image
import io

import src.config  # configura o caminho do Tesseract automaticamente
from src.models.document_model import OcrBlock
from src.processors.image_preprocessor import preprocess_for_ocr


# Resolução de renderização: 300 DPI garante boa qualidade para OCR
_RENDER_DPI = 300
_DPI_MATRIX = fitz.Matrix(_RENDER_DPI / 72, _RENDER_DPI / 72)

# Confiança mínima aceita pelo Tesseract (0-100).
_MIN_CONFIDENCE = 20

# PSM por tipo de página detectado automaticamente:
#   PSM 3  = Auto-segmentation → documentos estruturados (tabelas, colunas, parágrafos)
#   PSM 11 = Sparse text       → texto espalhado sem estrutura (certificados, designs)
_PSM_STRUCTURED = 3
_PSM_SPARSE = 11

# Brilho médio abaixo do qual a página é considerada de fundo escuro (0-255)
_DARK_BG_THRESHOLD = 110

# Valor sentinela: o usuário não especificou PSM, usar detecção automática
_PSM_AUTO = -1
_DEFAULT_PSM = _PSM_AUTO

_TESSERACT_CONFIG_TEMPLATE = "--psm {psm} --oem 1"


def _detect_page_psm(image: Image.Image) -> int:
    """
    Detecta automaticamente o PSM mais adequado para a página com base no
    brilho médio da imagem renderizada.

    - Fundo escuro (certificados, designs gráficos) → PSM 11 (sparse text)
    - Fundo claro (documentos, manuais, relatórios) → PSM 3 (auto-segmentation)

    Args:
        image: Imagem PIL da página renderizada (antes do pré-processamento).

    Returns:
        Valor inteiro do PSM recomendado (3 ou 11).
    """
    gray = np.array(image.convert("L"))
    mean_brightness = float(gray.mean())
    if mean_brightness < _DARK_BG_THRESHOLD:
        return _PSM_SPARSE    # fundo escuro: sparse text
    return _PSM_STRUCTURED    # fundo claro: auto-segmentation


def render_page_as_image(page: fitz.Page) -> Image.Image:
    """
    Renderiza uma página do PDF como imagem PIL em alta resolução.

    Args:
        page: Objeto de página do PyMuPDF.

    Returns:
        Imagem PIL no modo RGB.
    """
    pixmap = page.get_pixmap(matrix=_DPI_MATRIX, alpha=False)
    img_bytes = pixmap.tobytes("png")
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


def extract_ocr_blocks(
    image: Image.Image,
    page_number: int,
    lang: str = "por+eng",
    preprocess: bool = True,
    psm: int = _DEFAULT_PSM,
) -> tuple[list[OcrBlock], int]:
    """
    Aplica pré-processamento e OCR sobre uma imagem, retornando blocos de texto.

    Args:
        image: Imagem PIL de uma página do PDF (original, sem pré-processamento).
        page_number: Número da página (1-indexado).
        lang: Idiomas do Tesseract (ex: 'por+eng').
        preprocess: Se True, aplica pipeline de pré-processamento antes do OCR.
        psm: Page Segmentation Mode. Use -1 (padrão) para detecção automática,
             3 para documentos estruturados, 11 para texto espalhado.

    Returns:
        Tupla (lista de OcrBlock, psm_usado).
    """
    # Detecção automática de PSM se não especificado
    effective_psm = _detect_page_psm(image) if psm == _PSM_AUTO else psm

    # Aplica pré-processamento para melhorar reconhecimento
    ocr_image = preprocess_for_ocr(image) if preprocess else image

    config = _TESSERACT_CONFIG_TEMPLATE.format(psm=effective_psm)
    data = pytesseract.image_to_data(
        ocr_image,
        lang=lang,
        config=config,
        output_type=pytesseract.Output.DICT,
    )

    blocks: list[OcrBlock] = []
    num_items = len(data["text"])

    for i in range(num_items):
        text = data["text"][i].strip()
        raw_conf = data["conf"][i]

        # Tesseract retorna -1 para linhas sem confiança (separadores internos)
        if not text or raw_conf == -1:
            continue

        confidence = float(raw_conf)
        if confidence < _MIN_CONFIDENCE:
            continue

        blocks.append(
            OcrBlock(
                text=text,
                confidence=confidence,
                page_number=page_number,
                x=int(data["left"][i]),
                y=int(data["top"][i]),
                width=int(data["width"][i]),
                height=int(data["height"][i]),
            )
        )

    return blocks, effective_psm


def extract_pages_ocr(
    pdf_path: str,
    lang: str = "por+eng",
    verbose: bool = False,
    preprocess: bool = True,
    psm: int = _DEFAULT_PSM,
) -> list[tuple[int, list[OcrBlock], tuple[int, int]]]:
    """
    Processa todas as páginas de um PDF e retorna os blocos OCR de cada uma.

    Quando psm=-1 (padrão), o modo de segmentação é detectado automaticamente
    página a página com base no brilho médio da imagem. Isso permite que um
    mesmo PDF tenha páginas com layouts diferentes reconhecidas corretamente.

    Args:
        pdf_path: Caminho para o arquivo PDF.
        lang: Idiomas do Tesseract.
        verbose: Se True, imprime progresso por página.
        preprocess: Se True, aplica pré-processamento de imagem antes do OCR.
        psm: Page Segmentation Mode. -1 = detecção automática (padrão),
             3 = documentos estruturados, 11 = texto espalhado.

    Returns:
        Lista de tuplas: (page_number, lista_de_blocos, (img_width, img_height)).
    """
    results = []

    with fitz.open(pdf_path) as doc:
        total = len(doc)
        for page_index in range(total):
            page_number = page_index + 1
            page = doc[page_index]
            image = render_page_as_image(page)
            img_width, img_height = image.size

            blocks, used_psm = extract_ocr_blocks(
                image, page_number, lang=lang, preprocess=preprocess, psm=psm
            )

            if verbose:
                psm_label = "auto-detectado" if psm == _PSM_AUTO else "manual"
                page_type = "sparse (fundo escuro)" if used_psm == _PSM_SPARSE else "estruturado (fundo claro)"
                print(
                    f"  Pagina {page_number}/{total}: PSM {used_psm} [{psm_label}]"
                    f" > {page_type} | {len(blocks)} blocos extraidos",
                    flush=True,
                )

            results.append((page_number, blocks, (img_width, img_height)))

    return results
