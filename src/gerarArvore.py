# Lucas Balint Vilar - Aluno 1
import json
import os

raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
caminhoArvore = os.path.join(raiz, "saida", "arvore.json")
caminhoArvore_simplificada = os.path.join(raiz, "saida", "arvore_simplificada.json")
caminhoDerivacao = os.path.join(raiz, "saida", "derivacao.json")
caminhoGrafico = os.path.join(raiz, "saida", "arvore")


class No:
    def __init__(self, tipo_no, simbolo, producao=None, token=None, filhos=None):
        self.tipo_no = tipo_no
        self.simbolo = simbolo
        self.producao = producao or []
        self.token = token
        self.filhos = filhos or []

    def __repr__(self):
        return f"No(tipo_no={self.tipo_no}, simbolo={self.simbolo})"
    
def gerarArvore(derivacao): #cria a árvore a partir da derivação recebida
    no = No( # cria os nós a partir do dicionario
        tipo_no = derivacao.get("tipo_no"),
        simbolo = derivacao.get("simbolo"),
        producao = derivacao.get("producao", []),
        token = derivacao.get("token"),
        filhos = []
    )

    # percorrer recursivamente os filhos da derivação e converte em nós de árvore
    for filho in derivacao.get("filhos", []):
        no.filhos.append(gerarArvore(filho))

    return no

def simplificarArvore(no):
    if no.tipo_no == "terminal" and no.token:
        return { # caso terminal
            "tipo": "terminal",
            "simbolo": no.simbolo,
            "valor": no.token.get("valor"),
            "linha": no.token.get("linha")
        }
    match no.simbolo:
        case "programa":
            for filho in no.filhos:
                if filho.simbolo == "linhas":
                    return simplificarArvore(filho)

        case "linhas":
            for filho in no.filhos:
                if filho.simbolo == "linhas_rest":
                    return simplificarArvore(filho)
        
        case "linhas_rest":
            if len(no.filhos) == 2:
                primeiroTermo = no.filhos[0]
                if primeiroTermo.tipo_no == "terminal" and primeiroTermo.simbolo == "KW_END":
                    return {
                        "tipo": "fim_programa",
                        "linha": primeiroTermo.token.get("linha")
                    }
                
            # caso linhas normais
            if len(no.filhos) == 3:
                termoAtual = simplificarArvore(no.filhos[0])
                proximoTermo = simplificarArvore(no.filhos[2])
                return {
                    "tipo": "sequencia",
                    "atual": termoAtual,
                    "proximo": proximoTermo 
                }
            
        case "linha":
            for filho in no.filhos:
                if filho.simbolo == "corpo":
                    return simplificarArvore(filho)
                
        case "corpo": 

            # para for
            if len(no.filhos) == 5:
                primeiroTermo = no.filhos[0]

                if(primeiroTermo.tipo_no == "terminal" and primeiroTermo.simbolo == "KW_FOR"):
                    return {
                        "tipo": "for",
                        "inicio": simplificarArvore(no.filhos[1]),
                        "fim": simplificarArvore(no.filhos[2]),
                        "variavel": no.filhos[3].token.get("valor"),
                        "corpo": simplificarArvore(no.filhos[4]),
                        "linha": primeiroTermo.token.get("linha")
                    }

            # para while
            if len(no.filhos) == 3:
                primeiroTermo = no.filhos[0]

                if (primeiroTermo.tipo_no == "terminal" and primeiroTermo.simbolo == "KW_WHILE"):
                    return {
                        "tipo": "while",
                        "condicao": simplificarArvore(no.filhos[1]),
                        "corpo": simplificarArvore(no.filhos[2]),
                        "linha": primeiroTermo.token.get("linha")
                    }

            # para IF
            if len(no.filhos) == 4:
                primeiroTermo = no.filhos[0]

                if (primeiroTermo.tipo_no == "terminal" and primeiroTermo.simbolo == "KW_IF"):
                    return {
                        "tipo": "if",
                        "condicao": simplificarArvore(no.filhos[1]),
                        "entao": simplificarArvore(no.filhos[2]),
                        "senao": simplificarArvore(no.filhos[3]),
                        "linha": primeiroTermo.token.get("linha")
                    }

            if len(no.filhos) == 2:
                primeiroTermo = no.filhos[0]
                segundoTermo = no.filhos[1]

                #para RES
                if (primeiroTermo.tipo_no == "terminal" and primeiroTermo.simbolo == "INT" and segundoTermo.simbolo == "resto_corpo" and len(segundoTermo.filhos) == 1 and segundoTermo.filhos[0].tipo_no == "terminal" and segundoTermo.filhos[0].simbolo == "KW_RES"):
                    return {
                        "tipo": "res",
                        "indice": int(primeiroTermo.token.get("valor")),
                        "linha": primeiroTermo.token.get("linha")
                    }
                
                # caso de leitura de memória
                if (primeiroTermo.tipo_no == "terminal" and primeiroTermo.simbolo == "MEM_ID" and segundoTermo.simbolo == "cauda_mem" and len(segundoTermo.filhos) == 0):
                    return{
                        "tipo": "leitura_memoria",
                        "nome": primeiroTermo.token.get("valor"),
                        "linha": primeiroTermo.token.get("linha")
                    }
                
                # caso de atribuição de memória
                if (segundoTermo.simbolo == "resto_corpo" and segundoTermo.filhos[0].tipo_no == "terminal" and segundoTermo.filhos[0].simbolo == "KW_MEM" and segundoTermo.filhos[1].tipo_no == "terminal" and segundoTermo.filhos[1].simbolo == "MEM_ID"):
                    return{
                        "tipo": "atribuicao_memoria",
                        "nome": segundoTermo.filhos[1].token.get("valor"),
                        "valor": simplificarArvore(primeiroTermo),
                        "linha": segundoTermo.filhos[1].token.get("linha")
                    }
                
                #caso expressão aritmética
                esquerdo = simplificarArvore(no.filhos[0])
                resto = no.filhos[1]

                # Caso: MEM_ID -> cauda_mem -> resto_corpo
                if resto.simbolo == "cauda_mem" and len(resto.filhos) == 1:
                    resto = resto.filhos[0]

                if resto.simbolo == "resto_corpo" and len(resto.filhos) == 2:
                    direito = simplificarArvore(resto.filhos[0])
                    operador = simplificarArvore(resto.filhos[1])

                    return {
                        "tipo": "expressao_aritmetica",
                        "operador": operador["valor"],
                        "operandos": [esquerdo, direito],
                        "linha": esquerdo.get("linha")
                    }
                
        case "operando":
            if len(no.filhos) == 1:
                return simplificarArvore(no.filhos[0])
            
        case "operador_arit":
            if len(no.filhos) == 1:
                return simplificarArvore(no.filhos[0])
            
        case "condicao":
            if len(no.filhos) == 5:
                esquerdo = simplificarArvore(no.filhos[1])
                direito = simplificarArvore(no.filhos[2])
                operador = simplificarArvore(no.filhos[3])

                return {
                    "tipo": "condicao",
                    "operador": operador["valor"],
                    "esquerdo": esquerdo,
                    "direito": direito,
                    "linha": esquerdo.get("linha")
                }
            
        case "op_rel":
            if len(no.filhos) == 1:
                return simplificarArvore(no.filhos[0])
            
    return {
        "tipo": no.simbolo,
        "filhos": [simplificarArvore(filho) for filho in no.filhos]
    }

# função para converter árvore para dicionário
def converterArvore(no):
    return {
        "tipo_no": no.tipo_no,
        "simbolo": no.simbolo,
        "producao": no.producao,
        "token": no.token,
        "filhos": [converterArvore(filho) for filho in no.filhos]
    }

def imprimirArvore(no, nivel=0):
    espaco = "  " * nivel

    if no.tipo_no == "terminal" and no.token:
        valor = no.token.get("valor")
        linha = no.token.get("linha")
        print(f"{espaco} {no.simbolo}: '{valor}' (linha {linha})")
    else:
        if no.producao:
            producao = " ".join(no.producao)
            print(f"{espaco}{no.simbolo} -> {producao}")
        else:
            print(f"{espaco}{no.simbolo}")

    for filho in no.filhos:
        imprimirArvore(filho, nivel + 1)

# gera gráfico da árvore sintática
def gerarGraficoArvoreSimplificada(arvoreSimplificada):
    from graphviz import Digraph
    graf = Digraph()

    def visitar(no, id_pai=None, cont=[0]):
        id_atual = str(cont[0])
        cont[0] += 1

        tipo = no.get("tipo")

        match tipo:
            case "expressao_aritmetica":
                label = no.get("operador")
            case "terminal":
                label = str(no.get("valor"))
            case "res":
                label = f"RES({no.get('indice')})"
            case "sequencia":
                label = "sequencia"
            case "fim_programa":
                label="fim"
            case _:
                label = str(tipo)

        graf.node(id_atual, label)

        if id_pai is not None:
            graf.edge(id_pai, id_atual)
        if tipo == "sequencia":
            visitar(no["atual"], id_atual)
            visitar(no["proximo"], id_atual)
        elif tipo == "expressao_aritmetica":
            visitar(no["operandos"][0], id_atual)
            visitar(no["operandos"][1], id_atual)
        elif tipo == "if":
            visitar(no["condicao"], id_atual)
            visitar(no["entao"], id_atual)
            visitar(no["senao"], id_atual)
        elif tipo == "while":
            visitar(no["condicao"], id_atual)
            visitar(no["corpo"], id_atual)
        elif tipo == "for":
            visitar(no["inicio"], id_atual)
            visitar(no["fim"], id_atual)
            visitar(no["corpo"], id_atual)
        elif tipo == "atribuicao_memoria":
            visitar(no["valor"], id_atual)
        elif tipo == "condicao":
            visitar(no["esquerdo"], id_atual)
            visitar(no["direito"], id_atual)

    visitar(arvoreSimplificada)
    graf.render(caminhoGrafico, format="png", view=True)
    return caminhoGrafico

# salva a árvore convertida em um arquivo JSON
def salvarArvore(arvore):
    with open(caminhoArvore, "w") as f:
        json.dump(converterArvore(arvore), f, indent=2)

    return caminhoArvore

def salvarArvoreSimplificada(arvoreSimplificada):
    with open(caminhoArvore_simplificada, "w") as f:
        json.dump((arvoreSimplificada), f, indent=2)

    return caminhoArvore_simplificada

def carregarDerivacao():
    with open(caminhoDerivacao, 'r') as f:
        return json.load(f)