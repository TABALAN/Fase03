#Tabla de símbolos para utilizar en el analizador semántico directamente.
class Tabla:
    #Constructor
    def __init__(self):
        self.pila = [{}]   #ámbito global siempre en [0]
        self.errores = []
        self.advertencias = []
        self.otroAmbito = []

    #Gestión de ámbitos
    #Se abre un nuevo ámbito cuando se entra a una función o bloque
    def entrarAmbito(self):
        self.pila.append({})

    #Se cierra el ámbito actual en uso
    def salirAmbito(self):
        if len(self.pila) > 1:
            ambitoCerrado = self.pila.pop()
            if ambitoCerrado:
                self.otroAmbito.append(ambitoCerrado)

    #Devuelve el ámbito actual
    def ambitoActual(self):
        return self.pila[-1]


    #Búsqueda y declaración

    #Para buscar sube por la pila de ámbitos buscando el símbolo. Retorna entrado o None.
    def buscar(self, nombre):
        for ambito in reversed(self.pila):
            if nombre in ambito:
                return ambito[nombre]
        return None

    #Busca solo en el ámbito actual (para detectar declaraciones)
    def buscarAmbitoActual(self, nombre):
        return self.ambitoActual().get(nombre, None)

    #Declara una variable en el ámbito actual
    def declarar(self, nombre, entrada, linea=None):
        if nombre in self.ambitoActual(): #Va a retornar False si ya estaba declarado en este ámbito (redeclarar)
            self.error(f"'{nombre}' ya fue declarado en este ámbito.", linea)
            return False
        self.ambitoActual()[nombre] = entrada
        return True

    #Para actualizar el valor de un símbolo ya declarado
    def actualizar(self, nombre, valor, linea=None):
        for ambito in reversed(self.pila): #Recorre desde el interior hacia el ámbito global hasta hallarlo
            if nombre in ambito:
                if ambito[nombre].get('esConst'):
                    self.error(f"No se puede reasignar la constante '{nombre}'.", linea)
                    return False
                ambito[nombre]['valor'] = valor
                return True
        self.error(f"'{nombre}' no fue declarado.", linea)
        return False

    #Reporte de errores

    def error(self, mensaje, linea=None):
        if linea:
            ubicacion = f" (línea {linea})"
        else:
            ubicacion = ""

        self.errores.append(f"[Error semántico]{ubicacion} {mensaje}")
        print(f"[Error semántico]{ubicacion} {mensaje}")

    def advertencia(self, mensaje, linea=None):
        if linea:
            ubicacion = f" (línea {linea})"
        else:
            ubicacion = ""

        self.advertencias.append(f"[Advertencia]{ubicacion} {mensaje}")
        print(f"[Advertencia]{ubicacion} {mensaje}")

    def imprimirTabla(self):
        print("\n--- Tabla de simbolos (ambito actual) ---")
        # Ámbito global (siempre el primero)
        print("  Ámbito global:")
        for nombre, entrada in self.pila[0].items():
            print(f"    {nombre}: {entrada}")
        
        # Ámbitos internos del recorridos
        if self.otroAmbito:
            print("\n  Ambitos internos (funciones/bloques):")
            for i, scope in enumerate(self.otroAmbito):
                print(f"    --- Ambito {i + 1} ---")
                for nombre, entrada in scope.items():
                    print(f"      {nombre}: {entrada}")
        print("----------------------------------------")
