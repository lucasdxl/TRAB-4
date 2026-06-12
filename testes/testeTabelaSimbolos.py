# Paulo Henrique Eidi Mino - Aluno 2
# Testes unitários do construirTabelaSimbolos.
# Agora os nós são construídos no formato CRU do parser LL(1) (Fase 2):
# {tipo_no, simbolo, producao, token, filhos}, com símbolos da gramática.

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from construirTabelaSimbolos import (  # noqa: E402
    construirTabelaSimbolos,
    TIPO_INT,
    TIPO_REAL,
    TIPO_INDEFINIDO,
    COD_VARIAVEL_NAO_DECLARADA,
    COD_REDEFINICAO_INCOMPATIVEL,
    COD_RES_INDICE_INVALIDO,
    COD_FOR_VARIAVEL_REDEFINIDA,
)

# ==========================================================================
# Construtores de nós crus (espelham a saída de parsear.py).
# ==========================================================================
def terminal(simbolo, valor, linha):
    return {
        "tipo_no": "terminal",
        "simbolo": simbolo,
        "producao": [],
        "token": {"tipo": simbolo, "valor": str(valor), "linha": linha},
        "filhos": [],
    }

def nt(simbolo, filhos, producao=None):
    return {
        "tipo_no": "nao_terminal",
        "simbolo": simbolo,
        "producao": producao or [f["simbolo"] for f in filhos],
        "token": None,
        "filhos": filhos,
    }

# --- Valores / operandos ---
def lit_int(valor, linha):
    return terminal("INT", valor, linha)

def lit_real(valor, linha):
    return terminal("REAL", valor, linha)

def mem(nome, linha):
    return terminal("MEM_ID", nome, linha)

def operando(no_valor):
    # operando -> INT | REAL | MEM_ID | linha
    return nt("operando", [no_valor])

def operador(op):
    # operador_arit -> OP_*
    return nt("operador_arit", [terminal(op, op, 0)])

def op_rel(op):
    return nt("op_rel", [terminal(op, op, 0)])

# --- Envoltório de linha aninhada: linha -> LPAREN corpo RPAREN ---
def L(corpo_node, linha=0):
    return nt(
        "linha",
        [terminal("LPAREN", "(", linha), corpo_node, terminal("RPAREN", ")", linha)],
        producao=["LPAREN", "corpo", "RPAREN"],
    )

# --- Corpos (conteúdo de uma linha) ---
def corpo_leitura(nome, linha):
    # corpo -> MEM_ID cauda_mem(ε)
    cauda = nt("cauda_mem", [], producao=["ε"])
    return nt("corpo", [mem(nome, linha), cauda], producao=["MEM_ID", "cauda_mem"])

def corpo_atribuicao(valor_node, alvo, linha):
    # resto_corpo -> KW_MEM MEM_ID
    resto = nt(
        "resto_corpo",
        [terminal("KW_MEM", "MEM", linha), terminal("MEM_ID", alvo, linha)],
        producao=["KW_MEM", "MEM_ID"],
    )
    sb = valor_node["simbolo"]
    if sb == "MEM_ID":
        cauda = nt("cauda_mem", [resto], producao=["resto_corpo"])
        return nt("corpo", [valor_node, cauda], producao=["MEM_ID", "cauda_mem"])
    return nt("corpo", [valor_node, resto], producao=[sb, "resto_corpo"])

def corpo_res(indice, linha):
    # corpo -> INT resto_corpo(KW_RES)
    resto = nt("resto_corpo", [terminal("KW_RES", "RES", linha)], producao=["KW_RES"])
    return nt("corpo", [lit_int(indice, linha), resto], producao=["INT", "resto_corpo"])

def corpo_expr(esq_node, op, dir_node):
    # corpo -> <esq> resto_corpo(operando operador_arit)
    resto = nt(
        "resto_corpo",
        [operando(dir_node), operador(op)],
        producao=["operando", "operador_arit"],
    )
    sb = esq_node["simbolo"]
    if sb == "MEM_ID":
        cauda = nt("cauda_mem", [resto], producao=["resto_corpo"])
        return nt("corpo", [esq_node, cauda], producao=["MEM_ID", "cauda_mem"])
    return nt("corpo", [esq_node, resto], producao=[sb, "resto_corpo"])

def cond(esq_node, op, dir_node, linha):
    # condicao -> LPAREN operando operando op_rel RPAREN
    return nt(
        "condicao",
        [
            terminal("LPAREN", "(", linha),
            operando(esq_node),
            operando(dir_node),
            op_rel(op),
            terminal("RPAREN", ")", linha),
        ],
        producao=["LPAREN", "operando", "operando", "op_rel", "RPAREN"],
    )

def corpo_if(condicao_node, entao_corpo, senao_corpo, linha):
    # corpo -> KW_IF condicao linha linha
    return nt(
        "corpo",
        [terminal("KW_IF", "IF", linha), condicao_node, L(entao_corpo, linha), L(senao_corpo, linha)],
        producao=["KW_IF", "condicao", "linha", "linha"],
    )

def corpo_while(condicao_node, corpo_body, linha):
    # corpo -> KW_WHILE condicao linha
    return nt(
        "corpo",
        [terminal("KW_WHILE", "WHILE", linha), condicao_node, L(corpo_body, linha)],
        producao=["KW_WHILE", "condicao", "linha"],
    )

def corpo_for(inicio, fim, var, corpo_body, linha):
    # corpo -> KW_FOR INT INT MEM_ID linha
    return nt(
        "corpo",
        [
            terminal("KW_FOR", "FOR", linha),
            lit_int(inicio, linha),
            lit_int(fim, linha),
            mem(var, linha),
            L(corpo_body, linha),
        ],
        producao=["KW_FOR", "INT", "INT", "MEM_ID", "linha"],
    )

def corpo_trivial(linha):
    """Corpo válido qualquer, usado quando o conteúdo não importa para o teste."""
    return corpo_expr(lit_int(1, linha), "OP_SUM", lit_int(1, linha))

# --- Programa completo: monta a cadeia linhas/linhas_rest crua ---
def programa(*corpos, linha_end=999):
    fim = nt(
        "linhas_rest",
        [terminal("KW_END", "END", linha_end), terminal("RPAREN", ")", linha_end)],
        producao=["KW_END", "RPAREN"],
    )
    cadeia = nt("linhas", [terminal("LPAREN", "(", linha_end), fim],
                producao=["LPAREN", "linhas_rest"])

    for corpo in reversed(corpos):
        lr = nt(
            "linhas_rest",
            [corpo, terminal("RPAREN", ")", 0), cadeia],
            producao=["corpo", "RPAREN", "linhas"],
        )
        cadeia = nt("linhas", [terminal("LPAREN", "(", 0), lr],
                    producao=["LPAREN", "linhas_rest"])

    return nt(
        "programa",
        [terminal("LPAREN", "(", 1), terminal("KW_START", "START", 1),
         terminal("RPAREN", ")", 1), cadeia],
        producao=["LPAREN", "KW_START", "RPAREN", "linhas"],
    )

# ==========================================================================
# Declaração / leitura / redefinição.
# ==========================================================================
class TestDeclaracaoBasica(unittest.TestCase):
    def test_declaracao_real_simples(self):
        arvore = programa(corpo_atribuicao(lit_real("3.0", 2), "A", 2))
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["tipo"], TIPO_REAL)
        self.assertEqual(resultado["simbolos"]["A"]["linha_definicao"], 2)
        self.assertEqual(resultado["erros"], [])

    def test_declaracao_int_simples(self):
        arvore = programa(corpo_atribuicao(lit_int("5", 2), "B", 2))
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["B"]["tipo"], TIPO_INT)
        self.assertEqual(resultado["erros"], [])

    def test_multiplas_declaracoes(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_atribuicao(lit_int("5", 3), "B", 3),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["tipo"], TIPO_REAL)
        self.assertEqual(resultado["simbolos"]["B"]["tipo"], TIPO_INT)

class TestLeituraBasica(unittest.TestCase):
    def test_leitura_de_variavel_declarada(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_leitura("A", 3),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["linhas_uso"], [3])

    def test_leitura_em_multiplas_linhas(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_leitura("A", 3),
            corpo_leitura("A", 5),
            corpo_leitura("A", 7),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["linhas_uso"], [3, 5, 7])

class TestVariavelNaoDeclarada(unittest.TestCase):
    def test_leitura_sem_declaracao_gera_erro(self):
        arvore = programa(corpo_leitura("X", 2))
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(len(resultado["erros"]), 1)
        self.assertEqual(resultado["erros"][0]["codigo"], COD_VARIAVEL_NAO_DECLARADA)
        self.assertEqual(resultado["erros"][0]["simbolo"], "X")

    def test_uso_em_atribuicao_sem_declaracao(self):
        # (Y MEM X) com Y nunca declarada.
        arvore = programa(corpo_atribuicao(mem("Y", 2), "X", 2))
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["X"]["tipo"], TIPO_INDEFINIDO)
        self.assertEqual(resultado["erros"][0]["simbolo"], "Y")

class TestRedefinicao(unittest.TestCase):
    def test_redefinicao_compativel(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_atribuicao(lit_real("4.0", 5), "A", 5),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["tipo"], TIPO_REAL)
        self.assertEqual(resultado["erros"], [])
    def test_redefinicao_incompativel_real_para_int(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_atribuicao(lit_int("5", 7), "A", 7),
        )
        resultado = construirTabelaSimbolos(arvore)
        # Tipo original preservado para evitar cascata de erros.
        self.assertEqual(resultado["simbolos"]["A"]["tipo"], TIPO_REAL)
        self.assertEqual(resultado["erros"][0]["codigo"], COD_REDEFINICAO_INCOMPATIVEL)

# ==========================================================================
# RES (convenção N=0 = linha imediatamente anterior).
# ==========================================================================
class TestRes(unittest.TestCase):
    def test_res_valido(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),  # linha lógica 0
            corpo_atribuicao(lit_int("5", 3), "B", 3),      # linha lógica 1
            corpo_res(indice=1, linha=4),                    # linha lógica 2
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["erros"], [])

    def test_res_indice_alem_do_historico(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),  # linha lógica 0
            corpo_res(indice=5, linha=3),                    # linha lógica 1
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(len(resultado["erros"]), 1)
        self.assertEqual(resultado["erros"][0]["codigo"], COD_RES_INDICE_INVALIDO)
        self.assertEqual(resultado["erros"][0]["linha"], 3)

    def test_res_indice_negativo(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_res(indice=-1, linha=3),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["erros"][0]["codigo"], COD_RES_INDICE_INVALIDO)

    def test_res_na_primeira_linha_do_programa(self):
        arvore = programa(corpo_res(indice=0, linha=2))
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["erros"][0]["codigo"], COD_RES_INDICE_INVALIDO)

# ==========================================================================
# FOR.
# ==========================================================================
class TestFor(unittest.TestCase):
    def test_for_declara_variavel_nova_como_int(self):
        arvore = programa(
            corpo_for(0, 10, "I", corpo_expr(lit_int("1", 2), "OP_SUM", lit_int("2", 2)), 2),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertIn("I", resultado["simbolos"])
        self.assertEqual(resultado["simbolos"]["I"]["tipo"], TIPO_INT)
        self.assertEqual(resultado["erros"], [])

    def test_for_reaproveita_variavel_int_silenciosamente(self):
        arvore = programa(
            corpo_atribuicao(lit_int("0", 2), "I", 2),
            corpo_for(0, 10, "I", corpo_trivial(3), 3),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["I"]["tipo"], TIPO_INT)
        self.assertEqual(resultado["erros"], [])

    def test_for_conflita_com_variavel_real(self):
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "I", 2),
            corpo_for(0, 10, "I", corpo_trivial(3), 3),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["I"]["tipo"], TIPO_REAL)
        self.assertEqual(len(resultado["erros"]), 1)
        self.assertEqual(resultado["erros"][0]["codigo"], COD_FOR_VARIAVEL_REDEFINIDA)

# ==========================================================================
# Expressões aritméticas.
# ==========================================================================
class TestExpressaoAritmetica(unittest.TestCase):
    def test_expressao_simples_registra_uso(self):
        # (A 2 +) na linha 3.
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_expr(mem("A", 3), "OP_SUM", lit_int("2", 3)),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["linhas_uso"], [3])

    def test_expressao_aninhada_registra_todos_os_usos(self):
        # ((A 2 +) (B 3 *) -) na linha 4.
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),
            corpo_atribuicao(lit_int("5", 3), "B", 3),
            corpo_expr(
                L(corpo_expr(mem("A", 4), "OP_SUM", lit_int("2", 4)), 4),
                "OP_SUB",
                L(corpo_expr(mem("B", 4), "OP_MUL", lit_int("3", 4)), 4),
            ),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["linhas_uso"], [4])
        self.assertEqual(resultado["simbolos"]["B"]["linhas_uso"], [4])
        self.assertEqual(resultado["erros"], [])

# ==========================================================================
# IF / WHILE com condicao.
# ==========================================================================
class TestIfWhile(unittest.TestCase):
    def test_if_registra_uso_em_condicao_e_ramos(self):
        # (IF (A 5 <) (1 2 +) ((B) 3 -))
        arvore = programa(
            corpo_atribuicao(lit_int("0", 2), "A", 2),
            corpo_atribuicao(lit_int("0", 2), "B", 2),
            corpo_if(
                cond(mem("A", 4), "OP_LT", lit_int("5", 4), 4),
                corpo_expr(lit_int("1", 4), "OP_SUM", lit_int("2", 4)),
                corpo_expr(mem("B", 4), "OP_SUB", lit_int("3", 4)),
                4,
            ),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["A"]["linhas_uso"], [4])
        self.assertEqual(resultado["simbolos"]["B"]["linhas_uso"], [4])
        self.assertEqual(resultado["erros"], [])

    def test_while_detecta_uso_de_variavel_nao_declarada_na_condicao(self):
        # (WHILE (N 10 <) (N 1 +)) — N nunca declarada (2 usos).
        arvore = programa(
            corpo_while(
                cond(mem("N", 2), "OP_LT", lit_int("10", 2), 2),
                corpo_expr(mem("N", 2), "OP_SUM", lit_int("1", 2)),
                2,
            ),
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertNotIn("N", resultado["simbolos"])
        codigos = [e["codigo"] for e in resultado["erros"]]
        self.assertEqual(codigos.count(COD_VARIAVEL_NAO_DECLARADA), 2)

# ==========================================================================
# Contador de linha lógica não infla com aninhamento.
# ==========================================================================
class TestContadorLinhaLogica(unittest.TestCase):
    def test_res_apos_expressao_aninhada(self):
        # 3 linhas lógicas; a expressão aninhada da linha 2 NÃO infla o contador.
        arvore = programa(
            corpo_atribuicao(lit_real("3.0", 2), "A", 2),       # linha lógica 0
            corpo_expr(                                          # linha lógica 1
                L(corpo_expr(lit_int("2", 3), "OP_MUL", lit_int("3", 3)), 3),
                "OP_SUM",
                lit_int("1", 3),
            ),
            corpo_res(indice=1, linha=4),                        # linha lógica 2
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["erros"], [])

# ==========================================================================
# Programa completo combinando tudo.
# ==========================================================================
class TestProgramaCompleto(unittest.TestCase):
    def test_programa_realista(self):
        arvore = programa(
            corpo_atribuicao(lit_real("42.5", 2), "VALOR", 2),   # 0
            corpo_leitura("VALOR", 3),                            # 1
            corpo_if(                                             # 2
                cond(lit_int("3", 4), "OP_LT", lit_int("5", 4), 4),
                corpo_expr(lit_int("1", 4), "OP_SUM", lit_int("2", 4)),
                corpo_expr(lit_int("3", 4), "OP_MUL", lit_int("4", 4)),
                4,
            ),
            corpo_for(                                            # 3
                0, 3, "I",
                corpo_expr(mem("I", 5), "OP_SUM", lit_int("1", 5)),
                5,
            ),
            corpo_res(indice=0, linha=6),                         # 4
        )
        resultado = construirTabelaSimbolos(arvore)
        self.assertEqual(resultado["simbolos"]["VALOR"]["tipo"], TIPO_REAL)
        self.assertEqual(resultado["simbolos"]["I"]["tipo"], TIPO_INT)
        self.assertEqual(resultado["simbolos"]["VALOR"]["linhas_uso"], [3])
        self.assertEqual(resultado["simbolos"]["I"]["linhas_uso"], [5])
        self.assertEqual(resultado["erros"], [])

if __name__ == "__main__":
    unittest.main(verbosity=2)