from TablaSimbolos import Tabla

# Tipos compatibles para operaciones aritméticas
ARITMETICOS = {'int', 'float'}

# Coerción: int -> float cuando se mezclan
#Retrona el tipo resultante de operar var1 con var2
def coercionar(var1, var2):

    if var1 == 'error' or var2 == 'error':
        return 'error'   # no propagar errores en cascada
    
    if var1 in ARITMETICOS and var2 in ARITMETICOS:

        if 'float' in (var1, var2):
            return 'float'
        else:
            return 'int'
        
    return None #Si es una combinación inválida

#Sirve para verificar si tipo_expr es asignable a tipo_var
#Va a permitir la coerción de int a float, pero no de float a int por pérdida de precisión

def tipoCompatibleAsig(tipo_var, tipo_expr):
    if tipo_var == 'error' or tipo_expr == 'error':
        return True      # ya se reportó el error, no generar otro
    if tipo_var == tipo_expr:
        return True
    if tipo_var == 'float' and tipo_expr == 'int':
        return True      # coerción implícita
    return False


class EvaluadorTipos:

    #Constructor
    def __init__(self, tabla):
        self.tabla = tabla

    #Va a recibir un nodo del árbol sintáctico para retornar su tipo.
    def evaluar(self, nodo, linea=None):

        #si es None
        if nodo is None:
            return 'void'

        if not isinstance(nodo, tuple):
            #Valor literal directo (no debería ser, pero por si acaso)
            return type(nodo).__name__

        primerElemento = nodo[0]

        #Literales
        if primerElemento == 'int':
            return 'int'
        if primerElemento == 'float':
            return 'float'
        if primerElemento == 'string':
            return 'string'
        if primerElemento == 'boolean':
            return 'boolean'
        
        #input
        if primerElemento == 'input':
            return 'input'

        #Identificador
        if primerElemento == 'id':
            nombre = nodo[1]
            entrada = self.tabla.buscar(nombre) #Buscar si la variable fue declarada
            if entrada is None:
                self.tabla.error(f"'{nombre}' no fue declarado.", linea)
                return 'error'
            return entrada['tipo']

        #Exprepresión aditiva: ('expr', g, eprime)
        if  primerElemento == 'expr':
            aux = self.evaluar(nodo[1], linea)
            if nodo[2] is None:
                return aux
            # eprime: ('+'/'-', g, eprime)
            return self.evaluar_eprime(aux, nodo[2], linea)

        #Término multiplicativo: ('term', h, gprime) ---
        if primerElemento == 'term':
            t_h = self.evaluar(nodo[1], linea)
            if nodo[2] is None:
                return t_h
            return self.evaluar_gprime(t_h, nodo[2], linea)

        #Operaciones aditivas
        if primerElemento in ('+', '-'):
            var1 = self.evaluar(nodo[1], linea)
            var2 = self.evaluar(nodo[2], linea)
            resultado = coercionar(var1, var2)

            if resultado is None:
                self.tabla.error(
                    f"Operación '{primerElemento}' no permitida entre tipos '{var1}' y '{var2}'.", linea)
                return 'error'
            return resultado

        #Operaciones multiplicativas
        if primerElemento in ('*', '/', '%'):
            var1 = self.evaluar(nodo[1], linea)
            var2 = self.evaluar(nodo[2], linea)
            resultado = coercionar(var1, var2)
            if resultado is None:
                self.tabla.error(f"Operación '{primerElemento}' no permitida entre tipos '{var1}' y '{var2}'.", linea)
                return 'error'
            return resultado

        #Llamada a función
        if primerElemento == 'call':
            return self.evaluar_call(nodo, linea)

        #Input siempre retorna string
        if primerElemento == 'input':
            return 'string'

        #Nodo no reconocido — no es error, puede ser void
        return 'void'

    def evaluar_eprime(self, tipo_acum, nodo, linea):
        if nodo is None:
            return tipo_acum
        
        op, g, eprime = nodo
        auxg = self.evaluar(g, linea)
        resultado = coercionar(tipo_acum, auxg)

        if resultado is None:
            self.tabla.error(f"Operación '{op}' no permitida entre tipos '{tipo_acum}' y '{auxg}'.", linea)
            return 'error'
        
        return self.evaluar_eprime(resultado, eprime, linea)

    def evaluar_gprime(self, tipo_acum, nodo, linea):
        if nodo is None:
            return tipo_acum
        
        op, h, gprime = nodo
        auxh = self.evaluar(h, linea)
        resultado = coercionar(tipo_acum, auxh)

        if resultado is None:
            self.tabla.error(f"Operación '{op}' no permitida entre tipos '{tipo_acum}' y '{auxh}'.", linea)
            return 'error'
        
        return self.evaluar_gprime(resultado, gprime, linea)

    def evaluar_call(self, nodo, linea):
        _, nombre, args = nodo
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self.tabla.error(f"Función '{nombre}' no declarada.", linea)
            return 'error'
        
        if not entrada.get('esFuncion'):
            self.tabla.error(f"'{nombre}' no es una función.", linea)
            return 'error'

        #Validar argumentos
        params = entrada.get('params', [])
        args_lista = self.aplanarArgs(args)

        if len(args_lista) != len(params):
            self.tabla.error(
                f"Función '{nombre}' espera {len(params)} argumento(s), "
                f"se pasaron {len(args_lista)}.", linea)
            return entrada.get('tipo', 'void')

        for i, (arg, (tipo_param, tipo_param)) in enumerate(zip(args_lista, params)):
            tipo_arg = self.evaluar(arg, linea)

            if not tipoCompatibleAsig(tipo_param, tipo_arg):
                self.tabla.error(
                    f"Argumento {i+1} de '{nombre}': se esperaba '{tipo_param}', "
                    f"se recibió '{tipo_arg}'.", linea)

        return entrada.get('tipo', 'void')

    #Convierte la lista ecadenada ('arg', e, p) en una lista plana.
    def aplanarArgs(self, nodo):

        resultado = []

        while nodo is not None:
            _, e, p = nodo
            resultado.append(e)
            nodo = p

        return resultado

    #Va a funcionar para validar una condición A -> E F E D.
    def evaluarCondicion(self, nodo_a, linea=None):

        #nodo_a = ('condition', e1, op, e2, d)
        _, e1, op, e2, d = nodo_a
        t1 = self.evaluar(e1, linea)
        t2 = self.evaluar(e2, linea)

        # Comparación entre tipos compatibles
        valida = False
        if t1 == 'error' or t2 == 'error':
            valida = True   # ya se reportó
        elif t1 == t2:
            valida = True
        elif t1 in ARITMETICOS and t2 in ARITMETICOS:
            valida = True   # coerción en comparación
        
        if not valida:
            self.tabla.error(f"Comparación '{op}' no permitida entre tipos '{t1}' y '{t2}'.", linea)

        # Validar conectores lógicos (D)
        if d is not None:
            self.evaluar_d(d, linea)

    #Sirve para validar D -> and/or E F E D.
    def evaluar_d(self, nodo_d, linea):

        if nodo_d is None:
            return
        op, e1, f, e2, d = nodo_d
        t1 = self.evaluar(e1, linea)
        t2 = self.evaluar(e2, linea)

        if t1 != 'error' and t2 != 'error':

            if t1 not in ARITMETICOS and t1 != 'boolean':
                self.tabla.error(f"Operando izquierdo de '{op}' tiene tipo inválido '{t1}'.", linea)

            if t2 not in ARITMETICOS and t2 != 'boolean':
                self.tabla.error(f"Operando derecho de '{op}' tiene tipo inválido '{t2}'.", linea)

        self.evaluar_d(d, linea)
