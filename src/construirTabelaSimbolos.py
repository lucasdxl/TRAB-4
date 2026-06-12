# Paulo Henrique Eidi Mino - Aluno 2
# Constrói a tabela de símbolos a partir da ÁRVORE SINTÁTICA CRUA produzida
# pelo parser LL(1) da Fase 2 (parsear.py / gerarArvore.converterArvore), e
# detecta erros semânticos de declaração (uso sem declaração, redefinição
# incompatível, índice RES inválido, variável de FOR conflitante).
#
# Esta é a MESMA estrutura de árvore consumida por verificarTipos() (Aluno 3):
# nós no formato {tipo_no, simbolo, producao, token, filhos}, onde os símbolos
# são os da gramática (corpo, resto_corpo, cauda_mem, operando, condicao, ...).
#
# A saída (tabela + lista de erros) é consumida por verificarTipos() (Aluno 3)
# e gerarArvoreAtribuida() (Aluno 4).

import os
import json

# --------------------------------------------------------------------------
# Caminhos de saída (mesmo padrão raiz/saida usado pelo Aluno 4).
# --------------------------------------------------------------------------
_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CAMINHO_TABELA_JSON = os.path.join(_RAIZ, "saida", "tabela_simbolos.json")
_CAMINHO_TABELA_MD = os.path.join(_RAIZ, "saida", "tabela_simbolos.md")
_CAMINHO_ERROS = os.path.join(_RAIZ, "saida", "erros_declaracao.json")

# Tipos em MAIÚSCULAS para alinhar com os nomes dos terminais da gramática
# LL(1) (INT, REAL, BOOL).
TIPO_INT = "INT"
TIPO_REAL = "REAL"
TIPO_BOOL = "BOOL"
TIPO_INDEFINIDO = "INDEFINIDO"

ESCOPO_GLOBAL = "global"

# Erros são dicts estruturados (não strings) para permitir acúmulo sem
# interromper a análise — o usuário vê todos os erros de uma vez. O Aluno 3
# estende com mais códigos em verificarTipos().
COD_VARIAVEL_NAO_DECLARADA = "VARIAVEL_NAO_DECLARADA"
COD_REDEFINICAO_INCOMPATIVEL = "REDEFINICAO_INCOMPATIVEL"
COD_RES_INDICE_INVALIDO = "RES_INDICE_INVALIDO"
COD_FOR_VARIAVEL_REDEFINIDA = "FOR_VARIAVEL_REDEFINIDA"

# --------------------------------------------------------------------------
# Construtores de registros.
# --------------------------------------------------------------------------
def _criar_simbolo(nome, tipo, linha):
    return {
        "nome": nome,
        "tipo": tipo,
        "linha_definicao": linha,
        "linhas_uso": [],
        "inicializada": True,
        "escopo": ESCOPO_GLOBAL,
    }

def _criar_erro(codigo, linha, simbolo, mensagem):
    return {
        "codigo": codigo,
        "linha": linha,
        "simbolo": simbolo,
        "mensagem": mensagem,
    }

# --------------------------------------------------------------------------
# Acessores de nó cru.
# --------------------------------------------------------------------------
def _eh_terminal(no):
    return isinstance(no, dict) and no.get("tipo_no") == "terminal"

def _token(no):
    return (no or {}).get("token") or {}

def _valor(no):
    return _token(no).get("valor")

def _linha(no):
    return _token(no).get("linha")

def _linha_de(no):
    """Primeira linha de token encontrada numa subárvore (best-effort)."""
    if not isinstance(no, dict):
        return None
    tok = no.get("token")
    if tok and tok.get("linha") is not None:
        return tok["linha"]
    for filho in no.get("filhos", []):
        linha = _linha_de(filho)
        if linha is not None:
            return linha
    return None

# --------------------------------------------------------------------------
# Inferência de tipo do VALOR de uma atribuição.
# Só resolve literais e leitura de memória já declarada; expressões, RES e
# condições ficam INDEFINIDO e são responsabilidade do Aluno 3 (verificarTipos).
# --------------------------------------------------------------------------
def _inferir_tipo_valor(no_valor, simbolos):
    if _eh_terminal(no_valor):
        simbolo = no_valor.get("simbolo")
        if simbolo == "INT":
            return TIPO_INT
        if simbolo == "REAL":
            return TIPO_REAL
        if simbolo == "MEM_ID":
            nome = _valor(no_valor)
            if nome in simbolos:
                return simbolos[nome]["tipo"]
            return TIPO_INDEFINIDO
        return TIPO_INDEFINIDO
    # operando / linha (expressão aninhada) -> delegado.
    return TIPO_INDEFINIDO

# --------------------------------------------------------------------------
# Visitas a posições de "valor"/operando (registram leituras e descem em
# subexpressões, sem inflar o contador de linha lógica).
# --------------------------------------------------------------------------
def _visitar_valor(no, ctx):
    """Nó em posição de valor: terminal, 'operando' ou 'linha'."""
    if not isinstance(no, dict):
        return
    if _eh_terminal(no):
        if no.get("simbolo") == "MEM_ID":
            _registrar_leitura(no, ctx)
        return
    simbolo = no.get("simbolo")
    if simbolo == "operando":
        _visitar_operando(no, ctx)
    elif simbolo == "linha":
        _visitar_linha(no, ctx)
    # corpo solto (fragmento) — trata por robustez
    elif simbolo == "corpo":
        _visitar_corpo(no, ctx)

def _visitar_operando(operando, ctx):
    # operando -> INT | REAL | MEM_ID | linha
    filhos = operando.get("filhos", [])
    if filhos:
        _visitar_valor(filhos[0], ctx)

def _visitar_linha(linha, ctx):
    # linha -> LPAREN corpo RPAREN
    for filho in linha.get("filhos", []):
        if filho.get("simbolo") == "corpo":
            _visitar_corpo(filho, ctx)
            return

# --------------------------------------------------------------------------
# Handlers semânticos (mesma lógica da versão anterior, adaptada à árvore crua).
# --------------------------------------------------------------------------
def _registrar_leitura(mem_node, ctx):
    nome = _valor(mem_node)
    linha = _linha(mem_node)
    simbolos = ctx["simbolos"]
    erros = ctx["erros"]

    if nome not in simbolos:
        erros.append(_criar_erro(
            COD_VARIAVEL_NAO_DECLARADA,
            linha,
            nome,
            f"Erro semântico na linha {linha}: variável '{nome}' usada "
            f"sem ter sido declarada."
        ))
        return

    if linha not in simbolos[nome]["linhas_uso"]:
        simbolos[nome]["linhas_uso"].append(linha)

def _tratar_atribuicao(valor_node, alvo_node, ctx):
    simbolos = ctx["simbolos"]
    erros = ctx["erros"]

    # Visita o lado direito ANTES de registrar o símbolo. Garante que, em
    # (Y MEM X), a leitura de Y seja contabilizada (e possível erro de Y não
    # declarado seja reportado) antes de inferirmos o tipo de X.
    _visitar_valor(valor_node, ctx)

    tipo_inferido = _inferir_tipo_valor(valor_node, simbolos)
    nome = _valor(alvo_node)
    linha = _linha(alvo_node)

    if nome not in simbolos:
        simbolos[nome] = _criar_simbolo(nome, tipo_inferido, linha)
        return

    tipo_anterior = simbolos[nome]["tipo"]

    if tipo_anterior == TIPO_INDEFINIDO:
        simbolos[nome]["tipo"] = tipo_inferido
        return

    if tipo_inferido == TIPO_INDEFINIDO:
        return

    if tipo_anterior != tipo_inferido:
        erros.append(_criar_erro(
            COD_REDEFINICAO_INCOMPATIVEL,
            linha,
            nome,
            f"Erro semântico na linha {linha}: variável '{nome}' foi "
            f"declarada como {tipo_anterior} na linha "
            f"{simbolos[nome]['linha_definicao']} e está sendo redefinida "
            f"como {tipo_inferido}."
        ))
        # Mantemos o tipo original; sobrescrever propagaria erros em cascata.

def _tratar_res(valor_node, ctx):
    erros = ctx["erros"]
    linha_logica = ctx["linha_logica"]

    if _eh_terminal(valor_node) and valor_node.get("simbolo") == "INT":
        try:
            indice = int(_valor(valor_node))
        except (TypeError, ValueError):
            indice = None
        linha = _linha(valor_node)
    else:
        # (X RES) / ((expr) RES): índice não é um literal inteiro.
        indice = None
        linha = _linha_de(valor_node)

    # Convenção (Seção 2.2 + decisão do grupo): N=0 referencia a linha lógica
    # imediatamente anterior; N deve ser inteiro não-negativo e apontar para
    # uma linha já processada (0 <= N < linha_logica).
    if not isinstance(indice, int) or indice < 0:
        erros.append(_criar_erro(
            COD_RES_INDICE_INVALIDO,
            linha,
            "RES",
            f"Erro semântico na linha {linha}: índice de RES deve ser "
            f"inteiro não-negativo, recebido '{indice}'."
        ))
        return

    if indice >= linha_logica:
        erros.append(_criar_erro(
            COD_RES_INDICE_INVALIDO,
            linha,
            "RES",
            f"Erro semântico na linha {linha}: (RES {indice}) faz "
            f"referência a uma linha inexistente (só existem "
            f"{linha_logica} linha(s) anterior(es))."
        ))

def _tratar_for(corpo_filhos, ctx):
    # corpo -> KW_FOR INT INT MEM_ID linha
    simbolos = ctx["simbolos"]
    erros = ctx["erros"]

    no_inicio = corpo_filhos[1]
    no_fim = corpo_filhos[2]
    var_node = corpo_filhos[3]
    corpo_laco = corpo_filhos[4]

    # Limites são literais INT por gramática; visitamos por generalidade.
    _visitar_valor(no_inicio, ctx)
    _visitar_valor(no_fim, ctx)

    nome_variavel = _valor(var_node)
    linha = _linha(var_node)

    # A gramática força INT INT MEM_ID, então a variável de controle é sempre
    # INT por construção.
    if nome_variavel not in simbolos:
        simbolos[nome_variavel] = _criar_simbolo(nome_variavel, TIPO_INT, linha)
    else:
        tipo_anterior = simbolos[nome_variavel]["tipo"]
        if tipo_anterior not in (TIPO_INT, TIPO_INDEFINIDO):
            erros.append(_criar_erro(
                COD_FOR_VARIAVEL_REDEFINIDA,
                linha,
                nome_variavel,
                f"Erro semântico na linha {linha}: variável '{nome_variavel}' "
                f"foi declarada como {tipo_anterior} na linha "
                f"{simbolos[nome_variavel]['linha_definicao']} e está sendo "
                f"usada como variável de controle de FOR (que exige INT)."
            ))
        elif tipo_anterior == TIPO_INDEFINIDO:
            simbolos[nome_variavel]["tipo"] = TIPO_INT

    _visitar_linha(corpo_laco, ctx)

def _visitar_condicao(cond, ctx):
    # condicao -> LPAREN operando operando op_rel RPAREN
    for filho in cond.get("filhos", []):
        if filho.get("simbolo") == "operando":
            _visitar_operando(filho, ctx)

# --------------------------------------------------------------------------
# Núcleo: interpretação de um nó 'corpo' cru.
# --------------------------------------------------------------------------
def _despachar_resto(valor_node, resto, ctx):
    """resto = nó 'resto_corpo'. valor_node = operando à esquerda já consumido."""
    rfilhos = resto.get("filhos", [])
    if not rfilhos:
        return
    rsb = rfilhos[0].get("simbolo")

    if rsb == "KW_RES":
        # (valor RES)
        _tratar_res(valor_node, ctx)
        return

    if rsb == "KW_MEM":
        # (valor MEM alvo)
        if len(rfilhos) >= 2:
            _tratar_atribuicao(valor_node, rfilhos[1], ctx)
        return

    # resto_corpo -> operando operador_arit  => expressão aritmética
    _visitar_valor(valor_node, ctx)        # operando esquerdo
    _visitar_operando(rfilhos[0], ctx)     # operando direito (operador não tem símbolos)

def _visitar_corpo(corpo, ctx):
    filhos = corpo.get("filhos", [])
    if not filhos:
        return

    primeiro = filhos[0]
    sb = primeiro.get("simbolo")

    # --- Estruturas de controle ---
    if sb == "KW_IF":
        # corpo -> KW_IF condicao linha linha
        _visitar_condicao(filhos[1], ctx)
        _visitar_linha(filhos[2], ctx)
        _visitar_linha(filhos[3], ctx)
        return

    if sb == "KW_WHILE":
        # corpo -> KW_WHILE condicao linha
        _visitar_condicao(filhos[1], ctx)
        _visitar_linha(filhos[2], ctx)
        return

    if sb == "KW_FOR":
        # corpo -> KW_FOR INT INT MEM_ID linha
        _tratar_for(filhos, ctx)
        return

    # --- Casos liderados por operando ---
    if sb == "MEM_ID":
        # corpo -> MEM_ID cauda_mem
        cauda = filhos[1] if len(filhos) > 1 else None
        if cauda is None or not cauda.get("filhos"):
            # cauda_mem -> ε  =>  leitura de memória (X)
            _registrar_leitura(primeiro, ctx)
            return
        # cauda_mem -> resto_corpo
        _despachar_resto(primeiro, cauda["filhos"][0], ctx)
        return

    # corpo -> INT resto_corpo | REAL resto_corpo | linha resto_corpo
    if len(filhos) > 1:
        _despachar_resto(primeiro, filhos[1], ctx)

# --------------------------------------------------------------------------
# Travessia do nível superior do programa (conta linhas lógicas).
# --------------------------------------------------------------------------
def _encontrar_linhas(no):
    if not isinstance(no, dict):
        return None
    sb = no.get("simbolo")
    if sb == "linhas":
        return no
    if sb == "programa":
        for filho in no.get("filhos", []):
            if filho.get("simbolo") == "linhas":
                return filho
    return None

def _percorrer_linhas(linhas_node, ctx):
    # linhas -> LPAREN linhas_rest
    lr = None
    for filho in linhas_node.get("filhos", []):
        if filho.get("simbolo") == "linhas_rest":
            lr = filho
            break
    if lr is None:
        return

    rfilhos = lr.get("filhos", [])
    if not rfilhos:
        return

    # linhas_rest -> KW_END RPAREN  (fim do programa)
    if rfilhos[0].get("simbolo") == "KW_END":
        return

    # linhas_rest -> corpo RPAREN linhas
    # A linha lógica só incrementa no NÍVEL SUPERIOR. Subexpressões aninhadas
    # (visitadas via _visitar_linha) não contam para o histórico de RES —
    # mesma semântica do gerarAssembly da Fase 2.
    _visitar_corpo(rfilhos[0], ctx)
    ctx["linha_logica"] += 1

    for filho in rfilhos:
        if filho.get("simbolo") == "linhas":
            _percorrer_linhas(filho, ctx)
            return

# --------------------------------------------------------------------------
# API pública.
# --------------------------------------------------------------------------
def construirTabelaSimbolos(arvore):
    ctx = {"simbolos": {}, "erros": [], "linha_logica": 0}

    no_linhas = _encontrar_linhas(arvore)
    if no_linhas is not None:
        _percorrer_linhas(no_linhas, ctx)
    else:
        # Fragmento isolado (ex.: testes que passam um único corpo/linha).
        sb = arvore.get("simbolo") if isinstance(arvore, dict) else None
        if sb == "corpo":
            _visitar_corpo(arvore, ctx)
        elif sb == "linha":
            _visitar_linha(arvore, ctx)
        elif sb == "condicao":
            _visitar_condicao(arvore, ctx)

    return {
        "simbolos": ctx["simbolos"],
        "erros": ctx["erros"],
    }

# --------------------------------------------------------------------------
# Persistência dos artefatos (Seção 10.4: tabela e relatório da última execução).
# --------------------------------------------------------------------------
def _garantir_diretorio(caminho):
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

def salvarTabelaSimbolos(resultado, caminho=None):
    """Salva a tabela em JSON (artefato de máquina da última execução)."""
    caminho = caminho or _CAMINHO_TABELA_JSON
    _garantir_diretorio(caminho)

    simbolos = resultado.get("simbolos", {})
    dados = {"total_simbolos": len(simbolos), "simbolos": simbolos}

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    return caminho

def salvarErrosDeclaracao(resultado, caminho=None):
    """Relatório de erros de declaração — exigido mesmo se vazio (Seção 10.4)."""
    caminho = caminho or _CAMINHO_ERROS
    _garantir_diretorio(caminho)

    erros = resultado.get("erros", [])
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump({"total_erros": len(erros), "erros": erros}, f,
                  indent=2, ensure_ascii=False)
    return caminho

def salvarTabelaSimbolosMarkdown(resultado, caminho=None, arquivo_origem=None):
    """Versão legível para o repositório (Markdown)."""
    caminho = caminho or _CAMINHO_TABELA_MD
    _garantir_diretorio(caminho)

    simbolos = resultado.get("simbolos", {})
    erros = resultado.get("erros", [])

    linhas = ["# Tabela de Símbolos", ""]
    if arquivo_origem:
        linhas += [f"Arquivo analisado: `{arquivo_origem}`", ""]
    linhas += [f"Total de símbolos: **{len(simbolos)}**", ""]

    if simbolos:
        linhas += [
            "| Identificador | Tipo | Escopo | Linha def. | Linhas de uso | Inicializada |",
            "|---|---|---|---|---|---|",
        ]
        for nome in sorted(simbolos):
            s = simbolos[nome]
            usos = ", ".join(str(l) for l in s.get("linhas_uso", [])) or "—"
            linhas.append(
                f"| {nome} | {s.get('tipo')} | {s.get('escopo')} | "
                f"{s.get('linha_definicao')} | {usos} | "
                f"{'sim' if s.get('inicializada') else 'não'} |"
            )
    else:
        linhas.append("_Nenhum símbolo declarado._")

    linhas += ["", "## Erros de declaração", ""]
    if erros:
        linhas += ["| Código | Linha | Símbolo | Mensagem |", "|---|---|---|---|"]
        for e in erros:
            linhas.append(
                f"| {e.get('codigo')} | {e.get('linha')} | "
                f"{e.get('simbolo')} | {e.get('mensagem')} |"
            )
    else:
        linhas.append("_Nenhum erro de declaração encontrado._")

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    return caminho