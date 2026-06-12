# Victor Rahal Basseto - Aluno 4

import os

raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
caminhoAssembly = os.path.join(raiz, "saida", "Assembly.s")

def valoresConstantes(no, valores):
    if isinstance(no, dict):
        if no.get("tipo") == "terminal" and no.get('simbolo') in ["INT", "REAL"]:
            valores.add(float(no["valor"]))

        for valor in no.values():
            if isinstance(valor, dict):
                valoresConstantes(valor, valores)
            elif isinstance(valor, list):
                for i in valor:
                    if isinstance(i, dict):
                        valoresConstantes(i, valores)

def valoresMemorias(no, memorias):
    if isinstance(no, dict):
        if no.get("tipo") == "leitura_memoria" or no.get("tipo") == "atribuicao_memoria":
            memorias.add(no["nome"])
        elif no.get("tipo") == "for":
            memorias.add(no["variavel"])

        for valor in no.values():
            if isinstance(valor, dict):
                valoresMemorias(valor, memorias)
            elif isinstance(valor, list):
                for i in valor:
                    if isinstance(i, dict):
                        valoresMemorias(i, memorias)

def branchFalso(operador):
    match operador:
        case "<":
            return "BGE"
        case ">":
            return "BLE"
        case _:
            return "B erro_condicao"
        
def gerarCondicao(no, assembly, contadorPot, contadorLabel, numLinhaAtual):
    gerarNo_Assembly(no['esquerdo'], assembly, contadorPot, contadorLabel, numLinhaAtual)
    assembly.append("VMOV.F64 D1, D0")

    gerarNo_Assembly(no["direito"], assembly, contadorPot, contadorLabel, numLinhaAtual)
    assembly.append("VCMP.F64 D1, D0")
    assembly.append("VMRS APSR_nzcv, FPSCR")

    return no["operador"]

def gerarNo_Assembly(no, assembly, contadorPot, contadorLabel, numLinhaAtual):
    tipo = no.get("tipo")
    
    match tipo:
        case "sequencia":
            proximaLinha = gerarNo_Assembly(no["atual"], assembly, contadorPot, contadorLabel, numLinhaAtual)
            return gerarNo_Assembly(no["proximo"], assembly, contadorPot, contadorLabel, proximaLinha)
        
        case "fim_programa":
            return numLinhaAtual
        
        case "terminal":
            simbolo = no.get("simbolo")
            if simbolo in ["INT", "REAL"]:
                val = float(no["valor"])
                x = f"val_{str(val).replace('.','_')}"
                assembly.append(f"LDR R0, ={x}")
                assembly.append("VLDR.F64 D0, [R0]")

            return numLinhaAtual
        
        case "leitura_memoria":
            nomeMemo=no["nome"]
            assembly.append(f"LDR R0, =memo_{nomeMemo}")
            assembly.append("VLDR.F64 D0, [R0]")
            return numLinhaAtual
        
        case "atribuicao_memoria":
            nomeMemo = no["nome"]
            gerarNo_Assembly(no["valor"], assembly, contadorPot, contadorLabel, numLinhaAtual)
            assembly.append(f"LDR R0, =memo_{nomeMemo}")
            assembly.append("VSTR.F64 D0, [R0]")
            assembly.append(f"LDR R0, =resultado_{numLinhaAtual}")
            assembly.append("VSTR.F64 D0, [R0]")
            assembly.append(".ltorg")

            return numLinhaAtual + 1
        
        case "res":
            indice = no["indice"]
            linhaResultado = numLinhaAtual - indice

            if linhaResultado < 0:
                assembly.append("UDF #2")
            else:
                assembly.append(f"LDR R0, =resultado_{linhaResultado}")
                assembly.append("VLDR.F64 D0, [R0]")

            assembly.append(f"LDR R0, =resultado_{numLinhaAtual}")
            assembly.append("VSTR.F64 D0, [R0]")
            assembly.append(".ltorg")
            return numLinhaAtual + 1
        
        case "if":
            idLabel = contadorLabel[0]
            contadorLabel[0] += 1
            labelElse = f"if_else{idLabel}"
            labelFim = f"if_fim{idLabel}"

            operador = gerarCondicao(no["condicao"], assembly, contadorPot, contadorLabel, numLinhaAtual)
            assembly.append(f"{branchFalso(operador)} {labelElse}")

            numLinhaAtual = gerarNo_Assembly(no["entao"], assembly, contadorPot, contadorLabel, numLinhaAtual)
            assembly.append(f"B {labelFim}")

            assembly.append(f"{labelElse}:")
            numLinhaAtual = gerarNo_Assembly(no["senao"], assembly, contadorPot, contadorLabel, numLinhaAtual)
            
            assembly.append(f"{labelFim}:")
            assembly.append(".ltorg")

            return numLinhaAtual
        
        case "while":
            idLabel = contadorLabel[0]
            contadorLabel[0] += 1

            labelInicio = f"while_inicio_{idLabel}"
            labelFim = f"while_fim_{idLabel}"

            assembly.append(f"{labelInicio}:")

            operador = gerarCondicao(no["condicao"], assembly, contadorPot, contadorLabel, numLinhaAtual)
            assembly.append(f"{branchFalso(operador)} {labelFim}")

            numLinhaAtual = gerarNo_Assembly(no["corpo"], assembly, contadorPot, contadorLabel, numLinhaAtual)

            assembly.append(f"B {labelInicio}")
            assembly.append(f"{labelFim}:")
            assembly.append(".ltorg")

            return numLinhaAtual
        
        case "for":
            idLabel = contadorLabel[0]
            contadorLabel[0] += 1

            labelInicio = f"for_inicio_{idLabel}"
            labelFim = f"for_fim_{idLabel}"

            variavel = no["variavel"]

            # inicializa variavel
            gerarNo_Assembly(no["inicio"], assembly, contadorPot, contadorLabel, numLinhaAtual)
            assembly.append(f"LDR R0, =memo_{variavel}")
            assembly.append("VSTR.F64 D0, [R0]")

            assembly.append(f"{labelInicio}:")

            # carrega variavel em D1
            assembly.append(f"LDR R0, =memo_{variavel}")
            assembly.append("VLDR.F64 D1, [R0]")

            # carrega fim em D0
            gerarNo_Assembly(no["fim"], assembly, contadorPot, contadorLabel, numLinhaAtual)

            # se variavel > fim, sai
            assembly.append("VCMP.F64 D1, D0")
            assembly.append("VMRS APSR_nzcv, FPSCR")
            assembly.append(f"BGT {labelFim}")

            numLinhaAtual = gerarNo_Assembly(no["corpo"], assembly, contadorPot, contadorLabel, numLinhaAtual)

            # incremento da variável
            assembly.append(f"LDR R0, =memo_{variavel}")
            assembly.append("VLDR.F64 D0, [R0]")
            assembly.append("LDR R0, =val_1_0")
            assembly.append("VLDR.F64 D1, [R0]")
            assembly.append("VADD.F64 D0, D0, D1")
            assembly.append(f"LDR R0, =memo_{variavel}")
            assembly.append("VSTR.F64 D0, [R0]")

            assembly.append(f"B {labelInicio}")
            assembly.append(f"{labelFim}:")
            assembly.append(".ltorg")

            return numLinhaAtual
        
        case "expressao_aritmetica":
            operandoEsquerdo = no["operandos"][0]
            operandoDireito = no["operandos"][1]
            operador = no["operador"]

            #gera operando esquerdo no registardor D0
            gerarNo_Assembly(operandoEsquerdo, assembly, contadorPot, contadorLabel, numLinhaAtual)
            assembly.append("VMOV.F64 D1, D0")

            #gera operando direito no registrador D0
            gerarNo_Assembly(operandoDireito, assembly, contadorPot, contadorLabel, numLinhaAtual)

            match operador:
                case '+':
                    assembly.append(f"VADD.F64 D0, D1, D0") # operacao de soma
                case '-':
                    assembly.append(f"VSUB.F64 D0, D1, D0") # oepracao de subtração
                case '*':
                    assembly.append(f"VMUL.F64 D0, D1, D0") # operacao de multiplicação
                case '|':
                    assembly.append(f"VDIV.F64 D0, D1, D0") # operação de divisão real
                case '/':
                    assembly.append(f"VDIV.F64 D0, D1, D0") # divisão não inteira
                    assembly.append(f"VCVT.S32.F64 S0, D0") # converte para inteiro, truncando o float
                    assembly.append(f"VCVT.F64.S32 D0, S0") # volta o resultado para double
                case '%': # resto: A - (A/B) * B
                    assembly.append(f"VDIV.F64 D2, D1, D0") # divisão não inteira
                    assembly.append(f"VCVT.S32.F64 S0, D2") # converte para inteiro, truncando o float
                    assembly.append(f"VCVT.F64.S32 D2, S0") # volta o resultado para double
                    assembly.append(f"VMUL.F64 D2, D2, D0") # (A/B) * B
                    assembly.append(f"VSUB.F64 D0, D1, D2") # A - (A/B) * B
                case '^': #potenciacao
                    loopPot = f"pot_{contadorPot[0]}" # label do loop da potenciacao
                    fimLoop = f"potFim_{contadorPot[0]}" # label de saida do loop da potenciacao
                    contadorPot[0] += 1 # incrementa o contador
                    assembly.append(f"VMOV.F64 D6, D1") # numero base
                    assembly.append(f"VMOV.F64 D7, D0") # numero expoente
                    assembly.append(f"LDR R0, =val_1_0") # Carrega o 1.0 no registrador
                    assembly.append(f"VLDR.F64 D5, [R0]") #D5 = 1.0
                    assembly.append(f"{loopPot}:")
                    assembly.append(f"VCVT.S32.F64 S0, D7") # converte o expoente para numero inteiro
                    assembly.append(f"VMOV R2, S0") # move o valor para um registrador geral R2
                    assembly.append(f"CMP R2, #1") # compara o expoente com o numero 1
                    assembly.append(f"BLE {fimLoop}") # sai do loop se o expoente for menor que 1
                    assembly.append(f"VMUL.F64 D6, D6, D1") # multiplica o numero por ele mesmo
                    assembly.append(f"VSUB.F64 D7, D7, D5") # diminui o expoente em 1 
                    assembly.append(f"B {loopPot}") # volta pro loop e reinicia o processo
                    assembly.append(f"{fimLoop}:") 
                    assembly.append(f"VMOV.F64 D0, D6") # move o resultado final para r1

            assembly.append(f"LDR R0, =resultado_{numLinhaAtual}")
            assembly.append(f"VSTR.F64 D0, [R0]")
            assembly.append(".ltorg")

            return numLinhaAtual + 1

def gerarAssembly(arvoreSimplificada):
    assembly = []  # lista que armazena as instruções assembly
    contadorPot = [0] # contador para gerar labels únicos de pontenciação
    contadorLabel = [0]
    valores = set()
    memorias = set()
    valoresMemorias(arvoreSimplificada, memorias)
    valoresConstantes(arvoreSimplificada, valores)
    valores.add(1.0)

    # cabeçalho seção data para definição dos valores doubles
    assembly.append(".global _start")
    assembly.append(".data")
    assembly.append(".align 3")
    for val in sorted(valores):
        x = f"val_{str(val).replace('.', '_')}" # cria a label do valor
        assembly.append(f"{x}: .double {val}")

    for memo in sorted(memorias):
        assembly.append(f"memo_{memo}: .double 0.0")

    for k in range(20):
        assembly.append(f"resultado_{k}: .double 0.0")

    # cabeçalho padrão
    assembly.append(".text")
    assembly.append(".arm")
    assembly.append(".fpu vfpv3")
    assembly.append(".align 2")        
    assembly.append("_start:")

    gerarNo_Assembly(arvoreSimplificada, assembly, contadorPot, contadorLabel,0)

    # finaliza o programa para não ficar em loop
    assembly.append("    MOV R7, #1")
    assembly.append("    SWI #0")
                
    # escreve o código assembly no arquivo de saída
    with open(caminhoAssembly, 'w') as f:
        for linha in assembly:
            f.write(linha + '\n')

    return assembly  # retorna a lista