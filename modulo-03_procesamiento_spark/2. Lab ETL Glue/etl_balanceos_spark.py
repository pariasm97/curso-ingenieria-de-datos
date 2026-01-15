"""
ETL de Balanceos en PySpark (ejercicio)

Entradas (Silver, CSV con header):
  - ventas.csv: Fecha, Sucursal, ID interno, Temporada, Cantidad Vendida
  - stock.csv:  Sucursal, ID interno, Stock disponible para la venta
  - prioridades.csv: Sucursal, codigo_corto, prioridad_reposicion, prioridad_retiro

Salida (Gold):
  - CSV separado por ';' con columnas:
    NOTA, ID interno, HACIA, DESDE, CANTIDAD, ID EXT OT

El nombre del archivo final incluye fecha y hora (timestamp).
"""
# Glue ETL: Balanceos (Ventas + Stock + Prioridades) Silver a Gold


import sys
from datetime import datetime
from urllib.parse import urlparse

import boto3
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window


# ----------------------------
# Helpers: argumentos opcionales sin argparse
# ----------------------------
def get_opt(argv, key, default=None):
    """
    Lee un argumento opcional estilo Glue:
      --key value
    Si no existe, retorna default.
    """
    flag = f"--{key}"
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
        # flags booleanos sin valor (no recomendado en Glue UI)
        return "true"
    return default


def is_s3(uri: str) -> bool:
    return uri.lower().startswith("s3://")


def parse_s3(s3_uri: str):
    p = urlparse(s3_uri)
    if p.scheme != "s3":
        raise ValueError(f"URI S3 invalida: {s3_uri}")
    return p.netloc, p.path.lstrip("/")


def clean_id(colname: str):
    return F.regexp_replace(F.col(colname).cast("string"), r"\.0$", "")


def fail_if_bad_csv(df, dataset_name: str, sep_in: str):
    """
    Detecta el caso tipico: header completo quedo como una sola columna
    por separador incorrecto.
    """
    if len(df.columns) == 1:
        col0 = df.columns[0]
        if (sep_in == ";" and "," in col0) or (sep_in == "," and ";" in col0):
            raise ValueError(
                f"{dataset_name}: parece que el separador de entrada esta mal. "
                f"Estoy leyendo con csv_sep_in='{sep_in}' pero el header quedo en una sola columna: '{col0}'. "
                f"Corrige --csv_sep_in."
            )


def require_columns(df, required, dataset_name: str):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(
            f"{dataset_name}: faltan columnas requeridas: {missing}. "
            f"Columnas disponibles: {df.columns}"
        )


# ----------------------------
# Glue init
# ----------------------------
req = getResolvedOptions(
    sys.argv, ["JOB_NAME", "sales_path", "stock_path", "prior_path", "out_path"])

sc = SparkContext.getOrCreate()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

job = Job(glueContext)
job.init(req["JOB_NAME"], req)

# Opcionales con defaults
window_days = int(get_opt(sys.argv, "window_days", "15"))
csv_sep_in = get_opt(sys.argv, "csv_sep_in", ",")
csv_sep_out = get_opt(sys.argv, "csv_sep_out", ";")
out_prefix = get_opt(sys.argv, "out_prefix", "ordenes_traslado_netsuite")
single_file = str(get_opt(sys.argv, "single_file", "false")).lower() == "true"

run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

sales_path = req["sales_path"]
stock_path = req["stock_path"]
prior_path = req["prior_path"]
out_path = req["out_path"].rstrip("/")

print("PARAMS:")
print("  sales_path   =", sales_path)
print("  stock_path   =", stock_path)
print("  prior_path   =", prior_path)
print("  out_path     =", out_path)
print("  window_days  =", window_days)
print("  csv_sep_in   =", csv_sep_in)
print("  csv_sep_out  =", csv_sep_out)
print("  out_prefix   =", out_prefix)
print("  single_file  =", single_file)
print("  run_ts       =", run_ts)

# ----------------------------
# Extract
# ----------------------------
ventas = (spark.read
          .option("header", "true")
          .option("sep", csv_sep_in)
          .csv(sales_path))

stock = (spark.read
         .option("header", "true")
         .option("sep", csv_sep_in)
         .csv(stock_path))

prior = (spark.read
         .option("header", "true")
         .option("sep", csv_sep_in)
         .csv(prior_path))

fail_if_bad_csv(ventas, "VENTAS", csv_sep_in)
fail_if_bad_csv(stock, "STOCK", csv_sep_in)
fail_if_bad_csv(prior, "PRIORIDADES", csv_sep_in)

# Validar columnas base (ajusta si tus nombres reales difieren)
require_columns(ventas, ["Fecha", "Sucursal", "ID interno",
                "Temporada", "Cantidad Vendida"], "VENTAS")
require_columns(stock, ["Sucursal", "ID interno",
                "Stock disponible para la venta"], "STOCK")
require_columns(prior, ["Sucursal", "codigo_corto",
                "prioridad_reposicion", "prioridad_retiro"], "PRIORIDADES")

# ----------------------------
# Transform: limpieza
# ----------------------------
ventas = (ventas
          .withColumn("ID interno", clean_id("ID interno"))
          .withColumn("Sucursal", F.col("Sucursal").cast("string"))
          .withColumn("Fecha", F.to_date(F.col("Fecha")))
          .withColumn("Cantidad Vendida", F.col("Cantidad Vendida").cast("double")))

stock = (stock
         .withColumn("ID interno", clean_id("ID interno"))
         .withColumn("Sucursal", F.col("Sucursal").cast("string"))
         .withColumn("Stock disponible para la venta", F.col("Stock disponible para la venta").cast("double")))

prior = (prior
         .withColumn("Sucursal", F.col("Sucursal").cast("string"))
         .withColumn("codigo_corto", F.col("codigo_corto").cast("string"))
         .withColumn("prioridad_reposicion", F.col("prioridad_reposicion").cast("int"))
         .withColumn("prioridad_retiro", F.col("prioridad_retiro").cast("int")))

# Ventana de ventas
ventas = ventas.filter(F.col("Fecha") >= F.date_sub(
    F.current_date(), window_days))

# ----------------------------
# Demanda (needs)
# ----------------------------
needs = (ventas
         .groupBy("Sucursal", "ID interno", "Temporada")
         .agg(F.sum("Cantidad Vendida").alias("A_Reponer"))
         .filter((F.col("ID interno").isNotNull()) & (F.col("ID interno") != F.lit("")))
         .filter(F.col("A_Reponer") > 0))

needs = (needs
         .join(prior.select("Sucursal", "prioridad_reposicion", F.col("codigo_corto").alias("dest_corto")),
               on="Sucursal", how="left")
         .withColumn("prioridad_reposicion", F.coalesce(F.col("prioridad_reposicion"), F.lit(9999))))

# ----------------------------
# Oferta (sources)
# ----------------------------
sources = (stock
           .filter(F.col("Stock disponible para la venta") > 0)
           .join(prior.select("Sucursal", "prioridad_retiro", F.col("codigo_corto").alias("orig_corto")),
                 on="Sucursal", how="left")
           .withColumn("prioridad_retiro", F.coalesce(F.col("prioridad_retiro"), F.lit(9999))))

# ----------------------------
# Matching por acumulados (Spark puro)
# ----------------------------
w_need = Window.partitionBy("ID interno").orderBy(
    "prioridad_reposicion", "Sucursal")
needs2 = (needs
          .withColumn("need_idx", F.row_number().over(w_need))
          .withColumn("need_qty", F.col("A_Reponer").cast("double")))

w_need_cum = (Window.partitionBy("ID interno")
              .orderBy("need_idx")
              .rowsBetween(Window.unboundedPreceding, Window.currentRow))
needs2 = (needs2
          .withColumn("need_cum", F.sum("need_qty").over(w_need_cum))
          .withColumn("need_cum_prev",
                      F.coalesce(F.lag("need_cum", 1).over(Window.partitionBy("ID interno").orderBy("need_idx")),
                                 F.lit(0.0))))

w_src = Window.partitionBy("ID interno").orderBy(
    "prioridad_retiro", "Sucursal")
src2 = (sources
        .withColumn("src_idx", F.row_number().over(w_src))
        .withColumn("src_qty", F.col("Stock disponible para la venta").cast("double")))

w_src_cum = (Window.partitionBy("ID interno")
             .orderBy("src_idx")
             .rowsBetween(Window.unboundedPreceding, Window.currentRow))
src2 = (src2
        .withColumn("src_cum", F.sum("src_qty").over(w_src_cum))
        .withColumn("src_cum_prev",
                    F.coalesce(F.lag("src_cum", 1).over(Window.partitionBy("ID interno").orderBy("src_idx")),
                               F.lit(0.0))))

pairs = (src2.select(
    "ID interno",
    F.col("Sucursal").alias("DESDE"),
    "orig_corto",
    "src_idx", "src_cum", "src_cum_prev",
)
    .join(
    needs2.select(
        "ID interno",
        F.col("Sucursal").alias("HACIA"),
        "Temporada",
        "dest_corto",
        "need_idx", "need_cum", "need_cum_prev",
    ),
    on="ID interno",
    how="inner",
))

qty = F.greatest(
    F.lit(0.0),
    F.least(F.col("src_cum"), F.col("need_cum")) -
    F.greatest(F.col("src_cum_prev"), F.col("need_cum_prev")),
)

alloc = (pairs
         .withColumn("CANTIDAD", qty)
         .filter(F.col("CANTIDAD") > 0)
         .filter(F.col("DESDE") != F.col("HACIA")))

# ID externo con timestamp y secuencia
w_seq = Window.orderBy("ID interno", "DESDE", "HACIA", "need_idx", "src_idx")
alloc = alloc.withColumn("seq", F.row_number().over(w_seq))

alloc = alloc.withColumn(
    "ID EXT OT",
    F.concat(
        F.lit("OT-"),
        F.coalesce(F.col("orig_corto"), F.lit("XXX")),
        F.lit("-"),
        F.coalesce(F.col("dest_corto"), F.lit("YYY")),
        F.lit("-"),
        F.lit(run_ts),
        F.lit("-"),
        F.lpad(F.col("seq").cast("string"), 4, "0"),
    ),
)

out_df = alloc.select(
    F.col("Temporada").alias("NOTA"),
    F.col("ID interno"),
    "HACIA",
    "DESDE",
    F.col("CANTIDAD").cast("int"),
    F.col("ID EXT OT"),
)

# ----------------------------
# Load: escribe a tmp y (opcional) deja un solo archivo con nombre descriptivo
# ----------------------------
tmp_out = f"{out_path}/_tmp_run_ts={run_ts}/"
final_name = f"{out_prefix}_{run_ts}.csv"
final_out = f"{out_path}/{final_name}"

(out_df.coalesce(1)
 .write
 .mode("overwrite")
 .option("header", "true")
 .option("delimiter", csv_sep_out)
 .csv(tmp_out))

print("OK. Salida temporal:", tmp_out)

if single_file:
    if not is_s3(tmp_out) or not is_s3(final_out):
        raise ValueError("single_file=true requiere out_path en S3 (s3://...)")

    s3 = boto3.client("s3")
    bkt, pref = parse_s3(tmp_out)

    resp = s3.list_objects_v2(Bucket=bkt, Prefix=pref)
    objs = resp.get("Contents", [])
    part = [o["Key"]
            for o in objs if o["Key"].endswith(".csv") and "part-" in o["Key"]]
    if not part:
        raise RuntimeError(f"No encontre part-*.csv en s3://{bkt}/{pref}")

    src_key = part[0]
    out_bkt, out_key = parse_s3(final_out)

    s3.copy_object(
        Bucket=out_bkt,
        Key=out_key,
        CopySource={"Bucket": bkt, "Key": src_key},
    )

    del_objs = [{"Key": o["Key"]} for o in objs]
    if del_objs:
        s3.delete_objects(Bucket=bkt, Delete={"Objects": del_objs})

    print("OK. Archivo final:", final_out)

job.commit()
