"""Tipos da ingestão generalista de documentos.

Porquê: todo número carrega origem resolvível até trecho medido.
IA que não achou número devolve None em vez de inventar, e o RT decide.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Literal

TipoDocumento = Literal[
    "CAD_DXF",
    "CAD_DWG",
    "MEMORIAL_DESCRITIVO",
    "MEMORIAL_ATIVIDADES",
    "PLANILHA",
    "PDF_GENERICO",
]

ModoOperacao = Literal["IA", "OFFLINE"]


@dataclass(frozen=True)
class DocumentoEntrada:
    """Arquivo recebido com identidade para rastreabilidade.

    Porquê: sem hash e tamanho, refazer a medição dois anos depois
    é impossível; o hash entra na cadeia de proveniência.
    """

    caminho: Path
    tipo: TipoDocumento
    hash_sha256: str
    tamanho_bytes: int


@dataclass(frozen=True)
class TrechoExtraido:
    """Pedaço de texto com endereço para citação.

    Porquê: exigência ou serviço só vale se aponta para página ou aba
    exata; sem isso é opinião do modelo e cai no portão 7.
    """

    pagina_ou_aba: str
    texto: str
    origem: str


@dataclass(frozen=True)
class ExigenciaNormativa:
    """Regra ou exigência citada no documento.

    Porquê: responde "o que eu esqueci?" sem mexer em número;
    vira objeção de escopo quando o serviço falta no orçamento.
    """

    descricao: str
    fonte: str
    id_origem: str


@dataclass(frozen=True)
class ServicoDetectado:
    """Serviço lido no documento, com quantidade opcional.

    Porquê: quantidade None significa "IA não achou número";
    inventar aqui seria número mágico em documento assinado.
    """

    descricao: str
    unidade_sugerida: str
    quantidade: Decimal | None
    id_origem: str


@dataclass(frozen=True)
class LaudoTriagem:
    """Resultado da triagem CAD endereçado ao projetista.

    Porquê: laudo genérico não resolve na origem; o projetista precisa
    saber o que falta, em que camada e como reexportar.
    """

    aprovado_com_ressalva: bool
    laudo_para_projetista: str
    pendencias: list[str]
    recusado: bool = False
    codigos: list[str] | None = None

    def codigos_registrados(self) -> list[str]:
        """Devolve códigos E-CAD mesmo quando o campo opcional é None."""
        if self.codigos is None:
            return []
        return list(self.codigos)
