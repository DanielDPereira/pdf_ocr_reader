"""
Modelos de dados do documento PDF processado.
"""

from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class OcrBlock:
    """
    Bloco de texto extraído via OCR (ou leitura nativa) com posição na página.
    As coordenadas são relativas à imagem renderizada ou ao espaço de página (em pixels).
    """
    text: str
    confidence: float  # 0–100 do Tesseract; 100.0 para texto nativo
    page_number: int
    x: int
    y: int
    width: int
    height: int


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
class TableResult:
    """
    Tabela extraída da página com células estruturadas.

    rows é uma lista de linhas, onde cada linha é uma lista de strings
    (valor de cada célula). Células vazias ficam como string vazia "".
    """
    index: int
    rows: list[list[str]] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = field(default_factory=lambda: (0.0, 0.0, 0.0, 0.0))

    @property
    def headers(self) -> list[str]:
        """Primeira linha da tabela (cabeçalho)."""
        return self.rows[0] if self.rows else []

    @property
    def data_rows(self) -> list[list[str]]:
        """Linhas de dados (sem o cabeçalho)."""
        return self.rows[1:] if len(self.rows) > 1 else []

    def to_dict(self) -> dict:
        return {"index": self.index, "rows": self.rows, "bbox": self.bbox}

    def to_plain_text(self) -> str:
        """Representa a tabela como texto com separador | entre células."""
        if not self.rows:
            return ""
        col_widths = [
            max(len(str(row[i])) for row in self.rows if i < len(row))
            for i in range(len(self.rows[0]))
        ]
        lines = []
        for j, row in enumerate(self.rows):
            parts = [str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)]
            lines.append("| " + " | ".join(parts) + " |")
            if j == 0:  # linha separadora após cabeçalho
                lines.append("|" + "|".join("-" * (w + 2) for w in col_widths) + "|")
        return "\n".join(lines)


@dataclass
class PageResult:
    """Resultado da extração de uma página do PDF."""
    page_number: int
    header: PageRegion
    body: PageRegion
    footer: PageRegion
    extraction_mode: str = "ocr"                            # "native" ou "ocr"
    embedded_images: list[EmbeddedImage] = field(default_factory=list)
    tables: list[TableResult] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """
        Texto completo da página: header + body + footer (quando não vazios),
        separados por quebra de linha dupla.
        """
        parts = [
            region.text.strip()
            for region in (self.header, self.body, self.footer)
            if region.text.strip()
        ]
        return "\n\n".join(parts)

    def to_dict(self) -> dict:
        result = {
            "page_number": self.page_number,
            "extraction_mode": self.extraction_mode,
            "full_text": self.full_text,
            "header": self.header.to_dict(),
            "body": self.body.to_dict(),
            "footer": self.footer.to_dict(),
        }
        if self.tables:
            result["tables"] = [t.to_dict() for t in self.tables]
        if self.embedded_images:
            result["embedded_images"] = [img.to_dict() for img in self.embedded_images]
        return result

    def to_plain_text(self) -> str:
        """Texto formatado da página para saída em TXT."""
        lines = [f"=== Página {self.page_number} [{self.extraction_mode.upper()}] ==="]

        if self.header.text.strip():
            lines += ["--- Cabeçalho ---", self.header.text.strip(), ""]

        if self.body.text.strip():
            lines += [self.body.text.strip(), ""]

        if self.footer.text.strip():
            lines += ["--- Rodapé ---", self.footer.text.strip(), ""]

        for img in self.embedded_images:
            if img.ocr_text.strip():
                lines += [f"[Imagem {img.index}]", img.ocr_text.strip(), ""]

        return "\n".join(lines)


@dataclass
class PdfMetadata:
    """Metadados extraídos do PDF via PyMuPDF."""
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    subject: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            k: v for k, v in {
                "title": self.title,
                "author": self.author,
                "creator": self.creator,
                "producer": self.producer,
                "subject": self.subject,
                "creation_date": self.creation_date,
                "modification_date": self.modification_date,
            }.items()
            if v
        }


@dataclass
class DocumentResult:
    """Resultado completo da extração de um documento PDF."""
    file_path: str
    total_pages: int
    metadata: PdfMetadata = field(default_factory=PdfMetadata)
    pages: list[PageResult] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Texto completo do documento."""
        return "\n\n".join(
            page.full_text for page in self.pages if page.full_text
        )

    def to_dict(self) -> dict:
        result: dict = {
            "file": self.file_path,
            "total_pages": self.total_pages,
        }
        meta = self.metadata.to_dict()
        if meta:
            result["metadata"] = meta
        result["pages"] = [page.to_dict() for page in self.pages]
        return result

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_plain_text(self) -> str:
        lines = [f"Arquivo: {self.file_path}", f"Páginas: {self.total_pages}"]
        meta = self.metadata.to_dict()
        if meta:
            lines.append("")
            lines.append("Metadados:")
            for k, v in meta.items():
                lines.append(f"  {k}: {v}")
        lines.append("")
        for page in self.pages:
            lines.append(page.to_plain_text())
        return "\n".join(lines)

    def save_json(self, output_path: str) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    def save_txt(self, output_path: str) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_plain_text())
