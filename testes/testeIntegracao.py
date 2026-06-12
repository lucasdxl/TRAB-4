# Victor Rahal Basseto - Aluno 4

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prepararEntradaSemantica import prepararEntradaSemantica
from construirTabelaSimbolos import construirTabelaSimbolos
from verificarTipos import verificarTipos
from gerarArvoreAtribuida import gerarArvoreAtribuida
from gerarAssembly import gerarAssembly

def _rodar(arquivo):
    entrada = prepararEntradaSemantica(arquivo)
    tabela  = construirTabelaSimbolos(entrada["arvore_base_semantica"])
    tipos   = verificarTipos(entrada["arvore_base_semantica"], tabela)
    atrib   = gerarArvoreAtribuida(entrada["arvore_simplificada"], tabela, tipos)
    return {"entrada": entrada, "tabela": tabela, "tipos": tipos, "arvore": atrib}

class TesteIntegracao(unittest.TestCase):
    def test_programa_valido_sem_erros(self):
        r = _rodar("teste1.txt")
        self.assertEqual(r["tipos"]["erros"], [],
                         "teste1.txt não deve ter erros semânticos")
    def test_programa_valido_gera_arvore_atribuida(self):
        r = _rodar("teste1.txt")
        self.assertIsNotNone(r["arvore"], "Árvore atribuída não deve ser None")
        self.assertIn("tipo", r["arvore"], "Nó raiz deve ter campo 'tipo'")
    def test_programa_valido_tem_tipos_no_nos(self):
        r = _rodar("teste1.txt")
        def buscar_tipo_inferido(no):
            if not isinstance(no, dict):
                return False
            if "tipo_inferido" in no:
                return True
            for chave in ("atual", "proximo", "valor", "condicao",
                          "entao", "senao", "corpo"):
                if buscar_tipo_inferido(no.get(chave)):
                    return True
            return False
        self.assertTrue(buscar_tipo_inferido(r["arvore"]),
                        "Árvore atribuída deve ter ao menos um tipo_inferido")
    def test_tabela_contem_variaveis(self):
        r = _rodar("teste1.txt")
        simbolos = r["tabela"].get("simbolos", {})
        self.assertGreater(len(simbolos), 0,
                           "Tabela de símbolos deve ter ao menos um símbolo")
    def test_programa_com_erro_semantico_reporta_erros(self):
        r = _rodar("teste2.txt")
        self.assertGreater(len(r["tipos"]["erros"]), 0,
                           "teste2.txt deve reportar erros semânticos")
    def test_programa_com_erro_nao_produz_assembly(self):
        r = _rodar("teste2.txt")
        erros = r["tipos"]["erros"]
        self.assertGreater(len(erros), 0,
                           "teste2.txt deve ter erros semânticos")
        caminho_asm = os.path.join(
            os.path.dirname(__file__), "..", "saida", "Assembly.s"
        )
        if os.path.exists(caminho_asm):
            os.remove(caminho_asm)
        if not erros:
            gerarAssembly(r["arvore"])
        self.assertFalse(
            os.path.exists(caminho_asm),
            "Assembly.s não deve existir quando há erros semânticos"
        )
    def test_tipo_int_anotado_corretamente(self):
        from prepararEntradaSemantica import prepararEntradaSemantica as pep
        from construirTabelaSimbolos import construirTabelaSimbolos as cts
        from verificarTipos import verificarTipos as vt
        from gerarArvoreAtribuida import gerarArvoreAtribuida as gaa
        entrada = pep("teste1.txt")
        tabela  = cts(entrada["arvore_base_semantica"])
        tipos   = vt(entrada["arvore_base_semantica"], tabela)
        arvore  = gaa(entrada["arvore_simplificada"], tabela, tipos)
        def achar_terminal_int(no):
            if not isinstance(no, dict):
                return None
            if no.get("tipo") == "terminal" and no.get("simbolo") == "INT":
                return no
            for chave in ("atual", "proximo", "valor", "condicao",
                          "entao", "senao", "corpo", "esquerdo", "direito"):
                resultado = achar_terminal_int(no.get(chave))
                if resultado:
                    return resultado
            for op in no.get("operandos", []):
                resultado = achar_terminal_int(op)
                if resultado:
                    return resultado
            return None
        no_int = achar_terminal_int(arvore)
        self.assertIsNotNone(no_int, "Deve existir terminal INT na árvore")
        self.assertEqual(no_int.get("tipo_inferido"), "INT")
    def test_programa_3_sem_erros_semanticos(self):
        r = _rodar("teste3.txt")
        self.assertEqual(r["tipos"]["erros"], [],
                         "teste3.txt não deve ter erros semânticos")
    def test_variavel_nao_declarada_gera_erro(self):
        r = _rodar("teste2.txt")
        codigos = [e.get("codigo") for e in r["tipos"]["erros"]]
        self.assertIn("VARIAVEL_NAO_DECLARADA", codigos,
                      "Deve detectar variável não declarada em teste2.txt")
    def test_erro_tipo_divisao_inteira_com_real(self):
        r = _rodar("teste2.txt")
        codigos = [e.get("codigo") for e in r["tipos"]["erros"]]
        self.assertIn("OPERADOR_EXIGE_INT", codigos,
                      "Deve detectar divisão inteira com REAL em teste2.txt")

if __name__ == "__main__":
    unittest.main()