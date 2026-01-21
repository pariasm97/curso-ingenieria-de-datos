# import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum

if __name__ == "__main__":
    input_path = "s3://etl-cluster/data/transacciones_retail_large.csv"
    output_path = "s3://etl-cluster/data/output/"

    spark = SparkSession.builder.appName("retail-etl").getOrCreate()

    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .csv(input_path))

    result = (df.groupBy("product_id")
                .agg(_sum("cantidad").alias("total_cantidadt")))

    (result.write.mode("overwrite").parquet(output_path))
    spark.stop()
