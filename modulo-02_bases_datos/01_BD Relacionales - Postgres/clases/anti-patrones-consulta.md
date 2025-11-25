# Antipatrón SQL: 


### *Fear of the Unknown* (miedo a los `NULL`)  

## 1. Idea central del antipatrón


> En lugar de usar `NULL` para representar valores desconocidos o no aplicables, los desarrolladores inventan “valores mágicos” (0, `-1`, `'N/A'`, `'1900-01-01'`, etc.) porque *no quieren* tratar con `NULL`.

Problemas que esto genera:

- Distorsiona los cálculos (promedios, conteos, etc.).
- Rompe la integridad referencial (claves foráneas “falsas”).
- Obliga a recordar convenciones ocultas (“en esta columna `-1` significa ‘desconocido’”).
- Nuevos miembros del equipo no entienden la semántica real de los datos.

Recomendación:

- **Usa `NULL` cuando el valor es realmente desconocido o no aplica.**
- Trátalo de forma explícita (`IS NULL`, `IS NOT NULL`, `COALESCE`…) en consultas y reportes.
- Evita “sobrecargar” valores numéricos o strings para significar “desconocido”.

---

## 2. Contexto: tablas relevantes de Olist

En el dataset de Olist usaremos principalmente:

- `olist_orders`
  - `order_delivered_customer_date` (fecha de entrega al cliente).
  - `order_approved_at`, `order_delivered_carrier_date`, etc.
- `olist_order_reviews`
  - `review_comment_message` (comentario de texto).
- `olist_order_payments`
  - `payment_type` (tipo de pago).

En estos campos es perfectamente normal que existan `NULL`:

- Pedidos no entregados, fecha de entrega desconocida.
- Reviews sin comentario, mensaje de texto inexistente.
- Registros de pago incompletos, tipo de pago faltante.

---

## 3. Ejemplo 1: fecha de entrega de pedidos

### 3.1. Modelo “sano” (usa `NULL`)

En `olist_orders`:

```sql
order_delivered_customer_date TIMESTAMP NULL


### Consulta Spaguetti 

SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    c.customer_city,
    c.customer_state,
    oi.product_id,
    oi.seller_id,
    oi.price,
    p.payment_type,
    p.payment_installments,
    p.payment_value,

    (
        SELECT AVG(r.review_score)
        FROM olist_order_reviews r
        WHERE r.order_id = o.order_id
    ) AS avg_review_score,

    (
        SELECT COUNT(*)
        FROM olist_order_items oi2
        WHERE oi2.order_id = o.order_id
    ) AS items_in_order,

    (
        SELECT SUM(p2.payment_value)
        FROM olist_order_payments p2
        WHERE p2.order_id = o.order_id
    ) AS total_payment_value,

    (
        SELECT DISTINCT
               CASE
                 WHEN o2.order_status = 'delivered' THEN 'GOOD'
                 WHEN o2.order_status = 'canceled' THEN 'BAD'
                 ELSE 'OTHER'
               END
        FROM olist_orders o2
        WHERE o2.order_id = o.order_id
    ) AS random_order_quality_flag

FROM
    olist_orders o,
    olist_customers c,
    olist_order_items oi,
    olist_order_payments p,
    (
        SELECT
            oc.customer_id AS sub_customer_id,
            COUNT(*) AS total_orders,
            MAX(oo.order_purchase_timestamp) AS last_order_ts
        FROM olist_orders oo
        JOIN olist_customers oc
          ON oo.customer_id = oc.customer_id
        WHERE
            oo.order_status IN ('delivered', 'shipped', 'invoiced', 'processing', 'canceled')
            AND oc.customer_city IS NOT NULL
            AND oc.customer_state IS NOT NULL
        GROUP BY
            oc.customer_id
        HAVING
            COUNT(*) >= 1
    ) weird_subquery
WHERE
    o.customer_id = c.customer_id
    AND o.order_id = oi.order_id
    AND o.order_id = p.order_id
    AND c.customer_id = weird_subquery.sub_customer_id

    AND (
        o.order_status = 'delivered'
        OR o.order_status = 'shipped'
        OR o.order_status = 'processing'
        OR (o.order_status = 'canceled' AND p.payment_value > 0)
    )
    AND (
        c.customer_state = 'SP'
        OR c.customer_state = 'RJ'
        OR (c.customer_state <> 'SP' AND c.customer_city LIKE '%rio%')
    )
    AND o.order_purchase_timestamp >= '2017-01-01'
    AND (
        o.order_approved_at IS NULL
        OR o.order_approved_at >= '2017-01-01'
    )

    -- EXISTS con join implícito y varias condiciones
    AND EXISTS (
        SELECT 1
        FROM olist_order_items oi3,
             olist_products pr
        WHERE oi3.order_id = o.order_id
          AND oi3.product_id = pr.product_id
          AND (
              pr.product_category_name = 'bed_bath_table'
              OR pr.product_category_name IS NULL
              OR pr.product_category_name ILIKE '%furniture%'
          )
    )
ORDER BY
    o.order_purchase_timestamp DESC,
    c.customer_state,
    c.customer_city,
    o.order_id;


--- 2 Ejemplo

WITH customer_orders AS (
    SELECT
        o.customer_id,
        COUNT(*) AS total_orders,
        MAX(o.order_purchase_timestamp) AS last_order_ts
    FROM olist_orders o
    GROUP BY o.customer_id
),

-- CTE innecesariamente separado solo para marear
payments_agg AS (
    SELECT
        p.order_id,
        SUM(p.payment_value) AS total_payment_value,
        MAX(p.payment_type) AS any_payment_type
    FROM olist_order_payments p
    GROUP BY p.order_id
)

SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,

    c.customer_city,
    c.customer_state,

    oi.product_id,
    oi.seller_id,
    oi.price,
    oi.freight_value,

    pa.total_payment_value,
    pa.any_payment_type,

    -- Join a CTE y subconsulta a la vez
    co.total_orders,
    co.last_order_ts,

    -- Promedio de review con LEFT JOIN y COALESCE raro
    COALESCE(r_avg.avg_review_score, 0) AS avg_review_score,

    -- Campo derivado con lógica excesiva
    CASE
        WHEN pa.total_payment_value IS NULL THEN 'NO_PAYMENT'
        WHEN pa.total_payment_value > 500 THEN 'HIGH_VALUE'
        WHEN pa.total_payment_value BETWEEN 100 AND 500 THEN 'MID_VALUE'
        ELSE 'LOW_VALUE'
    END AS payment_segment,

    -- Join redundante a sellers y a una vista derivada del mismo sellers
    s.seller_city,
    s.seller_state,
    s_region.seller_region,

    -- Subconsulta correlacionada adicional, innecesaria
    (
        SELECT COUNT(*)
        FROM olist_order_items oi_x
        WHERE oi_x.order_id = o.order_id
    ) AS items_count_redundant

FROM olist_orders o
INNER JOIN olist_customers c
    ON c.customer_id = o.customer_id

-- JOIN que podría estar resumido, pero se repite la tabla items
LEFT JOIN olist_order_items oi
    ON oi.order_id = o.order_id

-- JOIN a CTE de pagos agregados
LEFT JOIN payments_agg pa
    ON pa.order_id = o.order_id

-- JOIN a CTE de clientes-agregados
LEFT JOIN customer_orders co
    ON co.customer_id = c.customer_id

-- LEFT JOIN a una subconsulta agregada de reviews
LEFT JOIN (
    SELECT
        r.order_id,
        AVG(r.review_score) AS avg_review_score
    FROM olist_order_reviews r
    GROUP BY r.order_id
) r_avg
    ON r_avg.order_id = o.order_id

-- JOIN a sellers, que depende de items
LEFT JOIN olist_sellers s
    ON s.seller_id = oi.seller_id

-- JOIN redundante a una derivación de sellers
LEFT JOIN (
    SELECT DISTINCT
        s2.seller_id,
        CASE
            WHEN s2.seller_state = 'SP' THEN 'SP_MAIN'
            WHEN s2.seller_state IN ('RJ', 'MG') THEN 'SUDESTE'
            ELSE 'OTHER_REGION'
        END AS seller_region
    FROM olist_sellers s2
) s_region
    ON s_region.seller_id = s.seller_id

-- JOIN innecesario a geolocation solo para tener más ruido
LEFT JOIN olist_geolocation g
    ON g.geolocation_zip_code_prefix = c.customer_zip_code_prefix

WHERE
    o.order_status IN ('delivered', 'shipped', 'processing')
    AND (
        c.customer_state = 'SP'
        OR (c.customer_state = 'RJ' AND pa.total_payment_value > 200)
        OR (c.customer_state <> 'SP' AND g.geolocation_city ILIKE '%rio%')
    )
    AND o.order_purchase_timestamp >= '2017-01-01'
    AND (
        r_avg.avg_review_score IS NULL
        OR r_avg.avg_review_score >= 3
        OR (r_avg.avg_review_score < 3 AND co.total_orders > 5)
    )
ORDER BY
    o.order_purchase_timestamp DESC,
    c.customer_state,
    c.customer_city,
    o.order_id;
