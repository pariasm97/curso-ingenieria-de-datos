# Guía Definitiva: Despliegue de Aplicaciones Spark de Misión Crítica en Kubernetes (AWS EKS) – con soporte PySpark

Esta guía consolida las mejores prácticas de ingeniería de datos moderna para ejecutar Apache Spark sobre Kubernetes, con un enfoque específico en la infraestructura de AWS. El objetivo es lograr un entorno estable, escalable y eficiente en costos, superando los desafíos comunes de la naturaleza efímera de los contenedores.

---

## 1. Cambio de Paradigma: De YARN a Kubernetes

En una arquitectura de misión crítica, Kubernetes (K8s) actúa como el orquestador de recursos. A diferencia de los clústeres tradicionales (Hadoop/YARN), K8s ofrece:

- **Aislamiento Total:** Cada aplicación de Spark tiene su propia versión de librerías, Python y Java. No hay conflictos de dependencias entre equipos.
- **Elasticidad Real:** Los recursos se crean solo cuando el trabajo de datos lo requiere y se destruyen al finalizar.
- **Desacoplamiento:** El cómputo (EKS) está separado del almacenamiento (S3), permitiendo escalar independientemente.

---

## 2. Arquitectura de Referencia en AWS

Para producción, se recomienda la siguiente topología:

1. **Plano de Control:** Amazon EKS (Elastic Kubernetes Service).
2. **Cómputo (Nodos):** Instancias EC2 gestionadas por *Karpenter* o *Cluster Autoscaler*.
3. **Almacenamiento de Datos:** Amazon S3 (Data Lake) accedido vía protocolo `s3a`.
4. **Almacenamiento Intermedio (Shuffle):** Discos NVMe locales o volúmenes EBS gp3.
5. **Registro de Imágenes:** Amazon ECR (Elastic Container Registry).
6. **Seguridad:** IAM Roles for Service Accounts (IRSA).

---

## 3. Construcción de la Imagen Docker (Inmutabilidad) con soporte PySpark

**Regla de Oro:** Nunca instales dependencias en tiempo de ejecución (`pip install` al inicio). Rompe la reproducibilidad y ralentiza el escalado. Construye una imagen "Golden Image".

### Dockerfile Optimizado para AWS y PySpark

Puntos clave para PySpark:
- Asegurar `python3` y `pip3` dentro de la imagen.
- Asegurar que `python` apunte a `python3` (para evitar problemas con herramientas y scripts).
- Instalar dependencias Python de forma reproducible (idealmente en un `venv`).
- Mantener usuario no-root al final (seguridad).

```dockerfile
# Base oficial compatible con la versión deseada
FROM spark:3.5.0-scala2.12-java11-ubuntu

USER root

# 1. Herramientas del sistema, Python y utilidades
RUN apt-get update && apt-get install -y \
      python3 python3-pip curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Opcional pero recomendable: asegurar que "python" exista y apunte a python3
RUN ln -sf /usr/bin/python3 /usr/bin/python

# 2. Descargar Jars para integración con S3 (Hadoop-AWS)
# Las versiones deben coincidir exactamente con el Hadoop incluido en la imagen de Spark
WORKDIR $SPARK_HOME/jars
RUN curl -O https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar \
    && curl -O https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

# 3. Instalación de dependencias de Python (Pre-empaquetado)
# Recomendado: venv para aislar dependencias y evitar problemas de permisos
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# 4. Copiar código fuente de la aplicación
COPY src/ /app/src/

# Configurar usuario no-root por seguridad
USER 185
```

Notas:
- Si tu app PySpark usa varios módulos (no solo `main.py`), empaqueta dependencias Python (zip) y pásalas con `--py-files` (ver sección 6).
- Si no quieres `venv`, puedes instalar global, pero cuida permisos y reproducibilidad.

---

## 4. Gestión de Seguridad (IAM y RBAC)

Evita usar claves de acceso (`AWS_ACCESS_KEY`) en el código. Usa la identidad nativa de EKS.

### Paso 1: Configurar IRSA (IAM Roles for Service Accounts)

Crea una ServiceAccount en Kubernetes que asuma un rol de AWS con permisos a tus buckets de datos.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark-etl-sa
  namespace: data-processing
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/RolAccesoDatosS3
```

---

## 5. El Desafío del Almacenamiento y Shuffle

En K8s, si un pod muere, su disco se borra. Spark depende del "Shuffle" (intercambio de datos entre nodos). Si pierdes esos archivos, el trabajo falla o se recalcula desde cero.

### Estrategias de Almacenamiento

| Tipo | Rendimiento | Caso de Uso |
|---|---|---|
| emptyDir (RAM/Disco Nodo) | Medio | Trabajos pequeños sin mucho shuffle. |
| HostPath (NVMe Local) | Alto (Recomendado) | Instancias AWS familia "d" (ej. r5d.large). Máxima velocidad para datos temporales. |
| PVC (EBS gp3) | Medio-Alto | Cuando se necesita persistencia más allá del ciclo de vida del pod (raro en batch puros). |

---

## 6. Configuración de Despliegue (spark-submit) con PySpark

Este es el comando consolidado con banderas de optimización, estabilidad y soporte explícito de Python 3.

### Recomendación para PySpark
Asegura el intérprete de Python para driver y executors:

- `spark.pyspark.driver.python`
- `spark.pyspark.python`

Si usas `venv` dentro de la imagen (como en el Dockerfile), apunta al `python` dentro de ese entorno.

```bash
bin/spark-submit   --master k8s://https://<EKS_API_ENDPOINT>   --deploy-mode cluster   --name procesamiento-ventas-diario     # --- Configuración de Imagen y Seguridad ---
  --conf spark.kubernetes.container.image=123456789012.dkr.ecr.us-east-1.amazonaws.com/mi-spark-app:v2.0   --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark-etl-sa   --conf spark.kubernetes.namespace=data-processing     # --- PySpark: seleccionar Python 3 (driver y executors) ---
  # Si usas venv: /opt/venv/bin/python
  --conf spark.pyspark.driver.python=/opt/venv/bin/python   --conf spark.pyspark.python=/opt/venv/bin/python     # --- Estabilidad y Asignación Dinámica (Shuffle Tracking) ---
  # Permite escalar a 0 ejecutores si no hay trabajo, pero protege los datos de shuffle
  --conf spark.dynamicAllocation.enabled=true   --conf spark.dynamicAllocation.shuffleTracking.enabled=true   --conf spark.dynamicAllocation.minExecutors=2   --conf spark.dynamicAllocation.maxExecutors=50     # --- Gestión de Memoria (Evitar OOM Killer) ---
  # K8s mata el pod si se pasa del límite. Dar margen extra (overhead).
  --conf spark.driver.memory=4g   --conf spark.executor.memory=8g   --conf spark.kubernetes.memoryOverheadFactor=0.2     # --- Optimización S3 (Commit Protocol) ---
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem   --conf spark.hadoop.fs.s3a.aws.credentials.provider=com.amazonaws.auth.WebIdentityTokenCredentialsProvider   --conf spark.sql.sources.commitProtocolClass=org.apache.spark.internal.io.cloud.PathOutputCommitProtocol   --conf spark.sql.parquet.output.committer.class=org.apache.spark.internal.io.cloud.BindingParquetOutputCommitter     # --- Optimización de Costos (Spot Instances) ---
  # Driver en On-Demand (estable), Executors en Spot (barato)
  --conf spark.kubernetes.driver.node.selector.lifecycle=OnDemand   --conf spark.kubernetes.executor.node.selector.lifecycle=Ec2Spot     # --- Código PySpark ---
  local:///app/src/main.py
```

### Si tu PySpark usa varios módulos (recomendado)
Si `main.py` importa otros módulos (por ejemplo `src/lib/*.py`), empaquétalos en un zip y pásalo con `--py-files`:

```bash
# Ejemplo: empaquetar libs en tu pipeline antes de construir la imagen o en el repo
zip -r deps.zip src/lib

bin/spark-submit   ...   --py-files local:///app/src/deps.zip   local:///app/src/main.py
```

---

## 7. Checklist de Fiabilidad (Misión Crítica)

Para evitar fallos silenciosos o cuellos de botella en producción:

- **Shuffle Tracking:** Asegúrate de que `spark.dynamicAllocation.shuffleTracking.enabled` esté en `true`. Sin esto, al escalar hacia abajo, K8s borrará pods que contienen datos intermedios necesarios para la siguiente etapa.
- **Tolerancia a Fallos:** Configura `spark.task.maxFailures=4` (o más). En entornos con instancias Spot, es normal perder nodos; Spark debe reintentar la tarea sin fallar todo el trabajo.
- **Timeout de Red:** Aumenta `spark.network.timeout=120s`. Las redes virtuales en K8s pueden tener latencias pico que Spark interpreta erróneamente como fallos.
- **Batch Size de API:** Configura `spark.kubernetes.allocation.batch.size=10`. Evita saturar el servidor API de Kubernetes solicitando muchos pods de golpe.

---

## 8. Observabilidad

La interfaz de usuario (UI) de Spark muere con el Driver. Para analizar el rendimiento post-mortem:

- **Persistencia de Eventos:** Configura Spark para escribir logs en S3:  
  `spark.eventLog.dir=s3a://mi-bucket-logs/spark-events/`
- **Spark History Server:** Despliega un servicio independiente en EKS que lea de esa ruta de S3 para visualizar los planes de ejecución y cuellos de botella de trabajos pasados.
