#Destinado a leer el archivo de entrada y pararlo al lexer
import os

class Lector:
    def __init__(self, fileN):
        self.fileName = fileN
        self.lineasArchivo = None

    def readFile(self):
        try:
            with open(self.fileName, "r") as archivo:
                self.lineasArchivo = archivo.read() 
            return self.lineasArchivo
        except:
            print("Archivo no encontrado. Verifique que este en la direccion correcta.")
            return None