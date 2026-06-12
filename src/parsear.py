# Lucas Balint Vilar - Aluno 1
from construirGramatica import construirGramatica
from lerTokens import lerTokens
import json
import os
raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


EPSILON = "ε"
EOF = "$"

class No:
    def __init__(self, simbolo,tipo_no):
        self.simbolo = simbolo # guarda o símbolo da gramática
        self.tipo_no = tipo_no  # "terminal" ou "nao_terminal"
        self.producao = None   # pega regra de produção da gramática 
        self.token = None  # tipagem e o valor em si (5)
        self.filhos = []  # listas de nós filhos

    def to_dict(self):   # transforma toda ela em um dicionário JSON
        resultado = {
            "tipo_no": self.tipo_no,
            "simbolo": self.simbolo
        }

        if self.producao:
            resultado["producao"] = self.producao

        if self.token:
            resultado["token"] = self.token

        if self.filhos:
            resultado["filhos"] = [f.to_dict() for f in self.filhos]

        return resultado


def validar_terminal(simbolo, tabela):    # valida terminais, verificando se está ou não dentro da tabela
    nao_terminais = {chave[0] for chave in tabela}
    return simbolo not in nao_terminais and simbolo != EPSILON


def parsear(tokens, tabela, simbolo_inicial):
    pilha = [EOF, simbolo_inicial]   # inicialisando a pilha com $ e S
    pilha_nos = [] # pilha da ávore

    derivacao = [] # guardando as regras aplicadas dentro da derivação
    i = 0 # lookahead

    raiz = No(simbolo_inicial, "nao_terminal")  # começo da árvore
    pilha_nos.append(No(EOF, "terminal"))  
    pilha_nos.append(raiz)

    while pilha:
        if i >= len(tokens):
            raise Exception("Erro sintático: fim inesperado da entrada")

        topo = pilha.pop()  # removendo símbolo e nó correspondente 
        no_atual = pilha_nos.pop()

        atual = tokens[i]   # lookahead
        tipo_atual = atual["tipo"]
        linha_atual = atual["linha"]

        # condição de parada
        if topo == EOF and tipo_atual == EOF:
            break

        if validar_terminal(topo, tabela) or topo == EOF: # Se topo for terminal consome o token
            if topo == tipo_atual:
                no_atual.token = atual  
                i += 1
            else:
                raise Exception(
                    f"Erro sintático na linha {linha_atual}: "  # Se não bate dá um erro sintático 
                    f"esperado '{topo}', encontrado '{tipo_atual}'"
                )

        # Não terminal
        else:
            chave = (topo, tipo_atual) # M[A, a]

            if chave in tabela:  # Se existe uma regra ele puxa 
                prod = tabela[chave] # Pegou a produção


                derivacao.append(f"{topo} -> {' '.join(prod)}")  # Salva derivação nesse formato

                no_atual.producao = prod # Salva na árvore

                filhos = []
                # Para cada símbolo da produção cria filhos
                for simbolo in prod:
                    if simbolo != EPSILON:
                        tipo_no = "terminal" if validar_terminal(simbolo, tabela) else "nao_terminal"
                        novo = No(simbolo, tipo_no)
                        filhos.append(novo)

             
                no_atual.filhos = filhos
                # Empilha produção de trás pra frente 
               
                for f in reversed(filhos):
                    pilha.append(f.simbolo)
                    pilha_nos.append(f)

            else:
                raise Exception(
                    f"Erro sintático na linha {linha_atual}: "
                    f"não há regra para ({topo}, {tipo_atual})" # Se não tem regra dá erro
                )

    return derivacao, raiz.to_dict() # retorna a derivação e a árvore em formato de JSON


if __name__ == "__main__":
    info = construirGramatica()

    caminho_tokens = os.path.join(raiz, "testes", "teste1.txt")
    tokens2 = lerTokens(caminho_tokens)

    derivacao, arvore = parsear(tokens2, info["tabela_ll1"], info["inicio"])

    caminho_arquivo = os.path.join(raiz, "saida", "derivacao.json")

    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(arvore, f, indent=2, ensure_ascii=False)

    print("Derivação salva em:", caminho_arquivo)