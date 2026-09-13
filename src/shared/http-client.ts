// Porquê toda chamada de rede mora aqui: VF-01 de VERTICE-LINT-SUITE.md —
// nenhuma chamada de rede fora de shared/http-client.ts. Telas pedem
// dado a este arquivo; nenhuma tela conhece o sidecar diretamente.

export interface ItemBusca {
  codigo: string;
  tipo: "INSUMO" | "COMPOSICAO";
  descricao: string;
  grupo: string | null;
  unidade: string;
  id_base: number;
}

export interface NoExplosao {
  codigo: string;
  tipo: "INSUMO" | "COMPOSICAO";
  descricao: string;
  unidade: string;
  coeficiente_acumulado: string;
  custo_unitario_centavos: number | null;
  custo_total_centavos: number | null;
  filhos: NoExplosao[];
}

export interface Explosao {
  codigo_raiz: string;
  uf: string;
  regime: "ONERADO" | "DESONERADO" | "SEM_ENCARGOS";
  custo_total_centavos: number | null;
  completo: boolean;
  arvore: NoExplosao;
}

export interface ParcelasBdi {
  administracao_central: string;
  seguro_garantia: string;
  risco: string;
  despesas_financeiras: string;
  lucro: string;
  pis: string;
  cofins: string;
  iss: string;
  cprb: string;
}

export interface Orcamento {
  id: number;
  identificacao: string;
  regime: Explosao["regime"];
  uf: string;
  id_base: number;
  data_base: string;
  id_origem: string;
}

export interface Bdi {
  id_orcamento: number;
  parcelas: ParcelasBdi;
  municipio_iss: string;
  base_iss: string;
  justificativa: string | null;
  id_fonte: number | null;
  bdi_percentual: string;
  faixa_tcu:
    | "ABAIXO_1_QUARTIL"
    | "ENTRE_1_QUARTIL_E_MEDIO"
    | "ENTRE_MEDIO_E_3_QUARTIL"
    | "ACIMA_3_QUARTIL";
  exige_justificativa: boolean;
  alertas: string[];
}

interface SessaoDev {
  token: string;
  porta: number;
}

// Porquê cache em módulo, não em cada chamada: a sessão do sidecar não
// muda enquanto a janela está aberta — buscar de novo a cada requisição
// seria uma chamada de rede a mais por chamada de rede.
let sessaoEmCache: Promise<SessaoDev> | null = null;

function obterSessao(): Promise<SessaoDev> {
  sessaoEmCache ??= fetch("/dev-session.json").then((resposta) => {
    if (!resposta.ok) {
      throw new Error(
        "sidecar não encontrado: dev-session.json ausente ou o processo não subiu",
      );
    }
    return resposta.json() as Promise<SessaoDev>;
  });
  return sessaoEmCache;
}

async function pedirAoSidecar<T>(
  caminho: string,
  opcoes?: { metodo?: "POST"; corpo?: unknown },
): Promise<T> {
  const sessao = await obterSessao();
  const resposta = await fetch(`http://127.0.0.1:${sessao.porta}${caminho}`, {
    method: opcoes?.metodo ?? "GET",
    headers: {
      "X-Vertice-Token": sessao.token,
      ...(opcoes?.corpo !== undefined ? { "Content-Type": "application/json" } : {}),
    },
    body: opcoes?.corpo !== undefined ? JSON.stringify(opcoes.corpo) : undefined,
  });
  if (!resposta.ok) {
    const corpo = await resposta.text();
    throw new Error(`sidecar respondeu ${resposta.status}: ${corpo}`);
  }
  return resposta.json() as Promise<T>;
}

/** `GET /sinapi/buscar` — busca textual no catálogo importado. */
export function buscar(termo: string, idBase?: number): Promise<ItemBusca[]> {
  const parametros = new URLSearchParams({ termo });
  if (idBase !== undefined) parametros.set("id_base", String(idBase));
  return pedirAoSidecar(`/sinapi/buscar?${parametros}`);
}

/** `GET /sinapi/composicao/{codigo}/explodir` — soma custo, com a árvore. */
export function explodir(
  codigo: string,
  uf: string,
  regime: Explosao["regime"],
  idBase?: number,
): Promise<Explosao> {
  const parametros = new URLSearchParams({ uf, regime });
  if (idBase !== undefined) parametros.set("id_base", String(idBase));
  return pedirAoSidecar(
    `/sinapi/composicao/${encodeURIComponent(codigo)}/explodir?${parametros}`,
  );
}

/** `POST /orcamento` — cadastra regime, base e UF (imutáveis após, §2.2). */
export function criarOrcamento(dados: {
  identificacao: string;
  regime: Orcamento["regime"];
  uf: string;
  data_base: string;
  id_base?: number;
}): Promise<Orcamento> {
  return pedirAoSidecar("/orcamento", { metodo: "POST", corpo: dados });
}

/** `GET /orcamento/{id}` — lê o orçamento cadastrado. */
export function obterOrcamento(idOrcamento: number): Promise<Orcamento> {
  return pedirAoSidecar(`/orcamento/${idOrcamento}`);
}

/** `POST /orcamento/{id}/bdi` — grava as parcelas, devolve o percentual. */
export function salvarBdi(
  idOrcamento: number,
  dados: {
    parcelas: ParcelasBdi;
    municipio_iss: string;
    base_iss: string;
    justificativa?: string;
    id_fonte?: number;
  },
): Promise<Bdi> {
  return pedirAoSidecar(`/orcamento/${idOrcamento}/bdi`, { metodo: "POST", corpo: dados });
}

/** `GET /orcamento/{id}/bdi` — relê as parcelas, recalcula o percentual. */
export function obterBdi(idOrcamento: number): Promise<Bdi> {
  return pedirAoSidecar(`/orcamento/${idOrcamento}/bdi`);
}
