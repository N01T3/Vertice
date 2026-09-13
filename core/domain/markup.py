"""Motor de markup declarativo — ADR-019 de VERTICE-decisoes.md.

Porquê: BDI soma e divide tributo de um jeito específico do Brasil;
outro domínio soma de outro jeito (VERTICE-plataforma.md §6). O
núcleo não decide a fórmula, só sabe avaliar uma com segurança, a
partir de nomes e valores que o pacote declara.
"""

from __future__ import annotations

import ast
from collections.abc import Callable
from decimal import Decimal

_OPERADORES_BINARIOS: dict[
    type[ast.operator], Callable[[Decimal, Decimal], Decimal]
] = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
}
_OPERADORES_UNARIOS: dict[type[ast.unaryop], Callable[[Decimal], Decimal]] = {
    ast.UAdd: lambda a: a,
    ast.USub: lambda a: -a,
}


class FormulaDeMarkupInvalida(ValueError):
    """A expressão declarada no pacote não é aritmética válida.

    Porquê existe: fórmula vem de arquivo de pacote — dado, não
    código (`VERTICE-plataforma.md` §3.1: "declarar fórmula como
    expressão", nunca "alterar o motor"). Sintaxe fora do permitido
    é erro do pacote, não bug do núcleo.
    """


def calcular_markup(formula: str, parcelas: dict[str, Decimal]) -> Decimal:
    """Avalia a fórmula declarada no pacote com as parcelas dadas.

    Porquê não `eval()`: `eval()` aceita qualquer expressão Python —
    import, chamada de função, o que vier. Isto só aceita aritmética
    com nome: `+`, `-`, `*`, `/`, parênteses e as parcelas do pacote.
    """
    try:
        arvore = ast.parse(formula, mode="eval")
    except SyntaxError as erro:
        raise FormulaDeMarkupInvalida(f"fórmula inválida: {formula!r}") from erro
    return _avaliar(arvore.body, parcelas)


def _avaliar(no: ast.expr, parcelas: dict[str, Decimal]) -> Decimal:
    """Percorre o nó permitido e devolve o `Decimal` resultante."""
    if isinstance(no, ast.BinOp):
        return _avaliar_binop(no, parcelas)
    if isinstance(no, ast.UnaryOp):
        return _avaliar_unaryop(no, parcelas)
    if isinstance(no, ast.Name):
        return _avaliar_nome(no, parcelas)
    if isinstance(no, ast.Constant):
        return _avaliar_constante(no)
    raise FormulaDeMarkupInvalida(f"elemento não permitido na fórmula: {ast.dump(no)}")


def _avaliar_binop(no: ast.BinOp, parcelas: dict[str, Decimal]) -> Decimal:
    operador = _OPERADORES_BINARIOS.get(type(no.op))
    if operador is None:
        raise FormulaDeMarkupInvalida(f"operador não permitido: {ast.dump(no.op)}")
    return operador(_avaliar(no.left, parcelas), _avaliar(no.right, parcelas))


def _avaliar_unaryop(no: ast.UnaryOp, parcelas: dict[str, Decimal]) -> Decimal:
    operador = _OPERADORES_UNARIOS.get(type(no.op))
    if operador is None:
        raise FormulaDeMarkupInvalida(f"operador não permitido: {ast.dump(no.op)}")
    return operador(_avaliar(no.operand, parcelas))


def _avaliar_nome(no: ast.Name, parcelas: dict[str, Decimal]) -> Decimal:
    if no.id not in parcelas:
        raise FormulaDeMarkupInvalida(f"parcela não declarada: {no.id!r}")
    return parcelas[no.id]


def _avaliar_constante(no: ast.Constant) -> Decimal:
    """Só número inteiro literal — `1`, nunca `1.5` — evita float na fórmula.

    Porquê restringir a inteiro: o próprio `ast.parse` já converteu
    um literal decimal do texto num `float` do Python antes de chegar
    aqui — não dá para recuperar o texto original sem reler a fórmula
    caractere a caractere. Restringir a inteiro elimina o float sem
    essa reconstrução; uma fórmula real que precise de fração declara
    uma parcela em vez de um literal solto.
    """
    if isinstance(no.value, bool) or not isinstance(no.value, int):
        raise FormulaDeMarkupInvalida(
            f"só número inteiro é permitido como literal: {no.value!r}"
        )
    return Decimal(no.value)
