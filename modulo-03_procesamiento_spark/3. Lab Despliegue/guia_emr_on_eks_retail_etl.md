# Guía paso a paso: desplegar y ejecutar una ETL PySpark en **Amazon EMR on EKS** (EMR sobre Kubernetes)

Esta guía explica cómo ejecutar tu ETL PySpark en **Amazon EMR on EKS** (EMR “sobre Kubernetes”), usando:
- Un clúster **Amazon EKS** (Kubernetes administrado).
- Un **namespace** dedicado para EMR.
- Un **Virtual Cluster** de EMR asociado a ese namespace.
- Un **Job Execution Role** (IAM) con **IRSA** (OIDC) para acceso a S3/logs.
- Envío del job con `aws emr-containers start-job-run`.

> Nota: en la CLI de AWS, EMR on EKS se maneja con comandos `aws emr-containers ...`.

---

## 0) Arquitectura mínima

1. Subes datos y script a **S3**.
2. Creas un clúster **EKS**.
3. Creas un **namespace** (por ejemplo `emr-etl`).
4. Habilitas el acceso RBAC para EMR (`eksctl create iamidentitymapping ... emr-containers`).
5. Configuras **OIDC/IRSA** para que los pods asuman un rol IAM.
6. Creas el **Job Execution Role** con permisos a S3 y logs.
7. Creas un **Virtual Cluster** (EMR asociado a `EKS + namespace`).
8. Envías tu ETL con `start-job-run`.
9. Verificas estado y revisas logs.
10. Validación: output en S3 (Parquet).

---

## 1) Prerrequisitos

### 1.1 Herramientas locales
- AWS CLI v2
- `kubectl`
- `eksctl`

https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html#windows_kubectl


### 1.2 Permisos en AWS
Tu identidad debe poder crear/administrar:
- EKS, EC2/VPC (si creas infraestructura), IAM roles/policies, S3, CloudWatch Logs, EMR on EKS (`emr-containers`).

### 1.3 Región
Esta guía usa `us-east-1` en ejemplos; ajusta a tu región real.

---

## 2) Preparación: variables de entorno

En **Git Bash** (Windows) o en Linux/macOS:

```bash
export AWS_REGION="us-east-1"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

# EKS
export EKS_CLUSTER_NAME="etl-eks"
export EMR_NAMESPACE="emr-etl"

# EMR on EKS
export VIRTUAL_CLUSTER_NAME="etl-virtual-cluster"
export JOB_ROLE_NAME="EMRContainers-JobExecutionRole"

# S3 (debe ser globalmente único)
export S3_BUCKET="etl-cluster"
export S3_DATA_PREFIX="data"
export S3_CODE_PREFIX="code"
export S3_LOG_PREFIX="logs"
```

**Validación rápida (evita errores “Invalid length ... value: 0”):**

```bash
echo "AWS_REGION=[$AWS_REGION]"
echo "AWS_ACCOUNT_ID=[$AWS_ACCOUNT_ID]"
echo "EKS_CLUSTER_NAME=[$EKS_CLUSTER_NAME]"
echo "EMR_NAMESPACE=[$EMR_NAMESPACE]"
echo "S3_BUCKET=[$S3_BUCKET]"
```

> Si alguna variable sale vacía, no continúes: corrige antes.

---

## 3) S3: crea bucket y sube datos + script

### 3.1 Crear el bucket
> Si el bucket ya existe o no es tuyo, elige uno único (ej: `etl-cluster-tuusuario-123`).

**En `us-east-1`:**
```bash
aws s3 mb "s3://$S3_BUCKET" --region "$AWS_REGION"
```

### 3.2 Subir el CSV a S3

Coloca el archivo `transacciones_retail_large.csv` en tu carpeta actual y sube:

```bash
aws s3 cp ./transacciones_retail_large.csv "s3://$S3_BUCKET/$S3_DATA_PREFIX/transacciones_retail_large.csv"
```

### 3.3 Script ETL recomendado 


```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

if __name__ == "__main__":
    input_path = "s3://etl-cluster/data/transacciones_retail_large.csv"
    output_path = "s3://etl-cluster/data/output/"

    spark = SparkSession.builder.appName("retail-etl").getOrCreate()

    df = (spark.read
          .option("header", "true")
          .option("inferSchema", "true")
          .csv(input_path))

    result = (df.groupBy("producto_id")
                .agg(F.sum(F.col("cantidad").cast("long")).alias("total_cantidad")))

    result.write.mode("overwrite").parquet(output_path)
    spark.stop()
```

> IMPORTANTE: si tu bucket no se llama `etl-cluster`, ajusta `input_path/output_path` para que apunten a tu bucket real.

Sube el script:

```bash
aws s3 cp ./retail_etl.py "s3://$S3_BUCKET/$S3_CODE_PREFIX/retail_etl.py"
```

---

## 4) Crear el clúster EKS

Ejemplo con `eksctl` (ajusta tamaño/cantidad según carga):

```bash
eksctl create cluster \
  --name "$EKS_CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --version "1.29" \
  --managed \
  --nodes 3 \
  --node-type m5.xlarge
```

Valida:

```bash
kubectl get nodes
```

---

## 5) Crear namespace para EMR

```bash
kubectl create namespace "$EMR_NAMESPACE"
kubectl get ns | grep "$EMR_NAMESPACE"
```

---

## 6) Habilitar acceso de EMR al namespace (RBAC)

Esto crea los recursos RBAC necesarios y mapea el acceso para EMR en el namespace.

```bash
eksctl create iamidentitymapping \
  --cluster "$EKS_CLUSTER_NAME" \
  --service-name emr-containers \
  --namespace "$EMR_NAMESPACE"
```

---

## 7) Habilitar IRSA (OIDC provider) en el clúster

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster "$EKS_CLUSTER_NAME" \
  --approve
```

---

## 8) Crear el **Job Execution Role** (IAM) para EMR on EKS

### 8.1 Crear rol base (trust policy inicial)

Crea `emr-trust-policy.json`:

```json
cat > emr-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "elasticmapreduce.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
  --role-name "${JOB_ROLE_NAME}" \
  --assume-role-policy-document file://emr-trust-policy.json

```

Crea el rol:

```bash
aws iam create-role \
  --role-name "$JOB_ROLE_NAME" \
  --assume-role-policy-document file://emr-trust-policy.json
```

### 8.2 Adjuntar permisos mínimos para S3 + CloudWatch Logs

Crea `job-role-policy.json` (ajusta el bucket si aplica):

```json
cat > job-role-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadWriteForJob",
      "Effect": "Allow",
      "Action": ["s3:PutObject","s3:GetObject","s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::${S3_BUCKET}",
        "arn:aws:s3:::${S3_BUCKET}/*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:PutLogEvents",
        "logs:CreateLogStream",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": ["arn:aws:logs:*:*:*"]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name "${JOB_ROLE_NAME}" \
  --policy-name "EMR-Containers-Job-Execution" \
  --policy-document file://job-role-policy.json

```

Adjunta la política inline:

```bash
aws iam put-role-policy \
  --role-name "$JOB_ROLE_NAME" \
  --policy-name "EMR-Containers-Job-Execution" \
  --policy-document file://job-role-policy.json
```

### 8.3 Actualizar trust policy para IRSA (paso crítico)

AWS provee un comando para actualizar la trust policy al formato requerido para EMR on EKS:

```bash
aws emr-containers update-role-trust-policy \
  --cluster-name "$EKS_CLUSTER_NAME" \
  --namespace "$EMR_NAMESPACE" \
  --role-name "$JOB_ROLE_NAME"
```

Captura el ARN del rol:

```bash
export JOB_ROLE_ARN="$(aws iam get-role --role-name "$JOB_ROLE_NAME" --query Role.Arn --output text)"
echo "JOB_ROLE_ARN=[$JOB_ROLE_ARN]"
```

---

## 9) Crear el Virtual Cluster (EMR asociado al namespace)

```bash
export VIRTUAL_CLUSTER_ID="$(
  aws emr-containers create-virtual-cluster \
    --name "$VIRTUAL_CLUSTER_NAME" \
    --container-provider "{
      \"id\": \"$EKS_CLUSTER_NAME\",
      \"type\": \"EKS\",
      \"info\": { \"eksInfo\": { \"namespace\": \"$EMR_NAMESPACE\" } }
    }" \
    --region "$AWS_REGION" \
    --query "id" --output text
)"

echo "VIRTUAL_CLUSTER_ID=[$VIRTUAL_CLUSTER_ID]"
```

**Si te queda vacío, no sigas**: revisa región, permisos y el paso RBAC (Sección 6).

---

## 10) Elegir un EMR release label

Lista labels disponibles en tu región:

```bash
aws emr list-release-labels --region "$AWS_REGION" --output table
```

Define una (ejemplo):

```bash
export EMR_RELEASE_LABEL="emr-7.12.0-latest"
```

> Si ese label no existe en tu región, elige uno de la lista.

---

## 11) Crear el request `start-job-run-request.json`

Crea `start-job-run-request.json`:

https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/emr-eks-jobs-submit.html

```json
cat > start-job-run-request.json << EOF
{
  "name": "retail-etl",
  "virtualClusterId": "${VIRTUAL_CLUSTER_ID}",
  "executionRoleArn": "${JOB_ROLE_ARN}",
  "releaseLabel": "${EMR_RELEASE_LABEL}",
  "jobDriver": {
    "sparkSubmitJobDriver": {
      "entryPoint": "s3://${S3_BUCKET}/${S3_CODE_PREFIX}/retail_etl.py",
      "sparkSubmitParameters": "--conf spark.executor.instances=2 --conf spark.executor.cores=2 --conf spark.executor.memory=4G --conf spark.driver.memory=2G"
    }
  },
  "configurationOverrides": {
    "monitoringConfiguration": {
      "persistentAppUI": "ENABLED",
      "s3MonitoringConfiguration": {
        "logUri": "s3://${S3_BUCKET}/${S3_LOG_PREFIX}/"
      }
    }
  }
}
EOF

```

Luego **reemplaza** (o regenera con bash) los campos:
- `virtualClusterId` = `$VIRTUAL_CLUSTER_ID`
- `executionRoleArn` = `$JOB_ROLE_ARN`
- `releaseLabel` = `$EMR_RELEASE_LABEL`
- `entryPoint` y `logUri` con tu bucket real

### Opción recomendada: generar el JSON desde variables (evita campos vacíos)

```bash
cat > start-job-run-request.json << EOF
{
  "name": "retail-etl",
  "virtualClusterId": "${VIRTUAL_CLUSTER_ID}",
  "executionRoleArn": "${JOB_ROLE_ARN}",
  "releaseLabel": "${EMR_RELEASE_LABEL}",
  "jobDriver": {
    "sparkSubmitJobDriver": {
      "entryPoint": "s3://${S3_BUCKET}/${S3_CODE_PREFIX}/retail_etl.py",
      "sparkSubmitParameters": "--conf spark.executor.instances=2 --conf spark.executor.cores=2 --conf spark.executor.memory=4G --conf spark.driver.memory=2G"
    }
  },
  "configurationOverrides": {
    "monitoringConfiguration": {
      "persistentAppUI": "ENABLED",
      "s3MonitoringConfiguration": {
        "logUri": "s3://${S3_BUCKET}/${S3_LOG_PREFIX}/"
      }
    }
  }
}
EOF
```

**Verifica que NO quedaron vacíos:**

```bash
python -c "import json;d=json.load(open('start-job-run-request.json'));print(d['virtualClusterId'], d['executionRoleArn'], d['releaseLabel'])"
```

---

## 12) Enviar el job y capturar el `JOB_RUN_ID`

Ejecuta y captura el ID automáticamente:

```bash
export JOB_RUN_ID="$(
  aws emr-containers start-job-run \
    --cli-input-json file://start-job-run-request.json \
    --region "$AWS_REGION" \
    --query "id" --output text
)"

echo "JOB_RUN_ID=[$JOB_RUN_ID]"
```

---

## 13) Monitoreo y debugging

### 13.1 Ver estado del job
```bash
aws emr-containers describe-job-run \
  --virtual-cluster-id "$VIRTUAL_CLUSTER_ID" \
  --id "$JOB_RUN_ID" \
  --region "$AWS_REGION" \
  --query "jobRun.{state:state,failureReason:failureReason,stateDetails:stateDetails}" \
  --output json
```

### 13.2 Listar jobs del virtual cluster
```bash
aws emr-containers list-job-runs \
  --virtual-cluster-id "$VIRTUAL_CLUSTER_ID" \
  --region "$AWS_REGION" \
  --output table
```

### 13.3 Ver pods en Kubernetes
```bash
kubectl get pods -n "$EMR_NAMESPACE"
```

Ver logs del driver (reemplaza el pod):

```bash
kubectl logs -n "$EMR_NAMESPACE" <driver-pod-name> --all-containers
```

### 13.4 Logs en S3 (si configuraste `logUri`)
```bash
aws s3 ls "s3://$S3_BUCKET/$S3_LOG_PREFIX/" --recursive | head -50
```

---

## 14) Validar output en S3

El script escribe Parquet en:

```bash
aws s3 ls "s3://$S3_BUCKET/$S3_DATA_PREFIX/output/" --recursive | head -50
```

---

## 15) Problemas comunes (los más frecuentes)

### 15.1 Variables vacías (tu caso anterior)
Síntoma:
- `Invalid length for parameter virtualClusterId, value: 0`
- `Invalid length for parameter id, value: 0`

Causa:
- `VIRTUAL_CLUSTER_ID` o `JOB_RUN_ID` no están exportados o el JSON se generó antes de exportarlos.

Solución:
- `echo` variables, regenere el JSON, capture el job run id con `--query id`.

### 15.2 Columna incorrecta en el groupBy
Síntoma:
- `UNRESOLVED_COLUMN... product_id cannot be resolved`

Causa:
- En tu CSV es `producto_id`.

Solución:
- Cambia a `groupBy("producto_id")` o normaliza/renombra columnas.

### 15.3 No hay output pero el job “parece” correr
Causas típicas:
- Escribes a un bucket/prefijo diferente al que estás inspeccionando.
- Error al escribir en S3 por permisos (`AccessDenied`).

Solución:
- `describe-job-run` para ver `failureReason`.
- Asegura `s3:PutObject` sobre `arn:aws:s3:::<bucket>/*`.

---

## 16) Limpieza (evitar costos)

1) Borra el virtual cluster:
```bash
aws emr-containers delete-virtual-cluster --id "$VIRTUAL_CLUSTER_ID" --region "$AWS_REGION"
```

2) Borra el clúster EKS:
```bash
eksctl delete cluster --name "$EKS_CLUSTER_NAME" --region "$AWS_REGION"
```

3) (Opcional) Borra objetos en S3 o el bucket:
```bash
aws s3 rm "s3://$S3_BUCKET/" --recursive
aws s3 rb "s3://$S3_BUCKET" --force
```

4) (Opcional) Limpia el rol IAM si no lo vas a reutilizar:
- Elimina la política inline y el rol.

---

## 17) Referencias oficiales (AWS)

- EMR on EKS: “Submit a job run with StartJobRun”  
  https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/emr-eks-jobs-submit.html

- “Managing virtual clusters”  
  https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/virtual-cluster.html

- `eksctl`: “Enabling Access for Amazon EMR”  
  https://docs.aws.amazon.com/eks/latest/eksctl/emr-access.html

- “Update the trust policy of the job execution role”  
  https://docs.aws.amazon.com/emr/latest/EMR-on-EKS-DevelopmentGuide/setting-up-trust-policy.html

- AWS CLI: `start-job-run` / `create-virtual-cluster` / `update-role-trust-policy`  
  https://docs.aws.amazon.com/cli/latest/reference/emr-containers/start-job-run.html  
  https://docs.aws.amazon.com/cli/latest/reference/emr-containers/create-virtual-cluster.html  
  https://docs.aws.amazon.com/cli/latest/reference/emr-containers/update-role-trust-policy.html
