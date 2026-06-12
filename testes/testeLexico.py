# Lucas Balint Vilar - Aluno 1

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lerTokens import lerTokens

def _caminho(arquivo):
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(raiz, "testes", arquivo)

def _criar_temp(nome, conteudo):
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    caminho = os.path.join(raiz, "testes", nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    return caminho

class TesteTokensValidos(unittest.TestCase):

    def test_token_fim_entrada_sempre_presente(self):
        tokens = lerTokens(_caminho("teste1.txt"))
        self.assertEqual(tokens[-1]["tipo"], "$")

    def test_inteiros_reconhecidos(self):
        tokens = lerTokens(_caminho("teste1.txt"))
        ints = [t for t in tokens if t["tipo"] == "INT"]
        self.assertGreater(len(ints), 0, "Deve haver tokens INT")

    def test_reais_reconhecidos(self):
        tokens = lerTokens(_caminho("teste1.txt"))
        reais = [t for t in tokens if t["tipo"] == "REAL"]
        self.assertGreater(len(reais), 0, "Deve haver tokens REAL")

    def test_mem_id_reconhecido(self):
        tokens = lerTokens(_caminho("teste1.txt"))
        mems = [t for t in tokens if t["tipo"] == "MEM_ID"]
        self.assertGreater(len(mems), 0, "Deve haver tokens MEM_ID")

    def test_todos_operadores_aritmeticos_reconhecidos(self):
        tokens = lerTokens(_caminho("teste1.txt"))
        tipos = {t["tipo"] for t in tokens}
        for op in ["OP_SUM", "OP_SUB", "OP_MUL",
                   "OP_DIVI", "OP_MOD", "OP_POW", "OP_DIVR"]:
            self.assertIn(op, tipos, f"Operador {op} não foi reconhecido")

    def test_keywords_reconhecidas(self):
        tokens = lerTokens(_caminho("teste1.txt"))
        tipos = {t["tipo"] for t in tokens}
        for kw in ["KW_START", "KW_END", "KW_MEM",
                   "KW_RES", "KW_IF", "KW_WHILE", "KW_FOR"]:
            self.assertIn(kw, tipos, f"Keyword {kw} não foi reconhecida")

    def test_linha_correta_registrada_no_token(self):
        tokens = lerTokens(_caminho("teste1.txt"))
        # KW_START deve estar na linha 1
        start = next(t for t in tokens if t["tipo"] == "KW_START")
        self.assertEqual(start["linha"], 1)

class TesteComentarios(unittest.TestCase):

    def test_comentario_em_linha_inteira_ignorado(self):
        # Arquivo: linha inteira é só *{ comentário }*
        tokens = lerTokens(_caminho("teste_comentario_linha.txt"))
        tipos = [t["tipo"] for t in tokens if t["tipo"] != "$"]
        # Conteúdo do comentário não deve virar token
        for t in tipos:
            self.assertNotIn("comentario", t.lower())
        # Expressão real ainda deve estar presente
        self.assertIn("INT", tipos)

    def test_comentario_no_fim_de_linha_ignorado(self):
        tokens = lerTokens(_caminho("teste_comentario_fim.txt"))
        tipos = [t["tipo"] for t in tokens if t["tipo"] != "$"]
        self.assertIn("INT", tipos)
        self.assertIn("OP_SUM", tipos)

    def test_comentario_antes_de_expressao_ignorado(self):
        tokens = lerTokens(_caminho("teste_comentario_inicio.txt"))
        tipos = [t["tipo"] for t in tokens if t["tipo"] != "$"]
        self.assertIn("INT", tipos)
        self.assertIn("OP_SUM", tipos)

    def test_comentario_entre_tokens_ignorado(self):
        # (3 *{ comentário }* 4 +) deve gerar os mesmos tokens que (3 4 +)
        tokens = lerTokens(_caminho("teste_comentario_meio.txt"))
        tipos = [t["tipo"] for t in tokens if t["tipo"] != "$"]
        self.assertIn("INT", tipos)
        self.assertIn("OP_SUM", tipos)

    def test_comentario_entre_tokens_nao_gera_token_extra(self):
        tokens = lerTokens(_caminho("teste_comentario_meio.txt"))
        ints = [t for t in tokens if t["tipo"] == "INT"]
        # Apenas os dois literais: 3 e 4
        self.assertEqual(len(ints), 2)

    def test_comentario_multilinhas_ignorado(self):
        caminho = _criar_temp("_temp_multiline.txt",
            "(START)\n*{ linha 1\nlinha 2 }*\n(3 4 +)\n(END)\n")
        try:
            tokens = lerTokens(caminho)
            tipos = [t["tipo"] for t in tokens if t["tipo"] != "$"]
            self.assertIn("INT", tipos)
            self.assertIn("OP_SUM", tipos)
        finally:
            os.remove(caminho)

class TesteErrosLexicos(unittest.TestCase):

    def test_comentario_nao_fechado_lanca_excecao(self):
        with self.assertRaises(ValueError):
            lerTokens(_caminho("teste_comentario_nao_fechado.txt"))

    def test_caractere_invalido_lanca_excecao(self):
        caminho = _criar_temp("_temp_char_invalido.txt",
            "(START)\n(5 @ 3)\n(END)\n")
        try:
            with self.assertRaises(ValueError):
                lerTokens(caminho)
        finally:
            os.remove(caminho)

    def test_numero_com_dois_pontos_decimais_lanca_excecao(self):
        caminho = _criar_temp("_temp_numero_invalido.txt",
            "(START)\n(3.1.4 2 +)\n(END)\n")
        try:
            with self.assertRaises(ValueError):
                lerTokens(caminho)
        finally:
            os.remove(caminho)

    def test_arquivo_inexistente_lanca_excecao(self):
        with self.assertRaises(FileNotFoundError):
            lerTokens("arquivo_que_nao_existe_jamais.txt")

if __name__ == "__main__":
    unittest.main(verbosity=2)