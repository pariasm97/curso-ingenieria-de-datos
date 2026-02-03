HU3: Diseño e Implementación del Modelo Relacional (PostgreSQL)

Objetivo: Modelar los datos transaccionales (Clientes, Catálogo, Pedidos, Entregas) asegurando integridad referencial.

Paso 1: Definición del Esquema (DDL)
Debes crear 4 tablas principales. Utiliza el esquema proporcionado en la página 2 y 3 del documento para definir los tipos de datos correctos:

Tabla Clientes:

Definir id_cliente como Primary Key (PK) (tipo VARCHAR).

Asegurar que el campo zona acepte los valores permitidos: Norte, Sur, Oriente, Occidente, Centro.

Asegurar que tipo_cliente acepte: Retail, Farmacéutico, Supermercado, etc..

Tabla Catalogo:

Definir id_producto como PK.

Configurar precio como FLOAT y tipo_entrega como VARCHAR (validar valores: Same Day, Next Day, etc.).

Tabla Pedidos:

Definir id_pedido como PK.

Crear Foreign Keys (FK):


id_cliente referenciando a Clientes(id_cliente).


id_producto referenciando a Catalogo(id_producto).

El campo fecha debe ser TIMESTAMP (UTC-agnóstico).

Tabla Entregas:


Nota Importante: Esta tabla solo contiene pedidos no cancelados.

Definir id_pedido como FK referenciando a Pedidos(id_pedido).

Incluir campos para logística: conductor y vehiculo.

Paso 2: Script de Creación (SQL)
Escribe un script .sql que ejecute las sentencias CREATE TABLE en el orden correcto para evitar errores de llaves foráneas:

Crear Clientes y Catalogo (Tablas maestras).

Crear Pedidos (Tabla transaccional dependiente).

Crear Entregas (Tabla dependiente de Pedidos).

Paso 3: Carga de Datos de Prueba (DML)
El documento indica que AceleraTI entrega archivos CSV (clientes.csv, pedidos.csv, etc.).

Desarrolla un script (en Python con Pandas o SQL COPY) para ingestar estos CSVs en tu base de datos local o instancia RDS de prueba.


Validación: Ejecuta un COUNT(*) en cada tabla para verificar que coincida con los volúmenes esperados (~300 clientes, ~2000 pedidos).

HU4: Diseño del Modelo NoSQL (Datos IoT)

Objetivo: Almacenar datos de alta velocidad provenientes de sensores IoT (Temperatura, Ubicación).

Paso 1: Selección del Motor y Estrategia
Dado que la plataforma es en AWS, DynamoDB es la opción nativa recomendada, aunque MongoDB también es válido.

Análisis del dato: Son series de tiempo por vehículo. Necesitas consultas rápidas por vehículo y rango de fechas.

Paso 2: Diseño de la Tabla (Ejemplo DynamoDB)
Diseña la tabla Sensores optimizada para patrones de acceso de lectura/escritura intensiva:


Partition Key (PK): id_vehiculo (Permite distribuir la carga por camión).


Sort Key (SK): timestamp (Permite ordenar eventos cronológicamente y consultar rangos de tiempo).

Atributos:

latitud (Number)

longitud (Number)

temperatura (Number)


evento (String: "OK" o "TEMP_CRITICA").

Paso 3: Carga de Datos NoSQL (Scripting)
Utiliza el archivo sensores.csv provisto (que simula 10,000 eventos).

Crea un script (Python con boto3 para DynamoDB o pymongo para MongoDB) que:

Lea el CSV fila por fila.

Convierta cada fila en un objeto JSON.

Inserte el documento en la base de datos NoSQL.

Tip: Para DynamoDB, usa BatchWriteItem para optimizar costos y velocidad.

Entregables Finales para estas HU
Según la tabla de evaluación:

Documento de Diseño (modelo_datos_logidata.pdf):

Diagrama Entidad-Relación (DER) del modelo SQL.

Diagrama o descripción JSON del modelo NoSQL.

Justificación de los tipos de datos elegidos.

Código Fuente:

Scripts SQL (schema.sql).

Scripts de carga inicial (load_data.py).