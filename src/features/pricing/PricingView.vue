<script setup lang="ts">
// Porquê estado local, sem store: mesma razão de SearchView — uma tela,
// um propósito. Loja global entra só quando duas telas precisarem do
// mesmo orçamento ao mesmo tempo (YAGNI documentado).
import { reactive, ref } from "vue";
import {
  criarOrcamento,
  obterBdi,
  salvarBdi,
  type Bdi,
  type Orcamento,
  type ParcelasBdi,
} from "../../shared/http-client";

const identificacao = ref("");
const regime = ref<Orcamento["regime"]>("ONERADO");
const uf = ref("SP");
const dataBase = ref("2026-08");

const orcamentoAtual = ref<Orcamento | null>(null);
const carregandoOrcamento = ref(false);
const erroOrcamento = ref<string | null>(null);

const parcelas = reactive<ParcelasBdi>({
  administracao_central: "0.0401",
  seguro_garantia: "0.0032",
  risco: "0.0050",
  despesas_financeiras: "0.0102",
  lucro: "0.0664",
  pis: "0.0065",
  cofins: "0.0300",
  iss: "0.0500",
  cprb: "0",
});
const municipioIss = ref("");
const baseIss = ref("1.00");

const bdiAtual = ref<Bdi | null>(null);
const carregandoBdi = ref(false);
const erroBdi = ref<string | null>(null);

const CAMPOS_DE_PARCELA: { chave: keyof ParcelasBdi; rotulo: string }[] = [
  { chave: "administracao_central", rotulo: "Administração central" },
  { chave: "seguro_garantia", rotulo: "Seguro e garantia" },
  { chave: "risco", rotulo: "Risco" },
  { chave: "despesas_financeiras", rotulo: "Despesas financeiras" },
  { chave: "lucro", rotulo: "Lucro" },
  { chave: "pis", rotulo: "PIS" },
  { chave: "cofins", rotulo: "COFINS" },
  { chave: "iss", rotulo: "ISS" },
  { chave: "cprb", rotulo: "CPRB" },
];

async function criar(): Promise<void> {
  if (!identificacao.value.trim()) return;
  carregandoOrcamento.value = true;
  erroOrcamento.value = null;
  bdiAtual.value = null;
  try {
    orcamentoAtual.value = await criarOrcamento({
      identificacao: identificacao.value,
      regime: regime.value,
      uf: uf.value,
      data_base: dataBase.value,
    });
  } catch (erro) {
    erroOrcamento.value = erro instanceof Error ? erro.message : String(erro);
  } finally {
    carregandoOrcamento.value = false;
  }
}

async function salvar(): Promise<void> {
  if (!orcamentoAtual.value) return;
  carregandoBdi.value = true;
  erroBdi.value = null;
  try {
    bdiAtual.value = await salvarBdi(orcamentoAtual.value.id, {
      parcelas: { ...parcelas },
      municipio_iss: municipioIss.value,
      base_iss: baseIss.value,
    });
  } catch (erro) {
    erroBdi.value = erro instanceof Error ? erro.message : String(erro);
  } finally {
    carregandoBdi.value = false;
  }
}

async function reler(): Promise<void> {
  if (!orcamentoAtual.value) return;
  carregandoBdi.value = true;
  erroBdi.value = null;
  try {
    bdiAtual.value = await obterBdi(orcamentoAtual.value.id);
  } catch (erro) {
    erroBdi.value = erro instanceof Error ? erro.message : String(erro);
  } finally {
    carregandoBdi.value = false;
  }
}

function emPercentual(texto: string): string {
  return `${(Number(texto) * 100).toFixed(2)}%`;
}
</script>

<template>
  <section class="precificacao">
    <h1>VÉRTICE — orçamento e BDI</h1>

    <form v-if="!orcamentoAtual" class="precificacao__form" @submit.prevent="criar">
      <input
        v-model="identificacao"
        type="text"
        placeholder="identificação do orçamento"
        autofocus
      />
      <select v-model="regime">
        <option value="ONERADO">Onerado</option>
        <option value="DESONERADO">Desonerado</option>
        <option value="SEM_ENCARGOS">Sem encargos</option>
      </select>
      <select v-model="uf">
        <option value="SP">SP</option>
        <option value="RJ">RJ</option>
        <option value="MG">MG</option>
        <option value="DF">DF</option>
      </select>
      <input v-model="dataBase" type="text" placeholder="AAAA-MM" />
      <button type="submit" :disabled="carregandoOrcamento">Criar orçamento</button>
    </form>

    <p v-if="erroOrcamento" class="precificacao__erro">{{ erroOrcamento }}</p>

    <div v-if="orcamentoAtual" class="precificacao__orcamento">
      <p>
        <strong>{{ orcamentoAtual.identificacao }}</strong>
        — {{ orcamentoAtual.regime }}, {{ orcamentoAtual.uf }}
      </p>

      <form class="precificacao__parcelas" @submit.prevent="salvar">
        <label v-for="campo in CAMPOS_DE_PARCELA" :key="campo.chave">
          {{ campo.rotulo }}
          <input v-model="parcelas[campo.chave]" type="text" />
        </label>
        <label>
          Município (ISS)
          <input v-model="municipioIss" type="text" />
        </label>
        <label>
          Base do ISS
          <input v-model="baseIss" type="text" />
        </label>
        <div class="precificacao__acoes">
          <button type="submit" :disabled="carregandoBdi">Salvar BDI</button>
          <button type="button" :disabled="carregandoBdi" @click="reler">
            Reler do banco
          </button>
        </div>
      </form>

      <p v-if="erroBdi" class="precificacao__erro">{{ erroBdi }}</p>

      <div v-if="bdiAtual" class="precificacao__resultado">
        <p>
          BDI: <strong>{{ emPercentual(bdiAtual.bdi_percentual) }}</strong>
          ({{ bdiAtual.faixa_tcu }})
        </p>
        <p v-if="bdiAtual.exige_justificativa">
          Acima do 3º quartil do TCU — exportação exige justificativa escrita.
        </p>
        <ul v-if="bdiAtual.alertas.length">
          <li v-for="alerta in bdiAtual.alertas" :key="alerta">{{ alerta }}</li>
        </ul>
      </div>
    </div>
  </section>
</template>

<style scoped>
.precificacao {
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem;
  font-family: system-ui, sans-serif;
}
.precificacao__form,
.precificacao__acoes {
  display: flex;
  gap: 0.5rem;
  margin-block: 1rem;
  flex-wrap: wrap;
}
.precificacao__parcelas {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-block: 1rem;
}
.precificacao__parcelas label {
  display: flex;
  flex-direction: column;
  font-size: 0.85rem;
  gap: 0.2rem;
}
.precificacao__erro {
  color: #a4444e;
}
.precificacao__resultado {
  margin-top: 1.5rem;
  padding: 1rem;
  border: 1px solid #cfe2ff;
  border-radius: 6px;
}
</style>
