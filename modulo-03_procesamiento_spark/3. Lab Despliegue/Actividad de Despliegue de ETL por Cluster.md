# Actividad Práctica: Arquitecturas de Vludyrt en AWS
## Despliegue de EMR, EC2 y Kubernetes con Escenarios Diferenciados

### Objetivo General
Comprender el impacto de las decisiones de arquitectura (costo, rendimiento, resiliencia y modernización) mediante la experimentación práctica con configuraciones variadas de AWS EMR y EKS.

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
**Misión:** Desacoplar el cómputo del servidor utilizando contenedores.

* **Infraestructura:** Amazon EKS (Kubernetes) + EMR on EKS.
* **Despliegue:**
    * No usar instancias EC2 directas para EMR.
    * Enviar trabajos como *Job Runs* virtualizados.
* **Experimento:**
    1.  Lanzar 5 trabajos pequeños de Spark simultáneamente.
    2.  Medir el tiempo de inicio de los Pods vs. el tiempo de arranque del clúster EC2 del Equipo 1.
* **Pregunta:** ¿Cómo cambia la gestión de recursos cuando Spark corre como un Pod de Kubernetes en lugar de un servidor dedicado?

---

### Equipo 5: "Automatización" (Bootstrap & Auto-Scaling)
**Misión:** Crear un clúster elástico y autoconfigurable.

* **Infraestructura:** AWS EMR sobre EC2.
* **Personalización:**
    * **Bootstrap Action:** Script `.sh` que instale `git`, `htop` y clone un repositorio privado al iniciar.
    * **Auto-Scaling:** Política agresiva (ej. "Si CPU > 50% por 1 min, agregar 2 nodos").
* **Experimento:**
    1.  Ejecutar un script de Python en bucle para estresar la CPU.
    2.  Observar los logs de CloudWatch para ver el evento de escalado.
* **Pregunta:** ¿Cuánto tiempo tarda el clúster en reaccionar y estar listo para procesar?

---

### Tabla Comparativa de Resultados (Para completar en clase)

| Equipo | Arquitectura | Tiempo Despliegue | Costo ($/h) | Resiliencia | Persistencia Datos |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Spot** | EMR + Spot Fleet | Lento | Bajo | Media | Alta (S3) |
| **2. Perf.** | EMR + HDFS | Medio | Alto | Baja | Baja (Local) |
| **3. ARM** | EMR + Graviton | Medio | Medio-Bajo | Media | Alta (S3) |
| **4. K8s** | EMR on EKS | Muy Rápido | Variable | Alta | Alta (S3) |
| **5. Auto** | EMR + Scaling | Lento (inicio) | Variable | Alta | Alta (S3) |