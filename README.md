# Repo Analyzer

Este proyecto es un pequeño experimento (una Prueba de Concepto) para revisar código automáticamente.

Básicamente, le damos la dirección (URL) de un proyecto de Java en GitHub, y este programa se encarga de descargarlo, leer sus archivos y detectar si hay problemas de arquitectura o código desordenado. Todo esto usando una herramienta de búsqueda inteligente llamada Semgrep.


**1. Instala las dependencias**
Asegúrate de tener Python instalado y ejecuta este comando para descargar las librerías necesarias:
```cmd
pip install -r requirements.txt
```

**2. Elige el proyecto a analizar**
Abre el archivo `src/portability.config.yaml` y pon la URL del repositorio de GitHub que quieres escanear.

**3. Ejecuta el escáner**
Corre el programa principal con:
```cmd
python src/main.py
```

Cuando termine de pensar, te dejará un archivo llamado `output.json` donde podrás leer un reporte muy claro con todas las cosas que encontró en el código.


**4. Avance**
De momento lo que hace el motor de reglas actuales es:

1. La regla ARQ-001 actúa como un escáner general que captura absolutamente todos los imports del código para construir un mapa completo de quién llama a quién (necesario para evaluar el acoplamiento entre capas). 

2. La regla ARQ-002 es un filtro específico diseñado para detectar si el código está fuertemente acoplado a proveedores de la nube (AWS, Google Cloud o Azure) capturando las dependencias directas a sus SDKs, lo que ayuda a evaluar el nivel de portabilidad del proyecto.

**Fase actual de la PoC:** Todo este sistema actúa ahora mismo como un **observador (extractor de datos puro)**. Su único trabajo es escanear ciegamente el código y recolectar todas las piezas (los `imports`) en el archivo JSON. 

En la siguiente fase del proyecto, un **Evaluador Inteligente** escrito en Python tomará este JSON, cruzará las dependencias descubiertas contra el diseño de las capas de tu arquitectura y determinará matemáticamente si las reglas se están rompiendo o si es una buena práctica, asignando finalmente un *Score* de calidad.
