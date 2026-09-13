"""Explosão analítica — interface pública `explodir` de arquitetura §3.

Porquê: `custo(composição) = soma de coeficiente(item) x preço(item, uf, regime)`,
recursivo, com as três armadilhas de VERTICE-modulo-sinapi.md §6: ciclo,
item sem preço na UF, e divergência de arredondamento contra o
sintético publicado — nunca escondida, sempre mostrada.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from decimal import ROUND_HALF_EVEN, Decimal
from typing import NamedTuple, cast

from core.reference_base.constants import PROFUNDIDADE_MAXIMA_EXPLOSAO, TIPO_INSUMO
from core.reference_base.literals import Regime, TipoItem
from core.reference_base.query_results import NoExplosao, ResultadoExplosao

ChaveItem = tuple[str, TipoItem]


class CicloDetectado(ValueError):
    """§6 armadilha 1: composição que referencia a si mesma pela cadeia."""


class ProfundidadeExcedida(ValueError):
    """Rede de segurança acima do que qualquer composição real usa."""


class ContextoPreco(NamedTuple):
    """UF, regime e base — o que fixa qual preço cada nó usa."""

    id_base: int
    uf: str
    regime: Regime


@dataclass
class _EstadoExplosao:
    """Caminho até a raiz — não visitados globais, para não barrar losango."""

    profundidade_maxima: int
    caminho: set[ChaveItem] = field(default_factory=set)


def explodir(
    conexao: sqlite3.Connection,
    contexto: ContextoPreco,
    codigo: str,
    tipo: TipoItem,
    profundidade_maxima: int = PROFUNDIDADE_MAXIMA_EXPLOSAO,
) -> ResultadoExplosao:
    """Explode uma composição (ou resolve um insumo) numa UF e regime."""
    estado = _EstadoExplosao(profundidade_maxima=profundidade_maxima)
    arvore = _resolver_no(conexao, contexto, estado, (codigo, tipo), Decimal(1))
    return ResultadoExplosao(
        codigo_raiz=codigo,
        uf=contexto.uf,
        regime=contexto.regime,
        custo_total_centavos=arvore.custo_total_centavos,
        completo=arvore.custo_total_centavos is not None,
        arvore=arvore,
    )


def _resolver_no(
    conexao: sqlite3.Connection,
    contexto: ContextoPreco,
    estado: _EstadoExplosao,
    chave_item: ChaveItem,
    coeficiente_acumulado: Decimal,
) -> NoExplosao:
    """Resolve um nó: insumo é folha; composição recursa nos filhos."""
    codigo, tipo = chave_item
    if len(estado.caminho) >= estado.profundidade_maxima:
        raise ProfundidadeExcedida(
            f"acima de {estado.profundidade_maxima} níveis em {codigo}"
        )
    if tipo == TIPO_INSUMO:
        return _no_folha(conexao, contexto, chave_item, coeficiente_acumulado)
    if chave_item in estado.caminho:
        raise CicloDetectado(f"composição {codigo} referencia a si mesma pela cadeia")
    return _no_composicao(conexao, contexto, estado, chave_item, coeficiente_acumulado)


def _no_folha(
    conexao: sqlite3.Connection,
    contexto: ContextoPreco,
    chave_item: ChaveItem,
    coeficiente_acumulado: Decimal,
) -> NoExplosao:
    """Insumo não tem filho — a recursão termina aqui."""
    codigo, tipo = chave_item
    descricao, unidade = _buscar_item(conexao, contexto.id_base, codigo, tipo)
    preco = _buscar_preco(conexao, contexto, codigo, tipo)
    total = _multiplicar(preco, coeficiente_acumulado)
    return NoExplosao(
        codigo=codigo,
        tipo=tipo,
        descricao=descricao,
        unidade=unidade,
        coeficiente_acumulado=str(coeficiente_acumulado),
        custo_unitario_centavos=preco,
        custo_total_centavos=total,
        filhos=[],
    )


def _no_composicao(
    conexao: sqlite3.Connection,
    contexto: ContextoPreco,
    estado: _EstadoExplosao,
    chave_item: ChaveItem,
    coeficiente_acumulado: Decimal,
) -> NoExplosao:
    """Soma os filhos; `None` em qualquer filho torna o total incompleto.

    Porquê: `custo_unitario_centavos` aqui é o preço sintético que a
    SINAPI já publica para a composição — guardado só para conferência
    contra a soma bottom-up, nunca usado na soma (§6 armadilha 3).
    """
    codigo, tipo = chave_item
    descricao, unidade = _buscar_item(conexao, contexto.id_base, codigo, tipo)
    preco_publicado = _buscar_preco(conexao, contexto, codigo, tipo)
    estado.caminho.add(chave_item)
    filhos = [
        _resolver_no(conexao, contexto, estado, (fc, ft), coeficiente_acumulado * coef)
        for fc, ft, coef in _buscar_filhos(conexao, contexto.id_base, codigo)
    ]
    estado.caminho.discard(chave_item)
    incompleto = any(f.custo_total_centavos is None for f in filhos)
    total = None if incompleto else sum(f.custo_total_centavos for f in filhos)  # type: ignore[misc]
    return NoExplosao(
        codigo=codigo,
        tipo=tipo,
        descricao=descricao,
        unidade=unidade,
        coeficiente_acumulado=str(coeficiente_acumulado),
        custo_unitario_centavos=preco_publicado,
        custo_total_centavos=total,
        filhos=filhos,
    )


def _multiplicar(centavos: int | None, coeficiente: Decimal) -> int | None:
    """Preço ausente na UF não vira zero — some, marcando o total incompleto."""
    if centavos is None:
        return None
    produto = Decimal(centavos) * coeficiente
    return int(produto.to_integral_value(rounding=ROUND_HALF_EVEN))


def _buscar_item(
    conexao: sqlite3.Connection, id_base: int, codigo: str, tipo: str
) -> tuple[str, str]:
    """Descrição e unidade do catálogo — para rotular o nó na árvore."""
    linha = conexao.execute(
        "SELECT descricao, unidade FROM item_sinapi "
        "WHERE id_base=? AND codigo=? AND tipo=?",
        (id_base, codigo, tipo),
    ).fetchone()
    if linha is None:
        raise KeyError(f"item {codigo} ({tipo}) não existe na base {id_base}")
    return linha[0], linha[1]


def _buscar_preco(
    conexao: sqlite3.Connection, contexto: ContextoPreco, codigo: str, tipo: str
) -> int | None:
    """Preço publicado do item nesta UF e regime; `None` quando ausente."""
    linha = conexao.execute(
        "SELECT valor_centavos FROM preco_sinapi "
        "WHERE id_base=? AND codigo=? AND tipo=? AND uf=? AND regime=?",
        (contexto.id_base, codigo, tipo, contexto.uf, contexto.regime),
    ).fetchone()
    return linha[0] if linha is not None else None


def _buscar_filhos(
    conexao: sqlite3.Connection, id_base: int, codigo_composicao: str
) -> list[tuple[str, TipoItem, Decimal]]:
    """Itens diretos de uma composição, com o coeficiente publicado.

    Porquê do `cast`: o `CHECK` de `composicao_item.tipo_item` já
    restringe a coluna a 'INSUMO'/'COMPOSICAO' — o esquema é a prova,
    o `cast` só repete para o verificador de tipo o que o banco garante.
    """
    linhas = conexao.execute(
        "SELECT codigo_item, tipo_item, coeficiente FROM composicao_item "
        "WHERE id_base=? AND codigo_composicao=?",
        (id_base, codigo_composicao),
    ).fetchall()
    return [
        (codigo, cast(TipoItem, tipo), Decimal(coef)) for codigo, tipo, coef in linhas
    ]
