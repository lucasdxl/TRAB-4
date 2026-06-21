# Lucas Balint Vilar
# Trabalho Final - Compiladores
#
# Lê saida/morse.json e gera um ELF ARM32 para o CPUlator.
# O ELF liga e desliga o LED conforme os eventos Morse.
#
# Os delays utilizam o SYS_CLOCK do semihosting do CPUlator.

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

# Serviço de relógio do semihosting do CPUlator.
# SYS_CLOCK retorna centésimos de segundo no registrador R0.
SEMIHOSTING_SYS_CLOCK = 0x10
SEMIHOSTING_SVC = 0x123456

# Pausa após terminar LUCAS e antes de repetir.
PAUSA_ENTRE_REPETICOES_MS = 2000


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
        if nome in self.labels:
            raise ValueError(f"Label duplicado: {nome}")

        self.labels[nome] = self.pos()

    def emit(self, word):
        self.words.append(word & 0xFFFFFFFF)

    def mov_imm(self, rd, imm):
        """
        MOV Rd, #imediato
        """

        if imm < 0 or imm > 255:
            raise ValueError(
                f"MOV imediato fora do intervalo 0..255: {imm}"
            )

        word = 0xE3A00000 | (rd << 12) | imm
        self.emit(word)

    def mov_reg(self, rd, rm):
        """
        MOV Rd, Rm
        """

        word = 0xE1A00000 | (rd << 12) | rm
        self.emit(word)

    def sub_reg(self, rd, rn, rm):
        """
        SUB Rd, Rn, Rm
        """

        word = (
            0xE0400000
            | (rn << 16)
            | (rd << 12)
            | rm
        )

        self.emit(word)

    def str_reg(self, rt, rn):
        """
        STR Rt, [Rn]
        """

        word = (
            0xE5800000
            | (rn << 16)
            | (rt << 12)
        )

        self.emit(word)

    def cmp_imm(self, rn, imm):
        """
        CMP Rn, #imediato
        """

        if imm < 0 or imm > 255:
            raise ValueError(
                f"CMP imediato fora do intervalo 0..255: {imm}"
            )

        word = (
            0xE3500000
            | (rn << 16)
            | imm
        )

        self.emit(word)

    def svc(self, imediato):
        """
        SVC #imediato
        """

        if imediato < 0 or imediato > 0xFFFFFF:
            raise ValueError(
                f"SVC imediato fora do intervalo de 24 bits: {imediato}"
            )

        word = 0xEF000000 | imediato
        self.emit(word)

    def b(self, label):
        """
        B label
        """

        self.branch_fixups.append(
            (self.pos(), label, 0xE)
        )

        self.emit(0)

    def blo(self, label):
        """
        BLO label

        Salta se o primeiro valor comparado for menor,
        considerando comparação sem sinal.
        """

        self.branch_fixups.append(
            (self.pos(), label, 0x3)
        )

        self.emit(0)

    def ldr_literal(self, rd, valor):
        """
        LDR Rd, =valor

        O valor é armazenado no literal pool localizado
        ao final do código.
        """

        indice_literal = len(self.literals)

        self.literals.append(
            valor & 0xFFFFFFFF
        )

        self.literal_fixups.append(
            (
                self.pos(),
                rd,
                indice_literal
            )
        )

        self.emit(0)

    def resolver_branches(self):
        for pos_instrucao, label, cond in self.branch_fixups:
            if label not in self.labels:
                raise ValueError(
                    f"Label não encontrado: {label}"
                )

            destino = self.labels[label]

            # Em ARM, durante um branch, o PC corresponde
            # ao endereço da instrução atual mais 8 bytes.
            offset = destino - pos_instrucao - 2

            if offset < -0x800000 or offset > 0x7FFFFF:
                raise ValueError(
                    f"Branch fora do alcance: {label}"
                )

            offset_24 = offset & 0x00FFFFFF

            word = (
                (cond << 28)
                | 0x0A000000
                | offset_24
            )

            self.words[pos_instrucao] = word

    def resolver_literais(self):
        inicio_literais = len(self.words)

        for valor in self.literals:
            self.words.append(valor)

        for (
            pos_instrucao,
            rd,
            indice_literal
        ) in self.literal_fixups:

            pos_literal = (
                inicio_literais
                + indice_literal
            )

            # O PC aponta para a instrução atual mais 8 bytes,
            # isto é, duas words à frente.
            offset_bytes = (
                pos_literal
                - pos_instrucao
                - 2
            ) * 4

            if offset_bytes < 0 or offset_bytes > 4095:
                raise ValueError(
                    "Literal pool fora do alcance do LDR."
                )

            word = (
                0xE59F0000
                | (rd << 12)
                | offset_bytes
            )

            self.words[pos_instrucao] = word

    def finalizar(self):
        self.resolver_branches()
        self.resolver_literais()

        return self.words


def gerar_delay(emitter, duracao_ms, indice_evento):
    """
    Gera um delay consultando o SYS_CLOCK do CPUlator.

    O SYS_CLOCK retorna centésimos de segundo:

        300 ms  -> 30 centésimos
        450 ms  -> 45 centésimos
        600 ms  -> 60 centésimos
        900 ms  -> 90 centésimos
        2000 ms -> 200 centésimos

    Registradores utilizados:

        R0 = operação do semihosting e valor retornado
        R4 = instante inicial
        R5 = tempo decorrido
    """

    if duracao_ms <= 0:
        raise ValueError(
            f"Duração inválida: {duracao_ms} ms"
        )

    if duracao_ms % 10 != 0:
        raise ValueError(
            f"Duração inválida para SYS_CLOCK: {duracao_ms} ms. "
            "A duração precisa ser múltipla de 10 ms."
        )

    centisegundos = duracao_ms // 10

    # CMP imediato desta versão suporta valores de 0 a 255.
    if centisegundos > 255:
        raise ValueError(
            f"Duração muito alta para o delay atual: {duracao_ms} ms"
        )

    label_delay = f"delay_{indice_evento}"

    # --------------------------------------------------
    # Consulta o horário inicial
    # --------------------------------------------------

    # R0 = operação SYS_CLOCK.
    emitter.mov_imm(
        0,
        SEMIHOSTING_SYS_CLOCK
    )

    # Executa a chamada de semihosting.
    # O resultado volta em R0.
    emitter.svc(
        SEMIHOSTING_SVC
    )

    # R4 = instante inicial.
    emitter.mov_reg(
        4,
        0
    )

    # --------------------------------------------------
    # Laço de espera
    # --------------------------------------------------

    emitter.label(label_delay)

    # Consulta novamente o SYS_CLOCK.
    emitter.mov_imm(
        0,
        SEMIHOSTING_SYS_CLOCK
    )

    emitter.svc(
        SEMIHOSTING_SVC
    )

    # R5 = tempo atual - tempo inicial.
    emitter.sub_reg(
        5,
        0,
        4
    )

    # Compara o tempo decorrido com a duração desejada.
    emitter.cmp_imm(
        5,
        centisegundos
    )

    # Enquanto R5 for menor, continua esperando.
    emitter.blo(label_delay)


def gerar_opcodes_morse(eventos):
    emitter = ArmEmitter()

    # R6 recebe o endereço dos LEDs.
    #
    # Antes usávamos R0 para o endereço dos LEDs,
    # mas agora R0 é utilizado pelo semihosting.
    emitter.ldr_literal(
        6,
        LED_ADDR
    )

    emitter.label("inicio_morse")

    for indice, evento in enumerate(eventos):
        estado = evento["estado"]
        duracao_ms = evento["duracao_ms"]

        if estado == "ON":
            # R1 = 1 e escreve no registrador dos LEDs.
            emitter.mov_imm(1, 1)
            emitter.str_reg(1, 6)

        elif estado == "OFF":
            # R1 = 0 e apaga os LEDs.
            emitter.mov_imm(1, 0)
            emitter.str_reg(1, 6)

        else:
            raise ValueError(
                f"Estado de LED inválido: {estado}"
            )

        # Mantém o estado ON ou OFF pelo tempo do evento.
        gerar_delay(
            emitter,
            duracao_ms,
            indice
        )

    # Apaga o LED depois do último ponto do S.
    emitter.mov_imm(1, 0)
    emitter.str_reg(1, 6)

    # Aguarda 2000 ms antes de iniciar LUCAS novamente.
    gerar_delay(
        emitter,
        PAUSA_ENTRE_REPETICOES_MS,
        len(eventos)
    )

    # Repete LUCAS para sempre.
    emitter.b("inicio_morse")

    return emitter.finalizar()


def words_para_bytes(words):
    """
    Converte as instruções ARM de 32 bits
    para bytes little-endian.
    """

    return b"".join(
        struct.pack("<I", word)
        for word in words
    )


def gerar_elf(codigo, caminho_saida):
    """
    Gera o arquivo ELF32 ARM executável.
    """

    shstrtab = (
        b"\x00"
        b".text\x00"
        b".shstrtab\x00"
    )

    shstrtab_offset = TEXT_OFFSET + len(codigo)

    arquivo = bytearray()

    # Reserva espaço para o ELF Header.
    arquivo.extend(
        b"\x00" * ELF_HEADER_SIZE
    )

    # Program Header.
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
            0x1000              # alinhamento
        )
    )

    # Padding até a seção .text.
    arquivo.extend(
        b"\x00"
        * (TEXT_OFFSET - len(arquivo))
    )

    # Conteúdo da seção .text.
    arquivo.extend(codigo)

    # Tabela com os nomes das seções.
    arquivo.extend(shstrtab)

    e_shoff = len(arquivo)

    # Section Header 0 — NULL.
    arquivo.extend(
        struct.pack(
            "<IIIIIIIIII",
            0, 0, 0, 0, 0,
            0, 0, 0, 0, 0
        )
    )

    # Section Header 1 — .text.
    arquivo.extend(
        struct.pack(
            "<IIIIIIIIII",
            1,                  # sh_name
            1,                  # SHT_PROGBITS
            0x6,                # ALLOC + EXEC
            TEXT_ADDR,          # sh_addr
            TEXT_OFFSET,        # sh_offset
            len(codigo),        # sh_size
            0,                  # sh_link
            0,                  # sh_info
            4,                  # sh_addralign
            0                   # sh_entsize
        )
    )

    # Section Header 2 — .shstrtab.
    arquivo.extend(
        struct.pack(
            "<IIIIIIIIII",
            7,                  # sh_name
            3,                  # SHT_STRTAB
            0,                  # sh_flags
            0,                  # sh_addr
            shstrtab_offset,    # sh_offset
            len(shstrtab),      # sh_size
            0,                  # sh_link
            0,                  # sh_info
            1,                  # sh_addralign
            0                   # sh_entsize
        )
    )

    # ELF Header.
    elf_header = struct.pack(
        "<16sHHIIIIIHHHHHH",
        b"\x7fELF" + bytes([
            1,                  # ELFCLASS32
            1,                  # little-endian
            1,                  # versão
            0,                  # System V
            0, 0, 0, 0,
            0, 0, 0, 0
        ]),
        2,                      # ET_EXEC
        40,                     # EM_ARM
        1,                      # versão
        TEXT_ADDR,              # entry point
        ELF_HEADER_SIZE,        # e_phoff
        e_shoff,                # e_shoff
        0x05000200,             # ARM EABI v5
        ELF_HEADER_SIZE,        # e_ehsize
        PROGRAM_HEADER_SIZE,    # e_phentsize
        1,                      # e_phnum
        SECTION_HEADER_SIZE,    # e_shentsize
        3,                      # e_shnum
        2                       # e_shstrndx
    )

    arquivo[0:ELF_HEADER_SIZE] = elf_header

    with open(
        caminho_saida,
        "wb"
    ) as arquivo_elf:
        arquivo_elf.write(arquivo)

    return {
        "arquivo": caminho_saida,
        "tamanho_codigo": len(codigo),
        "section_table": e_shoff
    }


def carregar_eventos_morse(caminho_morse):
    """
    Carrega o arquivo saida/morse.json.
    """

    with open(
        caminho_morse,
        "r",
        encoding="utf-8"
    ) as arquivo:
        dados = json.load(arquivo)

    if "eventos" not in dados:
        raise ValueError(
            "Arquivo Morse inválido: "
            "campo 'eventos' não encontrado."
        )

    return dados


def resolver_caminho_morse(argumento=None):
    """
    Localiza o arquivo morse.json.
    """

    raiz = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )

    if argumento:
        if os.path.isfile(argumento):
            return os.path.abspath(argumento)

        caminho_em_saida = os.path.join(
            raiz,
            "saida",
            argumento
        )

        if os.path.isfile(caminho_em_saida):
            return caminho_em_saida

        raise FileNotFoundError(
            f"Arquivo Morse não encontrado: {argumento}"
        )

    return os.path.join(
        raiz,
        "saida",
        "morse.json"
    )


def caminho_saida_elf():
    """
    Retorna o caminho de saída do ELF.
    """

    raiz = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )

    pasta_saida = os.path.join(
        raiz,
        "saida"
    )

    os.makedirs(
        pasta_saida,
        exist_ok=True
    )

    return os.path.join(
        pasta_saida,
        "lucas_morse.elf"
    )


if __name__ == "__main__":
    print("Gerando ELF Morse com SYS_CLOCK...")

    argumento = (
        sys.argv[1]
        if len(sys.argv) >= 2
        else None
    )

    try:
        caminho_morse = resolver_caminho_morse(
            argumento
        )

        dados_morse = carregar_eventos_morse(
            caminho_morse
        )

        eventos = dados_morse["eventos"]
        texto = dados_morse.get(
            "texto",
            ""
        )

        words = gerar_opcodes_morse(
            eventos
        )

        codigo = words_para_bytes(
            words
        )

        saida_elf = caminho_saida_elf()

        info = gerar_elf(
            codigo,
            saida_elf
        )

        print("Texto:", texto)
        print("Eventos:", len(eventos))
        print("Temporização: SYS_CLOCK do CPUlator")
        print("Unidade do relógio: 10 ms")
        print(
            "Pausa entre repetições:",
            PAUSA_ENTRE_REPETICOES_MS,
            "ms"
        )
        print(
            "Instruções ARM:",
            len(words)
        )
        print(
            "Tamanho do código:",
            info["tamanho_codigo"],
            "bytes"
        )
        print(
            "ELF gerado em:",
            info["arquivo"]
        )

    except Exception as erro:
        print("Erro:", erro)
        sys.exit(1)