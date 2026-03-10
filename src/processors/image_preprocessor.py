"""
Pré-processamento de imagem para melhorar o reconhecimento OCR.

Problemas comuns e soluções aplicadas:
  - Fundo escuro com texto claro  → inversão automática (principal melhoria)
  - Baixo contraste               → aumento de contraste adaptativo
  - Fontes decorativas/cursivas   → nitidez e binarização

O pipeline detecta automaticamente as características da imagem
e aplica as transformações necessárias.
"""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def _is_dark_background(image: Image.Image, threshold: float = 127.0) -> bool:
    """
    Detecta se a imagem tem fundo escuro (texto claro sobre fundo escuro).
    Analisa o brilho médio da imagem em escala de cinza.

    Args:
        image: Imagem PIL em qualquer modo.
        threshold: Brilho médio abaixo do qual considera fundo escuro (0-255).

    Returns:
        True se o fundo for predominantemente escuro.
    """
    gray = image.convert("L")
    pixels = np.array(gray)
    return float(pixels.mean()) < threshold


def _enhance_contrast(image: Image.Image, factor: float = 2.0) -> Image.Image:
    """Aumenta o contraste da imagem."""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(factor)


def _enhance_sharpness(image: Image.Image, factor: float = 2.0) -> Image.Image:
    """Aumenta a nitidez da imagem (útil para fontes decorativas)."""
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(factor)


def _adaptive_binarize(image: Image.Image) -> Image.Image:
    """
    Binarização adaptativa usando threshold de Otsu simplificado.
    Resultado tem apenas pixels 0 ou 255.
    """
    gray = np.array(image.convert("L"))
    threshold = int(np.mean(gray))
    result = np.where(gray > threshold, 255, 0).astype(np.uint8)
    return Image.fromarray(result, mode="L")


def preprocess_for_ocr(
    image: Image.Image,
    invert_dark_bg: bool = True,
    enhance_contrast: bool = True,
    enhance_sharpness: bool = True,
    binarize: bool = False,
) -> Image.Image:
    """
    Aplica pipeline de pré-processamento na imagem para melhorar o OCR.

    Pipeline:
    1. Converte para RGB
    2. Se fundo escuro detectado: inverte a imagem
    3. Aumenta contraste
    4. Aumenta nitidez
    5. [Opcional] Binarização adaptativa

    A binarização está desligada por padrão: o Tesseract LSTM lida bem
    com tons de cinza e a binarização pode remover detalhes de fontes
    cursivas em imagens complexas.

    Args:
        image: Imagem PIL original.
        invert_dark_bg: Inverte automaticamente se fundo for escuro.
        enhance_contrast: Aumenta o contraste.
        enhance_sharpness: Aumenta a nitidez.
        binarize: Aplica binarização adaptativa (cuidado com imagens complexas).

    Returns:
        Imagem PIL processada, pronta para OCR.
    """
    img = image.convert("RGB")

    if invert_dark_bg and _is_dark_background(img, threshold=110):
        img = ImageOps.invert(img)

    if enhance_contrast:
        img = _enhance_contrast(img, factor=1.8)

    if enhance_sharpness:
        img = _enhance_sharpness(img, factor=1.8)

    if binarize:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
        img = _adaptive_binarize(img).convert("RGB")

    return img


def preprocess_high_contrast(image: Image.Image) -> Image.Image:
    """
    Variante para documentos com fundo sólido escuro e texto em cor única.
    Aplica inversão + binarização agressiva.
    """
    img = image.convert("RGB")

    if _is_dark_background(img, threshold=127):
        img = ImageOps.invert(img)

    img = _enhance_contrast(img, factor=2.5)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    img = _adaptive_binarize(img).convert("RGB")
    return img
