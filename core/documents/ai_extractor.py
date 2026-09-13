"""Prompts, validação e queda offline da leitura por IA.

Porquê: documents/ monta o pedido e confere a resposta, mas nunca
chama rede; a chamada mora em classification/ por VD-05. Sem número
sem trecho, sem exceção.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from core.documents.constants import (
    GRUPO_NUMERO_QUANTIDADE,
    GRUPO_UNIDADE_QUANTIDADE,
    LIMITE_DESCRICAO_OFFLINE,
    LIMITE_MINIMO_FRASE,
    LIMITE_ORDEM_QUANTIDADE,
    LIMITE_TEXTO_ORIGEM,
    MARCADOR_NAO_VERIFICADO,
    QUANTIDADE_MINIMA,
    SERVICOS_GENERICOS,
    TAMANHO_PREFIXO_TRECHO,
    UNIDADES_VALIDAS,
)
from core.documents.provenance import montar_id_origem
from core.documents.types import ExigenciaNormativa, ServicoDetectado, TrechoExtraido

_PISTAS_NORMATIVAS: tuple[str, ...] = (
    "nbr",
    "norma",
    "deve",
    "conforme",
    "exig",
    "mínimo",
    "minimo",
    "máximo",
    "maximo",
)

_EXPRESSAO_QUANTIDADE = re.compile(
    r"(\d[\d\.,]*)\s*(m²|m³|m2|m3|\bm\b|kg|\bun\b|\bh\b|vb|mes|dia|\bt\b|\bl\b)",
    re.IGNORECASE,
)

_FONTES_BLOQUEADAS: tuple[str, ...] = ("desconhecida", "não informada", "ia", "exemplo")


def montar_prompt_exigencias(trechos: list[TrechoExtraido]) -> str:
    """Monta pedido de exigências com gramática JSON e trava anti-alucinação."""
    bloco = _formatar_trechos(trechos)
    return (
        "Leia os trechos de engenharia e devolva SÓ JSON válido.\n"
        'Formato: {"exigencias": [{"descricao": "", "fonte": "", '
        '"trecho_citado": "", "pagina_ou_aba": ""}]}\n'
        "Regras: cite trecho literal com página ou aba; sem trecho, descarte; "
        "nunca invente norma; fonte é a página ou aba.\n"
        f"Trechos:\n{bloco}\n"
    )


def montar_prompt_servicos(trechos: list[TrechoExtraido]) -> str:
    """Monta pedido de serviços com quantidade só quando há número."""
    bloco = _formatar_trechos(trechos)
    return (
        "Leia os trechos e devolva SÓ JSON válido.\n"
        'Formato: {"servicos": [{"descricao": "", "unidade_sugerida": "", '
        '"quantidade": null, "trecho_citado": "", "pagina_ou_aba": ""}]}\n'
        "Regras: quantidade como texto decimal ou null; null quando não há "
        "número no trecho; unidade entre as válidas; sem trecho, descarte; "
        "nunca estime.\n"
        f"Trechos:\n{bloco}\n"
    )


def validar_exigencias(
    carga: object, trechos: list[TrechoExtraido]
) -> list[ExigenciaNormativa]:
    """Aplica 7 portões locais e descarta exigência sem trecho citável."""
    itens = _extrair_lista(carga, "exigencias")
    indice = _indice_trechos(trechos)
    saida: list[ExigenciaNormativa] = []
    for item in itens:
        validada = _validar_uma_exigencia(item, indice)
        if validada is not None:
            saida.append(validada)
    return saida


def validar_servicos(
    carga: object, trechos: list[TrechoExtraido]
) -> list[ServicoDetectado]:
    """Aplica 7 portões locais; número sem trecho vira None, nunca chute."""
    itens = _extrair_lista(carga, "servicos")
    indice = _indice_trechos(trechos)
    saida: list[ServicoDetectado] = []
    for item in itens:
        validado = _validar_um_servico(item, indice)
        if validado is not None:
            saida.append(validado)
    return saida


def extrair_exigencias_offline(
    trechos: list[TrechoExtraido],
) -> list[ExigenciaNormativa]:
    """Regras locais quando sem chave; declara não verificado."""
    saida: list[ExigenciaNormativa] = []
    for posicao, trecho in enumerate(trechos):
        for frase in _frases(trecho.texto):
            if _tem_pista_normativa(frase):
                origem = montar_id_origem(trecho, posicao)
                fonte = f"{trecho.pagina_ou_aba} ({MARCADOR_NAO_VERIFICADO})"
                saida.append(
                    ExigenciaNormativa(
                        descricao=frase.strip(), fonte=fonte, id_origem=origem
                    )
                )
    return saida


def extrair_servicos_offline(trechos: list[TrechoExtraido]) -> list[ServicoDetectado]:
    """Dicionário genérico + regex de unidades; sem número, None."""
    saida: list[ServicoDetectado] = []
    for posicao, trecho in enumerate(trechos):
        inferior = trecho.texto.lower()
        for servico in SERVICOS_GENERICOS:
            if servico in inferior:
                quantidade, unidade = _buscar_quantidade(trecho.texto)
                origem = montar_id_origem(trecho, posicao)
                fonte_unidade = unidade if unidade else "un"
                if fonte_unidade not in UNIDADES_VALIDAS:
                    fonte_unidade = "un"
                descricao = (
                    f"{servico} — {trecho.texto.strip()[:LIMITE_DESCRICAO_OFFLINE]}"
                )
                saida.append(
                    ServicoDetectado(
                        descricao=descricao,
                        unidade_sugerida=fonte_unidade,
                        quantidade=quantidade,
                        id_origem=origem,
                    )
                )
                break
    return saida


def _formatar_trechos(trechos: list[TrechoExtraido]) -> str:
    """Numera trechos com origem para a IA citar sem adivinhar."""
    linhas: list[str] = []
    for posicao, trecho in enumerate(trechos):
        linhas.append(
            f"[{posicao}] {trecho.pagina_ou_aba}|{trecho.origem}: {trecho.texto}"
        )
    return "\n".join(linhas)


def _indice_trechos(trechos: list[TrechoExtraido]) -> dict[str, TrechoExtraido]:
    """Indexa por página para conferir proveniência em O(1)."""
    return {trecho.pagina_ou_aba: trecho for trecho in trechos}


def _extrair_lista(carga: object, chave: str) -> list[dict[str, object]]:
    """Extrai lista de dicionários do JSON da IA com falha segura."""
    if not isinstance(carga, dict):
        return []
    bruta = carga.get(chave)
    if not isinstance(bruta, list):
        return []
    return [item for item in bruta if isinstance(item, dict)]


def _validar_uma_exigencia(
    item: dict[str, object], indice: dict[str, TrechoExtraido]
) -> ExigenciaNormativa | None:
    """Sete portões da exigência; qualquer falha descarta."""
    descricao = _texto_de(item.get("descricao"))
    fonte = _texto_de(item.get("fonte"))
    trecho_citado = _texto_de(item.get("trecho_citado"))
    pagina = _texto_de(item.get("pagina_ou_aba"))
    if not descricao or not trecho_citado or not pagina:
        return None
    if pagina not in indice:
        return None
    if fonte.lower().strip() in _FONTES_BLOQUEADAS or not fonte.strip():
        return None
    original = indice[pagina].texto
    prefixo = trecho_citado[:TAMANHO_PREFIXO_TRECHO].strip()
    sem_vinculo = trecho_citado.strip() not in original
    sem_inverso = original not in trecho_citado
    sem_prefixo = prefixo not in original
    if sem_vinculo and sem_inverso and sem_prefixo:
        return None
    origem = f"{indice[pagina].origem}#{pagina}:{trecho_citado[:LIMITE_TEXTO_ORIGEM]}"
    return ExigenciaNormativa(
        descricao=descricao.strip(), fonte=fonte.strip(), id_origem=origem
    )


def _validar_um_servico(
    item: dict[str, object], indice: dict[str, TrechoExtraido]
) -> ServicoDetectado | None:
    """Sete portões do serviço; número órfão vira None."""
    descricao = _texto_de(item.get("descricao"))
    unidade = _texto_de(item.get("unidade_sugerida")).lower().strip()
    pagina = _texto_de(item.get("pagina_ou_aba"))
    trecho_citado = _texto_de(item.get("trecho_citado"))
    if not descricao or not pagina or not trecho_citado:
        return None
    if pagina not in indice:
        return None
    if unidade not in UNIDADES_VALIDAS:
        return None
    quantidade = _ler_quantidade_carga(item.get("quantidade"))
    if quantidade is not None and not _trecho_tem_numero(trecho_citado):
        quantidade = None
    if quantidade is not None and not _ordem_ok(quantidade):
        return None
    origem = f"{indice[pagina].origem}#{pagina}:{trecho_citado[:LIMITE_TEXTO_ORIGEM]}"
    return ServicoDetectado(
        descricao=descricao.strip(),
        unidade_sugerida=unidade,
        quantidade=quantidade,
        id_origem=origem,
    )


def _texto_de(valor: object) -> str:
    """Normaliza campo textual da IA sem aceitar tipo inesperado."""
    return valor.strip() if isinstance(valor, str) else ""


def _ler_quantidade_carga(valor: object) -> Decimal | None:
    """Lê quantidade da IA como texto decimal; resto vira None."""
    if valor is None:
        return None
    if isinstance(valor, (int, str)):
        return _converter_numero_br(str(valor))
    return None


def _trecho_tem_numero(trecho: str) -> bool:
    """Confere se há dígito no trecho antes de aceitar número."""
    return any(caractere.isdigit() for caractere in trecho)


def _ordem_ok(quantidade: Decimal) -> bool:
    """Barra negativo e ordem absurda sem documento robusto."""
    return QUANTIDADE_MINIMA <= quantidade <= LIMITE_ORDEM_QUANTIDADE


def _frases(texto: str) -> list[str]:
    """Quebra memorial em frases para achar exigência normativa."""
    partes = re.split(r"[.\n;]+", texto)
    return [
        parte.strip() for parte in partes if len(parte.strip()) > LIMITE_MINIMO_FRASE
    ]


def _tem_pista_normativa(frase: str) -> bool:
    """Detecta pista normativa sem IA, por vocabulário explícito."""
    inferior = frase.lower()
    return any(pista in inferior for pista in _PISTAS_NORMATIVAS)


def _buscar_quantidade(texto: str) -> tuple[Decimal | None, str]:
    """Busca número + unidade; sem número, devolve None sem inventar."""
    achado = _EXPRESSAO_QUANTIDADE.search(texto)
    if achado is None:
        return None, ""
    numero = _converter_numero_br(achado.group(GRUPO_NUMERO_QUANTIDADE))
    unidade = achado.group(GRUPO_UNIDADE_QUANTIDADE).lower().strip()
    return numero, unidade


def _converter_numero_br(texto_num: str) -> Decimal | None:
    """Converte BR (1.234,56) para Decimal; ilegível vira None."""
    limpo = texto_num.strip().replace(" ", "")
    if not limpo:
        return None
    try:
        if "," in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        return Decimal(limpo)
    except (InvalidOperation, ValueError, AttributeError):
        return None
