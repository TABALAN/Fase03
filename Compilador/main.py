#Instancias
from lexer import Lexer
from adaptadorLexer import adaptadorL
from parser import parserin

def main():
    #Etapa 1: Analizador Léxico
    archivo = "text1.mlng"
    print("------- Analizador Lexico -------")
    lec = Lexer()
    lec.leerArchivo(archivo)
    lec.imprimirTokens()
    
    #Etapa 2: Parserin
    print("\n\n------- Analizador sintactico -------")
    parser = parserin()

    #Ejecutar parserin
    resultado = parser.analizar(lec.getTokens())

if __name__ == "__main__":
    main() 