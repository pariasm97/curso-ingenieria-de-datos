from pyspark import SparkContext

# 1. Inicializar el SparkContext (modo local)
sc = SparkContext("local", "ConteoPalabrasRDD")

# 2. Datos de entrada (Lista de oraciones)
data = [
    "Spark es rapido",
    "Spark es escalable",
    "Python y Spark son una gran combinacion",
    "Spark usa RDD"
]

# Creamos el RDD (Si fuera un archivo usarías: sc.textFile("ruta/archivo.txt"))
rdd = sc.parallelize(data)

# 3. Transformaciones
conteo = rdd.flatMap(lambda linea: linea.split(" ")) \
            .map(lambda palabra: (palabra.lower(), 1)) \
            .reduceByKey(lambda a, b: a + b)

# 4. Acción (Recolección de resultados)
resultado = conteo.collect()

print("--- Resultado RDD ---")
for palabra, cuenta in resultado:
    print(f"{palabra}: {cuenta}")

# Detener el contexto
sc.stop()
