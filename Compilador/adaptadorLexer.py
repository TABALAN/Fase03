# Diccionarios de mapeo
KEYWORDS = {
    'int', 'float', 'if', 'else', 'while', 'return',
    'and', 'switch', 'do', 'not', 'for', 'default',
    'case', 'boolean', 'try', 'catch', 'or', 'main',
    'elif', 'print', 'input', 'def', 'const', 'True', 'False', 'void'
}

COMP = {
    '==': 'EQ', '!=': 'NEQ', '<=': 'LEQ', '>=': 'GEQ',
    '<':  'LT', '>':  'GT',  '%':  'MOD',
    '++': 'INC', '--': 'DEC', '+=': 'PLUSEQ', '-=': 'MINUSEQ'
}

ESP = {
    '(': 'LPAREN', ')': 'RPAREN',
    '{': 'LBRACE', '}': 'RBRACE',
    '=': 'ASSIGN', '!': 'NEG',
    '&': 'AMP',    '~': 'TILDE',
    '¬': 'NEG',    '°': 'DEG'
}

PUNT = {
    ',': 'COMMA', ':': 'COLON', ';': 'SEMI'
}

OP = {
    '+': 'PLUS', '-': 'MINUS',
    '*': 'TIMES', '/': 'DIVIDE'
}

CP = {
    'Salto': 'NEWLINE'
}

class Token:
    #Constructor perrón
    def __init__(self, diccionario):
        lexema = diccionario['lexema']
        self.tipo = diccionario['tipo']

        if self.tipo == 'key':
            self.type = lexema.upper()
        elif self.tipo == 'num':
            self.type = 'NUM'
        elif self.tipo == 'txt':
            self.type = 'STRING'
        elif self.tipo == 'decimal':
            self.type = 'DECIMAL'
        elif self.tipo == "id":
            self.type = "ID"
        elif self.tipo == 'ERROR':
            self.type = "LEXICO_ERROR"
        elif self.tipo == 'Salto':
            self.type = CP.get(lexema, 'CP')
        elif self.tipo == 'comp':
            self.type = COMP.get(lexema, 'COMP')
        elif self.tipo == 'esp':
            self.type = ESP.get(lexema, 'ESP')
        elif self.tipo == 'punt':
            self.type = PUNT.get(lexema, 'PUNT')
        elif self.tipo == 'op':
            self.type = OP.get(lexema, 'OP')
        else:
            self.type = self.tipo.upper()  

        self.value = diccionario['lexema']
        self.lineno = diccionario['linea']
        self.lexpos = diccionario['columna']

class adaptadorL:
    def __init__(self, listaTokens):
        #Se convierten todos los diccionarios de token a objetos Token
        self.tokens = [Token(tokensito) for tokensito in listaTokens]
        self.pos = 0
        self.pendiente = None #Para manejar recuperación
        self.parser = None

    def reinsert(self, token):
        self.pendiente = token   #Para guardar el token 

    def token(self):
        if self.pendiente is not None:   #revisar primero
            tok = self.pendiente
            self.pendiente = None
            return tok
        while self.pos < len(self.tokens):
            tokenito = self.tokens[self.pos]
            self.pos += 1
            #Saltar identación y newline para evitar errores en el parser
            if tokenito.tipo in ('INDENT', 'DEDENT', 'NEWLINE'):
                continue

            # Si hay un error léxico sin ';' después, inyectar uno para que lo consuma el parser
            if tokenito.type == 'LEXICO_ERROR':
                if self.pos < len(self.tokens) and self.tokens[self.pos].type != 'SEMI':
                    import ply.lex as lex
                    semi = lex.LexToken()
                    semi.type   = 'SEMI'
                    semi.value  = ';'
                    semi.lineno = tokenito.lineno
                    semi.lexpos = tokenito.lexpos
                    semi.lexer  = self
                    self.pendiente = semi
                tokenito.parser = self.parser
                tokenito.lexer  = self
                return tokenito
            
            tokenito.parser = self.parser
            tokenito.lexer = self
            return tokenito
        return None
    