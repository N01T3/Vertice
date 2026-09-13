"""Triagem CAD recusa rebaixado e orienta o projetista.

Porquê: DXF R12 abre bonito mas está destruído para medição;
o laudo precisa dizer como reexportar, por camada.
"""

from __future__ import annotations

from pathlib import Path

from core.documents.cad_triage import triar_arquivo_cad

_CONTEUDO_R12 = """  0
SECTION
  2
HEADER
  9
$ACADVER
  1
AC1009
  9
$INSUNITS
 70
     4
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
TEXT
  8
0
  1
parede 10m
  0
ENDSEC
  0
EOF
"""

_CONTEUDO_R2018 = """  0
SECTION
  2
HEADER
  9
$ACADVER
  1
AC1032
  9
$INSUNITS
 70
     6
  9
$DIMSCALE
 40
1.0
  0
ENDSEC
  0
SECTION
  2
TABLES
  0
LAYER
  8
ALVENARIA
  0
LAYER
  8
REVEST
  0
ENDSEC
  0
SECTION
  2
ENTITIES
  0
LWPOLYLINE
  8
ALVENARIA
  0
DIMENSION
  8
ALVENARIA
  0
ENDSEC
  0
EOF
"""


def _gravar_dxf(caminho: Path, conteudo: str) -> Path:
    alvo = caminho / "planta.dxf"
    alvo.write_text(conteudo, encoding="utf-8")
    return alvo


def test_recusa_dxf_r12_com_codigo_e_orientacao(tmp_path: Path) -> None:
    """E-CAD-01 recusa R12 com laudo ao projetista, nunca genérico."""
    arquivo = _gravar_dxf(tmp_path, _CONTEUDO_R12)
    laudo = triar_arquivo_cad(arquivo)
    assert laudo.recusado is True
    assert laudo.aprovado_com_ressalva is False
    assert "E-CAD-01" in (laudo.codigos or [])
    texto = laudo.laudo_para_projetista.lower()
    assert "projetista" in texto
    assert "r2013" in texto
    assert "arquivo inválido" not in texto
    assert any("E-CAD-01" in pendencia for pendencia in laudo.pendencias)


def test_aprova_dxf_r2018_com_camadas(tmp_path: Path) -> None:
    """DXF nativo com camadas libera medição automática."""
    arquivo = _gravar_dxf(tmp_path, _CONTEUDO_R2018)
    laudo = triar_arquivo_cad(arquivo)
    assert laudo.recusado is False
    assert laudo.pendencias == []
    assert "projetista" in laudo.laudo_para_projetista.lower()
