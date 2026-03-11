"""
Interface de linha de comando do PDF OCR Reader.

Uso:
    python -m src.cli <arquivo.pdf> [opções]

Exemplos:
    python -m src.cli documento.pdf
    python -m src.cli documento.pdf --output resultado.json --lang por+eng --verbose
    python -m src.cli certificado.pdf --psm 11
    python -m src.cli relatorio.pdf --output relatorio.txt --format txt
"""

import argparse
import sys
from pathlib import Path

from src.extractors.page_ocr import extract_pages_ocr, _DEFAULT_PSM, _PSM_AUTO
from src.extractors.image_extractor import extract_embedded_images
from src.extractors.metadata_extractor import extract_pdf_metadata
from src.processors.layout_analyzer import analyze_page_layout
from src.models.document_model import DocumentResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-ocr-reader",
        description="Le um PDF via OCR e extrai texto estruturado por pagina.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Formatos de saida (--format):
  json  Saida estruturada em JSON (padrao) - ideal para integracao com sistemas
  txt   Texto puro com separadores visuais - ideal para leitura humana e RAG

PSM - Page Segmentation Mode do Tesseract:
  auto  Detecta automaticamente por brilho da pagina (padrao)
  3     Documentos com colunas, tabelas e paragrafos
  11    Texto espalhado sem estrutura (certificados, designs)

Exemplos:
  python -m src.cli relatorio.pdf --output resultado.json --verbose
  python -m src.cli certificado.pdf --psm 11 --output cert.json
  python -m src.cli manual.pdf --output manual.txt --format txt
        """,
    )
    parser.add_argument(
        "pdf_path",
        help="Caminho para o arquivo PDF a ser processado.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Arquivo de saida (JSON ou TXT). Se omitido, imprime no terminal.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["json", "txt"],
        default="json",
        help="Formato de saida: json (padrao) ou txt.",
    )
    parser.add_argument(
        "--lang", "-l",
        default="por+eng",
        help="Idiomas do Tesseract (padrao: por+eng).",
    )
    parser.add_argument(
        "--psm",
        type=int,
        default=_PSM_AUTO,
        help=(
            "Page Segmentation Mode do Tesseract (padrao: auto-deteccao). "
            "3=documentos com tabelas/colunas, 11=texto espalhado (certificados)."
        ),
    )
    parser.add_argument(
        "--no-preprocess",
        action="store_true",
        help="Desativa o pre-processamento de imagem.",
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
    fmt: str,
    lang: str,
    psm: int,
    preprocess: bool,
    verbose: bool,
) -> DocumentResult:
    """
    Executa o pipeline completo de extracao.

    Returns:
        DocumentResult com todo o conteudo extraido.
    """
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"Erro: arquivo nao encontrado: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    if verbose:
        print(f"Processando: {pdf.name}")
        print(f"Idioma OCR : {lang}")
        print(f"PSM        : {psm if psm != _PSM_AUTO else 'auto'}")
        print(f"Formato    : {fmt}")
        print(f"Preprocess.: {'desativado' if not preprocess else 'ativado'}")

    # 1. Metadados do PDF
    if verbose:
        print("\n[1/4] Lendo metadados do PDF...")
    metadata = extract_pdf_metadata(pdf_path)
    if verbose and metadata.to_dict():
        for k, v in metadata.to_dict().items():
            print(f"       {k}: {v}")

    # 2. OCR de paginas completas
    if verbose:
        print("\n[2/4] Extraindo texto via OCR das paginas...")
    pages_data = extract_pages_ocr(
        pdf_path, lang=lang, verbose=verbose, preprocess=preprocess, psm=psm
    )

    # 3. Imagens embutidas
    if verbose:
        print("\n[3/4] Extraindo imagens embutidas...")
    images_by_page = extract_embedded_images(pdf_path, lang=lang)

    # 4. Analise de layout
    if verbose:
        print("\n[4/4] Analisando layout (header/body/footer)...")

    import fitz
    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)

    document = DocumentResult(
        file_path=str(pdf),
        total_pages=total_pages,
        metadata=metadata,
    )

    for page_number, blocks, (img_width, img_height) in pages_data:
        page_result = analyze_page_layout(page_number, blocks, img_height)
        page_result.embedded_images = images_by_page.get(page_number, [])
        document.pages.append(page_result)

    # Saida
    if output:
        out_path = Path(output)
        if fmt == "txt":
            document.save_txt(str(out_path))
        else:
            document.save_json(str(out_path))
        if verbose:
            print(f"\nResultado salvo em: {output}")
    else:
        if fmt == "txt":
            print(document.to_plain_text())
        else:
            print(document.to_json())

    return document


def main():
    parser = build_parser()
    args = parser.parse_args()
    run(
        pdf_path=args.pdf_path,
        output=args.output,
        fmt=args.format,
        lang=args.lang,
        psm=args.psm,
        preprocess=not args.no_preprocess,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
