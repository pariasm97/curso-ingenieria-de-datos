# Prompt pack - Glue ETL (asistido)

Use estos prompts como base. Ajuste nombres de bucket, rutas y requisitos.

## Prompt 1 - Generar ETL base

Necesito un script de AWS Glue (PySpark) que lea un archivo CSV con header desde:

- INPUT_PREFIX: s3://<bucket>/raw/source=synthetic/dt=2026-01-16
- ENTITY: orders (archivo orders.csv)

Debe:
- Tipificar columnas y convertir order_ts a timestamp
- Escribir a Parquet en:
  - OUTPUT_PREFIX: s3://<bucket>/silver/orders/
- Particionar por source y dt
- Ser idempotente por particion (overwrite por dt)
- Incluir argumentos: INPUT_PREFIX, OUTPUT_PREFIX, SOURCE, DT, ENTITY
- Habilitar logs en CloudWatch

Devuelve el codigo completo listo para Glue 4.0.

## Prompt 2 - Robustez

Sobre el script anterior, agregue:
- Validacion de argumentos (faltantes, valores invalidos)
- Manejo de errores con mensajes claros
- Modo de lectura PERMISSIVE y columna de errores si aplica

## Prompt 3 - Optimizacion

Sobre el script anterior:
- Evite shuffles innecesarios
- Ajuste particiones de salida de forma razonable
- Documente decisiones en comentarios
