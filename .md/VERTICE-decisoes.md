# VÉRTICE — Registro de Decisões

Registro de decisões arquiteturais no formato contexto, decisão, consequência e gatilho de revisão. Decisão aceita não é editada: é superada por decisão nova que a referencia.

**Versão:** 1.0
**Data:** 13/09/2026
**Relacionado:** `VERTICE-arquitetura.md`, `VERTICE-fundamentos.md`

Cada decisão declara o **nível de evidência** conforme `VERTICE-fundamentos.md` §1. Nível 4 ou 5 exige gatilho de revisão.

---

## ADR-001 — Nome: VÉRTICE

**Contexto.** Precisa evocar engenharia, orçamento e tecnologia.
**Decisão.** VÉRTICE.
**Consequência.** Verificar INPI e domínio antes de investir em identidade visual.
**Revisão:** antes da F1.

## ADR-002 — Shell desktop: Tauri 2 — REABERTA

**Contexto.** O app precisa virar `.exe` instalável. A escolha inicial foi Tauri 2 por peso de binário — cerca de 3 MB contra 85 MB do Electron — e tempo de partida.

**Por que reabri.** Esse argumento não sobrevive a exame. Peso de binário é irrelevante para software instalado uma vez numa estação de escritório. E a ADR-004, que põe o núcleo em Python, torna obrigatório um processo separado. Resultado: um shell Rust mais um sidecar Python, com handshake, watchdog, porta dinâmica e risco de processo órfão. Três runtimes para uma planilha com leitor de CAD.

A alternativa honesta: **FastAPI servindo o build do Vue, embrulhado em pywebview, empacotado com PyInstaller**. Um runtime, sem Rust, sem IPC entre processos, sem órfão possível.

| Critério | Tauri 2 + sidecar | pywebview + FastAPI |
|----------|-------------------|---------------------|
| Runtimes | Rust + Python + WebView | Python + WebView |
| Modos de falha de IPC | handshake, porta, watchdog, órfão | nenhum, mesmo processo |
| Instalador nativo `.msi` | pronto | exige WiX ou Inno Setup à parte |
| Assinatura de código e auto-update | suportado | manual |
| Curva de aprendizado | Rust mínimo, mas real | zero, só Python |
| Maturidade em Windows corporativo | alta | média |

**Decisão.** Mantida em Tauri 2, por razão diferente: instalador nativo, assinatura de código e auto-update. Isso importa num produto vendido a escritórios e, no caminho pywebview, vira trabalho manual recorrente. Peso de binário sai da justificativa.

**Consequência.** O custo do IPC é aceito conscientemente e vira requisito testável — bateria T-INFRA em §11.2.
**Revisão:** se a F0 acumular mais de dois incidentes de handshake, migrar para pywebview antes da F1, quando o custo de troca ainda é baixo.

## ADR-003 — Front-end: Vue 3 + TypeScript + Vite

**Contexto.** Stack já dominada no ENGEVITH.
**Decisão.** Mantida.
**Revisão:** não prevista.

## ADR-004 — Núcleo em Python

**Contexto.** Leitura de DXF e importação de planilha oficial.
**Decisão.** Python 3.12 com FastAPI.
**Consequência.** `ezdxf`, `pandas` e `openpyxl` cobrem o domínio inteiro; não há equivalente maduro em Rust ou JS. É o que torna o processo separado inevitável, conforme ADR-002.
**Revisão:** não prevista.

## ADR-005 — Banco: SQLite com FTS5

**Contexto.** Cerca de 1,25 milhão de linhas de preço por base importada.
**Decisão.** SQLite embarcado.
**Consequência.** Zero configuração e volume trivial para o motor. Exige estratégia de backup — §9.2 — que aplicativo local costuma esquecer.
**Revisão:** se houver demanda real de acesso simultâneo.

## ADR-006 — IA: OpenAI com a chave do usuário

**Contexto.** Classificação semântica de camadas.
**Decisão.** OpenAI, chave do próprio usuário, guardada no Windows Credential Manager.

**Consequência.** **Sem camada de abstração agora.** A versão anterior deste documento previa uma interface `ProvedorIA` com três implementações, das quais zero existiam. Abstração desenhada antes do segundo caso concreto é adivinhação: congela hipóteses erradas sobre o que varia. Uma classe concreta, e a interface se extrai quando o segundo provedor aparecer, com a forma que a realidade pedir.

**Revisão:** quando surgir demanda concreta de modo offline ou de outro provedor.

## ADR-007 — Sem SINAPI aderente: CPU própria mediante autorização

Detalhado em `VERTICE-modulo-cpu.md`.
**Revisão:** não prevista, é regra de domínio e não de tecnologia.

## ADR-008 — Base SINAPI: importação do pacote oficial

**Contexto.** A Caixa não tem API nem URL estável.
**Decisão.** O usuário entrega o pacote mensal; o app importa e registra o hash.
**Consequência.** Sem raspador para manter, rastreabilidade em auditoria, funcionamento sem rede. Detalhado em `VERTICE-modulo-sinapi.md`.
**Revisão:** se a Caixa publicar API oficial.

## ADR-009 — Memória de cálculo: registro declarativo, não grafo de dependências

**Contexto.** A planilha-modelo documenta cada cálculo com expressão, entradas e origem. Cogitei um motor com grafo de dependências em tempo de execução para gerar isso sozinho.

**Decisão.** Não. Um registro declarativo de fórmulas — cada cálculo nomeado, com expressão, entradas e destino — produz a mesma documentação com uma fração da complexidade.

**Consequência.** Grafo de dependências existe para recálculo incremental, problema que o VÉRTICE não tem: o orçamento inteiro recalcula em milissegundos. Seria infraestrutura sofisticada para um gargalo inexistente.
**Revisão:** se um orçamento real passar de 200 ms de recálculo.

## ADR-010 — Estrutura de pastas por funcionalidade

Padrão já adotado no ENGEVITH.
**Revisão:** não prevista.

## ADR-011 — Agente antagonista atravessando o sistema

**Contexto.** O classificador propõe códigos, o motor calcula, e o usuário revisa. Falta quem procure erro ativamente. A auditoria da planilha do CME mostrou por quê: erros reais sobreviveram meses porque a verificação embutida era auto-referente e nunca podia falhar.

**Decisão.** Um componente independente, somente leitura, cuja única função é produzir objeções — em três camadas, com a maior parte determinística e sem IA. Detalhado em `VERTICE-agente-antagonista.md`.

**Consequência.** **Quem propõe não valida.** Quatro papéis separados: classificador propõe, motor calcula, antagonista ataca, RT decide. Nenhum acumula dois. A ata de objeções é exportada junto do orçamento, virando peça de defesa em auditoria.

**Revisão:** se a taxa de objeções improcedentes passar de 20%, o catálogo de regras está mal calibrado e precisa de poda.

## ADR-012 — Laço lint → antagonista → Correct, sem travamento

**Contexto.** O antagonista, na versão inicial, bloqueava ativação de CPU e exportação. Ferramenta que trava é ferramenta que se desliga: na primeira sexta-feira de prazo apertado ela é contornada, e a partir daí não existe mais.

**Decisão.** O antagonista **nunca interrompe**. Ele produz especificação de defeito em formato fixo — alvo, evidência, teste que reproduz, critério de pronto, escopo permitido. Um módulo separado, o Correct, consome a especificação e executa a correção sob autorização do desenvolvedor. Detalhado em `VERTICE-modulo-correct.md`.

**Consequência.** Quatro papéis: lint mede, antagonista especifica, Correct conserta, desenvolvedor decide. Toda objeção termina em `CORRIGIDA`, `REFUTADA`, `ACEITA_COM_RISCO` ou `UTOPIA` — sempre há saída disponível, e por isso não existe estado bloqueado.

Quando o laço de correção diverge — corrigir A quebra B, corrigir B quebra A, ou o escopo cresce a cada rodada — o Correct retorna ao último estado estável e a objeção vira **utopia**: ideal correto que o sistema atual não alcança a custo aceitável, registrado com causa medida e condição de reabertura.

**Revisão:** se mais de 15% das objeções virarem utopia num estágio, o problema não é o laço — é a arquitetura, e a fase precisa ser replanejada.

## ADR-013 a ADR-017 — Modelo universal de obra

Cinco decisões tomadas após levantamento do estado da arte em português, inglês e chinês, detalhadas em `VERTICE-modelo-universal.md`:

| ADR | Decisão | Consequência |
|-----|---------|--------------|
| **013** | Regra de medição é dado versionado, não código | Trocar critério de dedução é editar tabela; o critério vira fonte rastreável |
| **014** | EAP é árvore de classificação em dois eixos: resultado e espaço | Acaba o grupo digitado por obra; composições viram reutilizáveis entre obras |
| **015** | Dedução automática entre elementos sobrepostos | Corrige lacuna real: a extração anterior somava por camada sem tratar sobreposição |
| **016** | Ambiente fechado é entidade de primeira classe | `U-003` deixa de ser utopia: o estado da arte resolve isso há anos |
| **017** | IFC como caminho de alta fidelidade, desde o modelo de dados | Em IFC a classificação já vem pronta; o app fica mais simples, não mais complexo |

**Contexto comum.** A planilha do CME é instância, não modelo. Desenhar a partir dela produziria um aplicativo para reformar central de esterilização. A China resolve a cobertura universal por particionamento — um padrão de precificação e dez padrões de cálculo de quantitativos por disciplina — e o Brasil não tem equivalente normativo, o que torna o acervo de critérios do escritório um ativo do produto.

**Revisão:** ADR-017 volta à mesa se a adoção de IFC no mercado-alvo se mostrar menor que o previsto na F2.

## ADR-018 a ADR-022 — Plataforma e pesquisa

Detalhadas em `VERTICE-plataforma.md` e `VERTICE-modulo-pesquisa.md`.

| ADR | Decisão | Consequência |
|-----|---------|--------------|
| **018** | Adaptador de base de preço | SINAPI vira uma implementação entre quatro casos concretos já conhecidos |
| **019** | Markup generalizado | BDI passa a ser instância declarada em pacote, não conceito do motor |
| **020** | Composição própria sobe ao núcleo | Toda base tem lacuna, em qualquer domínio |
| **021** | Pesquisa profunda como serviço do núcleo | O pacote declara perfis; a fronteira é do núcleo |
| **022** | Pesquisa é proposta, nunca lançamento | Nada entra no orçamento sem confirmação do RT |

**Contexto comum.** Enquanto o núcleo souber o que é alvenaria, BDI ou SINAPI, o produto está preso à construção civil brasileira. A escalabilidade não vem de acrescentar grupos: vem de **remover conhecimento de domínio do núcleo**. O que resta é verdade em qualquer orçamento — item, quantidade, preço unitário, markup, tributo, fonte, memória.

**A fronteira da pesquisa.** A base oficial tem precedência absoluta dentro da cobertura dela. Pesquisa atua no complemento. O fundamento é empírico: um agregador público divulgava R$ 37,91 para uma composição cujo valor oficial era R$ 40,63 no onerado e R$ 39,37 no desonerado — nenhum dos dois. Pesquisa automática que adotasse aquilo teria criado erro onde havia acerto.

**Revisão:** ADR-018 e ADR-019 voltam à mesa se o segundo pacote de domínio exigir alteração no núcleo — sinal de que a separação ficou no lugar errado.

## ADR-023 a ADR-029 — Otimização por gargalo medido

Detalhadas em `VERTICE-otimizacao-processo.md`. Regra que as governa: **nenhuma tecnologia entra sem gargalo medido e meta numérica**.

| ADR | Decisão | Gargalo atacado |
|-----|---------|-----------------|
| **023** | Ambiente por ciclos em grafo planar | Detecção de recinto fechado |
| **024** | Dedução por operação booleana | Área de parede sem descontar vãos |
| **025** | Embeddings locais para busca semântica | Encontrar o código certo entre 15 mil descrições |
| **026** | Endereçamento por conteúdo | Recálculo integral a cada revisão de projeto |
| **027** | Pesquisa concorrente com resultado progressivo | Latência da pesquisa profunda |
| **028** | Saída estruturada por gramática | Descarte de resposta malformada do modelo |
| **029** | Teste por propriedade e teste de mutação | Suíte que passa sempre, inclusive errada |

Duas consequências que mudam decisões anteriores:

**ADR-028 transforma a regra fundadora em impossibilidade estrutural.** "A IA nunca produz número" deixa de ser validação posterior e passa a ser restrição imposta durante a geração. A validação continua, como segunda barreira — regra crítica merece duas barreiras independentes.

**ADR-025 pode encolher a F3.** Boa parte do que atribuí ao classificador é problema de similaridade, não de raciocínio. Similaridade se resolve com vetor local: milissegundos, sem custo, sem rede e reprodutível. Vale medir quanto do problema é isso antes de assumir que precisa de modelo grande.

**Revisão:** cada ADR desta faixa cai se a medição do gargalo que a justifica não se confirmar.

## ADR-030 — Repositório preparado para construção por agentes

**Contexto.** A implementação será conduzida por agentes de IA. Agente não lê intenção: lê o que está no disco. Ambiguidade em documento vira decisão arbitrária em código — rápida, plausível e silenciosa.

**Decisão.** Formalizar o protocolo em `VERTICE-AGENTS.md`: tarefa com contrato verificável por comando, pacotes de contexto por módulo, grafo de construção que declara o paralelizável, anti-padrões com detecção automática.

**Descoberta que organiza tudo.** A especificação de defeito do antagonista — alvo, evidência, teste que reproduz, critério de pronto, escopo permitido — **já é um ticket de agente completo**. Ela foi desenhada para que outro módulo consertasse sem reinvestigar, e o requisito é o mesmo: quem executa precisa do contrato, não do histórico.

**Consequência.** Verificação fica fora do processo do agente. Ele não declara pronto — o portão declara. Agente que roda o próprio teste e relata sucesso está validando o próprio trabalho, que é o que a separação de papéis proíbe.

**Revisão:** se a proporção de tarefas devolvidas por contrato insuficiente passar de 20%, o problema está na especificação, não no agente.

## ADR-031 — Entrega de projeto: pedir formato, validar na chegada, recusar rebaixado

**Contexto.** Conversão degrada arquivo em silêncio. Rebaixar DXF para R12 explode texto e hachura e achata curvas; o arquivo abre e está destruído para medição. IFC perde informação a cada ciclo de exportação.

**Decisão.** O aplicativo gera o pedido ao projetista, por faixa de qualidade, e valida o arquivo na chegada com laudo endereçado a quem o produziu. DXF abaixo de R2013 é recusado. PDF não gera quantitativo. Detalhado em `VERTICE-entrega-cad.md`.

**Consequência.** A correção acontece na origem, onde custa dez vezes menos.

## ADR-032 — Esgotamento da base antes de qualquer composição própria

**Contexto.** CPU costuma nascer porque a primeira busca não achou — quando o código existia com outro nome.

**Decisão.** Sete passadas obrigatórias sobre a base, pesquisa por pares e confirmação por segundo avaliador, tudo registrado, **antes** do portão de permissão. Detalhado em `VERTICE-modulo-cpu.md` §3.

**Consequência.** A base determina o serviço. CPU é o que sobra depois de provar que a base não cobre — e a prova vai para o orçamento exportado.

## ADR-033 — Ciclo mensal com lembrete no dia 12

**Decisão.** O aplicativo pede a nova referência todo dia 12, com adiamento limitado e alerta de defasagem. Nunca importa sozinho. `VERTICE-modulo-sinapi.md` §8.

## ADR-034 — Limites duros contra god code

**Contexto.** Agente de IA gera arquivo grande com naturalidade: é mais fácil que dividir.

**Decisão.** Limites numéricos verificados por ferramenta: 300 linhas por arquivo, 40 por função, complexidade 10, 7 métodos públicos, 5 parâmetros, 8 importadores. `VERTICE-LINT-SUITE.md` §3.1.

**Consequência.** Estrutura pequena por construção, não por boa vontade.

## Em aberto

| # | Questão | Decidir em |
|---|---------|-----------|
| A01 | Modelo OpenAI específico | início da F3 |
| A02 | Modo offline com Ollama | pós-F3 |
| A03 | Licenciamento do produto | pré-F4 |
| A04 | Outras bases: SICRO, ORSE | pós-F1 |

---

---

## Histórico

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 13/09/2026 | Registro extraído do documento de arquitetura, que passa a conter apenas a estrutura estável. ADR-001 a ADR-034 preservadas com o texto original |
