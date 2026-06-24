# Compilador — Fase 4

**Instituição:** Pontifícia Universidade Católica do Paraná — Campus Curitiba
**Ano/Semestre:** 2026/1
**Disciplina:** Compiladores
**Professor:** Frank Coelho de Alcantara

Este projeto implementa a **Fase 4 de um compilador**, integrando as etapas de análise léxica, sintática e semântica com um novo backend responsável por:

1. avaliar as expressões da linguagem;
2. interpretar seus resultados como códigos ASCII;
3. converter os caracteres obtidos para código Morse;
4. transformar o Morse em eventos temporizados de LED;
5. gerar diretamente opcodes ARM de 32 bits;
6. construir um arquivo ELF executável;
7. executar o resultado no CPUlator, utilizando o sistema ARMv7 DE1-SoC.

A geração do ELF é realizada pelo próprio projeto, sem depender de assembler ou linker externos durante a execução normal do compilador.

---

## Responsável pela Fase 4

| Nome               | GitHub                                   |
| ------------------ | ---------------------------------------- |
| Lucas Balint Vilar | [@lucasdxl](https://github.com/lucasdxl) |

**Linguagem de implementação:** Python 3.10 ou superior
**Modalidade da Fase 4:** trabalho individual

> As etapas léxica, sintática e semântica foram desenvolvidas nas fases anteriores do projeto. Nesta fase foram implementados e integrados os módulos de geração ASCII, Morse, opcodes ARM32 e ELF.

---

## Funcionalidades principais

O compilador realiza o seguinte pipeline:

```text
Arquivo-fonte
    ↓
Análise léxica
    ↓
Análise sintática
    ↓
Análise semântica
    ↓
Árvore sintática simplificada
    ↓
Avaliação das expressões
    ↓
Valores ASCII
    ↓
Texto
    ↓
Código Morse
    ↓
Eventos ON/OFF temporizados
    ↓
Opcodes ARM32
    ↓
Arquivo ELF
    ↓
Execução no CPUlator
```

A geração de Morse e ELF ocorre somente quando não existem erros léxicos, sintáticos ou semânticos que impeçam a compilação.

---

## Novos módulos da Fase 4

### `src/gerarMorse.py`

Responsável por:

* avaliar as expressões presentes na árvore simplificada;
* resolver referências feitas com `RES`;
* validar se os resultados são inteiros;
* validar a faixa ASCII imprimível;
* converter números ASCII em caracteres;
* converter o texto para código Morse;
* gerar eventos temporizados de LED;
* salvar o resultado intermediário em `saida/morse.json`.

Fluxo do módulo:

```text
Árvore simplificada
→ resultados numéricos
→ ASCII
→ texto
→ Morse
→ eventos de LED
```

### `src/gerarElfMorse.py`

Responsável por:

* transformar os eventos Morse em instruções ARM32;
* gerar manualmente os opcodes das instruções utilizadas;
* resolver labels e deslocamentos de branches;
* construir e resolver o literal pool;
* converter words ARM para bytes little-endian;
* montar o ELF Header;
* montar o Program Header;
* montar as seções `.text` e `.shstrtab`;
* montar os Section Headers;
* salvar o executável em `saida/lucas_morse.elf`.

Fluxo do módulo:

```text
Eventos ON/OFF
→ instruções ARM32
→ opcodes
→ bytes little-endian
→ estrutura ELF
→ executável
```

### Integração no analisador semântico

O `analisadorSemantico.py` atua como orquestrador do processo:

```text
validação semântica
→ geração Morse
→ geração ARM
→ geração ELF
→ manifesto da execução
```

Caso existam erros semânticos, as etapas Morse e ELF são ignoradas.

---

## Requisitos

### Execução do compilador

* Python 3.10 ou superior;
* nenhuma biblioteca externa obrigatória.

### Execução dos testes

A suíte de testes utiliza `pytest`.

Instalação:

```bash
python -m pip install pytest
```

### Execução do ELF

Para visualizar a saída nos LEDs:

* navegador atualizado;
* CPUlator;
* sistema selecionado: **ARMv7 DE1-SoC**.

---

## Estrutura principal do projeto

```text
TRAB-4/
├── analisadorSemantico.py
├── README.md
├── gramatica_ebnf.md
├── regras_de_tipos.md
│
├── src/
│   ├── main.py
│   ├── gerarMorse.py
│   ├── gerarElfMorse.py
│   └── demais módulos do compilador
│
├── testes/
│   ├── testeLucasMorse.txt
│   ├── testeLexico.py
│   ├── testeSintatico.py
│   ├── testeTabelaSimbolos.py
│   ├── testeSemantico.py
│   ├── testeIntegracao.py
│   └── demais arquivos de teste
│
├── docs/
│
└── saida/
    ├── morse.json
    ├── lucas_morse.elf
    ├── tabela_simbolos.json
    ├── tabela_simbolos.md
    ├── erros_declaracao.json
    ├── arvore_atribuida.json
    ├── arvore_atribuida.md
    └── ultima_execucao.json
```

---

## Como executar

Execute os comandos a partir da raiz do projeto.

### Opção 1 — analisador principal

```bash
python analisadorSemantico.py testes/testeLucasMorse.txt
```

### Opção 2 — entrypoint da pasta `src`

```bash
python src/main.py testes/testeLucasMorse.txt
```

A segunda opção chama o mesmo fluxo de compilação.

### Saída esperada no terminal

Em uma execução válida, serão apresentadas mensagens semelhantes a:

```text
[Léxico]    OK
[Sintático] OK
[Semântico] OK
[Morse]     OK
[ELF]       OK
```

O terminal também informa:

* quantidade de tokens reconhecidos;
* quantidade de símbolos registrados;
* erros semânticos encontrados;
* texto formado pelos valores ASCII;
* quantidade de eventos Morse;
* quantidade de words ARM geradas;
* tamanho do código ARM em bytes;
* caminhos dos artefatos criados.

### Códigos de saída

| Código | Significado                                     |
| -----: | ----------------------------------------------- |
|    `0` | compilação concluída sem erros                  |
|    `1` | erro léxico, sintático, semântico ou de geração |

---

## Como executar no CPUlator

Após executar o compilador, o arquivo abaixo será criado:

```text
saida/lucas_morse.elf
```

Para executá-lo:

1. abra o CPUlator;
2. selecione o sistema **ARMv7 DE1-SoC**;
3. utilize a opção **Load ELF Executable**;
4. selecione `saida/lucas_morse.elf`;
5. pressione **Continue** ou **Run**;
6. observe os LEDs virtuais do sistema.

O programa repete continuamente o texto convertido para Morse.

O arquivo de saída ainda possui o nome fixo `lucas_morse.elf`, mas seu conteúdo pode representar qualquer texto válido produzido pelo arquivo de entrada.

---

## Exemplo de conversão

O arquivo `testes/testeLucasMorse.txt` produz os seguintes resultados:

```text
76, 85, 67, 65, 83
```

Esses valores são interpretados como códigos ASCII:

| Código | Caractere |  Morse |
| -----: | :-------: | :----: |
|     76 |     L     | `.-..` |
|     85 |     U     |  `..-` |
|     67 |     C     | `-.-.` |
|     65 |     A     |  `.-`  |
|     83 |     S     |  `...` |

Resultado:

```text
LUCAS
```

Fluxo completo:

```text
[76, 85, 67, 65, 83]
→ "LUCAS"
→ ".-.. ..- -.-. .- ..."
→ eventos ON/OFF
→ opcodes ARM32
→ lucas_morse.elf
```

---

## Conversão ASCII

Os resultados das expressões não são letras inicialmente. Eles continuam sendo valores numéricos.

O backend utiliza a função `chr()` do Python para interpretar cada inteiro como código de caractere:

```python
chr(76)  # L
chr(85)  # U
chr(67)  # C
chr(65)  # A
chr(83)  # S
```

Os caracteres são unidos para formar o texto final.

### Faixa aceita

Os valores devem:

* ser inteiros;
* estar entre `32` e `126`;
* representar caracteres ASCII imprimíveis.

Exemplos:

| Valor | Resultado |
| ----: | :-------: |
|    32 |   espaço  |
|    48 |    `0`    |
|    65 |    `A`    |
|    76 |    `L`    |
|    90 |    `Z`    |
|    97 |    `a`    |
|   122 |    `z`    |

Embora a faixa ASCII imprimível contenha pontuações, a tabela Morse atual aceita apenas:

* letras de `A` a `Z`;
* dígitos de `0` a `9`;
* espaço.

Caracteres não presentes na tabela Morse resultam em erro.

---

## Outros nomes e nomes compostos

O compilador não está limitado ao texto `LUCAS`.

Qualquer sequência válida de resultados ASCII pode gerar outro nome.

### Exemplo: `FULANO`

```text
F = 70
U = 85
L = 76
A = 65
N = 78
O = 79
```

### Exemplo: `LUCAS VILAR`

O espaço deve ser representado pelo código ASCII `32`:

```text
76, 85, 67, 65, 83, 32, 86, 73, 76, 65, 82
```

### Exemplo: `ANA BEATRIZ`

```text
65, 78, 65, 32, 66, 69, 65, 84, 82, 73, 90
```

As letras são convertidas para maiúsculas antes da consulta à tabela Morse.

Caracteres acentuados, como `Á`, `Ã`, `Ç` e `É`, não fazem parte da tabela atual. Para esses casos, deve-se utilizar a versão sem acento ou ampliar a tabela.

---

## Tempos do código Morse

Os eventos são definidos em milissegundos:

| Evento                                  | Estado do LED | Duração |
| --------------------------------------- | :-----------: | ------: |
| Ponto                                   |       ON      |  300 ms |
| Traço                                   |       ON      |  600 ms |
| Intervalo entre símbolos da mesma letra |      OFF      |  450 ms |
| Intervalo entre letras                  |      OFF      |  900 ms |
| Intervalo entre palavras                |      OFF      | 2000 ms |
| Intervalo antes de repetir o texto      |      OFF      | 2000 ms |

Os tempos são registrados no arquivo `saida/morse.json`.

Exemplo:

```json
{
  "estado": "ON",
  "duracao_ms": 300,
  "descricao": "ponto de L"
}
```

---

## Temporização com `SYS_CLOCK`

A versão final utiliza o serviço de semihosting `SYS_CLOCK` disponibilizado pelo CPUlator.

O serviço:

* é identificado pela operação `0x10`;
* é chamado por meio da instrução `SVC 0x123456`;
* retorna o tempo no registrador `R0`;
* utiliza centésimos de segundo;
* possui resolução de 10 ms.

Conversões utilizadas:

| Duração | Unidades do `SYS_CLOCK` |
| ------: | ----------------------: |
|  300 ms |                      30 |
|  450 ms |                      45 |
|  600 ms |                      60 |
|  900 ms |                      90 |
| 2000 ms |                     200 |

O delay funciona da seguinte forma:

```text
consulta o horário inicial
→ guarda o resultado
→ consulta o relógio novamente
→ calcula o tempo decorrido
→ repete enquanto o tempo for menor que o desejado
```

Conceitualmente:

```asm
MOV R0, #0x10
SVC 0x123456
MOV R4, R0

delay:
    MOV R0, #0x10
    SVC 0x123456
    SUB R5, R0, R4
    CMP R5, #tempo
    BLO delay
```

> O `SYS_CLOCK` é um serviço de semihosting oferecido pelo ambiente de simulação. Ele não corresponde diretamente ao contador de ciclos físico do Cortex-A9 e é utilizado nesta implementação para controlar os tempos observáveis no CPUlator.

---

## Controle dos LEDs

O endereço mapeado utilizado para os LEDs é:

```python
LED_ADDR = 0xFF200000
```

O endereço é carregado no registrador `R6`.

Para ligar o primeiro LED:

```asm
MOV R1, #1
STR R1, [R6]
```

Para apagá-lo:

```asm
MOV R1, #0
STR R1, [R6]
```

O registrador `R0` não é utilizado para armazenar o endereço dos LEDs porque ele é reservado para as chamadas de semihosting.

---

## Geração dos opcodes ARM32

A classe `ArmEmitter` funciona como um pequeno emissor de código de máquina.

Ela gera os opcodes das instruções utilizadas pelo programa:

| Método          | Instrução                     |
| --------------- | ----------------------------- |
| `mov_imm()`     | `MOV Rd, #imediato`           |
| `mov_reg()`     | `MOV Rd, Rm`                  |
| `sub_reg()`     | `SUB Rd, Rn, Rm`              |
| `str_reg()`     | `STR Rt, [Rn]`                |
| `cmp_imm()`     | `CMP Rn, #imediato`           |
| `svc()`         | `SVC #imediato`               |
| `b()`           | branch incondicional          |
| `blo()`         | branch se menor sem sinal     |
| `ldr_literal()` | carregamento por literal pool |

Exemplo:

```python
emitter.mov_imm(1, 1)
```

gera o opcode correspondente a:

```asm
MOV R1, #1
```

O Python não executa essa instrução. Ele apenas produz a word de 32 bits que será executada posteriormente pelo ARM simulado.

---

## Labels e branches

Os destinos dos branches podem não ser conhecidos no momento em que a instrução é emitida.

Por isso, o gerador utiliza duas etapas:

```text
1. reserva a posição do branch;
2. calcula e preenche o deslocamento ao finalizar o código.
```

O cálculo considera que, no modo ARM utilizado, o valor observado do PC está oito bytes à frente da instrução atual.

---

## Literal pool

Constantes grandes, como:

```text
0xFF200000
```

não são inseridas diretamente por um `MOV` simples.

O valor é armazenado ao final do código em um **literal pool**, e uma instrução `LDR` relativa ao PC é gerada para carregá-lo.

Fluxo:

```text
LDR reservado
→ constante armazenada no literal pool
→ cálculo do deslocamento
→ preenchimento do opcode final
```

---

## Formato ELF gerado

O executável utiliza:

```text
Classe: ELF32
Arquitetura: ARM
Endian: little-endian
Tipo: executável
Ponto de entrada: 0x8000
```

A estrutura contém:

```text
ELF Header
Program Header
seção .text
seção .shstrtab
Section Headers
```

### Endereços principais

| Constante     |        Valor | Finalidade                          |
| ------------- | -----------: | ----------------------------------- |
| `TEXT_OFFSET` |     `0x1000` | posição do código dentro do arquivo |
| `TEXT_ADDR`   |     `0x8000` | endereço do código na memória       |
| `LED_ADDR`    | `0xFF200000` | endereço mapeado dos LEDs           |

### Segmento carregável

O Program Header define um segmento:

```text
Tipo: PT_LOAD
Permissões: leitura e execução
Endereço: 0x8000
Alinhamento: 0x1000
```

Quando o ELF é carregado, o CPUlator copia a seção de código para o endereço informado e inicia a execução em `0x8000`.

---

## Little-endian

Cada instrução ARM é representada por uma word de 32 bits.

O projeto utiliza:

```python
struct.pack("<I", word)
```

onde:

```text
< = little-endian
I = inteiro sem sinal de 32 bits
```

Por exemplo, a word:

```text
0xE3A01001
```

é armazenada no arquivo como:

```text
01 10 A0 E3
```

---

## Descrição da linguagem

A linguagem utiliza **notação polonesa reversa — RPN**.

Cada instrução é delimitada por parênteses, e todo programa deve começar com `(START)` e terminar com `(END)`.

### Estrutura geral

```text
(START)
(instrução 1)
(instrução 2)
...
(END)
```

### Comentários

Comentários são delimitados por `*{` e `}*`.

```text
*{ comentário em linha inteira }*
(5 3 +) *{ comentário ao final da linha }*
(5 *{ comentário entre tokens }* 3 +)
```

### Operadores aritméticos

| Operador | Operação        |              |
| :------: | --------------- | ------------ |
|    `+`   | soma            |              |
|    `-`   | subtração       |              |
|    `*`   | multiplicação   |              |
|     `    | `               | divisão real |
|    `/`   | divisão inteira |              |
|    `%`   | resto           |              |
|    `^`   | potenciação     |              |

Exemplos:

```text
(5 3 +)
(10 2 -)
(4 3 *)
(9.0 3.0 |)
(9 4 /)
(9 4 %)
(2 3 ^)
```

### Expressões aninhadas

```text
((3 2 +) (5 1 -) *)
```

Equivale a:

```text
(3 + 2) × (5 - 1)
```

### Memória

```text
(V MEM X)
```

Armazena o valor `V` na variável `X`.

Exemplo:

```text
(15 MEM TOTAL)
```

Para consultar a variável:

```text
(TOTAL)
```

### Operação `RES`

```text
(N RES)
```

Retorna o resultado obtido `N` posições atrás.

| Comando   | Resultado                        |
| --------- | -------------------------------- |
| `(1 RES)` | resultado anterior               |
| `(2 RES)` | resultado de duas posições atrás |
| `(3 RES)` | resultado de três posições atrás |

O valor deve ser maior ou igual a `1` e não pode ultrapassar a quantidade de resultados disponíveis.

### Estruturas de controle

```text
(IF (condicao) (ramo_verdadeiro) (ramo_falso))
(WHILE (condicao) (corpo))
(FOR inicio fim VARIAVEL (corpo))
```

Operadores relacionais suportados:

```text
<
>
```

---

## Tipos suportados

| Tipo   | Descrição                 | Exemplos                |
| ------ | ------------------------- | ----------------------- |
| `INT`  | número inteiro            | `5`, `42`, `0`          |
| `REAL` | número de ponto flutuante | `3.14`, `9.0`, `2.5`    |
| `BOOL` | resultado lógico          | resultado de `<` ou `>` |

### Regras principais

* `/` e `%` exigem operandos `INT`;
* `|` representa divisão real;
* `<` e `>` aceitam `INT` ou `REAL`;
* o resultado de uma condição é `BOOL`;
* valores utilizados como ASCII devem ser inteiros.

---

## Regras de variáveis

* identificadores utilizam letras latinas maiúsculas;
* uma variável é definida na primeira atribuição com `MEM`;
* o tipo é inferido no momento da definição;
* o tipo não pode ser alterado por uma reatribuição incompatível;
* utilizar uma variável antes da definição é erro semântico;
* a variável de controle do `FOR` é do tipo `INT`;
* o escopo das variáveis é global dentro do arquivo.

---

## Execução dos testes

### Todos os testes

```bash
python -m pytest testes/ -v
```

### Testes por módulo

```bash
python -m pytest testes/testeLexico.py -v
python -m pytest testes/testeSintatico.py -v
python -m pytest testes/testeTabelaSimbolos.py -v
python -m pytest testes/testeSemantico.py -v
python -m pytest testes/testeIntegracao.py -v
python -m pytest testes/testePrepararEntradaSemantica.py -v
```

### Arquivos de entrada disponíveis

* `testeLucasMorse.txt` — programa válido que gera o texto `LUCAS`;
* `teste_comentario_fim.txt` — comentário ao final da linha;
* `teste_comentario_inicio.txt` — comentário no início;
* `teste_comentario_linha.txt` — comentário em linha separada;
* `teste_comentario_meio.txt` — comentário entre tokens;
* `teste_comentario_nao_fechado.txt` — comentário sem fechamento.

Exemplos:

```bash
python analisadorSemantico.py testes/testeLucasMorse.txt
python analisadorSemantico.py testes/teste_comentario_nao_fechado.txt
```

---

## Artefatos gerados

Todos os artefatos são armazenados em `saida/`.

| Arquivo                 | Formato   | Descrição                                    |
| ----------------------- | --------- | -------------------------------------------- |
| `tabela_simbolos.json`  | JSON      | tabela de símbolos                           |
| `tabela_simbolos.md`    | Markdown  | representação legível da tabela              |
| `erros_declaracao.json` | JSON      | erros semânticos encontrados                 |
| `arvore_atribuida.json` | JSON      | árvore anotada com tipos                     |
| `arvore_atribuida.md`   | Markdown  | representação legível da árvore              |
| `morse.json`            | JSON      | valores ASCII, texto, Morse e eventos ON/OFF |
| `lucas_morse.elf`       | ELF32 ARM | executável para o CPUlator                   |
| `ultima_execucao.json`  | JSON      | resumo e estatísticas da última compilação   |

### Manifesto `ultima_execucao.json`

O manifesto registra:

* arquivo analisado;
* tokens reconhecidos;
* símbolos registrados;
* erros encontrados;
* confirmação da geração do ELF;
* texto gerado;
* quantidade de eventos Morse;
* quantidade de words ARM;
* tamanho do código ARM em bytes.

Exemplo simplificado:

```json
{
  "arquivo_analisado": "testes/testeLucasMorse.txt",
  "tokens_reconhecidos": 32,
  "simbolos_registrados": 0,
  "total_erros": 0,
  "assembly_gerado": false,
  "elf_gerado": true,
  "texto_morse": "LUCAS",
  "eventos_morse": 31,
  "instrucoes_arm": 0,
  "tamanho_codigo_arm_bytes": 0
}
```

Os valores numéricos variam conforme o programa compilado.

---

## Tratamento de erros

O compilador interrompe a geração do backend quando encontra erros.

Podem ser detectados:

* erros léxicos;
* comentários não finalizados;
* estrutura sintática inválida;
* variáveis não declaradas;
* redefinições incompatíveis;
* uso inválido de `RES`;
* operadores aplicados a tipos incompatíveis;
* resultado ASCII decimal;
* valor fora da faixa ASCII imprimível;
* caractere sem representação Morse;
* erro na geração de branches ou literais;
* erro ao escrever o ELF.

Quando existem erros semânticos:

```text
[Morse/ELF] IGNORADO — erros semânticos impedem a geração
```

Quando ocorre um erro específico no backend:

```text
[Morse/ELF] ERRO — descrição do erro
```

---

## Limitações atuais

* a tabela Morse suporta letras de `A` a `Z`, números de `0` a `9` e espaço;
* caracteres acentuados não são suportados;
* o arquivo ELF de saída possui nome fixo `lucas_morse.elf`;
* o delay atual aceita valores múltiplos de 10 ms;
* o `CMP` imediato implementado suporta até 255 centésimos, equivalentes a 2550 ms;
* o literal pool deve permanecer dentro do alcance do `LDR` relativo ao PC;
* o `SYS_CLOCK` é específico do ambiente de semihosting do CPUlator;
* o ELF atual é direcionado ao sistema ARMv7 DE1-SoC.

---

## Documentação adicional

* [`gramatica_ebnf.md`](gramatica_ebnf.md) — gramática da linguagem em EBNF;
* [`regras_de_tipos.md`](regras_de_tipos.md) — regras da análise semântica;
* [`docs/`](docs/) — documentação complementar do projeto.

---

## Repositório

[github.com/lucasdxl/TRAB-4](https://github.com/lucasdxl/TRAB-4)