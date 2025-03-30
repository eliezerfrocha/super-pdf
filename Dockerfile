# Usa uma imagem Python oficial
FROM python:3.10

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários para o container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte
COPY src/ /app/src/

# Define o comando padrão ao rodar o container
CMD ["python", "/app/src/main.py"]