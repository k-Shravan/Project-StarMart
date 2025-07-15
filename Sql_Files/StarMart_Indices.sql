-- Indexes for starmart_employees
CREATE INDEX idx_emp_store_id ON starmart_employees(store_id);

-- Indexes for starmart_products
CREATE INDEX idx_prod_store_id ON starmart_products(store_id);
CREATE INDEX idx_prod_category_subcat ON starmart_products(category, subcategory);

-- Indexes for starmart_inventory
-- product_id is PK so no need; often filtered by expiry
CREATE INDEX idx_inv_expiry_date ON starmart_inventory(expiry_date);

-- Indexes for starmart_inventory_lookup
CREATE INDEX idx_invlk_product_date ON starmart_inventory_lookup(product_id, restock_date);

-- Indexes for starmart_vendors
CREATE INDEX idx_vendor_product_id ON starmart_vendors(product_id);

-- Indexes for starmart_customers
CREATE INDEX idx_cust_email ON starmart_customers(email);
CREATE INDEX idx_cust_phone ON starmart_customers(phone_number);

-- Indexes for starmart_orders
CREATE INDEX idx_order_customer_id ON starmart_orders(customer_id);
CREATE INDEX idx_order_product_id ON starmart_orders(product_id);
CREATE INDEX idx_order_store_id ON starmart_orders(store_id);
CREATE INDEX idx_order_datetime ON starmart_orders(order_datetime);

-- Indexes for starmart_inventory_log
CREATE INDEX idx_log_product_restock_date ON starmart_inventory_log(product_id, restocked_date);
CREATE INDEX idx_log_product_discarded_date ON starmart_inventory_log(product_id, discarded_date);
CREATE INDEX idx_log_vendor_id ON starmart_inventory_log(vendor_unique_id);

-- Index for simulated current date (only one row but indexed for fast checks)
CREATE UNIQUE INDEX idx_current_sim_date ON starmart_current_date(current_sim_date);

-- Indexes for starmart_markup_discount
CREATE INDEX idx_markup_product ON starmart_markup_discount(product_id);

-- Indexes for restock and event dates
CREATE INDEX idx_holiday_dates ON starmart_holiday_dates(holiday_dates);
CREATE INDEX idx_discount_dates ON starmart_discount_dates(discount_dates);
CREATE INDEX idx_restock_dates ON starmart_restock_dates(restock_date);

CREATE INDEX idx_starmart_inventory_product_expiry ON starmart_inventory (product_id, expiry_date);
