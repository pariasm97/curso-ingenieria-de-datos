# Lab 04 - Bedrock Agent para Operacion del Pipeline (Action Groups)

## Objetivo

Crear un agente que pueda operar el pipeline ETL a traves de dos acciones verificables:

- `StartPipeline`: inicia una ejecucion de Step Functions con input (input_prefix, output_prefix, source, dt)
- `GetPipelineStatus`: consulta el estado por executionArn

En este lab se despliega la Lambda fulfillment y se configura el Action Group.

## Recursos incluidos

- OpenAPI: `openapi/etl_agent_openapi.yaml`
- Lambda: `src/bedrock_agent_fulfillment.py`
- CloudFormation: `infra/template.yaml`

## Pre-requisitos

- Lab 03 desplegado (State Machine)
- Lab 00 desplegado (bucket de artifacts)

## Paso 1. Empacar y subir la Lambda

Empaque el codigo en un zip con el nombre:

- `bedrock_agent_fulfillment.zip`

y subalo a:

- `s3://<ArtifactsBucketName>/lambdas/lab-04/bedrock_agent_fulfillment.zip`

Se incluye un zip listo en `dist/` si usted prefiere.

## Paso 2. Desplegar la Lambda (CloudFormation)

Despliegue `infra/template.yaml` con:

- ArtifactsBucketName = output Lab 00
- StateMachineArn = output Lab 03

Guarde el Output `FulfillmentLambdaArn`.

## Paso 3. Crear el agente en Bedrock (manual)

1. En Amazon Bedrock, cree un Agent con instrucciones:
   - Rol: use un rol que Bedrock pueda asumir segun su setup.
   - Instruccion sugerida:
     - "Eres un asistente de operaciones. Solo usas las acciones disponibles. Debes pedir los parametros faltantes. Siempre respondes con executionArn y estado."
2. Cree un Action Group:
   - Espec. OpenAPI: pegue el contenido de `openapi/etl_agent_openapi.yaml`
   - Fulfillment: seleccione la Lambda del stack (FulfillmentLambdaArn)
3. Publique una version del agente.

## Paso 4. Pruebas guiadas

Prueba A (start):

- "Inicia el pipeline para dt 2026-01-16, source synthetic. El input_prefix es s3://<DataBucket>/raw/source=synthetic/dt=2026-01-16 y el output_prefix es s3://<DataBucket>/silver"

Prueba B (status):

- "Consulta el estado para executionArn <...>"

## Entregables

- Evidencia de Action Group configurado (captura)
- Respuesta del agente con executionArn
- Consulta de estado hasta SUCCEEDED o FAILED

## Limpieza

Siga `CLEANUP.md`.
