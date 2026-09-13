"""Adaptador SINAPI — o único que existe hoje (ADR-008).

Porquê: schema, busca e explosão em `reference_base/` são o motor;
tudo que sabe o nome de uma aba ou a posição de uma coluna mora aqui.
"""

from core.reference_base.adapters.sinapi.importer import importar_pacote

__all__ = ["importar_pacote"]
