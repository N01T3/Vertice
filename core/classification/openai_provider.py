"""Provedor concreto de IA, sem abstração prematura.

Porquê: ADR-006 manda classe concreta até o segundo provedor aparecer;
chave do usuário no cofre via ambiente, nunca versionada.
"""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass

NOME_VARIAVEL_CHAVE: str = "OPENAI_API_KEY"
MODELO_PADRAO: str = "gpt-4o-mini"
TEMPO_LIMITE_SEGUNDOS: int = 60
CAMPO_MENSAGENS: str = "messages"


class ErroProvedorIa(Exception):
    """Falha de rede ou resposta ilegível do provedor externo."""


def chave_configurada() -> bool:
    """Diz se há chave para decidir entre IA e modo OFFLINE."""
    return bool(os.getenv(NOME_VARIAVEL_CHAVE, "").strip())


@dataclass(frozen=True)
class ProvedorOpenai:
    """Chamada mínima ao provedor com saída JSON estrita.

    Porquê: gramática imposta na geração impede número sem origem
    antes da validação posterior, que permanece como segunda barreira.
    """

    chave: str
    modelo: str = MODELO_PADRAO

    def sugerir_texto(self, instrucao: str) -> str:
        """Envia instrução e devolve texto JSON bruto para validar depois."""
        carga = self._montar_carga(instrucao)
        return self._enviar(carga)

    def _montar_carga(self, instrucao: str) -> bytes:
        """Monta corpo da requisição com formato JSON obrigatório."""
        corpo = {
            "model": self.modelo,
            CAMPO_MENSAGENS: [{"role": "user", "content": instrucao}],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        return json.dumps(corpo).encode("utf-8")

    def _enviar(self, carga: bytes) -> str:
        """Envia via stdlib para não exigir dependência pesada."""
        endereco = "https://api.openai.com/v1/chat/completions"
        cabecalhos = {
            "Authorization": f"Bearer {self.chave}",
            "Content-Type": "application/json",
        }
        pedido = urllib.request.Request(endereco, data=carga, headers=cabecalhos)
        try:
            with urllib.request.urlopen(
                pedido, timeout=TEMPO_LIMITE_SEGUNDOS
            ) as resposta:
                bruto = resposta.read().decode("utf-8")
        except OSError as erro:
            raise ErroProvedorIa("falha de rede ao consultar provedor") from erro
        return _extrair_conteudo(bruto)


def _extrair_conteudo(bruto: str) -> str:
    """Extrai texto do modelo com erro tipado em vez de KeyError solto."""
    try:
        decodificada: object = json.loads(bruto)
    except json.JSONDecodeError as erro:
        raise ErroProvedorIa("resposta ilegível do provedor") from erro
    if not isinstance(decodificada, dict):
        raise ErroProvedorIa("envelope inesperado do provedor")
    escolhas = decodificada.get("choices")
    if not isinstance(escolhas, list) or not escolhas:
        raise ErroProvedorIa("sem escolhas na resposta")
    primeira = escolhas[0]
    if not isinstance(primeira, dict):
        raise ErroProvedorIa("escolha ilegível")
    mensagem = primeira.get("message")
    if not isinstance(mensagem, dict):
        raise ErroProvedorIa("mensagem ilegível")
    conteudo = mensagem.get("content")
    if not isinstance(conteudo, str) or not conteudo.strip():
        raise ErroProvedorIa("conteúdo vazio do provedor")
    return conteudo


def obter_provedor() -> ProvedorOpenai | None:
    """Devolve provedor com chave do ambiente ou None para OFFLINE."""
    chave = os.getenv(NOME_VARIAVEL_CHAVE, "").strip()
    if not chave:
        return None
    return ProvedorOpenai(chave=chave)
