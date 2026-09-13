"""Token de sessão do sidecar — VS-02 e VS-03 de VERTICE-LINT-SUITE.md §8.

Porquê: o sidecar escuta em `127.0.0.1`, mas qualquer processo na
mesma máquina alcança essa porta. O token é a única barreira entre
"processo local" e "este app local" — sem ele, VS-02 falha por
construção, não por descuido.
"""

from __future__ import annotations

import secrets

from fastapi import Header, HTTPException, status

TAMANHO_TOKEN_BYTES: int = 32
NOME_CABECALHO_TOKEN: str = "X-Vertice-Token"


def gerar_token() -> str:
    """Gera um token de sessão novo, aleatório, a cada subida do processo.

    Porquê: token fixo em código ou arquivo versionado é segredo que
    vaza; um token por processo expira sozinho ao fechar a janela.
    """
    return secrets.token_urlsafe(TAMANHO_TOKEN_BYTES)


def criar_verificador_de_token(token_esperado: str) -> VerificadorDeToken:
    """Constrói a dependência do FastAPI que barra requisição sem token."""
    return VerificadorDeToken(token_esperado)


class VerificadorDeToken:
    """Dependência do FastAPI: compara o cabeçalho contra o token da sessão.

    Porquê classe, não função solta: o token pertence a uma sessão do
    processo, não é constante de módulo — cada `criar_app` tem o seu.
    """

    def __init__(self, token_esperado: str) -> None:
        self._token_esperado = token_esperado

    def __call__(self, x_vertice_token: str | None = Header(default=None)) -> None:
        """Lança 401 quando o cabeçalho falta ou não confere.

        Porquê `secrets.compare_digest`: comparação ingênua de string
        vaza tempo proporcional ao prefixo certo — pouco provável de
        ser explorável em localhost, mas comparar token é o único
        lugar do sidecar onde o hábito certo custa nada a mais.
        """
        if x_vertice_token is None or not secrets.compare_digest(
            x_vertice_token, self._token_esperado
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="token de sessão ausente ou inválido",
            )
