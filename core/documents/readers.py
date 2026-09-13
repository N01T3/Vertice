"""Fachada dos leitores: detecção, despacho e identidade.

Porquê: quem recebe arquivo precisa de um ponto único que detecta,
calcula hash e despacha; detalhe de cada formato mora nos módulos base.
"""

from __future__ import annotations

from pathlib import Path

from core.documents.base_readers import (
    calcular_hash,
    extrair_texto_csv,
    extrair_texto_pdf,
    extrair_texto_txt,
)
from core.documents.errors import ErroTipoNaoSuportado
from core.documents.office_readers import extrair_texto_docx, extrair_texto_xlsx
from core.documents.types import DocumentoEntrada, TipoDocumento, TrechoExtraido

__all__ = [
    "calcular_hash",
    "criar_documento",
    "detectar_tipo",
    "extrair_texto_csv",
    "extrair_texto_docx",
    "extrair_texto_pdf",
    "extrair_texto_txt",
    "extrair_texto_xlsx",
    "extrair_trechos",
]


def detectar_tipo(caminho: Path) -> TipoDocumento:
    """Sugere tipo pela extensão; RT confirma, nunca trava."""
    sufixo = caminho.suffix.lower()
    if sufixo == ".dxf":
        return "CAD_DXF"
    if sufixo == ".dwg":
        return "CAD_DWG"
    if sufixo == ".pdf":
        return "PDF_GENERICO"
    if sufixo in (".docx", ".doc", ".txt", ".md"):
        return "MEMORIAL_DESCRITIVO"
    if sufixo in (".xlsx", ".xlsm", ".csv"):
        return "PLANILHA"
    if sufixo == ".ifc":
        return "CAD_DXF"
    raise ErroTipoNaoSuportado(f"extensão sem leitor: {sufixo}")


def criar_documento(
    caminho: Path, tipo_forcado: TipoDocumento | None = None
) -> DocumentoEntrada:
    """Registra arquivo com hash e tamanho para rastrear a medição futura."""
    tipo_final = tipo_forcado if tipo_forcado is not None else detectar_tipo(caminho)
    resumo = calcular_hash(caminho)
    tamanho = _medir_tamanho(caminho)
    return DocumentoEntrada(
        caminho=caminho,
        tipo=tipo_final,
        hash_sha256=resumo,
        tamanho_bytes=tamanho,
    )


def extrair_trechos(documento: DocumentoEntrada) -> list[TrechoExtraido]:
    """Despacha para o leitor do tipo; CAD usa triagem própria."""
    if documento.tipo == "MEMORIAL_DESCRITIVO":
        return _extrair_por_extensao_textual(documento.caminho)
    if documento.tipo in ("PLANILHA", "MEMORIAL_ATIVIDADES"):
        return _extrair_por_extensao_planilha(documento.caminho)
    if documento.tipo == "PDF_GENERICO":
        return extrair_texto_pdf(documento.caminho)
    raise ErroTipoNaoSuportado("CAD usa triagem própria, não extração textual")


def _medir_tamanho(caminho: Path) -> int:
    """Mede bytes do arquivo com erro tipado para rastreabilidade."""
    from core.documents.errors import ErroLeituraDocumento

    try:
        return caminho.stat().st_size
    except OSError as erro:
        raise ErroLeituraDocumento(f"falha ao medir {caminho.name}") from erro


def _extrair_por_extensao_textual(caminho: Path) -> list[TrechoExtraido]:
    """Escolhe leitor textual pela extensão do memorial."""
    sufixo = caminho.suffix.lower()
    if sufixo in (".txt", ".md"):
        return extrair_texto_txt(caminho)
    if sufixo in (".docx", ".doc"):
        return extrair_texto_docx(caminho)
    if sufixo == ".pdf":
        return extrair_texto_pdf(caminho)
    return extrair_texto_txt(caminho)


def _extrair_por_extensao_planilha(caminho: Path) -> list[TrechoExtraido]:
    """Escolhe leitor de planilha pela extensão do arquivo."""
    if caminho.suffix.lower() == ".csv":
        return extrair_texto_csv(caminho)
    return extrair_texto_xlsx(caminho)
