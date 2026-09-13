"""Formato de saída do sidecar — não é o tipo do domínio.

Porquê: `arquitetura.md` §3 dá a `api` o segredo de formato de
resposta. Se a rota devolvesse o dataclass do domínio direto, mudar
uma exigência do domínio quebraria o contrato do §4.4 sem ninguém
perceber — a tradução aqui é o que impede isso.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from core.pricing.bdi import FaixaTcu, ParcelasBdi, Regime
from core.pricing.types import Orcamento, RegistroBdi
from core.reference_base.query_results import (
    NoExplosao,
    ResultadoBusca,
    ResultadoExplosao,
)


class ItemBuscaResposta(BaseModel):
    """Uma linha da resposta de `GET /sinapi/buscar`."""

    codigo: str
    tipo: str
    descricao: str
    grupo: str | None
    unidade: str
    id_base: int

    @staticmethod
    def de_dominio(item: ResultadoBusca) -> ItemBuscaResposta:
        """Traduz o resultado de busca do domínio para o formato de rede."""
        return ItemBuscaResposta(
            codigo=item.codigo,
            tipo=item.tipo,
            descricao=item.descricao,
            grupo=item.grupo,
            unidade=item.unidade,
            id_base=item.id_base,
        )


class NoExplosaoResposta(BaseModel):
    """Um nó da árvore de `GET /sinapi/composicao/{codigo}/explodir`."""

    codigo: str
    tipo: str
    descricao: str
    unidade: str
    coeficiente_acumulado: str
    custo_unitario_centavos: int | None
    custo_total_centavos: int | None
    filhos: list[NoExplosaoResposta]

    @staticmethod
    def de_dominio(no: NoExplosao) -> NoExplosaoResposta:
        """Traduz um nó, recursivamente, filho por filho."""
        return NoExplosaoResposta(
            codigo=no.codigo,
            tipo=no.tipo,
            descricao=no.descricao,
            unidade=no.unidade,
            coeficiente_acumulado=no.coeficiente_acumulado,
            custo_unitario_centavos=no.custo_unitario_centavos,
            custo_total_centavos=no.custo_total_centavos,
            filhos=[NoExplosaoResposta.de_dominio(filho) for filho in no.filhos],
        )


class ExplosaoResposta(BaseModel):
    """A resposta completa de `GET /sinapi/composicao/{codigo}/explodir`."""

    codigo_raiz: str
    uf: str
    regime: str
    custo_total_centavos: int | None
    completo: bool
    arvore: NoExplosaoResposta

    @staticmethod
    def de_dominio(resultado: ResultadoExplosao) -> ExplosaoResposta:
        """Traduz o resultado de explosão do domínio para o formato de rede."""
        return ExplosaoResposta(
            codigo_raiz=resultado.codigo_raiz,
            uf=resultado.uf,
            regime=resultado.regime,
            custo_total_centavos=resultado.custo_total_centavos,
            completo=resultado.completo,
            arvore=NoExplosaoResposta.de_dominio(resultado.arvore),
        )


class OrcamentoRequisicao(BaseModel):
    """Corpo de `POST /orcamento` — regime, base e UF, fixados na criação."""

    identificacao: str
    regime: Regime
    uf: str
    data_base: str
    id_base: int | None = None


class OrcamentoResposta(BaseModel):
    """Um orçamento cadastrado, com o `id` que as rotas de BDI referenciam."""

    id: int
    identificacao: str
    regime: Regime
    uf: str
    id_base: int
    data_base: str
    id_origem: str

    @staticmethod
    def de_dominio(id_orcamento: int, orcamento: Orcamento) -> OrcamentoResposta:
        """Traduz o orçamento do domínio, com o `id` que o domínio não guarda."""
        return OrcamentoResposta(
            id=id_orcamento,
            identificacao=orcamento.identificacao,
            regime=orcamento.regime,
            uf=orcamento.uf,
            id_base=orcamento.id_base,
            data_base=orcamento.data_base,
            id_origem=orcamento.id_origem,
        )


class ParcelasBdiPayload(BaseModel):
    """As nove parcelas do BDI, cada uma como texto decimal (arquitetura §5.1).

    Porquê texto, não `Decimal` direto no campo: um `float` JSON
    (`0.0401`) chegando pelo parser padrão do Pydantic passa por
    ponto flutuante antes de virar `Decimal` — exatamente o que VD-01
    proíbe. Texto elimina essa rota; a conversão exata fica explícita
    em `para_dominio`.

    Porquê um único tipo para pedido e resposta: é a mesma forma nos
    dois sentidos — só muda quem preenche o campo, não o que ele significa.
    """

    administracao_central: str
    seguro_garantia: str
    risco: str
    despesas_financeiras: str
    lucro: str
    pis: str
    cofins: str
    iss: str
    cprb: str

    def para_dominio(self) -> ParcelasBdi:
        """Converte o payload de rede para o tipo que `calcular_bdi` usa."""
        return ParcelasBdi(
            administracao_central=Decimal(self.administracao_central),
            seguro_garantia=Decimal(self.seguro_garantia),
            risco=Decimal(self.risco),
            despesas_financeiras=Decimal(self.despesas_financeiras),
            lucro=Decimal(self.lucro),
            pis=Decimal(self.pis),
            cofins=Decimal(self.cofins),
            iss=Decimal(self.iss),
            cprb=Decimal(self.cprb),
        )

    @staticmethod
    def de_dominio(parcelas: ParcelasBdi) -> ParcelasBdiPayload:
        """Traduz as parcelas do domínio para o formato de rede."""
        return ParcelasBdiPayload(
            administracao_central=str(parcelas.administracao_central),
            seguro_garantia=str(parcelas.seguro_garantia),
            risco=str(parcelas.risco),
            despesas_financeiras=str(parcelas.despesas_financeiras),
            lucro=str(parcelas.lucro),
            pis=str(parcelas.pis),
            cofins=str(parcelas.cofins),
            iss=str(parcelas.iss),
            cprb=str(parcelas.cprb),
        )


class BdiRequisicao(BaseModel):
    """Corpo de `POST /orcamento/{id}/bdi` — as parcelas mais o rastro de ISS."""

    parcelas: ParcelasBdiPayload
    municipio_iss: str
    base_iss: str
    justificativa: str | None = None
    id_fonte: int | None = None


class BdiResposta(BaseModel):
    """O BDI salvo, mais o percentual recalculado — nunca guardado (§3.5)."""

    id_orcamento: int
    parcelas: ParcelasBdiPayload
    municipio_iss: str
    base_iss: str
    justificativa: str | None
    id_fonte: int | None
    bdi_percentual: str
    faixa_tcu: FaixaTcu
    exige_justificativa: bool
    alertas: list[str]

    @staticmethod
    def de_dominio(
        registro: RegistroBdi,
        bdi_percentual: Decimal,
        faixa_tcu: FaixaTcu,
        exige_justificativa: bool,
        alertas: list[str],
    ) -> BdiResposta:
        """Traduz o registro salvo mais o percentual recém-calculado."""
        return BdiResposta(
            id_orcamento=registro.id_orcamento,
            parcelas=ParcelasBdiPayload.de_dominio(registro.parcelas),
            municipio_iss=registro.municipio_iss,
            base_iss=str(registro.base_iss),
            justificativa=registro.justificativa,
            id_fonte=registro.id_fonte,
            bdi_percentual=str(bdi_percentual),
            faixa_tcu=faixa_tcu,
            exige_justificativa=exige_justificativa,
            alertas=alertas,
        )
