# VÉRTICE — REGRAS

Protocolo de desenvolvimento. Documento vivo, atualizado apenas quando uma regra nova é acordada, um padrão muda, uma lacuna é identificada ou um incidente real ocorre.

**Versão:** 1.4
**Vigência:** a partir de 13/09/2026

---

## 1. Hierarquia de autoridade

Quando houver conflito, vence quem está mais acima:

1. Segurança do usuário final e responsabilidade técnica — orçamento errado tem consequência legal.
2. Este documento.
3. Documentos de arquitetura e módulos.
4. Padrões do ecossistema de cada linguagem.
5. Preferência pessoal.

**Documento prevalece sobre preferência.** Se a preferência for melhor, muda-se o documento primeiro.

---

## 2. Fluxo inviolável de trabalho

### 2.1 Antes de implementar

```text
analisar  →  derivar testes  →  executar todos  →  implementar
```

Nunca implementar sem análise completa anterior. Nunca perguntar sobre um problema antes de tê-lo analisado de forma independente.

### 2.2 Diante de um problema

1. Analisar sozinho, sem perguntar.
2. Executar os testes e mapear **todos** os bugs, não o primeiro.
3. Apresentar cada bug com severidade: crítica, alta, média, baixa.
4. Perguntar qual corrigir e **aguardar confirmação** antes de agir.

Corrigir o bug óbvio antes de mapear o conjunto esconde a causa raiz.

### 2.3 Laço de qualidade

Ordem fixa, sempre a mesma:

```text
LINT mede  →  ANTAGONISTA especifica  →  DEV decide  →  CORRECT conserta  →  LINT confirma
```

O lint nunca alimenta o Correct direto. Saída de linter é achado bruto; o Correct precisa de defeito especificado, com teste que reproduz e escopo delimitado.

**Nada nesse laço interrompe o trabalho.** Toda objeção termina em `CORRIGIDA`, `REFUTADA`, `ACEITA_COM_RISCO` ou `UTOPIA`, e sempre há ao menos uma saída disponível.

### 2.4 Quando o conserto não converge

Corrigir A quebra B, corrigir B quebra A, ou o escopo cresce a cada rodada: isso é divergência, não bug difícil. O Correct retorna ao último estado estável e a objeção vira **utopia** — ideal correto que o sistema atual não alcança a custo aceitável, registrado com causa medida e condição de reabertura.

Utopia não é desistência: a objeção continua procedente e volta quando a premissa mudar. Procedimento completo em `VERTICE-modulo-correct.md` §3 e §4.

### 2.5 Construção por agentes

Quando a implementação for conduzida por agente de IA, vale `VERTICE-AGENTS.md` além deste documento. Dois pontos não negociáveis: a tarefa tem critério de pronto verificável por comando, e **o agente não declara pronto — o portão declara**.

### 2.6 Escopo cirúrgico

- Nunca misturar dois padrões no mesmo arquivo.
- Nunca assumir quando um detalhe pode mudar o resultado.
- Uma correção resolve um problema. Refatoração oportunista entra em commit separado.

---

## 3. Derivação de testes

Todo teste tem **entrada definida, comportamento esperado preciso e resultado verificável**. Aprovação sem evidência é proibida.

Técnicas obrigatórias, com cobertura proporcional à complexidade:

| Técnica | Aplicação no VÉRTICE |
|---------|----------------------|
| Partição de equivalência | Regimes onerado, desonerado, sem encargos |
| Valor-limite | BDI nos quartis do TCU; tolerância de arredondamento na explosão |
| Tabela de decisão | Os três gatilhos de CPU contra situação do código na base |
| Fluxo positivo e negativo | Importação de base válida e corrompida |
| Borda | Composição sem preço na UF; orçamento sem itens; desenho sem camadas |
| Estado e sequência | Ciclo de vida da CPU; ciclo da objeção do antagonista |
| Regressão | Reconstrução do orçamento do CME após qualquer mudança no motor |
| Idempotência | Reimportar a mesma base não duplica nem altera |
| Efeito colateral | Corrigir escala não pode alterar orçamento já fechado |

### 3.1 Dimensões de risco

Todas percorridas em cada entrega: lógica, contrato externo, regressão, segurança, desempenho, interface, conteúdo, comportamento de JavaScript, tratamento de erro e perspectiva do usuário final.

### 3.2 Testes-âncora

Três números que **nunca podem mudar** sem decisão explícita registrada. Qualquer alteração neles reprova a entrega:

| Âncora | Valor | O que prova |
|--------|------:|-------------|
| Reconstrução do CME | R$ 141.194,42 | O motor inteiro, ponta a ponta |
| BDI do CME | 23,6245% | A fórmula de BDI |
| SINAPI 87622, SP, onerado | R$ 40,63 | O importador e a seleção de regime |

---

## 4. Padrões de código

### 4.1 Idioma

**Português no identificador, inglês no caminho.** Variável, função, classe, mensagem de commit e comentário: português. Nome de arquivo e de pasta: inglês, por padrão — é o que faz o repositório legível para qualquer ferramenta e qualquer colaborador que não leia português, sem tocar no vocabulário do domínio, que é o que importa ficar em português. Comentário explica **o porquê**, nunca o quê.

Exceções: palavras-chave e API da linguagem ou do framework; e um arquivo de dado cujo nome é a própria chave referenciada por outro arquivo do mesmo pacote (ex.: `regra: chapisco_base` em `chapisco_base.yaml`) — remonta o arquivo sem remontar a chave.

```python
# certo
def calcular_bdi(parcelas: ParcelasBdi) -> Decimal:
    # Tributos sobre faturamento dividem, não somam: o preço precisa
    # crescer o bastante para que a receita líquida feche.
    ...

# errado
def calculate_bdi(params):
    ...
```

Arquivos e pastas em kebab-case inglês no front-end; snake_case inglês no Python.

### 4.2 Proibições

- God class ou god object.
- Número mágico e valor codificado direto — usar constante nomeada.
- Responsabilidades misturadas na mesma unidade.
- Argumento ou retorno implícito: assinatura explícita, sempre.
- `float` em qualquer valor monetário ou coeficiente. **Usar `Decimal`.** Orçamento com erro de ponto flutuante é orçamento errado.
- `except` sem tipo, ou que engole o erro sem registrar.
- Abstração sem dois casos concretos — ver ADR-006.

### 4.3 Front-end

- Scripts ao final do `<body>`.
- Animação apenas em `transform` e `opacity`.
- Contraste mínimo de 4,5:1, WCAG AA.
- Diagramas Mermaid com `fill`, `stroke` e **`color` explícitos**. Sem `color`, o tema escuro do renderizador mantém o texto claro sobre o fundo claro definido — incidente real de 13/09/2026.
- Nenhuma chamada de rede fora da camada de cliente HTTP.

### 4.4 Contratos externos invioláveis

A partir da F1, não mudam de assinatura sem versionamento explícito:

- `GET /sinapi/buscar`
- `GET /sinapi/composicao/{codigo}/explodir`

---

## 5. Regras de domínio inegociáveis

Estas não são preferência de engenharia. São o que separa o produto de um gerador de números.

1. **A IA nunca produz número mágico.** Todo campo numérico carrega `id_origem` resolvível até geometria medida, base importada, entrada do usuário ou achado de pesquisa validado. Não existe configuração que desligue.
2. **Plausibilidade não qualifica número; origem qualifica.** Valor que parece razoável e não tem documento é rejeitado igual a valor absurdo.
3. **Quem propõe não valida.** Classificador, motor, antagonista e RT são papéis separados.
4. **CPU só nasce com autorização explícita e justificativa escrita.**
5. **Item sem base técnica não é precificado por estimativa** — vai para pendências, fora do total.
6. **Regime e data-base aparecem em todo cabeçalho exportado.**
7. **Nenhum valor sem fonte.** Fonte sem data-base é fonte incompleta.
8. **Silêncio do antagonista não é aprovação.**

---

## 6. Git

- Commit a cada funcionalidade ou correção concluída, e ao final de cada sessão.
- Formato: `tipo(escopo): descrição em português`
- Tipos: `feat`, `fix`, `refactor`, `style`, `docs`, `test`, `chore`
- Escopo é o módulo: `sinapi`, `cpu`, `cad`, `pricing`, `antagonist`, `infra`, `ui`

```text
feat(sinapi): recuperar código de composição pela aba Analítico
fix(pricing): corrigir divisor de tributos na fórmula do BDI
test(cpu): cobrir trava bidirecional de anti-duplicidade
```

Revisão antes do commit cobre: contratos externos, idioma, segurança e regressão entre telas.

---

## 7. Encerramento de estágio

Nenhum estágio é declarado concluído sem:

1. Suíte de lint completa aprovada — `VERTICE-LINT-SUITE.md`.
2. Testes-âncora reproduzindo os três valores da §3.2.
3. Sessão de revisão adversarial: tentar quebrar a entrega, não confirmar que funciona.
3.1. Revisão do registro de utopias: alguma condição de reabertura ocorreu?
4. Relatório de sessão.
5. Documentos atualizados quando a implementação divergir da especificação. **A especificação cede à realidade, mas por escrito.**

### 7.1 Relatório de sessão

Obrigatório ao final de cada sessão de trabalho:

- O que foi implementado.
- Decisões tomadas e alternativas descartadas, com motivo.
- Bugs encontrados, com severidade e situação.
- Divergências entre implementação e especificação.
- O que ficou pendente e por quê.
- Riscos novos identificados.
- Divergências de laço ocorridas, com rodadas e métricas.
- Utopias criadas ou reabertas no estágio.

---

## 8. Colaboração

- Perguntar proativamente para ganhar especificidade **antes** de implementar.
- Apontar riscos, alternativas e boas práticas mesmo sem solicitação.
- Discordar quando houver motivo técnico. Concordância automática não tem valor.
- Nunca declarar pronto o que não foi verificado com evidência.

---

## 9. Histórico

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.4 | 13/09/2026 | §4.1 esclarece: nome de arquivo e pasta em inglês por padrão; identificador interno continua em português. Lista de escopo de commit atualizada (`pricing`, `antagonist`) |
| 1.3 | 13/09/2026 | §2.5 remete ao protocolo de construção por agentes |
| 1.2 | 13/09/2026 | Regra 1 reformulada para cadeia de proveniência. Regra 2 passa a tratar plausibilidade como não qualificadora |
| 1.1 | 13/09/2026 | Laço lint → antagonista → Correct formalizado na §2.3. Tratamento de divergência e utopia na §2.4. Relatório de sessão passa a registrar divergências e utopias |
| 1.0 | 13/09/2026 | Documento inicial. Incorpora o incidente de contraste em Mermaid (§4.3) e a proibição de `float` em valor monetário (§4.2), ambos originados em problemas reais |
