# VÉRTICE — Suíte de Lint

Portões de qualidade executados ao **encerramento de cada estágio de desenvolvimento**. Nenhum estágio é declarado concluído com portão reprovado.

**Versão:** 1.8
**Documento-pai:** `VERTICE-REGRAS.md` §7

---

## 1. Como usar

Durante o desenvolvimento, a suíte **não roda**. Isso é deliberado: lint contínuo em fase de exploração interrompe raciocínio e gera correção de ruído em código que ainda vai mudar.

A suíte roda no fechamento do estágio, de uma vez. **Ela não trava nada.** A saída não é aprovação ou reprovação: é um conjunto de achados que alimenta o agente antagonista, que os traduz em especificação de defeito.

```text
SUÍTE mede  →  ANTAGONISTA especifica  →  DEV decide  →  CORRECT conserta  →  SUÍTE confirma
```

O estágio encerra quando **todo achado tem destino declarado**: corrigido, refutado, aceito com risco ou registrado como utopia. Achado sem destino é o único impedimento — e ele se resolve escrevendo uma linha, não consertando código.

```text
G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7
```

Portões em sequência. O primeiro que falha interrompe **a bateria**, não o desenvolvedor: não faz sentido medir desempenho de código que não compila. Os achados até ali já seguem para o antagonista.

### 1.1 O laço curto, que roda sempre

A suíte completa continua sendo de fechamento. Mas quatro comandos são baratos o bastante para rodar a cada mudança, e caros de descobrir tarde — erro de tipo e âncora quebrada custam mais depois de três horas de código por cima:

```bash
ruff check core/ tools/ tests/
mypy --strict core/
pytest tests/ -q
pytest tests/ -q -k ancora          # a âncora, isolada e com evidência
```

Critério para um comando entrar aqui: **abaixo de dez segundos no repositório inteiro**. Acima disso é bateria de fechamento, não laço curto. Desempenho, mutação, fuzzing e auditoria de dependência ficam de fora por esse critério, não por serem menos importantes.

O laço curto **também não trava**. Ele avisa cedo; quem decide continua sendo o desenvolvedor.

---

## 2. G0 — Higiene do repositório

| Verificação | Critério |
|-------------|----------|
| Segredo em código | Nenhuma chave de API, token ou senha versionada |
| `.env` e credenciais | Ausentes do índice do Git |
| Arquivo temporário ou de backup | Ausente |
| Arquivo maior que 5 MB | Justificado ou fora do repositório |
| Mensagens de commit do estágio | Todas no formato `tipo(escopo): descrição` |
| Dependência abandonada | Nenhuma sem uso no `package.json` e no `pyproject.toml` |

```bash
git secrets --scan            # ou detect-secrets scan
git ls-files | xargs -I{} sh -c 'test $(stat -c%s {}) -lt 5242880 || echo {}'
npx depcheck
python -m pip check
```

---

## 3. G1 — Python: formato, tipo e estilo

| Ferramenta | Papel | Critério |
|------------|-------|----------|
| `ruff format --check` | Formatação | Zero diferença |
| `ruff check` | Lint | Zero achado |
| `mypy --strict` | Tipagem | Zero erro |
| `bandit -r` | Segurança estática | Zero alto ou médio |
| `vulture` | Código morto | Zero, ou ignorado com justificativa |

```bash
ruff format --check core/
ruff check core/ --select E,F,W,I,N,UP,B,A,C4,SIM,ARG,PTH,RUF
mypy --strict core/
bandit -r core/ -ll
vulture core/ --min-confidence 80
```

### 3.1 Regras específicas do projeto

Verificações que ferramenta genérica não cobre. Implementadas como script próprio em `tools/domain_lint.py`:

| Código | Verificação | Motivo |
|--------|-------------|--------|
| `VD-01` | Nenhum `float` em valor monetário, coeficiente ou percentual. Isento em `reference_base/adapters/`: reconhecer o IEEE754 nativo do `.xlsx` na fronteira, para converter uma única vez, não é computar com `float` | Erro de ponto flutuante em orçamento é erro de orçamento |
| `VD-02` | Identificadores em português | `VERTICE-REGRAS.md` §4.1 |
| `VD-03` | Nenhum número mágico fora de constante nomeada | Legibilidade e auditoria |
| `VD-04` | Nenhum `except` sem tipo ou que engole erro | Falha silenciosa é o pior modo de falha |
| `VD-05` | Nenhuma chamada a provedor de IA fora de `classification/` e `antagonist/` | Contenção da superfície de rede |
| `VD-06` | Nenhuma escrita no banco a partir do módulo do antagonista | Independência do auditor |
| `VD-07` | Nenhum `SELECT *` em consulta de produção | Contrato implícito quebra em silêncio |
| `VD-08` | Toda função pública com anotação de tipo e docstring do porquê | Manutenibilidade |
| `VD-09` | Arquivo com mais de 300 linhas | God code. Arquivo grande é módulo que ainda não foi dividido |
| `VD-10` | Função com mais de 40 linhas | Faz mais de uma coisa |
| `VD-11` | Complexidade ciclomática acima de 10 | Ninguém testa todos os caminhos |
| `VD-12` | Classe com mais de 7 métodos públicos | Responsabilidade acumulada |
| `VD-13` | Função com mais de 5 parâmetros | Interface que esconde um objeto |
| `VD-14` | Módulo importado por mais de 8 outros | Ponto de acoplamento; candidato a ser interface |
| `VD-15` | Nenhuma coluna `REAL` em esquema SQL, no documento ou no código | `REAL` é o `float` do SQLite; `VD-01` proibido só no Python é meia proibição |
| `VD-16` | Todo literal de `id_origem` dentro da gramática de `VERTICE-arquitetura.md` §4.1 | Formato livre torna a auditoria de proveniência impossível de automatizar |

Os limites de `VD-09` a `VD-14` são **duros**, não sugestões. Agente de IA produz arquivo grande com naturalidade, porque gerar tudo num lugar é mais fácil que dividir. Sem limite numérico verificado por ferramenta, o repositório vira três arquivos de dois mil linhas em um mês.

```bash
ruff check core/ --select C901 --config "lint.mccabe.max-complexity=10"
python tools/domain_lint.py --max-linhas-arquivo 300 --max-linhas-funcao 40
python tools/schema_lint.py --docs .md      # VD-15 e VD-16
```

---

## 4. G2 — Front-end

| Ferramenta | Critério |
|------------|----------|
| `eslint` | Zero erro, zero aviso |
| `vue-tsc --noEmit` | Zero erro de tipo |
| `stylelint` | Zero erro |
| `prettier --check` | Zero diferença |

```bash
npx eslint src/ --max-warnings 0
npx vue-tsc --noEmit
npx stylelint "src/**/*.{css,vue}"
npx prettier --check "src/**/*.{ts,vue,css}"
```

### 4.1 Regras específicas

| Código | Verificação |
|--------|-------------|
| `VF-01` | Nenhuma chamada de rede fora de `shared/http-client.ts` |
| `VF-02` | Nenhum `localStorage` ou `sessionStorage` guardando dado de orçamento |
| `VF-03` | Nenhuma animação em propriedade que não seja `transform` ou `opacity` |
| `VF-04` | Nenhum valor monetário formatado fora de `shared/formatters/` |
| `VF-05` | Tabela com mais de 200 linhas usa virtualização |
| `VF-06` | Nenhum texto fixo em inglês na interface |
| `VF-07` | Componente com mais de 200 linhas — god component, dividir |
| `VF-08` | Componente com mais de 8 propriedades de entrada — interface que esconde um objeto |

---

## 5. G3 — Documentação

Executado por `tools/markdown_lint.py`. Todas as verificações abaixo foram usadas na revisão de 13/09/2026 e detectaram achados reais.

| Código | Verificação |
|--------|-------------|
| `VM-01` | Hierarquia de títulos sem pulo de nível |
| `VM-02` | Nenhum título duplicado no mesmo documento |
| `VM-03` | Nenhuma cerca de código sem linguagem declarada |
| `VM-04` | Cercas balanceadas |
| `VM-05` | Tabelas com número de colunas consistente |
| `VM-06` | Nenhum espaço em fim de linha |
| `VM-07` | Referência cruzada a documento existente |
| `VM-08` | **Todo nó Mermaid estilizado tem `fill`, `stroke` e `color`** |
| `VM-09` | Todo documento tem versão, data e tabela de histórico |
| `VM-10` | Nenhum número sem fonte declarada em documento de especificação |
| `VM-11` | `INDICE.md` cobre todo documento, na versão que o documento realmente traz |

> `VM-08` nasceu de incidente real: nós com `fill` claro renderizavam texto branco no tema escuro, deixando o diagrama ilegível. A regra impede a reincidência.

```bash
python tools/markdown_lint.py .md      # docs vivem em .md/
npx markdownlint-cli2 "docs/**/*.md"
```

---

## 6. G4 — Testes

| Verificação | Critério |
|-------------|----------|
| Suíte completa | 100% aprovada, zero ignorado sem justificativa |
| Cobertura do núcleo de domínio | Mínimo de 90% em `pricing/`, `reference_base/`, `custom_composition/` |
| Cobertura geral | Mínimo de 75% |
| Teste sem asserção | Zero |
| Teste dependente de ordem | Zero — execução aleatória aprova igual |
| **Índice de mutação** em `domain/` e `pricing/` | Acima de 80% |
| Fuzzing do importador de base | Nenhuma entrada deformada importa com dado errado |

O índice de mutação é o único número da suíte que mede **a qualidade da própria suíte**. Cobertura alta com mutação baixa significa testes que executam o código sem verificar nada — a versão em software da conferência auto-referente encontrada na planilha auditada.

**Por que só `domain/` e `pricing/`.** Mutação é a medida mais cara da bateria, e o custo cresce com a área varrida. Esses dois módulos são onde um teste frouxo vira dinheiro errado no orçamento assinado; em `cad_reading/` ou `export/`, um mutante sobrevivente custa um retrabalho, não um valor incorreto em documento de responsabilidade técnica. Ampliar a área exige gargalo medido, conforme `VERTICE-otimizacao-processo.md` §1.

```bash
pytest --cov=nucleo --cov-report=term-missing --cov-fail-under=75 -p no:randomly
pytest -p randomly            # segunda execução, ordem aleatória
npx vitest run --coverage
```

### 6.1 Testes-âncora

Divergência aqui gera objeção `A-DEV-08`, de severidade crítica, e **não pode ser resolvida como utopia**: é o único achado da suíte com essa restrição. Mudar um valor-âncora exige decisão explícita registrada, não um laço de correção. Rodam isolados, com evidência impressa:

| Âncora | Valor esperado |
|--------|---------------:|
| Reconstrução do orçamento do CME | R$ 141.194,42 |
| BDI analítico do CME | 23,6245% |
| SINAPI 87622, SP, onerado | R$ 40,63 |
| SINAPI 87622, SP, desonerado | R$ 39,37 |
| Importação do pacote 07/2026 | 10.544 composições, 4.875 insumos |

```bash
pytest tests/anchors/ -v --no-header
```

---

## 7. G5 — Desempenho

Medido em máquina de referência, com número registrado a cada estágio. Regressão acima de 20% reprova.

Tabela consolidada em `VERTICE-otimizacao-processo.md` §8, que é a fonte única das metas. Reproduzidas aqui as de maior peso:

| Métrica | Limite |
|---------|-------:|
| Busca textual na base completa | 100 ms |
| Busca semântica por similaridade | 50 ms |
| Importação da base completa | 180 s |
| Explosão de composição de três níveis | 50 ms |
| Recálculo de orçamento com 200 itens | 200 ms |
| Recálculo incremental após revisão | 300 ms |
| Antagonista, Camada 1, orçamento completo | 1 s |
| Partida do app até a janela utilizável | 3 s |

O limite de recálculo é o gatilho de revisão da ADR-009: se estourar, o registro declarativo de fórmulas deixa de bastar.

---

## 8. G6 — Segurança e integridade

| Código | Verificação |
|--------|-------------|
| `VS-01` | Chave de API apenas no cofre do sistema operacional, nunca em arquivo |
| `VS-02` | Sidecar recusa requisição sem token de sessão |
| `VS-03` | Sidecar escuta apenas em `127.0.0.1` |
| `VS-04` | Nenhum processo órfão após fechar a janela |
| `VS-05` | Backup gerado e **restaurado com sucesso** na bateria |
| `VS-06` | App recusa abrir banco em caminho de rede |
| `VS-07` | Modo sem IA não produz tráfego externo — verificado por captura |
| `VS-08` | Nenhum dado de projeto no payload enviado ao provedor de IA |
| `VS-09` | Dependências sem vulnerabilidade conhecida de severidade alta |

```bash
pip-audit
npm audit --audit-level=high
pytest tests/infra/ -v          # T-INFRA-01 a 04
```

---

## 9. G7 — Revisão adversarial

Portão humano. Não é automatizável e é o último por ser o mais caro.

**Regra:** quem implementou não conduz.

Roteiro:

1. Percorrer as dez dimensões de risco da §3.1 das REGRAS, uma a uma, tentando produzir falha.
2. Rodar o agente antagonista contra um orçamento real montado no app — não contra dado de teste.
3. Conferir se cada decisão do estágio tem gatilho de revisão registrado.
4. Reler o registro de utopias: alguma condição de reabertura ocorreu?
5. Listar o que foi implementado **diferente** da especificação e atualizar o documento, ou registrar a divergência.
6. Produzir o relatório de sessão da §7.1 das REGRAS.

Saída: lista de achados com severidade, que segue para o antagonista e entra no laço da §2.3 das REGRAS.

---

## 10. Portões por estágio

Nem todo portão se aplica a todo estágio. O que não se aplica é declarado, não omitido.

| Portão | F0 | F1 | F2 | F3 | F4 |
|--------|:--:|:--:|:--:|:--:|:--:|
| G0 higiene | ● | ● | ● | ● | ● |
| G1 Python | ● | ● | ● | ● | ● |
| G2 front-end | — | ● | ● | ● | ● |
| G3 documentação | ● | ● | ● | ● | ● |
| G4 testes | ● | ● | ● | ● | ● |
| G5 desempenho | ● | ● | ● | ● | ● |
| G6 segurança | parcial | ● | ● | ● | ● |
| G7 adversarial | ● | ● | ● | ● | ● |
| G8 convergência | ● | ● | ● | ● | ● |

Na F0, o G6 cobre apenas integridade de dados e backup: ainda não existe interface nem chamada de IA.

---

## 10.1 G8 — Convergência do laço

Portão final, medido sobre o estágio inteiro e não sobre uma execução.

| Verificação | Critério |
|-------------|----------|
| Achados sem destino declarado | Zero |
| Objeções em rodada aberta ao encerrar | Zero |
| Divergências de laço | Registradas com métrica e ponto de retorno |
| Utopias criadas | Todas com condição de reabertura preenchida |
| Proporção de objeções viradas utopia | Abaixo de 15% — acima disso, gatilho da ADR-012 |
| Utopias de estágios anteriores | Relidas, com situação atualizada |
| **Auditoria de proveniência** | Zero campo numérico persistido sem cadeia de origem resolvível |

Proporção alta de utopia não é falha de disciplina: é sintoma de que a arquitetura não comporta o que está sendo pedido dela. O gatilho manda replanejar a fase, não insistir.

---

## 11. Registro de execução

Cada execução da suíte gera um registro versionado em `registros/lint-<estagio>-<data>.md`, contendo: estágio, data, commit, resultado por portão, números de desempenho medidos, achados e seus destinos, divergências de laço com métricas, utopias criadas ou reabertas, e assinatura de quem conduziu o G7.

Comparar o registro do estágio atual com o anterior é o que revela regressão lenta — a que nenhum portão isolado pega, porque cada estágio piora só um pouco.

---

## 12. Histórico

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.8 | 13/09/2026 | Documentos `VERTICE-*.md` e `INDICE.md` movidos para `.md/` (feito pelo usuário). `tools/schema_lint.py` ganha `--docs` separado de `--raiz`, já que a pasta de código (`core/`) e a pasta de documentos deixaram de coincidir. Exemplos de comando atualizados |
| 1.7 | 13/09/2026 | Caminhos dos comandos atualizados para o rename retroativo: `nucleo/`→`core/`, `ferramentas/`→`tools/` (com `lint_dominio.py`→`domain_lint.py`, `lint_esquema.py`→`schema_lint.py`, `lint_markdown.py`→`markdown_lint.py`), `testes/`→`tests/` |
| 1.6 | 13/09/2026 | `VD-01` ganha isenção escopada a `reference_base/adapters/` — a fronteira que lê `.xlsx` precisa reconhecer o `float` nativo do formato para converter uma única vez, mesmo padrão de isenção diretorial já usado por `VD-05` |
| 1.5 | 13/09/2026 | `VM-11` amarra o conjunto compatível do `INDICE.md`. Laço curto contínuo na §1.1, com critério de dez segundos. `VD-15` e `VD-16` implementados em `tools/schema_lint.py`. Mutação restrita a `domain/` e `pricing/` por custo |
| 1.4 | 13/09/2026 | Limites duros contra god code: `VD-09` a `VD-14` no Python, `VF-07` e `VF-08` no front-end |
| 1.3 | 13/09/2026 | Auditoria de proveniência entra no portão G8 |
| 1.2 | 13/09/2026 | Índice de mutação e fuzzing do importador entram no portão G4. Metas de desempenho passam a referenciar a fonte única |
| 1.1 | 13/09/2026 | A suíte deixa de reprovar e passa a alimentar o antagonista. Encerramento de estágio condicionado a destino declarado por achado, não a achado zerado. Portão G8 de convergência criado |
| 1.0 | 13/09/2026 | Documento inicial. Regras `VM-01` a `VM-10` derivadas da revisão documental de 13/09/2026; `VM-08` originada em incidente real de contraste em Mermaid |
