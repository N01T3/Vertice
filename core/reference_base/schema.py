"""Esquema SQL do adaptador SINAPI, conforme VERTICE-modulo-sinapi.md §4.

Porquê: DDL definida uma vez, aqui — `importer.py` só a aplica.
Divergir o esquema do documento seria o mesmo erro que motivou o
`VD-15` da suíte de lint.
"""

from __future__ import annotations

import sqlite3

from core.reference_base.constants import NOME_TABELA_FTS

DDL_TABELAS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS base_referencia (
        id                  INTEGER PRIMARY KEY,
        mes_referencia      TEXT NOT NULL,
        data_emissao        TEXT NOT NULL,
        arquivo_nome        TEXT NOT NULL,
        arquivo_hash        TEXT NOT NULL,
        importado_em        TEXT NOT NULL,
        codigo_recuperado   INTEGER NOT NULL DEFAULT 0,
        metodo_recuperacao  TEXT,
        total_composicoes   INTEGER NOT NULL,
        total_insumos       INTEGER NOT NULL,
        UNIQUE (mes_referencia, arquivo_hash)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS item_sinapi (
        id_base        INTEGER NOT NULL REFERENCES base_referencia(id),
        codigo         TEXT NOT NULL,
        tipo           TEXT NOT NULL CHECK (tipo IN ('COMPOSICAO','INSUMO')),
        grupo          TEXT,
        descricao      TEXT NOT NULL,
        unidade        TEXT NOT NULL,
        situacao       TEXT,
        PRIMARY KEY (id_base, codigo, tipo)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS preco_sinapi (
        id_base        INTEGER NOT NULL,
        codigo         TEXT NOT NULL,
        tipo           TEXT NOT NULL,
        uf             TEXT NOT NULL,
        regime         TEXT NOT NULL
                       CHECK (regime IN ('ONERADO','DESONERADO','SEM_ENCARGOS')),
        valor_centavos INTEGER,
        percentual_as  TEXT,
        PRIMARY KEY (id_base, codigo, tipo, uf, regime)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS composicao_item (
        id_base           INTEGER NOT NULL,
        codigo_composicao TEXT NOT NULL,
        tipo_item         TEXT NOT NULL CHECK (tipo_item IN ('COMPOSICAO','INSUMO')),
        codigo_item       TEXT NOT NULL,
        coeficiente       TEXT NOT NULL,
        situacao          TEXT,
        PRIMARY KEY (id_base, codigo_composicao, tipo_item, codigo_item)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS manutencao_sinapi (
        id_base      INTEGER NOT NULL,
        referencia   TEXT NOT NULL,
        tipo         TEXT NOT NULL,
        codigo       TEXT NOT NULL,
        descricao    TEXT,
        manutencao   TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_manut_codigo "
    "ON manutencao_sinapi (id_base, codigo)",
    "CREATE INDEX IF NOT EXISTS idx_composicao_item_pai "
    "ON composicao_item (id_base, codigo_composicao)",
)

DDL_FTS: str = f"""
    CREATE VIRTUAL TABLE IF NOT EXISTS {NOME_TABELA_FTS} USING fts5(
        codigo, descricao, grupo, unidade, tipo, id_base UNINDEXED,
        tokenize = 'unicode61 remove_diacritics 2'
    )
"""


def criar_esquema(conexao: sqlite3.Connection) -> None:
    """Cria as tabelas e a FTS5 se ainda não existirem."""
    cursor = conexao.cursor()
    for instrucao in DDL_TABELAS:
        cursor.execute(instrucao)
    cursor.execute(DDL_FTS)
    conexao.commit()
