# Enunciado

Los dueños de un pequeño taller de reparación de computadores quieren llevar un registro de los trabajos de reparación de los equipos que arreglan, de los elementos usados en cada trabajo de reparación, de los costos de mano de obra de cada trabajo, de los técnicos que realizan cada reparación y del costo total de cada trabajo de reparación.

Cuando los clientes llevan sus computadores para ser reparados, hacen un depósito por el trabajo de reparación y se les da una fecha para regresar y retirar su computador. Luego los técnicos realizan las reparaciones en los computadores de los clientes según el trabajo de reparación, y detallan los costos de mano de obra y los elementos usados en cada trabajo.

Cuando los clientes regresan, pagan el costo total del trabajo de reparación menos el depósito, reciben un comprobante de pago y retiran el computador reparado usando ese comprobante.

## Matriz de entidades

| Entidades | TrabajosReparacion | Computadores | Items | Tecnicos | Clientes | Depositos | Facturas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TrabajosReparacion** | | | | hacen | solicitan | | genera |
| **Computadores** | | | | | tienen | | |
| **Items** | | | | usan | | | |
| **Tecnicos** | | | | | | | |
| **Clientes** | | | | | | hacen | |
| **Depositos** | | | | | | | |
| **Facturas** | | | | | | | |

## Matriz de cardinalidades

| Entidades | TrabajosReparacion | Computadores | Items | Tecnicos | Clientes | Depositos | Facturas |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TrabajosReparacion** | | | | 1:1 | 1:1 | | 1:1 |
| **Computadores** | | | | | 1:1 | | |
| **Items** | | | | 0:1 | | | |
| **Tecnicos** | 0:N | | 0:N | | | | |
| **Clientes** | 0:N | 1:N | | | | 1:1 | |
| **Depositos** | | | | | 1:1 | | |
| **Facturas** | 1:1 | | | | | | |

## Diagrama de entidad-relación

[Visualizar en draw.io](https://drive.google.com/file/d/1SsrUNAMbSANE5LrLEpckvz9nw7VtEqSS/view?usp=sharing)
