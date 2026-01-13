# Guía detallada: desplegar y ejecutar PySpark en Amazon EMR Serverless (sin administrar clústeres)

Esta guía te lleva de cero a ejecutar un **job PySpark** en **Amazon EMR Serverless** usando **AWS CLI**, con logs en **S3** (y opcionalmente **CloudWatch Logs**) y con una receta de permisos IAM mínima.

---

## 1) Conceptos básicos (qué vas a crear)

- **EMR Serverless Application**: el “contenedor lógico” donde correrán tus jobs (tipo *spark*).
- **Job run**: una ejecución concreta que usa `sparkSubmit` (script `.py` o `.jar`) y un **runtime role**.
- **S3**: almacenas script, datos, salidas y (recomendado) logs.

---

## 2) Prerrequisitos

- AWS CLI v2 instalado y autenticado.
- Permisos para: S3, IAM (crear rol/policies), EMR Serverless (crear application y lanzar jobs).
- Una región (ejemplo: `us-east-1`).

---

## 3) Variables (recomendado)

En tu terminal define variables para no equivocarte:

```bash
export AWS_REGION="us-east-1"
export ACCOUNT_ID="123456789012"

export BUCKET="tu-bucket-emr-serverless"
export PREFIX="emr-serverless"

export APP_NAME="spark-retail-app"
export ROLE_NAME="JobRuntimeRoleForEmrServerless"
```

---

## 4) Paso 1: crear el bucket y carpetas recomendadas en S3

> Nota: usa el bucket **en la misma cuenta y región** donde corre el job.

```bash
aws s3 mb "s3://${BUCKET}" --region "${AWS_REGION}"

# “Carpetas” lógicas (S3 no tiene carpetas reales, pero el prefijo ayuda)
aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/scripts/"
aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/data/"
aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/output/"
aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/logs/"
```

---

## 5) Paso 2: crear el IAM runtime role (rol que asume el job)

### 5.1 Trust policy (quién puede asumir el rol)

Crea un archivo `trust-emr-serverless.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "emr-serverless.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

Crea el rol:

```bash
aws iam create-role   --role-name "${ROLE_NAME}"   --assume-role-policy-document file://trust-emr-serverless.json
```

### 5.2 Policy mínima para S3 (scripts, data, output, logs)

Crea `policy-s3-emr-serverless.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": ["arn:aws:s3:::${BUCKET}"]
    },
    {
      "Sid": "RWObjects",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": ["arn:aws:s3:::${BUCKET}/${PREFIX}/*"]
    }
  ]
}
```

Adjunta la policy como inline-policy:

```bash
aws iam put-role-policy   --role-name "${ROLE_NAME}"   --policy-name "S3AccessForEmrServerlessJobs"   --policy-document file://policy-s3-emr-serverless.json
```

> Opcionales (según tu caso):
> - Si usas Spark SQL con Glue Data Catalog: agrega permisos `glue:*` específicos.
> - Si tu bucket usa KMS (SSE-KMS): agrega permisos `kms:Encrypt`, `kms:Decrypt`, etc.

### 5.3 Permiso para “pasar” el rol (iam:PassRole)

El usuario/rol con el que ejecutas `start-job-run` debe tener permiso de `iam:PassRole` sobre este runtime role.

Ejemplo de policy (para adjuntar a tu usuario/rol operador) `policy-passrole.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}",
      "Condition": {
        "StringLike": {
          "iam:PassedToService": "emr-serverless.amazonaws.com"
        }
      }
    }
  ]
}
```

---

## 6) Paso 3: crear la EMR Serverless Application (tipo Spark)

> Necesitas un `release-label` compatible con Spark. Consulta los release labels disponibles en tu región/cuenta.

Crear la aplicación:

```bash
aws emr-serverless create-application   --region "${AWS_REGION}"   --name "${APP_NAME}"   --type spark   --release-label "TU_RELEASE_LABEL"
```

Guarda el `applicationId` que te retorna el comando (lo vas a usar para enviar jobs).

Opcional: listar aplicaciones:

```bash
aws emr-serverless list-applications --region "${AWS_REGION}"
```

---

## 7) Paso 4: preparar un job PySpark simple y subirlo a S3

Crea `retail_job.py` (ejemplo mínimo: lee CSV, agrega y escribe Parquet):

```python
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum as _sum

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    spark = SparkSession.builder.appName("retail-etl").getOrCreate()

    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .csv(input_path))

    # Ajusta columnas según tu dataset
    result = (df.groupBy("product_id")
                .agg(_sum("amount").alias("total_amount")))

    (result.write.mode("overwrite").parquet(output_path))
    spark.stop()
```

Sube el script y (si aplica) tus datos:

```bash
aws s3 cp retail_job.py "s3://${BUCKET}/${PREFIX}/scripts/retail_job.py"

# Si tienes el CSV local:
aws s3 cp transacciones_retail_large.csv "s3://${BUCKET}/${PREFIX}/data/transacciones_retail_large.csv"
```

---

## 8) Paso 5: enviar el job (StartJobRun)

### 8.1 Crear un request JSON (recomendado)

Crea `start-job-run.json`:

```json
{
  "applicationId": "TU_APPLICATION_ID",
  "executionRoleArn": "arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}",
  "jobDriver": {
    "sparkSubmit": {
      "entryPoint": "s3://${BUCKET}/${PREFIX}/scripts/retail_job.py",
      "entryPointArguments": [
        "s3://${BUCKET}/${PREFIX}/data/transacciones_retail_large.csv",
        "s3://${BUCKET}/${PREFIX}/output/retail_parquet/"
      ],
      "sparkSubmitParameters": "--conf spark.executor.instances=2 --conf spark.executor.cores=1 --conf spark.executor.memory=4g --conf spark.driver.cores=1 --conf spark.driver.memory=4g"
    }
  },
  "configurationOverrides": {
    "monitoringConfiguration": {
      "s3MonitoringConfiguration": {
        "logUri": "s3://${BUCKET}/${PREFIX}/logs/"
      }
    }
  }
}
```

Ejecuta:

```bash
aws emr-serverless start-job-run   --region "${AWS_REGION}"   --cli-input-json file://start-job-run.json
```

Guarda el `jobRunId` que retorna.

### 8.2 Logs en CloudWatch (opcional)

Si quieres logs también en CloudWatch, agrega dentro de `monitoringConfiguration`:

```json
"cloudWatchLoggingConfiguration": {
  "enabled": true,
  "logGroupName": "/emr-serverless/spark",
  "logStreamNamePrefix": "retail"
}
```

> Tip: crea el log group antes si tu política no permite creación automática.

---

## 9) Paso 6: monitorear y depurar

### 9.1 Ver estado del job

```bash
aws emr-serverless get-job-run   --region "${AWS_REGION}"   --application-id "TU_APPLICATION_ID"   --job-run-id "TU_JOB_RUN_ID"
```

Listar jobs recientes:

```bash
aws emr-serverless list-job-runs   --region "${AWS_REGION}"   --application-id "TU_APPLICATION_ID"
```

### 9.2 Obtener URL del Spark UI / History Server

```bash
aws emr-serverless get-dashboard-for-job-run   --region "${AWS_REGION}"   --application-id "TU_APPLICATION_ID"   --job-run-id "TU_JOB_RUN_ID"
```

---

## 10) Paso 7: validar output

Si escribiste Parquet:

```bash
aws s3 ls "s3://${BUCKET}/${PREFIX}/output/retail_parquet/" --recursive
```

---

## 11) Problemas típicos (y cómo resolverlos rápido)

1) **AccessDenied en logs o output**
- Revisa que `executionRoleArn` tenga `s3:PutObject` sobre `${PREFIX}/logs/*` y `${PREFIX}/output/*`.

2) **No arranca el job o falla al iniciar**
- Revisa `release-label`, `applicationId`, región y que el bucket esté en la misma región.

3) **Errores de memoria o recursos**
- Ajusta recursos con `sparkSubmitParameters` (`spark.executor.memory`, `spark.driver.memory`, cores, instances).
- Evita setear memoria dentro del script; hazlo en la llamada del job.

4) **Spark SQL/Glue falla**
- Agrega permisos mínimos a Glue Data Catalog en el runtime role (Get/Create/Update según lo que uses).

---

## 12) Limpieza (evitar costos y desorden)

- Si fue una prueba, borra prefijos de output/logs que no necesites.
- Puedes borrar la aplicación cuando termines:

```bash
aws emr-serverless delete-application   --region "${AWS_REGION}"   --application-id "TU_APPLICATION_ID"
```

---

## Apéndice: comandos útiles

Mostrar detalle de la aplicación:

```bash
aws emr-serverless get-application   --region "${AWS_REGION}"   --application-id "TU_APPLICATION_ID"
```

Detener/cancelar un job (si aplica a tu estado):

```bash
aws emr-serverless cancel-job-run   --region "${AWS_REGION}"   --application-id "TU_APPLICATION_ID"   --job-run-id "TU_JOB_RUN_ID"
```
