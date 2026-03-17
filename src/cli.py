"""
Interface de linha de comando do PDF OCR Reader.

Uso:
    python -m src.cli <arquivo.pdf> [opções]

Exemplos:
    python -m src.cli documento.pdf
    python -m src.cli documento.pdf --output resultado.json --lang por+eng --verbose
    python -m src.cli certificado.pdf --psm 11
    python -m src.cli relatorio.pdf --output relatorio.txt --format txt
    python -m src.cli escaneado.pdf --no-hybrid   # força OCR puro
"""

import argparse
import sys
from pathlib import Path

from src.extractors.page_ocr import _PSM_AUTO
from src.core.pipeline import run_pipeline
from src.models.document_model import DocumentResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-ocr-reader",
        description="Le um PDF via extração híbrida (nativo + OCR) e retorna texto estruturado.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de extração (automático por página):
  nativo  PDFs gerados digitalmente (Word, InDesign): texto exato, sem OCR
  ocr     Páginas escaneadas: Tesseract com pré-processamento de imagem

Formatos de saída (--format):
  json  Estruturado com metadados, regiões e tabelas (padrão)
  txt   Texto puro com separadores visuais

PSM do Tesseract (--psm, usado apenas no modo OCR):
  auto  Detecta automaticamente por brilho (padrão)
  3     Documentos estruturados (colunas, tabelas)
  11    Texto esparso (certificados, designs)

Exemplos:
  python -m src.cli relatorio.pdf --output resultado.json --verbose
  python -m src.cli certif.pdf --psm 11 --output cert.json
  python -m src.cli manual.pdf --output manual.txt --format txt
  python -m src.cli escaneado.pdf --no-hybrid
        """,
    )
    parser.add_argument("pdf_path", help="Caminho para o arquivo PDF.")
    parser.add_argument("--output", "-o", default=None, help="Arquivo de saída.")
    parser.add_argument(
        "--format", "-f",
        choices=["json", "txt"],
        default="json",
        help="Formato de saída: json (padrão) ou txt.",
    )
    parser.add_argument("--lang", "-l", default="por+eng", help="Idiomas Tesseract.")
    parser.add_argument(
        "--psm",
        type=int,
        default=_PSM_AUTO,
        help="PSM do Tesseract (padrão: auto-detecção). 3=estruturado, 11=esparso.",
    )
    parser.add_argument(
        "--no-preprocess",
        action="store_true",
        help="Desativa pré-processamento de imagem.",
    )
    parser.add_argument(
        "--no-hybrid",
        action="store_true",
        help="Desativa extração nativa — usa OCR puro em todas as páginas.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Exibe progresso detalhado por página.",
    )
    return parser


def run(
    pdf_path: str,
    output: str | None,
    fmt: str,
    lang: str,
    psm: int,
    preprocess: bool,
    hybrid: bool,
    verbose: bool,
) -> DocumentResult:
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"Erro: arquivo nao encontrado: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    document = run_pipeline(
        pdf_path=str(pdf),
        lang=lang,
        psm=psm,
        preprocess=preprocess,
        hybrid=hybrid,
        verbose=verbose,
    )

    # Saída
    if output:
        if fmt == "txt":
            document.save_txt(output)
        else:
            document.save_json(output)
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
        hybrid=not args.no_hybrid,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
