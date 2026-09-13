"""instalar — carregar + validar encadeados, sem travar em alerta."""

from __future__ import annotations

from pathlib import Path

from core.packages.installer import instalar


def test_instalar_o_pacote_real_devolve_pacote_e_alertas() -> None:
    """Instalar não é tudo-ou-nada: um pacote incompleto ainda instala."""
    resultado = instalar(Path("packages/civil-construction-br/package.yaml"))
    assert resultado.pacote.dominio == "civil-construction-br"
    # A classificação NBR 15965 ainda não existe (INDICE.md §4.4) —
    # instalar não trava por isso, só relata.
    assert len(resultado.alertas) >= 1
