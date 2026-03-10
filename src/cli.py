"""
Interface de linha de comando do PDF OCR Reader.

Uso:
    python -m src.cli <arquivo.pdf> [opções]

Exemplos:
    python -m src.cli documento.pdf
    python -m src.cli documento.pdf --output resultado.json --lang por+eng --verbose
    python -m src.cli certificado.pdf --psm 11   # para docs com texto espalhado
"""

import argparse
import sys
from pathlib import Path

from src.extractors.page_ocr import extract_pages_ocr, _DEFAULT_PSM, _PSM_AUTO
from src.extractors.image_extractor import extract_embedded_images
from src.processors.layout_analyzer import analyze_page_layout
from src.models.document_model import DocumentResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-ocr-reader",
        description="Lê um PDF via OCR e extrai texto estruturado por página.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Dica sobre --psm (Page Segmentation Mode do Tesseract):
  3  = Auto (padrão) → melhor para documentos com colunas, tabelas e parágrafos
  6  = Bloco uniforme → bom para documentos com um único bloco de texto
  11 = Sparse text   → bom para certificados e texto espalhado sem estrutura

Exemplos:
  python -m src.cli relatorio.pdf --output resultado.json --verbose
  python -m src.cli certificado.pdf --psm 11 --output cert.json
        """,
    )
    parser.add_argument(
        "pdf_path",
        help="Caminho para o arquivo PDF a ser processado.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Arquivo de saída JSON. Se omitido, imprime no terminal.",
    )
    parser.add_argument(
        "--lang", "-l",
        default="por+eng",
        help="Idiomas do Tesseract (padrão: por+eng).",
    )
    parser.add_argument(
        "--psm",
        type=int,
        default=_PSM_AUTO,
        help=(
            "Page Segmentation Mode do Tesseract (padrão: auto-detecção). "
            "3=documentos com tabelas/colunas, 11=texto espalhado (certificados). "
            "Se omitido, o sistema detecta automaticamente por página."
        ),
    )
    parser.add_argument(
        "--no-preprocess",
        action="store_true",
        help="Desativa o pré-processamento de imagem (inversão, contraste, nitidez).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Exibe progresso detalhado durante o processamento.",
    )
    return parser


def run(
    pdf_path: str,
    output: str | None,
    lang: str,
    psm: int,
    preprocess: bool,
    verbose: bool,
) -> DocumentResult:
    """
    Executa o pipeline completo de extração.

    Returns:
        DocumentResult com todo o conteúdo extraído.
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"Erro: arquivo não encontrado: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"Processando: {pdf.name}")
        print(f"Idioma OCR : {lang}")
        print(f"PSM        : {psm}")
        print(f"Preprocessamento: {'desativado' if not preprocess else 'ativado'}")

    # 1. OCR de páginas completas
    if verbose:
        print("\n[1/3] Extraindo texto via OCR das páginas...")
    pages_data = extract_pages_ocr(
        pdf_path, lang=lang, verbose=verbose, preprocess=preprocess, psm=psm
    )

    # 2. Imagens embutidas
    if verbose:
        print("\n[2/3] Extraindo imagens embutidas...")
    images_by_page = extract_embedded_images(pdf_path, lang=lang)

    # 3. Análise de layout
    if verbose:
        print("\n[3/3] Analisando layout (header/body/footer)...")

    import fitz
    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)

    document = DocumentResult(file_path=str(pdf), total_pages=total_pages)

    for page_number, blocks, (img_width, img_height) in pages_data:
        page_result = analyze_page_layout(page_number, blocks, img_height)
        page_result.embedded_images = images_by_page.get(page_number, [])
        document.pages.append(page_result)

    # Saída
    if output:
        document.save_json(output)
        if verbose:
            print(f"\nResultado salvo em: {output}")
    else:
        print(document.to_json())

    return document


def main():
    parser = build_parser()
    args = parser.parse_args()
    run(
        pdf_path=args.pdf_path,
        output=args.output,
        lang=args.lang,
        psm=args.psm,
        preprocess=not args.no_preprocess,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
