# Lab 05 - Troubleshooting guiado (fallas controladas)

## Objetivo

Ejercitar diagnostico de fallas de un pipeline ETL orquestado (Step Functions + Glue), con evidencia trazable.

## Pre-requisitos

- Lab 03 (State Machine)
- Lab 01 (Glue Job)
- Opcional: Lab 04 (Agent con acciones StartPipeline y GetPipelineStatus)

## Escenario de falla 1 - Input path incorrecto

Inicie la ejecucion con un `input_prefix` que no existe (ejemplo: dt equivocado):

```json
{
  "input_prefix": "s3://<DataBucketName>/raw/source=synthetic/dt=2099-01-01",
  "output_prefix": "s3://<DataBucketName>/silver",
  "source": "synthetic",
  "dt": "2099-01-01"
}
```

Resultado esperado:
- Al menos una rama falla por archivo no encontrado.

## Escenario de falla 2 - Permisos

1. Quite temporalmente permisos S3 PutObject del rol de Glue (solo para el ejercicio).
2. Re-ejecute el pipeline.
3. Restablezca permisos.

Resultado esperado:
- Fallas de acceso (AccessDenied) visibles en logs.

## Paso 1. Obtener evidencia de falla

- Revise el ExecutionArn en Step Functions.
- Abra la ejecucion y mire el estado de las ramas.

## Paso 2. Diagnostico con script

Use `tools/diagnose_execution.py` para extraer el ultimo error desde el historial de Step Functions.

```bash
python tools/diagnose_execution.py --execution-arn "<ExecutionArn>"
```

## Paso 3. Diagnostico con Agente (opcional)

- Pida al agente: "Consulta el estado de executionArn ...".
- Si el estado es FAILED, pida: "Dime que parte fallo y que debo revisar".

Nota: si quiere una accion formal de diagnostico (endpoint /pipeline/diagnose), extienda el OpenAPI y la Lambda del Lab 04.

## Entregables

- ExecutionArn fallido
- Salida del script `diagnose_execution.py`
- Accion correctiva propuesta

## Limpieza

No hay recursos adicionales. Solo asegure devolver permisos si los modifico.
