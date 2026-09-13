# VÉRTICE — Módulo de Exportação

**Versão:** 0.2
**Documento-pai:** `VERTICE-arquitetura.md` §3
**Relacionado:** `VERTICE-agente-antagonista.md` (ata de objeções), `VERTICE-modulo-pesquisa.md` (dossiê), `VERTICE-modulo-precificacao.md` (planilha)

---

## 1. Princípio

> **Exportação é leitura. Nada que é exportado é calculado na exportação.**

O módulo recebe um orçamento já fechado e o escreve em formato que outra pessoa abre. Não calcula BDI, não resolve pendência, não formata número que ainda não existe. Se um valor precisa ser computado para caber na planilha, ele estava faltando no modelo — e o lugar de corrigir é o modelo.

Isso explica a regra de dependência do documento de arquitetura §3: **nenhum módulo importa `export`**. Quem exporta conhece todo mundo; ninguém conhece quem exporta. Acoplamento na direção contrária transformaria formato de saída em regra de negócio.

---

## 2. O que sai

| Artefato | Formato | Conteúdo | Obrigatório |
|----------|---------|----------|-------------|
| Planilha orçamentária | `.xlsx` | Itens, quantidades, preços, composições, BDI, AL, curva ABC | Sim |
| Ata de objeções | `.xlsx` e `.md` | Objeções do antagonista e resposta escrita do RT | Sim |
| Dossiê de pesquisa | `.md` com citação | Achados usados, URL, data de acesso, trecho | Quando houve pesquisa |
| Memória de cálculo | `.xlsx` | Conta legível por item, na coluna `memoria` | Sim |
| Acervo | `.xlsx` e `.json` | Base do escritório, a pedido | Não |

Os três primeiros saem juntos, num diretório único com o mesmo carimbo de data. Ata separada da planilha é ata que se perde.

---

## 3. Portões de exportação

Conforme ADR-012, **nada trava**. Mas duas condições produzem exportação marcada em vez de exportação recusada:

| Código | Condição | Efeito |
|--------|----------|--------|
| `E-EXP-01` | Objeção crítica sem resposta escrita do RT | Exporta com marca d'água `PRELIMINAR` e a objeção em aberto na ata |
| `E-EXP-02` | Item com `id_origem` que não resolve | Exporta com a célula marcada e a linha listada no quadro de pendências |
| `E-EXP-03` | Base de referência defasada em relação à data-base do orçamento | Exporta com aviso de defasagem no cabeçalho |

A resposta do RT exigida em `E-EXP-01` **pode ser refutação**. O que o portão exige é texto, não concordância. O motivo de a ata ser peça de defesa, e não controle interno, está em `VERTICE-agente-antagonista.md` §8 e não se repete aqui.

---

## 4. Representação numérica na saída

O banco guarda dinheiro em `INTEGER` de centavos e o resto em `TEXT` decimal, conforme `VERTICE-arquitetura.md` §5.1. A exportação é o **único** lugar que converte para a forma que o humano lê:

- Dinheiro: duas casas, separador decimal vírgula, milhar ponto.
- Coeficiente: **as casas exatas que a fonte publicou**. Não normaliza, não arredonda. `0,0350` da SINAPI sai `0,0350`.
- Percentual: quatro casas, porque BDI de 22,1234% e 22,12% são orçamentos diferentes em obra grande.

Arredondar coeficiente na saída quebra a reconstrução do valor por quem confere, que é exatamente o leitor deste arquivo.

---

## 5. Fora de escopo nesta versão

Declarado para não virar dívida silenciosa:

- Formato de tribunal específico (TCU, TCE-SP). Cada um quer um layout; entra quando houver um cliente com a exigência escrita.
- PDF assinado digitalmente.
- Exportação incremental ou diferencial entre revisões.

---

## Histórico

| Versão | Data | Mudança |
|--------|------|---------|
| 0.2 | 13/09/2026 | Referência ao módulo `export` (antes `exportacao`), acompanhando o rename retroativo de arquivos e pastas do código |
| 0.1 | 13/09/2026 | Documento inicial, mínimo. Criado para fechar a lacuna da tabela de módulos de `VERTICE-arquitetura.md` §3, que apontava para `—`. Portões `E-EXP-01` a `E-EXP-03` e regra de casas decimais na saída |
