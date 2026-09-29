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

Al terminar deja dos archivos en `result/`:
- `output.json`: el reporte de scores por criterio con su evidencia (archivo y linea).
- `discovery.json`: el inventario completo del descubrimiento (archivos, hechos, modulos y que criterios tienen insumos).

**4. Arquitectura del proyecto**
Pipeline por etapas. Cada carpeta tiene una unica responsabilidad y los datos viajan entre etapas como modelos de `src/models/`:

```
src/
├── main.py              Orquestacion: config -> clonado -> pipeline -> result/
├── config/loader.py     Lectura de YAML y del catalogo de criterios (CriterionDefinition)
├── models/              TODOS los modelos de datos y enums (sin logica)
│   ├── enums.py         EvaluationStatus, ModuleRole, TechClass, PortabilityClass
│   ├── discovery.py     Fact, ComponentInfo, ModuleInfo, RepositoryInventory
│   ├── catalog.py       CriterionDefinition, ScoreRule (criteria.yaml)
│   ├── metrics.py       CriterionMetrics (base) y metricas por criterio
│   └── report.py        RuleEvaluation, FinalReport
└── engine/              Etapas del pipeline
    ├── semgrep_runner.py  1. Discovery: ejecuta Semgrep y produce Facts (redacta secretos)
    ├── discoverer.py      1. Discovery: agrupa Facts en componentes y modulos
    ├── classifier.py      2. Classification: rol de cada componente (dominio/aplicacion/infra)
    ├── metrics.py         3. Metrics: calcula las metricas de cada criterio
    ├── scoring.py         4. Scoring: aplica applies_when y los niveles 0/3/5 del catalogo
    ├── conditions.py         Evaluador de condiciones ("layer_violations <= 5")
    └── reporting.py       5. Reporting: arma result/discovery.json
```

**Agregar un criterio nuevo:**
1. Declararlo en `catalog/criteria.yaml` (`name`, `confidence`, `applies_when`, `parameters`, `scores`).
2. Crear su modelo de metricas en `models/metrics.py` heredando de `CriterionMetrics` (si sus condiciones usan valores agregados, sobrescribir `scoring_inputs()`).
3. Calcularlo en `engine/metrics.py` y registrarlo en `metrics_by_criterion` de `main.py`. El `ScoringEngine` no se modifica.

**5. Como funciona el descubrimiento**
Semgrep es el **unico** extractor de contenido. Las reglas en `rules/` capturan *hechos neutrales* sin interpretarlos:

| Archivo | Fuente (catalogo) | Hechos |
|---|---|---|
| `java.yaml` | T1 patrones + T2 imports | paquete, imports, tipos (clase/interfaz/enum/record), implements/extends, anotaciones y sus argumentos, `main`, metodos nativos, llamadas relevantes (getenv, getInstance, exec, getHeader...), literales (URLs, SQL, rutas, FQDN de nube, headers), secretos embebidos |
| `build.yaml` | T0 dependencias declaradas | dependencias, parent, plugins, repositorios, packaging y modulos (Maven y Gradle) |
| `runtime.yaml` | T4 Dockerfile + T5 manifiestos | instrucciones de Dockerfile, objetos y claves de Kubernetes (probes, PVC, sessionAffinity, privileged...), variables de entorno, pasos y comandos de pipelines |
| `config.yaml` | configuracion | propiedades de `*.properties` y `application*.yml`, appenders/encoders de logging, claves MDC |
| `contracts.yaml` | T3 contratos | version OpenAPI/Swagger/AsyncAPI, extensiones `x-`, paths, esquemas Avro y Protobuf |
| `data.yaml` | T6 SQL | objetos DDL (procedures, triggers, secuencias) y tokens propios de cada motor |
| `iac.yaml` | T5 IaC | recursos, providers y modulos de Terraform, Bicep, CloudFormation y ARM |
| `secrets.yaml` | deteccion de secretos | llaves privadas, access keys, credenciales en connection strings, certificados |

Cada regla declara en `metadata` el tipo de hecho (`fact`), los valores capturados (`fields`) y los criterios del catalogo que alimenta (`criteria`). El significado de cada hecho (p.ej. que `com.azure.*` es un SDK de nube) lo deciden los catalogos (`catalog/`), no las reglas.

**Condicion N3:** los valores de claves sensibles (password, secret, token...) y las credenciales embebidas nunca se persisten; se guardan como `sha256:<hash>`. De los secretos en codigo solo se guarda el nombre de la variable.

**Pruebas:** `python -m unittest discover -s tests` (valida las reglas contra `tests/fixtures/sample-app`).

**Fuera del alcance del descubrimiento estatico** (requieren insumos externos): arbol transitivo / SBOM resuelto, inventario de la nube (T8), export de politicas de APIM (T9), resolucion de tipos con JDT (T10, ola 2), whitelist de frameworks BCP e instantanea de fin de vida.
