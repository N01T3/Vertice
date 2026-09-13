"""`instalar` — o terceiro nome da interface pública de arquitetura §3.

Porquê tão fino: carregar valida forma, validar confere conteúdo —
"instalar" hoje é só encadear os dois. Ainda não existe um registro
de "pacote ativo" no app (nenhuma configuração persistente foi
construída), então este módulo não promete mais do que isso.
"""

from __future__ import annotations

from pathlib import Path

from core.packages.loader import carregar
from core.packages.types import ResultadoInstalacao
from core.packages.validator import validar


def instalar(caminho_manifesto: Path) -> ResultadoInstalacao:
    """Carrega e valida um pacote de domínio.

    Porquê não lança em cima de alerta de `validar`: um pacote com
    `regras_medicao` vazio ainda é instalável — ele só não serve para
    medir nada ainda. Forma inválida (`carregar`) continua abortando,
    porque aí o manifesto nem é um pacote reconhecível.
    """
    pacote = carregar(caminho_manifesto)
    alertas = validar(pacote)
    return ResultadoInstalacao(pacote=pacote, alertas=alertas)
