"""carregar — a forma do manifesto, VERTICE-plataforma.md §3.

Porquê testar contra um manifesto escrito no teste, além do real:
o real (`packages/civil-construction-br/package.yaml`) prova que o
pacote de hoje carrega; um manifesto sintético prova que a rejeição
de forma errada funciona sem depender de eu nunca quebrar o real.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from core.packages.loader import PacoteInvalido, carregar

MANIFESTO_MINIMO: dict[str, object] = {
    "dominio": "teste",
    "unidades": ["m2", "un"],
    "classificacao": {"padrao": "X", "eixos": ["a"], "arquivo": "x.yaml"},
    "bases_preco": [
        {"adaptador": "x", "rotulo": "X", "oficial": True, "regimes": ["ONERADO"]}
    ],
    "regras_medicao": "rules/*.yaml",
    "markup": {
        "modelo": "m",
        "parcelas": ["a"],
        "tributos_sobre_faturamento": ["t"],
        "formula": "a+t",
    },
}


def _escrever_manifesto(tmp_path: Path, conteudo: object) -> Path:
    caminho = tmp_path / "package.yaml"
    caminho.write_text(yaml.safe_dump(conteudo), encoding="utf-8")
    return caminho


def test_carrega_manifesto_minimo_valido(tmp_path: Path) -> None:
    caminho = _escrever_manifesto(tmp_path, MANIFESTO_MINIMO)
    pacote = carregar(caminho)
    assert pacote.dominio == "teste"
    assert pacote.unidades == ("m2", "un")
    assert pacote.classificacao.padrao == "X"
    assert pacote.bases_preco[0].adaptador == "x"
    assert pacote.markup.formula == "a+t"
    assert pacote.caminho_raiz == tmp_path


def test_carrega_o_pacote_real_de_civil_construction_br() -> None:
    """O pacote que o app realmente usa — não um exemplo isolado."""
    caminho = Path("packages/civil-construction-br/package.yaml")
    pacote = carregar(caminho)
    assert pacote.dominio == "civil-construction-br"
    assert "m2" in pacote.unidades
    assert pacote.markup.modelo == "bdi-analitico-br"


def test_campo_obrigatorio_faltando_aborta(tmp_path: Path) -> None:
    manifesto = dict(MANIFESTO_MINIMO)
    del manifesto["markup"]
    caminho = _escrever_manifesto(tmp_path, manifesto)
    with pytest.raises(PacoteInvalido):
        carregar(caminho)


def test_raiz_que_nao_e_mapa_aborta(tmp_path: Path) -> None:
    caminho = _escrever_manifesto(tmp_path, ["isto", "e", "uma", "lista"])
    with pytest.raises(PacoteInvalido):
        carregar(caminho)


def test_lista_no_lugar_errado_aborta(tmp_path: Path) -> None:
    """`unidades` como mapa em vez de lista — YAML mal escrito, não crash."""
    manifesto = dict(MANIFESTO_MINIMO)
    manifesto["unidades"] = {"nao": "e uma lista"}
    caminho = _escrever_manifesto(tmp_path, manifesto)
    with pytest.raises(PacoteInvalido):
        carregar(caminho)
