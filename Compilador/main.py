#Instancias
from lexer import Lexer
from parser import parserin
from AnalizadorSemantico import AnalizadorSemantico

def main():
    #Etapa 1: Analizador Léxico
    archivo = "Prueba3.mlng"
    print("------- Analizador Lexico -------")
    lec = Lexer()
    lec.leerArchivo(archivo)
    lec.imprimirTokens()
    
    #Etapa 2: Parserin
    print("\n\n------- Analizador sintactico -------")
    parser = parserin()

    #Ejecutar parserin
    raiz = parser.analizar(lec.getTokens())

    #Etapa 3: Análisis semántico
    if raiz is not None:
        print("\n\n------- Analizador Semantico -------")
        semantico = AnalizadorSemantico()
        errores = semantico.analizar(raiz)

        #Tabla de símbolos
        semantico.tabla.imprimirTabla()

        #Reporte
        print(f"\n--- Reporte ---")
        print(f"Errores semánticos: {len(errores)}")
        print(f"Advertencias: {len(semantico.tabla.advertencias)}")

        if not errores and not semantico.tabla.advertencias:
            print("Análisis semántico completado sin errores.")

    else:
        print("\n\n------- Analizador Semantico -------")
        print("El parser no produjo un arbol sintactico. No se realiza analisis semantico")


if __name__ == "__main__":
    main() 