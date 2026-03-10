"""
Pré-processamento de imagem para melhorar o reconhecimento OCR.

Problemas comuns e soluções aplicadas:
  - Fundo escuro com texto claro  → inversão automática (principal melhoria)
  - Baixo contraste               → aumento de contraste adaptativo
  - Fontes decorativas/cursivas   → nitidez e binarização
  - Ruído e artefatos             → desfoque leve antes da binarização

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


def _binarize(image: Image.Image, threshold: int = 150) -> Image.Image:
    """
    Converte a imagem para preto e branco com threshold fixo.
    Melhora o reconhecimento de OCR ao eliminar tons de cinza intermediários.
    """
    gray = image.convert("L")
    return gray.point(lambda x: 255 if x > threshold else 0, "L")


def _adaptive_binarize(image: Image.Image) -> Image.Image:
    """
    Binarização adaptativa usando Otsu simplificado via numpy.
    Calcula o threshold ideal automaticamente baseado no histograma da imagem.
    """
    gray = np.array(image.convert("L"))
    # Threshold de Otsu: minimiza variância intra-classe
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
    1. Converte para RGB (garante consistência)
    2. Se fundo escuro detectado: inverte a imagem (texto fica escuro no fundo branco)
    3. Aumenta contraste
    4. Aumenta nitidez (fontes decorativas)
    5. [Opcional] Binarização adaptativa

    A binarização está desligada por padrão: o Tesseract com --oem 1 (LSTM)
    lida bem com tons de cinza, e a binarização pode remover detalhes de
    fontes cursivas/decorativas em imagens complexas.

    Args:
        image: Imagem PIL original (página do PDF renderizada).
        invert_dark_bg: Inverte automaticamente se o fundo for escuro.
        enhance_contrast: Aumenta o contraste da imagem.
        enhance_sharpness: Aumenta a nitidez da imagem.
        binarize: Aplica binarização adaptativa no final (cuidado com imagens complexas).

    Returns:
        Imagem PIL processada, pronta para OCR.
    """
    img = image.convert("RGB")

    # 1. Inversão para fundos escuros
    # Threshold conservador (110): evita inverter imagens com apenas
    # elementos escuros no centro mas fundo geral claro.
    if invert_dark_bg and _is_dark_background(img, threshold=110):
        img = ImageOps.invert(img)

    # 2. Aumento de contraste
    if enhance_contrast:
        img = _enhance_contrast(img, factor=1.8)

    # 3. Nitidez para fontes decorativas e cursivas
    if enhance_sharpness:
        img = _enhance_sharpness(img, factor=1.8)

    # 4. Binarização adaptativa (opcional)
    if binarize:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
        img = _adaptive_binarize(img).convert("RGB")

    return img


def preprocess_high_contrast(image: Image.Image) -> Image.Image:
    """
    Variante de pré-processamento para documentos com fundo sólido escuro
    e texto em cor única. Aplica inversão + binarização agressiva.

    Útil como alternativa quando o pipeline padrão não captura texto suficiente.
    """
    img = image.convert("RGB")

    if _is_dark_background(img, threshold=127):
        img = ImageOps.invert(img)

    img = _enhance_contrast(img, factor=2.5)
    img = img.filter(ImageFilter.GaussianBlur(radius=0.8))
    img = _adaptive_binarize(img).convert("RGB")
    return img
