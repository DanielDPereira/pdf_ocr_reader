"""
Extrator de imagens embutidas no PDF.

Usa PyMuPDF para localizar e extrair imagens que estão incorporadas
diretamente no documento PDF (figuras, logos, fotos, diagramas).
Aplica OCR em cada imagem extraída separadamente para capturar
texto que aparece dentro delas.
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

import src.config  # configura o caminho do Tesseract automaticamente
from src.models.document_model import EmbeddedImage


# Tamanho mínimo da imagem para tentar OCR (evita ícones e decorações pequenas)
_MIN_IMAGE_WIDTH = 50
_MIN_IMAGE_HEIGHT = 50


def _pixmap_to_pil(pixmap: fitz.Pixmap) -> Image.Image:
    """Converte um Pixmap do PyMuPDF em imagem PIL."""
    if pixmap.n > 4:
        # Converte espaço de cor CMYK ou outros para RGB
        pixmap = fitz.Pixmap(fitz.csRGB, pixmap)
    img_bytes = pixmap.tobytes("png")
    return Image.open(io.BytesIO(img_bytes)).convert("RGB")


def extract_embedded_images(
    pdf_path: str,
    lang: str = "por+eng",
) -> dict[int, list[EmbeddedImage]]:
    """
    Extrai todas as imagens embutidas de um PDF e aplica OCR em cada uma.

    Args:
        pdf_path: Caminho para o arquivo PDF.
        lang: Idiomas do Tesseract para OCR das imagens.

    Returns:
        Dicionário {page_number: [EmbeddedImage, ...]}.
    """
    result: dict[int, list[EmbeddedImage]] = {}

    with fitz.open(pdf_path) as doc:
        for page_index in range(len(doc)):
            page_number = page_index + 1
            page = doc[page_index]
            images_on_page: list[EmbeddedImage] = []

            # get_images() retorna lista de (xref, smask, width, height, bpc, colorspace, ...)
            for img_index, img_info in enumerate(page.get_images(full=True)):
                xref = img_info[0]
                img_width = img_info[2]
                img_height = img_info[3]

                # Filtra imagens muito pequenas (provavelmente ícones/decorações)
                if img_width < _MIN_IMAGE_WIDTH or img_height < _MIN_IMAGE_HEIGHT:
                    continue

                try:
                    pixmap = fitz.Pixmap(doc, xref)
                    pil_image = _pixmap_to_pil(pixmap)

                    ocr_text = pytesseract.image_to_string(
                        pil_image,
                        lang=lang,
                    ).strip()

                    images_on_page.append(
                        EmbeddedImage(
                            index=img_index,
                            page_number=page_number,
                            ocr_text=ocr_text,
                            width=img_width,
                            height=img_height,
                        )
                    )
                except Exception as e:
                    # Imagem corrompida ou formato não suportado: ignora silenciosamente
                    print(f"  [aviso] Imagem {img_index} na página {page_number} ignorada: {e}")
                    continue

            if images_on_page:
                result[page_number] = images_on_page

    return result
