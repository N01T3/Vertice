"""Sugestão de tipologia para instanciar template de obra.

Porquê: EAP nasce de classificação em dois eixos (resultado e espaço);
sugerir a tipologia evita grupo digitado por obra e permite comparar.
"""

from __future__ import annotations

_MAPA_TIPOLOGIAS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("hospital", "santa casa", "cme"), "reforma_hospitalar"),
    (("residencial", "apartamento"), "edificacao_residencial"),
    (("comercial", "loja", "escritório"), "edificacao_comercial"),
    (("retrofit", "corporativo"), "retrofit_corporativo"),
)


def sugerir_tipologia(descricao_obra: str) -> str:
    """Sugere tipologia pelo vocabulário; RT confirma, nunca trava."""
    inferior = descricao_obra.lower()
    for pistas, tipologia in _MAPA_TIPOLOGIAS:
        if _contem_pista(inferior, pistas):
            return tipologia
    return "obra_publica_padrao"


def _contem_pista(inferior: str, pistas: tuple[str, ...]) -> bool:
    """Diz se alguma pista aparece na descrição, sem encadear ors."""
    return any(pista in inferior for pista in pistas)
