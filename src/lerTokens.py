# Lucas Balint Vilar - Aluno 1

from tokensConfig import criarToken, OPERADORES_SIMPLES
from estadosLexicos import estadoNumero, estadoPalavra
 
def lerTokens(arquivo):
    tokens = [] # Lista que armazenará todos os rokens reconhecidos
    dentroComentario = False # Controla se o analisador está dentro de um bloco de comentário
 
    try:
        with open(arquivo, 'r') as f:
            linhas = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo '{arquivo}' não encontrado.")
 
    # Percorre todas as linhas do arquivo
    for num_linha, linha in enumerate(linhas, start=1):
        linha = linha.strip()
        if not linha:
            continue
 
        i = 0
        # Percorre caractere por caractere da linha atual
        while i < len(linha):

            # Início de comentário: *{
            if not dentroComentario and i + 1 < len(linha) and linha[i] == "*" and linha[i + 1] == "{":
                dentroComentario = True
                i += 2
                continue

            # Fim de comentário: }*
            if dentroComentario and i + 1 < len(linha) and linha[i] == "}" and linha[i + 1] == "*":
                dentroComentario = False
                i += 2
                continue

            # Enquanto estiver dentro do comentário, ignora caracteres
            if dentroComentario:
                i += 1
                continue

            ch = linha[i]
 
            # Espaços em branco
            if ch in (' ', '\t'):
                i += 1
                continue
            
            # Parênteses
            if ch == '(':
                tokens.append(criarToken("LPAREN", "(", num_linha))
                i += 1
                continue
 
            if ch == ')':
                tokens.append(criarToken("RPAREN", ")", num_linha))
                i += 1
                continue
 
            # Números (INT ou REAL)
            if ch.isdigit():
                tok, i = estadoNumero(linha, i, num_linha)
                tokens.append(tok)
                continue

            # Operadores simples (aritméticos e relacionais < >)
            if ch in OPERADORES_SIMPLES:
                tokens.append(criarToken(OPERADORES_SIMPLES[ch], ch, num_linha))
                i += 1
                continue
 
            # Palavras: keywords ou MEM_ID
            if ch.isalpha():
                tok, i = estadoPalavra(linha, i, num_linha)
                tokens.append(tok)
                continue
 
            # Erro de caractere não reconhecido
            raise ValueError(
                f"Erro léxico na linha {num_linha}: "
                f"caractere inesperado '{ch}'"
            )
        
    if dentroComentario:
        raise ValueError("Erro léxico: comentário iniciado com *{ não foi fechado com }*.")
 
    # Token de fim de entrada (necessário para o parser)
    tokens.append(criarToken("$", "$", -1))
    return tokens