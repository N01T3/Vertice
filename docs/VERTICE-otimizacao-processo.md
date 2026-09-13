# VÉRTICE — Otimização de Processo

**Versão:** 0.1
**Documento-pai:** `VERTICE-decisoes.md` — ADR-023 a ADR-029
**Relacionado:** `VERTICE-LINT-SUITE.md`, `VERTICE-modulo-pesquisa.md`, `VERTICE-plataforma.md`

---

## 1. Regra que governa este documento

> **Nenhuma tecnologia entra sem gargalo medido e meta numérica.**

Otimização sem medição prévia é adivinhação cara. "Alta tecnologia" é o pretexto mais comum para adicionar complexidade que ninguém pediu, e a §9 existe justamente para listar o que ficou de fora.

Cada item abaixo declara: o gargalo, a tecnologia, a meta e como verificar. Sem os quatro, não entra.

---

## 2. Onde o tempo realmente vai

Mapa do processo, com estimativa de onde está o custo hoje.

```mermaid
flowchart LR
    A["Medir o projeto"] --> B["Vincular à base"]
    B --> C["Compor o que falta"]
    C --> D["Precificar"]
    D --> E["Conferir"]
    E --> F["Documentar"]

    style A fill:#f8d7da,stroke:#a4444e,stroke-width:1.5px,color:#4a1219
    style B fill:#fff3cd,stroke:#8a6d1f,stroke-width:1.5px,color:#3d2f00
    style E fill:#f8d7da,stroke:#a4444e,stroke-width:1.5px,color:#4a1219
    style F fill:#f8d7da,stroke:#a4444e,stroke-width:1.5px,color:#4a1219
```

| Etapa | Custo hoje | Natureza |
|-------|-----------|----------|
| **Medir** | Dominante | Trabalho humano repetitivo sobre geometria |
| **Vincular à base** | Alto | Busca textual em 15 mil descrições, tentativa e erro |
| **Compor o que falta** | Médio | Pesquisa dispersa, sem registro |
| **Precificar** | Baixo | Conta simples, já resolvida |
| **Conferir** | Alto | Releitura manual, e a que existia era auto-referente |
| **Documentar** | Alto | Redigitação de dado derivado |

Três das seis etapas são trabalho que a máquina faz melhor. É onde a tecnologia entra.

---

## 3. Medição — geometria como grafo

### ADR-023 — Detecção de ambiente por ciclos em grafo planar

**Gargalo.** Identificar recinto fechado a partir de linhas soltas. Foi registrado como utopia e depois reclassificado, porque é problema resolvido — falta só o algoritmo certo.

**Tecnologia.** Construir grafo planar com os eixos de parede: interseções viram vértices, trechos viram arestas. As **faces mínimas** do grafo são os ambientes. Tolerância de encaixe para segmentos quase coincidentes; vãos de porta não quebram a face porque a parede continua.

Biblioteca de geometria computacional para operações booleanas, buffer e área; a detecção de faces é percurso de grafo, não heurística.

**Meta.** Em planta com camadas separadas, identificar ao menos 90% dos ambientes sem intervenção. Falhas viram ambiente manual, nunca ambiente errado.

**Verificação.** Conjunto de plantas reais com ambientes conferidos à mão.

### ADR-024 — Dedução por operação booleana

**Gargalo.** Somar área de parede sem descontar vãos é erro de dezenas de metros quadrados.

**Tecnologia.** Área líquida por diferença booleana entre o polígono do elemento e os polígonos de abertura, com o critério de desconto vindo da regra de medição. Nada de subtração aritmética por contagem: a geometria decide.

**Meta.** Erro abaixo de 0,5% contra medição manual em plantas de referência.

---

## 4. Vínculo à base — busca semântica local

### ADR-025 — Embeddings locais em vez de chamada de modelo

**Gargalo.** Encontrar o código certo entre ~15 mil descrições. Busca textual falha em sinônimo: quem digita "contrapiso" não acha "regularização de base".

**Tecnologia.** Modelo de embedding pequeno, rodando **na máquina**, gerando vetores das descrições da base uma vez por importação. Busca por similaridade em índice vetorial local, combinada com a busca textual existente.

**Por que isso é melhor que chamar um modelo grande:**

| | Embedding local | Chamada de LLM |
|---|---|---|
| Latência | Milissegundos | Segundos |
| Custo por busca | Zero | Recorrente |
| Funciona sem rede | Sim | Não |
| Reprodutível | Sim | Não |
| Sigilo | Nada sai da máquina | Descrição sai |

**Consequência de projeto.** Isso **reduz a dependência do classificador por IA**, que era o ponto mais frágil da arquitetura. Boa parte do que eu tinha atribuído ao LLM é, na verdade, problema de similaridade — e similaridade se resolve com vetor, não com raciocínio.

**Meta.** Código correto entre os cinco primeiros resultados em 90% das buscas, abaixo de 50 ms.

---

## 5. Recálculo — incremental por conteúdo

### ADR-026 — Endereçamento por conteúdo

**Gargalo.** Reforma muda o tempo todo. Recalcular tudo a cada revisão é o custo escondido do orçamento, e foi o problema que a indústria chinesa atacou com atualização incremental.

**Tecnologia.** Cada entrada — geometria de elemento, regra de medição, parcela de markup, preço de item — tem um hash do próprio conteúdo. O resultado guarda o hash das entradas que o produziram. Entrada com hash inalterado dispensa recálculo.

É a mesma ideia de sistema de build moderno, aplicada a orçamento. Nada de grafo de dependências em tempo de execução, que a ADR-009 já descartou: aqui é comparação de hash, que é trivial.

**Meta.** Revisão de projeto que altera 5% dos elementos recalcula no máximo 10% dos itens, abaixo de 300 ms.

**Efeito colateral valioso.** O hash prova quais entradas geraram um orçamento aprovado. Isso é rastreabilidade forte, de graça.

---

## 6. Pesquisa — paralela e progressiva

### ADR-027 — Execução concorrente com resultado progressivo

**Gargalo.** Pesquisa profunda sequencial em várias frentes e idiomas ultrapassaria facilmente dois minutos.

**Tecnologia.** Frentes executadas concorrentemente, com limite de concorrência por domínio consultado. O dossiê é **preenchido progressivamente na tela**: o usuário lê a frente normativa enquanto a de preço ainda roda.

**Meta.** Primeira geração abaixo de 90 s e incremental abaixo de 15 s, com o primeiro resultado visível em menos de 5 s.

**Princípio de interface.** Espera com resultado parcial é trabalho; espera com barra girando é ócio. A diferença não é técnica, é de percepção — e custa pouco implementar.

### ADR-028 — Saída estruturada por gramática, não por validação posterior

**Gargalo.** A arquitetura validava o JSON do modelo **depois** de recebê-lo, e descartava o que estivesse malformado. Descartar é retrabalho: gasta-se a chamada inteira para jogar fora.

**Tecnologia.** Decodificação restrita por esquema, em que o formato é imposto durante a geração. O modelo fica impedido de emitir campo numérico onde o esquema não permite.

**Consequência forte.** O esquema exige `id_origem` em todo campo numérico. O modelo fica **estruturalmente impedido de emitir valor sem origem**: não é validação posterior, é impossibilidade na geração. Regra aplicada na gramática não depende de o validador ter sido bem escrito.

A validação posterior permanece, como segunda barreira. Duas barreiras independentes é o padrão correto para regra crítica.

---

## 7. Desenvolvimento — verificar a verificação

### ADR-029 — Teste por propriedade e teste de mutação

**Gargalo.** O erro mais grave encontrado na auditoria da planilha foi uma conferência que não podia falhar. Suíte de testes sofre do mesmo mal: passa sempre, inclusive quando o código está errado.

**Tecnologia, em três frentes:**

**Teste por propriedade.** Em vez de conferir casos escolhidos a dedo, declarar invariantes e deixar a ferramenta procurar contraexemplo:

- Dobrar a quantidade dobra o custo direto do item.
- Trocar de regime move todos os preços de mão de obra na mesma direção.
- A soma dos itens é sempre igual ao total, para qualquer conjunto gerado.
- Explodir composição e somar dá o mesmo que o custo sintético, dentro da tolerância.
- Reimportar a mesma base não muda nada — idempotência.
- Dedução de vão nunca produz área negativa.

**Teste metamórfico.** Relações entre execuções, sem precisar do resultado esperado: escalar um projeto inteiro por um fator deve escalar o total pelo mesmo fator.

**Teste de mutação.** A ferramenta altera o código de propósito — troca sinal, inverte comparação, muda constante — e verifica se algum teste reprova. Mutação que sobrevive é **teste que não testa nada**.

Isso é o antagonista aplicado à própria suíte, e responde exatamente à lição da conferência auto-referente.

**Meta.** Índice de mutantes eliminados acima de 80% nos módulos de precificação, base e composição própria. Abaixo disso, a cobertura é ilusória por mais alta que seja.

**Verificação.** Portão G4 da suíte passa a incluir o índice de mutação.

### 7.1 Fuzzing do importador

O incidente da coluna de código zerada mostrou que base corrompida chega com aparência de normalidade. Geração automática de arquivos deformados — coluna faltando, tipo trocado, linha truncada, codificação inválida, valor negativo, unidade divergente — alimenta o importador.

**Critério:** nenhuma entrada deformada pode produzir importação bem-sucedida com dado errado. Ou importa certo, ou recusa com motivo.

---

## 8. Metas consolidadas

Entram no portão G5 da suíte de lint. Regressão acima de 20% reprova.

| Operação | Meta |
|----------|------|
| Busca textual na base completa | 100 ms |
| Busca semântica por similaridade | 50 ms |
| Explosão de composição de três níveis | 50 ms |
| Recálculo completo, 200 itens | 200 ms |
| Recálculo incremental após revisão | 300 ms |
| Importação de base completa | 180 s |
| Detecção de ambientes, planta média | 5 s |
| Antagonista, camada 1 | 1 s |
| Pesquisa profunda, primeira geração | 90 s |
| Pesquisa profunda, incremental | 15 s |
| Primeiro resultado visível na pesquisa | 5 s |
| Partida do aplicativo | 3 s |
| Índice de mutação no núcleo de domínio | acima de 80% |

---

## 9. Recusado

A parte mais importante. Cada item abaixo apareceria numa lista de "alta tecnologia" e **não entra**, com motivo.

| Tecnologia | Por que não |
|------------|-------------|
| Microsserviços | Aplicativo local de um usuário. Rede interna onde hoje há chamada de função é custo puro |
| Orquestração de contêineres | Não há frota. O produto roda numa estação de trabalho |
| Banco vetorial como serviço | Índice local resolve 15 mil descrições. Servidor externo quebra o funcionamento sem rede |
| Segundo motor analítico embarcado | O motor atual atende às metas da §8. Entra apenas se uma delas falhar, com medição |
| Event sourcing | Auditoria é atendida por versionamento e hash de conteúdo. Reconstruir estado por eventos é complexidade sem demanda |
| Registro em cadeia de blocos para auditoria | Auditoria de obra pública exige documento assinado e fonte rastreável, não prova criptográfica distribuída. Nenhum tribunal pede isso |
| Ajuste fino de modelo próprio | Sem volume de dados rotulados. Embedding local mais base oficial resolve o caso de uso |
| Agente autônomo que fecha o orçamento sozinho | Contraria a regra fundadora: quem propõe não valida, e quem assina é o responsável técnico |
| Tempo real colaborativo multiusuário | Fora de escopo declarado até a F4 |
| Mais uma camada de framework no front-end | Tabela virtualizada e formatação numérica não precisam disso |

**Critério comum a todos:** resolvem problema que o VÉRTICE não tem. Tecnologia boa aplicada a gargalo inexistente é dívida técnica com nome bonito.

---

## 10. Sequência de adoção

Nenhuma dessas otimizações entra antes da medição que a justifica.

| Fase | Entra | Condição |
|------|-------|----------|
| **F0** | Hash de conteúdo, fuzzing do importador, teste por propriedade | Base da corretude; barato agora, caro depois |
| **F1** | Teste de mutação, saída estruturada por gramática | Quando existir motor de cálculo e chamada de modelo |
| **F2** | Grafo planar, dedução booleana | Com a geometria em mãos |
| **F2b** | Recálculo incremental | Com duas versões de projeto para comparar |
| **F3** | Embeddings locais | Antes do classificador — pode reduzir o escopo dele |
| **F4** | Concorrência e resultado progressivo na pesquisa | Quando a latência medida justificar |

A F3 merece atenção: **implementar a busca semântica antes do classificador pode encolher o classificador**. Vale medir quanto do problema é similaridade antes de assumir que é raciocínio.

---

## 11. Testes de aceite

| # | Cenário | Esperado |
|---|---------|----------|
| O01 | Planta com ambientes fechados | 90% detectados; falha vira ambiente manual, nunca errado |
| O02 | Parede com três vãos | Área líquida por diferença booleana, erro abaixo de 0,5% |
| O03 | Busca por sinônimo não presente na descrição | Código correto entre os cinco primeiros |
| O04 | Busca semântica sem rede | Funciona normalmente |
| O05 | Revisão alterando 5% dos elementos | No máximo 10% dos itens recalculados |
| O06 | Hash de entrada inalterado | Nenhum recálculo disparado |
| O07 | Modelo tentando emitir campo numérico | Impedido pela gramática, antes da validação |
| O08 | Mutante inserido no cálculo de markup | Ao menos um teste reprova |
| O09 | Índice de mutação abaixo de 80% | Portão G4 acusa |
| O10 | Base com coluna corrompida gerada por fuzzing | Recusa com motivo, jamais importação silenciosa |
| O11 | Propriedade de escala do projeto | Total escala pelo mesmo fator |
| O12 | Pesquisa profunda em execução | Primeiro resultado visível em menos de 5 s |

---

## 12. Histórico

| Versão | Data | Alteração |
|--------|------|-----------|
| 0.1 | 13/09/2026 | Documento inicial. ADR-023 a ADR-029, cada uma ligada a gargalo medido. Lista de tecnologias recusadas com motivo. A regra de a IA não produzir número passa de validação posterior a restrição de gramática |
