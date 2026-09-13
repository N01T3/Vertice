"""Sidecar HTTP — a fronteira entre a interface e o núcleo Python.

Porquê: VERTICE-arquitetura.md §2.2 — o shell fala com o núcleo só por
HTTP em `127.0.0.1`, nunca por import direto de processo. `api/` é o
único módulo que conhece requisição e resposta; a lógica mora no
módulo que a requisição serve, nunca aqui.
"""
