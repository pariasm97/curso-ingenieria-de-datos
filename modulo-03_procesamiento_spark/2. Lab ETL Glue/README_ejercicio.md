# Ejercicio: ETL de Balanceos (Silver a Gold) con PySpark

## Qué vas a practicar
- Lectura de datasets Silver (ventas, stock, prioridades)
- Cálculo de demanda y oferta
- Asignación (matching) por prioridades
- Generación de un CSV final en Gold con nombre descriptivo y timestamp

## Archivos incluidos (datos simulados)
### Silver
- `silver/ventas.csv`
- `silver/stock.csv`
- `silver/prioridades.csv`

### Gold (referencia para comparar)
- `gold/ordenes_traslado_netsuite_ejemplo_20260114_000000.csv`

### Código
- `etl_balanceos_spark.py`

## Reglas del ejercicio
- Necesidad (`A_Reponer`) = suma de `Cantidad Vendida` por (Sucursal, SKU, Temporada) dentro de la ventana.
- Origen se prioriza por `prioridad_retiro` (menor es primero).
- Destino se prioriza por `prioridad_reposicion` (menor es primero).
- No se permiten traslados `DESDE` = `HACIA`.
- `ID EXT OT` = `OT-<ORIG_CORTO>-<DEST_CORTO>-<timestamp>-<secuencia>`.

## Ejecutar local
```bash
spark-submit etl_balanceos_spark.py \
  --sales_path /mnt/data/ejercicio_balanceos_silver_gold/silver/ventas.csv \
  --stock_path /mnt/data/ejercicio_balanceos_silver_gold/silver/stock.csv \
  --prior_path /mnt/data/ejercicio_balanceos_silver_gold/silver/prioridades.csv \
  --out_path /mnt/data/ejercicio_balanceos_silver_gold/gold \
  --window_days 15 \
  --single_file
```

## Debug rápido
- Si aparece una sola columna con todo el header, el separador no coincide. Cambia `--csv_sep_in`.
- Si falla por columna no encontrada, ejecuta `printSchema()` y confirma nombres exactos.
