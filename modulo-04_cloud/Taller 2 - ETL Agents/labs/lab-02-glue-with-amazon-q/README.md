# Lab 02 - Glue asistido (prompts para Amazon Q)

## Objetivo

Usar un asistente de generacion de codigo (por ejemplo Amazon Q integrado en Glue Studio) para:

- Generar una primera version del ETL en PySpark
- Aplicar una lista de chequeos (calidad de codigo, idempotencia, particiones)
- Ejecutar y corregir

Este lab no crea recursos nuevos. Reutiliza el Glue Job del Lab 01.

## Actividad

1. Abra el script `labs/lab-01-glue-basics/src/glue_entity_raw_to_silver.py`.
2. En la interfaz de Glue, use el asistente para proponer cambios.
3. Use `prompts/prompt_pack.md` y `prompts/review_checklist.md`.
4. Ejecute el job para `orders` y valide.

## Entregables

- Prompt usado (texto)
- Diff (antes y despues) del script
- Evidencia de ejecucion correcta

## Limpieza

No hay recursos adicionales.
