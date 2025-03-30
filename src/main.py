import os
import re
import pymongo
import mysql.connector
from processor import extrair_dados_pdf

# Configuração do MongoDB
mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
mongo_db = mongo_client["pdf_database"]
colecao_pdfs = mongo_db["pdfs"]

# Configuração do MySQL
mysql_conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="user",
    password="password",
    database="metadata_db"
)
mysql_cursor = mysql_conn.cursor()

# Criar tabela de metadados se não existir
mysql_cursor.execute("""
    CREATE TABLE IF NOT EXISTS metadados_pdf (
        id INT AUTO_INCREMENT PRIMARY KEY,
        titulo VARCHAR(255),
        autor VARCHAR(255),
        assunto VARCHAR(255),
        criado_em VARCHAR(255),
        modificado_em VARCHAR(255),
        numero_paginas INT
    )
""")
mysql_conn.commit()

def verificar_documento_processado(nome_arquivo):
    """Verifica se o documento já foi processado no MongoDB com base no nome do arquivo."""
    documento_existente = colecao_pdfs.find_one({"nome_arquivo": nome_arquivo})
    return documento_existente is not None

def preencher_metadados(metadados, texto_pdf):
    """Garantir que todos os campos de metadados sejam preenchidos, mesmo que vazios, 
    com base no conteúdo do PDF quando necessário."""
    
    # Função para tentar encontrar um valor em texto com regex
    def procurar_regex(texto, padrao):
        resultado = re.search(padrao, texto, re.IGNORECASE)
        if resultado:
            return resultado.group(1)
        return None

    # Preenchendo os metadados com os valores encontrados ou um valor padrão
    metadados_processados = {
        "titulo": metadados.get("title", "Desconhecido"),
        "autor": metadados.get("author", "Desconhecido"),
        "assunto": metadados.get("subject", "Desconhecido"),
        "criado_em": metadados.get("creationDate", "Desconhecido"),
        "modificado_em": metadados.get("modDate", "Desconhecido"),
        "numero_paginas": metadados.get("numero_paginas", 0)
    }

    # Tentando encontrar o título no texto (se não estiver nos metadados)
    if metadados_processados["titulo"] == "Desconhecido":
        metadados_processados["titulo"] = procurar_regex(texto_pdf, r'PROCESSO Nº:.*?([^\n]+)')

    # Tentando encontrar o autor no texto
    if metadados_processados["autor"] == "Desconhecido":
        metadados_processados["autor"] = procurar_regex(texto_pdf, r'(\b[A-Z][a-z]+(?: [A-Z][a-z]+)*)\s+(?:e outros)?\s+.*\b(?:AUTOR|DELEGADO|RESPONSÁVEL)\b')

    # Tentando encontrar o assunto no texto
    if metadados_processados["assunto"] == "Desconhecido":
        metadados_processados["assunto"] = procurar_regex(texto_pdf, r'ASSUNTO:.*?([^\n]+)')

    # Tentando encontrar as datas no texto
    if metadados_processados["criado_em"] == "Desconhecido":
        metadados_processados["criado_em"] = procurar_regex(texto_pdf, r'(\d{2}/\d{2}/\d{4})')

    if metadados_processados["modificado_em"] == "Desconhecido":
        metadados_processados["modificado_em"] = procurar_regex(texto_pdf, r'Assinado eletronicamente por:.*?(\d{2}/\d{2}/\d{4})')

    return metadados_processados

def processar_pdfs(diretorio_pdf):
    """Processa todos os PDFs no diretório especificado."""
    for arquivo in os.listdir(diretorio_pdf):
        if arquivo.endswith(".pdf"):
            caminho_pdf = os.path.join(diretorio_pdf, arquivo)
            dados = extrair_dados_pdf(caminho_pdf)

            # Debug: Verificar os dados extraídos antes de passar para o preenchimento de metadados
            print(f"📄 Processando arquivo: {arquivo}")
            print(f"Texto extraído: {dados['texto'][:100]}...")  # Exibindo o início do texto
            print(f"Metadados extraídos: {dados['metadados']}")

            # Preencher metadados com os dados encontrados no texto
            dados["metadados"] = preencher_metadados(dados["metadados"], dados["texto"])

            # Debug: Verificar metadados após preenchimento
            print(f"Metadados preenchidos: {dados['metadados']}")

            # Inserir texto no MongoDB
            colecao_pdfs.insert_one({"nome_arquivo": arquivo, "conteudo": dados["texto"]})
            print("Texto inserido no MongoDB.")

            # Inserir metadados no MySQL
            mysql_cursor.execute("""
                INSERT INTO metadados_pdf (titulo, autor, assunto, criado_em, modificado_em, numero_paginas)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                dados["metadados"]["titulo"],
                dados["metadados"]["autor"],
                dados["metadados"]["assunto"],
                dados["metadados"]["criado_em"],
                dados["metadados"]["modificado_em"],
                dados["metadados"]["numero_paginas"]
            ))
            mysql_conn.commit()
            print(f"Metadados inseridos no MySQL: {dados['metadados']}")

            print(f"📄 Processado: {arquivo}")

if __name__ == "__main__":
    diretorio_pdf = "src/pdfs"  # Caminho para o diretório dos PDFs
    processar_pdfs(diretorio_pdf)