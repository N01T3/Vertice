"""Leitura do manifesto — `carregar` da interface pública de arquitetura §3.

Porquê `yaml.safe_load`, nunca `yaml.load` puro: um manifesto de
pacote é dado que qualquer um pode escrever e distribuir. `safe_load`
não reconstrói objeto Python arbitrário a partir do YAML — é a mesma
razão de `calcular_markup` não usar `eval()` (VERTICE-plataforma.md §3.1).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from core.packages.types import BasePreco, Classificacao, ModeloMarkup, PacoteDominio

_CAMPOS_OBRIGATORIOS: tuple[str, ...] = (
    "dominio",
    "unidades",
    "classificacao",
    "bases_preco",
    "regras_medicao",
    "markup",
)


class PacoteInvalido(ValueError):
    """O manifesto não tem a forma que `VERTICE-plataforma.md` §3 exige."""


def carregar(caminho_manifesto: Path) -> PacoteDominio:
    """Lê e estrutura o manifesto de um pacote de domínio.

    Porquê não validar regra de negócio aqui: `carregar` só garante a
    forma — os campos existem e têm o tipo esperado. Se o arquivo
    referenciado existe, se a fórmula é aritmética válida, isso é
    trabalho de `validar` (`core.packages.validator`).
    """
    bruto = _ler_yaml(caminho_manifesto)
    _verificar_campos_obrigatorios(bruto, caminho_manifesto)
    return PacoteDominio(
        dominio=str(bruto["dominio"]),
        caminho_raiz=caminho_manifesto.parent,
        unidades=_lista_de_texto(bruto["unidades"], "unidades"),
        classificacao=_construir_classificacao(
            _mapa(bruto["classificacao"], "classificacao")
        ),
        bases_preco=tuple(
            _construir_base_preco(_mapa(item, "bases_preco[]"))
            for item in _lista(bruto["bases_preco"], "bases_preco")
        ),
        regras_medicao_glob=str(bruto["regras_medicao"]),
        markup=_construir_markup(_mapa(bruto["markup"], "markup")),
        custos_fora_do_markup=tuple(
            _mapa_de_texto(item, "custos_fora_do_markup[]")
            for item in _lista(
                bruto.get("custos_fora_do_markup", []), "custos_fora_do_markup"
            )
        ),
        bruto=bruto,
    )


def _ler_yaml(caminho_manifesto: Path) -> dict[str, object]:
    """Lê o arquivo e garante que a raiz do documento é um mapa."""
    with caminho_manifesto.open(encoding="utf-8") as arquivo:
        conteudo = yaml.safe_load(arquivo)
    if not isinstance(conteudo, dict):
        raise PacoteInvalido(f"{caminho_manifesto}: raiz do manifesto não é um mapa")
    return conteudo


def _verificar_campos_obrigatorios(bruto: dict[str, object], caminho: Path) -> None:
    """VERTICE-plataforma.md §3: os seis campos que todo pacote declara."""
    faltando = [campo for campo in _CAMPOS_OBRIGATORIOS if campo not in bruto]
    if faltando:
        raise PacoteInvalido(f"{caminho}: faltam campos obrigatórios {faltando}")


def _mapa(valor: object, contexto: str) -> dict[str, object]:
    """Garante que um nó do YAML é um mapa antes de indexar por chave."""
    if not isinstance(valor, dict):
        raise PacoteInvalido(
            f"{contexto}: esperava um mapa, veio {type(valor).__name__}"
        )
    return valor


def _lista(valor: object, contexto: str) -> list[object]:
    """Garante que um nó do YAML é uma lista antes de iterar."""
    if not isinstance(valor, list):
        raise PacoteInvalido(
            f"{contexto}: esperava uma lista, veio {type(valor).__name__}"
        )
    return valor


def _lista_de_texto(valor: object, contexto: str) -> tuple[str, ...]:
    """Uma lista do YAML cujos itens viram `str`, um por um."""
    return tuple(str(item) for item in _lista(valor, contexto))


def _mapa_de_texto(valor: object, contexto: str) -> dict[str, str]:
    """Um mapa do YAML cujos valores viram `str` — usado nos itens soltos."""
    return {chave: str(item) for chave, item in _mapa(valor, contexto).items()}


def _construir_classificacao(bruto: dict[str, object]) -> Classificacao:
    return Classificacao(
        padrao=str(bruto["padrao"]),
        eixos=_lista_de_texto(bruto["eixos"], "classificacao.eixos"),
        arquivo=str(bruto["arquivo"]),
    )


def _construir_base_preco(bruto: dict[str, object]) -> BasePreco:
    return BasePreco(
        adaptador=str(bruto["adaptador"]),
        rotulo=str(bruto["rotulo"]),
        oficial=bool(bruto["oficial"]),
        regimes=_lista_de_texto(bruto["regimes"], "bases_preco[].regimes"),
        granularidade_geografica=(
            str(bruto["granularidade_geografica"])
            if "granularidade_geografica" in bruto
            else None
        ),
    )


def _construir_markup(bruto: dict[str, object]) -> ModeloMarkup:
    return ModeloMarkup(
        modelo=str(bruto["modelo"]),
        parcelas=_lista_de_texto(bruto["parcelas"], "markup.parcelas"),
        tributos_sobre_faturamento=_lista_de_texto(
            bruto["tributos_sobre_faturamento"], "markup.tributos_sobre_faturamento"
        ),
        formula=str(bruto["formula"]),
        referencias_externas=_lista_de_texto(
            bruto.get("referencias_externas", []), "markup.referencias_externas"
        ),
    )
