"""Validação de conteúdo — `validar` da interface pública de arquitetura §3.

Porquê separado de `loader.py`: carregar garante a forma — os campos
existem e têm o tipo certo. Validar garante que a forma faz sentido —
arquivo referenciado existe, glob acha alguma coisa, fórmula é
aritmética válida. Duas perguntas diferentes, dois arquivos.
"""

from __future__ import annotations

import ast

from core.packages.types import PacoteDominio


def validar(pacote: PacoteDominio) -> list[str]:
    """Confere o pacote contra o mundo — arquivos, glob, fórmula.

    Porquê devolve lista, nunca lança: um pacote incompleto ainda é
    instalável — o mesmo espírito de "nada trava" que rege o
    antagonista (ADR-012). Quem decide o que fazer com o alerta é
    quem chama `instalar`, não este módulo.
    """
    alertas: list[str] = []
    alertas.extend(_validar_unidades(pacote))
    alertas.extend(_validar_classificacao(pacote))
    alertas.extend(_validar_regras_medicao(pacote))
    alertas.extend(_validar_bases_preco(pacote))
    alertas.extend(_validar_formula_markup(pacote))
    return alertas


def _validar_unidades(pacote: PacoteDominio) -> list[str]:
    """Nenhuma unidade declarada é pacote que não mede nada."""
    if not pacote.unidades:
        return ["unidades: lista vazia — nenhuma unidade declarada"]
    return []


def _validar_classificacao(pacote: PacoteDominio) -> list[str]:
    """O arquivo de taxonomia precisa existir de verdade, não só ser citado."""
    caminho = pacote.caminho_raiz / pacote.classificacao.arquivo
    if not caminho.exists():
        return [f"classificacao.arquivo não existe: {caminho}"]
    return []


def _validar_regras_medicao(pacote: PacoteDominio) -> list[str]:
    """O glob declarado precisa achar pelo menos uma regra real."""
    encontradas = list(pacote.caminho_raiz.glob(pacote.regras_medicao_glob))
    if not encontradas:
        glob = pacote.regras_medicao_glob
        return [f"regras_medicao: nenhum arquivo casa com {glob!r}"]
    return []


def _validar_bases_preco(pacote: PacoteDominio) -> list[str]:
    """Base sem regime declarado é base que nenhum orçamento consegue usar."""
    if not pacote.bases_preco:
        return ["bases_preco: lista vazia — nenhuma base de referência declarada"]
    return [
        f"bases_preco: {base.rotulo!r} sem regime declarado"
        for base in pacote.bases_preco
        if not base.regimes
    ]


def _validar_formula_markup(pacote: PacoteDominio) -> list[str]:
    """Só confere sintaxe aritmética válida.

    Porquê não confere se cada nome da fórmula tem parcela
    correspondente: o mapeamento de sigla (`AC`) para parcela por
    extenso (`administracao_central`) não está no manifesto —
    `VERTICE-plataforma.md` §3 não declara essa convenção. Exigir a
    correspondência aqui seria inventar uma regra que o documento
    não pede, não verificar uma que ele pede.
    """
    try:
        ast.parse(pacote.markup.formula, mode="eval")
    except SyntaxError:
        return [f"markup.formula não é aritmética válida: {pacote.markup.formula!r}"]
    return []
