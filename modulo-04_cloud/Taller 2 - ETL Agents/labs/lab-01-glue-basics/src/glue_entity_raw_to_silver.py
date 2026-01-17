import sys
from typing import Dict

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql import types as T


def _schemas() -> Dict[str, T.StructType]:
    return {
        "customers": T.StructType(
            [
                T.StructField("customer_id", T.StringType(), False),
                T.StructField("customer_name", T.StringType(), True),
                T.StructField("city", T.StringType(), True),
                T.StructField("country", T.StringType(), True),
                T.StructField("created_at", T.DateType(), True),
            ]
        ),
        "orders": T.StructType(
            [
                T.StructField("order_id", T.StringType(), False),
                T.StructField("customer_id", T.StringType(), False),
                T.StructField("order_ts", T.TimestampType(), True),
                T.StructField("status", T.StringType(), True),
                T.StructField("total_amount", T.DecimalType(18, 2), True),
                T.StructField("currency", T.StringType(), True),
            ]
        ),
        "payments": T.StructType(
            [
                T.StructField("payment_id", T.StringType(), False),
                T.StructField("order_id", T.StringType(), False),
                T.StructField("payment_method", T.StringType(), True),
                T.StructField("paid_amount", T.DecimalType(18, 2), True),
                T.StructField("currency", T.StringType(), True),
                T.StructField("paid_ts", T.TimestampType(), True),
            ]
        ),
    }


def main():
    # Argumentos
    # INPUT_PREFIX: por ejemplo s3://bucket/raw/source=synthetic/dt=2026-01-16/
    # OUTPUT_PREFIX: por ejemplo s3://bucket/silver/
    # ENTITY: customers | orders | payments
    # SOURCE: ejemplo synthetic
    # DT: ejemplo 2026-01-16
    args = getResolvedOptions(
        sys.argv,
        [
            "JOB_NAME",
            "INPUT_PREFIX",
            "OUTPUT_PREFIX",
            "ENTITY",
            "SOURCE",
            "DT",
        ],
    )

    entity = args["ENTITY"].strip().lower()
    if entity not in _schemas():
        raise ValueError(f"ENTITY invalida: {entity}. Use customers, orders o payments")

    input_prefix = args["INPUT_PREFIX"].rstrip("/")
    output_prefix = args["OUTPUT_PREFIX"].rstrip("/")
    source = args["SOURCE"].strip()
    dt = args["DT"].strip()

    input_path = f"{input_prefix}/{entity}.csv"
    output_path = f"{output_prefix}/{entity}/"

    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session

    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)

    schema = _schemas()[entity]

    # Leemos como string y casteamos para controlar errores de parseo
    raw_df = (
        spark.read.option("header", "true")
        .option("mode", "PERMISSIVE")
        .csv(input_path)
    )

    df = raw_df

    # Normalizacion y casteo por entidad
    if entity == "customers":
        df = df.select(
            F.col("customer_id").cast("string").alias("customer_id"),
            F.col("customer_name").cast("string").alias("customer_name"),
            F.col("city").cast("string").alias("city"),
            F.col("country").cast("string").alias("country"),
            F.to_date(F.col("created_at")).alias("created_at"),
        )
    elif entity == "orders":
        df = df.select(
            F.col("order_id").cast("string").alias("order_id"),
            F.col("customer_id").cast("string").alias("customer_id"),
            F.to_timestamp(F.col("order_ts")).alias("order_ts"),
            F.col("status").cast("string").alias("status"),
            F.col("total_amount").cast("decimal(18,2)").alias("total_amount"),
            F.col("currency").cast("string").alias("currency"),
        )
    else:
        df = df.select(
            F.col("payment_id").cast("string").alias("payment_id"),
            F.col("order_id").cast("string").alias("order_id"),
            F.col("payment_method").cast("string").alias("payment_method"),
            F.col("paid_amount").cast("decimal(18,2)").alias("paid_amount"),
            F.col("currency").cast("string").alias("currency"),
            F.to_timestamp(F.col("paid_ts")).alias("paid_ts"),
        )

    # Metadatos de particion
    df = df.withColumn("source", F.lit(source)).withColumn("dt", F.lit(dt))

    # Escritura idempotente por particion
    (
        df.repartition("source", "dt")
        .write.mode("overwrite")
        .format("parquet")
        .partitionBy("source", "dt")
        .save(output_path)
    )

    job.commit()


if __name__ == "__main__":
    main()
