Guía de Instalación: Apache Spark 4.x en Windows

Esta guía detalla los pasos para instalar **Apache Spark 4.0** (o versiones Preview/Beta de la rama 4.x) en un entorno local Windows, configurando correctamente las variables de entorno `SPARK_HOME` y `HADOOP_HOME`.

> **⚠️ CAMBIO IMPORTANTE EN SPARK 4:**
> A diferencia de versiones anteriores, Spark 4.0 requiere **Java 17** o superior. No funcionará correctamente con Java 8 o 11.

---

## 1. Prerrequisitos

### A. Java Development Kit (JDK) 17
Spark 4 corre sobre la JVM y requiere una versión moderna.
1.  Descarga **JDK 17** (o 21) desde [Eclipse Adoptium (Temurin)](https://adoptium.net/) o Oracle. https://www.oracle.com/java/technologies/downloads/#jdk21-windows
2.  Instálalo en una ruta sin espacios (ejemplo recomendado: `C:\Java\jdk-17`).

### B. Python
Necesario si planeas usar **PySpark**.
1.  Asegúrate de tener Python instalado (versión 3.9 o superior recomendada para Spark 4).
2.  Verifica en tu terminal escribiendo: `python --version`.

### C. 7-Zip
El archivo de Spark viene en formato `.tgz`, por lo que necesitarás [7-Zip](https://www.7-zip.org/) para descomprimirlo en Windows.

---

## 2. Descargar e Instalar Spark 4

1.  Ve al sitio oficial: [Spark Downloads](https://spark.apache.org/downloads.html).
2.  **Spark Release:** Selecciona la versión **4.0.0** (o la versión "Preview" si la estable aún no sale).
3.  **Package Type:** Selecciona **"Pre-built for Apache Hadoop 3.3 and later"**.
4.  Haz clic en el enlace de descarga `.tgz`.
5.  **Descomprimir:**
    * Usa 7-Zip para extraer el archivo. (Nota: A veces hay que extraer dos veces si es `.tar.gz`).
    * Mueve la carpeta resultante a la raíz de tu disco C y renómbrala a algo simple.
    * **Ruta final sugerida:** `C:\Spark`

---

## 3. Configurar Hadoop (Winutils)

Spark en Windows requiere binarios nativos de Windows para simular el sistema de archivos de Hadoop.

1.  Crea la siguiente estructura de carpetas en tu disco C:
    * `C:\Hadoop`
    * Dentro de esa, crea una carpeta llamada `bin`: `C:\Hadoop\bin`
2.  Descarga **`winutils.exe`** y **`hadoop.dll`**.
    * Dado que Spark 4 usa clientes de Hadoop 3 modernos, puedes usar los binarios de Hadoop 3.3.x o 3.4.x.
    * Repositorio confiable común: [cdarlint/winutils en GitHub](https://github.com/cdarlint/winutils). Ve a la carpeta `hadoop-3.3.5/bin` (o la más reciente disponible).
3.  Guarda los archivos `winutils.exe` y `hadoop.dll` dentro de **`C:\Hadoop\bin`**.

---

## 4. Configuración de Variables de Entorno

Este es el paso crítico para que el sistema encuentre `SPARK_HOME` y `HADOOP_HOME`.

1.  Presiona la tecla **Windows**, escribe **"Variables de entorno"** y abre la opción del sistema.
2.  Haz clic en **"Variables de entorno..."**.

### A. Crear Variables (Sección "Variables del sistema" o "Usuario")

Crea (o edita) las siguientes variables NUEVAS:

| Nombre de la Variable | Valor (Ruta Ejemplo) | Nota Importante |
| :--- | :--- | :--- |
| **JAVA_HOME** | `C:\Java\jdk-17` | Ruta raíz del JDK (sin la carpeta bin) |
| **SPARK_HOME** | `C:\Spark` | Ruta raíz donde descomprimiste Spark |
| **HADOOP_HOME** | `C:\Hadoop` | Ruta raíz de Hadoop (**NO** pongas la carpeta bin aquí) |
| **PYSPARK_PYTHON** | `python` | (Opcional) Fuerza a Spark a usar el python del sistema |

### B. Editar el PATH

1.  Busca la variable **Path** y dale a **Editar**.
2.  Agrega las siguientes rutas (una por línea):
    * `%JAVA_HOME%\bin`
    * `%SPARK_HOME%\bin`
    * `%HADOOP_HOME%\bin`
3.  Guarda y acepta todos los cambios.

---

## 5. Verificación

1.  Abre una **NUEVA** terminal (PowerShell o CMD) para que tome los cambios.
2.  Prueba las variables:
    ```cmd
    echo %SPARK_HOME%
    echo %HADOOP_HOME%
    ```
    *(Deben imprimir las rutas que configuraste)*.

3.  Ejecuta Spark Shell (Scala):
    ```cmd
    spark-shell
    ```
4.  Ejecuta PySpark (Python):
    ```cmd
    pyspark
    ```

Si ves el logo de Spark versión 4.x.x y un prompt de espera, **¡la instalación ha sido exitosa!**

---

## 6. Solución de Problemas Comunes

* **Error "Java heap space" o Java version:** Asegúrate de estar usando JDK 17+. Spark 4 no arrancará bien con Java 8.
* **Error `java.io.IOException: Could not locate executable null\bin\winutils.exe`:** Tu variable `HADOOP_HOME` está mal configurada o no pusiste el `winutils.exe` dentro de la subcarpeta `/bin`.
* **Permisos en C:\tmp\hive:** Si sale un error de permisos relacionado con Hive, ejecuta este comando en una terminal como Administrador:
    `winutils.exe chmod -R 777 C:\tmp\hive` (Crea la carpeta si no existe).