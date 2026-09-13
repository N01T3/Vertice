<script setup lang="ts">
// Porquê estado local, sem store: uma tela, um propósito — buscar e
// explodir. Loja de estado global entra quando duas telas precisarem
// do mesmo dado ao mesmo tempo, não antes (YAGNI documentado).
import { ref } from "vue";
import { buscar, explodir, type Explosao, type ItemBusca } from "../../shared/http-client";

const termo = ref("");
const uf = ref("SP");
const regime = ref<Explosao["regime"]>("ONERADO");

const resultados = ref<ItemBusca[]>([]);
const carregandoBusca = ref(false);
const erroBusca = ref<string | null>(null);

const explosaoAtual = ref<Explosao | null>(null);
const carregandoExplosao = ref(false);
const erroExplosao = ref<string | null>(null);

async function executarBusca(): Promise<void> {
  if (!termo.value.trim()) return;
  carregandoBusca.value = true;
  erroBusca.value = null;
  explosaoAtual.value = null;
  try {
    resultados.value = await buscar(termo.value);
  } catch (erro) {
    erroBusca.value = erro instanceof Error ? erro.message : String(erro);
  } finally {
    carregandoBusca.value = false;
  }
}

async function explodirItem(codigo: string): Promise<void> {
  carregandoExplosao.value = true;
  erroExplosao.value = null;
  try {
    explosaoAtual.value = await explodir(codigo, uf.value, regime.value);
  } catch (erro) {
    erroExplosao.value = erro instanceof Error ? erro.message : String(erro);
  } finally {
    carregandoExplosao.value = false;
  }
}

function emReais(centavos: number | null): string {
  if (centavos === null) return "— sem preço na UF";
  return (centavos / 100).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
</script>

<template>
  <section class="busca">
    <h1>VÉRTICE — busca na base</h1>

    <form class="busca__form" @submit.prevent="executarBusca">
      <input
        v-model="termo"
        type="text"
        placeholder="buscar por descrição ou código..."
        autofocus
      />
      <select v-model="uf">
        <option value="SP">SP</option>
        <option value="RJ">RJ</option>
        <option value="MG">MG</option>
        <option value="DF">DF</option>
      </select>
      <select v-model="regime">
        <option value="ONERADO">Onerado</option>
        <option value="DESONERADO">Desonerado</option>
        <option value="SEM_ENCARGOS">Sem encargos</option>
      </select>
      <button type="submit" :disabled="carregandoBusca">Buscar</button>
    </form>

    <p v-if="erroBusca" class="busca__erro">{{ erroBusca }}</p>

    <table v-if="resultados.length" class="busca__tabela">
      <thead>
        <tr>
          <th>Código</th>
          <th>Tipo</th>
          <th>Descrição</th>
          <th>Unidade</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in resultados" :key="`${item.tipo}:${item.codigo}`">
          <td>{{ item.codigo }}</td>
          <td>{{ item.tipo }}</td>
          <td>{{ item.descricao }}</td>
          <td>{{ item.unidade }}</td>
          <td>
            <button
              v-if="item.tipo === 'COMPOSICAO'"
              @click="explodirItem(item.codigo)"
              :disabled="carregandoExplosao"
            >
              Explodir
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <p v-if="erroExplosao" class="busca__erro">{{ erroExplosao }}</p>

    <div v-if="explosaoAtual" class="busca__explosao">
      <h2>
        {{ explosaoAtual.codigo_raiz }} em {{ explosaoAtual.uf }},
        {{ explosaoAtual.regime }}
      </h2>
      <p>
        Custo total: <strong>{{ emReais(explosaoAtual.custo_total_centavos) }}</strong>
        <span v-if="!explosaoAtual.completo"> — incompleto: falta preço em algum item</span>
      </p>
    </div>
  </section>
</template>

<style scoped>
.busca {
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem;
  font-family: system-ui, sans-serif;
}
.busca__form {
  display: flex;
  gap: 0.5rem;
  margin-block: 1rem;
}
.busca__form input {
  flex: 1;
}
.busca__tabela {
  width: 100%;
  border-collapse: collapse;
}
.busca__tabela th,
.busca__tabela td {
  text-align: left;
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid #ddd;
}
.busca__erro {
  color: #a4444e;
}
.busca__explosao {
  margin-top: 1.5rem;
  padding: 1rem;
  border: 1px solid #cfe2ff;
  border-radius: 6px;
}
</style>
