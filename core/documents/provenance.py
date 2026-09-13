"""Montagem do id_origem para número lido em documento entregue.

Porquê: a gramática é de `domain/origin.py`; aqui fica só a raiz DOC e
o que conta como endereço num memorial — página, aba e posição no lote.
"""

from __future__ import annotations

from core.documents.constants import (
    LIMITE_TEXTO_ORIGEM,
    ORIGEM_NAO_RESOLVIVEL,
    RAIZ_ORIGEM_DOCUMENTO,
)
from core.documents.types import TrechoExtraido
from core.domain.origin import sanear_endereco


def montar_id_origem(trecho: TrechoExtraido, posicao: int) -> str:
    """Monta id_origem na raiz DOC, resolvível até página e posição.

    Porquê: número lido em documento entregue precisa apontar o
    parágrafo exato; sem isso a citação é opinião do modelo.
    """
    chave = _endereco(trecho.origem)
    localizador = _endereco(trecho.pagina_ou_aba)
    return f"{RAIZ_ORIGEM_DOCUMENTO}:{chave}#{localizador}:{posicao}"


def _endereco(bruto: str) -> str:
    """Aplica o saneamento do domínio com os limites da ingestão."""
    return sanear_endereco(bruto, LIMITE_TEXTO_ORIGEM, ORIGEM_NAO_RESOLVIVEL)
