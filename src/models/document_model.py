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

    @property
    def full_text(self) -> str:
        """
        Texto completo da página: header + body + footer (quando não vazios),
        separados por quebra de linha dupla.

        Útil para pipelines de RAG, busca semântica e análise de texto sem
        precisar concatenar as regiões manualmente.
        """
        parts = [
            region.text.strip()
            for region in (self.header, self.body, self.footer)
            if region.text.strip()
        ]
        return "\n\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "full_text": self.full_text,
            "header": self.header.to_dict(),
            "body": self.body.to_dict(),
            "footer": self.footer.to_dict(),
            "embedded_images": [img.to_dict() for img in self.embedded_images],
        }

    def to_plain_text(self) -> str:
        """
        Texto formatado da página para saída em TXT.
        Inclui separadores visuais para header e footer.
        """
        lines = [f"=== Página {self.page_number} ==="]

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
    """
    Metadados extraídos do PDF via PyMuPDF.
    Todos os campos são opcionais — PDFs podem não ter metadados definidos.
    """
    title: Optional[str] = None
    author: Optional[str] = None
    creator: Optional[str] = None      # software que criou o documento
    producer: Optional[str] = None     # software que gerou o PDF
    subject: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None

    def to_dict(self) -> dict:
        """Retorna apenas campos com valor definido."""
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
            if v  # omite None e strings vazias
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
        """Texto completo do documento: todas as páginas concatenadas."""
        return "\n\n".join(
            page.full_text for page in self.pages if page.full_text
        )

    def to_dict(self) -> dict:
        result = {
            "file": self.file_path,
            "total_pages": self.total_pages,
        }
        # Inclui metadados apenas se houver algum preenchido
        meta = self.metadata.to_dict()
        if meta:
            result["metadata"] = meta

        result["pages"] = [page.to_dict() for page in self.pages]
        return result

    def to_json(self, indent: int = 2) -> str:
        """Serializa o resultado para JSON formatado."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_plain_text(self) -> str:
        """
        Serializa o resultado como texto simples.
        Útil para pipelines que não precisam do JSON estruturado.
        """
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
        """Salva o resultado em um arquivo JSON."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    def save_txt(self, output_path: str) -> None:
        """Salva o resultado em um arquivo TXT simples."""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_plain_text())
