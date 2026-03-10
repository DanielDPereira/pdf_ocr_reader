# PDF OCR Reader

Sistema de leitura de PDFs via OCR em Python.

Extrai texto de qualquer tipo de PDF — escaneado ou com texto nativo — renderi­zando cada página como imagem e aplicando OCR completo via Tesseract. Separa o conteúdo em regiões: cabeçalho, corpo, rodapé e imagens embutidas.

## Funcionalidades

- Leitura OCR de **página completa** (funciona com PDFs escaneados e digitais)
- Extração de **imagens embutidas** no PDF com OCR individual
- Separação de regiões por posição: **cabeçalho**, **corpo** e **rodapé**
- Saída em **JSON estruturado** por página
- CLI simples para uso local

## Pré-requisitos

- Python 3.10+
- [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado no sistema
  - Windows: instalar com suporte aos idiomas **Português (por)** e **Inglês (eng)**
  - Adicionar ao PATH: `C:\Program Files\Tesseract-OCR`

## Instalação

```bash
# Clone o repositório
git clone https://github.com/DanielDPereira/pdf_ocr_reader.git
cd pdf_ocr_reader

# Crie e ative o ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

## Uso

```bash
# Leitura básica de um PDF
python -m src.cli meu_arquivo.pdf

# Com arquivo de saída e idioma específico
python -m src.cli meu_arquivo.pdf --output resultado.json --lang por+eng

# Modo verbose (mostra progresso por página)
python -m src.cli meu_arquivo.pdf --verbose
```

## Estrutura do Projeto

```
pdf_ocr_reader/
├── src/
│   ├── extractors/
│   │   ├── page_ocr.py        # OCR de página completa
│   │   └── image_extractor.py # Extração de imagens embutidas
│   ├── processors/
│   │   └── layout_analyzer.py # Separação de regiões (header/body/footer)
│   ├── models/
│   │   └── document_model.py  # Modelos de dados e serialização JSON
│   └── cli.py                 # Interface de linha de comando
├── tests/
│   └── samples/               # PDFs de exemplo para testes
├── requirements.txt
└── README.md
```

## Exemplo de Saída JSON

```json
{
  "file": "exemplo.pdf",
  "total_pages": 2,
  "pages": [
    {
      "page_number": 1,
      "header": {
        "text": "Empresa XYZ - Manual Técnico v1.0"
      },
      "body": {
        "text": "Capítulo 1: Introdução\n\nEste manual descreve..."
      },
      "footer": {
        "text": "Página 1 de 10"
      },
      "embedded_images": [
        {
          "index": 0,
          "ocr_text": "Diagrama: Fluxo de operação do sistema"
        }
      ]
    }
  ]
}
```

## Casos de Uso

- **Currículos**: extração de texto, mesmo em PDFs gerados por ferramentas de design
- **Manuais técnicos**: leitura de texto e OCR de diagramas e imagens

## Roadmap

- [x] Estrutura base do projeto
- [ ] OCR de página completa
- [ ] Extração de imagens embutidas
- [ ] Análise de layout (header/body/footer)
- [ ] CLI completa
- [ ] API REST (FastAPI)

## Licença

MIT
