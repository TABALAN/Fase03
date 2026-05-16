# Compilador — Lenguaje .mlng
## Documentación Técnica del Proyecto
Integrantes:
    - Claudia Mejía - 1127224
    - Tony Balán - 1202124

---

## Tabla de Contenidos

1. [Descripción general](#descripción-general)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Gramática formal](#gramática-formal)
4. [Fase 1 — Análisis léxico](#fase-1--análisis-léxico)
5. [Fase 2 — Análisis sintáctico](#fase-2--análisis-sintáctico)
6. [Fase 3 — Análisis semántico](#fase-3--análisis-semántico)
7. [Comportamientos conocidos y limitaciones](#comportamientos-conocidos-y-limitaciones)
8. [Ejecución](#ejecución)

---

## Descripción General

Este proyecto implementa las tres primeras fases de un compilador para
un lenguaje de programación propio con extensión `.mlng`. Las fases
implementadas son: análisis léxico, análisis sintáctico y análisis
semántico.

El compilador reporta errores en cada fase con recuperación de errores,
permitiendo detectar múltiples problemas en una sola pasada sin detenerse
ante el primer error encontrado.

---

## Estructura del Proyecto

```
proyecto/
│
├── main.py                  # Punto de entrada del compilador
├── lector.py                # Clase que permite leer los archivos a procesar
├── lexer.py                 # Analizador léxico
├── adaptadorLexer.py        # Adaptador entre léxico y parser (PLY)
├── parser.py                # Analizador sintáctico (PLY/yacc)
├── TablaSimbolos.py         # Tabla de símbolos con ámbitos anidados
├── Evaluador.py             # Evaluador de tipos de expresiones
├── AnalizadorSemantico.py   # Analizador semántico principal
└── *.mlng                   # Archivos fuente del lenguaje
```

---

## Gramática Formal

Notación: MAYÚSCULAS = tokens terminales, minúsculas = no terminales,
eps = producción vacía.

```

# S' — Raíz del programa

S' -> S S'
    | error ; S'        # Recuperación: sentencia simple mal formada
    | error } S'        # Recuperación: bloque mal formado
    | eps


# S — Sentencias
# -------------------------------------------------
# Diseño pricipal de recuperación:
#   Sentencias de BLOQUE  -> no llevan ';' al final (el '}' las delimita)
#   Sentencias SIMPLES    -> siempre terminan en ';'
# -------------------------------------------------

# Estructuras de bloque
S -> if ( A ) C B
   | while ( A ) C
   | for ( K ; A ; I ) C
   | L
   | X

# Sentencias simples
S -> print ( E ) ;
   | return E ;
   | K ;
   | id ( O ) ;
   | LEXICO_ERROR ;     # Producción que consume errores léxicos
   | error ;            # Recuperación a nivel de sentencia
   | error C            # Recuperación a nivel de bloque


# C — Bloque de código (Para 'if' y bucles)

C -> { S' }


# B — Rama condicional else / elif

B -> elif ( A ) C B
   | else C
   | eps

# A — Condición

A -> E F E D

# D — Conectores lógicos (Para condiciones de 'if' y bucles)

D -> and E F E D
   | or  E F E D
   | eps

# F — Operadores de comparación

F -> == | != | <= | >= | < | >

# E / E' — Expresiones aditivas

E  -> G E'

E' -> + G E'
    | - G E'
    | eps

# G / G' — Expresiones multiplicativas

G  -> H G'

G' -> * H G'
    | / H G'
    | % H G'
    | eps

# H — Datos directos (símbolos terminales)

H -> ( E )
   | id ( O )
   | id
   | num
   | decimal
   | string
   | True
   | False
   | input ( string )

# I — Actualizaciones (exclusivo para el for)

I -> id =  E
   | id ++
   | id --
   | id += E
   | id -= E

# J — Tipos de dato (void incluido para funciones)

J -> int | float | boolean | void | string

# K — Asignación / Declaración / Incremento

K -> id = E
   | J id = E
   | const J id = E
   | id ++
   | id --
   | id += E
   | id -= E

# L — Definición de función

L -> def J id ( M ) C

# M / N — Parámetros formales

M -> J id N | eps

N -> , J id N | eps

# O / P — Argumentos en llamada a función

O -> E P | eps

P -> , E P | eps

# X — Definición de clase

X -> class id { S' }
```

---

## Fase 1 — Análisis Léxico

### Descripción

El analizador léxico lee el archivo fuente carácter a carácter y produce
una lista de tokens. Cada token es un diccionario con los campos:
lexema, tipo, línea, columna e identación.

### Tipos de tokens reconocidos

| Tipo     | Descripción                          | Ejemplos                        |
|----------|--------------------------------------|---------------------------------|
| key      | Palabras reservadas                  | if, while, int, def, const      |
| id       | Identificadores                      | x, contador, miVariable         |
| num      | Enteros                              | 0, 42, 100                      |
| decimal  | Flotantes                            | 3.14, 0.5                       |
| txt      | Cadenas de texto                     | "hola", "mundo"                 |
| op       | Operadores aritméticos               | +, -, *, /                      |
| comp     | Operadores de comparación            | ==, !=, <=, >=, ++, +=          |
| esp      | Caracteres especiales                | (, ), {, }, =, !                |
| punt     | Puntuación                           | ,, :, ;                         |
| ERROR    | Token inválido (error léxico)        | @, tildes, cadenas sin cerrar   |

### Palabras reservadas

```
int, float, boolean, void, string, if, elif, else, while, for,
return, and, or, not, switch, do, default, case, try, catch,
main, print, input, def, const, True, False, class, read
```

### Decisiones técnicas

**Booleanos con mayúscula inicial:** Los valores booleanos se escriben
`True` y `False` (con mayúscula inicial, como en Python). En minúscula
(`true`, `false`) son tratados como identificadores válidos, no como
booleanos. Esta distinción es intencional y por diseño del lenguaje.

**Saltos de línea no tokenizados:** Inicialmente el lexer tokenizaba
los saltos de línea (`\n`). Se decidió eliminarlos del flujo de tokens
porque el lenguaje usa llaves `{}` para delimitar bloques, haciendo los
saltos de línea irrelevantes para el parser. Esto simplificó
significativamente la gramática.

**Adaptador léxico:** Se implementó una clase `adaptadorL` que actúa
como puente entre la lista de tokens del lexer y la interfaz que PLY
requiere. El adaptador:
- Filtra tokens de INDENT, DEDENT y NEWLINE
- Convierte diccionarios de tokens en objetos con atributos `.type`,
  `.value`, `.lineno`, `.lexpos`
- Inyecta automáticamente un `;` cuando un LEXICO_ERROR no va seguido
  de punto y coma, para facilitar la recuperación sintáctica

---

## Fase 2 — Análisis Sintáctico

### Descripción

El parser es LALR(1) generado con PLY/yacc. Recibe la lista de tokens
del adaptador y construye un AST (árbol sintáctico abstracto) compuesto
por tuplas anidadas de Python.

### Estructura del AST

Cada nodo del AST es una tupla donde el primer elemento es el tipo de
nodo:

```python
('decl',   'int', 'x', expr)          # int x = 5;
('assign', 'x', expr)                 # x = 5;
('const',  'int', 'MAX', expr)        # const int MAX = 100;
('if',     condicion, bloque, rama)   # if(...){}
('while',  condicion, bloque)         # while(...){}
('for',    k_init, cond, update, c)   # for(...){}
('def',    tipo, nombre, params, c)   # def int f(int x){}
('call',   nombre, args)              # f(x, y)
('print',  expr)                      # print(x)
('return', expr)                      # return x
('class',  nombre, sprime)            # class Program{}
```

### Recuperación de errores

El parser implementa cuatro niveles de recuperación, del más específico
al más general:

**Nivel 1 — Sentencia simple inválida:**
```
s : error SEMI
```
Para errores como `int x = + 5;`. Descarta hasta el `;` sin afectar
el bloque padre.

**Nivel 2 — Bloque inválido:**
```
s : error C
```
Para errores como `while() { ... }`. Descarta la estructura completa
incluyendo su bloque, sin consumir el `}` del bloque padre. Esta regla
fue clave para evitar el colapso en cascada de bloques anidados.

**Nivel 3 — Lista de sentencias con SEMI:**
```
sprime : error SEMI sprime
```
Respaldo cuando los niveles 1 y 2 no pueden recuperarse.

**Nivel 4 — Lista de sentencias con RBRACE:**
```
sprime : error RBRACE sprime
```
Para bloques sin cierre. Consume el `}` como punto de sincronización.

### Decisión técnica: SEMI como terminador

Las sentencias simples terminan en `;` como en C/Java. Las sentencias
de bloque (if, while, for, def) NO llevan `;` porque el `}` ya las
delimita. Esta decisión permite usar `;` como punto de sincronización
confiable para la recuperación de errores.

### Mensajes del parser

Los mensajes de recuperación pueden aparecer en orden inverso al
cronológico. Esto es normal en parsers LALR(1): los errores se apilan
y se desapilan en orden LIFO. Ver sección de comportamientos conocidos.

---

## Fase 3 — Análisis Semántico

### Descripción general

El analizador semántico recorre el AST producido por el parser en un
recorrido en profundidad. En otras palabras, se realiza un análisis semántico 
después del análisis sintáctico. Valida tipos, ámbitos, uso de
constantes, parámetros de funciones y retornos.

Está compuesto por tres módulos:

- **TablaSimbolos.py** — Gestiona la pila de ámbitos y el registro
  de símbolos.
- **Evaluador.py** — Determina el tipo resultante de cualquier
  expresión del AST.
- **AnalizadorSemantico.py** — Orquesta el recorrido del AST y
  despacha cada tipo de nodo al validador correspondiente.

---

### Tabla de Símbolos

#### Estructura

La tabla de símbolos es una **pila de diccionarios**. Cada diccionario
representa un ámbito (scope). El ámbito global siempre está en la
posición 0 de la pila.

```
pila = [
    { 'x': {tipo:'int', valor:5, esConst:False, esFuncion:False} },  ← global
    { 'n': {tipo:'int', valor:None, esConst:False, esFuncion:False} } ← función
]
```

#### Entrada de variable o constante

```python
{
    'tipo'     : 'int' | 'float' | 'boolean' | 'string' | 'void' | 'error',
    'valor'    : valor Python o None,
    'esConst'  : True | False,
    'esFuncion': False
}
```

#### Entrada de función

```python
{
    'tipo'     : tipo de retorno declarado,
    'esFuncion': True,
    'params'   : [('nombre_param', 'tipo_param'), ...],
    'esConst'  : False
}
```

#### Entrada de clase

```python
{
    'tipo'    : 'class',
    'esClase' : True,
    'esFuncion': False,
    'esConst' : False
}
```

### Vista general de la tabla de símbolos

```
	Pila de ámbitos. Cada ámbito es un diccionario:
        nombre -> { 'tipo', 'valor', 'esConst', 'esFuncion', 'params' }

    Estructura de una entrada de variable/constante:
        {
            'tipo'     : 'int' | 'float' | 'boolean' | 'string' | 'error',
            'valor'    : valor Python o None si no se conoce en compilación,
            'esConst'  : True | False,
            'esFuncion': False
        }

    Estructura de una entrada de función:
        {
            'tipo'     : tipo de retorno o 'void' si no retorna,
            'esFuncion': True,
            'params'   : [ ('nombre', 'tipo'), ... ]
        }
```
#### Gestión de ámbitos

Al entrar a una función, bloque if, while o for, se llama
`entrarAmbito()` que apila un nuevo diccionario vacío. Al salir, se
llama `salirAmbito()` que desapila el diccionario y lo guarda en el
historial para su visualización posterior.

La búsqueda de un símbolo sube por la pila desde el ámbito más interno
hasta el global:

```python
def buscar(self, nombre):
    for ambito in reversed(self.pila):
        if nombre in ambito:
            return ambito[nombre]
    return None
```

Esto implementa el comportamiento estándar de **lexical scoping**:
una variable interna puede ocultar (shadowing) una variable externa
del mismo nombre sin generar error.

#### Valores en tiempo de compilación

La tabla almacena el valor de variables cuando es posible evaluarlo
en tiempo de compilación. Solo funciona para literales simples:

```
int x = 5;          → valor: 5         (evaluado)
float y = 3.14;     → valor: 3.14      (evaluado)
boolean b = True;   → valor: True      (evaluado)
int z = x + 3;      → valor: None      (expresión compleja, no evaluada)
```

Los parámetros de funciones siempre tienen `valor: None` porque su
valor real se conoce solo en tiempo de ejecución.

---

### Sistema de Tipos

#### Tipos del lenguaje

| Tipo      | Descripción                    | Literales válidos       |
|-----------|--------------------------------|-------------------------|
| int       | Entero                         | 0, 42, -1               |
| float     | Flotante                       | 3.14, 0.5, 2.0          |
| boolean   | Booleano                       | True, False             |
| string    | Cadena de texto                | "hola", "mundo"         |
| void      | Sin valor de retorno           | (solo en funciones)     |

#### Coerción de tipos

El compilador implementa coerción implícita únicamente de `int`
hacia `float`. No se permite la dirección inversa porque implica
pérdida de precisión.

| Situación                  | Resultado  | Ejemplo                      |
|----------------------------|------------|------------------------------|
| `float = int`              | válido     | `float x = 10;`              |
| `int = float`              | error      | `int x = 3.14;`              |
| `int + float`              | float      | `3 + 2.5` → tipo float       |
| `float + int`              | float      | `2.5 + 3` → tipo float       |
| `int + int`                | int        | `3 + 4` → tipo int           |
| `float + float`            | float      | `2.5 + 1.5` → tipo float     |
| `float retorna int`        | válido     | `def float f(){ return 5; }` |
| `int retorna float`        | error      | `def int f(){ return 3.14; }`|
| Comparación `int == float` | válido     | resultado boolean            |
| Argumento `int` -> `float` | válido     | coerción en paso de params   |

#### Operaciones aritméticas

Los operadores `+`, `-`, `*`, `/`, `%` solo están permitidos entre
tipos numéricos (int y float). Operar con boolean o string genera
error semántico.

| Operandos         | Resultado | Válido |
|-------------------|-----------|--------|
| int op int        | int       | Sí     |
| int op float      | float     | Sí     |
| float op float    | float     | Sí     |
| boolean op *      | —         | No     |
| string op *       | —         | No     |

#### Operadores lógicos

`and` y `or` operan exclusivamente entre expresiones de tipo boolean.
No están permitidos entre tipos numéricos.

| Operandos              | Resultado | Válido |
|------------------------|-----------|--------|
| boolean and/or boolean | boolean   | Sí     |
| int and/or int         | —         | No     |
| * and/or *             | —         | No     |

#### Comparaciones

| Comparación          | Resultado |       Válido      |
|----------------------|-----------|-------------------|
| int cmp int          | boolean   |        Sí         |
| int cmp float        | boolean   |   Sí (coerción)   |
| float cmp float      | boolean   |        Sí         |
| boolean cmp boolean  | boolean   | Sí (solo == y !=) |
| string cmp string    | boolean   | Sí (solo == y !=) |
| int cmp boolean      | —         |        No         |
| string cmp int       | —         |        No         |

---

### Errores y Advertencias Semánticas

#### Errores semánticos (bloquean la validez del programa)

| Caso | Mensaje |
|------|---------|
| Variable no declarada | `'x' no fue declarado.` |
| Redeclaración en mismo ámbito | `'x' ya fue declarado en este ámbito.` |
| Tipo incompatible en declaración | `No se puede asignar tipo 'float' a variable 'x' de tipo 'int'.` |
| Tipo incompatible en asignación | `No se puede asignar tipo 'string' a 'x' de tipo 'int'.` |
| Reasignación de constante | `No se puede reasignar la constante 'MAX'.` |
| Modificación de constante (++/--) | `No se puede modificar la constante 'MAX'.` |
| Operación aritmética inválida | `Operación '+' no permitida entre tipos 'boolean' y 'int'.` |
| Comparación inválida | `Comparación '==' no permitida entre tipos 'string' y 'int'.` |
| ++ sobre no numérico | `'++' no aplicable a tipo 'boolean'.` |
| += inválido | `'+=' no permitido entre 'int' y 'string'.` |
| Función no declarada | `Función 'f' no declarada.` |
| Llamar a no-función | `'x' no es una función.` |
| Argumentos incorrectos (cantidad) | `Función 'f' espera 2 argumento(s), se pasaron 1.` |
| Argumentos incorrectos (tipo) | `Argumento 1 de 'f': se esperaba 'int', se recibió 'string'.` |
| Retorno con tipo incorrecto | `'return' retorna 'string', pero la función espera 'int'.` |

#### Advertencias semánticas (informativas, no bloquean)

| Caso | Mensaje |
|------|---------|
| Función void retorna valor | `Función void no puede retornar valor.` |
| Función no-void sin return | `Función 'f' declarada para retornar int, pero no tiene return.` |
| Return fuera de función | `'return' fuera de una función.` |

#### Recuperación de errores semánticos

Cuando el evaluador de tipos no puede determinar el tipo de una
expresión (por un error previo), retorna el tipo especial `'error'`.
Las validaciones posteriores que involucren ese tipo lo ignoran
silenciosamente, evitando que un solo error genere decenas de errores
en cascada.

```python
def tipoCompatibleAsig(tipo_var, tipo_expr):
    if tipo_var == 'error' or tipo_expr == 'error':
        return True   # ya se reportó, no generar otro
    ...
```

---

### Validación de Funciones

#### Declaración

Las funciones se declaran con tipo de retorno explícito:
```
def int sumar(int a, int b) { return a + b; }
def void saludar() { print("hola"); }
```

La función se registra en la tabla de símbolos antes de analizar
su cuerpo, lo que permite recursión directa:
```
def int factorial(int n) {
    if(n == 0) { return 1; }
    else { return n * factorial(n - 1); }  ← válido: factorial ya está registrada
}
```

#### Parámetros

Los parámetros se declaran con tipo explícito y se registran en el
ámbito local de la función:
```
def float promedio(int a, int b) { ... }
```

Al llamar la función, se valida que el número de argumentos coincida
y que cada argumento sea compatible con el tipo del parámetro
correspondiente (aplicando coerción int a float cuando corresponde).

#### Retorno

El tipo de retorno declarado se valida contra el tipo de la expresión
del `return`. Se permite coerción int→float.

Si la función declara un tipo de retorno distinto de `void` y no se
encuentra ningún `return` en el bloque, se genera una advertencia.

---
### input
Se incluyó que el `input` sea compatible con cualquier asignación primitiva. En otras, 
palabras se asume que es responsabilidad del programador que el input sea coherente 
con el tipo declarado.

---
### Constantes

Las constantes se declaran con `const J id = E`:
```
const int MAX = 100;
const float PI = 3.14159;
const boolean DEBUG = True;
```

El compilador detecta y reporta como error semántico cualquier intento
de modificar una constante:
- Reasignación directa: `MAX = 200;`
- Incremento: `MAX++;` o `MAX--;`
- Operadores compuestos: `MAX += 5;` o `MAX -= 3;`

---

### Ámbitos

#### Reglas de ámbito

- Las variables declaradas dentro de una función, bloque if, while o
  for solo son visibles dentro de ese bloque.
- Una variable interna puede tener el mismo nombre que una externa
  (shadowing) sin generar error. La interna tiene prioridad dentro
  de su ámbito.
- Las variables globales son visibles desde cualquier función o bloque.

#### Ejemplo de shadowing válido

```
int valor = 1;       ← global
if(x > 0) {
    int valor = 2;   ← local, oculta la global dentro del bloque
    print(valor);    ← imprime 2
}
print(valor);        ← imprime 1 (la global)
```

#### Variables de control del for

La variable declarada en la inicialización del `for` pertenece al
ámbito del for y no es visible fuera de él:
```
for(int i = 0; i < 10; i++) { ... }
print(i);   ← Error semántico: 'i' no fue declarado
```

---

### Clases

El compilador reconoce la declaración de clases como estructura de
bloque:
```
class NombreClase {
    ...variables y funciones...
}
```

La clase se registra en la tabla de símbolos global con tipo `'class'`.
El contenido del bloque se analiza semánticamente de forma normal.
**Nota:** la validación semántica avanzada de clases (herencia, métodos,
instanciación) está fuera del alcance de este proyecto.

---

## Comportamientos Conocidos y Limitaciones

### Errores en cadena por fallo sintáctico

Cuando una declaración falla sintácticamente, la variable no entra al
AST. Si se usa después, el semántico la reporta como no declarada,
generando un error semántico que es consecuencia del error sintáctico
original, no un error independiente.

```
int z = + 5;    ← Error sintáctico
print(z);       ← Error semántico en cadena: 'z' no fue declarado
```

Este es el comportamiento estándar de compiladores LALR(1).

### Orden invertido en mensajes de recuperación

Los mensajes de "Se descartó una sentencia inválida" pueden aparecer
en orden inverso al cronológico. Esto ocurre porque el parser LALR(1)
desapila en orden LIFO al recuperarse. Es cosmético y no indica ningún
problema funcional.

### El semántico analiza el AST aunque haya errores sintácticos

Por decisión de diseño, el análisis semántico se ejecuta siempre que
el parser produzca algún AST, aunque haya errores sintácticos. Esto
maximiza la información reportada en una sola pasada, a costa de
posibles errores en cadena adicionales.

### Verificación de return superficial

La verificación de que una función no-void tenga `return` es
superficial: busca un `return` directo en el bloque o dentro de un
`if` inmediato. No analiza todos los caminos de ejecución posibles.
Puede generar advertencias falsas cuando el `return` está dentro de
un `while` o `for`.

### Valores en tiempo de compilación solo para literales

La tabla de símbolos almacena valores solo para literales simples.
Expresiones como `x + 3` se almacenan como `None`. Esto es informativo
y no afecta la validación de tipos.

### Parámetros sin tipo en versiones anteriores

La gramática actual exige tipo explícito en los parámetros formales
(`def int f(int a, float b)`). Versiones anteriores no requerían tipo
en parámetros, lo que impedía la validación de argumentos en llamadas.

---

## Ejecución

### Requisitos

- Python 3.8 o superior
- PLY (Python Lex-Yacc): `pip install ply`
- **Nota:** Se recomienda crear un entorno virtual para realizar la instalación.

### Uso

Escribir directamente sobre el main el nombre del archivo a analizar.
**Nota:** Los archivos deben de estar dentro de la carpeta. 

### Formato de salida

```
------- Analizador Léxico -------
[lista de tokens]

------- Analizador Sintáctico -------
[errores sintácticos si los hay]

------- Analizador Semántico -------
[errores y advertencias semánticas]

--- Tabla de Símbolos ---
  Ámbito global:
    [símbolos globales]
  Ámbitos internos:
    [símbolos de funciones y bloques]

--- Reporte ---
Errores semánticos: N
Advertencias: N
```

### Códigos de salida implícitos

El compilador no termina con error de sistema ante errores en el
código fuente. Todos los errores se reportan como mensajes en consola
y el análisis continúa hasta donde sea posible.
