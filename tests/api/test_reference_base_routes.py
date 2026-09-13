"""Os dois contratos travados por VERTICE-REGRAS.md §4.4, e o token (VS-02).

Porquê testar o contrato pelo path exato: uma regressão de assinatura
aqui é o tipo de mudança que a regra existe para impedir — o teste é
a prova de que ela não aconteceu.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.api.app import criar_app
from core.reference_base.schema import criar_esquema

TOKEN_DE_TESTE = "token-fixo-para-teste"
ID_BASE = 1


def _preparar_banco(caminho: Path) -> None:
    """Base mínima: uma composição com um insumo, preço em SP onerado."""
    conexao = sqlite3.connect(caminho)
    criar_esquema(conexao)
    conexao.execute(
        "INSERT INTO base_referencia "
        "(id, mes_referencia, data_emissao, arquivo_nome, arquivo_hash, "
        "importado_em, codigo_recuperado, total_composicoes, total_insumos) "
        "VALUES (1, '2026-08', '2026-08-11', 'x.xlsx', 'hash', "
        "datetime('now'), 0, 1, 1)"
    )
    conexao.execute(
        "INSERT INTO item_sinapi "
        "(id_base, codigo, tipo, grupo, descricao, unidade, situacao) "
        "VALUES (1, 'CIMENTO', 'INSUMO', NULL, 'Cimento', 'KG', NULL)"
    )
    conexao.execute(
        "INSERT INTO item_sinapi "
        "(id_base, codigo, tipo, grupo, descricao, unidade, situacao) "
        "VALUES (1, 'ARGAMASSA', 'COMPOSICAO', NULL, 'Argamassa de teste', 'M2', NULL)"
    )
    conexao.execute(
        "INSERT INTO preco_sinapi "
        "(id_base, codigo, tipo, uf, regime, valor_centavos, percentual_as) "
        "VALUES (1, 'CIMENTO', 'INSUMO', 'SP', 'ONERADO', 150, NULL)"
    )
    conexao.execute(
        "INSERT INTO composicao_item "
        "(id_base, codigo_composicao, tipo_item, codigo_item, coeficiente, situacao) "
        "VALUES (1, 'ARGAMASSA', 'INSUMO', 'CIMENTO', '2', NULL)"
    )
    conexao.execute(
        "INSERT INTO busca_sinapi "
        "(codigo, descricao, grupo, unidade, tipo, id_base) "
        "VALUES ('ARGAMASSA', 'Argamassa de teste', NULL, 'M2', "
        f"'COMPOSICAO', {ID_BASE})"
    )
    conexao.commit()
    conexao.close()


@pytest.fixture
def cliente(tmp_path: Path) -> Iterator[TestClient]:
    caminho_banco = tmp_path / "teste.db"
    _preparar_banco(caminho_banco)
    app = criar_app(caminho_banco, token=TOKEN_DE_TESTE)
    with TestClient(app) as cliente:
        yield cliente


def _cabecalho() -> dict[str, str]:
    return {"X-Vertice-Token": TOKEN_DE_TESTE}


def test_saude_nao_exige_token(cliente: TestClient) -> None:
    """`/saude` é o que o shell sonda a cada 5 s — sem barreira (§2.2)."""
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200


def test_rota_protegida_sem_token_e_401(cliente: TestClient) -> None:
    """VS-02: sidecar recusa requisição sem token de sessão."""
    resposta = cliente.get("/sinapi/buscar", params={"termo": "cimento"})
    assert resposta.status_code == 401


def test_rota_protegida_com_token_errado_e_401(cliente: TestClient) -> None:
    """Token presente, mas errado, ainda é recusado — não basta existir."""
    resposta = cliente.get(
        "/sinapi/buscar",
        params={"termo": "cimento"},
        headers={"X-Vertice-Token": "token-errado"},
    )
    assert resposta.status_code == 401


def test_buscar_contrato_de_regras_4_4(cliente: TestClient) -> None:
    """`GET /sinapi/buscar` — o path exato travado por REGRAS §4.4."""
    resposta = cliente.get(
        "/sinapi/buscar", params={"termo": "argamassa"}, headers=_cabecalho()
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert any(item["codigo"] == "ARGAMASSA" for item in corpo)


def test_explodir_contrato_de_regras_4_4(cliente: TestClient) -> None:
    """`GET /sinapi/composicao/{codigo}/explodir` — o path exato de §4.4."""
    resposta = cliente.get(
        "/sinapi/composicao/ARGAMASSA/explodir",
        params={"uf": "SP", "regime": "ONERADO"},
        headers=_cabecalho(),
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["custo_total_centavos"] == 300  # 2 kg x R$1,50
    assert corpo["completo"] is True
    assert corpo["arvore"]["filhos"][0]["codigo"] == "CIMENTO"


def test_explodir_sem_id_base_usa_a_mais_recente(cliente: TestClient) -> None:
    """Sem `id_base`, a rota resolve para a última base importada."""
    resposta = cliente.get(
        "/sinapi/composicao/ARGAMASSA/explodir",
        params={"uf": "SP", "regime": "ONERADO"},
        headers=_cabecalho(),
    )
    assert resposta.status_code == 200


def test_explodir_codigo_inexistente_e_404(cliente: TestClient) -> None:
    """Código fora do catálogo não deve virar 500 — é 404, previsível."""
    resposta = cliente.get(
        "/sinapi/composicao/NAO_EXISTE/explodir",
        params={"uf": "SP", "regime": "ONERADO"},
        headers=_cabecalho(),
    )
    assert resposta.status_code == 404


def test_explodir_regime_invalido_e_422(cliente: TestClient) -> None:
    """Regime fora do vocabulário oficial barra na validação, antes da rota."""
    resposta = cliente.get(
        "/sinapi/composicao/ARGAMASSA/explodir",
        params={"uf": "SP", "regime": "INVENTADO"},
        headers=_cabecalho(),
    )
    assert resposta.status_code == 422
