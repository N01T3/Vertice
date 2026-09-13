"""Filtro de sigilo para envio à IA.

Porquê: dado de cliente nunca sai da máquina como consulta;
consulta com identificador é bloqueada e vira incidente, não reescrita.
"""

from __future__ import annotations

from core.documents.constants import TERMOS_SIGILOSOS
from core.documents.errors import ErroSigilo
from core.documents.types import TrechoExtraido


def contem_dado_sigiloso(texto: str) -> bool:
    """Detecta termo de cliente em texto livre, sem depender de IA."""
    inferior = texto.lower()
    return any(termo in inferior for termo in TERMOS_SIGILOSOS)


def validar_trechos_para_ia(trechos: list[TrechoExtraido]) -> None:
    """Bloqueia lote com sigilo antes de qualquer chamada externa."""
    for trecho in trechos:
        if contem_dado_sigiloso(trecho.texto):
            raise ErroSigilo(
                "trecho com possível dado de cliente; envio à IA bloqueado "
                f"na origem {trecho.origem}#{trecho.pagina_ou_aba}"
            )
        if contem_dado_sigiloso(trecho.origem):
            raise ErroSigilo("nome de arquivo com dado de cliente; renomear antes.")
