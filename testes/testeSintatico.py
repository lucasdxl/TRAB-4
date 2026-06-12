# Lucas Balint Vilar - Aluno 1

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lerTokens import lerTokens
from construirGramatica import construirGramatica
from parsear import parsear

def _tokens(arquivo):
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    caminho = os.path.join(raiz, "testes", arquivo)
    return lerTokens(caminho)

def _parsear(arquivo):
    tokens = _tokens(arquivo)
    info = construirGramatica()
    return parsear(tokens, info["tabela_ll1"], info["inicio"])

class TesteSintatico(unittest.TestCase):

    def test_programa_valido_nao_lanca_excecao(self):
        try:
            _parsear("teste1.txt")
        except Exception as e:
            self.fail(f"Programa válido gerou exceção: {e}")

    def test_programa_com_erro_lexico_lanca_excecao(self):
        with self.assertRaises(Exception):
            _tokens("teste_comentario_nao_fechado.txt")

    def test_programa_sem_start_lanca_erro_sintatico(self):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        caminho = os.path.join(raiz, "testes", "sem_start_temp.txt")
        with open(caminho, "w") as f:
            f.write("(5 3 +)\n(END)\n")
        try:
            with self.assertRaises(Exception):
                _parsear("sem_start_temp.txt")
        finally:
            os.remove(caminho)

    def test_programa_sem_end_lanca_erro_sintatico(self):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        caminho = os.path.join(raiz, "testes", "sem_end_temp.txt")
        with open(caminho, "w") as f:
            f.write("(START)\n(5 3 +)\n")
        try:
            with self.assertRaises(Exception):
                _parsear("sem_end_temp.txt")
        finally:
            os.remove(caminho)

    def test_expressao_simples_gera_derivacao(self):
        derivacao, derivacaoJson = _parsear("teste1.txt")
        self.assertIsNotNone(derivacao)
        self.assertIsNotNone(derivacaoJson)

    def test_programa_apenas_start_end(self):
        raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        caminho = os.path.join(raiz, "testes", "so_start_end_temp.txt")
        with open(caminho, "w") as f:
            f.write("(START)\n(END)\n")
        try:
            _parsear("so_start_end_temp.txt")
        except Exception as e:
            self.fail(f"(START)(END) deveria ser válido: {e}")
        finally:
            os.remove(caminho)

if __name__ == "__main__":
    unittest.main()