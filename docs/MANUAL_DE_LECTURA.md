# Manual de lectura de resultados — Repo Analyzer

Este manual explica cómo interpretar los resultados que genera el Repo Analyzer al revisar un repositorio. No hace falta saber programar para seguirlo.

---

## 1. Qué genera cada análisis

Cada ejecución deja dos archivos en la carpeta `result/`:

| Archivo | Para quién | Contenido |
|---|---|---|
| `output.json` | **Toda persona que revise resultados** | El score de cada criterio, el motivo y dónde está la evidencia en el código |
| `discovery.json` | Equipo técnico | El inventario completo de lo que se encontró en el repositorio (archivos, dependencias, configuración, etc.) |

**Este manual se centra en `output.json`.** El archivo `discovery.json` se explica brevemente en la sección 8.

> Cada ejecución sobrescribe ambos archivos. Si necesitas conservar el resultado de un repositorio, copia los archivos antes de analizar otro.

---

## 2. Estructura general de `output.json`

```json
{
  "repository_path": "https://github.com/organizacion/repositorio",
  "commit_sha": "6242262792280dd73ebf07c91ab5e7e0c40a4d58",
  "evaluations": [
    { ...evaluación del criterio ARQ.001... },
    { ...evaluación del criterio ARQ.002... }
  ]
}
```

| Campo | Significado |
|---|---|
| `repository_path` | Repositorio analizado |
| `commit_sha` | Versión exacta del código analizada. **El resultado solo es válido para esa versión**: si el código cambia, hay que volver a ejecutar el análisis |
| `evaluations` | Una entrada por cada criterio evaluado |

---

## 3. Cómo leer una evaluación (orden recomendado)

Cada elemento de `evaluations` tiene esta forma:

```json
{
  "rule_id": "ARQ.001",
  "name": "Estilo Arquitectónico",
  "status": "EVALUATED",
  "score": 5,
  "confidence": 0.6,
  "reason": "Cumple todos los requisitos para nivel óptimo.",
  "metrics": { ... },
  "evidence": [ ... ]
}
```

Léela **en este orden**:

| Paso | Campo | Pregunta que responde |
|---|---|---|
| 1 | `rule_id` y `name` | ¿Qué criterio del catálogo es? |
| 2 | `status` | ¿Se pudo medir? **Léelo siempre antes que el score** |
| 3 | `score` | ¿Qué tan portable es la aplicación en este criterio? |
| 4 | `confidence` | ¿Cuánto peso darle a ese score? |
| 5 | `reason` | ¿Por qué obtuvo ese score? |
| 6 | `metrics` | ¿Qué números sustentan el resultado? |
| 7 | `evidence` | ¿En qué archivo y línea está lo encontrado? |

---

## 4. El campo `status`

El status indica **cómo debe interpretarse el score**.

| Status | Significado | Cómo interpretar el score |
|---|---|---|
| `EVALUATED` | El criterio se midió con evidencia real del código | El score es válido tal cual |
| `NOT_APPLICABLE` | El criterio no aplica a esta aplicación (por ejemplo, ARQ.002 cuando no se usa ningún SDK de nube) | El score es **5 por decisión del programa**: sin evidencia de acoplamiento, se considera apto para migrar. No es una medición |
| `UNKNOWN` | El resultado no encaja en ningún nivel definido en el catálogo | El score es `null`. **Requiere revisión manual** |

---

## 5. El campo `score`

La escala es **0, 3 o 5**. Su significado depende del criterio:

### ARQ.001 — Estilo Arquitectónico
Mide si el código está separado en capas (dominio, aplicación e infraestructura) y si las dependencias van en la dirección correcta: hacia el núcleo del negocio.

| Score | Significado | Condiciones que usa el programa |
|---|---|---|
| **5** | Arquitectura hexagonal, clean u onion aplicada de forma consistente. El dominio es independiente | Ninguna violación de capa **y** existe una capa de puertos (interfaces) |
| **3** | Arquitectura por capas razonable, con algunas dependencias técnicas en la capa de aplicación | 5 violaciones o menos, **ninguna** en el dominio |
| **0** | No hay separación reconocible, o el dominio depende de otras capas o de frameworks | Más de 5 violaciones, **o** alguna violación en el dominio, **o** no se reconocen las capas |

### ARQ.002 — Aislamiento de Dependencias / SDK Específicos
Mide si los SDK de proveedores de nube (AWS, Azure, GCP) están aislados en los adaptadores o si contaminan la lógica de negocio.

| Score | Significado | Condiciones que usa el programa |
|---|---|---|
| **5** | Todo SDK está limitado a los adaptadores y puede sustituirse | Sin uso en el dominio, 100% encapsulado **y** sin SDK específico de nube |
| **3** | SDK parcialmente encapsulado | Sin uso en el dominio y al menos el 70% del uso en adaptadores |
| **0** | SDK usado directamente en la lógica de negocio | Algún uso en el dominio, **o** menos del 70% del uso en adaptadores |

> **Nota:** un SDK de nube (por ejemplo, Azure Blob Storage) correctamente encapsulado obtiene **3, no 5**, porque sigue siendo específico de un proveedor. Así lo define el catálogo.

**Cómo se decide el score:** primero se revisan las condiciones de score 0 (basta con que se cumpla una). Si ninguna se cumple, se prueba el score 5 y luego el 3 (en ambos deben cumplirse todas las condiciones). Si nada encaja, el status queda en `UNKNOWN`.

---

## 6. El campo `confidence`

Indica cuánto confía el catálogo en que el método de medición refleje la realidad. Es un valor fijo por criterio, definido por el comité:

| Criterio | Confianza | Cómo interpretarlo |
|---|---|---|
| ARQ.001 | **0.6 (baja)** | Es una **señal fuerte, no un veredicto definitivo**. La clasificación de capas se deduce de los nombres de las carpetas. Conviene que un arquitecto confirme el resultado, sobre todo cuando es 0 |
| ARQ.002 | **0.9 (alta)** | El resultado se puede tomar como firme |

---

## 7. Los campos `reason`, `metrics` y `evidence`

### `reason`: el motivo en una frase

| Texto | Significado |
|---|---|
| `Cumple todos los requisitos para nivel óptimo.` | Score 5: no hay nada que corregir |
| `Cumple nivel 3. No alcanza nivel óptimo por fallar en: <condición>` | Score 3. La condición indicada es **lo que falta para llegar a 5** |
| `Fallo crítico detectado: <condición>` | Score 0. La condición indicada es **la causa principal** |
| `No aplica (...): sin evidencia de acoplamiento, se considera apto para migrar.` | `NOT_APPLICABLE`: el criterio no aplica |
| `No cumple con las reglas de evaluación configuradas.` | `UNKNOWN`: requiere revisión manual |

### `metrics`: los números

**ARQ.001**

| Métrica | Significado | Valor ideal |
|---|---|---|
| `layer_violations` | Total de dependencias en dirección incorrecta | `0` |
| `domain_violations` | Dependencias del **dominio** hacia la capa de aplicación, la infraestructura o frameworks y SDK externos | `0` |
| `application_violations` | Dependencias de la **capa de aplicación** hacia la infraestructura | `0` |
| `ports_layer_present` | Si existen interfaces (puertos) en el dominio o en la capa de aplicación | `true` |
| `structure_classifiable` | Si el programa reconoció las capas del proyecto | `true` |
| `violation_details` | **Lista de problemas a corregir**, uno por línea | vacía |

> **Librerías permitidas en el dominio:** los imports de `java.*` y de Lombok no cuentan como violación. Cualquier otro framework (Spring, JPA/`jakarta.persistence`, `javax.*`, etc.) importado desde el dominio **sí cuenta**. Esta lista es una propuesta inicial, a validar con el comité.

**ARQ.002**

El campo `integrations` contiene un elemento por cada SDK de nube detectado:

| Campo | Significado | Valor ideal |
|---|---|---|
| `technology` | SDK detectado (`aws_sdk`, `azure_sdk`, `gcp_sdk`) | — |
| `references` | Cantidad de usos en el código | — |
| `domain_leak` | Usos dentro del dominio | `0` |
| `encapsulation_ratio` | Fracción del uso que está en adaptadores (de 0.0 a 1.0) | `1.0` |

Si `integrations` está vacío, no se usa ningún SDK de nube.

### `evidence`: dónde mirar en el código

Cada elemento señala un lugar concreto del repositorio:

```json
{
  "kind": "java.type",
  "file_path": "application/src/main/java/.../port/in/cart/AddToCartUseCase.java",
  "line_number": 13,
  "attributes": { "name": "AddToCartUseCase", "kind": "interface" },
  "criteria": ["ARQ.001", "ARQ.002", "ARQ.004"],
  "rule_id": "java-interface"
}
```

| Campo | Qué hacer con él |
|---|---|
| `file_path` + `line_number` | Abrir ese archivo en esa línea |
| `attributes` | Lo que se encontró (en el ejemplo, la interfaz `AddToCartUseCase`) |
| `kind` | Tipo de hallazgo: `java.type` (una clase o interfaz), `java.import` (una dependencia) |
| `criteria`, `rule_id` | **Ignorar al leer el reporte.** Son datos técnicos: `criteria` indica a qué criterios *podría* servir ese tipo de hallazgo, **no** qué criterios se evaluaron |

**Cómo leer la evidencia según el score:**
- **Score 5:** muestra lo que está **bien** (por ejemplo, los puertos encontrados).
- **Score 0 o 3:** muestra las **dependencias problemáticas** que hay que corregir.
- **NOT_APPLICABLE:** la lista está vacía.

---

## 8. El archivo `discovery.json` (referencia técnica)

Contiene todo lo que se encontró en el repositorio, sirva o no para los criterios evaluados hoy:

| Sección | Contenido |
|---|---|
| `summary` | Cantidad de archivos analizados y de hallazgos, por tipo |
| `inputs_by_criterion` | Cuántos hallazgos hay disponibles para cada criterio del catálogo. **No es un score**: indica que existe información de entrada, no que el criterio esté evaluado |
| `criteria_without_signal` | Criterios para los que no se encontró ningún dato en el repositorio (por ejemplo, SRE.003 si no hay configuración de logging) |
| `modules` | Módulos del proyecto y de qué otros módulos dependen |
| `components` | Cada archivo Java con su paquete, módulo y la capa asignada (`DOMAIN`, `APPLICATION`, `INFRASTRUCTURE`, `UNKNOWN`) |
| `facts` | Cada hallazgo individual con su archivo y línea |

> Los valores sensibles (contraseñas, tokens, llaves) **nunca** aparecen en texto plano: se muestran como `sha256:<código>`. De los secretos escritos en el código solo se guarda el nombre de la variable.

---

## 9. Ejemplos de lectura

### Ejemplo A — Arquitectura correcta (score 5)
```json
"status": "EVALUATED", "score": 5, "confidence": 0.6,
"reason": "Cumple todos los requisitos para nivel óptimo.",
"metrics": { "layer_violations": 0, "ports_layer_present": true, "violation_details": [] }
```
**Lectura:** el dominio no depende de otras capas ni de frameworks, y existen puertos (interfaces). No hay nada que corregir. Como la confianza es baja (0.6), conviene una confirmación rápida por parte de un arquitecto.

### Ejemplo B — Dominio acoplado a un framework (score 0)
```json
"status": "EVALUATED", "score": 0,
"reason": "Fallo crítico detectado: domain_violations > 0",
"metrics": {
  "domain_violations": 1,
  "violation_details": [
    "DOMAIN component 'model/Order.java' depends on external framework/SDK 'jakarta.persistence.Entity'"
  ]
}
```
**Lectura:** la clase de negocio `Order.java` usa directamente JPA (`jakarta.persistence`), un detalle de persistencia. **Acción:** mover las anotaciones de persistencia a una entidad en la capa de infraestructura y dejar el modelo de dominio libre de frameworks. La evidencia indica el archivo y la línea exactos.

### Ejemplo C — SDK de nube bien encapsulado (score 3)
```json
"status": "EVALUATED", "score": 3,
"reason": "Cumple nivel 3. No alcanza nivel óptimo por fallar en: portability_class != \"CLOUD_SPECIFIC\""
```
**Lectura:** el SDK de nube solo se usa en los adaptadores (bien encapsulado), pero sigue siendo específico de un proveedor. Migrar implica reescribir ese adaptador, sin tocar la lógica de negocio.

### Ejemplo D — Criterio que no aplica
```json
"status": "NOT_APPLICABLE", "score": 5,
"reason": "No aplica (no se cumple 'vendor_sdk_integrations > 0'): sin evidencia de acoplamiento, se considera apto para migrar."
```
**Lectura:** la aplicación no usa SDK de ningún proveedor de nube. No hay acoplamiento que migrar en este criterio.

---

## 10. Preguntas frecuentes

**¿Por qué la evidencia de ARQ.001 menciona ARQ.004?**
El campo `criteria` de la evidencia indica a qué criterios *podría* servir ese hallazgo en el futuro, no qué se evaluó. Hoy solo se evalúan ARQ.001 y ARQ.002.

**¿Por qué un criterio que no aplica obtiene 5?**
Porque, sin evidencia de acoplamiento, la aplicación se considera apta para migrar en ese criterio. El status `NOT_APPLICABLE` permite distinguirlo de un 5 medido. El catálogo original indica que un criterio que no aplica "no penaliza ni premia y sale del denominador"; esta diferencia está pendiente de validación con el comité.

**Obtuve 0 en ARQ.001 pero la arquitectura está bien. ¿Qué pasó?**
Revisa `structure_classifiable` y la sección `components` de `discovery.json`. Si las capas figuran como `UNKNOWN`, el programa no las reconoció porque las carpetas no usan nombres estándar (`domain`, `model`, `application`, `port`, `adapter`, etc.). En ese caso hay que declarar las capas en `src/portability.config.yaml`, en la sección `overrides.module_roles`.

**¿Qué lenguajes se pueden analizar?**
Java (Spring Boot y Quarkus). Proyectos en C#, Python o Kotlin darían resultados incorrectos.

**¿Qué criterios del catálogo se puntúan hoy?**
Solo ARQ.001 y ARQ.002. Para el resto, `discovery.json` ya recoge la información de entrada, pero todavía no se calcula su score.
