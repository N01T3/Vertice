"""Lint de representação persistida VÉRTICE: VD-15 e VD-16.

Porquê: `VD-01` proíbe float no Python, mas o esquema vive no Markdown.
Proibir metade do caminho é conselho, não arquitetura — aqui vira comando.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

# A ferramenta roda de qualquer diretório; a gramática mora no domínio,
# e o domínio é dono único dela — copiar a expressão aqui é como ela diverge.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.domain.origin import RAIZES_ID_ORIGEM

# Coluna REAL é o float do SQLite; ver VERTICE-arquitetura.md §5.1.
EXPRESSAO_COLUNA_REAL = re.compile(r"^\s*\w+\s+REAL\b", re.MULTILINE)

# Bloco ```sql ... ``` dentro de documento Markdown.
EXPRESSAO_BLOCO_SQL = re.compile(r"```sql\n(.*?)```", re.DOTALL)

NOME_CAMPO_ORIGEM: str = "id_origem"


def main() -> int:
    """Roda VD-15 e VD-16 sobre docs e núcleo; 0 quando sem achado."""
    argumentos = _analisar_argumentos()
    raiz = Path(argumentos.raiz)
    docs = Path(argumentos.docs)
    achados: list[str] = []
    for documento in sorted(docs.glob("VERTICE-*.md")):
        achados.extend(_checar_real(documento))
    for arquivo in sorted((raiz / "core").rglob("*.py")):
        achados.extend(_checar_real(arquivo))
        achados.extend(_checar_id_origem(arquivo))
    for achado in achados:
        print(achado)
    print(f"schema_lint: {len(achados)} achado(s)")
    return 0 if not achados else 1


def _analisar_argumentos() -> argparse.Namespace:
    """Lê a raiz do repositório e a pasta de documentos da linha de comando.

    Porquê separado: `core/` mora na raiz do repositório, mas os
    documentos `VERTICE-*.md` ficam em `docs/` — uma única
    `--raiz` deixou de servir aos dois propósitos.
    """
    analisador = argparse.ArgumentParser(description="Lint de esquema VÉRTICE")
    analisador.add_argument("--raiz", default=".", help="onde fica core/")
    analisador.add_argument("--docs", default="docs", help="onde ficam os VERTICE-*.md")
    return analisador.parse_args()


def _checar_real(arquivo: Path) -> list[str]:
    """VD-15: nenhuma coluna REAL em esquema, no doc ou no código."""
    texto = arquivo.read_text(encoding="utf-8")
    eh_doc = arquivo.suffix == ".md"
    blocos = EXPRESSAO_BLOCO_SQL.findall(texto) if eh_doc else [texto]
    achados: list[str] = []
    for bloco in blocos:
        for linha in EXPRESSAO_COLUNA_REAL.findall(bloco):
            achados.append(f"VD-15 {arquivo}: coluna REAL em {linha.strip()!r}")
    return achados


def _checar_id_origem(arquivo: Path) -> list[str]:
    """VD-16: literal de id_origem dentro da gramática de §4.1."""
    try:
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
    except SyntaxError as erro:
        return [f"VD-00 {arquivo}: sintaxe inválida: {erro}"]
    achados: list[str] = []
    for no in ast.walk(arvore):
        if not isinstance(no, ast.Call):
            continue
        for palavra in no.keywords:
            if palavra.arg != NOME_CAMPO_ORIGEM:
                continue
            prefixo = _prefixo_literal(palavra.value)
            if prefixo is None:
                continue
            if not any(prefixo.startswith(f"{raiz}:") for raiz in RAIZES_ID_ORIGEM):
                achados.append(
                    f"VD-16 {arquivo}:{no.lineno}: id_origem sem raiz: {prefixo!r}"
                )
    return achados


def _prefixo_literal(valor: ast.expr) -> str | None:
    """Devolve o começo textual do valor, ou None se não for literal."""
    if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
        return valor.value
    if isinstance(valor, ast.JoinedStr) and valor.values:
        primeiro = valor.values[0]
        if isinstance(primeiro, ast.Constant) and isinstance(primeiro.value, str):
            return primeiro.value
    return None


if __name__ == "__main__":
    sys.exit(main())
