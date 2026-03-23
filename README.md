# 📄 PDF OCR Reader

<p align="center">
  <em>Sistema completo, moderno e robusto para extração inteligente e em alta performance de textos de arquivos PDF.</em>
</p>

---

## 🚀 Sobre o Projeto

O **PDF OCR Reader** é uma solução de ponta projetada para lidar magistralmente com o desafio de extrair dados de PDFs. Diferente das abordagens comuns, sua engine híbrida domina a leitura imensamente veloz de **documentos nativos** (gerados por software) bem como a mineração avançada e minuciosa de textos em **documentos puramente digitalizados** (via OCR).

Empacotada por meio de uma arquitetura modular de grau corporativo, a ferramenta oferta acesso contíguo flexível aos desenvolvedores e operações por meio de metodologias unificadas:
- 🖥️ **Interface Gráfica (GUI):** Experiência de uso direta para o corporativo e o desktop final.
- ⌨️ **Linha de Comando (CLI):** Automação pragmática nativa do terminal Bash ou Scripts.
- 🌐 **API REST Web:** Microsserviço plug-and-play resiliente e altamente escalável para integrações sistêmicas ágeis de Data Pipelines e Microsserviços.

---

## 🧠 Solução Híbrida e Arquitetura

O ato minucioso de minerar dados tabulares lineares de arquivos PDF habitualmente sofre com corrupções baseadas na raiz formadora (digital vs papel impresso). O **PDF OCR Reader** ultrapassa essa barreira englobando uma arquitetura **Híbrida Definitiva e de Alto Desempenho**:

1. 🎯 **Detecção Inteligente Instantânea:** O sistema rastreia as engrenagens binárias de cada página sob demanda buscando o *footprint* vetorial. Ele mapeia em frações de segundos se a página carrega blocos de dados indexados reais ou se o layout resume-se a fotografias e exibições focadas em pixels rasterizados no buffer de tela (Scans comuns).
2. ⚡ **Engrenagem de Extração Dinâmica (O Segredo do Desempenho):**
   - **Camada Nativa (Alta Fidelidade e Exatidão):** Ao localizar vetores nativos, abstrações supersônicas processam a leitura tabular ignorando processos lentos de IA. Os textos, com todo respeito ao design tabular nativo, são convertidos fielmente gerando resultados instantâneos, sem uso de poder custoso de CPU que atrase a sua fila de requisições.
   - **Camada de Visões Integradas (OCR Fallback Impecável):** Se o papel é escaneado em pixel, o *engine* passa para a renderização óptica em alta clareza. São feitos pré-processamentos iterativos de brilho, nitidez, geometria liminar e cálculos de alvos contrastes escuros. O sistema molda proativamente os pesos em torno do algortimo Tesseract configurando a rede *Page Segmentation Mode (PSM)* on-the-fly com adaptações extremas, por exemplo: revertendo paletas de cores e configurando o core da IA para dominar facilmente a decodificação de letras alvas presas em relatórios cinzas e pretos.
3. 📐 **Mapeamento Lógico por Layout Semântico:** Uma inteligência de renderizações separa os metadados gerados (de ambos os métodos de origem) numa hierarquia contextual perfeita subdividindo todos seus domínios de leitura em nichos fundamentais para regras de negócio: **Cabeçalho (Header)**, **Corpo (Body)**, **Rodapé (Footer)** e as incríveis imersões pontuais OCR isoladas em toda e qualquer foto (*Embedded Image*) achada aleatória dentro do corpo do PDF final.
4. 💎 **Estruturação Pura (Feito para LLM e Data Lakes):** Na finalização, as propriedades sistêmicas como Autores do PDF, Datas de Criação, Aliases do Documento juntam-se ao fluxo lido e originam num único formato normalizado altamente limpo (em serializações JSON robustas, ou Texto Plano Imaculado) formatados meticulosamente para integrarem alimentações corporativas e pipelines de modelagens *RAG (Retrieval-Augmented Generation)* sem os comuns ruídos nojentos de final de string das antigas bibliotecas PDF normais.

---

## 🛠 Tecnologias de Ponta Utilizadas

Arquitetura pautada baseando-se por princípios SOLID, testagem unitária acoplada, blindado por tecnologias performáticas e ferramentas Open-Source globais:

- 🐍 **Linguagem Cérebro Backend:** [Python 3.10+](https://www.python.org/)
- 📄 **Manipulação de PDF:** [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) — O core supersônico e esguio em manipulação que permite as buscas textuais, tabulares e extrações nativas puras alcançarem o máximo da velocidade sem degradações.
- 👁️ **Músculo de IA Visão Biológica (OCR):** [Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki) orquestrado cirurgicamente pelo *wrapper* `pytesseract`.
- 🖼️ **Frameworking e Álgebra de Visão:** [Pillow (PIL)](https://pillow.readthedocs.io/en/stable/) e as matrizes otimizadas de cálculos unificadores pelo [NumPy](https://numpy.org/).
- 🎨 **Desktop Modern App (UI UI/UX):** Engajamos o uso limpo usando o amado [CustomTkinter](https://customtkinter.tomschimansky.com/) para layouts fluidos, dark-mode práticos e interatividade minimalista local.
- ⚡ **Servidor RESTful e Framework Web:** Liderando as métricas e o desempenho, a [FastAPI](https://fastapi.tiangolo.com/) potencializada pelos corações em assíncrono do `uvicorn` aceita multipart form objects efetuando pipelines on the go e devolvendo um response sem perdas.
- 🐳 **Deploy Engine:** [Docker](https://www.docker.com/) e orquestrações por [Docker Compose](https://docs.docker.com/compose/) provendo a estabilidade definitiva corporativa livre de maldições e bibliotecas de janelas.
- 🧪 **DevOps Analítico:** Cobertura implacável de testes de CI providos pelas asserções assertivas do *Framework* `pytest` juntamente à tiranias limpas em formatações lidas pelo super-linter e formatador escrito em Rust `Ruff`.

---

## 💼 Modelos de Uso Contíguos

Com design purista em Arquitetura Hexagonal, você atua em três interfaces poderosas, feitas sob demanda do mercado de base corporativa:

### 1. 🖱 Interface Gráfica Orientada Visual (GUI)
Independência Operacional completa e amigável.  
**Alvo Profissional Ideal:** Usuários corporativos de ponta nas extremidades como escritórios advocatícios que lidam com petições, cartórios em digitalização de certidões, ou back-office de contabilidade convertendo holerites retroativos de lotes densos para tabelas editáveis na nuvem local. Um ambiente leve pra se jogar os arquivos no *drag-and-drop* da tela gerando serializados completos em dois milissegundos sem digitar um único comando ou alterar paths pelo windows.

### 2. 💻 Interface de Linha de Comando Autônoma (CLI)
Poderosos subsolos sistêmicos de orquestração.  
**Alvo Especialista Ideal:** Sysadmins, DevOps ou Engenheiros de Dados do ambiente de Cloud montando seus Data Lakes em instâncias linux rodopiando Bash ou CronJobs em background. Permite uso das magias do CLI para desligar ou tunar otimizações visuais (ignorando tratamentos custosos) usando chaves (`--psm`, `--no-preprocess`, `--verbose`). Você joga pra fora e capta o *SysOut* puro direto pra sua indexação vetorial.

### 3. 🌐 Microsserviço Escalado via API REST (Docker + FastAPI)
A cereja em micro-arquiteturas para Fullstacks na nuvem.  
**Alvo Corporativo Master:** Integrações escaladas e massivas web onde o sistema ERP Finance do servidor manda um blob do PDF recebido pelo painel e colhe perfeitamente pela porta `http/8000` um JSON tabulado impecável da fatura ou da NFE para popular um Postgres sem instalar uma só dependência de Tesseract nos seus servidores hospedes base! Tudo executado numa caixa preta auto gerenciável nativa por conteinerização limpa no Debian Linux.

---

## 🚦 Executando Localmente de Forma Profissional

### Pré-requisitos
- Base universal no host necessita do runtime do **Python 3.10 ou versões mais modernas**.
- EXCLUSIVAMENTE quando desejar testar os fluxos manuais de terminal/janelas (*CLI* e *GUI* sem auxílio da malha docker) na sua máquina original Windows/Linux, dedique 30 segundos injetando a suíte principal C++ de visão **[Tesseract-OCR](https://github.com/UB-Mannheim/tesseract/wiki)** da Mannheim nos pacotes base de aplicativos e indique o *Path C:/Program Files/* em suas variáveis de roteamento globais ambientais nativamente (sempre marcando junto *Portuguese* porção adicional para que consiga reconhecer nossa língua).
- Pro ambiente API REST nativo? Somente o **Docker Engine** e o silêncio para apreciar.

### Clone e Start da Engenharia Base
```bash
# Espelhe localmente no seu workplace
git clone https://github.com/DanielDPereira/pdf_ocr_reader.git
cd pdf_ocr_reader

# Arquitetura isolada de uma VENV confiável Python
python -m venv .venv
.\.venv\Scripts\activate      # [Ambientes MS Windows Powershell]
# source .venv/bin/activate  # [Ambientes POSIX Linux e macOS]

# Instala a master branch em depósitos controlados sem inflar ambiente base
pip install -r requirements.txt
```

---

### Iniciações Produtivas na Ferramenta

#### 👩‍💻 A. Chamando o Front Desktop: Interface Gráfica (GUI)
Em 2 segundos aparecerão as interfaces polivalentes na tela em *Dark UI*.
```bash
python -m src.gui
```

#### 🛠️ B. Chamando o Backend Silencioso: Interface (CLI)
Rotas diretas para injeções no terminal (acesse com -h para todos metadados possíveis na ferramenta explícita).
```bash
# Exportando uma página financeira num lote JSON enriquecido detalhadamente (Logs e Verbose On)
python -m src.cli relat_caixa.pdf --output dados_consolidados.json --verbose

# Abasteça as Entranhas do seu ChatGPT pessoal exportando dados pra RAG (Text Purista Format)
python -m src.cli peticao_adv.pdf --output alimentando_ia.txt --format txt

# Tunagem e Moding Profundo: Lidando com Certidões negativas escuras forçando leitura por esparsidade e zerando otimizações base
python -m src.cli certidao_obito.pdf --psm 11 --no-preprocess
```

#### 🚢 C. Lançando Rotinas na Atmosfera Containerizada: API RESTful (Docker World)

Eis aqui a maravilha das nuvens e servidores remotos prontas sem burocracias:
```bash
docker compose up -d --build
```
Dê permissão, aceite o café gerado em processamento binário do docker baixando a vida útil para Alpine e libere os testes navegando em um maravilhoso Swag UI Swagger interativamente mapeado nas portas de *bindings* do teu SO hospede, injetando e experimentando a rotação de arquivos:
👉 **http://localhost:8000/docs**

Finalize todo o ambiente quando o dia e a sua fila de dev caírem em total desligamento e destruição segurável do contêiner com:
```bash
docker compose down
```

> **Para Tribos Dev:** Pode tranquilamente plugar as mudanças em *Hot-Reloading Live* da API nativa sem compilar dockers executando um trivial `python run_api.py`.

---

## 🏗 Formato JSON: Big Data Enriquecida Mapeada
Independentemente dos processos escolhidos para interagir, todo os mapeamentos serão desconstruídos para normalização robusta integrável como os das *NoSQL Database* e documentais com facilidade total para integrações externas.

```json
{
  "file": "aditivo_trabalho.pdf",
  "total_pages": 1,
  "metadata": {
    "title": "Aditivo Final Confidencial",
    "author": "Gerência Financeira SA",
    "creation_date": "2026-03-23 09:30:00 -03:00"
  },
  "pages": [
    {
      "page_number": 1,
      "full_text": "Cabeçalho Fiscal\n\nCláusula Financeira\n\nRodapé Contratual NF",
      "header": { "text": "Cabeçalho Fiscal" },
      "body": { "text": "Cláusula Financeira" },
      "footer": { "text": "Rodapé Contratual NF" },
      "embedded_images": [
        { "index": 0, "ocr_text": "Selo Reconhecimento Firme Autêntica Cartório", "width": 450, "height": 380 }
      ]
    }
  ]
}
```

---

## 🧪 Excelência Regicida e Cobertura Confiança

As bases dos fluxos de trabalhos não foram feitas amadoramente. O Mock implementado injeta segurança e coesão sob cada classe modular implementada em um esqueleto *TDD* implacável.  
Trabalhadores testando e iterando na infraestrutura executariam por sua rotina de refatoração garantindo qualidade com:

```bash
# Execução da suíte massiva integral cruzando módulos, isolamento unitário em tempo veloz
pytest tests/ -v

# Cobertura gráfica terminal e dedução dos ramos órfãos baseando as árvores codificadas e relatando pontos falsos não-testados na execução src
pytest tests/ --cov=src --cov-report=term-missing
```

---

<div align="center">

  <b>👨‍💻 Criado e Desenvolvido por <a href="https://github.com/DanielDPereira">Daniel Dias Pereira</a></b><br><br>
  <i>Desenvolvido orgulhosamente com o auxílio brilhante da <b>Inteligência Artificial</b>, acelerado e codificado inteiramente por dentro da IDE <a href="https://antigravity.google/">Antigravity</a>.</i>

</div>
