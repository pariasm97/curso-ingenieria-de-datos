-- Crear tabla Iceberg de ejemplo (ajusta columnas a tu dataset)
-- Supón columnas: fecha TIMESTAMP, region VARCHAR, valor DOUBLE
CREATE TABLE IF NOT EXISTS iceberg.energy.demanda_horaria (
  fecha TIMESTAMP,
  region VARCHAR,
  valor DOUBLE
)
WITH (
  format = 'PARQUET',
  partitioning = ARRAY['year(fecha)', 'month(fecha)']
);
