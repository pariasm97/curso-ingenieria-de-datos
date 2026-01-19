import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    spark = SparkSession.builder.appName("retail-etl").getOrCreate()

    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .csv(input_path))

    result = (df.groupBy("product_id")
                .agg(_sum("amount").alias("total_amount")))

    (result.write.mode("overwrite").parquet(output_path))
    spark.stop()
