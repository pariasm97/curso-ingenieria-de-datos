from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
from pyspark.sql.functions import col, sum as spark_sum, desc

# 1. Configuración de la Sesión
# A diferencia del 'sc' (SparkContext) de los RDDs, aquí usamos 'spark' (SparkSession)
spark = SparkSession.builder.appName("IntroDataFrames").getOrCreate()

# --- PASO 1: DEFINICIÓN DE ESQUEMA (Metadata) ---
# En RDD convertíamos tipos manualmente con int() o float().
# Aquí definimos la estructura antes de leer. Esto es más seguro y rápido.
schema_transacciones = StructType([
    StructField("transaccion_id", StringType(), False),
    StructField("timestamp", TimestampType(), True),
    # Nuestra clave de agrupación
    StructField("tienda_id", StringType(), True),
    StructField("producto_id", StringType(), True),
    StructField("categoria", StringType(), True),
    StructField("cantidad", IntegerType(), True),     # Int
    StructField("precio_unitario", DoubleType(), True),  # Double
    StructField("metodo_pago", StringType(), True)
])

# --- PASO 2: CARGA (Extract) ---
# Spark maneja la cabecera y los tipos automáticamente gracias al esquema.
df_ventas = spark.read.csv(
    "transacciones_retail_large.csv",
    header=True,
    schema=schema_transacciones
)

# --- PASO 3: TRANSFORMACIÓN (Proyecciones) ---
# Equivalente al 'map' del RDD, pero usando nombres de columnas.
# Calculamos el ingreso por fila.
df_calculado = df_ventas.withColumn(
    "ingreso_venta",
    col("cantidad") * col("precio_unitario")
)

# --- PASO 4: AGREGACIÓN (GroupBy) ---
# Equivalente al 'reduceByKey'.
# Spark optimiza esto usando HashAggregation bajo el capó.
df_reporte = (df_calculado
              .groupBy("tienda_id")
              .agg(
                  spark_sum("ingreso_venta").alias("venta_total")
              )
              .orderBy(desc("venta_total"))  # Ordenamos para ver el top
              )

# --- PASO 5: ACCIÓN (Show) ---
# Muestra la tabla formateada
print("--- Total Ventas por Tienda (DataFrames) ---")
df_reporte.show()

# spark.stop()
