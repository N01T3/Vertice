# VÉRTICE — Fundamentos

Bases acadêmicas e critérios de rigor que sustentam cada decisão do projeto.

**Versão:** 1.0
**Data:** 13/09/2026
**Relacionado:** `VERTICE-arquitetura.md`, `VERTICE-decisoes.md`

---

## 0. Como ler

Cada seção nomeia um problema de engenharia enfrentado pelo VÉRTICE, o princípio que o resolve e a referência que o sustenta. As referências são obras estabelecidas da literatura de computação e engenharia; **verificar DOI e edição antes de citar formalmente** — este documento foi escrito sem acesso direto aos textos, a partir do conhecimento consolidado da área.

O objetivo não é acumular citação. É que nenhuma decisão do projeto fique sustentada apenas em preferência.

---

## 1. Hierarquia de evidência

Toda decisão registrada em `VERTICE-decisoes.md` declara em que nível se apoia. Nível abaixo de 3 exige plano de medição para entrar.

| Nível | Fonte | Exemplo no projeto |
|-------|-------|--------------------|
| 1 | Norma ou padrão internacional | IEEE 754, ISO 16739 (IFC), ABNT NBR 15965 |
| 2 | Literatura revisada por pares | Parnas 1972, Claessen e Hughes 2000 |
| 3 | Documentação primária do fornecedor ou do padrão | Documentação da biblioteca de leitura DXF; especificação do SQLite |
| 4 | Consenso de praticantes, com fonte identificável | Diretrizes de modelagem para medição em BIM |
| 5 | Opinião ou preferência | Nome do produto |

Regra: **decisão de nível 4 ou 5 carrega gatilho de revisão obrigatório**. Decisão de nível 1 a 3 pode ser estável.

---

## 2. Modularização

**Problema.** Sistema com dez módulos que precisam evoluir separadamente, construídos em parte por agentes.

**Princípio.** Cada módulo esconde uma decisão de projeto provável de mudar — o *segredo* do módulo — e expõe apenas uma interface. A decomposição correta não segue o fluxograma do processamento; segue as decisões que podem mudar.

**Referência.** Parnas, D. L. (1972). *On the criteria to be used in decomposing systems into modules*. Communications of the ACM, 15(12).

**Aplicação.** O segredo de cada módulo do VÉRTICE:

| Módulo | Segredo que esconde |
|--------|---------------------|
| Adaptador de base | O formato do arquivo de cada base de preços |
| Regras de medição | Como cada serviço é quantificado |
| Motor de markup | A fórmula de transformação custo → preço |
| Leitor CAD | O formato geométrico de entrada |
| Classificador | O provedor de IA e o prompt |
| Antagonista | O catálogo de regras de verificação |
| Pacote de domínio | Tudo que é específico de uma área |

Se dois módulos compartilham um segredo, são um módulo. Se um módulo tem dois segredos, são dois.

**Complemento.** Acoplamento e coesão como métricas de qualidade da decomposição: Stevens, W., Myers, G., Constantine, L. (1974). *Structured design*. IBM Systems Journal, 13(2). Módulo com alta coesão e baixo acoplamento é o que a regra `VD-14` — máximo de oito importadores — mede de forma grosseira e verificável.

---

## 3. Tamanho e complexidade

**Problema.** Agente de IA gera arquivo grande com naturalidade. Sem limite verificável, o repositório degrada.

**Princípio.** Complexidade ciclomática mede o número de caminhos linearmente independentes de uma função. Acima de dez, a função é difícil de testar exaustivamente.

**Referência.** McCabe, T. J. (1976). *A complexity measure*. IEEE Transactions on Software Engineering, SE-2(4).

**Complemento.** Sobre a "classe deus" e os limites de responsabilidade: Riel, A. J. (1996). *Object-Oriented Design Heuristics*. Addison-Wesley. Sobre profundidade de módulo — interface pequena, funcionalidade grande — como critério de bom projeto: Ousterhout, J. (2018). *A Philosophy of Software Design*. Yaknyam Press.

**Aplicação.** Regras `VD-09` a `VD-14` e `VF-07`, `VF-08`. Os números específicos — 300 linhas, 40 linhas, complexidade 10 — são nível 4: consenso de praticantes, com McCabe como base de nível 2 para o critério de complexidade. Por isso carregam gatilho de revisão.

**Contra o inchaço.** Wirth, N. (1995). *A plea for lean software*. IEEE Computer, 28(2). A seção de tecnologias recusadas em `VERTICE-otimizacao-processo.md` é aplicação direta.

---

## 4. Aritmética monetária

**Problema.** Orçamento é dinheiro. Ponto flutuante binário não representa 0,10 exatamente.

**Princípio.** Aritmética decimal com arredondamento controlado, conforme padrão.

**Referências.**
- IEEE 754-2008, *Standard for Floating-Point Arithmetic*, que introduz os formatos decimais.
- Goldberg, D. (1991). *What every computer scientist should know about floating-point arithmetic*. ACM Computing Surveys, 23(1).
- Cowlishaw, M. F. (2003). *Decimal floating-point: algorism for computers*. Proceedings of the 16th IEEE Symposium on Computer Arithmetic.

**Aplicação.** O módulo `decimal` do Python implementa a General Decimal Arithmetic Specification, base do IEEE 754-2008 decimal. Regra `VD-01` — `float` proibido em valor monetário — é nível 1.

---

## 5. Geometria

**Problema.** Dedução de vãos, detecção de ambiente fechado e área líquida exigem operações booleanas sobre polígonos e extração de faces de grafo planar. Feitas em ponto flutuante ingênuo, produzem resultado inconsistente em casos degenerados — segmentos quase coincidentes, pontos quase colineares.

**Princípios.**
- Predicados geométricos robustos com precisão adaptativa, para que orientação e interseção nunca dependam de erro de arredondamento.
- Operações booleanas sobre polígonos por varredura de segmentos.
- Ambiente fechado como face de subdivisão planar, extraída de estrutura de arestas dupla.

**Referências.**
- Shewchuk, J. R. (1997). *Adaptive precision floating-point arithmetic and fast robust geometric predicates*. Discrete & Computational Geometry, 18(3).
- Martínez, F., Rueda, A. J., Feito, F. R. (2009). *A new algorithm for computing Boolean operations on polygons*. Computers & Geosciences, 35(6).
- de Berg, M., Cheong, O., van Kreveld, M., Overmars, M. (2008). *Computational Geometry: Algorithms and Applications*, 3ª ed. Springer. Capítulo 2 para subdivisões planares e a estrutura DCEL.

**Aplicação.** ADR-023 e ADR-024. A biblioteca de geometria adotada no núcleo envolve um motor em C++ que implementa esses algoritmos; o VÉRTICE **não reimplementa** predicado geométrico. Reimplementar Shewchuk é a forma mais rápida de produzir área negativa.

---

## 6. Dados e busca

**Problema.** 1,25 milhão de linhas de preço por base, busca textual e por similaridade abaixo de 100 ms, tudo local.

**Princípios.**
- Modelo relacional para integridade e consulta declarativa.
- Motor embarcado, sem servidor, com transação e integridade referencial.
- Ranqueamento textual probabilístico.
- Busca por similaridade em espaço vetorial gerado por modelo de sentença.

**Referências.**
- Codd, E. F. (1970). *A relational model of data for large shared data banks*. Communications of the ACM, 13(6).
- Gaffney, K. P. et al. (2022). *SQLite: past, present, and future*. Proceedings of the VLDB Endowment, 15(12).
- Robertson, S., Zaragoza, H. (2009). *The probabilistic relevance framework: BM25 and beyond*. Foundations and Trends in Information Retrieval, 3(4).
- Reimers, N., Gurevych, I. (2019). *Sentence-BERT: sentence embeddings using Siamese BERT-networks*. EMNLP.

**Aplicação.** ADR-005 e ADR-025. A busca híbrida — textual mais vetorial — é a combinação que a literatura de recuperação de informação aponta como superior a qualquer uma isolada para consultas curtas com vocabulário técnico variável.

---

## 7. Regras como dados

**Problema.** Como medir cada serviço muda por edital, por escritório, por domínio. Codificar isso é congelar o que mais varia.

**Princípio.** Conhecimento declarativo separado do motor que o interpreta. É o fundamento da programação em lógica e dos sistemas baseados em regras: a regra é dado, a inferência é motor.

**Referências.**
- Ceri, S., Gottlob, G., Tanca, L. (1989). *What you always wanted to know about Datalog (and never dared to ask)*. IEEE Transactions on Knowledge and Data Engineering, 1(1).
- Codd (1970), já citado, para a separação entre dado e procedimento.

**Aplicação.** ADR-013 e a arquitetura de pacotes de domínio. O VÉRTICE não adota Datalog como linguagem — adota o princípio: regra de medição é tabela versionada, interpretada por um motor pequeno e estável. Adotar a linguagem seria tecnologia sem gargalo.

---

## 8. Escolha de linguagem por paradigma

**Problema.** Nenhuma linguagem serve bem a todos os paradigmas do sistema. A escolha precisa ser por problema, com referência.

| Paradigma enfrentado | Linguagem | Fundamento |
|----------------------|-----------|------------|
| Aritmética decimal, geometria, dados tabulares, leitura de CAD | **Python** | Ecossistema científico consolidado; `decimal` conforme IEEE 754-2008; vínculos maduros com motores geométricos em C++. Tipagem gradual permite rigor onde importa sem custo onde não importa |
| Interface de usuário reativa | **TypeScript** | Sistema de tipos estrutural sobre JavaScript, formalizado academicamente; captura erro de contrato entre componentes em tempo de compilação |
| Shell de processo, ciclo de vida, credenciais | **Rust** | Segurança de memória e ausência de corrida de dados provadas formalmente para o subconjunto seguro da linguagem |
| Regras de medição, pacotes de domínio | **Dado declarativo** (YAML, SQL) | Seção 7 |

**Referências.**
- Siek, J. G., Taha, W. (2006). *Gradual typing for functional languages*. Scheme and Functional Programming Workshop. Fundamento teórico do que `mypy --strict` aplica ao Python.
- Bierman, G., Abadi, M., Torgersen, M. (2014). *Understanding TypeScript*. ECOOP.
- Jung, R., Jourdan, J.-H., Krebbers, R., Dreyer, D. (2018). *RustBelt: securing the foundations of the Rust programming language*. POPL.
- Pierce, B. C. (2002). *Types and Programming Languages*. MIT Press. Referência geral para o valor de tipagem estática em fronteiras.

**Consequência honesta.** Python **não** é a escolha por ser a mais rápida nem a mais segura. É a escolha porque o domínio — geometria, decimal, planilha, CAD — tem seu ecossistema maduro ali, e reimplementar esse ecossistema em outra linguagem é custo sem retorno. Onde Python é fraco — segurança de memória no processo que guarda credencial — entra Rust, com prova formal como justificativa. A ADR-002 registra o custo dessa divisão.

---

## 9. Contratos e invariantes

**Problema.** Módulo construído por agente precisa de fronteira verificável, não de intenção.

**Princípio.** Pré-condição, pós-condição e invariante declaradas como parte da interface, verificáveis em execução.

**Referência.** Meyer, B. (1992). *Applying "Design by Contract"*. IEEE Computer, 25(10).

**Aplicação.** A tarefa com contrato de `VERTICE-AGENTS.md` e o `criterio_de_pronto` obrigatório. O contrato não é documentação: é o que o portão executa.

---

## 10. Verificação

**Problema.** Suíte de testes que passa sempre, inclusive com o código errado — o mesmo defeito da conferência auto-referente encontrada na planilha auditada.

**Princípios e referências.**

| Técnica | Princípio | Referência |
|---------|-----------|------------|
| Teste por propriedade | Declarar invariante; a ferramenta procura contraexemplo | Claessen, K., Hughes, J. (2000). *QuickCheck: a lightweight tool for random testing of Haskell programs*. ICFP |
| Teste metamórfico | Relação entre execuções quando o resultado esperado é desconhecido | Chen, T. Y., Cheung, S. C., Yiu, S. M. (1998). *Metamorphic testing: a new approach for generating next test cases*. Technical Report HKUST-CS98-01 |
| Teste de mutação | Alterar o código de propósito; mutante que sobrevive revela teste inútil | DeMillo, R. A., Lipton, R. J., Sayward, F. G. (1978). *Hints on test data selection: help for the practicing programmer*. IEEE Computer, 11(4) |
| Fuzzing | Entrada aleatória ou deformada para revelar falha de robustez | Miller, B. P., Fredriksen, L., So, B. (1990). *An empirical study of the reliability of UNIX utilities*. Communications of the ACM, 33(12) |

**Aplicação.** ADR-029 e portão G4. O índice de mutação é a única métrica que mede a suíte, não o código.

---

## 11. Separação de papéis

**Problema.** Quem propõe um valor tem viés a favor dele. Modelo que classifica e depois confere a própria classificação produz aprovação fluente.

**Princípio.** Separação de funções: nenhuma entidade executa e certifica a mesma transação. Diversidade de projeto: verificação independente feita por componente construído separadamente.

**Referências.**
- Clark, D. D., Wilson, D. R. (1987). *A comparison of commercial and military computer security policies*. IEEE Symposium on Security and Privacy. Formaliza a separação de funções como mecanismo de integridade.
- Avižienis, A. (1985). *The N-version approach to fault-tolerant software*. IEEE Transactions on Software Engineering, SE-11(12).
- Popper, K. (1959). *The Logic of Scientific Discovery*. Fundamento epistemológico: uma afirmação vale pelo que resistiu a tentativas de refutação, não pelo que a confirma.

**Aplicação.** ADR-011, ADR-012 e a regra "quem propõe não valida". O antagonista é a tentativa de refutação institucionalizada.

---

## 12. Proveniência

**Problema.** Todo número precisa responder de onde veio, em auditoria e dois anos depois.

**Princípio.** Proveniência como modelo de dados de primeira classe: entidade, atividade, agente e as relações entre eles.

**Referências.**
- W3C (2013). *PROV-DM: The PROV Data Model*. Recomendação W3C.
- Buneman, P., Khanna, S., Tan, W.-C. (2001). *Why and where: a characterization of data provenance*. ICDT.
- Merkle, R. C. (1987). *A digital signature based on a conventional encryption function*. CRYPTO. Base do endereçamento por conteúdo.

**Aplicação.** A cadeia de proveniência de `VERTICE-arquitetura.md` §4.1, o `id_origem` obrigatório e a ADR-026. O modelo do VÉRTICE é uma projeção simplificada do PROV-DM: origem, atividade que produziu e agente responsável.

---

## 13. Modelos de linguagem

**Problema.** O modelo produz texto plausível sem compromisso com verdade. Precisa ser confinado a onde plausibilidade não basta.

**Princípios.**
- Geração restrita a gramática: o formato é imposto durante a decodificação, não verificado depois.
- Geração aumentada por recuperação: o modelo responde a partir de documento recuperado, não de memória paramétrica.

**Referências.**
- Willard, B. T., Louf, R. (2023). *Efficient guided generation for large language models*. arXiv:2307.09702.
- Lewis, P. et al. (2020). *Retrieval-augmented generation for knowledge-intensive NLP tasks*. NeurIPS.

**Aplicação.** ADR-028 e o módulo de pesquisa profunda. O portão 7 — número sem documento é descartado — é a aplicação disciplinar do princípio de recuperação: se não há documento recuperado, não há resposta.

---

## 14. Software local

**Problema.** Aplicativo que precisa funcionar sem rede, com o dado sob controle do usuário, sem ficar refém de servidor.

**Princípio.** Software local-first: o dispositivo do usuário é a fonte primária; rede é otimização, não requisito.

**Referência.** Kleppmann, M., Wiggins, A., van Hardenberg, P., McGranaghan, M. (2019). *Local-first software: you own your data, in spite of the cloud*. Onward! (ACM SIGPLAN).

**Aplicação.** ADR-005, ADR-008 e a §5 da arquitetura. A degradação sem rede do módulo de pesquisa é consequência direta.

---

## 15. Segurança do processo

**Problema.** Sidecar que escuta em porta local e guarda credencial de API.

**Princípios.** Privilégio mínimo; mediação completa; projeto aberto — a segurança não depende do segredo do mecanismo.

**Referência.** Saltzer, J. H., Schroeder, M. D. (1975). *The protection of information in computer systems*. Proceedings of the IEEE, 63(9).

**Aplicação.** Token de sessão, escuta apenas em interface local, credencial no cofre do sistema operacional, antagonista com conexão somente leitura.

---

## 16. Responsabilidade técnica

**Problema.** Software que produz documento assinado por profissional com responsabilidade legal.

**Princípio.** Segurança como propriedade emergente do sistema sociotécnico, não do componente. Automação que remove o humano do laço de decisão transfere risco sem transferir responsabilidade.

**Referência.** Leveson, N. G. (2011). *Engineering a Safer World: Systems Thinking Applied to Safety*. MIT Press.

**Aplicação.** O responsável técnico confirma item a item; o antagonista exige resposta escrita sem impedir; a ata de objeções vai com o documento. O humano permanece no laço por projeto, não por falta de automação.

---

## 17. Registro de decisões

**Princípio.** Decisão arquitetural registrada com contexto, decisão e consequência, imutável depois de aceita, superada por nova decisão em vez de editada.

**Referência.** Nygard, M. (2011). *Documenting architecture decisions*. Cognitect blog. Nível 4 — prática consolidada sem revisão por pares, adotada por convenção.

**Aplicação.** `VERTICE-decisoes.md`, com o gatilho de revisão como acréscimo do projeto ao formato original.

---

## 18. O que não tem base acadêmica

Por honestidade, o que está no projeto sustentado apenas em nível 4 ou 5:

| Item | Nível | Gatilho de revisão |
|------|-------|--------------------|
| Nome VÉRTICE | 5 | Antes da F1 |
| Tauri 2 sobre pywebview | 4 | Dois incidentes de handshake na F0 |
| Limites numéricos de god code | 4 | Medição de defeitos por tamanho de arquivo na F2 |
| Lembrete no dia 12 | 4 | Data de publicação da base mudar |
| Cinco rodadas como limite do laço de correção | 5 | Distribuição real de rodadas na F1 |
| Sete passadas de esgotamento | 4 | Taxa de CPU revertida para código da base |
| Divisão de ferramentas entre agentes | 4 | Medição de tarefas devolvidas |

Nenhum destes é errado por estar nesse nível. Estão marcados para que ninguém os trate como se fossem lei.

---

## 19. Histórico

| Versão | Data | Alteração |
|--------|------|-----------|
| 1.0 | 13/09/2026 | Documento inicial. Hierarquia de evidência em cinco níveis; fundamento por problema com referência; linguagem por paradigma; inventário do que está sem base acadêmica |
