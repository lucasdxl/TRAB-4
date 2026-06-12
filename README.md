# Analisador Semântico — Fase 3

**Instituição:** Pontifícia Universidade Católica do Paraná - Campus Curitiba  
**Ano/Semestre:** 2026/1  
**Disciplina:** Compiladores  
**Professor:** Frank Coelho de Alcantara  
**Nome do grupo no Canvas:** RA3_12  

---

## Integrantes

| Nome | GitHub |
|------|--------|
| João Henrique Tomaz Dutra | [@Jhtomaz](https://github.com/Jhtomaz) |
| Lucas Balint Vilar | [@lucasdxl](https://github.com/lucasdxl) |
| Paulo Henrique Eidi Mino | [@phmino](https://github.com/phmino) |
| Victor Rahal Basseto | [@victorrahal](https://github.com/victorrahal) |

**Linguagem de implementação:** Python 3

---

## Como executar

### Pré-requisito

Python 3.10 ou superior. Sem dependências externas.

### Executar o analisador

Na raiz do projeto:

```bash
python AnalisadorSemantico.py <arquivo_de_teste>
```

Exemplo com programa válido:

```bash
python AnalisadorSemantico.py teste1.txt
```

Exemplo com programa com erros semânticos:

```bash
python AnalisadorSemantico.py teste2.txt
```

O programa exibe no terminal:
- Resultado da análise léxica (tokens reconhecidos)
- Resultado da análise sintática (árvore gerada)
- Resultado da análise semântica (erros encontrados ou OK)
- Caminhos de todos os artefatos gerados em `saida/`

Retorna código de saída `0` se sem erros semânticos, `1` se houver erros.

### Executar os testes

```bash
# Todos os testes de uma vez
python -m pytest testes/ -v

# Por módulo
python -m pytest testes/testeLexico.py        -v   # Aluno 1 — léxico
python -m pytest testes/testeSintatico.py     -v   # Aluno 1 — sintático
python -m pytest testes/testeTabelaSimbolos.py -v  # Aluno 2 — tabela de símbolos
python -m pytest testes/testeSemantico.py     -v   # Aluno 3 — verificação de tipos
python -m pytest testes/testeIntegracao.py    -v   # Aluno 4 — integração completa
```

---

## Descrição da Linguagem

A linguagem é baseada em **notação polonesa reversa (RPN)**. Cada instrução é
delimitada por parênteses. Todo programa deve começar com `(START)` e terminar
com `(END)`.

### Estrutura geral

```
(START)
(instrução 1)
(instrução 2)
...
(END)
```

### Comentários

Comentários são delimitados por `*{` e `}*` e podem aparecer em qualquer
posição: linha inteira, final de linha ou entre tokens de uma expressão.

```
*{ comentário em linha inteira }*
(5 3 +) *{ comentário no fim da linha }*
(5 *{ entre operandos }* 3 +)
```

### Expressões aritméticas

Operações seguem a notação `(operando operando operador)`:

```
(5 3 +)           -> soma: 5 + 3
(10 2 -)          -> subtração: 10 - 2
(4 3 *)           -> multiplicação: 4 * 3
(9.0 3.0 |)       -> divisão real: 9.0 / 3.0
(9 4 /)           -> divisão inteira: 9 // 4
(9 4 %)           -> resto: 9 % 4
(2 3 ^)           -> potenciação: 2 ** 3
```

Expressões podem ser aninhadas sem limite:

```
((A B *) (C D +) -)    -> (A*B) - (C+D)
```

### Comandos especiais

| Sintaxe | Descrição |
|---------|-----------|
| `(V MEM X)` | Armazena o valor `V` na variável `X` |
| `(X)` | Retorna o valor armazenado em `X` (0 se não inicializada) |
| `(N RES)` | Retorna o resultado da linha N posições atrás (N ≥ 1) |

### Estruturas de controle

```
(IF (condicao) (ramo_verdadeiro) (ramo_falso))
(WHILE (condicao) (corpo))
(FOR inicio fim VARIAVEL (corpo))
```

As condições usam operadores relacionais `<` e `>`:

```
(IF (TOTAL 10 <) (3 3 +) (2 2 -))
(WHILE (CONT 5 <) ((CONT 1 +) MEM CONT))
(FOR 1 5 I (I 2 *))
```

---

## Tipos suportados

| Tipo | Descrição | Exemplos |
|------|-----------|---------|
| `INT` | Número inteiro | `5`, `42`, `0` |
| `REAL` | Número real de ponto flutuante | `3.14`, `9.0`, `2.5` |
| `BOOL` | Valor lógico — resultado de operações relacionais | resultado de `<` ou `>` |

### Regras de promoção de tipo

Nas operações `+`, `-`, `*`, `^` e `|`:

| Operando 1 | Operando 2 | Resultado |
|-----------|-----------|-----------|
| `INT` | `INT` | `INT` |
| `INT` | `REAL` | `REAL` |
| `REAL` | `INT` | `REAL` |
| `REAL` | `REAL` | `REAL` |

As operações `/` e `%` **exigem ambos os operandos INT** e retornam `INT`.  
A operação `|` sempre retorna `REAL`.  
As condições `<` e `>` aceitam `INT` ou `REAL` e retornam `BOOL`.

---

## Regras de definição e uso de variáveis

- Identificadores são sequências de **letras latinas maiúsculas** (ex: `X`, `TOTAL`, `CONTADOR`).
- Uma variável é **definida** no momento de sua primeira atribuição via `MEM`.
- O tipo da variável é inferido no momento da definição e **não pode ser alterado**.
- Usar uma variável antes de defini-la é **erro semântico** (`VARIAVEL_NAO_DECLARADA`).
- Reatribuir uma variável com tipo diferente do original é **erro semântico** (`REDEFINICAO_INCOMPATIVEL`).
- A variável de controle do `FOR` é automaticamente do tipo `INT`.
- O escopo de todas as variáveis é **global** por arquivo.

---

## Exemplos de programas semanticamente válidos

### teste1.txt — programa completo com todos os recursos

```
(START)
*{ Programa valido: todas as operacoes, memoria, RES, IF, WHILE, FOR }*
(5 3 +)
(10 2 -)
(4 3 *)
(9.0 3.0 |)
(9 4 /)
(9 4 %)
(2 3 ^)
(15 MEM TOTAL)
(2.5 MEM PESO)
(TOTAL)
(1 RES)
((5 3 +) 2 *)
(IF (TOTAL 10 <) (3 3 +) (2 2 -))
(0 MEM CONT)
(WHILE (CONT 5 <) ((CONT 1 +) MEM CONT))
(FOR 1 5 I (I 2 *))
(END)
```

### teste3.txt — expressões aninhadas e comentários em várias posições

```
(START)
*{ Programa 3: expressoes aninhadas, comentarios em varias posicoes }*
(2 3 +) *{ comentario no fim da linha }*
*{ comentario em linha inteira }*
((3 2 +) (5 1 -) *)
(((2 3 +) 4 *) 2 /)
(9 4 %)
(8.0 *{ comentario entre tokens }* 2.0 |)
(2 3 ^)
(0 MEM BASE)
(1 MEM FATOR)
(5 MEM LIMITE)
(BASE)
(1 RES)
((BASE FATOR +) MEM BASE)
(IF (BASE LIMITE <) (BASE 2 *) (BASE FATOR -))
(0 MEM N)
(WHILE (N 4 <) ((N 1 +) MEM N))
(FOR 1 5 K (K K *))
(END)
```

---

## Exemplos de programas semanticamente inválidos

### teste2.txt — múltiplos erros semânticos

```
(START)
(10 MEM INTVAR)
(3.5 MEM REALVAR)
(3.5 2 /)           *{ ERRO 1: divisao inteira com REAL }*
(5 2.5 %)           *{ ERRO 2: modulo com REAL }*
(XSEMDEF 5 +)       *{ ERRO 3: variavel nao declarada }*
(100 RES)           *{ ERRO 4: RES referencia linha inexistente }*
(END)
```

Erros detectados:
- `OPERADOR_EXIGE_INT` — `/` e `%` usados com REAL
- `VARIAVEL_NAO_DECLARADA` — `XSEMDEF` nunca definida
- `RES_INDICE_INVALIDO` — índice 100 maior que o histórico disponível

---

## Arquivos de saída (`saida/`)

Todos os artefatos são gerados na pasta `saida/` a cada execução:

| Arquivo | Formato | Descrição |
|---------|---------|-----------|
| `tabela_simbolos.json` | JSON | Tabela de símbolos com tipos, escopos e linhas |
| `tabela_simbolos.md` | Markdown | Tabela de símbolos em formato legível |
| `erros_declaracao.json` | JSON | Erros semânticos encontrados (vazio se nenhum) |
| `arvore_atribuida.json` | JSON | Árvore sintática anotada com tipos inferidos |
| `arvore_atribuida.md` | Markdown | Árvore atribuída em formato legível |
| `Assembly.s` | Assembly ARMv7 | Código gerado — **apenas se sem erros semânticos** |
| `ultima_execucao.json` | JSON | Indica qual arquivo de teste foi analisado por último |

Para documentação adicional, consulte:
- [`gramatica_ebnf.md`](gramatica_ebnf.md) — gramática em formato EBNF
- [`regras_de_tipos.md`](regras_de_tipos.md) — regras de validação de tipos em cálculo de sequentes
