"""Ponto de entrada do sidecar — o que roda quando alguém sobe o processo.

Porquê separado de `app.py`: `criar_app` é testável sem subir servidor
nem tocar disco; este módulo é o único que lê variável de ambiente,
escreve arquivo e chama `uvicorn.run` — o efeito colateral fica todo
num lugar só.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import uvicorn

from core.api.app import criar_app
from core.api.security import gerar_token

HOST_SIDECAR: str = "127.0.0.1"  # VS-03: nunca 0.0.0.0
PORTA_PADRAO_DEV: int = 8756

VAR_CAMINHO_BANCO: str = "VERTICE_DB_PATH"
VAR_PORTA: str = "VERTICE_SIDECAR_PORT"

# Onde o frontend em modo dev busca token e porta — ver
# src/shared/http-client.ts. Vite serve `public/` na raiz do site.
CAMINHO_SESSAO_DEV: Path = (
    Path(__file__).resolve().parents[2] / "public" / "dev-session.json"
)


def main() -> None:
    """Sobe o sidecar: lê configuração, publica a sessão, serve."""
    caminho_banco = _ler_caminho_banco()
    porta = int(os.environ.get(VAR_PORTA, PORTA_PADRAO_DEV))
    token = gerar_token()

    _publicar_sessao_dev(token, porta)
    app = criar_app(caminho_banco, token=token)

    print(f"VÉRTICE sidecar em http://{HOST_SIDECAR}:{porta} — banco: {caminho_banco}")
    uvicorn.run(app, host=HOST_SIDECAR, port=porta, log_level="info")


def _ler_caminho_banco() -> Path:
    """Lê `VERTICE_DB_PATH`; falha cedo e claro se faltar ou não existir.

    Porquê falhar aqui, não deixar o SQLite falhar depois: abrir banco
    inexistente cria um arquivo vazio em silêncio — o pior tipo de erro,
    porque parece ter funcionado.
    """
    bruto = os.environ.get(VAR_CAMINHO_BANCO)
    if not bruto:
        raise SystemExit(f"defina {VAR_CAMINHO_BANCO} apontando para o .db do acervo")
    caminho = Path(bruto)
    if not caminho.exists():
        raise SystemExit(f"{VAR_CAMINHO_BANCO}={caminho} não existe")
    return caminho


def _publicar_sessao_dev(token: str, porta: int) -> None:
    """Escreve token e porta onde o frontend em modo dev sabe procurar."""
    CAMINHO_SESSAO_DEV.parent.mkdir(parents=True, exist_ok=True)
    CAMINHO_SESSAO_DEV.write_text(
        json.dumps({"token": token, "porta": porta}), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
