# Lucas Balint Vilar
# Trabalho Final - Compiladores
#
# Lê saida/morse.json e gera um ELF ARM32 para o CPUlator.
# O ELF liga e desliga o LED conforme os eventos Morse.

import os
import sys
import json
import struct


LED_ADDR = 0xFF200000

TEXT_OFFSET = 0x1000
TEXT_ADDR = 0x8000

ELF_HEADER_SIZE = 52
PROGRAM_HEADER_SIZE = 32
SECTION_HEADER_SIZE = 40

# Ajuste de velocidade.
# Se piscar rápido demais, aumente.
# Se piscar lento demais, diminua.
DELAY_ITERACOES_POR_MS = 3000


class ArmEmitter:
    def __init__(self):
        self.words = []
        self.labels = {}
        self.branch_fixups = []
        self.literal_fixups = []
        self.literals = []

    def pos(self):
        return len(self.words)

    def label(self, nome):
        self.labels[nome] = self.pos()

    def emit(self, word):
        self.words.append(word & 0xFFFFFFFF)

    def mov_imm(self, rd, imm):
        if imm < 0 or imm > 255:
            raise ValueError(f"MOV imediato fora do intervalo 0..255: {imm}")

        word = 0xE3A00000 | (rd << 12) | imm
        self.emit(word)

    def str_reg(self, rt, rn):
        word = 0xE5800000 | (rn << 16) | (rt << 12)
        self.emit(word)

    def subs_imm(self, rd, rn, imm):
        if imm < 0 or imm > 255:
            raise ValueError(f"SUBS imediato fora do intervalo 0..255: {imm}")

        word = 0xE2500000 | (rn << 16) | (rd << 12) | imm
        self.emit(word)

    def b(self, label):
        self.branch_fixups.append((self.pos(), label, 0xE))
        self.emit(0)

    def bne(self, label):
        self.branch_fixups.append((self.pos(), label, 0x1))
        self.emit(0)

    def ldr_literal(self, rd, valor):
        indice_literal = len(self.literals)
        self.literals.append(valor & 0xFFFFFFFF)

        self.literal_fixups.append((self.pos(), rd, indice_literal))
        self.emit(0)

    def resolver_branches(self):
        for pos_instrucao, label, cond in self.branch_fixups:
            if label not in self.labels:
                raise ValueError(f"Label não encontrado: {label}")

            destino = self.labels[label]

            # Branch ARM usa PC = endereço da instrução atual + 8 bytes.
            offset = destino - pos_instrucao - 2

            if offset < -0x800000 or offset > 0x7FFFFF:
                raise ValueError(f"Branch fora do alcance: {label}")

            offset_24 = offset & 0x00FFFFFF
            word = (cond << 28) | 0x0A000000 | offset_24
            self.words[pos_instrucao] = word

    def resolver_literais(self):
        inicio_literais = len(self.words)

        for valor in self.literals:
            self.words.append(valor)

        for pos_instrucao, rd, indice_literal in self.literal_fixups:
            pos_literal = inicio_literais + indice_literal

            # PC relativo: PC aponta para a instrução atual + 8 bytes.
            offset_bytes = (pos_literal - pos_instrucao - 2) * 4

            if offset_bytes < 0 or offset_bytes > 4095:
                raise ValueError("Literal pool fora do alcance do LDR.")

            word = 0xE59F0000 | (rd << 12) | offset_bytes
            self.words[pos_instrucao] = word

    def finalizar(self):
        self.resolver_branches()
        self.resolver_literais()
        return self.words


def gerar_delay(emitter, duracao_ms, indice_evento):
    iteracoes = int(duracao_ms * DELAY_ITERACOES_POR_MS)

    if iteracoes <= 0:
        return

    label_delay = f"delay_{indice_evento}"

    emitter.ldr_literal(2, iteracoes)

    emitter.label(label_delay)
    emitter.subs_imm(2, 2, 1)
    emitter.bne(label_delay)


def gerar_opcodes_morse(eventos):
    emitter = ArmEmitter()

    # R0 = endereço dos LEDs
    emitter.ldr_literal(0, LED_ADDR)

    emitter.label("inicio_morse")

    for indice, evento in enumerate(eventos):
        estado = evento["estado"]
        duracao_ms = evento["duracao_ms"]

        if estado == "ON":
            emitter.mov_imm(1, 1)
            emitter.str_reg(1, 0)

        elif estado == "OFF":
            emitter.mov_imm(1, 0)
            emitter.str_reg(1, 0)

        else:
            raise ValueError(f"Estado de LED inválido: {estado}")

        gerar_delay(emitter, duracao_ms, indice)

    # Repete LUCAS para sempre
    emitter.b("inicio_morse")

    return emitter.finalizar()


def words_para_bytes(words):
    return b"".join(struct.pack("<I", word) for word in words)


def gerar_elf(codigo, caminho_saida):
    shstrtab = (
        b"\x00"
        b".text\x00"
        b".shstrtab\x00"
    )

    shstrtab_offset = TEXT_OFFSET + len(codigo)

    arquivo = bytearray()

    # Espaço reservado para ELF Header
    arquivo.extend(b"\x00" * ELF_HEADER_SIZE)

    # Program Header
    arquivo.extend(
        struct.pack(
            "<IIIIIIII",
            1,                  # PT_LOAD
            TEXT_OFFSET,        # p_offset
            TEXT_ADDR,          # p_vaddr
            TEXT_ADDR,          # p_paddr
            len(codigo),        # p_filesz
            len(codigo),        # p_memsz
            5,                  # R + X
            0x1000              # align
        )
    )

    # Padding até .text
    arquivo.extend(b"\x00" * (TEXT_OFFSET - len(arquivo)))

    # .text
    arquivo.extend(codigo)

    # .shstrtab
    arquivo.extend(shstrtab)

    e_shoff = len(arquivo)

    # Section 0 - NULL
    arquivo.extend(
        struct.pack("<IIIIIIIIII", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    )

    # Section 1 - .text
    arquivo.extend(
        struct.pack(
            "<IIIIIIIIII",
            1,
            1,
            0x6,
            TEXT_ADDR,
            TEXT_OFFSET,
            len(codigo),
            0,
            0,
            4,
            0
        )
    )

    # Section 2 - .shstrtab
    arquivo.extend(
        struct.pack(
            "<IIIIIIIIII",
            7,
            3,
            0,
            0,
            shstrtab_offset,
            len(shstrtab),
            0,
            0,
            1,
            0
        )
    )

    # ELF Header
    elf_header = struct.pack(
        "<16sHHIIIIIHHHHHH",
        b"\x7fELF" + bytes([
            1,
            1,
            1,
            0,
            0, 0, 0, 0, 0, 0, 0, 0
        ]),
        2,
        40,
        1,
        TEXT_ADDR,
        ELF_HEADER_SIZE,
        e_shoff,
        0x05000200,
        ELF_HEADER_SIZE,
        PROGRAM_HEADER_SIZE,
        1,
        SECTION_HEADER_SIZE,
        3,
        2
    )

    arquivo[0:ELF_HEADER_SIZE] = elf_header

    with open(caminho_saida, "wb") as f:
        f.write(arquivo)

    return {
        "arquivo": caminho_saida,
        "tamanho_codigo": len(codigo),
        "section_table": e_shoff
    }


def carregar_eventos_morse(caminho_morse):
    with open(caminho_morse, "r", encoding="utf-8") as f:
        dados = json.load(f)

    if "eventos" not in dados:
        raise ValueError("Arquivo Morse inválido: campo 'eventos' não encontrado.")

    return dados


def resolver_caminho_morse(argumento=None):
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    if argumento:
        if os.path.isfile(argumento):
            return os.path.abspath(argumento)

        caminho_em_saida = os.path.join(raiz, "saida", argumento)

        if os.path.isfile(caminho_em_saida):
            return caminho_em_saida

        raise FileNotFoundError(f"Arquivo Morse não encontrado: {argumento}")

    return os.path.join(raiz, "saida", "morse.json")


def caminho_saida_elf():
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pasta_saida = os.path.join(raiz, "saida")
    os.makedirs(pasta_saida, exist_ok=True)

    return os.path.join(pasta_saida, "lucas_morse.elf")


if __name__ == "__main__":
    print("Gerando ELF Morse...")

    argumento = sys.argv[1] if len(sys.argv) >= 2 else None

    try:
        caminho_morse = resolver_caminho_morse(argumento)
        dados_morse = carregar_eventos_morse(caminho_morse)

        eventos = dados_morse["eventos"]
        texto = dados_morse.get("texto", "")

        words = gerar_opcodes_morse(eventos)
        codigo = words_para_bytes(words)

        saida_elf = caminho_saida_elf()
        info = gerar_elf(codigo, saida_elf)

        print("Texto:", texto)
        print("Eventos:", len(eventos))
        print("Instruções ARM:", len(words))
        print("Tamanho do código:", info["tamanho_codigo"], "bytes")
        print("ELF gerado em:", info["arquivo"])

    except Exception as erro:
        print("Erro:", erro)
        sys.exit(1)