# Laboratorios: ETL en AWS con Agentes (y n8n)

Este paquete contiene un set completo de laboratorios para ensenar ETL en AWS con un enfoque progresivo y orientado a operacion:

- ETL con AWS Glue (PySpark)
- Catalogo y validacion con Glue Data Catalog y Athena
- Orquestacion con AWS Step Functions
- Enfoque "agentic" para operaciones y soporte usando Amazon Bedrock Agents (Action Groups)
- Integracion con n8n (Webhook, carga a S3 y disparo de pipelines)

Ademas, incluye un dataset sintetico pequeno (para no depender de licencias externas) y plantillas de infraestructura (CloudFormation) para desplegar recursos con minimo privilegio.


## Requisitos

- Cuenta AWS con permisos para: S3, IAM (crear roles), Glue, Athena, Step Functions, Lambda y CloudWatch Logs.
- Para labs con Bedrock: acceso habilitado a Amazon Bedrock en la region elegida.
- Docker instalado (solo para Lab 07 con n8n).

## Orden recomendado

1. Lab 00: Bootstrap (S3, Glue DB, roles base, Athena workgroup)
2. Lab 01: Glue basics (CSV a Parquet particionado)
3. Lab 02: Glue con prompts para Amazon Q (asistido)
4. Lab 03: Step Functions orquestando Glue
5. Lab 04: Bedrock Agent para operaciones del pipeline
6. Lab 05: Troubleshooting guiado (fallas controladas)
7. Lab 06: Calidad de datos (reportes y hard-fail)
8. Lab 07: n8n como orquestador externo

## Convenciones

- Capas en S3:
  - `raw/` entrada tal cual
  - `silver/` parquet limpio y tipado
  - `gold/` agregados listos para BI
- Particiones sugeridas:
  - `dt=YYYY-MM-DD`
  - `source=...` (opcional)
- Logging:
  - CloudWatch Logs por Glue Job y por Lambda

## Despliegue rapido (CloudFormation)

Cada lab incluye su propio `infra/template.yaml` con parametros. En general:

- Despliegue primero `labs/lab-00-bootstrap/infra/template.yaml`
- Suba los scripts de Glue y Lambda a un bucket de "artifacts" (instrucciones en cada lab)
- Despliegue las plantillas siguientes apuntando a esos artifacts

Se incluye `tools/pack_and_upload.sh` para empacar y subir scripts al bucket.

## Costos y seguridad

- Este set evita recursos caros por defecto.
- Incluye parametros para limitar concurrencia y tamano.
- Limpie al final: cada lab tiene `CLEANUP.md`.

## Dataset

- `labs/lab-00-bootstrap/data/` contiene CSV sinteticos (customers, orders, payments).
- Se pueden reemplazar por Olist u otro dataset si usted lo prefiere.

## Como usar este paquete

- Abra cada lab en orden.
- Ejecute los pasos del README.
- Entregables y rubrica estan al final de cada README.

