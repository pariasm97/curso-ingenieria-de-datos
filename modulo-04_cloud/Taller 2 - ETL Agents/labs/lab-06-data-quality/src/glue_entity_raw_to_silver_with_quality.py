import json
import sys
from datetime import datetime, timezone

import boto3
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F


def _parse_s3_uri(uri: str):
    if not uri.lower().startswith("s3://"):
        raise ValueError(f"No es s3:// URI: {uri}")
    no_scheme = uri[5:]
    bucket, key = no_scheme.split("/", 1)
    return bucket, key


def main():
    args = getResolvedOptions(
        sys.argv,
        [
            "JOB_NAME",
            "INPUT_PREFIX",
            "OUTPUT_PREFIX",
            "QUALITY_OUTPUT_PREFIX",
            "ENTITY",
            "SOURCE",
            "DT",
        ],
    )

    entity = args["ENTITY"].strip().lower()
    if entity not in ("customers", "orders", "payments"):
        raise ValueError("ENTITY invalida. Use customers, orders o payments")

    input_prefix = args["INPUT_PREFIX"].rstrip("/")
    output_prefix = args["OUTPUT_PREFIX"].rstrip("/")
    quality_prefix = args["QUALITY_OUTPUT_PREFIX"].rstrip("/")
    source = args["SOURCE"].strip()
    dt = args["DT"].strip()

    input_path = f"{input_prefix}/{entity}.csv"
    output_path = f"{output_prefix}/{entity}/"

    sc = SparkContext.getOrCreate()
    glue_context = GlueContext(sc)
    spark = glue_context.spark_session

    job = Job(glue_context)
    job.init(args["JOB_NAME"], args)

    raw_df = spark.read.option("header", "true").option("mode", "PERMISSIVE").csv(input_path)

    if entity == "customers":
        df = raw_df.select(
            F.col("customer_id").cast("string").alias("customer_id"),
            F.col("customer_name").cast("string").alias("customer_name"),
            F.col("city").cast("string").alias("city"),
            F.col("country").cast("string").alias("country"),
            F.to_date(F.col("created_at")).alias("created_at"),
        )
        required_cols = ["customer_id"]
        unique_cols = ["customer_id"]
    elif entity == "orders":
        df = raw_df.select(
            F.col("order_id").cast("string").alias("order_id"),
            F.col("customer_id").cast("string").alias("customer_id"),
            F.to_timestamp(F.col("order_ts")).alias("order_ts"),
            F.col("status").cast("string").alias("status"),
            F.col("total_amount").cast("decimal(18,2)").alias("total_amount"),
            F.col("currency").cast("string").alias("currency"),
        )
        required_cols = ["order_id", "customer_id"]
        unique_cols = ["order_id"]
    else:
        df = raw_df.select(
            F.col("payment_id").cast("string").alias("payment_id"),
            F.col("order_id").cast("string").alias("order_id"),
            F.col("payment_method").cast("string").alias("payment_method"),
            F.col("paid_amount").cast("decimal(18,2)").alias("paid_amount"),
            F.col("currency").cast("string").alias("currency"),
            F.to_timestamp(F.col("paid_ts")).alias("paid_ts"),
        )
        required_cols = ["payment_id", "order_id"]
        unique_cols = ["payment_id"]

    df = df.withColumn("source", F.lit(source)).withColumn("dt", F.lit(dt))

    total_rows = df.count()

    nulls = {}
    for c in required_cols:
        nulls[c] = df.filter(F.col(c).isNull() | (F.col(c) == "")).count()

    dupes = {}
    for c in unique_cols:
        dup_cnt = (
            df.groupBy(c)
            .count()
            .filter((F.col(c).isNotNull()) & (F.col("count") > 1))
            .count()
        )
        dupes[c] = dup_cnt

    extra_checks = {}
    if entity in ("orders", "payments"):
        amt_col = "total_amount" if entity == "orders" else "paid_amount"
        extra_checks[f"{amt_col}_negative_or_null"] = df.filter(F.col(amt_col).isNull() | (F.col(amt_col) < 0)).count()

    report = {
        "entity": entity,
        "source": source,
        "dt": dt,
        "input_path": input_path,
        "output_path": output_path,
        "row_count": total_rows,
        "required_nulls": nulls,
        "unique_duplicates": dupes,
        "extra_checks": extra_checks,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    # Guardar reporte en S3
    s3 = boto3.client("s3")
    bucket, base_key = _parse_s3_uri(quality_prefix)
    key = f"{base_key.rstrip('/')}/{entity}/source={source}/dt={dt}/report.json"
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(report, ensure_ascii=False).encode("utf-8"), ContentType="application/json")

    # Falla dura si hay problemas
    violations = 0
    violations += sum(v for v in nulls.values())
    violations += sum(v for v in dupes.values())
    violations += sum(v for v in extra_checks.values())

    if violations > 0:
        raise Exception(f"Data quality fallo. Violaciones={violations}. Ver reporte: s3://{bucket}/{key}")

    # Escritura a silver
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
