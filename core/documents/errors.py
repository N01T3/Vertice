"""Erros tipados da ingestão de documentos.

Porquê: `except` genérico esconde se faltou dependência, se o arquivo
quebrou ou se o sigilo barrou. Quem chama precisa decidir pelo tipo.
"""

from __future__ import annotations


class ErroDocumento(Exception):
    """Base dos erros de ingestão; nunca lançada direta, só herdada."""


class ErroTipoNaoSuportado(ErroDocumento):
    """Extensão sem leitor correspondente no modo generalista."""


class ErroDependenciaAusente(ErroDocumento):
    """Leitor opcional indisponível; diz qual instalar, sem travar o resto."""


class ErroLeituraDocumento(ErroDocumento):
    """Arquivo existe mas não pôde ser lido com o leitor indicado."""


class ErroSigilo(ErroDocumento):
    """Trecho com dado de cliente; bloqueia envio à IA e registra incidente."""


class ErroValidacaoConteudo(ErroDocumento):
    """Carga da IA sem trecho ou página que a sustente; descartada."""
