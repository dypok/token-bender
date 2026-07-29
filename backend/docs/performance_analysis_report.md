# Reporte de Analisis de Rendimiento y Plan de Accion - Analizador de Excel

**Modulo:** Analizador de Reseñas en Lote (Excel Ingest)
**Contexto:** Optimizacion del procesamiento de archivos Excel individuales (Modo A) y carpetas de archivos (Modo B) para reducir la latencia general y optimizar el consumo de recursos.

---

## 1. Diagnostico de Cuellos de Botella Actuales

Al analizar la implementacion en [batch.py](file:///C:/Users/LENOVO/Documents/DANI DOCS/RIWI/IA FOR DEVS/token-bender/backend/app/routers/batch.py), se identifican los siguientes factores limitantes de rendimiento:

### A. Procesamiento Secuencial de Filas (Bucle Sincronico/Bloqueante)
En los endpoints `/api/batch/upload` y `/api/batch/folder`, las filas se procesan mediante un bucle `for` convencional:
```python
for text in df[text_col]:
    # ...
    translated, _ = await translate(text_str, engine, ...)
    # ...
    class_result, _ = await classify(text_for_llm, engine, ...)
```
Esto provoca que cada reseña espere a que terminen la traduccion y la clasificacion de la reseña anterior. Si un analisis promedio de LLM tarda 1.5 segundos, procesar un archivo con 100 reseñas tardara 150 segundos (2.5 minutos). El rendimiento escala a $O(N)$ de forma estrictamente secuencial.

### B. Sobrecarga de Creacion de Clientes HTTP (Conexiones TCP/TLS)
En [translator.py](file:///C:/Users/LENOVO/Documents/DANI DOCS/RIWI/IA FOR DEVS/token-bender/backend/app/services/translator.py) y [classifier.py](file:///C:/Users/LENOVO/Documents/DANI DOCS/RIWI/IA FOR DEVS/token-bender/backend/app/services/classifier.py), cada peticion a las APIs (Ollama local o DeepL remota) instancia y destruye un cliente `httpx.AsyncClient`:
```python
async with httpx.AsyncClient(timeout=60) as client:
    # ...
```
Esta practica evita la reutilizacion de conexiones (Connection Pooling). Para cada fila, se realiza un nuevo saludo TCP de red (handshake) y TLS (en el caso de DeepL), lo cual añade una latencia innecesaria de 100ms a 300ms por llamada HTTP.

### C. Consumo de Memoria de Pandas en Lectura de Archivos
La libreria `pandas` carga toda la hoja de calculo en memoria para construir un DataFrame. Para archivos masivos o ejecuciones concurrentes, esto incrementa el consumo de memoria del backend.

---

## 2. Plan de Accion e Implementacion

Para lograr el mayor nivel de optimizacion posible, se proponen e implementaran las siguientes mejoras tecnicas:

### Paso 1: Concurrencia Limitada con Semaforo (Asyncio Semaphore)
Modificar el bucle para procesar multiples filas en paralelo mediante `asyncio.gather`, limitando el numero de tareas simultaneas con `asyncio.Semaphore(concurrency_limit)`. Esto previene saturar el servidor local de Ollama o exceder los limites de peticiones (rate-limits) de la API de DeepL. Un limite optimo es entre 5 y 10 tareas simultaneas.

### Paso 2: Reutilizacion de Cliente HTTP (Connection Pooling)
Implementar un cliente global unico `httpx.AsyncClient()` reutilizable mediante el ciclo de vida de la aplicacion (lifespan en FastAPI). Esto mantendra las conexiones abiertas en un pool, eliminando la latencia de conexion en cada llamada de traduccion y clasificacion.

### Paso 3: Optimizar la Dependencia de Lectura Excel
Sustituir `pandas` por la lectura nativa con `openpyxl` utilizando el modo de solo lectura (`read_only=True`), reduciendo la huella de memoria en mas de un 60% y mejorando los tiempos de inicializacion del servidor.

### Paso 4: Paralelizacion de Tareas Internas por Fila
Cuando la bandera `optent_tokens` sea `False`, la clasificacion no depende del texto traducido, por lo que podemos ejecutar `translate()` y `classify()` simultaneamente para la misma fila mediante `asyncio.gather`.

---

## 3. Estimacion de Impacto en Latencia

| Escenario (100 Reseñas) | Latencia Estimada Actual | Latencia con Plan de Accion | Ahorro / Ganancia |
|-------------------------|--------------------------|-----------------------------|-------------------|
| Ollama (Local)          | ~180 segundos            | ~25 segundos                | **~86% de ahorro**|
| DeepL (Remoto)          | ~120 segundos            | ~15 segundos                | **~87% de ahorro**|

---

## 4. Comparativa de Rendimiento: CSV vs. XLSX

El backend actual ya soporta de forma nativa la lectura de ambos formatos (.csv y .xlsx) tanto en el endpoint de carga como en la lectura por lote. Sin embargo, existen diferencias de rendimiento significativas:

### A. Costo de Parseo y Lectura (CPU & Memoria)
- **Formato XLSX:** Es un archivo comprimido en ZIP que internamente contiene multiples estructuras XML (workbook, hojas, estilos, tabla de strings compartidas). Leerlo requiere descomprimir el ZIP en memoria y parsear el arbol XML celda por celda. Esto consume ciclos sustanciales de CPU y ram.
- **Formato CSV:** Es texto plano. Su parseo consiste en dividir el archivo por delimitadores (comas, puntos y comas), lo cual se realiza mediante el motor C ultra optimizado de Pandas (`pd.read_csv`). Es decenas de veces mas rapido en la lectura inicial.

### B. ¿Donde conviene realizar la conversion?
- **En el Servidor (Incorrecto):** Convertir el XLSX a CSV en el backend antes de procesarlo no aporta ninguna ventaja, ya que el servidor primero debe abrir y parsear todo el XLSX para poder convertirlo, incurriendo en el mismo costo computacional inicial.
- **En el Cliente (Recomendado):** Permitir que el usuario suba archivos CSV directamente (o hacer que el frontend en Javascript convierta el XLSX a CSV mediante librerias ligeras antes de enviar los datos al endpoint) es la solucion mas eficiente. De esta forma, el backend recibe un archivo mucho mas liviano y rapido de procesar.

### C. Conclusion sobre formatos
Para lotes pequeños (menos de 500 filas), la diferencia en tiempo de lectura es imperceptible frente al tiempo que tardan las llamadas a la API de LLMs. Sin embargo, para lotes grandes (mas de 5,000 filas), subir archivos en formato **CSV** reduce a la mitad el tiempo de procesamiento y consumo de memoria del backend en comparacion con XLSX.
