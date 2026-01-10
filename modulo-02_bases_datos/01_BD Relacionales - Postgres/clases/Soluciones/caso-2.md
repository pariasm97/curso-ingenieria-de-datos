# Enunciado

Los dueños de un pequeño taller de reparación de computadores quieren llevar un registro de los trabajos de reparación de los equipos que arreglan, de los elementos usados en cada trabajo de reparación, de los costos de mano de obra de cada trabajo, de los técnicos que realizan cada reparación y del costo total de cada trabajo de reparación.

Cuando los clientes llevan sus computadores para ser reparados, hacen un depósito por el trabajo de reparación y se les da una fecha para regresar y retirar su computador. Luego los técnicos realizan las reparaciones en los computadores de los clientes según el trabajo de reparación, y detallan los costos de mano de obra y los elementos usados en cada trabajo.

Cuando los clientes regresan, pagan el costo total del trabajo de reparación menos el depósito, reciben un comprobante de pago y retiran el computador reparado usando ese comprobante.

## Matriz de entidades

| Entidad ↓ / → | Clientes | Computadores | TrabajosReparacion | Facturas | Depositos | Tecnicos | DetallesReparacion | Items |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Clientes** | - | Tienen | - | - | - | - | - | - |
| **Computadores** | - | - | Repara | - | - | - | - | - |
| **TrabajosReparacion** | - | - | - | Generan | Reciben | Hacen | Contienen | - |
| **Facturas** | - | - | - | - | - | - | - | - |
| **Depositos** | - | - | - | - | - | - | - | - |
| **Tecnicos** | - | - | - | - | - | - | - | - |
| **DetallesReparacion** | - | - | - | - | - | - | - | Usan |
| **Items** | - | - | - | - | - | - | - | - |

## Matriz de cardinalidades

| Entidad (Origen) ↓ | Clientes | Computadores | TrabajosReparacion | Facturas | Depositos | Tecnicos | DetallesReparacion | Items |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Clientes** | - | 1:N | - | - | - | - | - | - |
| **Computadores** | 1:1 | - | 1:1 | - | - | - | - | - |
| **TrabajosReparacion** | - | 1:1 | - | 1:1 | 1:N | 1:1 | 0:N | - |
| **Facturas** | - | - | 1:1 | - | - | - | - | - |
| **Depositos** | - | - | 1:1 | - | - | - | - | - |
| **Tecnicos** | - | - | 0:N | - | - | - | - | - |
| **DetallesReparacion** | - | - | 1:1 | - | - | - | - | 1:1 |
| **Items** | - | - | - | - | - | - | 0:N | - |

## Diagrama de entidad-relación

[Visualizar en draw.io](https://drive.google.com/file/d/1SsrUNAMbSANE5LrLEpckvz9nw7VtEqSS/view?usp=sharing)

## Argumentación sobre Gestión de Pagos

Decisión: Relacionar la entidad Depositos con TrabajosReparacion (1:N) en lugar de relacionarlos con Facturas o Clientes. 

Justificación: 

1. El depósito ocurre desde el día 1, momento en el cual la Factura final no existe todavía. Relacionarlo con el Trabajo garantiza la integridad referencial desde el inicio.

2. Al establecer una relación 1:N, permitimos que no solo se pueda realizar un depósito, sino que queda preparado para aceptar múltiples abonos si el cliente lo necesitara.


