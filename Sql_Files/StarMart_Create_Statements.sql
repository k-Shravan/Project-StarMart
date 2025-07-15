DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

/*
=============================================================================
-- STARmart Retail Schema Overview
=============================================================================
This schema models the day-to-day operations of a retail convenience chain
with a focus on perishable inventory management, customer purchasing behavior,
staff tracking, and promotional discount logic.

KEY TABLES & RELATIONSHIPS:
-----------------------------------------------------------------------------
- `starmart_stores`: Master table for physical stores.
- `starmart_employees`: Staff per store; includes cashier linkages.
- `starmart_products`: Each product is associated with a specific store.
- `starmart_inventory`: Tracks real-time on-hand quantities of products.
- `starmart_inventory_lookup`: Defines restock quantities on given dates.
- `starmart_vendors`: Multiple vendors can supply the same product.
- `starmart_customers`: Holds customer membership and contact info.
- `starmart_orders`: Captures each individual item purchase by customers.
- `starmart_holiday_dates`: Stores dates for national or store holidays.
- `starmart_discount_dates`: Stores dates for non-holiday promotions.
- `starmart_inventory_log`: Audit trail for restocks and discards.
- `starmart_current_date`: Simulated date for time-aware triggers.
- `starmart_markup_discount`: Product-level pricing and discount strategy.
- `starmart_restock_dates`: Drives the restocking simulation schedule.
- `starmart_orders_summary`: Aggregated sales log per product and period.
=============================================================================
*/

-- 1. Store master table: One row per store
CREATE TABLE starmart_stores (
  store_id VARCHAR(25) PRIMARY KEY, -- Unique store identifier
  region VARCHAR(7),                -- Geographical region
  neighbourhood VARCHAR(15),
  pop_density INT,                  -- Population density around the store
  store_size VARCHAR(6),            -- e.g., Small/Med/Large
  parking_space VARCHAR(12),
  zip_codes INT                     -- Parking availability
);

-- 2. Store employees (linked to store_id)
CREATE TABLE starmart_employees (
  emp_id VARCHAR(25) PRIMARY KEY,
  store_id VARCHAR(25),             -- FK to starmart_stores
  "name" VARCHAR(35),
  "age" INT,
  gender VARCHAR(6),
  ph_num VARCHAR(16),
  email VARCHAR(75),
  address VARCHAR(100),
  department VARCHAR(16),
  "role" VARCHAR(24),               -- e.g., cashier, stocker
  hourly_rate DECIMAL(10, 2),
  CONSTRAINT fk_store_emp FOREIGN KEY (store_id) REFERENCES starmart_stores ON DELETE CASCADE
);

-- 3. Store-specific product catalog
CREATE TABLE starmart_products (
  product_id VARCHAR(25) PRIMARY KEY,
  store_id VARCHAR(25),             -- FK to starmart_stores
  category VARCHAR(24),
  subcategory VARCHAR(28),
  product_name VARCHAR(60),
  variant VARCHAR(59),       
  cost_price DECIMAL(10, 2),
  shelf_life INT,                   -- Shelf life in days
  rating DECIMAL(3, 1),             -- product rating
  CONSTRAINT fk_store_product FOREIGN KEY (store_id) REFERENCES starmart_stores ON DELETE CASCADE
);

-- 4. Current inventory on hand (1 row per product_id)
CREATE TABLE starmart_inventory (
    product_id VARCHAR(25),
    on_hand_qty INT NOT NULL,       -- Quantity available
    restock_date DATE,
    expiry_date DATE                -- Product expiration
);

-- 5. Ideal restock quantities per product per date
CREATE TABLE starmart_inventory_lookup (
    product_id        VARCHAR(25) NOT NULL,
    restock_date      DATE        NOT NULL,
    prod_lookup_qty   INT         NOT NULL,
    CONSTRAINT fk_invlk_product FOREIGN KEY (product_id) REFERENCES starmart_products ON DELETE CASCADE
);

-- 6. Vendor details per product
CREATE TABLE starmart_vendors (
  vendor_unique_id VARCHAR(25) PRIMARY KEY,
  vendor_id VARCHAR(25),            -- Business ID
  vendor_name VARCHAR(50),
  delivery_fee DECIMAL(10, 2),
  product_id VARCHAR(25),           -- FK to supplied product
  per_item_cost DECIMAL(10, 2),
  CONSTRAINT fk_vendor_product FOREIGN KEY (product_id) REFERENCES starmart_products ON DELETE CASCADE
);

-- 7. Customer profile and loyalty tier
CREATE TABLE starmart_customers (
  customer_id VARCHAR(25) PRIMARY KEY,
  "name" VARCHAR(50),
  "age" INT,
  gender VARCHAR(6),
  phone_number VARCHAR(16),
  email VARCHAR(75),
  address VARCHAR(100),
  recurring VARCHAR(30),           -- Frequency descriptor
  membership INT                  
);

-- 8. One row per item sold in an order
CREATE TABLE starmart_orders (
  line_order_id VARCHAR(25) PRIMARY KEY,
  order_id VARCHAR(25),             -- Group orders by this ID
  customer_id VARCHAR(25),
  product_id VARCHAR(25),
  store_id VARCHAR(25),
  cashier_id VARCHAR(25),           -- FK to employee who processed the order
  order_datetime TIMESTAMP NOT NULL,
  quantity INT NOT NULL,
  final_price DECIMAL(10, 2),       -- Final price after all discounts

  CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES starmart_products ON DELETE CASCADE 
);

-- 9. Dates marked as national or store holidays
CREATE TABLE starmart_holiday_dates (holiday_dates DATE UNIQUE);

-- 10. Dates for standard promotions (not holidays)
CREATE TABLE starmart_discount_dates (discount_dates DATE UNIQUE);

-- 11. Logs restock and expiration-based discards,  log_discard_date log_discard_quantity
CREATE TABLE starmart_inventory_log (
  product_id VARCHAR(25),
  restocked_date date,
  discarded_date DATE,
  log_quantity INT NOT NULL,
  vendor_unique_id VARCHAR(25),
  reason TEXT,
  CONSTRAINT fk_restock_products FOREIGN KEY (product_id) REFERENCES starmart_products ON DELETE CASCADE,
  CONSTRAINT fk_restock_vendor FOREIGN KEY (vendor_unique_id) REFERENCES starmart_vendors ON DELETE CASCADE
);

-- 12. Tracks the current simulation day (used by triggers)
CREATE TABLE starmart_current_date (current_sim_date DATE UNIQUE);

-- 13. Pricing rules and discounts per product
CREATE TABLE starmart_markup_discount (
  product_id VARCHAR(25),
  markup DECIMAL(5, 2),              -- Markup over cost
  normal_day_discount DECIMAL(5, 2),
  holiday_discount DECIMAL(5, 2),
  CONSTRAINT fk_markup_discount_products FOREIGN KEY (product_id) REFERENCES starmart_products ON DELETE CASCADE
);

-- 14. Dates when restocking is scheduled
CREATE TABLE starmart_restock_dates (restock_date DATE PRIMARY KEY);

-- Holiday Lookup
CREATE TABLE starmart_holiday_lookup(
    "date" DATE,
    holiday_name TEXT
);
