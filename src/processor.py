import fitz  # PyMuPDF

def extrair_dados_pdf(caminho_pdf):
    """Extrai texto e metadados de um PDF e retorna um dicionário."""
    with fitz.open(caminho_pdf) as doc:
        texto = ""
        for pagina in doc:
            texto += pagina.get_text("text") + "\n"

        metadados = doc.metadata
        numero_paginas = len(doc)  # Agora, o número de páginas é calculado enquanto o doc está aberto.

    return {
        "texto": texto.strip(),
        "metadados": {
            "titulo": metadados.get("title", ""),
            "autor": metadados.get("author", ""),
            "assunto": metadados.get("subject", ""),
            "criado_em": metadados.get("creationDate", ""),
            "modificado_em": metadados.get("modDate", ""),
            "numero_paginas": numero_paginas,
        }
    }