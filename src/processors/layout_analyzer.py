"""
Analisador de layout de página.

Separa os blocos OCR em três regiões verticais:
  - Header (cabeçalho): blocos no topo 10% da página
  - Footer (rodapé): blocos nos 10% inferiores da página
  - Body (corpo): todo o restante (80% central da página)

Reconstrução de texto:
  Os blocos são agrupados em "linhas" com base na proximidade vertical
  (blocos cujo centro Y difere menos que LINE_MERGE_THRESHOLD px são
  considerados parte da mesma linha). Dentro de cada linha, os blocos
  são ordenados por X. As linhas são ordenadas de cima para baixo.
  Isso preserva a ordem correta em documentos com múltiplas colunas e tabelas.
"""

from src.models.document_model import OcrBlock, PageRegion, PageResult


# Limite superior para cabeçalho: blocos com y < img_height * HEADER_RATIO
HEADER_RATIO = 0.10

# Limite inferior para rodapé: blocos com y > img_height * FOOTER_RATIO
FOOTER_RATIO = 0.90

# Tolerância vertical para agrupar palavras na mesma linha (em pixels).
LINE_MERGE_THRESHOLD = 12


def _group_into_lines(blocks: list[OcrBlock]) -> list[list[OcrBlock]]:
    """
    Agrupa blocos OCR em linhas de texto com base na proximidade vertical.

    Algoritmo:
    1. Ordena blocos pelo centro Y.
    2. Para cada bloco, calcula seu centro Y (cy = y + height/2).
    3. Se o cy estiver dentro de LINE_MERGE_THRESHOLD px do cy médio
       da linha atual, adiciona à linha. Caso contrário, inicia nova linha.
    4. Dentro de cada linha, ordena os blocos por X.

    Args:
        blocks: Lista de OcrBlock (qualquer ordem).

    Returns:
        Lista de linhas, onde cada linha é uma lista de OcrBlock ordenada por X.
    """
    if not blocks:
        return []

    sorted_blocks = sorted(blocks, key=lambda b: b.y + b.height / 2)

    lines: list[list[OcrBlock]] = []
    current_line: list[OcrBlock] = [sorted_blocks[0]]
    current_line_cy = sorted_blocks[0].y + sorted_blocks[0].height / 2

    for block in sorted_blocks[1:]:
        block_cy = block.y + block.height / 2

        if abs(block_cy - current_line_cy) <= LINE_MERGE_THRESHOLD:
            current_line.append(block)
            current_line_cy = sum(
                b.y + b.height / 2 for b in current_line
            ) / len(current_line)
        else:
            lines.append(sorted(current_line, key=lambda b: b.x))
            current_line = [block]
            current_line_cy = block_cy

    lines.append(sorted(current_line, key=lambda b: b.x))
    return lines


def _blocks_to_text(blocks: list[OcrBlock]) -> str:
    """
    Consolida uma lista de blocos OCR em texto, respeitando linhas e colunas.

    1. Agrupa blocos em linhas por proximidade vertical.
    2. Ordena blocos dentro de cada linha por X (esquerda para direita).
    3. Junta palavras da mesma linha com espaço, linhas diferentes com '\\n'.
    """
    lines = _group_into_lines(blocks)
    return "\n".join(
        " ".join(block.text for block in line)
        for line in lines
    )


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
