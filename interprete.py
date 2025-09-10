# FuncLang Interprete
# Parcial del Primer Corte de teoria de los compiladores - Parte 2

# = Parte 1 de requerimientos: ANÁLISIS LÉXICO =
def analisis_lexico(codigo):
    """
    Convierte el código en una lista de tokens (palabras importantes)
    Ejemplo: "func suma(a,b)" -> ["func", "suma", "(", "a", ",", "b", ")"]
    """
    tokens = []
    i = 0
    linea = 1
    
    while i < len(codigo):
        char = codigo[i]
        
        # Saltar los espacios y los salto de línea
        if char.isspace():
            if char == '\n':
                linea += 1
            i += 1
            continue
        
        # Leer números (123, 30.67)
        if char.isdigit():
            numero = ""
            while i < len(codigo) and (codigo[i].isdigit() or codigo[i] == '.'):
                numero += codigo[i]
                i += 1
            tokens.append(("NUMBER", numero, linea))
            continue
        
        # Leer los identificadores y las palabras claves defindas como suma, func, print, etc.
        if char.isalpha():
            palabra = ""
            while i < len(codigo) and (codigo[i].isalnum() or codigo[i] == '_'):
                palabra += codigo[i]
                i += 1
            
            # Verificar si es o no unas de las palabras claves
            if palabra == "func":
                tokens.append(("FUNC", palabra, linea))
            elif palabra == "print":
                tokens.append(("PRINT", palabra, linea))
            else:
                tokens.append(("ID", palabra, linea))
            continue
        
        # Operadores y símbolos
        simbolos = {
            '+': 'PLUS', '-': 'MINUS', '*': 'MULT', '/': 'DIV', '^': 'POW',
            '(': 'LPAREN', ')': 'RPAREN', ',': 'COMMA', ';': 'SEMICOLON', '=': 'EQUALS'
        }
        
        if char in simbolos:
            tokens.append((simbolos[char], char, linea))
            i += 1
        else:
            # Reporte de ERROR en caso de encontrarrse un Símbolo desconocido
            print(f"ERROR LÉXICO: Símbolo desconocido '{char}' en línea {linea}")
            return None
    
    return tokens

# =Parte 2 de requerimientos:  ANÁLISIS SINTÁCTICO =
 # Validar gramática del lenguaje:
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def token_actual(self):
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]
    
    def avanzar(self):
        self.pos += 1
    
    def esperar(self, tipo_esperado):
        token = self.token_actual()
        if not token or token[0] != tipo_esperado:
            print(f"ERROR SINTÁCTICO: Se esperaba {tipo_esperado}, pero se encontró {token}")                   #Reporte de error sintactico 
            return None
        self.avanzar()
        return token
    
    def parsear_programa(self):
        """
        <programa> ::= { <definicion_funcion> } { <print> }
        """
        funciones = []
        prints = []
        
        # Leer todas las definiciones de funciones
        while self.token_actual() and self.token_actual()[0] == "FUNC":
            funcion = self.parsear_funcion()
            if funcion:
                funciones.append(funcion)
            else:
                return None
        
        # Leer todos los prints
        while self.token_actual() and self.token_actual()[0] == "PRINT":
            print_stmt = self.parsear_print()
            if print_stmt:
                prints.append(print_stmt)
            else:
                return None
        
        return {"funciones": funciones, "prints": prints}
    
    def parsear_funcion(self):
        """
        <definicion_funcion> ::= func <id>( <param_list> ) = <expr> ;
        """
        if not self.esperar("FUNC"):
            return None
        
        nombre_token = self.esperar("ID")
        if not nombre_token:
            return None
        nombre = nombre_token[1]
        
        if not self.esperar("LPAREN"):
            return None
        
        # Leer parámetros
        parametros = []
        if self.token_actual() and self.token_actual()[0] == "ID":
            param_token = self.esperar("ID")
            parametros.append(param_token[1])
            
            while self.token_actual() and self.token_actual()[0] == "COMMA":
                self.avanzar()  # saltar la coma
                param_token = self.esperar("ID")
                if param_token:
                    parametros.append(param_token[1])
        
        if not self.esperar("RPAREN"):
            return None
        if not self.esperar("EQUALS"):
            return None
        
        # Parsear la expresión del cuerpo de la función (Reglas de gramatica)
        cuerpo = self.parsear_expresion()
        if not cuerpo:
            return None
        
        if not self.esperar("SEMICOLON"):
            return None
        
        return {
            "tipo": "funcion",
            "nombre": nombre,
            "parametros": parametros,
            "cuerpo": cuerpo
        }
    
    def parsear_print(self):
        """
        <print> ::= print <llamada_funcion> ;
        """
        if not self.esperar("PRINT"):
            return None
        
        expresion = self.parsear_expresion()
        if not expresion:
            return None
        
        if not self.esperar("SEMICOLON"):
            return None
        
        return {
            "tipo": "print",
            "expresion": expresion
        }
    
    def parsear_expresion(self):
        """
        <expr> ::= <term> { (+|-) <term> }*
        """
        izq = self.parsear_termino()
        if not izq:
            return None
        
        while self.token_actual() and self.token_actual()[0] in ["PLUS", "MINUS"]:
            op = self.token_actual()[1]
            self.avanzar()
            der = self.parsear_termino()
            if not der:
                return None
            izq = {"tipo": "binaria", "izq": izq, "op": op, "der": der}
        
        return izq
    
    def parsear_termino(self):
        """
        <term> ::= <factor> { (*|/) <factor> }*
        """
        izq = self.parsear_factor()
        if not izq:
            return None
        
        while self.token_actual() and self.token_actual()[0] in ["MULT", "DIV"]:
            op = self.token_actual()[1]
            self.avanzar()
            der = self.parsear_factor()
            if not der:
                return None
            izq = {"tipo": "binaria", "izq": izq, "op": op, "der": der}
        
        return izq
    
    def parsear_factor(self):
        """
        <factor> ::= <number> | <id> | ( <expr> ) | <llamada_funcion> | <factor> ^ <factor>
        """
        token = self.token_actual()
        if not token:
            return None
        
        # Número
        if token[0] == "NUMBER":
            self.avanzar()
            resultado = {"tipo": "numero", "valor": float(token[1])}
        
        # Identificador o llamada a función
        elif token[0] == "ID":
            nombre = token[1]
            self.avanzar()
            
            # ¿Es una llamada a función?
            if self.token_actual() and self.token_actual()[0] == "LPAREN":
                self.avanzar()  # saltar (
                argumentos = []
                
                # Leer argumentos
                if self.token_actual() and self.token_actual()[0] != "RPAREN":
                    arg = self.parsear_expresion()
                    if arg:
                        argumentos.append(arg)
                    
                    while self.token_actual() and self.token_actual()[0] == "COMMA":
                        self.avanzar()  # saltar coma
                        arg = self.parsear_expresion()
                        if arg:
                            argumentos.append(arg)
                
                if not self.esperar("RPAREN"):
                    return None
                
                resultado = {"tipo": "llamada", "nombre": nombre, "argumentos": argumentos}
            else:
                # Es una variable
                resultado = {"tipo": "variable", "nombre": nombre}
        
        # Expresión entre paréntesis
        elif token[0] == "LPAREN":
            self.avanzar()
            resultado = self.parsear_expresion()
            if not self.esperar("RPAREN"):
                return None
        
        else:
            print(f"ERROR SINTÁCTICO: Factor inesperado {token}")
            return None
        
        # Manejar potencia (^)
        if self.token_actual() and self.token_actual()[0] == "POW":
            self.avanzar()
            der = self.parsear_factor()  # Asociatividad derecha
            if not der:
                return None
            resultado = {"tipo": "binaria", "izq": resultado, "op": "^", "der": der}
        
        return resultado

# = Parte  3 de requerimientos : ANÁLISIS SEMÁNTICO =
       #Validacion de las funciones
def analisis_semantico(ast):
    """
    Verifica que:
    1. Las funciones se definan antes de usarse
    2. El número de parámetros sea correcto
    """
    # Crear tabla de funciones
    funciones_definidas = {}
    errores = []
    
    # Registrar todas las funciones primero
    for func in ast["funciones"]:
        nombre = func["nombre"]
        if nombre in funciones_definidas:
            errores.append(f"Función '{nombre}' ya está definida")
        else:
            funciones_definidas[nombre] = func
    
    # Verificar las llamadas en los prints
    for print_stmt in ast["prints"]:
        verificar_expresion(print_stmt["expresion"], funciones_definidas, errores)
    
    # Mostrar errores
    if errores:
        for error in errores:
            print(f"Error: {error}")
        return False
    
    return True

def verificar_expresion(expr, funciones, errores):
    """
    Verifica recursivamente una expresión
    """
    if expr["tipo"] == "llamada":
        nombre = expr["nombre"]
        argumentos = expr["argumentos"]
        
        # ¿La función existe?
        if nombre not in funciones:
            errores.append(f"función no definida '{nombre}'")
            return
        
        # ¿Número correcto de parámetros?
        func_def = funciones[nombre]
        esperados = len(func_def["parametros"])
        recibidos = len(argumentos)
        
        if esperados != recibidos:
            errores.append(f"número incorrecto de parámetros en {nombre} (esperado {esperados}, recibido {recibidos})")
        
        # Verificar argumentos recursivamente
        for arg in argumentos:
            verificar_expresion(arg, funciones, errores)
    
    elif expr["tipo"] == "binaria":
        verificar_expresion(expr["izq"], funciones, errores)
        verificar_expresion(expr["der"], funciones, errores)

# =Parte 4: EJECUCIÓN =
def ejecutar_programa(ast):
    """
    Ejecuta el programa: guarda las funciones y ejecuta los prints
    """
    # Guardar funciones en tabla de símbolos
    tabla_funciones = {}
    for func in ast["funciones"]:
        tabla_funciones[func["nombre"]] = func
    
    # Ejecutar cada print
    for print_stmt in ast["prints"]:
        try:
            resultado = evaluar_expresion(print_stmt["expresion"], tabla_funciones, {})
            # Mostrar como entero si es posible
            if resultado == int(resultado):
                print(int(resultado))
            else:
                print(resultado)
        except ZeroDivisionError:
            print("Error: división por cero")
        except Exception as e:
            print(f"Error: {e}")

def evaluar_expresion(expr, funciones, variables):
    """
    Evalúa una expresión y devuelve su valor
    """
    if expr["tipo"] == "numero":
        return expr["valor"]
    
    elif expr["tipo"] == "variable":
        nombre = expr["nombre"]
        if nombre in variables:
            return variables[nombre]
        else:
            raise Exception(f"Variable no definida: {nombre}")
    
    elif expr["tipo"] == "binaria":
        izq = evaluar_expresion(expr["izq"], funciones, variables)
        der = evaluar_expresion(expr["der"], funciones, variables)
        
        op = expr["op"]
        if op == "+":
            return izq + der
        elif op == "-":
            return izq - der
        elif op == "*":
            return izq * der
        elif op == "/":
            if der == 0:
                raise ZeroDivisionError()
            return izq / der
        elif op == "^":
            return izq ** der
    
    elif expr["tipo"] == "llamada":
        nombre = expr["nombre"]
        argumentos = expr["argumentos"]
        
        # Obtener definición de la función
        func_def = funciones[nombre]
        
        # Evaluar argumentos
        valores_args = []
        for arg in argumentos:
            valores_args.append(evaluar_expresion(arg, funciones, variables))
        
        # Crear nuevas variables con los parámetros
        nuevas_variables = variables.copy()
        for i, param in enumerate(func_def["parametros"]):
            nuevas_variables[param] = valores_args[i]
        
        # Evaluar el cuerpo de la función
        return evaluar_expresion(func_def["cuerpo"], funciones, nuevas_variables)

# ============= FUNCIÓN PRINCIPAL =============
def interpretar_funclang(codigo):
    """
    Función principal que ejecuta todas las fases
    """
    print(" Fase 1: Análisis Léxico...")
    tokens = analisis_lexico(codigo)
    if not tokens:
        return
    
    print(" Fase 2: Análisis Sintáctico...")
    parser = Parser(tokens)
    ast = parser.parsear_programa()
    if not ast:
        return
    
    print(" Fase 3: Análisis Semántico...")
    if not analisis_semantico(ast):
        return
    
    print(" Fase 4: Ejecución...")
    ejecutar_programa(ast)

# ===EJEMPLOS Y PRUEBAS ==
def main():
    # Ejemplo exitoso del parcial
    print("=== EJEMPLO EXITOSO ===")
    codigo_ejemplo = """func suma(a, b) = a + b;
func cuadrado(x) = x * x;
func potencia(x, y) = x ^ y;
print suma(4, 5);
print cuadrado(3);
print potencia(2, 4);
print potencia(3, suma(2,2));"""
    
    interpretar_funclang(codigo_ejemplo)
    
    print("\n=== EJEMPLO CON ERRORES ===")
    codigo_con_errores = """func mult(a, b) = a * b;
print mult(5);
print potencia(2,3);"""
    
    interpretar_funclang(codigo_con_errores)

# ============= LEER DESDE ARCHIVO =============
def leer_archivo(nombre_archivo):
    """
    Fase 5: Leer código desde archivo
    """
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as archivo:
            codigo = archivo.read()
        print(f" Leyendo desde {nombre_archivo}...")
        interpretar_funclang(codigo)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{nombre_archivo}'")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # python interprete.py codigo.txt
        leer_archivo(sys.argv[1])
    else:
        # python interprete.py
        main()