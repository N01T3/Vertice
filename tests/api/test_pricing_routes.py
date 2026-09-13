"""Rotas de orçamento e BDI — cadastro, salvar, reler, tudo pelo HTTP.

Porquê a âncora do CME aparece de novo aqui: a rota usa a fórmula real
do pacote instalado (`packages/civil-construction-br/package.yaml`),
não uma fórmula de teste — se o pacote real divergir do que os módulos
internos já provam, é aqui que a integração ponta a ponta pega.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.api.app import criar_app
from core.pricing.schema import criar_esquema as criar_esquema_pricing
from core.reference_base.schema import criar_esquema as criar_esquema_reference_base

TOKEN_DE_TESTE = "token-fixo-para-teste"

PARCELAS_CME = {
    "administracao_central": "0.0401",
    "seguro_garantia": "0.0032",
    "risco": "0.0050",
    "despesas_financeiras": "0.0102",
    "lucro": "0.0664",
    "pis": "0.0065",
    "cofins": "0.0300",
    "iss": "0.0500",
    "cprb": "0",
}


def _preparar_banco(caminho: Path) -> None:
    conexao = sqlite3.connect(caminho)
    criar_esquema_reference_base(conexao)
    criar_esquema_pricing(conexao)
    conexao.execute(
        "INSERT INTO base_referencia "
        "(id, mes_referencia, data_emissao, arquivo_nome, arquivo_hash, "
        "importado_em, codigo_recuperado, total_composicoes, total_insumos) "
        "VALUES (1, '2026-08', '2026-08-11', 'x.xlsx', 'hash', "
        "datetime('now'), 0, 0, 0)"
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


def _criar_orcamento(cliente: TestClient) -> int:
    resposta = cliente.post(
        "/orcamento",
        json={
            "identificacao": "Reforma CME",
            "regime": "ONERADO",
            "uf": "SP",
            "data_base": "2026-08",
        },
        headers=_cabecalho(),
    )
    assert resposta.status_code == 201
    return int(resposta.json()["id"])


def test_criar_orcamento_sem_token_e_401(cliente: TestClient) -> None:
    resposta = cliente.post(
        "/orcamento",
        json={
            "identificacao": "X",
            "regime": "ONERADO",
            "uf": "SP",
            "data_base": "2026-08",
        },
    )
    assert resposta.status_code == 401


def test_criar_orcamento_e_ler_de_volta(cliente: TestClient) -> None:
    id_orcamento = _criar_orcamento(cliente)
    resposta = cliente.get(f"/orcamento/{id_orcamento}", headers=_cabecalho())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["identificacao"] == "Reforma CME"
    assert corpo["regime"] == "ONERADO"
    assert corpo["id_base"] == 1
    assert corpo["id_origem"].startswith("USUARIO:sidecar#")


def test_obter_orcamento_inexistente_e_404(cliente: TestClient) -> None:
    resposta = cliente.get("/orcamento/999", headers=_cabecalho())
    assert resposta.status_code == 404


def test_salvar_bdi_reproduz_a_ancora_do_cme(cliente: TestClient) -> None:
    """A fórmula vem do pacote real — 23,62% é a prova de integração ponta a ponta."""
    id_orcamento = _criar_orcamento(cliente)
    resposta = cliente.post(
        f"/orcamento/{id_orcamento}/bdi",
        json={
            "parcelas": PARCELAS_CME,
            "municipio_iss": "Cerqueira César",
            "base_iss": "1.00",
        },
        headers=_cabecalho(),
    )
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert round(float(corpo["bdi_percentual"]), 4) == 0.2362
    assert corpo["faixa_tcu"] == "ENTRE_MEDIO_E_3_QUARTIL"
    assert corpo["exige_justificativa"] is False
    assert corpo["alertas"] == []


def test_obter_bdi_sem_cadastro_e_404(cliente: TestClient) -> None:
    id_orcamento = _criar_orcamento(cliente)
    resposta = cliente.get(f"/orcamento/{id_orcamento}/bdi", headers=_cabecalho())
    assert resposta.status_code == 404


def test_obter_bdi_depois_de_salvar_relê_o_mesmo_percentual(
    cliente: TestClient,
) -> None:
    id_orcamento = _criar_orcamento(cliente)
    cliente.post(
        f"/orcamento/{id_orcamento}/bdi",
        json={
            "parcelas": PARCELAS_CME,
            "municipio_iss": "Cerqueira César",
            "base_iss": "1.00",
        },
        headers=_cabecalho(),
    )
    resposta = cliente.get(f"/orcamento/{id_orcamento}/bdi", headers=_cabecalho())
    assert resposta.status_code == 200
    assert round(float(resposta.json()["bdi_percentual"]), 4) == 0.2362


def test_bdi_cprb_positivo_em_regime_onerado_gera_alerta(cliente: TestClient) -> None:
    """P03: dupla contagem não trava a rota — só entra na lista de alertas."""
    id_orcamento = _criar_orcamento(cliente)
    parcelas_com_cprb = {**PARCELAS_CME, "cprb": "0.045"}
    resposta = cliente.post(
        f"/orcamento/{id_orcamento}/bdi",
        json={
            "parcelas": parcelas_com_cprb,
            "municipio_iss": "Cerqueira César",
            "base_iss": "1.00",
        },
        headers=_cabecalho(),
    )
    assert resposta.status_code == 200
    assert len(resposta.json()["alertas"]) == 1


def test_salvar_bdi_para_orcamento_inexistente_e_404(cliente: TestClient) -> None:
    resposta = cliente.post(
        "/orcamento/999/bdi",
        json={
            "parcelas": PARCELAS_CME,
            "municipio_iss": "Cerqueira César",
            "base_iss": "1.00",
        },
        headers=_cabecalho(),
    )
    assert resposta.status_code == 404
