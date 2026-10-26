-- Delivered purchases only; each purchase maps to a persistent unique customer ID.
-- ROW_NUMBER() identifies the first purchase per unique customer.
WITH ranked AS (
  SELECT order_id, customer_unique_id, customer_state, purchased_at,
         ROW_NUMBER() OVER (
             PARTITION BY customer_unique_id ORDER BY purchased_at, order_id
         ) AS order_number
  FROM delivered_orders
)
SELECT r.order_id, r.customer_unique_id, r.customer_state, r.purchased_at,
       f.purchased_at AS first_purchase_at, r.order_number
FROM ranked r
JOIN ranked f ON f.customer_unique_id=r.customer_unique_id AND f.order_number=1
ORDER BY r.customer_unique_id, r.order_number;
