# Victor Rahal Basseto - Aluno 4

from collections import defaultdict

EPSILON = "ε"         
EOF = "$"           

TERMINAIS = {
    "LPAREN", "RPAREN",
    # Literais e identificadores
    "INT", "REAL", "MEM_ID",
    # Operadores aritméticos
    "OP_SUM", "OP_SUB", "OP_MUL",
    "OP_DIVR", "OP_DIVI", "OP_MOD", "OP_POW",
    # Operadores relacionais (para estruturas de controle)
    "OP_LT", "OP_GT",
    # Palavras reservadas
    "KW_START", "KW_END",
    "KW_RES", "KW_MEM",
    "KW_IF", "KW_WHILE", "KW_FOR",
    # Fim de entrada
    EOF,
}

NAO_TERMINAIS = {
    "programa", "bloco", "linhas", "linhas_rest",
    "linha", "abre_linha",
    "expressao", "corpo", "resto_corpo",
    "cauda_mem",
    "operando", "operador_arit",
    "comando_especial",
    "estrutura_controle", "cond_if", "laco_while", "laco_for",
    "condicao", "op_rel",
}

INICIO = "programa"

GRAMATICA = {
    "programa": [
        ["LPAREN", "KW_START", "RPAREN", "linhas"],
    ],
    "linhas": [
        ["LPAREN", "linhas_rest"],
    ],
    "linhas_rest": [
        ["KW_END", "RPAREN"],
        ["corpo", "RPAREN", "linhas"],
    ],
    "linha": [
        ["LPAREN", "corpo", "RPAREN"],
    ],
    "corpo": [
        ["KW_IF", "condicao", "linha", "linha"],
        ["KW_WHILE", "condicao", "linha"],
        ["KW_FOR", "INT", "INT", "MEM_ID", "linha"],
        ["INT", "resto_corpo"],
        ["REAL", "resto_corpo"],
        ["MEM_ID", "cauda_mem"],
        ["linha", "resto_corpo"],
    ],
    "cauda_mem": [
        [EPSILON],
        ["resto_corpo"],
    ],
    "resto_corpo": [
        ["KW_RES"],
        ["KW_MEM", "MEM_ID"],
        ["operando", "operador_arit"],
    ],
    "operando": [
        ["INT"],
        ["REAL"],
        ["MEM_ID"],
        ["linha"],
    ],
    "operador_arit": [
        ["OP_SUM"], ["OP_SUB"], ["OP_MUL"],
        ["OP_DIVR"], ["OP_DIVI"], ["OP_MOD"], ["OP_POW"],
    ],
    "expressao": [
        ["LPAREN", "operando", "operando", "operador_arit", "RPAREN"],
    ],
    "comando_especial": [
        ["LPAREN", "INT", "KW_RES", "RPAREN"],
        ["LPAREN", "REAL", "KW_MEM", "MEM_ID", "RPAREN"],
        ["LPAREN", "INT",  "KW_MEM", "MEM_ID", "RPAREN"],
        ["LPAREN", "MEM_ID", "RPAREN"],
    ],
    "estrutura_controle": [
        ["cond_if"], ["laco_while"], ["laco_for"],
    ],
    "cond_if": [
        ["LPAREN", "KW_IF", "condicao", "linha", "linha", "RPAREN"],
    ],
    "laco_while": [
        ["LPAREN", "KW_WHILE", "condicao", "linha", "RPAREN"],
    ],
    "laco_for": [
        ["LPAREN", "KW_FOR", "INT", "INT", "MEM_ID", "linha", "RPAREN"],
    ],
    "condicao": [
        ["LPAREN", "operando", "operando", "op_rel", "RPAREN"],
    ],
    "op_rel": [
        ["OP_LT"], ["OP_GT"],
    ],
}
NAO_TERMINAIS_ATIVOS = {
    "programa", "linhas", "linhas_rest", "linha",
    "corpo", "cauda_mem", "resto_corpo",
    "operando", "operador_arit",
    "condicao", "op_rel",
}

def eh_terminal(simbolo: str) -> bool:
    return simbolo in TERMINAIS or simbolo == EPSILON

def eh_nao_terminal(simbolo: str) -> bool:
    return simbolo in GRAMATICA

def calcularFirst(gramatica=GRAMATICA):
    first = defaultdict(set)
    for t in TERMINAIS:
        first[t] = {t}
    first[EPSILON] = {EPSILON}

    mudou = True
    while mudou:
        mudou = False
        for nt, producoes in gramatica.items():
            for prod in producoes:
                # Produção ε
                if prod == [EPSILON]:
                    if EPSILON not in first[nt]:
                        first[nt].add(EPSILON)
                        mudou = True
                    continue

                # Percorre símbolos da produção
                pode_epsilon = True
                for simb in prod:
                    novos = first[simb] - {EPSILON}
                    if not novos.issubset(first[nt]):
                        first[nt] |= novos
                        mudou = True
                    if EPSILON not in first[simb]:
                        pode_epsilon = False
                        break
                if pode_epsilon:
                    if EPSILON not in first[nt]:
                        first[nt].add(EPSILON)
                        mudou = True
    return dict(first)


def firstDeCadeia(cadeia, first):
    """FIRST de uma sequência de símbolos (α)."""
    resultado = set()
    if not cadeia:
        resultado.add(EPSILON)
        return resultado

    pode_epsilon = True
    for simb in cadeia:
        resultado |= (first[simb] - {EPSILON})
        if EPSILON not in first[simb]:
            pode_epsilon = False
            break
    if pode_epsilon:
        resultado.add(EPSILON)
    return resultado

def calcularFollow(gramatica, first, inicio=INICIO):
    follow = defaultdict(set)
    follow[inicio].add(EOF)

    mudou = True
    while mudou:
        mudou = False
        for nt, producoes in gramatica.items():
            for prod in producoes:
                for i, simb in enumerate(prod):
                    if not eh_nao_terminal(simb):
                        continue
                    beta = prod[i + 1:]
                    first_beta = firstDeCadeia(beta, first)

                    # Adiciona FIRST(β) \ {ε} a FOLLOW(simb)
                    novos = first_beta - {EPSILON}
                    if not novos.issubset(follow[simb]):
                        follow[simb] |= novos
                        mudou = True

                    # Se ε ∈ FIRST(β), adiciona FOLLOW(nt) a FOLLOW(simb)
                    if EPSILON in first_beta:
                        if not follow[nt].issubset(follow[simb]):
                            follow[simb] |= follow[nt]
                            mudou = True
    return dict(follow)

def construirTabelaLL1(gramatica, first, follow):
    """
    Retorna tupla (tabela, conflitos):
      - tabela: dict {(não_terminal, terminal): produção}
      - conflitos: lista de descrições de conflitos encontrados
    """
    tabela = {}
    conflitos = []

    for nt, producoes in gramatica.items():
        if nt not in NAO_TERMINAIS_ATIVOS:
            continue  # ignora NTs "documentais"
        for prod in producoes:
            first_alpha = firstDeCadeia(prod, first)

            # Para cada terminal a em FIRST(α) \ {ε}: M[A,a] = A → α
            for term in first_alpha - {EPSILON}:
                chave = (nt, term)
                if chave in tabela and tabela[chave] != prod:
                    conflitos.append(
                        f"Conflito em M[{nt},{term}]: "
                        f"{tabela[chave]} vs {prod}"
                    )
                tabela[chave] = prod

            # Se ε ∈ FIRST(α): para cada b em FOLLOW(A), M[A,b] = A → α
            if EPSILON in first_alpha:
                for term in follow[nt]:
                    chave = (nt, term)
                    if chave in tabela and tabela[chave] != prod:
                        conflitos.append(
                            f"Conflito em M[{nt},{term}] (ε-regra): "
                            f"{tabela[chave]} vs {prod}"
                        )
                    tabela[chave] = prod

    return tabela, conflitos

def construirGramatica():
    first = calcularFirst(GRAMATICA)
    follow = calcularFollow(GRAMATICA, first, INICIO)
    tabela, conflitos = construirTabelaLL1(GRAMATICA, first, follow)

    if conflitos:
        raise ValueError(
            "Gramática NÃO é LL(1). Conflitos encontrados:\n  - "
            + "\n  - ".join(conflitos)
        )

    return {
        "gramatica": GRAMATICA,
        "terminais": TERMINAIS,
        "nao_terminais": NAO_TERMINAIS,
        "inicio": INICIO,
        "first": first,
        "follow": follow,
        "tabela_ll1": tabela,
    }

def _fmt_conj(conj):
    return "{ " + ", ".join(sorted(conj)) + " }"


def _imprimir_resumo(info):
    print("=" * 70)
    print("GRAMÁTICA (regras de produção)")
    print("=" * 70)
    for nt, prods in info["gramatica"].items():
        alternativas = " | ".join(" ".join(p) for p in prods)
        print(f"  {nt}  ::=  {alternativas}")

    print()
    print("=" * 70)
    print("FIRST")
    print("=" * 70)
    for nt in sorted(NAO_TERMINAIS_ATIVOS):
        print(f"  FIRST({nt}) = {_fmt_conj(info['first'][nt])}")

    print()
    print("=" * 70)
    print("FOLLOW")
    print("=" * 70)
    for nt in sorted(NAO_TERMINAIS_ATIVOS):
        print(f"  FOLLOW({nt}) = {_fmt_conj(info['follow'][nt])}")

    print()
    print("=" * 70)
    print("TABELA LL(1) — entradas (nao_terminal, terminal) -> produção")
    print("=" * 70)
    for (nt, term), prod in sorted(info["tabela_ll1"].items()):
        print(f"  M[{nt:14s}, {term:10s}] = {nt} -> {' '.join(prod)}")


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    info = construirGramatica()
    _imprimir_resumo(info)
    print()
    print("Gramática validada como LL(1) (sem conflitos na tabela).")