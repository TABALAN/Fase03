from TablaSimbolos import Tabla
from Evaluador import EvaluadorTipos

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
    if tipo_expr == 'input':
        return tipo_var in {'int', 'float', 'boolean', 'string'}
    return False

#Orquestador principal entre la tabla de símbolos y el evaluador
class AnalizadorSemantico:

    def __init__(self):
        self.tabla = Tabla()
        self.evaluador = EvaluadorTipos(self.tabla)
        self.tipoRetornoAct = None   #tipo de retorno de la función actual

    #Va a ser el punto de entrada que recibe la raíz del árbol sintáctico (sprime)
    def analizar(self, ast):
        self.recorrer_sprime(ast)
        return self.tabla.errores

    #Recorrido de listas de sentencias

    def recorrer_sprime(self, nodo):
        if nodo is None:
            return
        if not isinstance(nodo, tuple):
            return
        
        primerElemento = nodo[0]
        if primerElemento == 'sprime':
            self.recorrer_s(nodo[1])
            self.recorrer_sprime(nodo[2])

    #Entrea cada tipo de sentencia
    def recorrer_s(self, nodo):
        if nodo is None:
            return
        primerElemento = nodo[0]

        if primerElemento == 'decl':
            self.s_decl(nodo)
        elif primerElemento == 'class':
            self.s_class(nodo)
        elif primerElemento == 'const':
            self.s_const(nodo)
        elif primerElemento == 'assign':
            self.s_assign(nodo)
        elif primerElemento == 'inc':
            self.s_inc(nodo)
        elif primerElemento == 'dec':
            self.s_dec(nodo)
        elif primerElemento == 'pluseq':
            self.s_pluseq(nodo)
        elif primerElemento == 'minuseq':
            self.s_minuseq(nodo)
        elif primerElemento == 'print':
            self.s_print(nodo)
        elif primerElemento == 'return':
            self.s_return(nodo)
        elif primerElemento == 'if':
            self.s_if(nodo)
        elif primerElemento == 'while':
            self.s_while(nodo)
        elif primerElemento == 'for':
            self.s_for(nodo)
        elif primerElemento == 'def':
            self.s_def(nodo)
        elif primerElemento == 'call':
            self.evaluador.evaluar_call(nodo, None)
        #primerElemento == None o desconocido: recuperación silenciosa

    #Sentencias/Producciones

    #Declaración de una variable
    def s_decl(self, nodo):
        # ('decl', tipo_j, nombre_id, expr)
        _, tipo, nombre, expr = nodo
        tipo_expr = self.evaluador.evaluar(expr)

        if not tipoCompatibleAsig(tipo, tipo_expr):
            self.tabla.error(f"No se puede asignar tipo '{tipo_expr}' a variable '{nombre}' de tipo '{tipo}'.")

        valor = self.evaluarValor(expr)
        self.tabla.declarar(nombre, {
            'tipo': tipo, 'valor': valor, 'esConst': False, 'esFuncion': False
        })

    #Declarar una constante
    def s_const(self, nodo):
        # ('const', tipo_j, nombre_id, expr)
        _, tipo, nombre, expr = nodo
        tipo_expr = self.evaluador.evaluar(expr)

        if not tipoCompatibleAsig(tipo, tipo_expr):
            self.tabla.error(f"No se puede asignar tipo '{tipo_expr}' a constante '{nombre}' de tipo '{tipo}'.")

        valor = self.evaluarValor(expr)
        self.tabla.declarar(nombre, {
            'tipo': tipo, 'valor': valor, 'esConst': True, 'esFuncion': False
        })
    
    #Asignación normal
    def s_assign(self, nodo):
        # ('assign', nombre_id, expr)
        _, nombre, expr = nodo
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self.tabla.error(f"'{nombre}' no fue declarado.")
            return
        if entrada.get('esConst'):
            self.tabla.error(f"No se puede reasignar la constante '{nombre}'.")
            return

        tipoExpr = self.evaluador.evaluar(expr)

        if not tipoCompatibleAsig(entrada['tipo'], tipoExpr):
            self.tabla.error(f"No se puede asignar tipo '{tipoExpr}' a '{nombre}' de tipo '{entrada['tipo']}'.")
            return

        valor = self.evaluarValor(expr)
        self.tabla.actualizar(nombre, valor)

    #Aplicación de incremento a una variable. Se puede aplicar a int o float (ARITMETICOS)
    def s_inc(self, nodo):
        # ('inc', nombre)
        _, nombre = nodo
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self.tabla.error(f"'{nombre}' no fue declarado.")
            return
        
        if entrada.get('esConst'):
            self.tabla.error(f"No se puede modificar la constante '{nombre}'.")
            return
        
        if entrada['tipo'] not in ARITMETICOS:
            self.tabla.error(f"'++' no aplicable a tipo '{entrada['tipo']}'.")

    #Caso contrario. Aplicación de decremento.
    def s_dec(self, nodo):
        _, nombre = nodo
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self.tabla.error(f"'{nombre}' no fue declarado.")
            return
        
        if entrada.get('esConst'):
            self.tabla.error(f"No se puede modificar la constante '{nombre}'.")
            return
        
        if entrada['tipo'] not in ARITMETICOS:
            self.tabla.error(f"'--' no aplicable a tipo '{entrada['tipo']}'.")

    #Validación de +=.
    def s_pluseq(self, nodo):
        # ('pluseq', nombre, expr)
        _, nombre, expr = nodo
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self.tabla.error(f"'{nombre}' no fue declarado.")
            return
        
        if entrada.get('esConst'):
            self.tabla.error(f"No se puede modificar la constante '{nombre}'.")
            return
        
        #Obtener el tipo de expresión y realizar verificación por coerción
        tipoExpr = self.evaluador.evaluar(expr)
        resultado = coercionar(entrada['tipo'], tipoExpr)

        if resultado is None:
            self.tabla.error(f"'+=' no permitido entre '{entrada['tipo']}' y '{tipoExpr}'.")

    #Validación de -=
    def s_minuseq(self, nodo):
        _, nombre, expr = nodo
        entrada = self.tabla.buscar(nombre)

        if entrada is None:
            self.tabla.error(f"'{nombre}' no fue declarado.")
            return
        
        if entrada.get('esConst'):
            self.tabla.error(f"No se puede modificar la constante '{nombre}'.")
            return
        
        #Obtener el tipo de expresión y realizar verificación por coerción
        tipo_expr = self.evaluador.evaluar(expr)
        resultado = coercionar(entrada['tipo'], tipo_expr)

        if resultado is None:
            self.tabla.error(f"'-=' no permitido entre '{entrada['tipo']}' y '{tipo_expr}'.")

    def s_print(self, nodo):
        # ('print', expr) — cualquier tipo es imprimible, solo validamos que exista
        _, expr = nodo
        self.evaluador.evaluar(expr)

    #Corrobar que el return devuelva correctamente
    def s_return(self, nodo):
        _, expr = nodo
        tipo_expr = self.evaluador.evaluar(expr)

        if self.tipoRetornoAct is None:
            self.tabla.advertencia("'return' fuera de una función.")
            return
        
        if self.tipoRetornoAct == 'void':
            self.tabla.advertencia("Funcion void no puede retornar valor.")
            return
        
        if not tipoCompatibleAsig(self.tipoRetornoAct, tipo_expr):
            self.tabla.error(f"'return' retorna '{tipo_expr}', pero la función espera '{self.tipoRetornoAct}'.")

    #Condición 'if'. Se evalúa que la condición esté correcta y 
    def s_if(self, nodo):
        # ('if', condicion_a, bloque_c, rama_b)
        _, condicion, bloque, rama = nodo

        self.evaluador.evaluarCondicion(condicion)
        self.recorrerBloque(bloque)
        self.recorrer_b(rama)

    #Bucle 'while'. Se evalúa que la condición esté correcta y
    def s_while(self, nodo):
        _, condicion, bloque = nodo

        self.evaluador.evaluarCondicion(condicion)
        self.recorrerBloque(bloque)

    #Bucle 'for'.
    def s_for(self, nodo):
        # ('for', k_init, condicion_a, i_update, bloque_c)
        _, k_init, condicion, i_update, bloque = nodo

        self.tabla.entrarAmbito()

        self.recorrer_s(k_init)
        self.evaluador.evaluarCondicion(condicion)
        self.recorrer_s(i_update)
        self.recorrerBSAmbito(bloque)  # el ámbito ya está abierto
        self.tabla.salirAmbito()


    #Definción de funciones
    def s_def(self, nodo):
        # ('def', tipoRetorno, nombre, params_m, bloque_c)
        _, tipoRetorno, nombre, params, bloque = nodo

        #Aplanar parámetros
        paramLista = self.aplanarParam(params)

        # Registrar la función en el ámbito actual antes de entrar al ambito
        # (permite recursión)
        self.tabla.declarar(nombre, {
            'tipo': tipoRetorno,  
            'esFuncion': True,
            'params': paramLista,
            'esConst': False
        })

        # Entrar al ámbito de la función
        self.tabla.entrarAmbito()
        tipoRetornoAnt = self.tipoRetornoAct
        self.tipoRetornoAct = tipoRetorno 

        # Declarar parámetros en el ámbito local
        for nombre_param, tipo_param in paramLista:
            self.tabla.declarar(nombre_param, {
                'tipo': tipo_param, 'valor': None,
                'esConst': False, 'esFuncion': False
            })

        self.recorrerBSAmbito(bloque)

        #Verificar que haya al menos un return si el tipo no es void 
        if tipoRetorno != 'void' and not self.bloqueTieneReturn(bloque):
            self.tabla.advertencia(f"Funcion '{nombre}' declarada para retornar {tipoRetorno}, pero no tiene return.")

        self.tipoRetornoAct = tipoRetornoAnt
        self.tabla.salirAmbito()

    #Rama de producción B (elif/else)
    def recorrer_b(self, nodo):

        if nodo is None:
            return
        primerElemento = nodo[0]

        if primerElemento == 'elif':

            _, condicion, bloque, siguiente = nodo
            self.evaluador.evaluarCondicion(condicion)
            self.recorrerBloque(bloque)
            self.recorrer_b(siguiente)

        elif primerElemento == 'else':
            _, bloque = nodo
            self.recorrerBloque(bloque)

    #Bloques de código

    #Abre ámbito, recorre las producciones y cierra
    def recorrerBloque(self, nodo):
        
        self.tabla.entrarAmbito()

        if nodo and nodo[0] == 'block':
            self.recorrer_sprime(nodo[1])

        self.tabla.salirAmbito()

    #Recorre un bloque sin abrir ámbito (tendría que haber sido llamado)
    def recorrerBSAmbito(self, nodo):

        if nodo and nodo[0] == 'block':
            self.recorrer_sprime(nodo[1])

    #Método para revisar la declaración de clases
    def s_class(self, nodo):
        _, nombre, cuerpo = nodo

        self.tabla.declarar(nombre, {
            'tipo': 'class',
            'esFuncion': False,
            'esConst': False,
            'esClase': True
        })
         
        #Debería entrar al ámbito de la función
        self.tabla.entrarAmbito()
        self.recorrer_sprime(cuerpo)
        self.tabla.salirAmbito()

    #Otras funciones útiles para el análisis

    #va a convertir ('param', nombre, siguiente) en lista de (nombre, tipo).
    def aplanarParam(self, nodo):
        resultado = []
        while nodo is not None:
            _, nombre, tipo, siguiente = nodo
            resultado.append((nombre, tipo))
            nodo = siguiente
        return resultado
    
    #Para revisión superficial, se ve que el bloque tenga al menos un return
    def bloqueTieneReturn(self, bloque):
        if bloque is None or bloque[0] != 'block':
            return False
        return self.sprimeTieneReturn(bloque[1])


    def sprimeTieneReturn(self, nodo):
        if nodo is None:
            return False
        
        if not isinstance(nodo, tuple) or nodo[0] != 'sprime':
            return False
        s = nodo[1]

        if isinstance(s, tuple) and s[0] == 'return':
            return True
        
        # Buscar en if/elif/else también
        if isinstance(s, tuple) and s[0] == 'if':

            if self.bloqueTieneReturn(s[2]):
                return True
            
        return self.sprimeTieneReturn(nodo[2])


    #Para evaluar el valor en tiempo de ejecución. Solo funciona con literales simples. Cualquier cosa devuelve None
    def evaluarValor(self, nodo):

        if not isinstance(nodo, tuple):
            return None
        primerElemento = nodo[0]

        if primerElemento == 'int':
            return int(nodo[1])
        if primerElemento == 'float':
            return float(nodo[1])
        if primerElemento == 'string':
            return str(nodo[1])
        if primerElemento == 'boolean':
            return bool(nodo[1])
        if primerElemento == 'expr':
            # Solo evalúa si eprime es None (expresión simple sin operadores)
            if nodo[2] is None:
                return self.evaluarValor(nodo[1])
        if primerElemento == 'term':
            if nodo[2] is None:
                return self.evaluarValor(nodo[1])
        return None   # expresión compleja, valor desconocido en compilación