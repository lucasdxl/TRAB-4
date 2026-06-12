# Lucas Balint Vilar
# Trabalho Final - Compiladores
#
# Este módulo transforma os resultados das expressões da linguagem
# em caracteres ASCII, depois em código Morse e depois em eventos
# de LED para o backend ARM/ELF.

import os
import sys
import json

from prepararEntradaSemantica import prepararEntradaSemantica


# ==================================================
# Tabela Morse
# ==================================================

TABELA_MORSE = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",

    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----."
}


# ==================================================
# Tempos do projeto
# ==================================================

TEMPO_PONTO = 300
TEMPO_TRACO = 600
TEMPO_ENTRE_SIMBOLOS = 450
TEMPO_ENTRE_LETRAS = 900
TEMPO_ENTRE_PALAVRAS = 2000


# ==================================================
# Funções auxiliares
# ==================================================

def eh_numero(valor):
    try:
        float(valor)
        return True
    except (TypeError, ValueError):
        return False


def normalizar_numero(valor):
    numero = float(valor)

    if numero.is_integer():
        return int(numero)

    return numero


def obter_valor_terminal(no):
    if not isinstance(no, dict):
        return None

    if "valor" in no and eh_numero(no["valor"]):
        return normalizar_numero(no["valor"])

    if "lexema" in no and eh_numero(no["lexema"]):
        return normalizar_numero(no["lexema"])

    token = no.get("token")

    if isinstance(token, dict):
        if "valor" in token and eh_numero(token["valor"]):
            return normalizar_numero(token["valor"])

        if "lexema" in token and eh_numero(token["lexema"]):
            return normalizar_numero(token["lexema"])

    return None


# ==================================================
# Avaliação da árvore simplificada
# ==================================================

def avaliar_expressao(no, resultados=None):
    if resultados is None:
        resultados = []

    if no is None or not isinstance(no, dict):
        return None

    tipo = no.get("tipo")

    valor_terminal = obter_valor_terminal(no)

    if valor_terminal is not None:
        return valor_terminal

    if tipo in ("INT", "REAL", "numero"):
        return obter_valor_terminal(no)

    if tipo == "expressao_aritmetica":
        operador = no.get("operador")
        operandos = no.get("operandos", [])

        if len(operandos) != 2:
            raise ValueError(f"Expressão aritmética inválida: {no}")

        esquerdo = avaliar_expressao(operandos[0], resultados)
        direito = avaliar_expressao(operandos[1], resultados)

        if esquerdo is None or direito is None:
            raise ValueError(f"Não foi possível avaliar os operandos: {no}")

        if operador == "+":
            return esquerdo + direito

        if operador == "-":
            return esquerdo - direito

        if operador == "*":
            return esquerdo * direito

        if operador == "/":
            return esquerdo / direito

        if operador == "//":
            return esquerdo // direito

        if operador == "%":
            return esquerdo % direito

        if operador == "^":
            return esquerdo ** direito

        raise ValueError(f"Operador aritmético não reconhecido: {operador}")

    if tipo == "res":
        indice = no.get("indice")

        if indice is None:
            indice = no.get("valor")

        if indice is None:
            raise ValueError("Nó RES sem índice.")

        indice = int(indice)

        if indice <= 0 or indice > len(resultados):
            raise ValueError(f"RES inválido: não existe resultado {indice} posições atrás.")

        return resultados[-indice]

    return None


def percorrer_sequencia(no, resultados):
    if no is None or not isinstance(no, dict):
        return

    tipo = no.get("tipo")

    if tipo == "sequencia":
        atual = no.get("atual")
        proximo = no.get("proximo")

        valor = avaliar_expressao(atual, resultados)

        if valor is not None:
            resultados.append(valor)

        percorrer_sequencia(proximo, resultados)
        return

    if tipo == "fim_programa":
        return

    valor = avaliar_expressao(no, resultados)

    if valor is not None:
        resultados.append(valor)


def extrair_valores_ascii(arvore_simplificada):
    resultados = []
    percorrer_sequencia(arvore_simplificada, resultados)

    valores_ascii = []

    for valor in resultados:
        if isinstance(valor, float) and not valor.is_integer():
            raise ValueError(f"Valor ASCII não inteiro encontrado: {valor}")

        valor_int = int(valor)

        if valor_int < 32 or valor_int > 126:
            raise ValueError(
                f"Valor ASCII fora da faixa imprimível: {valor_int}. "
                "Use valores entre 32 e 126."
            )

        valores_ascii.append(valor_int)

    return valores_ascii


# ==================================================
# ASCII -> Texto -> Morse
# ==================================================

def ascii_para_texto(valores_ascii):
    return "".join(chr(valor) for valor in valores_ascii)


def texto_para_morse(texto):
    resultado = []

    for caractere in texto.upper():
        if caractere == " ":
            resultado.append({
                "caractere": " ",
                "morse": " "
            })
            continue

        if caractere not in TABELA_MORSE:
            raise ValueError(f"Caractere sem representação Morse: {caractere}")

        resultado.append({
            "caractere": caractere,
            "morse": TABELA_MORSE[caractere]
        })

    return resultado


# ==================================================
# Morse -> Eventos de LED
# ==================================================

def morse_para_eventos(morse):
    eventos = []

    for indice_letra, item in enumerate(morse):
        caractere = item["caractere"]
        codigo = item["morse"]

        if caractere == " ":
            eventos.append({
                "estado": "OFF",
                "duracao_ms": TEMPO_ENTRE_PALAVRAS,
                "descricao": "espaço entre palavras"
            })
            continue

        for indice_simbolo, simbolo in enumerate(codigo):
            if simbolo == ".":
                eventos.append({
                    "estado": "ON",
                    "duracao_ms": TEMPO_PONTO,
                    "descricao": f"ponto de {caractere}"
                })

            elif simbolo == "-":
                eventos.append({
                    "estado": "ON",
                    "duracao_ms": TEMPO_TRACO,
                    "descricao": f"traço de {caractere}"
                })

            else:
                raise ValueError(f"Símbolo Morse inválido: {simbolo}")

            if indice_simbolo < len(codigo) - 1:
                eventos.append({
                    "estado": "OFF",
                    "duracao_ms": TEMPO_ENTRE_SIMBOLOS,
                    "descricao": f"espaço interno de {caractere}"
                })

        if indice_letra < len(morse) - 1:
            proximo = morse[indice_letra + 1]

            if proximo["caractere"] != " ":
                eventos.append({
                    "estado": "OFF",
                    "duracao_ms": TEMPO_ENTRE_LETRAS,
                    "descricao": "espaço entre letras"
                })

    return eventos


# ==================================================
# Pipeline completo
# ==================================================

def gerar_morse_do_arquivo(arquivo_teste):
    resultado = prepararEntradaSemantica(arquivo_teste)

    arvore_simplificada = resultado["arvore_simplificada"]

    valores_ascii = extrair_valores_ascii(arvore_simplificada)
    texto = ascii_para_texto(valores_ascii)
    morse = texto_para_morse(texto)
    eventos = morse_para_eventos(morse)

    return {
        "arquivo": resultado["arquivo"],
        "valores_ascii": valores_ascii,
        "texto": texto,
        "morse": morse,
        "eventos": eventos
    }


def salvar_resultado_morse(resultado):
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pasta_saida = os.path.join(raiz, "saida")
    os.makedirs(pasta_saida, exist_ok=True)

    caminho_saida = os.path.join(pasta_saida, "morse.json")

    with open(caminho_saida, "w", encoding="utf-8") as arquivo:
        json.dump(resultado, arquivo, indent=2, ensure_ascii=False)

    return caminho_saida


# ==================================================
# Execução via terminal
# ==================================================

if __name__ == "__main__":
    print("Iniciando geração Morse...")

    if len(sys.argv) >= 2:
        arquivo_teste = sys.argv[1]
    else:
        arquivo_teste = "testeLucasMorse.txt"
        print("Nenhum arquivo informado. Usando padrão:", arquivo_teste)

    try:
        resultado = gerar_morse_do_arquivo(arquivo_teste)
        caminho_saida = salvar_resultado_morse(resultado)

        print("Arquivo processado:", resultado["arquivo"])
        print("Valores ASCII:", resultado["valores_ascii"])
        print("Texto:", resultado["texto"])

        print("\nMorse:")
        for item in resultado["morse"]:
            print(f"{item['caractere']}: {item['morse']}")

        print("\nQuantidade de eventos:", len(resultado["eventos"]))
        print("Resultado salvo em:", caminho_saida)

    except Exception as erro:
        print("Erro:", erro)
        sys.exit(1)