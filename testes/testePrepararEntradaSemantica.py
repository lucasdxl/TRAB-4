# Lucas Balint Vilar - Aluno 1
import sys
import os
import json

# Adiciona a pasta src ao caminho de importação do Python
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'src')
    )
)

from prepararEntradaSemantica import prepararEntradaSemantica

# Verifica se o arquivo de entrada foi informado corretamente
if len(sys.argv) != 2:
    print("Uso: python testePrepararEntradaSemantica.py <arquivo.txt>")
    sys.exit(1)

# Obtém o nome do arquivo passado por linha de comando
arquivo = sys.argv[1]

try:
    # Executa a preparação da entrada semântica
    resultado = prepararEntradaSemantica(arquivo)

    # Obtémo caminho da pasta de saída do projeto
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    pastaSaida = os.path.join(raiz, 'saida')
    # Cria a pasta de saída caso ela não exista
    os.makedirs(pastaSaida, exist_ok=True)

    # Define o caminho do arquivo json gerado
    caminhoJson = os.path.join(pastaSaida, 'arvore_sintatica_inicial.json')

    # Salva a árvore-base semântica em formato JSON
    with open(caminhoJson, 'w', encoding='utf-8') as f:
        json.dump(resultado["arvore_base_semantica"], f, indent=2, ensure_ascii=False)

    # Exibe informações do processamento realizado
    print("Arquivo processado:", resultado["arquivo"])
    print("Quantidade de tokens:", len(resultado["tokens"]))
    print("Árvore sintática inicial gerada com sucesso.")
    print("Árvore salva em:", caminhoJson)

except Exception as erro:
    # Exibe erros encontrados durante o processamento
    print("Erro encontrado:", erro)