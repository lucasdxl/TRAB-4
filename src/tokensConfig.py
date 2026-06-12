# Paulo Henrique Eidi Mino - Aluno 2
# Configuração e constantes para utilização no analisador léxico

KEYWORDS = {
    "START": "KW_START",
    "END":   "KW_END",
    "RES":   "KW_RES",
    "MEM":   "KW_MEM",
    "IF":    "KW_IF",
    "WHILE": "KW_WHILE",
    "FOR":   "KW_FOR"}
 
OPERADORES_SIMPLES = {
    '+': 'OP_SUM',
    '-': 'OP_SUB',
    '*': 'OP_MUL',
    '|': 'OP_DIVR',
    '/': 'OP_DIVI',
    '%': 'OP_MOD',
    '^': 'OP_POW',
    '<': 'OP_LT',
    '>': 'OP_GT'} 

OPERADORES_DUPLOS = {
    '<': 'OP_LE',
    '>': 'OP_GE',
    '=': 'OP_EQ',
    '!': 'OP_NE'
}
 
def criarToken(tipo, valor, linha):
    return {"tipo": tipo, "valor": valor, "linha": linha}