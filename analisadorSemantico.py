# Lucas Balint Vilar – lucasdxl
# Adaptado para o Trabalho Final - geração de ELF ARM com Morse

import sys
import os
import json

_RAIZ = os.path.dirname(os.path.abspath(__file__))
_PASTA_SAIDA = os.path.join(_RAIZ, "saida")

sys.path.insert(0, os.path.join(_RAIZ, "src"))

from prepararEntradaSemantica import prepararEntradaSemantica

from construirTabelaSimbolos import (
    construirTabelaSimbolos,
    salvarTabelaSimbolos,
    salvarTabelaSimbolosMarkdown,
    salvarErrosDeclaracao,
)

from verificarTipos import verificarTipos

from gerarArvoreAtribuida import (
    gerarArvoreAtribuida,
    salvarArvoreAtribuida,
    salvarArvoreAtribuidaMarkdown,
)

from gerarMorse import (
    extrair_valores_ascii,
    ascii_para_texto,
    texto_para_morse,
    morse_para_eventos,
    salvar_resultado_morse,
)

from gerarElfMorse import (
    gerar_opcodes_morse,
    words_para_bytes,
    gerar_elf,
    caminho_saida_elf,
)


def _garantir_saida():
    os.makedirs(_PASTA_SAIDA, exist_ok=True)


def _rel(caminho):
    return os.path.relpath(caminho, _RAIZ)


def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo_de_teste>")
        sys.exit(1)

    arquivo = sys.argv[1]

    _garantir_saida()

    print(f"\n{'=' * 60}")
    print(f"  Arquivo: {arquivo}")
    print(f"{'=' * 60}")

    # ==================================================
    # Etapa 1 — Léxico + Sintático
    # ==================================================

    try:
        entrada = prepararEntradaSemantica(arquivo)

    except FileNotFoundError as erro:
        print(f"[ERRO] {erro}")
        sys.exit(1)

    except Exception as erro:
        print(f"[ERRO LÉXICO/SINTÁTICO] {erro}")
        sys.exit(1)

    print(f"[Léxico]    OK — {len(entrada['tokens'])} tokens reconhecidos")
    print("[Sintático] OK — árvore sintática gerada")

    arvore_base = entrada["arvore_base_semantica"]
    arvore_simplificada = entrada["arvore_simplificada"]

    # ==================================================
    # Etapa 2 — Semântico
    # ==================================================

    tabelaSimbolos = construirTabelaSimbolos(arvore_base)
    tipos = verificarTipos(arvore_base, tabelaSimbolos)

    todos_erros = tipos.get("erros", [])

    cam_tab_json = salvarTabelaSimbolos(tabelaSimbolos)
    cam_tab_md = salvarTabelaSimbolosMarkdown(tabelaSimbolos, arquivo_origem=arquivo)
    cam_erros = salvarErrosDeclaracao({"erros": todos_erros})

    n_simbolos = len(tabelaSimbolos.get("simbolos", {}))

    print(f"\n[Semântico] {n_simbolos} símbolo(s) na tabela")

    if todos_erros:
        print(f"[Semântico] {len(todos_erros)} erro(s) encontrado(s):")

        for erro in todos_erros:
            print(
                f"  • [{erro.get('codigo')}] "
                f"linha {erro.get('linha')}: "
                f"{erro.get('mensagem')}"
            )

    else:
        print("[Semântico] OK — nenhum erro encontrado")

    arvoreAtribuida = gerarArvoreAtribuida(
        arvore_simplificada,
        tabelaSimbolos,
        tipos
    )

    cam_arv_json = salvarArvoreAtribuida(arvoreAtribuida)
    cam_arv_md = salvarArvoreAtribuidaMarkdown(
        arvoreAtribuida,
        arquivo_origem=arquivo
    )

    print("[Semântico] Árvore sintática atribuída gerada")

    # ==================================================
    # Etapa 3 — ASCII + Morse + ELF
    # ==================================================

    cam_morse = None
    cam_elf = None
    texto_morse = ""
    total_eventos = 0
    total_instrucoes = 0
    tamanho_codigo = 0

    if todos_erros:
        print("\n[Morse/ELF] IGNORADO — erros semânticos impedem a geração")

    else:
        try:
            # A árvore simplificada gera os valores numéricos.
            # Esses valores são interpretados como códigos ASCII.
            valores_ascii = extrair_valores_ascii(arvore_simplificada)

            texto_morse = ascii_para_texto(valores_ascii)
            morse = texto_para_morse(texto_morse)
            eventos = morse_para_eventos(morse)

            resultado_morse = {
                "arquivo": entrada["arquivo"],
                "valores_ascii": valores_ascii,
                "texto": texto_morse,
                "morse": morse,
                "eventos": eventos
            }

            cam_morse = salvar_resultado_morse(resultado_morse)

            print(f"\n[Morse] OK — texto gerado: {texto_morse}")
            print(f"[Morse] {len(eventos)} evento(s) ON/OFF gerado(s)")

            # Os eventos ON/OFF viram opcodes ARM.
            words = gerar_opcodes_morse(eventos)
            codigo = words_para_bytes(words)

            total_eventos = len(eventos)
            total_instrucoes = len(words)
            tamanho_codigo = len(codigo)

            cam_elf = caminho_saida_elf()
            gerar_elf(codigo, cam_elf)

            print("[ELF]     OK — executável ARM gerado")
            print(f"[ELF]     Código ARM: {tamanho_codigo} byte(s)")
            print(f"[ELF]     Instruções ARM: {total_instrucoes}")

        except Exception as erro:
            print(f"\n[Morse/ELF] ERRO — {erro}")
            sys.exit(1)

    # ==================================================
    # Manifesto da execução
    # ==================================================

    manifest = {
        "arquivo_analisado": arquivo,
        "tokens_reconhecidos": len(entrada["tokens"]),
        "simbolos_registrados": n_simbolos,
        "total_erros": len(todos_erros),
        "erros": todos_erros,

        "assembly_gerado": False,
        "elf_gerado": cam_elf is not None,

        "texto_morse": texto_morse,
        "eventos_morse": total_eventos,
        "instrucoes_arm": total_instrucoes,
        "tamanho_codigo_arm_bytes": tamanho_codigo,
    }

    cam_manifest = os.path.join(_PASTA_SAIDA, "ultima_execucao.json")

    with open(cam_manifest, "w", encoding="utf-8") as arquivo_manifest:
        json.dump(manifest, arquivo_manifest, indent=2, ensure_ascii=False)

    # ==================================================
    # Saída final
    # ==================================================

    print(f"\n{'─' * 60}")
    print("Artefatos gerados:")

    for caminho in [
        cam_tab_json,
        cam_tab_md,
        cam_erros,
        cam_arv_json,
        cam_arv_md,
        cam_manifest,
    ]:
        print(f"  {_rel(caminho)}")

    if cam_morse:
        print(f"  {_rel(cam_morse)}")

    if cam_elf:
        print(f"  {_rel(cam_elf)}")

    print(f"{'─' * 60}\n")

    sys.exit(1 if todos_erros else 0)


if __name__ == "__main__":
    main()