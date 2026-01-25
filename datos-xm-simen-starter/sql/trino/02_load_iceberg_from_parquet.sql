-- Cargar datos a Iceberg desde archivos Parquet del data lake (MinIO)
-- Si has escrito tus Parquet en s3://datalake/warehouse/stage/demanda/..., puedes crear una tabla externa temporal:
-- (Aquí mostramos un SELECT directo si montas los Parquet con Trino mediante un catálogo adicional; si no, inserta desde cliente Python)
-- Ejemplo: INSERT ... VALUES demo:
INSERT INTO iceberg.energy.demanda_horaria (fecha, region, valor) VALUES 
  (TIMESTAMP '2024-01-01 00:00:00', 'ALL', 100.0);
