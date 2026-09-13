<script setup lang="ts">
// Porquê abas aqui, não em cada tela: navegação é decisão do app, não
// de uma feature — SearchView e PricingView não sabem uma da outra.
import { ref } from "vue";
import SearchView from "./features/search/SearchView.vue";
import PricingView from "./features/pricing/PricingView.vue";

const telaAtual = ref<"busca" | "precificacao">("busca");
</script>

<template>
  <nav class="abas">
    <button :class="{ ativa: telaAtual === 'busca' }" @click="telaAtual = 'busca'">
      Busca
    </button>
    <button
      :class="{ ativa: telaAtual === 'precificacao' }"
      @click="telaAtual = 'precificacao'"
    >
      Orçamento / BDI
    </button>
  </nav>
  <SearchView v-if="telaAtual === 'busca'" />
  <PricingView v-else />
</template>

<style scoped>
.abas {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem 0;
  font-family: system-ui, sans-serif;
}
.abas button {
  padding: 0.4rem 0.9rem;
  border: 1px solid #cfe2ff;
  border-radius: 6px 6px 0 0;
  background: #f4f8ff;
  cursor: pointer;
}
.abas button.ativa {
  background: white;
  font-weight: 600;
}
</style>
