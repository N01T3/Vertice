"""Monta o sidecar: `/saude` livre, todo o resto atrás do token de sessão.

Porquê `criar_app` ser fábrica, não módulo-nível: teste precisa de um
banco próprio e um token conhecido: um `app` global amarrado a
variável de ambiente tornaria isso impossível de isolar por teste.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.api.routes.pricing import roteador as roteador_precificacao
from core.api.routes.reference_base import roteador as roteador_sinapi
from core.api.security import criar_verificador_de_token, gerar_token
from core.packages.installer import instalar

ORIGENS_DEV_PERMITIDAS: tuple[str, ...] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

# Repo raiz: core/api/app.py -> core/api -> core -> raiz. Mesmo cálculo
# de server.py para CAMINHO_SESSAO_DEV — um só jeito de achar a raiz.
CAMINHO_PACOTE_PADRAO: Path = (
    Path(__file__).resolve().parents[2]
    / "packages"
    / "civil-construction-br"
    / "package.yaml"
)


def criar_app(
    caminho_banco: Path,
    token: str | None = None,
    caminho_pacote: Path | None = None,
) -> FastAPI:
    """Monta o app do sidecar para um banco, um pacote e um token dados.

    Porquê `token` opcional: em produção o processo gera o seu ao
    subir (§2.2); em teste, o chamador passa um fixo para poder
    montar o cabeçalho de antemão. `caminho_pacote` idem: em produção
    é sempre o pacote instalado; em teste, o chamador pode apontar
    para um manifesto sintético.
    """
    token_da_sessao = token if token is not None else gerar_token()
    app = FastAPI(title="VÉRTICE — sidecar", version="0.1.0")
    app.state.caminho_banco = caminho_banco
    app.state.token = token_da_sessao
    app.state.pacote = instalar(caminho_pacote or CAMINHO_PACOTE_PADRAO).pacote
    _configurar_cors_de_desenvolvimento(app)

    @app.get("/saude")
    def saude() -> dict[str, str]:
        """Sem token de propósito: é o que o shell sonda a cada 5 s (§2.2)."""
        return {"situacao": "ok"}

    verificador = criar_verificador_de_token(token_da_sessao)
    dependencias = [Depends(verificador)]
    app.include_router(roteador_sinapi, dependencies=dependencias)
    app.include_router(roteador_precificacao, dependencies=dependencias)
    return app


def _configurar_cors_de_desenvolvimento(app: FastAPI) -> None:
    """Libera o servidor de dev do Vite — nunca usado no build empacotado.

    Porquê existe: em produção o Tauri serve a interface do mesmo
    processo que fala com o sidecar, sem origem cruzada. Em dev, Vite
    roda numa porta própria — sem isto o navegador barra a chamada.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(ORIGENS_DEV_PERMITIDAS),
        allow_methods=["GET"],
        allow_headers=["X-Vertice-Token"],
    )
