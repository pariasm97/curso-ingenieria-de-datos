# Guía detallada: desplegar Apache Spark en Amazon EMR sobre EC2 (clúster “clásico”)

Esta guía te muestra cómo crear un **clúster EMR en EC2**, instalar **Spark**, ejecutar un **job PySpark** como *Step*, y dejarlo con **logs en S3**, buenas prácticas de **seguridad**, **escalado** y **costos**.

---

## 1) Cuándo elegir EMR en EC2 (vs EMR Serverless)
El modo **EMR on EC2** conviene cuando necesitas:
- Control fino de infraestructura (tipos de instancia, EBS, redes, bootstrap, paquetes nativos).
- Jobs largos o cargas compartidas por varios equipos en un clúster.
- Estrategias avanzadas de costo con **Instance Fleets** y **Spot**.

---

## 2) Arquitectura base (muy resumida)
Un clúster EMR típico tiene:
- **Primary (master)**: coordinación (YARN ResourceManager / Spark driver en algunos modos).
- **Core**: almacenamiento HDFS (si lo usas) y cómputo.
- **Task** (opcional): solo cómputo, ideal para elasticidad y Spot.

Puedes aprovisionar nodos con:
- **Instance Groups** (más simple, 1 tipo de instancia por grupo).
- **Instance Fleets** (más flexible, varios tipos de instancia y modelos de precio).  
  Referencia: “instance fleets” y “instance groups”. 

---

## 3) Prerrequisitos
- AWS CLI v2 instalado y autenticado.
- Un bucket S3 para scripts, datos, logs y outputs.
- Un VPC/Subnet donde lanzar el clúster (recomendado: subred privada con NAT si descargas dependencias).
- Un EC2 Key Pair si vas a entrar por SSH (opcional, pero útil).

---

## 4) Paso 1: crear bucket y prefijos recomendados en S3

Estructura sugerida:

- `s3://TU_BUCKET/emr-ec2/scripts/`
- `s3://TU_BUCKET/emr-ec2/data/`
- `s3://TU_BUCKET/emr-ec2/output/`
- `s3://TU_BUCKET/emr-ec2/logs/`

Ejemplo:

```bash
export AWS_REGION="us-east-1"
export BUCKET="tu-bucket-emr"
export PREFIX="emr-ec2"

aws s3 mb "s3://${BUCKET}" --region "${AWS_REGION}"

aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/scripts/"
aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/data/"
aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/output/"
aws s3api put-object --bucket "${BUCKET}" --key "${PREFIX}/logs/"
```

### Activar logs del clúster a S3 (recomendado)
EMR permite publicar **logs específicos del clúster en S3** (por ejemplo `s3://.../logs`). En consola aparece como “Publish cluster-specific logs to Amazon S3”. 

---

## 5) Paso 2: IAM roles requeridos (service role + instance profile)

Cada clúster EMR necesita:
- Un **service role** (para que EMR aprovisione recursos y haga tareas del servicio).
- Un rol para el **EC2 instance profile** (lo asumen las instancias del clúster para acceder a S3/otros servicios).  

Si quieres lo “default”, puedes crearlos con AWS CLI:

```bash
aws emr create-default-roles
```

Esto crea los roles por defecto (incluyendo `EMR_DefaultRole` y `EMR_EC2_DefaultRole`).  
Si planeas usar **Spot**, ten en cuenta el requisito de service-linked role para solicitudes Spot.

> Recomendación: aplica el principio de mínimo privilegio (S3 de scripts/data/output/logs, Glue si aplica, KMS si usas SSE-KMS).

---

## 6) Paso 3: elegir Release label y aplicaciones (Spark)
Al crear el clúster:
- Selecciona un **Release** (release label).
- En **Applications**, elige el bundle que incluya **Spark** (y lo que necesites: Hive, etc.).  

AWS documenta el flujo “Create a cluster with Apache Spark” en la consola.

---

## 7) Paso 4: crear el clúster (Consola)

### Opción A: “Quick options” (la más rápida)
1. EMR Console
2. **Create cluster** (Quick options)
3. Cluster name
4. Software configuration: Release
5. Applications: **Spark**
6. Hardware: elige instancia para Primary y Core
7. Security and access: roles IAM, EC2 key pair (opcional)
8. Logging: habilita logs a S3 (`s3://TU_BUCKET/.../logs`)
9. Create cluster

---

## 8) Paso 5: crear el clúster (AWS CLI)

### Variables
```bash
export AWS_REGION="us-east-1"
export SUBNET_ID="subnet-xxxxxxxx"
export KEY_NAME="tu-keypair"   # opcional
export RELEASE_LABEL="emr-7.x.x"  # ajusta a tu preferencia
```

### Ejemplo mínimo con Instance Groups (Spark instalado) y auto-terminate
```bash
aws emr create-cluster   --region "${AWS_REGION}"   --name "spark-emr-ec2-retail"   --release-label "${RELEASE_LABEL}"   --applications Name=Spark   --ec2-attributes SubnetId="${SUBNET_ID}",KeyName="${KEY_NAME}"   --log-uri "s3://${BUCKET}/${PREFIX}/logs/"   --instance-groups     InstanceGroupType=MASTER,InstanceCount=1,InstanceType=m5.xlarge     InstanceGroupType=CORE,InstanceCount=2,InstanceType=m5.xlarge   --auto-terminate
```

> El AWS CLI tiene ejemplos oficiales de `create-cluster` incluyendo Spark y opciones de red y auto-terminate.

### Alternativa: Instance Fleets (más flexible)
Si quieres mezclar tipos de instancia y usar Spot para Task/Core, usa **Instance Fleets** (ideal para optimizar costo y resiliencia).  

---

## 9) Paso 6: subir tu script PySpark y datos a S3

Ejemplo `retail_job.py` (lee CSV, agrega por producto, escribe Parquet):

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

    result = (df.groupBy("product_id")
                .agg(_sum("amount").alias("total_amount")))

    (result.write.mode("overwrite").parquet(output_path))
    spark.stop()
```

Sube a S3:

```bash
aws s3 cp retail_job.py "s3://${BUCKET}/${PREFIX}/scripts/retail_job.py"
aws s3 cp transacciones_retail_large.csv "s3://${BUCKET}/${PREFIX}/data/transacciones_retail_large.csv"
```

---

## 10) Paso 7: ejecutar el job como “Step” (Spark application)

### Opción A: Consola
En el clúster (estado **Waiting**):
- Tab **Steps**
- **Add step**
- Step type: **Spark application**
- Argumentos típicos: `spark-submit` apuntando al script en S3, más parámetros

AWS documenta cómo “Add a Spark step” desde la consola.

### Opción B: CLI (add-steps)
Ejemplo (ajusta `CLUSTER_ID`):

```bash
export CLUSTER_ID="j-XXXXXXXXXXXXX"

aws emr add-steps   --region "${AWS_REGION}"   --cluster-id "${CLUSTER_ID}"   --steps Type=Spark,Name="retail-etl",ActionOnFailure=CONTINUE,Args=[spark-submit,--deploy-mode,cluster,"s3://${BUCKET}/${PREFIX}/scripts/retail_job.py","s3://${BUCKET}/${PREFIX}/data/transacciones_retail_large.csv","s3://${BUCKET}/${PREFIX}/output/retail_parquet/"]
```

> La documentación de EMR describe el patrón de envío de pasos para Spark (`spark-submit`) y el subcomando `add-steps`.

---

## 11) Paso 8: ver logs y depurar

### Logs del clúster en S3
Si configuraste `--log-uri` o habilitaste logs en consola, EMR archiva logs en el bucket. Para verlos:
- Abre el bucket de logs en S3 y navega por las carpetas del clúster/step.

AWS explica cómo “View Amazon EMR log files” cuando están archivados en S3.

### Spark UI y YARN
- Puedes revisar el estado del Step en la pestaña **Steps** del clúster.
- Para diagnósticos de performance, la Spark UI (History Server) suele ser clave.

---

## 12) Seguridad: cifrado en tránsito y en reposo (recomendado)
EMR soporta **security configurations** para habilitar:
- Cifrado **at rest** (EBS local, y también EMRFS/S3).
- Cifrado **in transit** (TLS) en componentes que soportan cifrado.

AWS documenta las opciones de cifrado y cómo crear una security configuration reutilizable.

---

## 13) Escalado (3 enfoques)
1) **Manual**: ajustas el tamaño de Core/Task a mano.
2) **Automatic scaling con policy** (solo instance groups): escala según métricas.  
3) **Managed scaling**: EMR ajusta instancias/unidades según la carga (disponible para instance groups o fleets).  
   Buenas prácticas: mantener Core más estable y escalar principalmente con Task.

---

## 14) Optimización de costos (recomendaciones prácticas)
- **Auto-terminate** en clústeres “por job” para evitar costos al quedar idle (ejemplos del CLI lo muestran).
- Usa **Task nodes Spot** para elasticidad barata; deja Primary/Core en On-Demand si la carga lo exige.
- Si usas Instance Fleets, mezcla 2 o 3 tipos de instancia para mejorar probabilidad de capacidad Spot.

---

## 15) Checklist final (para que no falle el primer job)
- Roles IAM creados (service role + EC2 instance profile) y permisos S3 correctos.
- Subnet y security groups permiten salida si necesitas bajar dependencias.
- Logs a S3 habilitados.
- Script y datos están en S3 y la ruta está bien en `spark-submit`.
- Revisa el Step en consola y, si falla, abre logs en S3.

---

## Referencias (AWS docs)
- Create a cluster with Apache Spark (EMR on EC2)
- Add a Spark step / Spark submit step
- AWS CLI EMR examples (`create-cluster`, `add-steps`, `create-default-roles`)
- IAM roles for Amazon EMR (service role e instance profile)
- Encryption options / security configurations
- Managed scaling e automatic scaling
- View EMR log files en S3
