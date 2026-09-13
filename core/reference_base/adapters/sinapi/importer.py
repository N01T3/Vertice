"""Orquestra a importação do pacote SINAPI — leitura, validação, gravação.

Porquê: é o único lugar que decide a ordem — ler antes de validar,
validar antes de gravar, gravar tudo numa transação. Espalhar essa
ordem pelos módulos de leitura tornaria a sequência implícita.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import cast

import openpyxl

from core.reference_base.adapters.sinapi.analytical_reader import (
    ResultadoAnalitico,
    ler_analitico,
)
from core.reference_base.adapters.sinapi.labor_reader import (
    ler_chave_por_codigo,
)
from core.reference_base.adapters.sinapi.maintenance_reader import ler_manutencoes
from core.reference_base.adapters.sinapi.metadata import ler_metadados
from core.reference_base.adapters.sinapi.price_reader import (
    codigos_brutos_da_aba,
    ler_insumos_onerados,
    ler_precos_composicao,
    ler_precos_insumo,
)
from core.reference_base.adapters.sinapi.validation import (
    coluna_de_codigo_esta_corrompida,
    conferir_recuperacao_cruzada,
    verificar_referencias_cruzadas,
)
from core.reference_base.constants import (
    ABA_COMPOSICAO_POR_REGIME,
    ABA_INSUMO_POR_REGIME,
    REGIME_ONERADO,
)
from core.reference_base.literals import Regime
from core.reference_base.persistence import (
    inserir_base,
    inserir_composicao_itens,
    inserir_itens,
    inserir_manutencoes,
    inserir_precos,
    reconstruir_indice_busca,
)
from core.reference_base.schema import criar_esquema
from core.reference_base.types import (
    MetadadosArquivo,
    RegistroItem,
    RegistroPreco,
    ResultadoImportacao,
    ResultadoRecuperacao,
)

TAMANHO_BLOCO_HASH: int = (
    1 << 20
)  # 1 MiB por leitura, arquivo cabe em memória aos poucos


@dataclass
class _Preparo:
    """O que a leitura e a validação decidem, antes de tocar no banco."""

    metadados: MetadadosArquivo
    recuperacao: ResultadoRecuperacao
    catalogo_insumos: dict[str, RegistroItem]
    precos_insumo_onerado: list[RegistroPreco]
    resultado_analitico: ResultadoAnalitico
    alertas: list[str]


def importar_pacote(
    caminho_referencia: Path,
    caminho_mao_de_obra: Path,
    caminho_manutencoes: Path,
    conexao: sqlite3.Connection,
) -> ResultadoImportacao:
    """Lê os três arquivos do pacote mensal e grava uma base completa.

    Porquê abrir `caminho_referencia` uma única vez aqui: é o arquivo
    grande do pacote (§2.1), lido por seis leitores diferentes. Nove
    aberturas separadas mediram ~487 s no pacote real de 08/2026 —
    reabrir o mesmo `.xlsx` de 13 MB era o gargalo, não a leitura.
    """
    inicio = time.monotonic()
    livro = openpyxl.load_workbook(caminho_referencia, read_only=True, data_only=True)
    try:
        preparo = _preparar_importacao(
            livro, caminho_referencia, caminho_mao_de_obra, caminho_manutencoes
        )
        id_base, total_precos = _gravar_importacao(
            conexao, preparo, livro, caminho_manutencoes
        )
    finally:
        livro.close()
    catalogo_composicoes = preparo.resultado_analitico.catalogo_composicoes
    return ResultadoImportacao(
        id_base=id_base,
        total_composicoes=len(catalogo_composicoes),
        total_insumos=len(preparo.catalogo_insumos),
        total_precos=total_precos,
        recuperacao=preparo.recuperacao,
        tempo_segundos=Decimal(str(time.monotonic() - inicio)),
        alertas=preparo.alertas,
    )


def _preparar_importacao(
    livro: openpyxl.Workbook,
    caminho_referencia: Path,
    caminho_mao_de_obra: Path,
    caminho_manutencoes: Path,
) -> _Preparo:
    """Lê e valida — nada aqui escreve no banco."""
    resultado_analitico = ler_analitico(livro)
    metadados = _identificar_pacote(
        livro, caminho_referencia, caminho_mao_de_obra, caminho_manutencoes
    )
    recuperacao = _resolver_recuperacao(livro, caminho_mao_de_obra, resultado_analitico)
    catalogo_insumos, precos_insumo_onerado = _ler_insumos(livro, resultado_analitico)
    alertas = verificar_referencias_cruzadas(
        resultado_analitico.itens,
        catalogo_insumos,
        resultado_analitico.catalogo_composicoes,
    )
    return _Preparo(
        metadados,
        recuperacao,
        catalogo_insumos,
        precos_insumo_onerado,
        resultado_analitico,
        alertas,
    )


def _gravar_importacao(
    conexao: sqlite3.Connection,
    preparo: _Preparo,
    livro: openpyxl.Workbook,
    caminho_manutencoes: Path,
) -> tuple[int, int]:
    """Cria o esquema e grava tudo numa única transação (§12 do documento)."""
    criar_esquema(conexao)
    catalogo_composicoes = preparo.resultado_analitico.catalogo_composicoes
    id_base = inserir_base(
        conexao,
        preparo.metadados,
        preparo.recuperacao,
        len(catalogo_composicoes),
        len(preparo.catalogo_insumos),
    )
    inserir_itens(conexao, id_base, preparo.catalogo_insumos.values())
    inserir_itens(conexao, id_base, catalogo_composicoes.values())
    inserir_composicao_itens(conexao, id_base, preparo.resultado_analitico.itens)
    inserir_manutencoes(conexao, id_base, ler_manutencoes(caminho_manutencoes))
    total_precos = _inserir_todos_os_precos(
        conexao,
        id_base,
        livro,
        preparo.precos_insumo_onerado,
        preparo.resultado_analitico.recuperacao_por_chave,
    )
    reconstruir_indice_busca(conexao, id_base)
    conexao.commit()
    return id_base, total_precos


def _identificar_pacote(
    livro: openpyxl.Workbook,
    caminho_referencia: Path,
    caminho_mao_de_obra: Path,
    caminho_manutencoes: Path,
) -> MetadadosArquivo:
    """V2: mês e emissão do próprio arquivo; hash do pacote inteiro.

    Porquê: S11 exige identificar pelo cabeçalho, não pelo nome do
    arquivo — por isso a leitura do mês vem daqui, não do nome do `.xlsx`.
    O hash, ao contrário, precisa do caminho: é lido em bytes crus,
    não pela planilha já aberta.
    """
    aba_ancora = ABA_INSUMO_POR_REGIME[REGIME_ONERADO]
    mes_referencia, data_emissao = ler_metadados(livro, aba_ancora)
    hash_pacote = _hash_de_arquivos(
        [caminho_referencia, caminho_mao_de_obra, caminho_manutencoes]
    )
    return MetadadosArquivo(
        caminho=caminho_referencia,
        hash_sha256=hash_pacote,
        mes_referencia=mes_referencia,
        data_emissao=data_emissao,
    )


def _hash_de_arquivos(caminhos: list[Path]) -> str:
    """SHA-256 combinado dos arquivos do pacote, ordem irrelevante.

    Porquê: provar qual pacote gerou o orçamento exige o conjunto —
    hashear só a Referência deixaria manutenção e mão de obra fora
    da prova de proveniência.
    """
    digestos = sorted(_hash_de_um_arquivo(c) for c in caminhos)
    combinado = hashlib.sha256("".join(digestos).encode("ascii"))
    return combinado.hexdigest()


def _hash_de_um_arquivo(caminho: Path) -> str:
    """SHA-256 de um arquivo, lido em blocos para não estourar memória."""
    sha = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(TAMANHO_BLOCO_HASH), b""):
            sha.update(bloco)
    return sha.hexdigest()


def _resolver_recuperacao(
    livro: openpyxl.Workbook,
    caminho_mao_de_obra: Path,
    resultado_analitico: ResultadoAnalitico,
) -> ResultadoRecuperacao:
    """V3: detecta corrupção na coluna de código e, se preciso, recupera."""
    aba = ABA_COMPOSICAO_POR_REGIME[REGIME_ONERADO]
    brutos = codigos_brutos_da_aba(livro, aba)
    if not coluna_de_codigo_esta_corrompida(brutos):
        return ResultadoRecuperacao(aconteceu=False, metodo=None, itens_recuperados=0)
    mapa_mao_de_obra = ler_chave_por_codigo(caminho_mao_de_obra)
    conferir_recuperacao_cruzada(
        resultado_analitico.recuperacao_por_chave, mapa_mao_de_obra
    )
    return ResultadoRecuperacao(
        aconteceu=True,
        metodo="ANALITICO",
        itens_recuperados=len(resultado_analitico.recuperacao_por_chave),
    )


def _ler_insumos(
    livro: openpyxl.Workbook, resultado_analitico: ResultadoAnalitico
) -> tuple[dict[str, RegistroItem], list[RegistroPreco]]:
    """Catálogo de insumo e preço onerado, de uma única leitura de ISD.

    Porquê o catálogo ainda passa por aqui, não só pelo `price_reader`:
    o Analítico cobre o insumo `SEM PREÇO` que ISD nunca lista — sem
    o reforço, V6 confunde item real e sem preço com item órfão.
    """
    aba = ABA_INSUMO_POR_REGIME[REGIME_ONERADO]
    catalogo, precos = ler_insumos_onerados(
        livro, aba, resultado_analitico.situacao_por_insumo
    )
    mapa = {item.codigo: item for item in catalogo}
    for codigo, reserva in resultado_analitico.catalogo_insumos_de_reserva.items():
        mapa.setdefault(codigo, reserva)
    return mapa, precos


def _inserir_todos_os_precos(
    conexao: sqlite3.Connection,
    id_base: int,
    livro: openpyxl.Workbook,
    precos_insumo_onerado: list[RegistroPreco],
    recuperacao_por_chave: dict[tuple[str, str], str],
) -> int:
    """Grava preço de insumo e de composição, nos três regimes.

    Porquê ONERADO não entra no laço de insumo: já foi lido junto do
    catálogo em `_ler_insumos` — reler ISD aqui desfaria a fusão.

    Porquê do `cast`: as chaves de `ABA_*_POR_REGIME` são os três
    literais de `Regime` por construção (`constants.py`) — o dicionário
    é só tipado `str` para não fazer `constantes` importar `tipos`.
    """
    total = inserir_precos(conexao, id_base, precos_insumo_onerado)
    for regime, aba_insumo in ABA_INSUMO_POR_REGIME.items():
        if regime == REGIME_ONERADO:
            continue
        precos = ler_precos_insumo(livro, aba_insumo, cast(Regime, regime))
        total += inserir_precos(conexao, id_base, precos)
    for regime, aba_composicao in ABA_COMPOSICAO_POR_REGIME.items():
        precos = ler_precos_composicao(
            livro, aba_composicao, cast(Regime, regime), recuperacao_por_chave
        )
        total += inserir_precos(conexao, id_base, precos)
    return total
