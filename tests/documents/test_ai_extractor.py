"""IA leitora degrada sem inventar e sigilo bloqueia cliente.

Porquê: número sem documento é número mágico; dado de cliente
nunca sai da máquina, nem como trecho de memorial.
"""

from __future__ import annotations

import pytest

from core.classification.document_extractor import (
    extrair_exigencias,
    extrair_servicos,
)
from core.documents.ai_extractor import validar_exigencias, validar_servicos
from core.documents.errors import ErroSigilo
from core.documents.types import TrechoExtraido
from core.domain.origin import resolve


def _trecho(texto: str, pagina: str = "página 1") -> TrechoExtraido:
    return TrechoExtraido(pagina_ou_aba=pagina, texto=texto, origem="memorial.txt")


def test_offline_sem_numero_devolve_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem chave, IA degrada para OFFLINE e quantidade vira None."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    trechos = [_trecho("Pintura de parede interna sem quantitativo definido.")]
    servicos = extrair_servicos(trechos)
    assert len(servicos) >= 1
    assert all(servico.quantidade is None for servico in servicos)
    assert all(servico.id_origem for servico in servicos)


def test_offline_com_numero_preserva_decimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Com número no trecho, OFFLINE preserva Decimal com origem."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    trechos = [_trecho("Alvenaria de vedação com 12,5 m2 conforme projeto.")]
    servicos = extrair_servicos(trechos)
    assert len(servicos) >= 1
    primeiro = servicos[0]
    assert primeiro.quantidade is not None
    assert str(primeiro.quantidade) == "12.5"
    assert primeiro.unidade_sugerida in ("m2", "m²")


def test_sigilo_bloqueia_memorial_com_cliente(monkeypatch: pytest.MonkeyPatch) -> None:
    """Memorial com nome e endereço nunca chega à IA."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    trechos = [_trecho("Obra da Santa Casa na Rua Coronel Vaz, 123.")]
    with pytest.raises(ErroSigilo):
        extrair_servicos(trechos)
    with pytest.raises(ErroSigilo):
        extrair_exigencias(trechos)


def test_exigencia_sem_trecho_descartada() -> None:
    """Exigência sem trecho citável cai antes do dossiê."""
    trechos = [_trecho("Executar conforme NBR 15965.", "página 2")]
    carga = {
        "exigencias": [
            {
                "descricao": "Seguir norma",
                "fonte": "página 2",
                "trecho_citado": "",
                "pagina_ou_aba": "página 2",
            }
        ]
    }
    assert validar_exigencias(carga, trechos) == []


def test_servico_com_unidade_invalida_descartado() -> None:
    """Unidade fora do vocabulário não entra nem como sugestão."""
    trechos = [_trecho("Alvenaria com 10 m2.", "linha 1")]
    carga = {
        "servicos": [
            {
                "descricao": "Alvenaria",
                "unidade_sugerida": "litros-por-hora",
                "quantidade": "10",
                "trecho_citado": "Alvenaria com 10 m2.",
                "pagina_ou_aba": "linha 1",
            }
        ]
    }
    assert validar_servicos(carga, trechos) == []


def test_id_origem_respeita_a_gramatica(monkeypatch: pytest.MonkeyPatch) -> None:
    """Âncora de §4.1: origem emitida resolve pela gramática, sempre.

    Porquê: a auditoria de proveniência A11 percorre id_origem por
    máquina; formato livre transforma a varredura em adivinhação.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    trechos = [
        TrechoExtraido(
            pagina_ou_aba="página 12 — aba 'Resumo'",
            texto="Alvenaria de vedação com 12,5 m2 conforme projeto.",
            origem="Memorial Descritivo (rev. B).pdf",
        )
    ]
    servicos = extrair_servicos(trechos)
    assert servicos
    for servico in servicos:
        assert resolve(servico.id_origem), servico.id_origem
        assert servico.id_origem.startswith("DOC:")
