"""
Extrator de texto via OCR de páginas completas do PDF.

Estratégia:
  1. Cada página do PDF é renderizada como imagem de alta resolução (DPI 300) usando PyMuPDF.
  2. pytesseract.image_to_data() é aplicado sobre a imagem para obter
     cada palavra/bloco com suas coordenadas, texto e confiança de reconhecimento.
  3. Blocos com confiança abaixo do limiar mínimo são descartados.
  4. Os blocos retornados são usados pelo layout_analyzer para separar
     cabeçalho, corpo e rodapé com base na posição vertical.
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

import src.config  # configura o caminho do Tesseract automaticamente
from src.models.document_model import OcrBlock


# Resolução de renderização: 300 DPI garante boa qualidade para OCR
_RENDER_DPI = 300
_DPI_MATRIX = fitz.Matrix(_RENDER_DPI / 72, _RENDER_DPI / 72)

# Confiança mínima aceita do Tesseract (0-100). Abaixo disso, o bloco é descartado.
_MIN_CONFIDENCE = 30


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
) -> list[OcrBlock]:
    """
    Aplica OCR sobre uma imagem e retorna os blocos de texto com coordenadas.

    Args:
        image: Imagem PIL de uma página do PDF.
        page_number: Número da página (1-indexado).
        lang: Idiomas do Tesseract (ex: 'por+eng').

    Returns:
        Lista de OcrBlock com texto, confiança e posição.
    """
    data = pytesseract.image_to_data(
        image,
        lang=lang,
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

    return blocks


def extract_pages_ocr(
    pdf_path: str,
    lang: str = "por+eng",
    verbose: bool = False,
) -> list[tuple[int, list[OcrBlock], tuple[int, int]]]:
    """
    Processa todas as páginas de um PDF e retorna os blocos OCR de cada uma.

    Args:
        pdf_path: Caminho para o arquivo PDF.
        lang: Idiomas do Tesseract.
        verbose: Se True, imprime progresso por página.

    Returns:
        Lista de tuplas com: (page_number, lista_de_blocos, (img_width, img_height)).
        As dimensões da imagem são necessárias para cálculo de proporções no layout_analyzer.
    """
    results = []

    with fitz.open(pdf_path) as doc:
        total = len(doc)
        for page_index in range(total):
            page_number = page_index + 1

            if verbose:
                print(f"  Processando página {page_number}/{total}...", flush=True)

            page = doc[page_index]
            image = render_page_as_image(page)
            img_width, img_height = image.size

            blocks = extract_ocr_blocks(image, page_number, lang=lang)
            results.append((page_number, blocks, (img_width, img_height)))

    return results
