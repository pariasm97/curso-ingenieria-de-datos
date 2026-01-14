from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, split, col, lower

# 1. Inicializar la SparkSession
spark = SparkSession.builder \
    .appName("ConteoPalabrasDF") \
    .getOrCreate()

# 2. Datos de entrada
data = [
    ("Spark es rapido",),
    ("Spark es escalable",),
    ("Python y Spark son una gran combinacion",),
    ("Spark usa Dataframes",)
]

# Creamos el DataFrame
df = spark.createDataFrame(data, ["oracion"])

# 3. Transformaciones
# Dividimos la oracion en un array de palabras y luego 'explotamos' el array en filas
df_palabras = df.select(
    explode(split(col("oracion"), " ")).alias("palabra")
)

# Agrupamos y contamos (normalizando a minusculas)
df_conteo = df_palabras.groupBy(lower(col("palabra")).alias("palabra")) \
                       .count() \
                       .orderBy("count", ascending=False)

# 4. Mostrar resultado
print("--- Resultado DataFrame ---")
df_conteo.show()

# Detener la sesión
spark.stop()
