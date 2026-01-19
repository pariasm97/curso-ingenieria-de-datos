# Actividad Práctica: Arquitecturas de Big Data en AWS
## Despliegue de EMR, EC2, Kubernetes y Serverless

### Objetivo General
Comprender el impacto de las decisiones de arquitectura (costo, rendimiento, resiliencia y modernización) mediante la experimentación práctica con configuraciones variadas de AWS EMR, EKS y Serverless.

---

### Equipo 1: "Los Ahorradores" (Cost Optimization)
**Misión:** Desplegar el clúster más económico posible y probar su resistencia ante interrupciones.

* **Infraestructura:** AWS EMR sobre EC2.
* **Configuración de Instancias:**
    * **Modelo:** Instance Fleets (no Instance Groups).
    * **Estrategia de Compra:** 100% Spot Instances (Task y Core nodes).
* **Almacenamiento:** EMRFS (S3) estricto. Prohibido usar HDFS para datos persistentes.
* **Experimento:**
    1.  Lanzar un trabajo de Spark de larga duración.
    2.  Simular una interrupción: Terminar manualmente una instancia del grupo *Task* desde la consola EC2.
* **Pregunta:** ¿El trabajo sobrevivió a la "muerte" del nodo? ¿Cuál es el ahorro estimado vs. el Equipo 2?

---

### Equipo 2: "Rendimiento Puro" (High Performance & HDFS)
**Misión:** Maximizar la velocidad de I/O simulando un entorno crítico (SLA bancario).

* **Infraestructura:** AWS EMR sobre EC2.
* **Configuración de Instancias:**
    * **Familia:** Instancias optimizadas para memoria (`r5` o `r6i`).
    * **Estrategia de Compra:** 100% On-Demand (Sin riesgo de interrupción).
* **Almacenamiento:** HDFS Nativo (usando los discos EBS/Instance Store de los nodos).
* **Experimento:**
    1.  Ejecutar un trabajo con alto "Shuffle" de datos escribiendo en HDFS.
    2.  Terminar el clúster al finalizar.
* **Pregunta:** ¿Qué sucede con los datos procesados si olvidaron copiarlos a S3 antes de apagar el clúster? (Contraste con Equipo 1).

---

### Equipo 3: "Los Modernos" (Arquitectura ARM/Graviton)
**Misión:** Evaluar la nueva generación de procesadores y compatibilidad de software.

* **Infraestructura:** AWS EMR sobre EC2.
* **Configuración de Instancias:**
    * **Familia:** Instancias `g` (ej. `m7g.xlarge`, `r7g.xlarge`) con procesadores AWS Graviton (ARM64).
* **Configuración de Software:** Asegurar versiones compatibles de Spark/Java.
* **Experimento:**
    1.  Intentar instalar una librería binaria compilada para x86 mediante un Bootstrap Action (provocar error controlado).
    2.  Corregir y comparar tiempos de ejecución vs. instancias Intel tradicionales.
* **Pregunta:** ¿Es real la mejora de precio-rendimiento del 20% que promete AWS con Graviton?

---

### Equipo 4: "Cloud Native" (EMR on EKS)
**Misión:** Desacoplar el cómputo del servidor utilizando contenedores gestionados por EMR.

* **Infraestructura:** Amazon EKS (Kubernetes) + EMR on EKS Virtual Cluster.
* **Despliegue:**
    * No usan consola de EC2.
    * Envían trabajos mediante `aws emr-containers start-job-run`.
* **Experimento:**
    1.  Lanzar 5 trabajos pequeños de Spark simultáneamente.
    2.  Observar cómo EMR crea y destruye Pods automáticamente.
* **Pregunta:** ¿Cómo cambia la gestión de recursos cuando Spark corre como un Pod de Kubernetes en lugar de un servidor dedicado?

---

### Equipo 5: "Automatización" (Bootstrap & Auto-Scaling)
**Misión:** Crear un clúster tradicional que "respire" (crezca y se encoja).

* **Infraestructura:** AWS EMR sobre EC2.
* **Personalización:**
    * **Bootstrap Action:** Script `.sh` que instale `git`, `htop` y clone un repositorio privado al iniciar.
    * **Auto-Scaling:** Política agresiva (ej. "Si CPU > 50% por 1 min, agregar 2 nodos").
* **Experimento:**
    1.  Ejecutar un script de Python en bucle para estresar la CPU.
    2.  Observar los logs de CloudWatch para ver el evento de escalado.
* **Pregunta:** ¿Cuánto tiempo tarda el clúster en reaccionar y estar listo para procesar?

---

### Equipo 6: EMR Serverless
**Misión:** Ejecutar trabajos  sin configurar ni un solo servidor.

* **Infraestructura:** AWS EMR Serverless (Applications).
* **Configuración:**
    * Crear una "Application" de Spark con límites de pre-inicialización.
    * No hay instancias EC2, no hay SSH, no hay Bootstrap Actions tradicionales.
* **Experimento:**
    1.  Enviar el mismo trabajo que el Equipo 1.
    2.  Comparar el tiempo de "arranque en frío" (Cold Start) vs el Equipo 4.
* **Pregunta:** ¿Es realmente más fácil? ¿Qué pierdes al no tener acceso al sistema operativo (SSH)?

---

### Equipo 7: "Los Artesanos" (DIY Spark on Kubernetes)
**Misión:** Montar Spark "a mano" en Kubernetes sin la ayuda de EMR.

* **Infraestructura:** Amazon EKS (Kubernetes) estándar.
* **Despliegue:**
    * Instalar el **Spark Operator** de Google o usar `spark-submit` nativo con imagen Docker propia.
    * No usar las APIs de EMR.
* **Experimento:**
    1.  Construir una imagen de Docker con PySpark y sus dependencias.
    2.  Desplegarla manualmente en el clúster.
* **Pregunta:** ¿Cuánto más difícil fue configurar esto comparado con el Equipo 4 (EMR on EKS)? ¿Qué ventaja tiene controlar tu propia imagen de Docker?

---

### Tabla Comparativa Final (Para completar en clase)

| Equipo | Arquitectura | Tiempo Despliegue | Nivel de Control (OS) | Complejidad Gestión |
| :--- | :--- | :--- | :--- | :--- |
| **1. Spot** | EMR + EC2 Spot | Lento | Alto (Root) | Media |
| **2. Perf.** | EMR + EC2 HDFS | Medio | Alto (Root) | Media |
| **3. ARM** | EMR + Graviton | Medio | Alto (Root) | Media |
| **4. EKS** | EMR on EKS | Rápido | Medio (Container) | Alta (K8s) |
| **5. Auto** | EMR Scalable | Lento | Alto (Root) | Alta |
| **6. Srvls** | EMR Serverless | **Inmediato** | **Nulo** | **Muy Baja** |
| **7. DIY** | K8s Vanilla | Rápido | Alto (Docker) | **Muy Alta** |