"""Helpers de leitura sem índice fixo — a garantia de VD-01/§2.1.

Porquê: se `normalizar` ou `valor_para_centavos` quebrarem, todo
importador quebra em silêncio; são a fronteira mais barata de testar.
"""

from __future__ import annotations

from core.reference_base.adapters.sinapi.spreadsheet import (
    localizar_linha_cabecalho,
    mapa_ufs_por_coluna_unica,
    mapa_ufs_por_par_de_colunas,
    normalizar,
    valor_para_centavos,
    valor_para_texto_decimal,
)


def test_normalizar_ignora_acento_e_caixa() -> None:
    """'Código', 'codigo' e 'CÓDIGO' são o mesmo rótulo."""
    assert normalizar("Código") == normalizar("codigo") == normalizar("CÓDIGO")


def test_localizar_cabecalho_nao_depende_da_posicao() -> None:
    """Âncora de §2.1: a linha do cabeçalho é achada pelo conteúdo, não pela posição."""
    linhas = [("lixo",), ("mais lixo", "x"), ("Grupo", "Código")]
    assert localizar_linha_cabecalho(linhas, "grupo") == 2


def test_mapa_ufs_por_coluna_unica_ignora_colunas_nao_uf() -> None:
    """Layout de insumo: uma coluna por UF, o resto é ignorado."""
    cabecalho = (
        "Classificação",
        "Código",
        "Descrição",
        "Unidade",
        "Origem",
        "AC",
        "SP",
    )
    mapa = mapa_ufs_por_coluna_unica(cabecalho, {"AC", "SP"})
    assert mapa == {5: "AC", 6: "SP"}


def test_mapa_ufs_por_par_de_colunas_segue_a_sigla_mesclada() -> None:
    """Layout de composição: a sigla só aparece na primeira das duas colunas."""
    linha_siglas = (None, None, None, None, "AC", None, "SP", None)
    mapa = mapa_ufs_por_par_de_colunas(linha_siglas, {"AC", "SP"})
    assert mapa == {"AC": (4, 5), "SP": (6, 7)}


def test_valor_para_centavos_arredonda_meio_par() -> None:
    """Decimal exato, arredondamento bancário — nunca o float ingênuo."""
    assert valor_para_centavos(40.63) == 4063
    assert valor_para_centavos(None) is None
    assert valor_para_centavos("") is None


def test_valor_para_centavos_trata_zero_como_ausencia() -> None:
    """§2 nota da própria aba: custo zerado é ausência, não preço real."""
    assert valor_para_centavos(0) is None
    assert valor_para_centavos("-") is None


def test_valor_para_texto_decimal_preserva_o_literal_da_fonte() -> None:
    """O texto gravado é o menor decimal que reproduz o float da fonte.

    Porquê: coeficiente real do pacote (`0.9464285`) não pode virar
    `0.9464284999999999...` nem qualquer arredondamento arbitrário —
    conferido contra amostra do arquivo real na revisão de 13/09/2026.
    """
    assert valor_para_texto_decimal(0.9464285) == "0.9464285"
    assert valor_para_texto_decimal(None) is None
