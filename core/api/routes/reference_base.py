"""Rotas de `reference_base` — os dois contratos travados por REGRAS §4.4.

Porquê exatamente estas duas assinaturas: `VERTICE-REGRAS.md` §4.4 as
declara invioláveis a partir da F1. Mudar path ou parâmetro aqui sem
versionamento explícito é o tipo de regressão que essa regra existe
para impedir.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from core.api.schemas import ExplosaoResposta, ItemBuscaResposta
from core.reference_base.explosion import ContextoPreco, explodir
from core.reference_base.literals import Regime, TipoItem
from core.reference_base.search import LIMITE_PADRAO, buscar

roteador = APIRouter(prefix="/sinapi", tags=["sinapi"])


def obter_conexao(requisicao: Request) -> Iterator[sqlite3.Connection]:
    """Abre uma conexão por requisição — SQLite não promete thread segura.

    Porquê por requisição, não uma conexão global: o servidor roda
    handler síncrono numa pool de threads: uma conexão compartilhada
    entre threads é exatamente o caso que `sqlite3` não garante seguro.
    """
    conexao = sqlite3.connect(requisicao.app.state.caminho_banco)
    try:
        yield conexao
    finally:
        conexao.close()


def resolver_id_base(conexao: sqlite3.Connection, id_base: int | None) -> int:
    """Sem `id_base` explícito, usa a base importada mais recente.

    Porquê: a maioria das telas quer "a base atual", não pedir ao
    usuário para saber o número interno de uma linha do banco.
    """
    if id_base is not None:
        return id_base
    linha = conexao.execute("SELECT MAX(id) FROM base_referencia").fetchone()
    if linha is None or linha[0] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="nenhuma base importada ainda",
        )
    return int(linha[0])


@roteador.get("/buscar", response_model=list[ItemBuscaResposta])
def rota_buscar(
    termo: str,
    id_base: int | None = None,
    limite: int = LIMITE_PADRAO,
    conexao: sqlite3.Connection = Depends(obter_conexao),
) -> list[ItemBuscaResposta]:
    """`GET /sinapi/buscar` — busca textual no catálogo importado."""
    base = resolver_id_base(conexao, id_base)
    resultados = buscar(conexao, termo, id_base=base, limite=limite)
    return [ItemBuscaResposta.de_dominio(item) for item in resultados]


class ParametrosExplosao(BaseModel):
    """Os parâmetros de consulta de `/composicao/{codigo}/explodir`.

    Porquê um modelo, não quatro parâmetros soltos na rota: VD-13 bane
    função com mais de cinco parâmetros — o path `codigo` mais quatro
    parâmetros de consulta já eram seis. FastAPI expande cada campo
    num parâmetro de URL igual, então o contrato de §4.4 não muda.
    """

    uf: str
    regime: Regime
    id_base: int | None = None
    tipo: TipoItem = "COMPOSICAO"


@roteador.get("/composicao/{codigo}/explodir", response_model=ExplosaoResposta)
def rota_explodir(
    codigo: str,
    parametros: ParametrosExplosao = Depends(),
    conexao: sqlite3.Connection = Depends(obter_conexao),
) -> ExplosaoResposta:
    """`GET /sinapi/composicao/{codigo}/explodir` — soma custo, com a árvore."""
    base = resolver_id_base(conexao, parametros.id_base)
    contexto = ContextoPreco(
        id_base=base, uf=parametros.uf.upper(), regime=parametros.regime
    )
    try:
        resultado = explodir(conexao, contexto, codigo, parametros.tipo)
    except KeyError as erro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(erro)
        ) from erro
    except ValueError as erro:
        # CicloDetectado ou ProfundidadeExcedida: a base tem um problema
        # de topologia, não a requisição — 422 diz "seu pedido é válido,
        # o dado é que não fecha".
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        ) from erro
    return ExplosaoResposta.de_dominio(resultado)
