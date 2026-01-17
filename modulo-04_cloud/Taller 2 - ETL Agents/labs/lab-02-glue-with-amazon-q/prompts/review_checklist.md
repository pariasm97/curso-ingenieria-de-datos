# Checklist de revision - codigo generado (ETL Glue)

## Correctitud

- Lee del path esperado
- Interpreta header correctamente
- Castea tipos (fechas, timestamps, numericos)
- No pierde columnas criticas (IDs)

## Idempotencia

- El modo de escritura garantiza re-ejecucion segura por particion
- No sobreescribe todo el dataset accidentalmente

## Particionado y layout

- Usa columnas de particion (source, dt)
- La ruta de salida es consistente por entidad

## Observabilidad

- Logs y metricas habilitadas
- Mensajes de error utiles (incluyen entidad, dt, input_path)

## Seguridad

- No hay credenciales hardcodeadas
- Usa parametros y roles de IAM
