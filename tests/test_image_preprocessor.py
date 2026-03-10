"""
Testes para o pré-processador de imagem (src/processors/image_preprocessor.py).

Testa a lógica de detecção de fundo escuro e transformações de imagem.
Não requer Tesseract — trabalha apenas com imagens PIL e numpy.
"""

import pytest
import numpy as np
from PIL import Image

from src.processors.image_preprocessor import (
    _is_dark_background,
    _enhance_contrast,
    _enhance_sharpness,
    _adaptive_binarize,
    preprocess_for_ocr,
)


def make_white_image(size=(200, 100)) -> Image.Image:
    """Cria imagem RGB totalmente branca."""
    return Image.new("RGB", size, color=(255, 255, 255))


def make_dark_image(size=(200, 100)) -> Image.Image:
    """Cria imagem RGB totalmente escura (azul marinho, como certificados)."""
    return Image.new("RGB", size, color=(10, 20, 50))


def make_gray_image(brightness: int, size=(200, 100)) -> Image.Image:
    """Cria imagem RGB com brilho uniforme especificado."""
    return Image.new("RGB", size, color=(brightness, brightness, brightness))


class TestIsDarkBackground:
    """Testa a detecção de fundo escuro."""

    def test_white_image_is_not_dark(self):
        img = make_white_image()
        assert _is_dark_background(img, threshold=110) is False

    def test_black_image_is_dark(self):
        img = Image.new("RGB", (100, 100), color=(0, 0, 0))
        assert _is_dark_background(img, threshold=110) is True

    def test_dark_blue_is_dark(self):
        """Azul marinho (como certificado) deve ser detectado como escuro."""
        img = make_dark_image()
        assert _is_dark_background(img, threshold=110) is True

    def test_threshold_boundary(self):
        """Imagem com brilho exatamente no threshold."""
        img = make_gray_image(brightness=109)
        assert _is_dark_background(img, threshold=110) is True

        img = make_gray_image(brightness=111)
        assert _is_dark_background(img, threshold=110) is False

    def test_custom_threshold(self):
        img = make_gray_image(brightness=100)
        assert _is_dark_background(img, threshold=80) is False
        assert _is_dark_background(img, threshold=120) is True


class TestEnhanceContrast:
    """Testa o aumento de contraste."""

    def test_returns_image(self):
        img = make_white_image()
        result = _enhance_contrast(img, factor=2.0)
        assert isinstance(result, Image.Image)

    def test_same_size(self):
        img = make_white_image(size=(300, 200))
        result = _enhance_contrast(img, factor=1.5)
        assert result.size == (300, 200)

    def test_pure_white_stays_white(self):
        """Imagem branca pura não muda com contraste."""
        img = make_white_image()
        result = _enhance_contrast(img, factor=2.0)
        pixels = np.array(result)
        assert pixels.mean() > 200  # continua clara


class TestEnhanceSharpness:
    """Testa o aumento de nitidez."""

    def test_returns_image(self):
        img = make_white_image()
        result = _enhance_sharpness(img, factor=2.0)
        assert isinstance(result, Image.Image)

    def test_same_size(self):
        img = make_white_image(size=(150, 80))
        result = _enhance_sharpness(img, factor=1.5)
        assert result.size == (150, 80)


class TestAdaptiveBinarize:
    """Testa a binarização adaptativa."""

    def test_returns_grayscale_image(self):
        img = make_white_image()
        result = _adaptive_binarize(img)
        assert isinstance(result, Image.Image)
        assert result.mode == "L"

    def test_only_black_and_white_pixels(self):
        """Resultado deve ter apenas pixels 0 ou 255."""
        img = make_gray_image(brightness=128)
        result = _adaptive_binarize(img)
        pixels = np.array(result)
        unique_values = set(pixels.flatten())
        assert unique_values.issubset({0, 255})

    def test_dark_image_becomes_black(self):
        img = Image.new("RGB", (100, 100), color=(20, 20, 20))
        result = _adaptive_binarize(img)
        pixels = np.array(result)
        # Imagem muito escura → pixels abaixo do threshold → preto
        assert pixels.mean() < 128


class TestPreprocessForOcr:
    """Testa o pipeline completo de pré-processamento."""

    def test_dark_image_is_inverted(self):
        """Imagem escura deve ser invertida (fundo fica claro)."""
        dark = make_dark_image()
        result = preprocess_for_ocr(dark, invert_dark_bg=True)
        result_brightness = np.array(result.convert("L")).mean()
        original_brightness = np.array(dark.convert("L")).mean()
        # Após inversão, brilho deve aumentar
        assert result_brightness > original_brightness

    def test_light_image_not_inverted(self):
        """Imagem clara não deve ser invertida."""
        white = make_white_image()
        result = preprocess_for_ocr(white, invert_dark_bg=True)
        result_brightness = np.array(result.convert("L")).mean()
        # Imagem branca continua clara após processamento
        assert result_brightness > 150

    def test_returns_rgb_image(self):
        img = make_white_image()
        result = preprocess_for_ocr(img)
        assert result.mode == "RGB"

    def test_same_dimensions_preserved(self):
        img = make_white_image(size=(400, 300))
        result = preprocess_for_ocr(img)
        assert result.size == (400, 300)

    def test_no_invert_flag(self):
        """Com invert_dark_bg=False, imagem escura NÃO deve ser invertida."""
        dark = make_dark_image()
        result = preprocess_for_ocr(dark, invert_dark_bg=False)
        result_brightness = np.array(result.convert("L")).mean()
        original_brightness = np.array(dark.convert("L")).mean()
        # Sem inversão, diferença de brilho deve ser pequena
        assert abs(result_brightness - original_brightness) < 80
