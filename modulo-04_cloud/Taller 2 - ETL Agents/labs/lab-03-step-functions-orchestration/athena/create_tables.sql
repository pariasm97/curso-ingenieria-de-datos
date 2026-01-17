-- Reemplace <DATA_BUCKET> y <GLUE_DB>.

CREATE DATABASE IF NOT EXISTS <GLUE_DB>;

-- Customers
CREATE EXTERNAL TABLE IF NOT EXISTS <GLUE_DB>.customers_silver (
  customer_id string,
  customer_name string,
  city string,
  country string,
  created_at date
)
PARTITIONED BY (source string, dt string)
STORED AS PARQUET
LOCATION 's3://<DATA_BUCKET>/silver/customers/';

-- Orders
CREATE EXTERNAL TABLE IF NOT EXISTS <GLUE_DB>.orders_silver (
  order_id string,
  customer_id string,
  order_ts timestamp,
  status string,
  total_amount decimal(18,2),
  currency string
)
PARTITIONED BY (source string, dt string)
STORED AS PARQUET
LOCATION 's3://<DATA_BUCKET>/silver/orders/';

-- Payments
CREATE EXTERNAL TABLE IF NOT EXISTS <GLUE_DB>.payments_silver (
  payment_id string,
  order_id string,
  payment_method string,
  paid_amount decimal(18,2),
  currency string,
  paid_ts timestamp
)
PARTITIONED BY (source string, dt string)
STORED AS PARQUET
LOCATION 's3://<DATA_BUCKET>/silver/payments/';

-- Descubrir particiones
MSCK REPAIR TABLE <GLUE_DB>.customers_silver;
MSCK REPAIR TABLE <GLUE_DB>.orders_silver;
MSCK REPAIR TABLE <GLUE_DB>.payments_silver;
