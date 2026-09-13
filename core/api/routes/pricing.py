"""Rotas de orçamento e BDI — VERTICE-modulo-precificacao.md §3.

Porquê separadas de `reference_base`: não são os dois contratos que
`VERTICE-REGRAS.md` §4.4 trava a partir de F1 — podem evoluir sem esse freio.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status

from core.api.routes.reference_base import obter_conexao, resolver_id_base
from core.api.schemas import (
    BdiRequisicao,
    BdiResposta,
    OrcamentoRequisicao,
    OrcamentoResposta,
)
from core.pricing.bdi import (
    calcular_bdi,
    classificar_faixa_tcu,
    exige_justificativa,
    verificar_coerencia_de_regime,
)
from core.pricing.persistence import (
    buscar_orcamento,
    carregar_bdi,
    criar_orcamento,
    salvar_bdi,
)
from core.pricing.types import Orcamento, RegistroBdi

roteador = APIRouter(prefix="/orcamento", tags=["precificacao"])


def _gerar_id_origem_sidecar() -> str:
    """`USUARIO:sidecar#<instante>` — provisório: falta identidade de usuário.

    Porquê `USUARIO`, não `CALCULO`: quem decide criar o orçamento ou
    salvar o BDI é uma pessoa operando o app, não uma derivação
    automática — arquitetura §4.1 reserva `CALCULO` para essa outra coisa.
    Sem microssegundo o instante colidiria entre chamadas na mesma
    rajada de teste; `isoformat` inclui microssegundo por padrão.
    """
    instante = datetime.now(UTC).replace(tzinfo=None).isoformat()
    return f"USUARIO:sidecar#{instante}"


def _obter_orcamento_ou_404(
    conexao: sqlite3.Connection, id_orcamento: int
) -> Orcamento:
    """Lê um orçamento ou lança 404 — as quatro rotas abaixo precisam disto."""
    orcamento = buscar_orcamento(conexao, id_orcamento)
    if orcamento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="orçamento não encontrado"
        )
    return orcamento


def _calcular_resposta_bdi(
    formula: str, orcamento: Orcamento, registro: RegistroBdi
) -> BdiResposta:
    """Recalcula o percentual e monta a resposta — nunca lê o valor guardado."""
    bdi = calcular_bdi(formula, registro.parcelas)
    alertas = verificar_coerencia_de_regime(orcamento.regime, registro.parcelas)
    return BdiResposta.de_dominio(
        registro, bdi, classificar_faixa_tcu(bdi), exige_justificativa(bdi), alertas
    )


@roteador.post(
    "", response_model=OrcamentoResposta, status_code=status.HTTP_201_CREATED
)
def rota_criar_orcamento(
    requisicao: OrcamentoRequisicao,
    conexao: sqlite3.Connection = Depends(obter_conexao),
) -> OrcamentoResposta:
    """`POST /orcamento` — cadastra regime, base e UF (imutáveis após, §2.2)."""
    orcamento = Orcamento(
        identificacao=requisicao.identificacao,
        regime=requisicao.regime,
        uf=requisicao.uf.upper(),
        id_base=resolver_id_base(conexao, requisicao.id_base),
        data_base=requisicao.data_base,
        id_origem=_gerar_id_origem_sidecar(),
    )
    id_orcamento = criar_orcamento(conexao, orcamento)
    return OrcamentoResposta.de_dominio(id_orcamento, orcamento)


@roteador.get("/{id_orcamento}", response_model=OrcamentoResposta)
def rota_obter_orcamento(
    id_orcamento: int,
    conexao: sqlite3.Connection = Depends(obter_conexao),
) -> OrcamentoResposta:
    """`GET /orcamento/{id}` — lê o orçamento cadastrado."""
    orcamento = _obter_orcamento_ou_404(conexao, id_orcamento)
    return OrcamentoResposta.de_dominio(id_orcamento, orcamento)


@roteador.post("/{id_orcamento}/bdi", response_model=BdiResposta)
def rota_salvar_bdi(
    id_orcamento: int,
    requisicao: BdiRequisicao,
    requisicao_http: Request,
    conexao: sqlite3.Connection = Depends(obter_conexao),
) -> BdiResposta:
    """`POST /orcamento/{id}/bdi` — grava as parcelas, devolve o percentual."""
    orcamento = _obter_orcamento_ou_404(conexao, id_orcamento)
    registro = RegistroBdi(
        id_orcamento=id_orcamento,
        parcelas=requisicao.parcelas.para_dominio(),
        municipio_iss=requisicao.municipio_iss,
        base_iss=Decimal(requisicao.base_iss),
        id_origem=_gerar_id_origem_sidecar(),
        justificativa=requisicao.justificativa,
        id_fonte=requisicao.id_fonte,
    )
    salvar_bdi(conexao, registro)
    formula = requisicao_http.app.state.pacote.markup.formula
    return _calcular_resposta_bdi(formula, orcamento, registro)


@roteador.get("/{id_orcamento}/bdi", response_model=BdiResposta)
def rota_obter_bdi(
    id_orcamento: int,
    requisicao_http: Request,
    conexao: sqlite3.Connection = Depends(obter_conexao),
) -> BdiResposta:
    """`GET /orcamento/{id}/bdi` — relê as parcelas, recalcula o percentual."""
    orcamento = _obter_orcamento_ou_404(conexao, id_orcamento)
    registro = carregar_bdi(conexao, id_orcamento)
    if registro is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="BDI não cadastrado para este orçamento",
        )
    formula = requisicao_http.app.state.pacote.markup.formula
    return _calcular_resposta_bdi(formula, orcamento, registro)
