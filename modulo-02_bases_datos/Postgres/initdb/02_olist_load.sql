-- 02_olist_load.sql

\connect olist;

-- Cargar clientes
\COPY olist_customers
FROM '/data/olist/olist_customers_dataset.csv'
WITH (FORMAT csv, HEADER true);

-- Cargar órdenes
\COPY olist_orders
FROM '/data/olist/olist_orders_dataset.csv'
WITH (FORMAT csv, HEADER true);

-- Cargar items de las órdenes
\COPY olist_order_items
FROM '/data/olist/olist_order_items_dataset.csv'
WITH (FORMAT csv, HEADER true);

-- Cargar pagos
\COPY olist_order_payments
FROM '/data/olist/olist_order_payments_dataset.csv'
WITH (FORMAT csv, HEADER true);
