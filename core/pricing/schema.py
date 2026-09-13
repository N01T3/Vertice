"""Esquema SQL de precificação: `orcamento`, `bdi`, `fonte`.

Porquê `fonte` mora aqui, não em `reference_base`: é citação
compartilhada — `VERTICE-modulo-cpu.md` também a referencia
(`cpu_componente.id_fonte`) — mas `pricing` é o primeiro módulo a
precisar dela de verdade. `IF NOT EXISTS` deixa o segundo módulo que
precisar chamar `criar_esquema` sem conflito.
"""

from __future__ import annotations

import sqlite3

DDL_TABELAS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS fonte (
        id              INTEGER PRIMARY KEY,
        tipo            TEXT NOT NULL,
        nome            TEXT NOT NULL,
        item            TEXT NOT NULL,
        data_base       TEXT NOT NULL,
        url             TEXT,
        uso             TEXT,
        confiabilidade  TEXT NOT NULL CHECK (confiabilidade IN
                            ('PRIMARIA','PUBLICA','PUBLICA_REGIONAL','COMERCIAL','FABRICANTE')),
        observacao      TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS orcamento (
        id              INTEGER PRIMARY KEY,
        identificacao   TEXT NOT NULL,
        regime          TEXT NOT NULL
                        CHECK (regime IN ('ONERADO','DESONERADO','SEM_ENCARGOS')),
        uf              TEXT NOT NULL,
        id_base         INTEGER NOT NULL REFERENCES base_referencia(id),
        data_base       TEXT NOT NULL,
        criado_em       TEXT NOT NULL,
        id_origem       TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS bdi (
        id_orcamento          INTEGER PRIMARY KEY REFERENCES orcamento(id),
        administracao_central TEXT NOT NULL,
        seguro_garantia       TEXT NOT NULL,
        risco                 TEXT NOT NULL,
        despesas_financeiras  TEXT NOT NULL,
        lucro                 TEXT NOT NULL,
        pis                   TEXT NOT NULL,
        cofins                TEXT NOT NULL,
        iss                   TEXT NOT NULL,
        cprb                  TEXT NOT NULL,
        municipio_iss         TEXT NOT NULL,
        base_iss              TEXT NOT NULL,
        justificativa         TEXT,
        id_fonte              INTEGER REFERENCES fonte(id),
        id_origem             TEXT NOT NULL
    )
    """,
)


def criar_esquema(conexao: sqlite3.Connection) -> None:
    """Cria `fonte`, `orcamento` e `bdi` se ainda não existirem.

    Porquê `orcamento.id_base` referencia `base_referencia`: um
    orçamento sempre aponta para uma base específica, e nunca troca
    de preço sozinho quando uma nova é importada (`VERTICE-arquitetura.md`
    §5). Rodar isto sem antes ter chamado
    `core.reference_base.schema.criar_esquema` deixa a referência
    solta — SQLite não impõe a chave estrangeira por padrão, mas o
    dado deixa de fazer sentido.
    """
    cursor = conexao.cursor()
    for instrucao in DDL_TABELAS:
        cursor.execute(instrucao)
    conexao.commit()
