

## Herramientas a Instalar

Antes de iniciar, asegúrate de tener instaladas las siguientes herramientas en tu entorno local:

### Entorno base

| Herramienta | Descripción | Enlace de descarga |
|--------------|--------------|-------------------|
| **Git** | Control de versiones y colaboración en código. | [https://git-scm.com/downloads](https://git-scm.com/downloads) |
| **Anaconda o Miniconda** | Administración de entornos y paquetes. | [https://www.anaconda.com/](https://www.anaconda.com/) |
| **Visual Studio Code** | Editor de código recomendado. | [https://code.visualstudio.com/](https://code.visualstudio.com/) |

### Herramientas de ingeniería de datos

| Herramienta | Descripción | Instalación |
|--------------|-------------|-------------|
| **Docker Desktop** | Contenedores y despliegues locales. | [Instalar Docker](https://www.docker.com/get-started/) |
| **dbt Core** | Transformaciones SQL versionadas. | `pip install dbt-core dbt-postgres` |
| **Apache Airflow** | Orquestador de pipelines. | `pip install apache-airflow` |
| **PostgreSQL** | Base de datos relacional para prácticas. | [Descargar PostgreSQL](https://www.postgresql.org/download/) |
| **DBeaver o TablePlus** | Cliente SQL visual. | [DBeaver.io](https://dbeaver.io/) |
| **DataGriop (Opcional)** | Cliente SQL visual (Preferido personal, si tiene un correo educativo puede aplicar a la licencia) | [DBeaver.io](https://www.jetbrains.com/datagrip/) |

| **AWS CLI** | Acceso a servicios cloud. | `pip install awscli` |

---

## Prework: Preparación del Entorno

Antes del primer módulo, realiza los siguientes pasos:

### 1️⃣ Clona el repositorio del curso

```bash
git clone https://github.com/JEstebanMejiaV/curso-ingenieria-de-datos
cd curso-ingenieria-datos
```

### 2️⃣ Crea un entorno de trabajo con Conda

```bash
conda create -n ing_datos python=3.10
conda activate ing_datos
```

### 3️⃣ Instala dependencias del curso

```bash
pip install -r requirements.txt
```

*(El archivo `requirements.txt` será actualizado a lo largo del curso).*

### 4️⃣ Verifica la instalación

```bash
python --version
git --version
docker --version
airflow version
```

---

## Sugerencias

- Crea un directorio llamado `~/Desktop/Git/curso-ingenieria-de-datos` para mantener el repositorio limpio.
- Si usas **Windows**, ejecuta los comandos desde **Git Bash** o **Anaconda Prompt**.
- Si encuentras errores con `gpg` o `git commit`, desactiva la firma temporal con:
  ```bash
  git config --global commit.gpgsign false
  ```

---


