"""Leitores extraem texto com origem para a IA citar.

Porquê: sem trecho com página ou aba, exigência e serviço são
opinião do modelo e caem no portão 7.
"""

from __future__ import annotations

from pathlib import Path

from core.documents.readers import (
    calcular_hash,
    criar_documento,
    detectar_tipo,
    extrair_texto_csv,
    extrair_texto_txt,
    extrair_texto_xlsx,
)


def test_hash_e_tipo_txt(tmp_path: Path) -> None:
    """Hash rastreia o arquivo e tipo sugere memorial descritivo."""
    arquivo = tmp_path / "memorial.txt"
    arquivo.write_text("Alvenaria de vedação conforme NBR 15965.", encoding="utf-8")
    resumo = calcular_hash(arquivo)
    assert len(resumo) == 64
    assert detectar_tipo(arquivo) == "MEMORIAL_DESCRITIVO"
    documento = criar_documento(arquivo)
    assert documento.hash_sha256 == resumo
    assert documento.tamanho_bytes > 0


def test_texto_extraido_de_csv(tmp_path: Path) -> None:
    """CSV vira trechos endereçáveis por linha."""
    arquivo = tmp_path / "atividades.csv"
    arquivo.write_text(
        "servico;quantidade;unidade\npintura parede;120;m2\n", encoding="utf-8"
    )
    trechos = extrair_texto_csv(arquivo)
    assert len(trechos) >= 2
    juntos = " ".join(trecho.texto for trecho in trechos)
    assert "pintura" in juntos.lower()
    assert all(trecho.pagina_ou_aba for trecho in trechos)


def test_texto_extraido_de_xlsx(tmp_path: Path) -> None:
    """XLSX vira trechos por aba, com biblioteca ou XML puro."""
    arquivo = tmp_path / "memorial.xlsx"
    _gravar_xlsx_minimo(arquivo)
    trechos = extrair_texto_xlsx(arquivo)
    assert len(trechos) >= 1
    juntos = " ".join(trecho.texto for trecho in trechos)
    assert "alvenaria" in juntos.lower()
    assert all(trecho.pagina_ou_aba and trecho.origem for trecho in trechos)


def test_texto_extraido_de_txt(tmp_path: Path) -> None:
    """TXT preserva conteúdo para citação literal."""
    arquivo = tmp_path / "nota.txt"
    arquivo.write_text("Revestimento com chapisco e emboço.", encoding="utf-8")
    trechos = extrair_texto_txt(arquivo)
    assert len(trechos) == 1
    assert "chapisco" in trechos[0].texto.lower()


def _gravar_xlsx_minimo(arquivo: Path) -> None:
    """Grava XLSX mínimo via openpyxl para o teste ler de volta."""
    import openpyxl as pacote_planilha

    pasta = pacote_planilha.Workbook()
    aba = pasta.active
    assert aba is not None
    aba.title = "Atividades"
    aba["A1"] = "servico"
    aba["B1"] = "detalhe"
    aba["A2"] = "alvenaria de vedação"
    aba["B2"] = "12,5 m2 conforme projeto"
    pasta.save(str(arquivo))
    pasta.close()
