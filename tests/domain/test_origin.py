"""Origem: id_origem validado no construtor — nunca um str cru.

Porquê: regra 1 de VERTICE-REGRAS.md ("a IA nunca produz número
mágico") só é impossibilidade de verdade se o tipo recusar existir
sem origem válida — não apenas se alguém lembrar de checar antes.
"""

from __future__ import annotations

import pytest

from core.domain.origin import Origem, OrigemInvalida, resolve, sanear_endereco


def test_resolve_aceita_as_seis_raizes() -> None:
    for exemplo in (
        "GEO:planta-r03#parede/1187",
        "BASE:sinapi-2026-08#87622",
        "USUARIO:rt-01#2026-09-13T14:02",
        "DOC:memorial#p12:4",
        "ACHADO:4471",
        "CALCULO:item-3120",
    ):
        assert resolve(exemplo), exemplo


def test_resolve_recusa_raiz_desconhecida() -> None:
    assert not resolve("CHUTE:qualquer-coisa")
    assert not resolve("sem raiz nenhuma")


def test_origem_valida_constroi_normalmente() -> None:
    origem = Origem("BASE:sinapi-2026-08#87622")
    assert origem.raiz == "BASE"
    assert str(origem) == "BASE:sinapi-2026-08#87622"


def test_origem_invalida_nao_constroi() -> None:
    """O tipo recusa existir fora da gramática — não é checagem à parte."""
    with pytest.raises(OrigemInvalida):
        Origem("numero-magico-sem-origem")


def test_sanear_endereco_preserva_pista_com_acento() -> None:
    resultado = sanear_endereco("página 12 — aba 'Resumo'.pdf", limite=60, vazio="x")
    assert resultado.startswith("página")


def test_sanear_endereco_vazio_devolve_marcador() -> None:
    assert sanear_endereco("   ", limite=10, vazio="nao-resolvivel") == "nao-resolvivel"
