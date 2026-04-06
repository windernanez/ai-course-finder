import random

# Base de datos de quizzes estáticos para cuando la IA no esté disponible (ej: cuota excedida)
QUIZZES_ESTATICOS = {
    'python': {
        'principiante': {
            'titulo': 'Examen de Python - Nivel Principiante (Modo Offline)',
            'preguntas': [
                {
                    'pregunta': '¿Cuál es la función correcta para imprimir en consola?',
                    'opciones': ['console.log()', 'print()', 'echo', 'cout'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Cómo se define una lista en Python?',
                    'opciones': ['{1, 2}', '(1, 2)', '[1, 2]', '<1, 2>'],
                    'respuesta_correcta': 2
                },
                {
                    'pregunta': '¿Qué palabra clave se usa para definir una función?',
                    'opciones': ['func', 'function', 'define', 'def'],
                    'respuesta_correcta': 3
                },
                {
                    'pregunta': '¿Cuál es la extensión de archivo estándar para Python?',
                    'opciones': ['.py', '.python', '.pt', '.pyt'],
                    'respuesta_correcta': 0
                },
                {
                    'pregunta': '¿Qué operador se utiliza para la división entera?',
                    'opciones': ['/', '%', '//', 'div'],
                    'respuesta_correcta': 2
                }
            ]
        },
        'intermedio': {
            'titulo': 'Examen de Python - Nivel Intermedio (Modo Offline)',
            'preguntas': [
                {
                    'pregunta': '¿Qué hace "list comprehension" en Python?',
                    'opciones': ['Comprime una lista', 'Crea una lista de forma concisa', 'Ordena una lista', 'Borra duplicados'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Cuál es la diferencia entre una lista y una tupla?',
                    'opciones': ['Ninguna', 'La tupla es mutable', 'La lista es inmutable', 'La tupla es inmutable'],
                    'respuesta_correcta': 3
                },
                {
                    'pregunta': '¿Qué método se usa para añadir un elemento al final de una lista?',
                    'opciones': ['add()', 'push()', 'append()', 'insert()'],
                    'respuesta_correcta': 2
                },
                {
                    'pregunta': '¿Cómo se manejan las excepciones en Python?',
                    'opciones': ['try/except', 'try/catch', 'if/else', 'on error'],
                    'respuesta_correcta': 0
                },
                {
                    'pregunta': '¿Qué paquete se usa para manejar entornos virtuales?',
                    'opciones': ['env', 'venv', 'virt', 'pip'],
                    'respuesta_correcta': 1
                }
            ]
        }
    },
    'javascript': {
        'principiante': {
            'titulo': 'Examen de JavaScript - Nivel Principiante (Modo Offline)',
            'preguntas': [
                {
                    'pregunta': '¿Cómo se declara una variable que no cambiará su valor?',
                    'opciones': ['var', 'let', 'const', 'set'],
                    'respuesta_correcta': 2
                },
                {
                    'pregunta': '¿Qué método añade un elemento al final de un array?',
                    'opciones': ['pop()', 'push()', 'shift()', 'unshift()'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Cuál es el operador de igualdad estricta?',
                    'opciones': ['=', '==', '===', '!=='],
                    'respuesta_correcta': 2
                },
                {
                    'pregunta': '¿Cómo se escribe un comentario de una sola línea?',
                    'opciones': ['//', '/*', '#', '<!--'],
                    'respuesta_correcta': 0
                },
                {
                    'pregunta': '¿Qué función convierte un string a un número entero?',
                    'opciones': ['toInt()', 'Number.int()', 'parseInt()', 'parse()'],
                    'respuesta_correcta': 2
                }
            ]
        }
    },
    'java': {
        'principiante': {
            'titulo': 'Examen de Java - Nivel Principiante (Modo Offline)',
            'preguntas': [
                {
                    'pregunta': '¿Cuál es el punto de entrada de una aplicación Java?',
                    'opciones': ['start()', 'init()', 'main()', 'run()'],
                    'respuesta_correcta': 2
                },
                {
                    'pregunta': '¿Qué palabra clave se usa para heredar una clase?',
                    'opciones': ['implements', 'extends', 'inherits', 'from'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Cuál es el tipo de dato para un solo carácter?',
                    'opciones': ['String', 'char', 'Letter', 'chr'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Cómo se llama el compilador de Java?',
                    'opciones': ['java', 'javac', 'javamake', 'comp'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Qué clase es la raíz de todas las clases en Java?',
                    'opciones': ['Base', 'Root', 'Class', 'Object'],
                    'respuesta_correcta': 3
                }
            ]
        }
    }
}

def obtener_quiz_estatico(lenguaje, nivel):
    """Retorna un quiz estático o uno genérico si no existe"""
    lenguaje = lenguaje.lower()
    nivel = nivel.lower()
    
    quiz = QUIZZES_ESTATICOS.get(lenguaje, {}).get(nivel)
    
    if not quiz:
        # Quiz genérico si no tenemos el específico
        return {
            'titulo': f'Examen General de Programación - {lenguaje.capitalize()} {nivel.capitalize()}',
            'preguntas': [
                {
                    'pregunta': f'¿Cuál es la función principal de {lenguaje}?',
                    'opciones': ['Desarrollo Web', 'Análisis de datos', 'Uso general/Cualquiera', 'Sistemas operativos'],
                    'respuesta_correcta': 2
                },
                {
                    'pregunta': '¿Qué es una variable?',
                    'opciones': ['Un tipo de bucle', 'Un espacio en memoria para guardar datos', 'Una función matemática', 'Un error de sintaxis'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Para qué sirve un bucle "for"?',
                    'opciones': ['Para tomar decisiones', 'Para declarar variables', 'Para repetir un bloque de código', 'Para terminar el programa'],
                    'respuesta_correcta': 2
                },
                {
                    'pregunta': '¿Qué significa que un lenguaje sea Case Sensitive?',
                    'opciones': ['Que no importa mayúsculas/minúsculas', 'Que diferencia entre mayúsculas y minúsculas', 'Que es fácil de leer', 'Que necesita mucha memoria'],
                    'respuesta_correcta': 1
                },
                {
                    'pregunta': '¿Qué es un algoritmo?',
                    'opciones': ['Un lenguaje de programación', 'Un tipo de hardware', 'Una serie de pasos ordenados para resolver un problema', 'Una base de datos'],
                    'respuesta_correcta': 2
                }
            ]
        }
    return quiz
