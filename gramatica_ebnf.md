# Gramática Atribuída — Formato EBNF

**Grupo:** RA3_12  
**Linguagem:** baseada em RPN (Notação Polonesa Reversa)  
**Tipo de parser:** LL(1)

Convenção: **minúsculas** = não-terminais · **`"texto"`** = terminais literais · **MAIÚSCULAS** = classes de tokens.

---

## Regras de Produção

```ebnf
programa    ::= "(" "START" ")" linhas

linhas      ::= "(" linhas_rest

linhas_rest ::= "END" ")"
              | corpo ")" linhas

linha       ::= "(" corpo ")"

corpo       ::= "IF"    condicao linha linha
              | "WHILE" condicao linha
              | "FOR"   INT INT MEM_ID linha
              | INT     resto_corpo
              | REAL    resto_corpo
              | MEM_ID  cauda_mem
              | linha   resto_corpo

cauda_mem   ::= ε
              | resto_corpo

resto_corpo ::= "RES"
              | "MEM" MEM_ID
              | operando operador_arit

operando    ::= INT
              | REAL
              | MEM_ID
              | linha

operador_arit ::= "+" | "-" | "*" | "|" | "/" | "%" | "^"

condicao    ::= "(" operando operando op_rel ")"

op_rel      ::= "<" | ">"
```

---

## Classes de Tokens (Terminais)

| Token | Padrão | Exemplos |
|-------|--------|---------|
| `INT` | Sequência de dígitos sem ponto | `5`, `42`, `0` |
| `REAL` | Dígitos com exatamente um ponto decimal | `3.14`, `9.0` |
| `MEM_ID` | Sequência de letras latinas maiúsculas | `X`, `TOTAL`, `CONT` |
| `"("` | Parêntese esquerdo | |
| `")"` | Parêntese direito | |
| `"START"` | Palavra reservada de início | |
| `"END"` | Palavra reservada de fim | |
| `"MEM"` | Palavra reservada de atribuição | |
| `"RES"` | Palavra reservada de referência | |
| `"IF"` | Palavra reservada de decisão | |
| `"WHILE"` | Palavra reservada de repetição | |
| `"FOR"` | Palavra reservada de laço contado | |
| `"+"` `"-"` `"*"` `"^"` | Operadores aritméticos gerais | |
| `"/"` | Divisão inteira | |
| `"%"` | Resto inteiro | |
| `"\|"` | Divisão real | |
| `"<"` `">"` | Operadores relacionais | |

### Comentários (descartados pelo léxico)
```
*{ qualquer texto aqui }*
```
Podem aparecer em qualquer posição: linha inteira, fim de linha ou entre tokens.

---

## Gramática Atribuída — Atributos e Ações Semânticas

Cada não-terminal carrega um atributo sintetizado **`.tipo`** que representa o tipo inferido da expressão.  
Tipos possíveis: `INT`, `REAL`, `BOOL`, `INDEFINIDO`.

### `operando`

```
operando ::= INT
    { operando.tipo := INT }

operando ::= REAL
    { operando.tipo := REAL }

operando ::= MEM_ID
    { verificar MEM_ID ∈ Γ;
      operando.tipo := Γ(MEM_ID).tipo }

operando ::= linha
    { operando.tipo := linha.tipo }
```

### `operador_arit` e `resto_corpo`

```
resto_corpo ::= "RES"
    { resto_corpo.tipo := histórico[N].tipo }

resto_corpo ::= "MEM" MEM_ID
    { verificar compatibilidade de tipos;
      Γ(MEM_ID).tipo := esquerdo.tipo;
      resto_corpo.tipo := esquerdo.tipo }

resto_corpo ::= operando operador_arit
    onde operador_arit ∈ { "+", "-", "*", "^" }:
    { verificar esquerdo.tipo ∈ {INT, REAL};
      verificar operando.tipo ∈ {INT, REAL};
      resto_corpo.tipo := promover(esquerdo.tipo, operando.tipo) }

    onde operador_arit ∈ { "/", "%" }:
    { verificar esquerdo.tipo = INT;
      verificar operando.tipo = INT;
      resto_corpo.tipo := INT }

    onde operador_arit = "|":
    { verificar esquerdo.tipo ∈ {INT, REAL};
      verificar operando.tipo ∈ {INT, REAL};
      resto_corpo.tipo := REAL }
```

### `condicao`

```
condicao ::= "(" operando₁ operando₂ op_rel ")"
    { verificar operando₁.tipo ∈ {INT, REAL};
      verificar operando₂.tipo ∈ {INT, REAL};
      condicao.tipo := BOOL }
```

### `corpo` — estruturas de controle

```
corpo ::= "IF" condicao linha₁ linha₂
    { verificar condicao.tipo = BOOL;
      corpo.tipo := ⊥ }

corpo ::= "WHILE" condicao linha
    { verificar condicao.tipo = BOOL;
      corpo.tipo := ⊥ }

corpo ::= "FOR" INT₁ INT₂ MEM_ID linha
    { Γ(MEM_ID).tipo := INT;
      corpo.tipo := ⊥ }
```

---

## Regra de Promoção de Tipo

```
promover(INT,  INT)  = INT
promover(INT,  REAL) = REAL
promover(REAL, INT)  = REAL
promover(REAL, REAL) = REAL
```

---

## Conjuntos FIRST e FOLLOW

| Não-terminal | FIRST | FOLLOW |
|---|---|---|
| `programa` | `(` | `$` |
| `linhas` | `(` | `$` |
| `linhas_rest` | `END`, `IF`, `WHILE`, `FOR`, `INT`, `REAL`, `MEM_ID`, `(` | `$`, `)` |
| `linha` | `(` | `(`, `)`, `END` |
| `corpo` | `IF`, `WHILE`, `FOR`, `INT`, `REAL`, `MEM_ID`, `(` | `)` |
| `cauda_mem` | `RES`, `MEM`, `INT`, `REAL`, `MEM_ID`, `(`, `ε` | `)` |
| `resto_corpo` | `RES`, `MEM`, `INT`, `REAL`, `MEM_ID`, `(` | `)` |
| `operando` | `INT`, `REAL`, `MEM_ID`, `(` | `+`, `-`, `*`, `\|`, `/`, `%`, `^`, `)` |
| `operador_arit` | `+`, `-`, `*`, `\|`, `/`, `%`, `^` | `)` |
| `condicao` | `(` | `(` |
| `op_rel` | `<`, `>` | `)` |

---

## Exemplos de Derivação

### `(5 3 +)` — expressão aritmética simples

```
linha
  → "(" corpo ")"
  → "(" INT resto_corpo ")"
  → "(" 5 operando operador_arit ")"
  → "(" 5 INT "+" ")"
  → "(" 5 3 + ")"
```

### `(IF (TOTAL 10 <) (3 3 +) (2 2 -))` — decisão

```
linha
  → "(" corpo ")"
  → "(" "IF" condicao linha linha ")"
  → "(" "IF" "(" operando operando op_rel ")" linha linha ")"
  → "(" "IF" "(" MEM_ID INT "<" ")" linha linha ")"
  → "(" "IF" "(" TOTAL 10 < ")" "(" 3 3 + ")" "(" 2 2 - ")" ")"
```