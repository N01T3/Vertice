"""Base textual: hash, tipo, TXT, CSV e PDF.

Porquê: separa o que é stdlib puro do que precisa de XML de office;
arquivo pequeno por construção, não por boa vontade.
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path
from typing import Any

from core.documents.constants import LIMITE_CARACTERES_TRECHO, TAMANHO_BLOCO_HASH
from core.documents.errors import ErroDependenciaAusente, ErroLeituraDocumento
from core.documents.types import TrechoExtraido


def calcular_hash(caminho: Path) -> str:
    """Calcula SHA256 em blocos para não carregar memorial inteiro."""
    try:
        somador = hashlib.sha256()
        with caminho.open("rb") as manuseio:
            while True:
                bloco = manuseio.read(TAMANHO_BLOCO_HASH)
                if not bloco:
                    break
                somador.update(bloco)
    except OSError as erro:
        raise ErroLeituraDocumento(f"falha ao ler {caminho.name}") from erro
    return somador.hexdigest()


def ler_texto_arquivo(caminho: Path) -> str:
    """Tenta utf-8 e cai para latin-1, pois memorial vem de Windows."""
    try:
        return caminho.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return caminho.read_text(encoding="latin-1")
        except OSError as erro:
            raise ErroLeituraDocumento(f"falha ao ler {caminho.name}") from erro
    except OSError as erro:
        raise ErroLeituraDocumento(f"falha ao ler {caminho.name}") from erro


def origem_base(caminho: Path) -> str:
    """Base da proveniência: nome do arquivo, sem dado de cliente."""
    return caminho.name


def dividir_texto(texto: str, pagina: str, origem: str) -> list[TrechoExtraido]:
    """Fatia texto longo para caber no prompt mantendo citação."""
    limpo = texto.strip()
    if not limpo:
        return []
    partes = fatiar(limpo)
    saida: list[TrechoExtraido] = []
    for posicao, parte in enumerate(partes):
        rotulo = f"{pagina}#{posicao}" if len(partes) > 1 else pagina
        saida.append(TrechoExtraido(pagina_ou_aba=rotulo, texto=parte, origem=origem))
    return saida


def fatiar(texto: str) -> list[str]:
    """Corta por limite de caracteres sem quebrar no meio da palavra."""
    saida: list[str] = []
    restante = texto
    while len(restante) > LIMITE_CARACTERES_TRECHO:
        corte = restante.rfind(" ", 0, LIMITE_CARACTERES_TRECHO)
        if corte <= 0:
            corte = LIMITE_CARACTERES_TRECHO
        saida.append(restante[:corte].strip())
        restante = restante[corte:].strip()
    if restante:
        saida.append(restante)
    return saida


def extrair_texto_txt(caminho: Path) -> list[TrechoExtraido]:
    """Lê memorial em texto puro com queda para latin-1."""
    conteudo = ler_texto_arquivo(caminho)
    return dividir_texto(conteudo, "página 1", origem_base(caminho))


def extrair_texto_csv(caminho: Path) -> list[TrechoExtraido]:
    """Lê planilha CSV linha a linha, preservando número da linha."""
    try:
        with caminho.open("r", encoding="utf-8-sig", newline="") as manuseio:
            leitor = csv.reader(manuseio)
            linhas = list(leitor)
    except OSError as erro:
        raise ErroLeituraDocumento(f"falha ao ler {caminho.name}") from erro
    except csv.Error as erro:
        raise ErroLeituraDocumento(f"csv deformado: {caminho.name}") from erro
    return linhas_para_trechos(linhas, origem_base(caminho))


def linhas_para_trechos(linhas: list[list[str]], origem: str) -> list[TrechoExtraido]:
    """Transforma cada linha CSV em trecho endereçável por linha."""
    saida: list[TrechoExtraido] = []
    for indice, colunas in enumerate(linhas):
        texto = " | ".join(coluna.strip() for coluna in colunas).strip(" |")
        if texto:
            rotulo = f"linha {indice + 1}"
            saida.append(
                TrechoExtraido(pagina_ou_aba=rotulo, texto=texto, origem=origem)
            )
    return saida


def extrair_texto_pdf(caminho: Path) -> list[TrechoExtraido]:
    """Extrai PDF via pypdf opcional; sem ele, orienta sem travar."""
    try:
        from pypdf import PdfReader as LeitorPdf
    except ImportError as erro:
        raise ErroDependenciaAusente(
            "leitura de PDF exige pypdf; instale o extra pdf ou envie TXT/CSV"
        ) from erro
    try:
        leitor = LeitorPdf(str(caminho))
        paginas: list[Any] = list(leitor.pages)
    except OSError as erro:
        raise ErroLeituraDocumento(f"falha ao ler {caminho.name}") from erro
    return paginas_pdf_para_trechos(paginas, origem_base(caminho))


def paginas_pdf_para_trechos(paginas: list[Any], origem: str) -> list[TrechoExtraido]:
    """Converte páginas de PDF em trechos, ignorando página vazia."""
    saida: list[TrechoExtraido] = []
    for indice, pagina in enumerate(paginas):
        extrair = getattr(pagina, "extract_text", None)
        texto = str(extrair() or "") if callable(extrair) else ""
        if texto.strip():
            rotulo = f"página {indice + 1}"
            saida.extend(dividir_texto(texto, rotulo, origem))
    return saida
