"""Leitura e escrita de `fonte`, `orcamento` e `bdi`.

Porquê `salvar_bdi` substitui em vez de acumular histórico: até o
orçamento fechar, revisar uma parcela é normal — `id_orcamento` é
chave primária da tabela `bdi` por isso (§3.5), não por descuido.
"""

from __future__ import annotations

import sqlite3
from decimal import Decimal
from typing import cast

from core.pricing.bdi import ParcelasBdi
from core.pricing.types import Fonte, Orcamento, RegistroBdi


def inserir_fonte(conexao: sqlite3.Connection, fonte: Fonte) -> int:
    """Grava uma citação e devolve o `id` para outra tabela referenciar."""
    cursor = conexao.execute(
        """
        INSERT INTO fonte
            (tipo, nome, item, data_base, url, uso, confiabilidade, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fonte.tipo,
            fonte.nome,
            fonte.item,
            fonte.data_base,
            fonte.url,
            fonte.uso,
            fonte.confiabilidade,
            fonte.observacao,
        ),
    )
    conexao.commit()
    id_fonte = cursor.lastrowid
    assert id_fonte is not None  # PRIMARY KEY autoincrementa; nunca None aqui
    return id_fonte


def criar_orcamento(conexao: sqlite3.Connection, orcamento: Orcamento) -> int:
    """Cria a linha de `orcamento` e devolve seu `id`.

    Porquê regime, uf, id_base e data_base são obrigatórios no tipo
    (não têm padrão): `VERTICE-modulo-precificacao.md` §2.2 regra 1 —
    "regime é obrigatório na criação... sem padrão silencioso".
    """
    cursor = conexao.execute(
        """
        INSERT INTO orcamento
            (identificacao, regime, uf, id_base, data_base, criado_em, id_origem)
        VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
        """,
        (
            orcamento.identificacao,
            orcamento.regime,
            orcamento.uf,
            orcamento.id_base,
            orcamento.data_base,
            orcamento.id_origem,
        ),
    )
    conexao.commit()
    id_orcamento = cursor.lastrowid
    assert id_orcamento is not None  # PRIMARY KEY autoincrementa; nunca None aqui
    return id_orcamento


def buscar_orcamento(
    conexao: sqlite3.Connection, id_orcamento: int
) -> Orcamento | None:
    """Lê um orçamento pelo `id`; `None` se não existir."""
    linha = conexao.execute(
        "SELECT identificacao, regime, uf, id_base, data_base, id_origem "
        "FROM orcamento WHERE id = ?",
        (id_orcamento,),
    ).fetchone()
    if linha is None:
        return None
    identificacao, regime, uf, id_base, data_base, id_origem = linha
    return Orcamento(identificacao, regime, uf, id_base, data_base, id_origem)


def salvar_bdi(conexao: sqlite3.Connection, registro: RegistroBdi) -> None:
    """Grava (ou substitui) as parcelas de BDI de um orçamento."""
    campos = registro.parcelas.como_simbolos()
    conexao.execute(
        """
        INSERT OR REPLACE INTO bdi
            (id_orcamento, administracao_central, seguro_garantia, risco,
             despesas_financeiras, lucro, pis, cofins, iss, cprb,
             municipio_iss, base_iss, justificativa, id_fonte, id_origem)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            registro.id_orcamento,
            str(registro.parcelas.administracao_central),
            str(registro.parcelas.seguro_garantia),
            str(registro.parcelas.risco),
            str(registro.parcelas.despesas_financeiras),
            str(registro.parcelas.lucro),
            str(campos["PIS"]),
            str(campos["COFINS"]),
            str(campos["ISS"]),
            str(campos["CPRB"]),
            registro.municipio_iss,
            str(registro.base_iss),
            registro.justificativa,
            registro.id_fonte,
            registro.id_origem,
        ),
    )
    conexao.commit()


def carregar_bdi(conexao: sqlite3.Connection, id_orcamento: int) -> RegistroBdi | None:
    """Lê as parcelas de BDI de um orçamento; `None` se nunca foi salvo."""
    linha = conexao.execute(
        """
        SELECT administracao_central, seguro_garantia, risco, despesas_financeiras,
               lucro, pis, cofins, iss, cprb, municipio_iss, base_iss,
               justificativa, id_fonte, id_origem
        FROM bdi WHERE id_orcamento = ?
        """,
        (id_orcamento,),
    ).fetchone()
    if linha is None:
        return None
    return _registro_bdi_da_linha(id_orcamento, linha)


NUMERO_PARCELAS_BDI: int = 9  # colunas de ParcelasBdi antes de município/base_iss/etc.


def _registro_bdi_da_linha(id_orcamento: int, linha: tuple[object, ...]) -> RegistroBdi:
    """Reconstrói `RegistroBdi` a partir de uma linha crua do banco."""
    municipio, base_iss, justificativa, id_fonte, id_origem = linha[
        NUMERO_PARCELAS_BDI:
    ]
    return RegistroBdi(
        id_orcamento=id_orcamento,
        parcelas=_parcelas_da_linha(linha[:NUMERO_PARCELAS_BDI]),
        municipio_iss=str(municipio),
        base_iss=Decimal(str(base_iss)),
        id_origem=str(id_origem),
        justificativa=cast("str | None", justificativa),
        id_fonte=cast("int | None", id_fonte),
    )


def _parcelas_da_linha(valores: tuple[object, ...]) -> ParcelasBdi:
    """As nove parcelas de BDI, cada uma `TEXT` no banco virando `Decimal`.

    Porquê `str()` em cima de `object`: a coluna do SQLite é `TEXT`
    (arquitetura §5.1) — o valor já é `str` em tempo de execução;
    `str()` só repete isso para o verificador de tipo.
    """
    ac, sg, r, df, lucro, pis, cofins, iss, cprb = valores
    return ParcelasBdi(
        administracao_central=Decimal(str(ac)),
        seguro_garantia=Decimal(str(sg)),
        risco=Decimal(str(r)),
        despesas_financeiras=Decimal(str(df)),
        lucro=Decimal(str(lucro)),
        pis=Decimal(str(pis)),
        cofins=Decimal(str(cofins)),
        iss=Decimal(str(iss)),
        cprb=Decimal(str(cprb)),
    )
