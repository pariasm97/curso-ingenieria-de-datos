# Cleanup - Lab 03

1. Elimine el stack de CloudFormation del Lab 03.
2. Si creo tablas en Athena y desea limpiarlas:

```sql
DROP TABLE IF EXISTS <GLUE_DB>.customers_silver;
DROP TABLE IF EXISTS <GLUE_DB>.orders_silver;
DROP TABLE IF EXISTS <GLUE_DB>.payments_silver;
```
