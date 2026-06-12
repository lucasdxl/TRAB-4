# Lucas Balint Vilar - Aluno 1

import os

from lerTokens import lerTokens
from construirGramatica import construirGramatica
from parsear import parsear
from gerarArvore import gerarArvore, simplificarArvore

def prepararEntradaSemantica(arquivo):
    # Obtém o caminho raiz do projeto
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    # Monta o caminhodo arquivo teste recebido
    caminhoArquivo = os.path.join(raiz, "testes", arquivo)

    # Verifica se o arquivo existe
    if not os.path.isfile(caminhoArquivo):
        raise FileNotFoundError(f'Arquivo "{arquivo}" não encontrado na pasta testes.')

    # Executa a análise léxica e gera o vetor de tokens
    tokens = lerTokens(caminhoArquivo)

    # Constrói a gramática LL(1) utilizada pelo parser 
    info = construirGramatica()

    # Executa análise sintática e gera a derivação e a árvore sintática inicial
    derivacao, derivacaoJson = parsear(
        tokens, 
        info["tabela_ll1"],
        info["inicio"]
    )

    # Converte json retornado pelo parser para estrutura em objetos
    arvoreSintatica = gerarArvore(derivacaoJson)

    # Gerauma versão simplificada da árvore sintática
    arvoreSimplificada = simplificarArvore(arvoreSintatica)

    # Retorna todas as estruturasque serão utilizadas pelas próximas etapas da análise semântica
    return {
        "arquivo": caminhoArquivo,
        "tokens": tokens,
        "derivacao": derivacao,
        "arvore_sintatica": arvoreSintatica,
        "arvore_base_semantica": derivacaoJson,
        "arvore_simplificada": arvoreSimplificada
    }