# Victor Rahal Basseto - Aluno 4

import json
import os

_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CAMINHO_JSON = os.path.join(_RAIZ, "saida", "arvore_atribuida.json")
_CAMINHO_MD   = os.path.join(_RAIZ, "saida", "arvore_atribuida.md")
TIPO_INT       = "INT"
TIPO_REAL      = "REAL"
TIPO_BOOL      = "BOOL"
TIPO_INDEFINIDO = "INDEFINIDO"
TIPO_ERRO      = "ERRO"

def _promover(t1, t2):
    if TIPO_ERRO in (t1, t2):
        return TIPO_ERRO
    if TIPO_REAL in (t1, t2):
        return TIPO_REAL
    if t1 == TIPO_INT and t2 == TIPO_INT:
        return TIPO_INT
    return TIPO_INDEFINIDO

def _tipo_no(no, simbolos, historico):
    """
    Percorre a árvore simplificada e adiciona 'tipo_inferido' a cada nó.
    historico: lista mutável de tipos das linhas lógicas já processadas.
    Retorna o nó anotado (cópia rasa do dict original).
    """
    if not isinstance(no, dict):
        return no
    no = dict(no)   # cópia rasa — não altera o original
    tipo = no.get("tipo")
    if tipo == "terminal":
        simb = no.get("simbolo")
        if simb == "INT":
            no["tipo_inferido"] = TIPO_INT
        elif simb == "REAL":
            no["tipo_inferido"] = TIPO_REAL
        else:
            no["tipo_inferido"] = TIPO_INDEFINIDO
    elif tipo == "leitura_memoria":
        nome = no.get("nome")
        no["tipo_inferido"] = simbolos.get(nome, {}).get("tipo", TIPO_INDEFINIDO)
    elif tipo == "atribuicao_memoria":
        val_anotado = _tipo_no(no["valor"], simbolos, historico)
        no["valor"] = val_anotado
        t_val = val_anotado.get("tipo_inferido", TIPO_INDEFINIDO)
        nome = no.get("nome")
        if nome in simbolos and simbolos[nome].get("tipo") == TIPO_INDEFINIDO:
            simbolos[nome]["tipo"] = t_val
        no["tipo_inferido"] = simbolos.get(nome, {}).get("tipo", t_val)
        historico.append(no["tipo_inferido"])
    elif tipo == "expressao_aritmetica":
        ops_anotados = [_tipo_no(op, simbolos, historico) for op in no.get("operandos", [])]
        no["operandos"] = ops_anotados
        operador = no.get("operador")
        t1 = ops_anotados[0].get("tipo_inferido", TIPO_INDEFINIDO) if ops_anotados else TIPO_INDEFINIDO
        t2 = ops_anotados[1].get("tipo_inferido", TIPO_INDEFINIDO) if len(ops_anotados) > 1 else TIPO_INDEFINIDO
        if operador in ("/", "%"):
            no["tipo_inferido"] = TIPO_INT
        elif operador == "|":
            no["tipo_inferido"] = TIPO_REAL
        else:
            no["tipo_inferido"] = _promover(t1, t2)
        historico.append(no["tipo_inferido"])
    elif tipo == "condicao":
        no["esquerdo"] = _tipo_no(no["esquerdo"], simbolos, historico)
        no["direito"]  = _tipo_no(no["direito"],  simbolos, historico)
        no["tipo_inferido"] = TIPO_BOOL
    elif tipo == "res":
        indice = no.get("indice", 0)
        pos = len(historico) - 1 - indice
        no["tipo_inferido"] = historico[pos] if 0 <= pos < len(historico) else TIPO_INDEFINIDO
        historico.append(no["tipo_inferido"])
    elif tipo == "if":
        no["condicao"] = _tipo_no(no["condicao"], simbolos, historico)
        no["entao"]    = _tipo_no(no["entao"],    simbolos, historico)
        no["senao"]    = _tipo_no(no["senao"],    simbolos, historico)
        no["tipo_inferido"] = None
    elif tipo == "while":
        no["condicao"] = _tipo_no(no["condicao"], simbolos, historico)
        no["corpo"]    = _tipo_no(no["corpo"],    simbolos, historico)
        no["tipo_inferido"] = None
    elif tipo == "for":
        no["inicio"] = _tipo_no(no["inicio"], simbolos, historico)
        no["fim"]    = _tipo_no(no["fim"],    simbolos, historico)
        no["corpo"]  = _tipo_no(no["corpo"],  simbolos, historico)
        no["tipo_inferido"] = None
    elif tipo == "sequencia":
        atual = _tipo_no(no["atual"],   simbolos, historico)
        no["atual"]  = atual
        no["proximo"] = _tipo_no(no["proximo"], simbolos, historico)
        no["tipo_inferido"] = atual.get("tipo_inferido")
    elif tipo == "fim_programa":
        no["tipo_inferido"] = None
    else:
        if "filhos" in no:
            no["filhos"] = [_tipo_no(f, simbolos, historico) for f in no["filhos"]]
        no["tipo_inferido"] = TIPO_INDEFINIDO
    return no

def gerarArvoreAtribuida(arvore, tabelaSimbolos, tipos):
    """
    Entrada:
        arvore        – árvore simplificada (saída de simplificarArvore)
        tabelaSimbolos – saída de construirTabelaSimbolos
        tipos          – saída de verificarTipos (contém tabelaSimbolos atualizada)
    Saída:
        árvore simplificada com 'tipo_inferido' em cada nó relevante
    """
    simbolos_atualizados = dict(
        tipos.get("tabelaSimbolos", tabelaSimbolos).get("simbolos", {})
    )
    historico = []
    return _tipo_no(arvore, simbolos_atualizados, historico)

def _garantir_dir(caminho):
    d = os.path.dirname(caminho)
    if d:
        os.makedirs(d, exist_ok=True)

def salvarArvoreAtribuida(arvoreAtribuida, caminho=None):
    caminho = caminho or _CAMINHO_JSON
    _garantir_dir(caminho)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(arvoreAtribuida, f, indent=2, ensure_ascii=False)
    return caminho

def _linhas_md(no, nivel=0):
    if not isinstance(no, dict):
        return []
    tipo          = no.get("tipo", "?")
    tipo_inferido = no.get("tipo_inferido", "—")
    indent = "  " * nivel
    linhas = [f"{indent}- **{tipo}** → `{tipo_inferido}`"]
    for chave in ("atual", "proximo", "valor", "condicao",
                  "entao", "senao", "corpo", "esquerdo", "direito",
                  "inicio", "fim"):
        filho = no.get(chave)
        if isinstance(filho, dict):
            linhas += _linhas_md(filho, nivel + 1)
    for op in no.get("operandos", []):
        linhas += _linhas_md(op, nivel + 1)
    return linhas

def salvarArvoreAtribuidaMarkdown(arvoreAtribuida, caminho=None, arquivo_origem=None):
    caminho = caminho or _CAMINHO_MD
    _garantir_dir(caminho)
    linhas = ["# Árvore Sintática Atribuída", ""]
    if arquivo_origem:
        linhas += [f"Arquivo: `{arquivo_origem}`", ""]
    linhas += _linhas_md(arvoreAtribuida)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")
    return caminho