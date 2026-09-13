"""Triagem CAD generalista conforme VERTICE-entrega-cad §4.

Porquê: arquivo que abre bonito pode estar destruído para medição;
o laudo vai ao projetista com camada e ação, nunca "inválido" genérico.
"""

from __future__ import annotations

import re
from pathlib import Path

from core.documents.constants import (
    CODIGO_CAMADA_PADRAO,
    CODIGO_COTA_TEXTO,
    CODIGO_ESCALA,
    CODIGO_IFC_REEXPORTADO,
    CODIGO_IFC_SEM_ESPACO,
    CODIGO_IFC_SEM_QUANTIDADE,
    CODIGO_PROXY,
    CODIGO_UNIDADE_INDEFINIDA,
    CODIGO_VERSAO_ANTIGA,
    CODIGO_XREF_AUSENTE,
    LIMITE_NOMES_XREF,
    ORDEM_VERSAO_DESCONHECIDA,
    ORDEM_VERSAO_DXF,
    VERSAO_DXF_MINIMA_ACEITA,
)
from core.documents.errors import ErroLeituraDocumento
from core.documents.types import LaudoTriagem


def triar_arquivo_cad(caminho: Path) -> LaudoTriagem:
    """Triagem por faixa: DXF/DWG audita estrutura, IFC confere semântica."""
    sufixo = caminho.suffix.lower()
    if sufixo == ".dwg":
        return _triar_dwg(caminho)
    conteudo = _ler_texto_cad(caminho)
    if sufixo == ".ifc":
        return _triar_ifc(conteudo)
    return _triar_dxf(conteudo)


def _ler_texto_cad(caminho: Path) -> str:
    """Lê CAD como texto ignorando binário, pois DXF e IFC são ASCII."""
    try:
        return caminho.read_text(encoding="utf-8", errors="ignore")
    except OSError as erro:
        raise ErroLeituraDocumento(f"falha ao ler {caminho.name}") from erro


def _triar_dwg(caminho: Path) -> LaudoTriagem:
    """DWG pede conversão no app de origem, nunca rebaixamento interno."""
    del caminho
    pendencias = [
        "Converter para DXF R2013 ou superior em ASCII no aplicativo que desenhou"
        " e reenviar; conversão interna degrada a medição."
    ]
    codigos = [CODIGO_VERSAO_ANTIGA]
    texto = (
        "Prezado projetista, recebemos DWG e precisamos do DXF nativo para medir. "
        "Exporte em ASCII, versão R2013 ou superior, direto da ferramenta que "
        "desenhou, sem conversor de terceiros na cadeia. Reenvie com unidades "
        "declaradas e referências vinculadas."
    )
    return LaudoTriagem(
        aprovado_com_ressalva=True,
        laudo_para_projetista=texto,
        pendencias=pendencias,
        recusado=False,
        codigos=codigos,
    )


def _triar_dxf(conteudo: str) -> LaudoTriagem:
    """Aplica E-CAD-01 a 07 e monta laudo com ação por camada."""
    codigos: list[str] = []
    pendencias: list[str] = []
    _acumular(
        _verificar_versao_dxf(conteudo), CODIGO_VERSAO_ANTIGA, codigos, pendencias
    )
    _acumular(_verificar_proxy(conteudo), CODIGO_PROXY, codigos, pendencias)
    _acumular(
        _verificar_unidade(conteudo), CODIGO_UNIDADE_INDEFINIDA, codigos, pendencias
    )
    _acumular(_verificar_camada(conteudo), CODIGO_CAMADA_PADRAO, codigos, pendencias)
    _acumular(_verificar_xref(conteudo), CODIGO_XREF_AUSENTE, codigos, pendencias)
    _acumular(_verificar_cota(conteudo), CODIGO_COTA_TEXTO, codigos, pendencias)
    _acumular(_verificar_escala(conteudo), CODIGO_ESCALA, codigos, pendencias)
    recusado = CODIGO_VERSAO_ANTIGA in codigos
    texto = _montar_laudo_dxf(codigos, pendencias, recusado)
    ressalva = bool(pendencias) and not recusado
    return LaudoTriagem(
        aprovado_com_ressalva=ressalva,
        laudo_para_projetista=texto,
        pendencias=pendencias,
        recusado=recusado,
        codigos=codigos,
    )


def _triar_ifc(conteudo: str) -> LaudoTriagem:
    """Aplica E-CAD-08 a 10: quantidade, espaço e geração de exportação."""
    codigos: list[str] = []
    pendencias: list[str] = []
    _acumular(
        _verificar_ifc_quantidade(conteudo),
        CODIGO_IFC_SEM_QUANTIDADE,
        codigos,
        pendencias,
    )
    _acumular(
        _verificar_ifc_espaco(conteudo), CODIGO_IFC_SEM_ESPACO, codigos, pendencias
    )
    _acumular(
        _verificar_ifc_reexportado(conteudo),
        CODIGO_IFC_REEXPORTADO,
        codigos,
        pendencias,
    )
    texto = _montar_laudo_ifc(codigos, pendencias)
    return LaudoTriagem(
        aprovado_com_ressalva=bool(pendencias),
        laudo_para_projetista=texto,
        pendencias=pendencias,
        recusado=False,
        codigos=codigos,
    )


def _acumular(
    achado: str | None, codigo: str, codigos: list[str], pendencias: list[str]
) -> None:
    """Acumula pendência com código, pois nada trava sem destino."""
    if achado is not None:
        codigos.append(codigo)
        pendencias.append(f"{codigo}: {achado}")


def _verificar_versao_dxf(conteudo: str) -> str | None:
    """Recusa DXF rebaixado abaixo de R2013, que explode texto e hachura."""
    expressao = re.compile(r"\$ACADVER\s*\n\s*1\s*\n\s*(\w+)", re.IGNORECASE)
    achado = expressao.search(conteudo)
    if achado is None:
        return (
            "versão não declarada no cabeçalho; reexportar em R2013 ou superior ASCII."
        )
    versao = achado.group(1).upper().strip()
    ordem = ORDEM_VERSAO_DXF.get(versao, ORDEM_VERSAO_DESCONHECIDA)
    minima = ORDEM_VERSAO_DXF[VERSAO_DXF_MINIMA_ACEITA]
    if ordem < minima:
        return (
            f"versão {versao} abaixo de R2013; reexportar nativamente em R2013 ou "
            "superior ASCII, sem salvar como versão antiga."
        )
    return None


def _verificar_proxy(conteudo: str) -> str | None:
    """Aponta proxies de terceiros, que não são medíveis."""
    superior = conteudo.upper()
    if "ACAD_PROXY" in superior or "PROXY_ENTITY" in superior:
        return "há entidades proxy; explodir no aplicativo de origem e reexportar."
    return None


def _verificar_unidade(conteudo: str) -> str | None:
    """Exige unidade declarada antes de qualquer extração."""
    expressao = re.compile(r"\$INSUNITS\s*\n\s*\d+\s*\n\s*(\d+)", re.IGNORECASE)
    achado = expressao.search(conteudo)
    if achado is None or achado.group(1).strip() == "0":
        return "unidade indefinida no cabeçalho; declarar unidade e calibrar escala."
    return None


def _verificar_camada(conteudo: str) -> str | None:
    """Barra automático quando tudo está na camada padrão."""
    expressao = re.compile(r"\n\s*8\s*\n\s*([^\n\r]+)")
    camadas = {nome.strip() for nome in expressao.findall(conteudo) if nome.strip()}
    if not camadas or camadas == {"0"}:
        return "todas as entidades na camada 0; separar por serviço e reenviar."
    return None


def _verificar_xref(conteudo: str) -> str | None:
    """Lista referência externa não vinculada para reentrega junto."""
    if "XREF" in conteudo.upper():
        nomes = _nomes_xref(conteudo)
        detalhe = ", ".join(nomes) if nomes else "referência externa"
        return f"vincular e inserir {detalhe} ou enviar o arquivo junto."
    return None


def _verificar_cota(conteudo: str) -> str | None:
    """Avisa quando cota é texto solto e trava validação de escala."""
    superior = conteudo.upper()
    if "DIMENSION" not in superior and "TEXT" in superior:
        return "cotas como texto solto; usar entidade de cota para validar escala."
    return None


def _verificar_escala(conteudo: str) -> str | None:
    """Exige fator visível quando o modelo não está 1:1."""
    expressao = re.compile(r"\$DIMSCALE\s*\n\s*\d+\s*\n\s*([^\n\r]+)", re.IGNORECASE)
    achado = expressao.search(conteudo)
    if achado is not None:
        fator = achado.group(1).strip()
        if fator not in ("1", "1.0", "1,0"):
            return f"escala {fator} no modelo; declarar fator visível permanente."
    return None


def _verificar_ifc_quantidade(conteudo: str) -> str | None:
    """Sem quantidade base, cai para extração geométrica com aviso."""
    if "IFCELEMENTQUANTITY" not in conteudo.upper():
        return "sem quantidades base; extração será geométrica, com aviso."
    return None


def _verificar_ifc_espaco(conteudo: str) -> str | None:
    """Sem espaço modelado, ambiente sai por grafo planar com aviso."""
    if "IFCSPACE" not in conteudo.upper():
        return "sem espaços modelados; ambiente por grafo planar, com aviso."
    return None


def _verificar_ifc_reexportado(conteudo: str) -> str | None:
    """Avisa segunda geração de perda quando IFC nasceu de outro IFC."""
    inferior = conteudo.lower()
    ferramentas = ["revit", "archicad", "tekla", "autocad", "ifcconvert"]
    citadas = [nome for nome in ferramentas if nome in inferior]
    if "reexport" in inferior or len(citadas) > 1:
        return "indício de reexportação; exportar direto da ferramenta autora."
    return None


def _nomes_xref(conteudo: str) -> list[str]:
    """Extrai nomes de blocos externos para o projetista localizar."""
    expressao = re.compile(r"XREF[^\n\r]{0,80}", re.IGNORECASE)
    achados = [parte.strip() for parte in expressao.findall(conteudo)]
    return achados[:LIMITE_NOMES_XREF]


def _montar_laudo_dxf(codigos: list[str], pendencias: list[str], recusado: bool) -> str:
    """Redige pedido ao projetista com o que falta e como reexportar."""
    if recusado:
        base = (
            "Prezado projetista, o DXF chegou rebaixado e não permite medição "
            "confiável: texto e hachura explodem e a curva carrega erro. "
            "Reexporte nativamente em R2013 ou superior, ASCII, direto da "
            "ferramenta que desenhou. "
        )
        return base + _detalhar_pendencias(pendencias)
    if not pendencias:
        return (
            "Prezado projetista, arquivo em ordem para medição automática. "
            "Mantida a versão R2013 ou superior, com camadas e unidades."
        )
    del codigos
    base = (
        "Prezado projetista, dá para medir com ressalva por camada. "
        "Para liberar o automático, ajuste: "
    )
    return base + _detalhar_pendencias(pendencias)


def _montar_laudo_ifc(codigos: list[str], pendencias: list[str]) -> str:
    """Redige pedido BIM com quantidade, espaço e exportação nativa."""
    del codigos
    if not pendencias:
        return (
            "Prezado projetista, IFC em ordem: quantidades base, espaços e "
            "exportação nativa presentes. Segue para medição automática."
        )
    base = "Prezado projetista, o IFC mede com aviso nos pontos: "
    return base + _detalhar_pendencias(pendencias)


def _detalhar_pendencias(pendencias: list[str]) -> str:
    """Junta pendências em frase encaminhável, sem jargão de software."""
    return " ".join(pendencia.strip() for pendencia in pendencias if pendencia.strip())
