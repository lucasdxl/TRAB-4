# João Henrique Tomaz Dutra - Aluno 3

TIPO_INT = "INT"
TIPO_REAL = "REAL"
TIPO_BOOL = "BOOL"
TIPO_INDEFINIDO = "INDEFINIDO"
TIPO_ERRO = "ERRO"



def verificarTipos(arvore, tabelaSimbolos):
    """
    Entrada:
        arvore: árvore sintática em formato dict
        tabelaSimbolos: saída de construirTabelaSimbolos(arvore)

    Saída:
        {
            "arvore": arvore com atributo "tipo_inferido",
            "tabelaSimbolos": tabela atualizada,
            "erros": lista de erros semânticos estruturados
        }
    """

    erros = []  # criando lista de erros
    simbolos = tabelaSimbolos.get("simbolos", {}) # puxando simbolos da tabela 

    operadores_aritmeticos = {"OP_SUM", "OP_SUB", "OP_MUL", "OP_POW"}  # definição dos grupos de operadores aqui 
    operadores_int = {"OP_DIVI", "OP_MOD"}
    operadores_real = {"OP_DIVR"}
    operadores_relacionais = {"OP_LT", "OP_GT"}


    def eh_terminal(no):
        return isinstance(no, dict) and no.get("tipo_no") == "terminal"   # definindo os terminais 

    def token(no):
        return (no or {}).get("token") or {}   # puxando token da árvore

    def valor(no):
        return token(no).get("valor")   # puxando valor da árvore 

    linhas_por_no = {}
    linha_global = {"valor": None}

    def preencher_linhas(no, linha_contexto=None):
        if not isinstance(no, dict):
            return linha_contexto

        tok = token(no)
        linha_token = tok.get("linha")

        if linha_global["valor"] is None and linha_token is not None:
            linha_global["valor"] = linha_token

        # Se o nó não tem token próprio, herda a linha mais próxima já vista
        # no mesmo contexto sintático.
        linha_no = linha_token if linha_token is not None else linha_contexto
        linhas_por_no[id(no)] = linha_no

        ultima_linha = linha_no
        primeira_linha_filho = None

        for filho in no.get("filhos", []):
            ultima_linha = preencher_linhas(filho, ultima_linha)
            linha_filho = linhas_por_no.get(id(filho))
            if primeira_linha_filho is None and linha_filho is not None:
                primeira_linha_filho = linha_filho

        # Para nós estruturais como corpo/linha/condicao, usa a primeira linha
        # encontrada nos filhos se não houver linha herdada.
        if linhas_por_no[id(no)] is None and primeira_linha_filho is not None:
            linhas_por_no[id(no)] = primeira_linha_filho

        return ultima_linha if ultima_linha is not None else linhas_por_no.get(id(no))

    preencher_linhas(arvore)

    def linha_do_no(no):
        if not isinstance(no, dict):
            return linha_global["valor"] if linha_global["valor"] is not None else "?"

        tok = token(no)  # primeiro pega token do nó
        if tok.get("linha") is not None:
            return tok.get("linha")

        # Depois usa a linha propagada pelo pré-processamento da árvore.
        linha_propagada = linhas_por_no.get(id(no))
        if linha_propagada is not None:
            return linha_propagada

        # depois do pré-processamento.
        for filho in no.get("filhos", []):
            linha = linha_do_no(filho)
            if linha != "?":
                return linha

        return linha_global["valor"] if linha_global["valor"] is not None else "?"

    def adicionar_erro(codigo, no, simbolo, mensagem):
        linha = linha_do_no(no)
        erros.append({
            "codigo": codigo,     # adciona o erro na lista com esse format 
            "linha": linha,
            "simbolo": simbolo,
            "mensagem": f"Erro semântico na linha {linha}: {mensagem}"
        })

    def anotar(no, tipo):
        if isinstance(no, dict):
            no["tipo_inferido"] = tipo   # retorna o tipo 
        return tipo

    def tipo_numerico(tipo):
        return tipo in (TIPO_INT, TIPO_REAL)    # aray de tipos numéricos válidos

    def promover_tipo(t1, t2):
        if TIPO_ERRO in (t1, t2):    # define aqui os tipos das operações mistas 
            return TIPO_ERRO
        if TIPO_REAL in (t1, t2):
            return TIPO_REAL
        return TIPO_INT

    def buscar_primeiro(no, simbolo):
        for filho in no.get("filhos", []):   # busca o primeiro filho (dentro de linha pega o corpo)
            if filho.get("simbolo") == simbolo:
                return filho
        return None

    def buscar_filhos(no, simbolo):
        return [f for f in no.get("filhos", []) if f.get("simbolo") == simbolo]  # retorna todos os filhos com determinado símbolo 

    def tipo_terminal(no):
        simb = no.get("simbolo")      # aqui tem as definições e anotações dos símbolos

        if simb == "INT":
            return anotar(no, TIPO_INT)
        if simb == "REAL":
            return anotar(no, TIPO_REAL)
        if simb == "MEM_ID":
            nome = valor(no)
            if nome not in simbolos: # Faz a verificação do MEM_ID dentro da tabela de simbolos, caso ele não esteja lá já retorna o erro de não declarado 
                adicionar_erro(
                    "VARIAVEL_NAO_DECLARADA", 
                    no,
                    nome,
                    f"variável '{nome}' usada sem ter sido declarada."
                )
                return anotar(no, TIPO_ERRO)

            tipo = simbolos[nome].get("tipo", TIPO_INDEFINIDO)
            if tipo == TIPO_INDEFINIDO:
                return anotar(no, TIPO_INDEFINIDO)
            return anotar(no, tipo)

        return anotar(no, None)


    def aplicar_operador(no_operador, t1, t2):    #tratativas para os operadores 
        operador = no_operador.get("simbolo")

        if operador in operadores_aritmeticos:
            if not tipo_numerico(t1) or not tipo_numerico(t2):  # verifica tipos através da função, tem que estar dentro deles
                adicionar_erro(
                    "TIPOS_INCOMPATIVEIS_OPERADOR",
                    no_operador,
                    operador,
                    f"operador '{operador}' espera INT ou REAL, mas recebeu {t1} e {t2}."
                )
                return TIPO_ERRO
            return promover_tipo(t1, t2)

        if operador in operadores_int:
            if t1 != TIPO_INT or t2 != TIPO_INT:  # em operadores_int tem que ter ambos como tipo inteiro 
                adicionar_erro(
                    "OPERADOR_EXIGE_INT",
                    no_operador,
                    operador,
                    f"operador '{operador}' só aceita INT e INT, mas recebeu {t1} e {t2}."
                )
                return TIPO_ERRO
            return TIPO_INT

        if operador in operadores_real:
            if not tipo_numerico(t1) or not tipo_numerico(t2):   # faz verificação de deles com o os tipos numéricos 
                adicionar_erro(
                    "TIPOS_INCOMPATIVEIS_OPERADOR",
                    no_operador,
                    operador,
                    f"divisão real '{operador}' espera INT ou REAL, mas recebeu {t1} e {t2}."
                )
                return TIPO_ERRO
            return TIPO_REAL

        if operador in operadores_relacionais:
            if not tipo_numerico(t1) or not tipo_numerico(t2):    # afz verificação dos tipo relacionais 
                adicionar_erro(
                    "TIPOS_INCOMPATIVEIS_RELACIONAL",
                    no_operador,
                    operador,
                    f"operador relacional '{operador}' espera operandos numéricos, mas recebeu {t1} e {t2}."
                )
                return TIPO_ERRO
            return TIPO_BOOL

        return TIPO_ERRO

    def atualizar_tipo_mem(mem_node, tipo_valor):
        """Atualiza variável INDEFINIDA quando uma atribuição permite inferir o tipo."""
        nome = valor(mem_node)
        if nome not in simbolos:
            return
        tipo_atual = simbolos[nome].get("tipo", TIPO_INDEFINIDO)
        if tipo_atual == TIPO_INDEFINIDO and tipo_valor not in (TIPO_ERRO, None, TIPO_INDEFINIDO):
            simbolos[nome]["tipo"] = tipo_valor


    def inferir(no):   # Percorre a árvore e retorna o tipo de cada subárvore 
        if not isinstance(no, dict):
            return None

        if eh_terminal(no):   # caso ele for terminal
            return tipo_terminal(no)

        simb = no.get("simbolo")
        filhos = no.get("filhos", [])

        if simb == "programa" or simb == "linhas" or simb == "linhas_rest": # faz o tratamento para os nós estruturais da gramática
            ultimo_tipo = None
            for filho in filhos:
                tipo_filho = inferir(filho)  # percorre os filhos e guarda o último 
                if tipo_filho is not None:
                    ultimo_tipo = tipo_filho
            return anotar(no, ultimo_tipo)

        if simb == "linha":
            corpo = buscar_primeiro(no, "corpo")  # de acordo com a gramática tem que puxar o corpo quando é linha
            return anotar(no, inferir(corpo) if corpo else None)

        if simb == "operando":  # operando vai atrás dos filhos 
            if not filhos:
                return anotar(no, None)
            return anotar(no, inferir(filhos[0]))

        if simb == "op_rel" or simb == "operador_arit":
            # O tipo real é calculado pelo nó pai; aqui só anotamos None.
            for filho in filhos:
                inferir(filho)
            return anotar(no, None)

        if simb == "condicao":
            # condicao -> LPAREN operando operando op_rel RPAREN
            operandos = buscar_filhos(no, "operando")
            op_rel = buscar_primeiro(no, "op_rel")

            if len(operandos) < 2 or op_rel is None or not op_rel.get("filhos"):
                adicionar_erro("CONDICAO_MAL_FORMADA", no, "condicao", "condição relacional mal formada.")
                return anotar(no, TIPO_ERRO)

            t1 = inferir(operandos[0])
            t2 = inferir(operandos[1])
            operador_terminal = op_rel["filhos"][0]
            inferir(op_rel)

            tipo = aplicar_operador(operador_terminal, t1, t2)
            return anotar(no, tipo)

        if simb == "corpo":    # faz o tratamento do corpo de acordo com a gramática
            if not filhos:
                return anotar(no, None)

            primeiro = filhos[0].get("simbolo")

            # corpo -> KW_IF condicao linha linha
            if primeiro == "KW_IF":
                tipo_cond = inferir(filhos[1])
                if tipo_cond not in (TIPO_BOOL, TIPO_ERRO):
                    adicionar_erro("CONDICAO_NAO_BOOL", filhos[1], "IF", f"condição do IF deve ser BOOL, mas recebeu {tipo_cond}.")
                inferir(filhos[2])
                inferir(filhos[3])
                return anotar(no, None)

            # corpo -> KW_WHILE condicao linha
            if primeiro == "KW_WHILE":
                tipo_cond = inferir(filhos[1])
                if tipo_cond not in (TIPO_BOOL, TIPO_ERRO):
                    adicionar_erro("CONDICAO_NAO_BOOL", filhos[1], "WHILE", f"condição do WHILE deve ser BOOL, mas recebeu {tipo_cond}.")
                inferir(filhos[2])
                return anotar(no, None)

            # corpo -> KW_FOR INT INT MEM_ID linha
            if primeiro == "KW_FOR":
                inferir(filhos[1])
                inferir(filhos[2])
                var_controle = filhos[3]
                tipo_var = inferir(var_controle)
                if tipo_var not in (TIPO_INT, TIPO_INDEFINIDO, TIPO_ERRO):
                    adicionar_erro("FOR_VARIAVEL_NAO_INT", var_controle, valor(var_controle), f"variável de controle do FOR deve ser INT, mas recebeu {tipo_var}.")
                atualizar_tipo_mem(var_controle, TIPO_INT)
                inferir(filhos[4])
                return anotar(no, None)

            # corpo -> MEM_ID cauda_mem
            if primeiro == "MEM_ID":
                tipo_esq = inferir(filhos[0])
                cauda = filhos[1] if len(filhos) > 1 else None

                if cauda is None or not cauda.get("filhos"):
                    return anotar(no, tipo_esq)  # leitura simples: (X)

                tipo = inferir_cauda_ou_resto(filhos[0], cauda)
                return anotar(no, tipo)

            # corpo -> INT resto_corpo | REAL resto_corpo | linha resto_corpo
            if primeiro in ("INT", "REAL", "linha"):
                tipo = inferir_cauda_ou_resto(filhos[0], filhos[1])
                return anotar(no, tipo)

            # fallback simples
            ultimo = None
            for filho in filhos:
                tipo_filho = inferir(filho)
                if tipo_filho is not None:
                    ultimo = tipo_filho
            return anotar(no, ultimo)

        if simb in ("cauda_mem", "resto_corpo"):
            # Normalmente estes nós são tratados pelo pai, pois precisam saber
            # o operando da esquerda. Este fallback evita nó sem anotação.
            ultimo = None
            for filho in filhos:
                tipo_filho = inferir(filho)
                if tipo_filho is not None:
                    ultimo = tipo_filho
            return anotar(no, ultimo)

        # fallback geral para outros não-terminais documentais.
        ultimo = None
        for filho in filhos:
            tipo_filho = inferir(filho)
            if tipo_filho is not None:
                ultimo = tipo_filho
        return anotar(no, ultimo)

    def inferir_cauda_ou_resto(valor_node, resto_ou_cauda):
        """
        Trata:
          cauda_mem -> ε | resto_corpo
          resto_corpo -> KW_RES | KW_MEM MEM_ID | operando operador_arit
        """
        tipo_esq = inferir(valor_node)

        if resto_ou_cauda is None:
            return tipo_esq

        no = resto_ou_cauda

        # Se vier cauda_mem -> resto_corpo, entra no filho interno.
        if no.get("simbolo") == "cauda_mem":
            if not no.get("filhos"):
                return anotar(no, tipo_esq)
            tipo = inferir_cauda_ou_resto(valor_node, no["filhos"][0])
            return anotar(no, tipo)

        filhos_resto = no.get("filhos", [])
        if not filhos_resto:
            return anotar(no, tipo_esq)

        primeiro = filhos_resto[0].get("simbolo")

        if primeiro == "KW_RES":
            return anotar(no, TIPO_INDEFINIDO)

        # resto_corpo -> KW_MEM MEM_ID
        if primeiro == "KW_MEM":
            alvo = filhos_resto[1]
            tipo_alvo = inferir(alvo)

            if tipo_alvo == TIPO_INDEFINIDO:
                atualizar_tipo_mem(alvo, tipo_esq)
                tipo_alvo = tipo_esq
                anotar(alvo, tipo_alvo)

            elif tipo_esq not in (TIPO_ERRO, TIPO_INDEFINIDO) and tipo_alvo != tipo_esq:
                adicionar_erro(
                    "ATRIBUICAO_TIPO_INCOMPATIVEL",
                    alvo,
                    valor(alvo),
                    f"variável '{valor(alvo)}' é {tipo_alvo}, mas recebeu valor {tipo_esq}."
                )

            return anotar(no, tipo_esq)

        # resto_corpo -> operando operador_arit
        if primeiro == "operando":
            tipo_dir = inferir(filhos_resto[0])
            operador_nt = filhos_resto[1]
            if not operador_nt.get("filhos"):
                adicionar_erro("OPERADOR_AUSENTE", operador_nt, "operador", "operação sem operador.")
                return anotar(no, TIPO_ERRO)

            operador_terminal = operador_nt["filhos"][0]
            inferir(operador_nt)
            tipo = aplicar_operador(operador_terminal, tipo_esq, tipo_dir)
            return anotar(no, tipo)

        return anotar(no, tipo_esq)

    inferir(arvore)

    # Junta os erros prévios da tabela com os erros de tipo desta etapa.
    erros_anteriores = tabelaSimbolos.get("erros", [])

    return {
        "arvore": arvore,
        "tabelaSimbolos": tabelaSimbolos,
        "erros": erros_anteriores + erros
    }