# Victor Rahal Basseto - Aluno 4

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

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
from gerarAssembly import gerarAssembly

_RAIZ        = os.path.dirname(os.path.abspath(__file__))
_PASTA_SAIDA = os.path.join(_RAIZ, "saida")

def _garantir_saida():
    os.makedirs(_PASTA_SAIDA, exist_ok=True)

def _rel(caminho):
    return os.path.relpath(caminho, _RAIZ)

def main():
    if len(sys.argv) < 2:
        print("Uso: python AnalisadorSemantico.py <arquivo_de_teste>")
        sys.exit(1)
    arquivo = sys.argv[1]
    _garantir_saida()
    print(f"\n{'='*60}")
    print(f"  Arquivo: {arquivo}")
    print(f"{'='*60}")

    try:
        entrada = prepararEntradaSemantica(arquivo)
    except FileNotFoundError as e:
        print(f"[ERRO] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO LÉXICO/SINTÁTICO] {e}")
        sys.exit(1)
    print(f"[Léxico]    OK — {len(entrada['tokens'])} tokens reconhecidos")
    print("[Sintático] OK — árvore sintática gerada")
    arvore_base  = entrada["arvore_base_semantica"]
    arvore_simpl = entrada["arvore_simplificada"]
    tabelaSimbolos = construirTabelaSimbolos(arvore_base)
    tipos       = verificarTipos(arvore_base, tabelaSimbolos)
    todos_erros = tipos.get("erros", [])
    cam_tab_json = salvarTabelaSimbolos(tabelaSimbolos)
    cam_tab_md   = salvarTabelaSimbolosMarkdown(tabelaSimbolos, arquivo_origem=arquivo)
    cam_erros    = salvarErrosDeclaracao({"erros": todos_erros})
    n_simbolos = len(tabelaSimbolos.get("simbolos", {}))
    print(f"\n[Semântico] {n_simbolos} símbolo(s) na tabela")

    if todos_erros:
        print(f"[Semântico] {len(todos_erros)} erro(s) encontrado(s):")
        for e in todos_erros:
            print(f"  • [{e.get('codigo')}] linha {e.get('linha')}: {e.get('mensagem')}")
    else:
        print("[Semântico] OK — nenhum erro encontrado")
    arvoreAtribuida = gerarArvoreAtribuida(arvore_simpl, tabelaSimbolos, tipos)
    cam_arv_json    = salvarArvoreAtribuida(arvoreAtribuida)
    cam_arv_md      = salvarArvoreAtribuidaMarkdown(arvoreAtribuida, arquivo_origem=arquivo)
    print("[Semântico] Árvore sintática atribuída gerada")
    cam_asm = None
    if todos_erros:
        print("\n[Assembly]  IGNORADO — erros semânticos impedem a geração")
    else:
        gerarAssembly(arvoreAtribuida)
        cam_asm = os.path.join(_PASTA_SAIDA, "Assembly.s")
        print("[Assembly]  OK")

    manifest = {
        "arquivo_analisado": arquivo,
        "tokens_reconhecidos": len(entrada["tokens"]),
        "simbolos_registrados": n_simbolos,
        "total_erros": len(todos_erros),
        "erros": todos_erros,
        "assembly_gerado": cam_asm is not None,
    }
    cam_manifest = os.path.join(_PASTA_SAIDA, "ultima_execucao.json")
    with open(cam_manifest, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n{'─'*60}")
    print("Artefatos gerados:")
    for cam in [cam_tab_json, cam_tab_md, cam_erros,
                cam_arv_json, cam_arv_md, cam_manifest]:
        print(f"  {_rel(cam)}")
    if cam_asm:
        print(f"  {_rel(cam_asm)}")
    print(f"{'─'*60}\n")

    sys.exit(1 if todos_erros else 0)

if __name__ == "__main__":
    main()