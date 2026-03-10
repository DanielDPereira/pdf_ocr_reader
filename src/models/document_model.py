"""
Modelos de dados do documento PDF processado.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class OcrBlock:
    """
    Bloco de texto extraído via OCR com posição na página.
    As coordenadas são relativas à imagem renderizada (em pixels).
    """
    text: str
    confidence: float  # 0 a 100 (retornado pelo Tesseract)
    page_number: int
    x: int
    y: int
    width: int
    height: int

    @property
    def top_ratio(self) -> float:
        """Posição vertical do bloco relativa à altura total da imagem (0.0 = topo, 1.0 = base)."""
        return 0.0  # será preenchido pelo layout_analyzer com a altura da página


@dataclass
class PageRegion:
    """Região de uma página com o texto consolidado."""
    text: str

    def to_dict(self) -> dict:
        return {"text": self.text.strip()}


@dataclass
class EmbeddedImage:
    """Imagem embutida no PDF com texto extraído via OCR."""
    index: int
    page_number: int
    ocr_text: str
    width: int
    height: int

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "ocr_text": self.ocr_text.strip(),
            "width": self.width,
            "height": self.height,
        }


@dataclass
class PageResult:
    """Resultado da extração de uma página do PDF."""
    page_number: int
    header: PageRegion
    body: PageRegion
    footer: PageRegion
    embedded_images: list[EmbeddedImage] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "header": self.header.to_dict(),
            "body": self.body.to_dict(),
            "footer": self.footer.to_dict(),
            "embedded_images": [img.to_dict() for img in self.embedded_images],
        }


@dataclass
class DocumentResult:
    """Resultado completo da extração de um documento PDF."""
    file_path: str
    total_pages: int
    pages: list[PageResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file": self.file_path,
            "total_pages": self.total_pages,
            "pages": [page.to_dict() for page in self.pages],
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializa o resultado para JSON formatado."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def save_json(self, output_path: str) -> None:
        """Salva o resultado em um arquivo JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
