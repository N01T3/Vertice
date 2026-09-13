"""Constantes da ingestão de documentos.

Porquê: número e lista soltos no código viram decisão invisível.
Tudo que é limiar, versão ou vocabulário mora aqui, com nome
que explica o papel no domínio.
"""

from __future__ import annotations

from decimal import Decimal

# Leitura de arquivo em blocos: evita carregar memorial grande de uma vez.
TAMANHO_BLOCO_HASH: int = 8192

# Trecho longo demais estoura prompt e dificulta citação; divide para rastrear.
LIMITE_CARACTERES_TRECHO: int = 2000

# DXF: versão mínima aceita é R2013 (AC1027). Rebaixar destrói hachura e texto.
VERSAO_DXF_MINIMA_ACEITA: str = "AC1027"

# Ordem cronológica das versões DXF para comparar sem adivinhar pelo nome.
ORDEM_VERSAO_DXF: dict[str, int] = {
    "AC1006": 1,
    "AC1009": 2,
    "AC1012": 3,
    "AC1014": 4,
    "AC1015": 5,
    "AC1018": 6,
    "AC1021": 7,
    "AC1024": 8,
    "AC1027": 9,
    "AC1032": 10,
}

# Códigos de triagem CAD, conforme VERTICE-entrega-cad §4.1.
CODIGO_VERSAO_ANTIGA: str = "E-CAD-01"
CODIGO_PROXY: str = "E-CAD-02"
CODIGO_UNIDADE_INDEFINIDA: str = "E-CAD-03"
CODIGO_CAMADA_PADRAO: str = "E-CAD-04"
CODIGO_XREF_AUSENTE: str = "E-CAD-05"
CODIGO_COTA_TEXTO: str = "E-CAD-06"
CODIGO_ESCALA: str = "E-CAD-07"
CODIGO_IFC_SEM_QUANTIDADE: str = "E-CAD-08"
CODIGO_IFC_SEM_ESPACO: str = "E-CAD-09"
CODIGO_IFC_REEXPORTADO: str = "E-CAD-10"

# Unidades do pacote construcao-civil-br; núcleo não inventa unidade nova.
UNIDADES_VALIDAS: frozenset[str] = frozenset(
    {"m", "m2", "m²", "m3", "m³", "kg", "un", "h", "vb", "mes", "dia", "t", "l"}
)

# Dicionário genérico para modo OFFLINE: termos que indicam serviço.
# Porquê genérico: núcleo não conhece obra; só reconhece vocabulário comum.
SERVICOS_GENERICOS: tuple[str, ...] = (
    "alvenaria",
    "chapisco",
    "reboco",
    "emboço",
    "emboco",
    "contrapiso",
    "pintura",
    "revestimento",
    "concreto",
    "argamassa",
    "impermeabilização",
    "impermeabilizacao",
    "esquadria",
    "forro",
    "piso",
    "telhado",
    "demolição",
    "demolicao",
    "instalação",
    "instalacao",
    "hidráulica",
    "hidraulica",
    "elétrica",
    "eletrica",
)

# Termos que indicam dado de cliente; nunca saem da máquina para a IA.
TERMOS_SIGILOSOS: tuple[str, ...] = (
    "santa casa",
    "cerqueira",
    "cnpj",
    "cpf",
    "paciente",
    "prontuário",
    "prontuario",
    "rua ",
    "avenida",
    "alameda",
    "travessa",
    "endereço",
    "endereco",
    "cep ",
)

# Quantidade absurda para barrar ordem de grandeza sem documento robusto.
LIMITE_ORDEM_QUANTIDADE: Decimal = Decimal("1000000")

# Quantidade mínima aceita: nada negativo entra, nem por IA nem por planilha.
QUANTIDADE_MINIMA: Decimal = Decimal("0")

# Marcador de modo degradado: deixa explícito que ninguém verificou.
MARCADOR_NAO_VERIFICADO: str = "OFFLINE — não verificado, requer confirmação do RT"

# Marcador de origem offline: preserva de onde veio o trecho.
PREFIXO_ORIGEM_OFFLINE: str = "trecho:"

# Limites de fatiamento para citação sem estourar origem ou prompt.
LIMITE_NOMES_XREF: int = 3
LIMITE_TEXTO_ORIGEM: int = 60
LIMITE_DESCRICAO_OFFLINE: int = 120
LIMITE_MINIMO_FRASE: int = 3
TAMANHO_PREFIXO_TRECHO: int = 20
ORDEM_VERSAO_DESCONHECIDA: int = 0

# Índices dos grupos da regex de quantidade (número e unidade).
GRUPO_NUMERO_QUANTIDADE: int = 1
GRUPO_UNIDADE_QUANTIDADE: int = 2

# Raiz do id_origem para número lido em documento entregue.
# Gramática completa em VERTICE-arquitetura.md §4.1.
RAIZ_ORIGEM_DOCUMENTO: str = "DOC"

# Marcador de origem que não resolve; a auditoria A11 tem de enxergar.
ORIGEM_NAO_RESOLVIVEL: str = "nao-resolvivel"
