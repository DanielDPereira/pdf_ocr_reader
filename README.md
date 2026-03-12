# PDF OCR Reader

Sistema de leitura de PDFs via OCR em Python — com **interface gráfica** e linha de comando.

Extrai texto de qualquer tipo de PDF — escaneado ou digital — renderizando cada página como imagem e aplicando OCR via Tesseract. Separa o conteúdo em regiões (cabeçalho, corpo, rodapé) e extrai texto de imagens embutidas.

---

## Funcionalidades

- 🖥️ **Interface gráfica** moderna (CustomTkinter) — arraste, processe e salve sem terminal
- 📄 Leitura OCR de **página completa** (PDFs escaneados e digitais)
- 🔄 **Detecção automática** de modo de segmentação por brilho da página
  - Fundo escuro (certificados) → PSM 11 (sparse text)
  - Fundo claro (documentos, manuais) → PSM 3 (auto-segmentation)
- 🖼️ Extração de **imagens embutidas** com OCR individual
- 📐 Separação de regiões: **cabeçalho**, **corpo** e **rodapé** com agrupamento por linhas
- 📋 **Metadados do PDF** extraídos automaticamente (título, autor, data de criação)
- 💾 Saída em **JSON** (estruturado) ou **TXT** (texto plano para leitura humana/RAG)
- 🔧 Pré-processamento de imagem: inversão de fundo escuro, contraste, nitidez
- CLI completa para automação e uso em scripts

---

## Pré-requisitos

- Python 3.10+
- [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) instalado no sistema
  - Windows: instalar com suporte aos idiomas **Português (por)** e **Inglês (eng)**
  - Adicionar ao PATH ou instalar no caminho padrão: `C:\Program Files\Tesseract-OCR`

---

## Instalação

```bash
# Clone o repositório
git clone https://github.com/DanielDPereira/pdf_ocr_reader.git
cd pdf_ocr_reader

# Crie e ative o ambiente virtual
python -m venv .venv
.\.venv\Scripts\activate       # Windows
# source .venv/bin/activate    # Linux/Mac

# Instale as dependências
pip install -r requirements.txt
```

---

## Uso

### Interface Gráfica (recomendado)

```bash
python -m src.gui
```

A interface permite:
1. **Selecionar PDF** via botão (qualquer tipo)
2. **Configurar opções**: idioma OCR, formato de saída, modo PSM, pré-processamento
3. **Acompanhar progresso** em tempo real no log
4. **Salvar resultado** em JSON ou TXT com um clique

### Linha de Comando (CLI)

```bash
# Leitura básica (saída no terminal)
python -m src.cli meu_arquivo.pdf

# Salvar em JSON com verbose
python -m src.cli meu_arquivo.pdf --output resultado.json --verbose

# Salvar em TXT (texto simples, ideal para RAG)
python -m src.cli meu_arquivo.pdf --output resultado.txt --format txt

# Forçar PSM para certificados com fundo escuro
python -m src.cli certificado.pdf --psm 11 --output cert.json

# Desativar pré-processamento de imagem
python -m src.cli documento.pdf --no-preprocess
```

#### Parâmetros da CLI

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `--output`, `-o` | terminal | Arquivo de saída |
| `--format`, `-f` | `json` | Formato: `json` ou `txt` |
| `--lang`, `-l` | `por+eng` | Idiomas Tesseract |
| `--psm` | auto | Page Segmentation Mode (3, 11) |
| `--no-preprocess` | — | Desativa inversão/contraste |
| `--verbose`, `-v` | — | Progresso detalhado por página |

---

## Estrutura do Projeto

```
pdf_ocr_reader/
├── src/
│   ├── config.py                     # Detecção automática do Tesseract
│   ├── cli.py                        # Interface de linha de comando
│   ├── gui/
│   │   ├── app.py                    # Janela principal (CustomTkinter)
│   │   └── __main__.py               # Entry point: python -m src.gui
│   ├── extractors/
│   │   ├── page_ocr.py               # OCR full-page com auto-detecção PSM
│   │   ├── image_extractor.py        # Extração de imagens embutidas
│   │   └── metadata_extractor.py     # Metadados do PDF (autor, título, data)
│   ├── processors/
│   │   ├── layout_analyzer.py        # Separação header/body/footer por linhas
│   │   └── image_preprocessor.py     # Inversão, contraste, nitidez, binarização
│   └── models/
│       └── document_model.py         # Dataclasses: OcrBlock, PageResult, DocumentResult
├── tests/
│   ├── conftest.py                   # Fixtures: gera PDFs para testes
│   ├── test_page_ocr.py
│   ├── test_layout_analyzer.py
│   └── test_image_preprocessor.py
├── requirements.txt
└── README.md
```

---

## Formato de Saída JSON

```json
{
  "file": "documento.pdf",
  "total_pages": 2,
  "metadata": {
    "title": "Título do Documento",
    "author": "Nome do Autor",
    "creation_date": "2026-03-10 18:30:00 -03:00"
  },
  "pages": [
    {
      "page_number": 1,
      "full_text": "Cabeçalho\n\nCorpo do texto...\n\nRodapé",
      "header": { "text": "Cabeçalho" },
      "body": { "text": "Corpo do texto..." },
      "footer": { "text": "Rodapé" },
      "embedded_images": [
        { "index": 0, "ocr_text": "Texto da imagem", "width": 800, "height": 600 }
      ]
    }
  ]
}
```

---

## Testes

```bash
# Rodar todos os testes
pytest tests/ -v

# Com cobertura de código
pytest tests/ --cov=src --cov-report=term-missing
```

**42 testes** cobrindo: OCR, agrupamento de layout, pré-processamento e integração.

---

## Roadmap

- [x] Pipeline OCR full-page com Tesseract
- [x] Pré-processamento de imagem (inversão, contraste, nitidez)
- [x] Detecção automática de PSM por brilho da página
- [x] Separação header/body/footer com agrupamento por linhas
- [x] Metadados do PDF (autor, título, data)
- [x] Saída em JSON e TXT
- [x] Interface gráfica (CustomTkinter)
- [ ] Extração híbrida: texto nativo + OCR fallback por página
- [ ] Extração de tabelas (`page.find_tables()`)
- [ ] API REST (FastAPI)

---

## Limitações Conhecidas

- O OCR por imagem não compreende estrutura tabular — tabelas complexas podem ficar misturadas
- Fontes manuscritas/cursivas decorativas têm qualidade reduzida (limitação do Tesseract)
- PDFs com texto nativo (Word, InDesign) têm melhor resultado quando processados com extração híbrida (em desenvolvimento)
