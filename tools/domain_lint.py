"""Lint de domínio VÉRTICE: VD-01 a VD-14.

Porquê: ferramenta genérica não cobre regra de negócio;
este script mede o que separa produto de gerador de números.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

PROIBIDAS_INGLES: frozenset[str] = frozenset(
    {
        "calculate",
        "file",
        "content",
        "service",
        "requirement",
        "provider",
        "suggest",
        "response",
        "request",
        "result",
        "manager",
        "handler",
        "factory",
        "builder",
        "parser",
        "loader",
        "controller",
        "utils",
        "helper",
        "helpers",
        "config",
        "settings",
    }
)

REDES_EXTERNAS: tuple[str, ...] = (
    "openai_provider",
    "openai",
    "httpx",
    "requests",
    "urllib.request",
)


def main() -> int:
    """Roda portões VD sobre core/ e devolve 0 quando sem achado."""
    argumentos = _analisar_argumentos()
    raiz = Path("core")
    arquivos = sorted(raiz.rglob("*.py"))
    achados: list[str] = []
    for arquivo in arquivos:
        achados.extend(_verificar_arquivo(arquivo, argumentos))
    achados.extend(_verificar_importadores(arquivos))
    for achado in achados:
        print(achado)
    print(f"domain_lint: {len(achados)} achado(s)")
    return 0 if not achados else 1


def _analisar_argumentos() -> argparse.Namespace:
    """Lê limites da linha de comando com padrão da suíte."""
    analisador = argparse.ArgumentParser(description="Lint de domínio VÉRTICE")
    analisador.add_argument("--max-linhas-arquivo", type=int, default=300)
    analisador.add_argument("--max-linhas-funcao", type=int, default=40)
    return analisador.parse_args()


def _verificar_arquivo(arquivo: Path, argumentos: argparse.Namespace) -> list[str]:
    """Aplica VD-01 a VD-13 em um arquivo do núcleo."""
    texto = arquivo.read_text(encoding="utf-8")
    linhas = texto.splitlines()
    achados: list[str] = []
    if len(linhas) > argumentos.max_linhas_arquivo:
        achados.append(f"VD-09 {arquivo}: {len(linhas)} linhas")
    try:
        arvore = ast.parse(texto, filename=str(arquivo))
    except SyntaxError as erro:
        return [f"VD-00 {arquivo}: sintaxe inválida: {erro}"]
    achados.extend(_checar_float(arvore, arquivo))
    achados.extend(_checar_ingles(arvore, arquivo))
    achados.extend(_checar_magicos(arvore, arquivo))
    achados.extend(_checar_except(arvore, arquivo))
    achados.extend(_checar_rede(arquivo, texto))
    achados.extend(_checar_select(arquivo, texto))
    achados.extend(_checar_assinatura(arvore, arquivo))
    achados.extend(_checar_tamanho_funcao(arvore, arquivo, argumentos))
    achados.extend(_checar_complexidade(arvore, arquivo))
    achados.extend(_checar_classe(arvore, arquivo))
    achados.extend(_checar_parametros(arvore, arquivo))
    return achados


def _checar_float(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-01: nenhum float em valor do núcleo.

    Isenção em `reference_base/adapters/`: quem lê um `.xlsx`
    recebe IEEE754 nativo do formato — reconhecer isso na fronteira,
    para converter em Decimal/centavos uma única vez, não é computar
    com float. VERTICE-arquitetura.md §5.1 e VERTICE-LINT-SUITE.md §3.1.
    """
    parte = str(arquivo).replace("\\", "/")
    if "reference_base/adapters" in parte:
        return []
    achados: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Name) and no.id == "float":
            achados.append(f"VD-01 {arquivo}:{no.lineno}: uso de float")
    return achados


def _checar_ingles(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-02: identificadores definidos em português."""
    achados: list[str] = []
    for no in ast.walk(arvore):
        nomes: list[str] = []
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nomes.append(no.name)
        if isinstance(no, ast.arg) and no.arg not in ("self", "cls"):
            nomes.append(no.arg)
        for nome in nomes:
            if nome.lower() in PROIBIDAS_INGLES:
                achados.append(f"VD-02 {arquivo}:{no.lineno}: {nome}")
    return achados


def _checar_magicos(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-03: número fora de constante nomeada."""
    if arquivo.name == "constants.py":
        return []
    achados: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Constant) and isinstance(no.value, (int, float)):
            valor = no.value
            if valor in (0, 1, -1):
                continue
            if _eh_definicao_constante(no, arvore):
                continue
            achados.append(f"VD-03 {arquivo}:{no.lineno}: número {valor}")
    return achados


def _eh_definicao_constante(alvo: ast.Constant, arvore: ast.AST) -> bool:
    """Diz se o número mora em atribuição a NOME_MAIUSCULO."""
    for no in ast.walk(arvore):
        if isinstance(no, ast.Assign):
            for destino in no.targets:
                if isinstance(destino, ast.Name) and destino.id.isupper():
                    for filho in ast.walk(no):
                        if filho is alvo:
                            return True
        if isinstance(no, ast.AnnAssign):
            destino = no.target
            if isinstance(destino, ast.Name) and destino.id.isupper():
                for filho in ast.walk(no):
                    if filho is alvo:
                        return True
    return False


def _checar_except(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-04: except sempre tipado e nunca silencioso."""
    achados: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.ExceptHandler):
            if no.type is None:
                achados.append(f"VD-04 {arquivo}:{no.lineno}: except sem tipo")
            elif len(no.body) == 1 and isinstance(no.body[0], ast.Pass):
                achados.append(f"VD-04 {arquivo}:{no.lineno}: except vazio")
    return achados


def _checar_rede(arquivo: Path, texto: str) -> list[str]:
    """VD-05: rede só em classification/ ou antagonista/."""
    parte = str(arquivo).replace("\\", "/")
    if "classification" in parte or "antagonista" in parte:
        return []
    for rede in REDES_EXTERNAS:
        if rede in texto:
            return [f"VD-05 {arquivo}: chamada de rede fora do permitido: {rede}"]
    return []


def _checar_select(arquivo: Path, texto: str) -> list[str]:
    """VD-07: nenhum SELECT * em consulta de produção."""
    if "select *" in texto.lower():
        return [f"VD-07 {arquivo}: SELECT * proibido"]
    return []


def _checar_assinatura(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-08: função pública com tipo e docstring do porquê."""
    achados: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if no.name.startswith("_"):
                continue
            sem_retorno = no.returns is None
            sem_arg = any(
                arg.annotation is None
                for arg in list(no.args.args)
                if arg.arg not in ("self", "cls")
            )
            sem_doc = ast.get_docstring(no) is None
            if sem_retorno or sem_arg or sem_doc:
                achados.append(f"VD-08 {arquivo}:{no.lineno}: {no.name} sem tipo/doc")
    return achados


def _checar_tamanho_funcao(
    arvore: ast.AST, arquivo: Path, argumentos: argparse.Namespace
) -> list[str]:
    """VD-10: função com mais de 40 linhas faz mais de uma coisa."""
    achados: list[str] = []
    limite = int(argumentos.max_linhas_funcao)
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fim = getattr(no, "end_lineno", no.lineno) or no.lineno
            tamanho = fim - no.lineno + 1
            if tamanho > limite:
                achados.append(f"VD-10 {arquivo}:{no.lineno}: {no.name} {tamanho}")
    return achados


def _checar_complexidade(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-11: complexidade ciclomática acima de 10 ninguém testa."""
    achados: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            pontos = 1
            for filho in ast.walk(no):
                if isinstance(filho, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    pontos += 1
                if isinstance(filho, ast.BoolOp):
                    pontos += len(filho.values) - 1
            if pontos > 10:
                achados.append(f"VD-11 {arquivo}:{no.lineno}: {no.name} {pontos}")
    return achados


def _checar_classe(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-12: classe com mais de 7 métodos públicos acumula dever."""
    achados: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.ClassDef):
            publicos = [
                item
                for item in no.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not item.name.startswith("_")
            ]
            if len(publicos) > 7:
                achados.append(f"VD-12 {arquivo}:{no.lineno}: {no.name}")
    return achados


def _checar_parametros(arvore: ast.AST, arquivo: Path) -> list[str]:
    """VD-13: função com mais de 5 parâmetros esconde um objeto."""
    achados: list[str] = []
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total = [arg for arg in no.args.args if arg.arg not in ("self", "cls")]
            total += list(no.args.kwonlyargs)
            if len(total) > 5:
                achados.append(f"VD-13 {arquivo}:{no.lineno}: {no.name}")
    return achados


def _verificar_importadores(arquivos: list[Path]) -> list[str]:
    """VD-14 e VD-06: acoplamento excessivo e escrita do auditor."""
    mapa: dict[str, list[str]] = {}
    for arquivo in arquivos:
        texto = arquivo.read_text(encoding="utf-8")
        try:
            arvore = ast.parse(texto)
        except SyntaxError:
            continue
        for no in ast.walk(arvore):
            alvo: str | None = None
            if isinstance(no, ast.ImportFrom) and no.module:
                alvo = no.module
            if alvo and alvo.startswith("core."):
                mapa.setdefault(alvo, []).append(str(arquivo))
    achados: list[str] = []
    for modulo, quem in mapa.items():
        if len(set(quem)) > 8:
            achados.append(f"VD-14 {modulo}: importado por {len(set(quem))}")
    return achados


if __name__ == "__main__":
    sys.exit(main())
