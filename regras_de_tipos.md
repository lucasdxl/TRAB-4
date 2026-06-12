# Sistema de Regras de Validação de Tipos

## Tipos Suportados

| Tipo | Descrição |
|------|-----------|
| `INT` | Número inteiro (ex: `5`, `42`) |
| `REAL` | Número real de ponto flutuante (ex: `3.14`, `9.0`) |
| `BOOL` | Valor lógico — resultado de operações relacionais |
| `INDEFINIDO` | Tipo ainda não inferido (resolvido em fases posteriores) |
| `ERRO` | Tipo inválido — resultado de operação incompatível |

---

## Regras de Inferência (Cálculo de Sequentes)

### Literais

─────────────────  (T-INT)
Γ ⊢ n : INT        (n ∈ Z)

─────────────────  (T-REAL)
Γ ⊢ r : REAL       (r ∈ R, r ∉ Z)


### Variáveis e Memória

Γ(x) = T
─────────────  (T-VAR)
Γ ⊢ x : T

Γ ⊢ e : T    Γ(x) = T
────────────────────────  (T-MEM-ATRIB)
Γ ⊢ (e MEM x) : T


 Γ(x) = T
──────────────────  (T-MEM-LEITURA)
Γ ⊢ (x) : T


### Operadores Aritméticos Gerais (+, -, *, ^)

Γ ⊢ e1 : T1    Γ ⊢ e2 : T2    T1,T2 ∈ {INT,REAL}
────────────────────────────────────────────────────  (T-ARIT)
Γ ⊢ (e1 e2 op) : promover(T1, T2)

onde: promover(INT, INT)  = INT
promover(INT, REAL) = REAL
promover(REAL, INT) = REAL
promover(REAL,REAL) = REAL


### Divisão Inteira e Resto (/, %)

Γ ⊢ e1 : INT    Γ ⊢ e2 : INT
────────────────────────────────  (T-DIVI)
Γ ⊢ (e1 e2 /) : INT

Γ ⊢ e1 : INT    Γ ⊢ e2 : INT
────────────────────────────────  (T-MOD)
Γ ⊢ (e1 e2 %) : INT


### Divisão Real (|)

Γ ⊢ e1 : T1    Γ ⊢ e2 : T2    T1,T2 ∈ {INT,REAL}
────────────────────────────────────────────────────  (T-DIVR)
Γ ⊢ (e1 e2 |) : REAL


### Operadores Relacionais (<, >)

Γ ⊢ e1 : T1    Γ ⊢ e2 : T2    T1,T2 ∈ {INT,REAL}
────────────────────────────────────────────────────  (T-REL)
Γ ⊢ (e1 e2 op_rel) : BOOL


### Estruturas de Controle

Γ ⊢ c : BOOL    Γ ⊢ e1 : T1    Γ ⊢ e2 : T2
───────────────────────────────────────────────  (T-IF)
Γ ⊢ IF(c, e1, e2) : ⊥

Γ ⊢ c : BOOL    Γ ⊢ corpo : T
─────────────────────────────────  (T-WHILE)
Γ ⊢ WHILE(c, corpo) : ⊥

n1,n2 : INT    Γ, x:INT ⊢ corpo : T
──────────────────────────────────────  (T-FOR)
Γ ⊢ FOR(n1, n2, x, corpo) : ⊥



### Referência a Resultado (RES)

histórico[n] = T    0 ≤ n < |histórico|
──────────────────────────────────────────  (T-RES)
Γ ⊢ (n RES) : T


---

## Erros de Tipo

| Código | Regra violada | Exemplo |
|--------|--------------|---------|
| `OPERADOR_EXIGE_INT` | T-DIVI ou T-MOD com REAL | `(3.5 2 /)` |
| `TIPOS_INCOMPATIVEIS_OPERADOR` | T-ARIT com não-numérico | `(BOOL 2 +)` |
| `TIPOS_INCOMPATIVEIS_RELACIONAL` | T-REL com não-numérico | operando não INT/REAL |
| `ATRIBUICAO_TIPO_INCOMPATIVEL` | T-MEM-ATRIB com T incompatível | REAL atribuído a variável INT |
| `VARIAVEL_NAO_DECLARADA` | T-VAR sem Γ(x) definido | uso antes de definição |
| `CONDICAO_NAO_BOOL` | T-IF/T-WHILE sem BOOL | condição não-relacional |
