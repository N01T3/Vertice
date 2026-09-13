"""Extração de documentos com IA como leitora e RT como decisor.

Porquê: único ponto com chamada de rede por VD-05; valida sigilo antes,
degrada para OFFLINE sem chave e nunca inventa número.
"""

from __future__ import annotations

import json

from core.classification.openai_provider import ErroProvedorIa, obter_provedor
from core.documents.ai_extractor import (
    extrair_exigencias_offline,
    extrair_servicos_offline,
    montar_prompt_exigencias,
    montar_prompt_servicos,
    validar_exigencias,
    validar_servicos,
)
from core.documents.confidentiality_filter import validar_trechos_para_ia
from core.documents.types import ExigenciaNormativa, ServicoDetectado, TrechoExtraido


def extrair_exigencias(trechos: list[TrechoExtraido]) -> list[ExigenciaNormativa]:
    """Extrai exigências via IA quando há chave, senão por regras locais."""
    validar_trechos_para_ia(trechos)
    provedor = obter_provedor()
    if provedor is None:
        return extrair_exigencias_offline(trechos)
    instrucao = montar_prompt_exigencias(trechos)
    try:
        bruto = provedor.sugerir_texto(instrucao)
        carga: object = json.loads(bruto)
    except (json.JSONDecodeError, ErroProvedorIa):
        return extrair_exigencias_offline(trechos)
    return validar_exigencias(carga, trechos)


def extrair_servicos(trechos: list[TrechoExtraido]) -> list[ServicoDetectado]:
    """Extrai serviços via IA quando há chave, senão por regras locais."""
    validar_trechos_para_ia(trechos)
    provedor = obter_provedor()
    if provedor is None:
        return extrair_servicos_offline(trechos)
    instrucao = montar_prompt_servicos(trechos)
    try:
        bruto = provedor.sugerir_texto(instrucao)
        carga: object = json.loads(bruto)
    except (json.JSONDecodeError, ErroProvedorIa):
        return extrair_servicos_offline(trechos)
    return validar_servicos(carga, trechos)
