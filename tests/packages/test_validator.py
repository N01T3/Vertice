"""validar — o pacote confere contra o mundo, não só contra a forma."""

from __future__ import annotations

from pathlib import Path

from core.packages.loader import carregar
from core.packages.types import BasePreco, Classificacao, ModeloMarkup, PacoteDominio
from core.packages.validator import validar


def _pacote_valido(tmp_path: Path) -> PacoteDominio:
    """Um pacote cujos arquivos referenciados existem de verdade."""
    (tmp_path / "x.yaml").write_text("chave: valor", encoding="utf-8")
    pasta_regras = tmp_path / "rules"
    pasta_regras.mkdir()
    (pasta_regras / "uma.yaml").write_text("regra: uma", encoding="utf-8")
    return PacoteDominio(
        dominio="teste",
        caminho_raiz=tmp_path,
        unidades=("m2",),
        classificacao=Classificacao(padrao="X", eixos=("a",), arquivo="x.yaml"),
        bases_preco=(BasePreco("x", "X", True, ("ONERADO",), None),),
        regras_medicao_glob="rules/*.yaml",
        markup=ModeloMarkup("m", ("a",), ("t",), "a+t", ()),
    )


def test_pacote_completo_nao_gera_alerta(tmp_path: Path) -> None:
    assert validar(_pacote_valido(tmp_path)) == []


def test_arquivo_de_classificacao_ausente_gera_alerta(tmp_path: Path) -> None:
    pacote = _pacote_valido(tmp_path)
    (tmp_path / "x.yaml").unlink()
    alertas = validar(pacote)
    assert any("classificacao.arquivo" in a for a in alertas)


def test_glob_de_regras_sem_correspondencia_gera_alerta(tmp_path: Path) -> None:
    pacote = _pacote_valido(tmp_path)
    (tmp_path / "rules" / "uma.yaml").unlink()
    alertas = validar(pacote)
    assert any("regras_medicao" in a for a in alertas)


def test_base_sem_regime_gera_alerta(tmp_path: Path) -> None:
    pacote = _pacote_valido(tmp_path)
    sem_regime = PacoteDominio(
        dominio=pacote.dominio,
        caminho_raiz=pacote.caminho_raiz,
        unidades=pacote.unidades,
        classificacao=pacote.classificacao,
        bases_preco=(BasePreco("x", "X", True, (), None),),
        regras_medicao_glob=pacote.regras_medicao_glob,
        markup=pacote.markup,
    )
    alertas = validar(sem_regime)
    assert any("sem regime declarado" in a for a in alertas)


def test_formula_com_sintaxe_invalida_gera_alerta(tmp_path: Path) -> None:
    pacote = _pacote_valido(tmp_path)
    formula_quebrada = PacoteDominio(
        dominio=pacote.dominio,
        caminho_raiz=pacote.caminho_raiz,
        unidades=pacote.unidades,
        classificacao=pacote.classificacao,
        bases_preco=pacote.bases_preco,
        regras_medicao_glob=pacote.regras_medicao_glob,
        markup=ModeloMarkup("m", ("a",), ("t",), "a + * t", ()),
    )
    alertas = validar(formula_quebrada)
    assert any("aritmética válida" in a for a in alertas)


def test_pacote_real_hoje_acusa_a_classificacao_ausente() -> None:
    """O pacote real ainda não tem a taxonomia NBR 15965 — validar o admite."""
    pacote = carregar(Path("packages/civil-construction-br/package.yaml"))
    alertas = validar(pacote)
    assert any("classificacao.arquivo" in a for a in alertas)
