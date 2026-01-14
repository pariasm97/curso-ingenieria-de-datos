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

import argparse
from datetime import datetime
from urllib.parse import urlparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window


def is_s3(uri: str) -> bool:
    return uri.lower().startswith("s3://")


def clean_id(colname: str):
    return F.regexp_replace(F.col(colname).cast("string"), r"\.0$", "")


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sales_path", required=True)
    ap.add_argument("--stock_path", required=True)
    ap.add_argument("--prior_path", required=True)
    ap.add_argument("--out_path", required=True, help="Prefijo/dir de salida (S3 o local)")
    ap.add_argument("--window_days", type=int, default=15)
    ap.add_argument("--csv_sep_in", default=",")
    ap.add_argument("--csv_sep_out", default=";")
    ap.add_argument("--single_file", action="store_true")
    ap.add_argument("--out_prefix", default="ordenes_traslado_netsuite")
    return ap.parse_args()


def main():
    args = parse_args()
    spark = SparkSession.builder.appName("etl-balanceos-spark").getOrCreate()

    run_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    ventas = (spark.read.option("header", "true").option("sep", args.csv_sep_in).csv(args.sales_path))
    stock  = (spark.read.option("header", "true").option("sep", args.csv_sep_in).csv(args.stock_path))
    prior  = (spark.read.option("header", "true").option("sep", args.csv_sep_in).csv(args.prior_path))

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

    # Ventana de días
    ventas = ventas.filter(F.col("Fecha") >= F.date_sub(F.current_date(), args.window_days))

    # Demanda
    needs = (ventas
             .groupBy("Sucursal", "ID interno", "Temporada")
             .agg(F.sum("Cantidad Vendida").alias("A_Reponer"))
             .filter((F.col("ID interno").isNotNull()) & (F.col("ID interno") != F.lit("")))
             .filter(F.col("A_Reponer") > 0))

    needs = (needs
             .join(prior.select("Sucursal", "prioridad_reposicion", F.col("codigo_corto").alias("dest_corto")),
                   on="Sucursal", how="left")
             .withColumn("prioridad_reposicion", F.coalesce(F.col("prioridad_reposicion"), F.lit(9999))))

    # Oferta
    sources = (stock
               .filter(F.col("Stock disponible para la venta") > 0)
               .join(prior.select("Sucursal", "prioridad_retiro", F.col("codigo_corto").alias("orig_corto")),
                     on="Sucursal", how="left")
               .withColumn("prioridad_retiro", F.coalesce(F.col("prioridad_retiro"), F.lit(9999))))

    # Matching por acumulados (Spark puro)
    w_need = Window.partitionBy("ID interno").orderBy("prioridad_reposicion", "Sucursal")
    needs2 = (needs
              .withColumn("need_idx", F.row_number().over(w_need))
              .withColumn("need_qty", F.col("A_Reponer").cast("double")))

    w_need_cum = Window.partitionBy("ID interno").orderBy("need_idx").rowsBetween(Window.unboundedPreceding, Window.currentRow)
    needs2 = (needs2
              .withColumn("need_cum", F.sum("need_qty").over(w_need_cum))
              .withColumn("need_cum_prev", F.coalesce(F.lag("need_cum", 1).over(Window.partitionBy("ID interno").orderBy("need_idx")), F.lit(0.0))))

    w_src = Window.partitionBy("ID interno").orderBy("prioridad_retiro", "Sucursal")
    src2 = (sources
            .withColumn("src_idx", F.row_number().over(w_src))
            .withColumn("src_qty", F.col("Stock disponible para la venta").cast("double")))

    w_src_cum = Window.partitionBy("ID interno").orderBy("src_idx").rowsBetween(Window.unboundedPreceding, Window.currentRow)
    src2 = (src2
            .withColumn("src_cum", F.sum("src_qty").over(w_src_cum))
            .withColumn("src_cum_prev", F.coalesce(F.lag("src_cum", 1).over(Window.partitionBy("ID interno").orderBy("src_idx")), F.lit(0.0))))

    pairs = (src2.select(
                "ID interno",
                F.col("Sucursal").alias("DESDE"),
                "orig_corto",
                "src_idx", "src_cum", "src_cum_prev"
             )
             .join(
                needs2.select(
                    "ID interno",
                    F.col("Sucursal").alias("HACIA"),
                    "Temporada",
                    "dest_corto",
                    "need_idx", "need_cum", "need_cum_prev"
                ),
                on="ID interno",
                how="inner"
             ))

    qty = F.greatest(
        F.lit(0.0),
        F.least(F.col("src_cum"), F.col("need_cum")) - F.greatest(F.col("src_cum_prev"), F.col("need_cum_prev")),
    )

    alloc = (pairs
             .withColumn("CANTIDAD", qty)
             .filter(F.col("CANTIDAD") > 0)
             .filter(F.col("DESDE") != F.col("HACIA")))

    # ID EXT OT con timestamp y secuencia
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
        )
    )

    out = (alloc.select(
                F.col("Temporada").alias("NOTA"),
                F.col("ID interno"),
                "HACIA",
                "DESDE",
                F.col("CANTIDAD").cast("int"),
                F.col("ID EXT OT"),
            ))

    out_base = args.out_path.rstrip("/")
    tmp_out = f"{out_base}/_tmp_run_ts={run_ts}/"

    (out.coalesce(1)
        .write
        .mode("overwrite")
        .option("header", "true")
        .option("delimiter", args.csv_sep_out)
        .csv(tmp_out))

    final_name = f"{args.out_prefix}_{run_ts}.csv"
    final_out = f"{out_base}/{final_name}"

    if not args.single_file:
        print("OK. Salida escrita en (directorio):", tmp_out)
        spark.stop()
        return

    # Single file: S3 copy/rename o local move
    if is_s3(tmp_out):
        import boto3

        def parse_s3(s3_uri: str):
            p = urlparse(s3_uri)
            return p.netloc, p.path.lstrip("/")

        s3 = boto3.client("s3")
        bkt, pref = parse_s3(tmp_out)

        resp = s3.list_objects_v2(Bucket=bkt, Prefix=pref)
        objs = resp.get("Contents", [])
        part = [o["Key"] for o in objs if o["Key"].endswith(".csv") and "part-" in o["Key"]]
        if not part:
            raise RuntimeError(f"No encontré part-*.csv en s3://{bkt}/{pref}")

        src_key = part[0]
        out_bkt, out_key = parse_s3(final_out)
        s3.copy_object(Bucket=out_bkt, Key=out_key, CopySource={"Bucket": bkt, "Key": src_key})

        # limpiar tmp
        del_objs = [{"Key": o["Key"]} for o in objs]
        if del_objs:
            s3.delete_objects(Bucket=bkt, Delete={"Objects": del_objs})

        print("OK. Archivo final:", final_out)
    else:
        import os, glob, shutil

        tmp_local = tmp_out
        if tmp_local.startswith("file:"):
            tmp_local = tmp_local[5:]

        part_files = glob.glob(os.path.join(tmp_local, "part-*.csv"))
        if not part_files:
            raise RuntimeError(f"No encontré part-*.csv en {tmp_local}")

        src = part_files[0]
        os.makedirs(out_base, exist_ok=True)
        dst = os.path.join(out_base, final_name)
        shutil.move(src, dst)
        shutil.rmtree(tmp_local, ignore_errors=True)

        print("OK. Archivo final:", dst)

    spark.stop()


if __name__ == "__main__":
    main()
