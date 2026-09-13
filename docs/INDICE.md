# VÉRTICE — Índice do Conjunto Documental

**Versão:** 1.9
**Conjunto compatível:** 13/09/2026

Este arquivo existe por um motivo só: **um assunto, um dono.** Documento que reafirma regra de outro documento produz duas versões da regra, e a segunda envelhece em silêncio. Aqui fica quem manda em quê, e em que versão os documentos se entendem.

---

## 1. Conjunto compatível

As referências cruzadas entre os documentos pressupõem estas versões. Alterar um documento sem atualizar esta linha quebra a suposição.

| Documento | Versão | Papel |
|-----------|-------:|-------|
| `VERTICE-REGRAS.md` | 1.4 | Protocolo de desenvolvimento e hierarquia de autoridade |
| `VERTICE-arquitetura.md` | 1.2 | Estrutura estável: módulos, fluxo, proveniência, dados |
| `VERTICE-decisoes.md` | 1.0 | ADR-001 a ADR-034: por que cada escolha |
| `VERTICE-fundamentos.md` | 1.0 | Base acadêmica e níveis de evidência |
| `VERTICE-LINT-SUITE.md` | 1.8 | Portões G0 a G8 e regras verificáveis |
| `VERTICE-AGENTS.md` | 1.1 | Construção por agentes de IA |
| `VERTICE-agente-antagonista.md` | 0.5 | Catálogo de objeções `A-*` |
| `VERTICE-modulo-correct.md` | 0.2 | Protocolo de correção e divergência |
| `VERTICE-plataforma.md` | 0.2 | Núcleo, pacote de domínio, instância |
| `VERTICE-modelo-universal.md` | 0.1 | Espaço, regra de medição, item de orçamento |
| `VERTICE-modulo-sinapi.md` | 0.3 | Importação e ciclo da base de referência |
| `VERTICE-modulo-cpu.md` | 0.4 | Esgotamento da base e composição própria |
| `VERTICE-modulo-precificacao.md` | 0.1 | BDI, encargos, administração local |
| `VERTICE-modulo-pesquisa.md` | 0.2 | Pesquisa profunda e dossiê |
| `VERTICE-modulo-exportacao.md` | 0.2 | Formatos de saída e portões de exportação |
| `VERTICE-entrega-cad.md` | 1.0 | Formato de projeto exigido do projetista |
| `VERTICE-otimizacao-processo.md` | 0.1 | Tecnologia só entra com gargalo medido |

Verificado por `VM-11`: `python tools/markdown_lint.py docs` reprova se algum documento estiver numa versão diferente da declarada aqui.

---

## 2. Um assunto, um dono

Coluna **Dono** é quem define. Os demais documentos podem citar, nunca reafirmar com palavras próprias — reafirmação é cópia que vai divergir.

| Assunto | Dono | Citam |
|---------|------|-------|
| Aritmética decimal, proibição de `float` | `VERTICE-REGRAS.md` §4.2 | fundamentos, LINT-SUITE `VD-01`, antagonista `A-DEV-01`, AGENTS |
| **Representação numérica persistida** (`TEXT`/`INTEGER`, centavos) | `VERTICE-arquitetura.md` §5.1 | todos os esquemas de módulo, LINT-SUITE `VD-15` |
| Princípio da proveniência (número sem origem não existe) | `VERTICE-REGRAS.md` regra 1 | fundamentos, otimizacao-processo, AGENTS |
| **Formato do `id_origem`** | `VERTICE-arquitetura.md` §4.1 | modelo-universal, cpu, precificacao, LINT-SUITE `VD-16` |
| Antagonista não bloqueia nada | `VERTICE-decisoes.md` ADR-012 | agente-antagonista, arquitetura, exportacao |
| Catálogo de objeções `A-*` | `VERTICE-agente-antagonista.md` §9 | correct, LINT-SUITE |
| Metas numéricas de desempenho | `VERTICE-LINT-SUITE.md` §7 | arquitetura, sinapi, otimizacao-processo |
| Limites duros contra god code | `VERTICE-LINT-SUITE.md` §3.1 `VD-09`–`VD-14` | decisoes ADR-034, arquitetura, fundamentos |
| Esgotamento da base antes de CPU | `VERTICE-modulo-cpu.md` §3 | decisoes ADR-032, sinapi, antagonista |
| Regime de encargos (onerado/desonerado) | `VERTICE-modulo-precificacao.md` §2 | sinapi, cpu, plataforma |
| Sidecar, handshake e processo órfão | `VERTICE-decisoes.md` ADR-002 | arquitetura §3 e §7, LINT-SUITE `VS-02`–`VS-04` |
| Backup e restauração verificada | `VERTICE-arquitetura.md` §5 | LINT-SUITE `VS-05`, decisoes |
| Formato de projeto exigido do projetista | `VERTICE-entrega-cad.md` | modelo-universal, antagonista |
| Critério de entrada de tecnologia | `VERTICE-otimizacao-processo.md` §1 | decisoes ADR-023 a ADR-029 |

**Como usar em revisão.** Ao escrever uma regra, procurar o assunto nesta tabela. Se já tem dono e não é este documento, escrever a referência — não a regra.

---

## 3. Regra de precedência

Herdada de `VERTICE-REGRAS.md` §1 e repetida aqui **porque é a única exceção deliberada** à regra do dono único: sem ela, este índice não sabe resolver conflito.

```text
REGRAS  >  decisoes (ADR)  >  arquitetura  >  documento de módulo
```

Documento de módulo que contraria uma ADR está errado, não a ADR. O caminho é abrir ADR nova que supere a anterior, nunca editar a ADR aceita.

---

## 4. Estado do código

| Portão | Comando | Situação em 13/09/2026 |
|--------|---------|------------------------|
| Formato e lint | `ruff check core/ tools/ tests/` | Passa |
| Tipos | `mypy --strict core/` | Passa |
| Testes | `pytest tests/ -q` | Passa, 88 testes |
| Domínio `VD-01`–`VD-14` | `python tools/domain_lint.py` | Passa |
| Esquema `VD-15`–`VD-16` | `python tools/schema_lint.py --docs docs` | Passa |
| Documentos `VM-01`–`VM-11` | `python tools/markdown_lint.py docs` | Passa |
| Tipos do front-end | `npx vue-tsc --noEmit` | Passa |

Módulos com código: `core/domain/` (`Origem`, `Quantia`, `calcular_markup` — a interface pública inteira de §3 já existe), `core/documents/`, `core/classification/`, `core/reference_base/` (adaptador SINAPI em `core/reference_base/adapters/sinapi/`), `core/packages/` (`carregar`/`validar`/`instalar` — §4.5), `core/pricing/` (BDI analítico — §4.4), `core/api/` (sidecar FastAPI — §4.3). Frontend mínimo em `src/` (Vue 3 + Vite). Os demais da tabela de `VERTICE-arquitetura.md` §3 existem apenas como especificação.

### 4.1 F0 — medido contra o pacote real 08/2026

Não é o 07/2026 que `VERTICE-modulo-sinapi.md` analisou — é o pacote que chegou. Números diferentes entre os dois meses são o mercado, não erro.

| Métrica | Meta (`LINT-SUITE` §7) | Medido | Situação |
|---------|-----------------------:|-------:|----------|
| Composições importadas | — | 10.547 | — |
| Insumos importados | — | 6.120 (4.876 com preço coletado + 1.244 `SEM PREÇO`, só no Analítico) | — |
| Linhas de preço | — | 1.249.263 | — |
| Importação da base completa | 180 s | 82 s | Bate. Ver §4.2 — número tem ressalva de cache |
| Busca textual (`impermeabilizacao`) | 100 ms | < 1 ms | Bate, com folga larga |
| Explosão analítica (3 níveis) | 50 ms | 4 ms | Bate, com folga larga |
| `.db` gerado | — | 127 MB | — |
| 87622 em SP, onerado / desonerado | — | R$ 40,50 / R$ 39,24 | Para conferência: `VERTICE-modulo-sinapi.md` S04 cita 40,63/39,37, do pacote 07/2026 |

### 4.2 Importação: 487 s → 199 s → 82 s, meta é 180 s

Duas correções, cada uma medida antes e depois:

1. **Nove aberturas do mesmo `.xlsx` viraram uma.** Cada leitor abria sua própria cópia do arquivo de 13 MB; unificado num único `openpyxl.load_workbook` compartilhado. 487 s → 199 s.
2. **`ISD` parou de ser lido duas vezes inteiro.** Catálogo de insumo e preço onerado vinham da mesma aba, em duas passadas separadas; `ler_insumos_onerados` funde as duas numa só. 199 s → 82 s.

**Ressalva sobre o número de 82 s.** As três medições acima aconteceram na mesma sessão, no mesmo arquivo — o cache de disco do sistema operacional esquenta a cada leitura, e parte da queda de 199 s para 82 s é esse cache, não só o corte de leitura. O ganho da correção 1 é sólido (nove aberturas para uma é estrutural). O ganho exato da correção 2, isolado do cache, não foi medido à parte. Primeira leitura em máquina fria tende a ficar entre 82 s e 199 s, não necessariamente nos 82 s.

`CSD`/`CCD`/`CSE` (58 colunas, ~10.550 linhas cada) continuam sendo as três leituras mais caras que sobram — preço em três regimes, dados genuinamente diferentes, sem leitura redundante a cortar.

### 4.3 Sidecar e frontend — primeira fatia vertical, verificada de ponta a ponta

Tauri ainda não entra: sem Rust/MSVC nesta máquina (ADR-002 não muda — só a ordem de montagem). `core/api/` é o sidecar real, `src/` é o frontend real; o que falta é só o empacotamento.

| Peça | Onde | Verificado |
|------|------|------------|
| Sidecar FastAPI | `core/api/app.py`, `server.py` | 8 testes (`tests/api/`) + rodado ao vivo contra o `.db` real |
| Token de sessão (VS-02) | `core/api/security.py` | Sem token → 401; token errado → 401; testado |
| `127.0.0.1` (VS-03) | `core/api/server.py` | `HOST_SIDECAR` fixo, nunca `0.0.0.0` |
| Contratos travados (REGRAS §4.4) | `core/api/routes/reference_base.py` | `GET /sinapi/buscar` e `GET /sinapi/composicao/{codigo}/explodir`, path exato, testado |
| Frontend | `src/` (Vue 3 + TS + Vite) | `vue-tsc --noEmit` limpo; `npm run dev` servindo `index.html`, `main.ts` e `public/dev-session.json` confirmado ao vivo |
| Ponte dev sidecar↔frontend | `public/dev-session.json`, `src/shared/http-client.ts` | Sidecar escreve token+porta; frontend lê e chama com `X-Vertice-Token` |
| Rotas de precificação (não travadas por §4.4 — podem evoluir) | `core/api/routes/pricing.py` | `POST /orcamento`, `GET /orcamento/{id}`, `POST /orcamento/{id}/bdi`, `GET /orcamento/{id}/bdi` — 9 testes (`tests/api/test_pricing_routes.py`), incluindo a fórmula real do pacote reproduzindo a âncora do CME pela rota HTTP |
| Pacote de domínio carregado no boot do sidecar | `core/api/app.py::criar_app` | `app.state.pacote` vem de `core.packages.installer.instalar`; as rotas de BDI leem a fórmula dali, nunca hardcoded na API |
| Tela de orçamento/BDI | `src/features/pricing/PricingView.vue` | `vue-tsc --noEmit` limpo; abas em `App.vue` alternam entre busca e orçamento |

**Como rodar hoje:**
```bash
VERTICE_DB_PATH=/caminho/para/o.db python -m core.api.server   # sidecar em :8756
npm run dev                                                     # frontend em :5173
```

**Nota de ambiente:** a porta `5173` (padrão do Vite, e a única liberada em `ORIGENS_DEV_PERMITIDAS` de `app.py`) estava ocupada por outro processo Node nesta máquina durante a verificação — não identificado como parte deste projeto, não finalizado por precaução. `npm run dev` recusa subir com a porta ocupada (`strictPort`); libere a `5173` ou ajuste `vite.config.ts` e `ORIGENS_DEV_PERMITIDAS` juntos.

### 4.4 BDI analítico — escopo cortado deliberadamente

`VERTICE-modulo-precificacao.md` especifica um módulo inteiro: BDI (§3), administração local (§4), taxas (§5), resíduos (§6), cronograma (§7), curva ABC (§8), sensibilidade (§9). Construído agora: só o §3, com persistência.

**Confirmado contra a planilha real.** `data/examples/ENGEViTH_CME_SANTACASA_ABNT_SINAPI (1).xlsx` — a planilha auditada que `VERTICE-modulo-cpu.md` e `VERTICE-modulo-precificacao.md` citam como "modelo de referência" — está na pasta de dados. A aba `BDI` tem as nove parcelas célula a célula: AC 4,01%, SG 0,32%, R 0,50%, DF 1,02%, L 6,64%, PIS 0,65%, COFINS 3,00%, ISS 5,00% (base 100%, Cerqueira César), CPRB 0% — exatamente os valores já usados em `PARCELAS_CME` nos testes, não uma aproximação da tabela do documento. A aba `ORÇAMENTO FINAL` confirma no cabeçalho: **"BDI: 23,6245%"**, literal.

| Peça | Onde | Verificado |
|------|------|------------|
| Fórmula BDI analítico | `core/pricing/bdi.py` | P01: parcelas do CME → 23,62% (4 casas), bate com a âncora de `VERTICE-REGRAS.md` §3.2 e com a planilha real |
| Faixas do TCU (§3.3) | `classificar_faixa_tcu`, `exige_justificativa` | P04: testado nas quatro faixas |
| Coerência de regime (§2.2 regra 5) | `verificar_coerencia_de_regime` | P03: CPRB > 0 em onerado alerta; em desonerado, não |
| "Nunca um valor guardado à parte" (§3.5) | — | Testado: duas instâncias das mesmas parcelas sempre concordam |
| Persistência (`orcamento`, `bdi`, `fonte`) | `core/pricing/schema.py`, `persistence.py` | Ida e volta no banco reproduz a âncora; salvar de novo substitui, não acumula |

**Nota arquitetural fechada (ADR-019).** A ressalva de versões anteriores deste índice — fórmula hardcoded, pacote não existia, sem persistência — não vale mais. `calcular_bdi` exige a fórmula como argumento, `packages/civil-construction-br/package.yaml` a declara de verdade, e `orcamento`/`bdi`/`fonte` têm tabela e teste de ida e volta.

**Recorte deliberado do `orcamento` construído.** Não existe módulo `obra` (VERTICE-modelo-universal.md referencia `obra(id)`, nunca definida) nem cenário/revisão (§9 do módulo de precificação). `Orcamento` aqui é o mínimo que dá alvo real para a chave estrangeira de `bdi` — identificação, regime, UF, base, data-base, origem. Sem método para trocar regime depois de criado (§2.2 regra 3 exige recálculo comparativo, que não existe ainda) — o tipo recusa oferecer o atalho.

**Não construído:** administração local, taxas, resíduos, cronograma, curva ABC, sensibilidade, `obra`/geometria, cenários/revisões de orçamento.

### 4.5 `core/packages` — ADR-018/019, a interface pública inteira de §3

`carregar`, `validar`, `instalar` — os três nomes que `VERTICE-arquitetura.md` §3 documenta para o módulo `packages` — existem e leem um manifesto real, não um exemplo hipotético.

| Peça | Onde | Verificado |
|------|------|------------|
| `carregar` (forma do manifesto) | `core/packages/loader.py` | `yaml.safe_load` (nunca `load` — mesma razão de `calcular_markup` não usar `eval()`); 5 testes, incluindo o pacote real |
| `validar` (conteúdo contra o mundo) | `core/packages/validator.py` | Arquivo referenciado existe, glob de regra acha algo, fórmula é aritmética válida; nunca trava (ADR-012) |
| `instalar` | `core/packages/installer.py` | `carregar` + `validar` encadeados; pacote incompleto ainda instala |
| Manifesto real | `packages/civil-construction-br/package.yaml` | Carrega; `validar` acusa corretamente a `classificacao.arquivo` que ainda não existe (NBR 15965, §4.4 acima) |
| **A prova de ADR-019** | `tests/packages/test_integracao_pricing.py` | A fórmula **lida do arquivo**, não uma cópia dela em código, reproduz a âncora do CME (23,6245%) |

**O que ficou de fora, por não ter consumidor ainda:** `tipologias`, `antagonista.regras` e `pesquisa.perfis` do formato de manifesto de `VERTICE-plataforma.md` §3 — carregados como `bruto` (dict cru), sem tipo próprio, porque tipar antes do segundo caso concreto é adivinhação (o mesmo critério de ADR-018). E o mapeamento de sigla da fórmula (`AC` → `administracao_central`) não está no manifesto — `VERTICE-plataforma.md` §3 não declara essa convenção, e `validar` não inventa uma regra que o documento não pede.

---

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 1.9 | 13/09/2026 | `core/pricing` ligado ao sidecar e ao frontend: rotas `POST /orcamento`, `GET /orcamento/{id}`, `POST /orcamento/{id}/bdi`, `GET /orcamento/{id}/bdi` (`core/api/routes/pricing.py`), pacote de domínio carregado em `app.state` no boot (`criar_app` agora chama `core.packages.installer.instalar`), e `src/features/pricing/PricingView.vue` no frontend. `id_origem` de registros criados pelo sidecar usa a raiz `USUARIO:sidecar#<instante>` — provisório, documentado como tal, até existir identidade de usuário real. 96 testes no total |
| 1.8 | 13/09/2026 | `core/pricing/`: tabelas `orcamento`, `bdi`, `fonte` persistidas (schema.py, persistence.py), fechando a lacuna de BDI-sem-persistência de §4.4. Confirmado contra a planilha real `data/examples/ENGEViTH_CME_SANTACASA_ABNT_SINAPI (1).xlsx` fornecida pelo usuário — as nove parcelas de BDI e o "BDI: 23,6245%" do cabeçalho batem exatamente com os valores já usados nos testes. 88 testes no total |
| 1.7 | 13/09/2026 | `core/packages/` completa `carregar`/`validar`/`instalar` (ADR-018/019) contra um manifesto real, `packages/civil-construction-br/package.yaml`. `core.pricing.bdi.calcular_bdi` deixa de hardcodar a fórmula — passa a exigi-la como argumento, sourced do pacote. Teste de integração prova que a fórmula lida do arquivo reproduz a âncora do CME. 81 testes no total |
| 1.6 | 13/09/2026 | `core/pricing/bdi.py`: fórmula BDI analítico via `calcular_markup`, faixas do TCU, coerência de regime. P01 bate com a âncora do CME (23,6245%) de `VERTICE-REGRAS.md` §3.2. Escopo cortado deliberadamente do resto de `VERTICE-modulo-precificacao.md` — ver §4.4. 68 testes no total |
| 1.5 | 13/09/2026 | `core/domain/` completa a interface pública documentada em `VERTICE-arquitetura.md` §3: `Origem` (id_origem validado no construtor, OrigemInvalida se fora da gramática), `Quantia` (centavo inteiro, `de_reais`/`de_centavos`/`para_reais`, aritmética exata) e `calcular_markup` (ADR-019 — avaliador de expressão aritmética por AST, não `eval()`, fórmula é dado do pacote). 22 testes novos, 63 no total |
| 1.4 | 13/09/2026 | Primeira fatia do app: sidecar FastAPI (`core/api/`, token de sessão, os dois contratos de REGRAS §4.4) e frontend mínimo (`src/`, Vue 3 + Vite) verificados de ponta a ponta contra o `.db` real. Tauri fica para quando Rust/MSVC estiverem instalados — não muda a ADR-002 |
| 1.3 | 13/09/2026 | `ISD` deixa de ser lido duas vezes (catálogo + preço onerado fundidos em `ler_insumos_onerados`). Importação real caiu de 199 s para 82 s, com ressalva de cache de disco aquecido entre as três medições da sessão |
| 1.2 | 13/09/2026 | Documentos organizados em `docs/`. Comandos de `VM-11` e `VD-15`/`VD-16` atualizados para apontar para a nova pasta |
| 1.1 | 13/09/2026 | Rename retroativo de arquivos e pastas do código para inglês (`core/`, `tools/`, `tests/`, `reference_base/`). §4 atualizado com os caminhos novos e com os números reais de F0 medidos contra o pacote SINAPI 08/2026 fornecido — importação, busca, explosão e o gargalo de 199 s ainda acima da meta de 180 s |
| 1.0 | 13/09/2026 | Índice inicial. Conjunto compatível declarado e verificado por `VM-11`. Tabela de dono único criada após varredura que mediu dez assuntos afirmados em mais de dois documentos |
