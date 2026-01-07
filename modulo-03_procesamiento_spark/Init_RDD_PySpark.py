from pyspark import SparkContext

# 1. Configuración del Contexto
# Si estás en un notebook (Colab/Jupyter), el 'sc' suele existir.
# Si corres esto como script .py, necesitas las siguientes líneas:
sc = SparkContext.getOrCreate()

# --- PASO 1: CARGA (Extract) ---
# Leemos el archivo como una colección de líneas de texto (Strings).
# No hay columnas todavía, solo líneas crudas.
rdd_raw = sc.textFile("transacciones_retail_large.csv")

# --- PASO 2: GESTIÓN DE CABECERA (Limpieza Básica) ---
# Los RDDs no saben qué es una cabecera. La leen como una fila más de datos.
# Debemos aislarla y filtrarla.
header = rdd_raw.first()  # Acción: Trae la primera línea
rdd_no_header = rdd_raw.filter(lambda linea: linea != header)

# --- PASO 3: PARSING (Estructuración) ---
# Convertimos la línea de texto "TXN-001,..." en una lista de objetos Python.
# Índices del CSV generado:
# 0: id, 1: timestamp, 2: tienda, 3: producto, 4: categoria,
# 5: cantidad (int), 6: precio (float), 7: metodo_pago


def parsear_linea(linea):
    campos = linea.split(",")
    # Retornamos una tupla con los datos convertidos a su tipo real
    # Es crucial convertir String -> Float/Int para hacer matemáticas
    return (
        campos[2],           # Tienda (Key)
        campos[4],           # Categoria
        int(campos[5]),      # Cantidad
        float(campos[6])     # Precio Unitario
    )


# Aplicamos la función a cada línea
rdd_parsed = rdd_no_header.map(parsear_linea)

# --- PASO 4: TRANSFORMACIÓN (Map-Reduce Pattern) ---
# Objetivo: Calcular ingreso total por Tienda.

# 4.1 MAP: Crear pares Clave-Valor (Key-Value)
# Estructura deseada: (Tienda, Ingreso_Venta)
# Ingreso_Venta = Cantidad * Precio
rdd_kv = rdd_parsed.map(lambda x: (x[0], x[2] * x[3]))

# 4.2 REDUCE: Agregación por clave
# Spark junta todos los valores de la misma tienda y los suma.
rdd_totales = rdd_kv.reduceByKey(lambda acumulador, valor: acumulador + valor)

# 4.3 SORT (Opcional): Ordenar por mayor venta
# false = descendente
rdd_ordenado = rdd_totales.sortBy(lambda x: x[1], ascending=False)

# --- PASO 5: ACCIÓN (Load/Show) ---
# Traemos los resultados a la memoria del driver (Cuidado: solo si son pocos datos)
resultados = rdd_ordenado.collect()

print(f"{'TIENDA':<15} | {'VENTA TOTAL':>15}")
print("-" * 33)
for tienda, total in resultados:
    print(f"{tienda:<15} | ${total:>14.2f}")

# Detener contexto
sc.stop()
