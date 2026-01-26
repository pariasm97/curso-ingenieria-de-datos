# Guía detallada: Amazon EMR on EKS (Spark en Kubernetes con runtime de EMR)

Esta guía explica, paso a paso, cómo **desplegar y ejecutar Apache Spark en Amazon EKS usando Amazon EMR on EKS** (API: `emr-containers`). Incluye **dos modelos de envío de trabajos** (StartJobRun y Spark Operator) y una opción para **trabajo interactivo** con endpoints (EMR Studio). 

---

## 1) ¿Qué es EMR on EKS y cuándo elegirlo?

**Amazon EMR on EKS** permite correr runtimes de EMR (por ejemplo Spark) **sobre un clúster EKS existente**, usando un **namespace de Kubernetes** como “unidad” lógica (un *virtual cluster*). 

**Cuándo conviene**
- Ya usas Kubernetes (EKS) y quieres **un pool compartido** para cargas batch, streaming, ML, etc.
- Quieres mantener gobernanza Kubernetes (namespaces, quotas, RBAC) y, a la vez, usar runtime de EMR.
- Quieres evitar clústeres EMR “clásicos” por aplicación y **aprovechar capacidad compartida**.

**Modelos de ejecución (elige uno o usa ambos)**
1. **StartJobRun (API/CLI `emr-containers`)**: ideal para batch y orquestación (Airflow, Step Functions, pipelines). 
2. **Spark Operator**: ideal para GitOps y operación nativa en Kubernetes (`kubectl apply` con CRD `SparkApplication`). Requiere EMR **6.10.0 o superior**. 

---

## 2) Conceptos clave 

- **EKS Cluster**: tu clúster Kubernetes.
- **Namespace**: aislamiento lógico dentro del clúster.
- **Virtual cluster (EMR on EKS)**: mapeo 1:1 entre un **namespace** y un “cluster” lógico para EMR. 
- **Job execution role (IAM)**: rol que asumen los pods (driver y executors) para acceder a S3, CloudWatch, Glue, etc. 
- **IRSA**: IAM Roles for Service Accounts, para entregar credenciales a pods sin llaves estáticas. 

---

## 3) Prerrequisitos

### Requisitos mínimos recomendados
- **EKS** operativo (con nodegroup).
- Instancias de nodos con recursos suficientes; AWS recomienda **m5.xlarge o superior** para evitar fallas por falta de recursos en demos iniciales. 
- **AWS CLI** actualizado (en varias secciones AWS indica usar la versión más reciente).
- **kubectl** y **eksctl**.
- Para Spark Operator: **Helm**.

### Variables que vas a usar
Ajusta estos valores y reutilízalos en comandos y archivos:

```bash
export AWS_REGION="us-east-1"
export EKS_CLUSTER_NAME="mi-eks"
export EMR_NAMESPACE="emr-workloads"
export VIRTUAL_CLUSTER_NAME="vc-emr-workloads"
export LOG_BUCKET="s3://mi-bucket-logs-emr-eks"
export CW_LOG_GROUP="/emr-on-eks/${EKS_CLUSTER_NAME}/${EMR_NAMESPACE}"
export JOB_EXEC_ROLE_NAME="EMRContainers-JobExecutionRole"
```

---

## 4) Paso a paso (modelo StartJobRun con `emr-containers`)

### Paso 4.1: Crea el namespace de Kubernetes

```bash
kubectl create namespace "${EMR_NAMESPACE}"
```

### Paso 4.2: Habilita el acceso del clúster para EMR on EKS (AuthN/AuthZ)

AWS ofrece dos rutas. La recomendada para **nuevos virtual clusters** es usar **EKS Cluster Access Management (CAM) con Access Entries**; además, AWS indica que el `aws-auth` ConfigMap está en desuso. 
#### Opción A (recomendada): EKS Access Entry (CAM) para nuevos virtual clusters

Prerrequisitos (según AWS):
- AWS CLI **2.15.3 o superior**
- EKS **1.23 o superior**
- `authenticationMode` del clúster en `API_AND_CONFIG_MAP` citeturn7view0turn7view1

Comandos guía:

```bash
aws eks describe-cluster --name "${EKS_CLUSTER_NAME}" --region "${AWS_REGION}"
# Si necesitas ajustar el modo de autenticación:
aws eks update-cluster-config \
  --name "${EKS_CLUSTER_NAME}" \
  --region "${AWS_REGION}" \
  --access-config authenticationMode=API_AND_CONFIG_MAP
```

**Nota importante**: La integración CAM aplica solo a **virtual clusters nuevos**; no migra virtual clusters existentes. citeturn7view0turn7view1

#### Opción B (compatibilidad): eksctl IAM identity mapping (automatiza RBAC y `aws-auth`)

```bash
eksctl create iamidentitymapping \
  --cluster "${EKS_CLUSTER_NAME}" \
  --namespace "${EMR_NAMESPACE}" \
  --service-name "emr-containers"
```

Este comando crea recursos RBAC y actualiza `aws-auth` para enlazar el Service Linked Role de EMR con el usuario `emr-containers`. citeturn7view0turn7view2

> Si ya estás en CAM y vas a crear un virtual cluster nuevo, normalmente no necesitas esta opción B.

### Paso 4.3: Habilita IRSA (IAM Roles for Service Accounts)

1) Verifica el OIDC issuer del clúster: citeturn1view4

```bash
aws eks describe-cluster \
  --name "${EKS_CLUSTER_NAME}" \
  --region "${AWS_REGION}" \
  --query "cluster.identity.oidc.issuer" \
  --output text
```

2) Asocia el proveedor OIDC con `eksctl`: citeturn1view4

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster "${EKS_CLUSTER_NAME}" \
  --approve
```

### Paso 4.4: Crea el Job Execution Role (IAM) y su política

AWS llama a este rol **job execution role**. Debe tener permisos para los recursos que el job necesita (por ejemplo S3 para datos y logs, CloudWatch Logs). citeturn3view0

Ejemplo (CLI) basado en el flujo de AWS, con *placeholders* que debes ajustar: citeturn3view0

```bash
cat <<'EOF' > emr-trust-policy.json
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
  --role-name "${JOB_EXEC_ROLE_NAME}" \
  --assume-role-policy-document file://emr-trust-policy.json
```

Política mínima típica (ajusta bucket y, si aplica, Glue, KMS, DynamoDB, etc.). AWS recomienda **acotar** el acceso, no abrir a todo S3. citeturn3view0

```bash
cat <<EOF > emr-job-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ReadWriteLogsAndData",
      "Effect": "Allow",
      "Action": ["s3:PutObject","s3:GetObject","s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::MI_BUCKET",
        "arn:aws:s3:::MI_BUCKET/*"
      ]
    },
    {
      "Sid": "AllowCloudWatchLogs",
      "Effect": "Allow",
      "Action": ["logs:PutLogEvents","logs:CreateLogStream","logs:DescribeLogGroups","logs:DescribeLogStreams"],
      "Resource": ["arn:aws:logs:*:*:*"]
    }
  ]
}
EOF

# Reemplaza MI_BUCKET por el bucket real (solo ejemplo)
aws iam put-role-policy \
  --role-name "${JOB_EXEC_ROLE_NAME}" \
  --policy-name "EMR-Containers-Job-Execution" \
  --policy-document file://emr-job-policy.json
```

### Paso 4.5: Actualiza la trust policy del job execution role para IRSA

Cuando usas IRSA, debes crear una relación de confianza entre el execution role y el service account administrado por EMR, que se crea automáticamente al enviar jobs. AWS provee un comando directo para esto: 
```bash
aws emr-containers update-role-trust-policy \
  --cluster-name "${EKS_CLUSTER_NAME}" \
  --namespace "${EMR_NAMESPACE}" \
  --role-name "${JOB_EXEC_ROLE_NAME}" \
  --region "${AWS_REGION}"
```

### Paso 4.6: Registra el namespace como Virtual Cluster en EMR

Un virtual cluster es un namespace registrado en EMR. 

```bash
aws emr-containers create-virtual-cluster \
  --name "${VIRTUAL_CLUSTER_NAME}" \
  --container-provider '{
    "id": "'"${EKS_CLUSTER_NAME}"'",
    "type": "EKS",
    "info": { "eksInfo": { "namespace": "'"${EMR_NAMESPACE}"'" } }
  }' \
  --region "${AWS_REGION}"
```

Para validar:

```bash
aws emr-containers list-virtual-clusters --region "${AWS_REGION}"
```

### Paso 4.7: Envía un job Spark (PySpark) con StartJobRun

AWS muestra dos formas: con `--cli-input-json` o pasando parámetros directamente. 

#### Ejemplo A: con archivo JSON (recomendado)

Crea `start-job-run-request.json` (plantilla basada en AWS): 

```json
{
  "name": "pyspark-demo",
  "virtualClusterId": "REEMPLAZA_VIRTUAL_CLUSTER_ID",
  "executionRoleArn": "REEMPLAZA_ARN_JOB_EXEC_ROLE",
  "releaseLabel": "emr-6.2.0-latest",
  "jobDriver": {
    "sparkSubmitJobDriver": {
      "entryPoint": "s3://REGION.elasticmapreduce/emr-containers/samples/wordcount/scripts/wordcount.py",
      "entryPointArguments": ["s3://mi-bucket/input", "s3://mi-bucket/output"],
      "sparkSubmitParameters": "--conf spark.executor.instances=2 --conf spark.executor.memory=2G --conf spark.executor.cores=2 --conf spark.driver.cores=1"
    }
  },
  "configurationOverrides": {
    "applicationConfiguration": [
      {
        "classification": "spark-defaults",
        "properties": { "spark.driver.memory": "2G" }
      }
    ],
    "monitoringConfiguration": {
      "persistentAppUI": "ENABLED",
      "cloudWatchMonitoringConfiguration": {
        "logGroupName": "MI_LOG_GROUP",
        "logStreamNamePrefix": "pyspark-demo"
      },
      "s3MonitoringConfiguration": { "logUri": "s3://MI_BUCKET_LOGS/emr-on-eks/" }
    }
  }
}
```

Notas:
- El `entryPoint` del ejemplo anterior usa el script público de AWS en `s3://REGION.elasticmapreduce/...`. 
- `persistentAppUI` habilita UI persistente (útil para depurar). 

Ejecuta el job:

```bash
aws emr-containers start-job-run \
  --cli-input-json file://./start-job-run-request.json \
  --region "${AWS_REGION}"
```

### Paso 4.8: Monitorea y administra job runs

AWS documenta estos comandos para gestionar jobs por CLI:

```bash
# Listar jobs
aws emr-containers list-job-runs \
  --virtual-cluster-id REEMPLAZA_VIRTUAL_CLUSTER_ID \
  --region "${AWS_REGION}"

# Describir job
aws emr-containers describe-job-run \
  --virtual-cluster-id REEMPLAZA_VIRTUAL_CLUSTER_ID \
  --id REEMPLAZA_JOB_RUN_ID \
  --region "${AWS_REGION}"

# Cancelar job
aws emr-containers cancel-job-run \
  --virtual-cluster-id REEMPLAZA_VIRTUAL_CLUSTER_ID \
  --id REEMPLAZA_JOB_RUN_ID \
  --region "${AWS_REGION}"
```

---

## 5) Opción alternativa: Spark Operator (modelo Kubernetes nativo)

Amazon EMR soporta el **Spark Operator** como modelo de envío en **EMR 6.10.0 o superior**. 

### Paso 5.1: Instala prerrequisitos (Helm) y autentica Helm contra ECR

AWS indica que debes autenticar Helm al registry ECR y luego instalar el chart del operador desde un OCI registry. 

```bash
# Reemplaza region-id y ECR-registry-account según tu región
aws ecr get-login-password --region region-id | helm registry login \
  --username AWS \
  --password-stdin ECR-registry-account.dkr.ecr.region-id.amazonaws.com
```

### Paso 5.2: Instala el Spark Operator con Helm

Ejemplo de AWS (ajusta región y versión del chart; AWS sugiere derivarla del release label): 

```bash
helm install spark-operator-demo \
  oci://895885662937.dkr.ecr.region-id.amazonaws.com/spark-operator \
  --set emrContainers.awsRegion=region-id \
  --version 7.12.0 \
  --namespace spark-operator \
  --create-namespace
```

Verifica instalación:

```bash
helm list --namespace spark-operator -o yaml
```

### Paso 5.3: Ejecuta una app con `SparkApplication` (ejemplo base)

AWS muestra un ejemplo `spark-pi.yaml` y el recurso `SparkApplication`. citeturn5view1

- Para usar **S3** como almacenamiento y que el runtime de EMR funcione bien, AWS sugiere agregar `hadoopConf` y `sparkConf` específicos. En EMR **7.2.0 o superior**, estas configuraciones vienen incluidas por defecto. citeturn5view1

Ejemplo: crea tu YAML y aplícalo:

```bash
kubectl apply -f mi_spark_app.yaml
kubectl describe sparkapplication mi-app --namespace spark-operator
```

---

## 6) Trabajo interactivo: EMR Studio con Interactive Endpoints (opcional)

Un **interactive endpoint** conecta EMR Studio con tu virtual cluster para trabajo interactivo.

- Requiere EMR release **6.7.0 o superior**.
- El tipo soportado es `JUPYTER_ENTERPRISE_GATEWAY`. 

Ejemplo (AWS):

```bash
aws emr-containers create-managed-endpoint \
  --type JUPYTER_ENTERPRISE_GATEWAY \
  --virtual-cluster-id REEMPLAZA_VIRTUAL_CLUSTER_ID \
  --name mi-endpoint \
  --execution-role-arn arn:aws:iam::111122223333:role/JobExecutionRole \
  --release-label emr-6.9.0-latest \
  --region "${AWS_REGION}"
```

AWS indica que este comando crea un certificado autofirmado para comunicación HTTPS entre EMR Studio y el servidor del endpoint.

---

## 7) Costos y sizing: dos recordatorios útiles

- En Spark Operator, AWS especifica que el cálculo de precio en EKS se basa en **vCPU y memoria consumidos**, incluyendo driver y executors, medido desde que se descarga la imagen hasta que termina el pod (redondeado al segundo). 
- Para pruebas iniciales, AWS recomienda nodos con recursos suficientes (ejemplo: **m5.xlarge o superior**) para evitar fallas por recursos. 

---

## 8) Checklist rápido de verificación

1. Namespace creado y accesible.
2. Acceso del clúster habilitado (CAM recomendado o identity mapping).
3. IRSA habilitado (OIDC provider asociado).
4. Job execution role creado con permisos mínimos necesarios.
5. Trust policy actualizada con `update-role-trust-policy`.
6. Virtual cluster creado (id disponible).
7. Job StartJobRun ejecuta y logs aparecen en CloudWatch/S3.

---

## 9) Referencias principales

- Getting started con EMR on EKS (virtual cluster y ejemplo wordcount). 
- Virtual clusters: crear, listar, describir. 
- IRSA en EMR on EKS. 
- Job execution role y trust policy (incluye comando `update-role-trust-policy`). 
- StartJobRun y JSON de ejemplo. 
- Gestión de job runs por CLI (list, describe, cancel). 
- Spark Operator: setup y getting started. 
- Cluster access: CAM recomendado y nota sobre `aws-auth` en desuso. 
