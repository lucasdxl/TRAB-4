# Paulo Henrique Eidi Mino - Aluno 2
# Funções de estado do analisador léxico

from tokensConfig import criarToken, KEYWORDS

def estadoNumero(linha, i, num_linha):
    inicio = i
    tem_ponto = False

    while i < len(linha) and (linha[i].isdigit() or linha[i] == '.'):
        if linha[i] == '.':
            if tem_ponto:
                raise ValueError (
                    f"Erro léxico na linha {num_linha}: "
                    f"número com mais de um ponto decimal"
                )
            tem_ponto = True
        i += 1

    valor = linha[inicio:i]
    tipo = "REAL" if tem_ponto else "INT"
    return criarToken(tipo, valor, num_linha), i


def estadoPalavra(linha, i, num_linha):
    inicio = i

    while i < len(linha) and linha[i].isalpha():
        i += 1

    palavra = linha[inicio:i]

    if not palavra.isupper():
        raise ValueError (
            f"Erro léxico na linha {num_linha}: "
            f"identificador inválido '{palavra}' "
            f"(deve conter apenas letras maiúsculas)"
        )

    if palavra in KEYWORDS:
        tipo = KEYWORDS[palavra]
    else:
        tipo = "MEM_ID"

    return criarToken(tipo, palavra, num_linha), i