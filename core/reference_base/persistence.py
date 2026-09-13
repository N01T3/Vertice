"""Escrita em lote no SQLite — nunca linha a linha (§12 do documento).

Porquê: ~1,25 milhão de linhas de preço por base torna INSERT
individual uma importação de minutos virando horas. `executemany`
dentro de uma transação única é o que o documento exige.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from core.reference_base.constants import NOME_TABELA_FTS
from core.reference_base.types import (
    MetadadosArquivo,
    RegistroComposicaoItem,
    RegistroItem,
    RegistroManutencao,
    RegistroPreco,
    ResultadoRecuperacao,
)

TAMANHO_HASH_NA_MENSAGEM: int = (
    12  # prefixo suficiente para reconhecer, não o hash todo
)


class BaseJaImportada(ValueError):
    """S09: o mesmo arquivo, pelo hash, já foi importado antes."""


def inserir_base(
    conexao: sqlite3.Connection,
    metadados: MetadadosArquivo,
    recuperacao: ResultadoRecuperacao,
    total_composicoes: int,
    total_insumos: int,
) -> int:
    """Cria a linha de `base_referencia` e devolve seu `id`."""
    existente = conexao.execute(
        "SELECT id FROM base_referencia WHERE mes_referencia = ? AND arquivo_hash = ?",
        (metadados.mes_referencia, metadados.hash_sha256),
    ).fetchone()
    if existente is not None:
        prefixo = metadados.hash_sha256[:TAMANHO_HASH_NA_MENSAGEM]
        raise BaseJaImportada(
            f"base {metadados.mes_referencia} com hash {prefixo}… já foi importada"
        )
    cursor = conexao.execute(
        """
        INSERT INTO base_referencia
            (mes_referencia, data_emissao, arquivo_nome, arquivo_hash,
             importado_em, codigo_recuperado, metodo_recuperacao,
             total_composicoes, total_insumos)
        VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?, ?)
        """,
        (
            metadados.mes_referencia,
            metadados.data_emissao,
            metadados.caminho.name,
            metadados.hash_sha256,
            int(recuperacao.aconteceu),
            recuperacao.metodo,
            total_composicoes,
            total_insumos,
        ),
    )
    id_base = cursor.lastrowid
    assert id_base is not None  # PRIMARY KEY autoincrementa; nunca None aqui
    return id_base


def inserir_itens(
    conexao: sqlite3.Connection, id_base: int, itens: Iterable[RegistroItem]
) -> None:
    """Grava o catálogo — insumo ou composição, mesma tabela."""
    linhas = [
        (id_base, i.codigo, i.tipo, i.grupo, i.descricao, i.unidade, i.situacao)
        for i in itens
    ]
    conexao.executemany(
        """
        INSERT INTO item_sinapi
            (id_base, codigo, tipo, grupo, descricao, unidade, situacao)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        linhas,
    )


def inserir_precos(
    conexao: sqlite3.Connection, id_base: int, precos: Iterable[RegistroPreco]
) -> int:
    """Grava preços em lote; devolve quantas linhas foram gravadas."""
    total = 0
    lote: list[tuple[object, ...]] = []
    for preco in precos:
        lote.append(
            (
                id_base,
                preco.codigo,
                preco.tipo,
                preco.uf,
                preco.regime,
                preco.valor_centavos,
                preco.percentual_as,
            )
        )
        total += 1
    conexao.executemany(
        """
        INSERT INTO preco_sinapi
            (id_base, codigo, tipo, uf, regime, valor_centavos, percentual_as)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        lote,
    )
    return total


def inserir_composicao_itens(
    conexao: sqlite3.Connection,
    id_base: int,
    itens: Iterable[RegistroComposicaoItem],
) -> None:
    """Grava as arestas composição → item, base da explosão analítica."""
    linhas = [
        (
            id_base,
            i.codigo_composicao,
            i.tipo_item,
            i.codigo_item,
            i.coeficiente,
            i.situacao,
        )
        for i in itens
    ]
    conexao.executemany(
        """
        INSERT INTO composicao_item
            (id_base, codigo_composicao, tipo_item, codigo_item, coeficiente, situacao)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        linhas,
    )


def inserir_manutencoes(
    conexao: sqlite3.Connection,
    id_base: int,
    manutencoes: Iterable[RegistroManutencao],
) -> None:
    """Grava o histórico de manutenção — a §2.4 do documento."""
    linhas = [
        (id_base, m.referencia, m.tipo, m.codigo, m.descricao, m.manutencao)
        for m in manutencoes
    ]
    conexao.executemany(
        """
        INSERT INTO manutencao_sinapi
            (id_base, referencia, tipo, codigo, descricao, manutencao)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        linhas,
    )


def reconstruir_indice_busca(conexao: sqlite3.Connection, id_base: int) -> None:
    """Repovoa a FTS5 desta base — ela é derivada, não fonte de verdade."""
    conexao.execute(f"DELETE FROM {NOME_TABELA_FTS} WHERE id_base = ?", (id_base,))
    conexao.execute(
        f"""
        INSERT INTO {NOME_TABELA_FTS} (codigo, descricao, grupo, unidade, tipo, id_base)
        SELECT codigo, descricao, grupo, unidade, tipo, id_base
        FROM item_sinapi WHERE id_base = ?
        """,
        (id_base,),
    )
