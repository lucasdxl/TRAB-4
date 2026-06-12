import struct

# ==================================================
# Gerador ELF ARM32 mínimo
#
# Este arquivo gera um ELF executável ARM32 aceito
# pelo CPUlator ARMv7 DE1-SoC.
#
# Teste atual:
#   LDR R0, =0xFF200000
#   MOV R1, #1
#   STR R1, [R0]
#   B .
#   .word 0xFF200000
#
# Objetivo:
#   Acender o LED0 e ficar em loop infinito.
# ==================================================


def word_little_endian(hex_word):
    """
    Recebe uma instrução ARM em hexadecimal no formato visual normal
    e devolve os bytes em little endian.

    Exemplo:
        e3a01001 -> 01 10 a0 e3
    """
    valor = int(hex_word, 16)
    return struct.pack("<I", valor)


# ==================================================
# Código ARM
#
# Opcodes descobertos no CPUlator:
#
# e59f0008 -> LDR R0, [PC, #8]
# e3a01001 -> MOV R1, #1
# e5801000 -> STR R1, [R0]
# eafffffe -> B .
# ff200000 -> endereço dos LEDs
#
# Em ARM, o arquivo precisa guardar as words em little endian.
# ==================================================

opcodes = [
    "e59f0008",  # ldr r0, [pc, #8]
    "e3a01001",  # mov r1, #1
    "e5801000",  # str r1, [r0]
    "eafffffe",  # b .
    "ff200000",  # .word 0xFF200000
]

codigo = b"".join(word_little_endian(op) for op in opcodes)


# ==================================================
# Constantes do ELF
# ==================================================

TEXT_OFFSET = 0x1000
TEXT_ADDR = 0x8000

ELF_HEADER_SIZE = 52
PROGRAM_HEADER_SIZE = 32
SECTION_HEADER_SIZE = 40

# Tabela de strings das seções
# Índices:
#   0 -> ""
#   1 -> ".text"
#   7 -> ".shstrtab"
shstrtab = (
    b"\x00"
    b".text\x00"
    b".shstrtab\x00"
)

SHSTRTAB_OFFSET = TEXT_OFFSET + len(codigo)


# ==================================================
# Montagem do arquivo ELF
# ==================================================

arquivo = bytearray()

# Reserva espaço para o ELF Header
arquivo.extend(b"\x00" * ELF_HEADER_SIZE)

# Program Header
arquivo.extend(
    struct.pack(
        "<IIIIIIII",
        1,                  # p_type = PT_LOAD
        TEXT_OFFSET,        # p_offset
        TEXT_ADDR,          # p_vaddr
        TEXT_ADDR,          # p_paddr
        len(codigo),        # p_filesz
        len(codigo),        # p_memsz
        5,                  # p_flags = R + X
        0x1000              # p_align
    )
)

# Padding até o offset onde a seção .text começa
arquivo.extend(
    b"\x00" * (TEXT_OFFSET - len(arquivo))
)

# Seção .text
arquivo.extend(codigo)

# Seção .shstrtab
arquivo.extend(shstrtab)

# Offset da tabela de Section Headers
e_shoff = len(arquivo)


# ==================================================
# Section Header Table
# ==================================================

# Section 0 - NULL
arquivo.extend(
    struct.pack(
        "<IIIIIIIIII",
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    )
)

# Section 1 - .text
arquivo.extend(
    struct.pack(
        "<IIIIIIIIII",
        1,                  # sh_name = ".text"
        1,                  # sh_type = SHT_PROGBITS
        0x6,                # sh_flags = SHF_ALLOC | SHF_EXECINSTR
        TEXT_ADDR,          # sh_addr
        TEXT_OFFSET,        # sh_offset
        len(codigo),        # sh_size
        0,                  # sh_link
        0,                  # sh_info
        4,                  # sh_addralign
        0                   # sh_entsize
    )
)

# Section 2 - .shstrtab
arquivo.extend(
    struct.pack(
        "<IIIIIIIIII",
        7,                  # sh_name = ".shstrtab"
        3,                  # sh_type = SHT_STRTAB
        0,                  # sh_flags
        0,                  # sh_addr
        SHSTRTAB_OFFSET,    # sh_offset
        len(shstrtab),      # sh_size
        0,                  # sh_link
        0,                  # sh_info
        1,                  # sh_addralign
        0                   # sh_entsize
    )
)


# ==================================================
# ELF Header
# ==================================================

elf_header = struct.pack(
    "<16sHHIIIIIHHHHHH",
    b"\x7fELF" + bytes([
        1,                  # ELFCLASS32
        1,                  # ELFDATA2LSB
        1,                  # EV_CURRENT
        0,                  # System V ABI
        0, 0, 0, 0, 0, 0, 0, 0
    ]),
    2,                      # e_type = ET_EXEC
    40,                     # e_machine = ARM
    1,                      # e_version
    TEXT_ADDR,              # e_entry
    ELF_HEADER_SIZE,        # e_phoff
    e_shoff,                # e_shoff
    0x05000200,             # e_flags = ARM EABI v5, soft-float
    ELF_HEADER_SIZE,        # e_ehsize
    PROGRAM_HEADER_SIZE,    # e_phentsize
    1,                      # e_phnum
    SECTION_HEADER_SIZE,    # e_shentsize
    3,                      # e_shnum
    2                       # e_shstrndx
)

arquivo[0:ELF_HEADER_SIZE] = elf_header


# ==================================================
# Salva ELF
# ==================================================

with open("nosso.elf", "wb") as f:
    f.write(arquivo)

print("ELF gerado com sucesso.")
print(f"Tamanho do código: {len(codigo)} bytes")
print(f"Section Table: 0x{e_shoff:X}")