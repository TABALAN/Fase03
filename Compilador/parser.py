import ply.yacc as yacc 
from adaptadorLexer import adaptadorL

#Las funciones deben estar fuera para que funcione el PLY
tokens = (
            # Literales
            'ID', 'NUM', 'DECIMAL', 'STRING', 'TRUE', 'FALSE', 'STR',
            # Palabras clave
            'FLOAT', 'INT', 'IF', 'ELSE', 'WHILE', 'FOR', 'RETURN', 'AND', 'OR', 'NOT',
            'SWITCH', 'DO', 'DEFAULT', 'CASE', 'BOOLEAN', 'TRY', 'CATCH',
            'MAIN', 'ELIF', 'PRINT', 'INPUT', 'READ', 'DEF', 'CONST', 'VOID',
            # Operadores aritméticos
            'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
            # Operadores de comparación
            'EQ', 'NEQ', 'LEQ', 'GEQ', 'LT', 'GT', 'MOD',
            'INC', 'DEC', 'PLUSEQ', 'MINUSEQ',
            # Especiales
            'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
            'ASSIGN', 'NEG', 'AMP', 'TILDE', 'DEG',
            # Puntuación
            'COMMA', 'COLON', 'SEMI',
            # Especial
            'LEXICO_ERROR'
        )

#Todas las producciones escritas en funciones para que PLY las identifique
# S' -> S S' | eps
def p_sprime_recurse(p):
    "sprime : s sprime"
    p[0] = ('sprime', p[1], p[2])
 
def p_sprime_empty(p):
    "sprime : empty"
    p[0] = None

#Estructuras de bloque (sin SEMI al final)
def p_s_if(p):
    "s : IF LPAREN a RPAREN c b"
    p[0] = ('if', p[3], p[5], p[6])
 
def p_s_while(p):
    "s : WHILE LPAREN a RPAREN c"
    p[0] = ('while', p[3], p[5])
 
def p_s_for(p):
    # Los ';' dentro del for son separadores internos.
    # El bloque C cierra la sentencia.
    "s : FOR LPAREN k SEMI a SEMI i RPAREN c"
    p[0] = ('for', p[3], p[5], p[7], p[9])
 
def p_s_def(p):
    "s : l"
    p[0] = p[1]

#Sentencias simples (terminan en SEMI)
def p_s_print(p):
    "s : PRINT LPAREN e RPAREN SEMI"
    p[0] = ('print', p[3])
 
def p_s_return(p):
    "s : RETURN e SEMI"
    p[0] = ('return', p[2])
 
def p_s_k(p):
    "s : k SEMI"
    p[0] = p[1]
 
def p_s_call(p):
    "s : ID LPAREN o RPAREN SEMI"
    p[0] = ('call', p[1], p[3])

#Error léxico: se consume el token inválido.
def p_s_lexico_error(p):
    "s : LEXICO_ERROR SEMI"
    print(f"[Error léxico] Línea {p.lineno(1)}: token inválido '{p[1]}'") 
    p[0] = None

#Recuperación de errores
def p_sprime_error_semi(p):
    "sprime : error SEMI sprime"
    print(f"[Error sintáctico] Se descartó una sentencia inválida ({p.lineno(1)}).")
    p[0] = p[3]          # continúa con el resto del programa
    p.parser.errok()     # permite detectar más errores
 
def p_sprime_error_rbrace(p):
    "sprime : error RBRACE sprime"
    # Reinsertamos el '}' para que la producción C lo consuma correctamente.
    print(f"[Error sintáctico] Bloque mal formado, se intentó recuperar. ({p.lineno(2)})")
    p[0] = p[3]
    p.parser.errok()

#C — bloque de código {sprime}
def p_c(p):
    "c : LBRACE sprime RBRACE"
    p[0] = ('block', p[2])

#A — condición: E F E D
def p_a(p):
    "a : e f e d"
    p[0] = ('condition', p[1], p[2], p[3], p[4])

#B — rama else/elif
def p_b_elif(p):
    "b : ELIF LPAREN a RPAREN c b"
    p[0] = ('elif', p[3], p[5], p[6])
 
def p_b_else(p):
    "b : ELSE c"
    p[0] = ('else', p[2])
 
def p_b_empty(p):
    "b : empty"
    p[0] = None

#D — conectores lógicos: and/or E F E D | eps
def p_d_and(p):
    "d : AND e f e d"
    p[0] = ('and', p[2], p[3], p[4], p[5])
 
def p_d_or(p):
    "d : OR e f e d"
    p[0] = ('or', p[2], p[3], p[4], p[5])
 
def p_d_empty(p):
    "d : empty"
    p[0] = None

#E / E' — expresiones aditivas
def p_e(p):
    "e : g eprime"
    p[0] = ('expr', p[1], p[2])
 
def p_eprime_plus(p):
    "eprime : PLUS g eprime"
    p[0] = ('+', p[2], p[3])
 
def p_eprime_minus(p):
    "eprime : MINUS g eprime"
    p[0] = ('-', p[2], p[3])
 
def p_eprime_empty(p):
    "eprime : empty"
    p[0] = None

#F — operadores de comparación
def p_f_geq(p):
    "f : GEQ"
    p[0] = '>='
 
def p_f_eq(p):
    "f : EQ"
    p[0] = '=='
 
def p_f_neq(p):
    "f : NEQ"
    p[0] = '!='
 
def p_f_leq(p):
    "f : LEQ"
    p[0] = '<='
 
def p_f_lt(p):
    "f : LT"
    p[0] = '<'
 
def p_f_gt(p):
    "f : GT"
    p[0] = '>'

#G / G' — expresiones multiplicativas
def p_g(p):
    "g : h gprime"
    p[0] = ('term', p[1], p[2])
 
def p_gprime_times(p):
    "gprime : TIMES h gprime"
    p[0] = ('*', p[2], p[3])
 
def p_gprime_divide(p):
    "gprime : DIVIDE h gprime"
    p[0] = ('/', p[2], p[3])
 
def p_gprime_mod(p):
    "gprime : MOD h gprime"
    p[0] = ('%', p[2], p[3])
 
def p_gprime_empty(p):
    "gprime : empty"
    p[0] = None

#H — átomos (valores base)
def p_h_paren(p):
    "h : LPAREN e RPAREN"
    p[0] = p[2]
 
def p_h_call(p):
    "h : ID LPAREN o RPAREN"
    p[0] = ('call', p[1], p[3])
 
def p_h_id(p):
    "h : ID"
    p[0] = ('id', p[1])
 
def p_h_num(p):
    "h : NUM"
    p[0] = ('int', p[1])
 
def p_h_float(p):
    "h : DECIMAL"
    p[0] = ('float', p[1])
 
def p_h_string(p):
    "h : STR"
    p[0] = ('string', p[1])
 
def p_h_true(p):
    "h : TRUE"
    p[0] = ('boolean', True)

def p_h_false(p):
    "h : FALSE"
    p[0] = ('boolean', False)
 
def p_h_input(p):
    "h : INPUT LPAREN STR RPAREN"
    p[0] = ('input', p[3])

#I — actualizaciones (usadas dentro del for)
def p_i_assign(p):
    "i : ID ASSIGN e"
    p[0] = ('assign', p[1], p[3])

def p_i_inc(p):
    "i : ID INC"
    p[0] = ('inc', p[1])
 
def p_i_dec(p):
    "i : ID DEC"
    p[0] = ('dec', p[1])
 
def p_i_pluseq(p):
    "i : ID PLUSEQ e"
    p[0] = ('pluseq', p[1], p[3])
 
def p_i_minuseq(p):
    "i : ID MINUSEQ e"
    p[0] = ('minuseq', p[1], p[3])

#J — tipos de dato
def p_j_int(p):
    "j : INT"
    p[0] = 'int'
 
def p_j_float(p):
    "j : FLOAT"
    p[0] = 'float'
 
def p_j_bool(p):
    "j : BOOLEAN"
    p[0] = 'boolean'

def p_j_void(p):
    "j : VOID"
    p[0] = 'void'

def p_j_string(p):
    "j : STRING"
    p[0] = 'string'

#K — asignación / declaración / incremento (sentencias simples sin SEMI, porque S ya les añade el SEMI en su propia producción)
def p_k_assign(p):
    "k : ID ASSIGN e"
    p[0] = ('assign', p[1], p[3])
 
def p_k_decl(p):
    "k : j ID ASSIGN e"
    p[0] = ('decl', p[1], p[2], p[4])
 
def p_k_inc(p):
    "k : ID INC"
    p[0] = ('inc', p[1])
 
def p_k_dec(p):
    "k : ID DEC"
    p[0] = ('dec', p[1])

def p_k_const(p): #Agregar la producción para declarar constantes.
    "k : CONST j ID ASSIGN e"
    p[0] = ('const', p[2], p[3], p[5])

def p_k_pluseq(p): #Agregados para eliminar error de += y -=
    "k : ID PLUSEQ e"
    p[0] = ('pluseq', p[1], p[3])

def p_k_minuseq(p):
    "k : ID MINUSEQ e"
    p[0] = ('minuseq', p[1], p[3])

#L — definición de función  def id(M) C
def p_l(p):
    "l : DEF j ID LPAREN m RPAREN c"
    p[0] = ('def', p[2], p[3], p[5], p[7])

#M / N — parámetros formales
def p_m_id(p):
    "m : j ID n"                    
    p[0] = ('param', p[2], p[1], p[3])
 
def p_m_empty(p):
    "m : empty"
    p[0] = None
 
def p_n_comma(p):
    "n : COMMA j ID n"             
    p[0] = ('param', p[3], p[2], p[4])
 
def p_n_empty(p):
    "n : empty"
    p[0] = None

#O / P — argumentos en llamada a función
def p_o_expr(p):
    "o : e p"
    p[0] = ('arg', p[1], p[2])
 
def p_o_empty(p):
    "o : empty"
    p[0] = None
 
def p_p_comma(p):
    "p : COMMA e p"
    p[0] = ('arg', p[2], p[3])
 
def p_p_empty(p):
    "p : empty"
    p[0] = None

# empty
def p_empty(p):
    "empty :"
    p[0] = None

#p_error — manejador global
def p_error(token):
    if token is None:
        print("[Error sintáctico] Fin de archivo inesperado.")
        return
    print(
        f"[Error sintáctico] Línea {token.lineno}: "
        f"token inesperado '{token.value}' ({token.type})"
    )

pi = yacc.yacc(start="sprime")

#Instancia del parser

class parserin:
    def __init__(self):
        self.parser = pi

    def analizar(self, lista_tokens):
        adaptador = adaptadorL(lista_tokens)
        adaptador.parser = self.parser
        return self.parser.parse(input=None, lexer=adaptador)
