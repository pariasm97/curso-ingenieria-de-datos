from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, TimestampType

# 1. Configuración de la Sesión
spark = SparkSession.builder.appName("IntroSparkSQL").getOrCreate()

# --- PASO 1: ESQUEMA Y CARGA (Igual que DataFrames) ---
schema_transacciones = StructType([
    StructField("transaccion_id", StringType(), False),
    StructField("timestamp", TimestampType(), True),
    StructField("tienda_id", StringType(), True),
    StructField("producto_id", StringType(), True),
    StructField("categoria", StringType(), True),
    StructField("cantidad", IntegerType(), True),
    StructField("precio_unitario", DoubleType(), True),
    StructField("metodo_pago", StringType(), True)
])

df_ventas = spark.read.csv(
    "transacciones_retail_large.csv",
    header=True,
    schema=schema_transacciones
)

# --- PASO 2: EL PUENTE (Registrar la Vista Temporal) ---
# Esto es lo CRÍTICO. Convierte el objeto Python 'df_ventas'
# en una tabla SQL consultable llamada 'v_transacciones'.
df_ventas.createOrReplaceTempView("v_transacciones")

# --- PASO 3: LA CONSULTA SQL (Lógica de Negocio) ---
# Escribimos SQL estándar (ANSI SQL).
# Fíjate que hacemos la multiplicación y la suma en la misma línea.
query = """
    SELECT 
        tienda_id,
        SUM(cantidad * precio_unitario) as venta_total
    FROM v_transacciones
    GROUP BY tienda_id
    ORDER BY venta_total DESC
"""

# --- PASO 4: EJECUCIÓN ---
# spark.sql() devuelve un nuevo DataFrame. No muestra los datos todavía, solo prepara el plan.
df_resultado_sql = spark.sql(query)

# --- PASO 5: ACCIÓN ---
print("--- Resultados usando Spark SQL ---")
df_resultado_sql.show()

# spark.stop()
