#!/usr/bin/env python3
"""Lint documental do VÉRTICE — regras VM-01 a VM-09 e VM-11.

Ignora conteúdo dentro de cercas de código: comentário Python iniciado por '#'
não é título de markdown. Incidente de 13/09/2026.
"""

import collections
import re
import sys
from pathlib import Path

EXPRESSAO_VERSAO = re.compile(r"^\*\*Versão:\*\*\s*(\S+)", re.M)
EXPRESSAO_LINHA_INDICE = re.compile(
    r"\|\s*`(VERTICE[-\w]*\.md)`\s*\|\s*([0-9]+\.[0-9]+)\s*\|"
)


def fora_de_cerca(linhas):
    """Devolve (indice, linha) apenas para linhas fora de blocos de código."""
    dentro = False
    for i, linha in enumerate(linhas, 1):
        if linha.startswith("```"):
            dentro = not dentro
            continue
        if not dentro:
            yield i, linha


def analisar(caminho, conhecidos):
    """Aplica VM-01 a VM-09 num documento e devolve a lista de achados."""
    s = Path(caminho).read_text(encoding="utf-8")
    linhas = s.split("\n")
    achados = []
    uteis = list(fora_de_cerca(linhas))

    titulos = [
        (i, len(m.group(1)), m.group(2))
        for i, linha in uteis
        if (m := re.match(r"^(#+)\s+(.*)", linha))
    ]
    anterior = 0
    for i, nivel, _texto in titulos:
        if anterior and nivel > anterior + 1:
            achados.append(f"VM-01 L{i}: pulo de H{anterior} para H{nivel}")
        anterior = nivel
    for texto, qtd in collections.Counter(t for _, _, t in titulos).items():
        if qtd > 1:
            achados.append(f"VM-02: título duplicado '{texto[:45]}'")

    cercas = [linha for linha in linhas if linha.startswith("```")]
    if len(cercas) % 2:
        achados.append("VM-04: cerca de código não fechada")
    if [linha for linha in cercas[::2] if linha.strip() == "```"]:
        achados.append("VM-03: cerca sem linguagem declarada")

    achados.extend(_checar_tabelas(linhas))

    if [1 for linha in linhas if linha != linha.rstrip()]:
        achados.append("VM-06: espaço em fim de linha")
    for m in re.finditer(r"`(VERTICE[-\w]*\.md)`", s):
        if m.group(1) not in conhecidos:
            achados.append(f"VM-07: referência a documento inexistente '{m.group(1)}'")
    for i, linha in uteis:
        if (
            linha.strip().startswith("style ")
            and "fill:" in linha
            and ("color:" not in linha or "stroke:" not in linha)
        ):
            achados.append(f"VM-08 L{i}: nó Mermaid sem contraste explícito")
    if "**Versão:**" not in s:
        achados.append("VM-09: sem versão declarada")
    if "Histórico" not in s:
        achados.append("VM-09: sem tabela de histórico")
    return achados


def _checar_tabelas(linhas):
    """VM-05: toda linha da tabela tem a mesma contagem de colunas."""
    achados = []
    i = 0
    while i < len(linhas):
        cabecalho = linhas[i].strip().startswith("|")
        separador = i + 1 < len(linhas) and re.match(
            r"^\s*\|[\s:|-]+\|\s*$", linhas[i + 1]
        )
        if not (cabecalho and separador):
            i += 1
            continue
        colunas = linhas[i].count("|")
        j = i
        while j < len(linhas) and linhas[j].strip().startswith("|"):
            if linhas[j].count("|") != colunas:
                achados.append(f"VM-05 L{j + 1}: tabela com colunas divergentes")
            j += 1
        i = j
    return achados


def versao_declarada(caminho):
    """Lê a versão do cabeçalho do documento; None quando ausente."""
    m = EXPRESSAO_VERSAO.search(Path(caminho).read_text(encoding="utf-8"))
    return m.group(1) if m else None


def checar_indice(pasta, docs):
    """VM-11: INDICE.md cobre todo documento na versão que ele traz."""
    s = (Path(pasta) / "INDICE.md").read_text(encoding="utf-8")
    declarado = {m.group(1): m.group(2) for m in EXPRESSAO_LINHA_INDICE.finditer(s)}
    achados = []
    for d in docs:
        if d == "INDICE.md":
            continue
        real = versao_declarada(Path(pasta) / d)
        if d not in declarado:
            achados.append(f"VM-11: '{d}' fora do conjunto compatível do INDICE.md")
        elif declarado[d] != real:
            achados.append(f"VM-11: '{d}' está {real}, INDICE.md diz {declarado[d]}")
    for nome in declarado:
        if nome not in docs:
            achados.append(f"VM-11: INDICE.md lista '{nome}', que não existe")
    return achados


def main(pasta="."):
    """Roda o portão G3 sobre a pasta e devolve 1 quando há achado."""
    docs = sorted(
        f.name
        for f in Path(pasta).iterdir()
        if (f.name.startswith("VERTICE") or f.name == "INDICE.md")
        and f.name.endswith(".md")
    )
    total = 0
    for d in docs:
        achados = analisar(Path(pasta) / d, docs)
        if d == "INDICE.md":
            achados += checar_indice(pasta, docs)
        total += len(achados)
        print(f"{d:<38}{'OK' if not achados else 'REPROVADO'}")
        for a in achados:
            print(f"      x {a}")
    print(f"\nTOTAL DE ACHADOS: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
