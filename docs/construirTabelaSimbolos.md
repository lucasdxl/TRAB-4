# Tabela de Símbolos

Este documento descreve o funcionamento de `construirTabelaSimbolos(arvore)`, implementada em `src/construirTabelaSimbolos.py`. Esta é a etapa responsável por registrar as variáveis (memórias) da linguagem, inferir seus tipos no momento da definição e detectar erros semânticos de declaração antes da verificação de tipos.

## Objetivo

A função recebe a árvore sintática crua produzida pelo parser LL(1) da Fase 2 (no formato `{tipo_no, simbolo, producao, token, filhos}`) e produz:

- uma tabela de símbolos com todas as memórias declaradas;
- uma lista de erros semânticos de declaração.

Essa mesma estrutura de árvore é consumida depois por `verificarTipos()` (Aluno 3) e por `gerarArvoreAtribuida()` (Aluno 4).

## Estrutura de um símbolo

Cada identificador registrado na tabela é um dicionário com os campos:

| Campo | Significado |
|---|---|
| `nome` | Nome da memória (letras latinas maiúsculas, ex.: `TOTAL`, `CONT`). |
| `tipo` | Tipo inferido na definição: `INT`, `REAL`, `BOOL` ou `INDEFINIDO`. |
| `linha_definicao` | Linha do código-fonte onde a memória foi definida pela primeira vez. |
| `linhas_uso` | Lista de linhas em que a memória é lida/usada. |
| `inicializada` | Sempre `True` nesta linguagem (a definição já inicializa). |
| `escopo` | `global` — cada arquivo é um escopo de memória independente (Seção 2.2). |

A saída final tem o formato:

```python
{
    "simbolos": { "<NOME>": { ...campos acima... }, ... },
    "erros":    [ { "codigo", "linha", "simbolo", "mensagem" }, ... ]
}
```

## Inferência de tipo na definição

O tipo de uma memória é determinado no momento da definição `(V MEM X)`, a partir do valor `V`:

- literal inteiro → `INT`;
- literal real → `REAL`;
- leitura de outra memória já declarada → herda o tipo dessa memória;
- expressão, `RES` ou condição → fica `INDEFINIDO` nesta etapa e é resolvido depois por `verificarTipos()` (Aluno 3).

Os tipos são **estáticos e fortes**: uma vez definido, o tipo não pode mudar. Uma redefinição com tipo diferente é reportada como erro, mas o tipo original é preservado para evitar cascata de erros nas linhas seguintes.

## Comandos especiais

A tabela controla o significado semântico dos três comandos especiais:

- **`(V MEM X)`** — definição/atribuição. Visita o lado direito `V` primeiro (registrando leituras e possíveis erros), depois registra ou atualiza o símbolo `X`.
- **`(X)`** — leitura simples. Registra a linha de uso em `linhas_uso`; se `X` não existir, gera `VARIAVEL_NAO_DECLARADA`.
- **`(N RES)`** — referência a resultado anterior. Validada quanto ao índice (ver convenção abaixo).

### Convenção de RES

O índice `N` de `(N RES)` deve ser um inteiro não-negativo que aponte para uma linha lógica já processada. A contagem de linha lógica (`linha_logica`) **só incrementa no nível superior do programa**: expressões aninhadas dentro de uma linha não inflam o contador, mantendo a mesma semântica usada na geração de Assembly. Validação:

- `N` não inteiro ou negativo → `RES_INDICE_INVALIDO`;
- `N >= linha_logica` (linha inexistente) → `RES_INDICE_INVALIDO`.

## Variável de controle de FOR

A gramática força `FOR INT INT MEM_ID linha`, então a variável de controle é sempre `INT` por construção. A tabela:

- declara a variável como `INT` se ainda não existir;
- atualiza de `INDEFINIDO` para `INT` se necessário;
- gera `FOR_VARIAVEL_REDEFINIDA` se a variável já existia com tipo incompatível (ex.: `REAL`).

## Códigos de erro gerados

| Código | Quando ocorre |
|---|---|
| `VARIAVEL_NAO_DECLARADA` | Uso/leitura de uma memória que nunca foi definida. |
| `REDEFINICAO_INCOMPATIVEL` | Memória definida com um tipo e redefinida com outro. |
| `RES_INDICE_INVALIDO` | Índice de `RES` negativo, não inteiro, ou apontando para linha inexistente. |
| `FOR_VARIAVEL_REDEFINIDA` | Variável de controle de `FOR` já declarada com tipo diferente de `INT`. |

Os erros são dicionários estruturados (não strings), o que permite acumular vários erros sem interromper a análise — o usuário vê todos de uma vez. Cada erro traz `codigo`, `linha`, `simbolo` e `mensagem` (com indicação de linha).

## Artefatos persistidos (Seção 10.4)

A função expõe três rotinas de salvamento, todas gravando em `saida/`:

- `salvarTabelaSimbolos(resultado)` → `tabela_simbolos.json` (artefato de máquina);
- `salvarTabelaSimbolosMarkdown(resultado, arquivo_origem=...)` → `tabela_simbolos.md` (versão legível);
- `salvarErrosDeclaracao(resultado)` → `erros_declaracao.json` (relatório, exigido mesmo que vazio).

## Interface

- **Entrada:** árvore sintática inicial (`arvore_base_semantica`, saída de `prepararEntradaSemantica`).
- **Saída:** tabela de símbolos + lista de erros de declaração.
- **Fornece** a tabela para `verificarTipos()` (Aluno 3) e `gerarArvoreAtribuida()` (Aluno 4).

## Observação sobre integração

O erro `VARIAVEL_NAO_DECLARADA` é detectado tanto aqui quanto em `verificarTipos()` (Aluno 3). Para evitar mensagens duplicadas no relatório final, a fonte única de verdade desse erro deve ser a tabela de símbolos; o verificador de tipos deve apenas propagar o tipo `ERRO` sem re-registrar o mesmo erro. Esse alinhamento é responsabilidade conjunta dos Alunos 2 e 3.
