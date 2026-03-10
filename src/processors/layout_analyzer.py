"""
Analisador de layout de página.

Separa os blocos OCR em três regiões verticais:
  - Header (cabeçalho): blocos no topo 10% da página
  - Footer (rodapé): blocos nos 10% inferiores da página
  - Body (corpo): todo o restante (80% central da página)

A separação usa a posição vertical (y) de cada bloco relativa
à altura total da imagem renderizada.
"""

from src.models.document_model import OcrBlock, PageRegion, PageResult


# Limite superior para cabeçalho: blocos com y < img_height * HEADER_RATIO
HEADER_RATIO = 0.10

# Limite inferior para rodapé: blocos com y > img_height * FOOTER_RATIO
FOOTER_RATIO = 0.90


def _blocks_to_text(blocks: list[OcrBlock]) -> str:
    """
    Consolida uma lista de blocos OCR em texto contínuo.
    Ordena por posição (cima para baixo, esquerda para direita).
    """
    sorted_blocks = sorted(blocks, key=lambda b: (b.y, b.x))
    return " ".join(b.text for b in sorted_blocks)


def analyze_page_layout(
    page_number: int,
    blocks: list[OcrBlock],
    img_height: int,
) -> PageResult:
    """
    Separa os blocos OCR nas regiões header, body e footer.

    Args:
        page_number: Número da página (1-indexado).
        blocks: Lista de OcrBlock com coordenadas.
        img_height: Altura total da imagem renderizada (em pixels).

    Returns:
        PageResult com as três regiões preenchidas.
    """
    header_blocks: list[OcrBlock] = []
    body_blocks: list[OcrBlock] = []
    footer_blocks: list[OcrBlock] = []

    header_limit = img_height * HEADER_RATIO
    footer_limit = img_height * FOOTER_RATIO

    for block in blocks:
        # Usa o centro vertical do bloco para classificação
        block_center_y = block.y + block.height / 2

        if block_center_y < header_limit:
            header_blocks.append(block)
        elif block_center_y > footer_limit:
            footer_blocks.append(block)
        else:
            body_blocks.append(block)

    return PageResult(
        page_number=page_number,
        header=PageRegion(text=_blocks_to_text(header_blocks)),
        body=PageRegion(text=_blocks_to_text(body_blocks)),
        footer=PageRegion(text=_blocks_to_text(footer_blocks)),
    )
