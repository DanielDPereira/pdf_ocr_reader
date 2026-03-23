# Usamos uma imagem oficial enxuta do Python 3.11 no Linux Debian
FROM python:3.11-slim

# Definir diretório de trabalho dentro do container
WORKDIR /app

# Variáveis de ambiente para o Python não criar __pycache__ e o log ser em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalar as dependências do sistema operacional:
# - tesseract-ocr: o núcleo do OCR
# - tesseract-ocr-por / eng: idiomas Português e Inglês
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências Python primeiro (para aproveitar cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código da aplicação
COPY . .

# Expõe a porta 8000 (onde a FastAPI vai escutar)
EXPOSE 8000

# Comando para rodar a aplicação em modo de produção
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
