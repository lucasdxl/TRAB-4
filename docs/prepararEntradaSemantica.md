# Preparação da Entrada Semântica

Este documento descreve o funcionamento da função `prepararEntradaSemantica(arquivo)`.

A função é responsável por integrar as etapas anteriores do compilador (análise léxica e análise sintática) e preparar as estruturas que serão utilizadas pelo analisador semântico.

## Objetivo

A função recebe o nome de um arquivo de teste e produz:

* vetor de tokens gerado pelo analisador léxico;
* derivação sintática produzida pelo parser LL(1);
* árvore sintática inicial;
* árvore-base utilizada pela análise semântica;
* árvore sintática simplificada.

Além disso, a função reaproveita integralmente os componentes desenvolvidos nas fases anteriores do projeto.

---

## Fluxo de Execução

A preparação da entrada semântica ocorre na seguinte sequência:

```text
arquivo .txt
        ↓
análise léxica
        ↓
vetor de tokens
        ↓
análise sintática LL(1)
        ↓
derivação
        ↓
árvore sintática JSON
        ↓
gerarArvore()
        ↓
árvore sintática em objetos
        ↓
simplificarArvore()
        ↓
árvore simplificada
```

---

## Leitura do Arquivo

A função recebe o nome do arquivo por parâmetro:

```python
prepararEntradaSemantica("teste1.txt")
```

O caminho completo é montado automaticamente utilizando a pasta `testes` do projeto.

Caso o arquivo não exista, é gerada a exceção:

```text
FileNotFoundError
```

---

## Análise Léxica

A etapa léxica é executada através da função:

```python
tokens = lerTokens(caminhoArquivo)
```

O analisador léxico é responsável por:

* reconhecer tokens válidos da linguagem;
* identificar palavras reservadas;
* identificar números inteiros e reais;
* reconhecer operadores;
* reconhecer delimitadores;
* reconhecer comentários delimitados por:

```text
*{
comentário
}*
```

Os comentários são descartados e não geram tokens.

Caso existam caracteres inválidos ou comentários não fechados corretamente, erros léxicos são reportados antes da etapa sintática.

---

## Construção da Gramática

A gramática LL(1) utilizada pelo parser é construída por:

```python
info = construirGramatica()
```

A estrutura retornada contém:

* símbolo inicial;
* tabela LL(1);
* produções da gramática.

---

## Análise Sintática

A validação sintática é realizada através de:

```python
derivacao, derivacaoJson = parsear(
    tokens,
    info["tabela_ll1"],
    info["inicio"]
)
```

O parser LL(1) utiliza pilha e tabela preditiva para validar a entrada.

Nessa etapa são verificadas as regras da gramática, incluindo:

```text
(START)
...
(END)
```

Caso a sequência de tokens não respeite a gramática, um erro sintático é reportado.

---

## Geração da Árvore Sintática

A árvore retornada pelo parser é inicialmente produzida em formato JSON.

Posteriormente ela é convertida para uma estrutura baseada em objetos através da função:

```python
arvoreSintatica = gerarArvore(derivacaoJson)
```

Essa representação facilita a navegação pela árvore durante as próximas etapas do compilador.

---

## Árvore Base Semântica

A árvore-base utilizada pela análise semântica corresponde à árvore produzida diretamente pelo analisador sintático:

```python
arvore_base_semantica = derivacaoJson
```

Essa estrutura preserva integralmente a derivação reconhecida pela gramática e serve como entrada para:

```python
construirTabelaSimbolos()
gerarArvoreAtribuida()
```

---

## Árvore Simplificada

Também é produzida uma versão simplificada da árvore:

```python
arvoreSimplificada = simplificarArvore(arvoreSintatica)
```

Essa estrutura remove elementos intermediários da gramática e facilita algumas etapas posteriores do projeto.

---

## Estruturas Retornadas

A função retorna:

```python
{
    "arquivo",
    "tokens",
    "derivacao",
    "arvore_sintatica",
    "arvore_base_semantica",
    "arvore_simplificada"
}
```

Essas informações são utilizadas pelas próximas etapas da análise semântica do compilador.