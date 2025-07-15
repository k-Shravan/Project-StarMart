/*
Trigger & Function Descriptions:

1. is_holiday (COMMENTED OUT): 
   - Checks if a given date is listed as a holiday in `starmart_holiday_dates`.

2. restock_and_cleanup:
   - Performs two main actions on restock days:
     a. Adds new inventory based on `starmart_inventory_lookup`.
     b. Removes expired/depleted stock and logs the restock/expiry events.

3. inventory_updater:
   - Deducts ordered quantities from inventory on a FIFO basis after an order is placed.

4. apply_order_item_discount (COMMENTED OUT):
   - Computes applicable discounts (holiday, normal, membership) and adjusts the final price for each order item.

5. scheduled_restock_and_cleanup:
   - Triggers the `restock_and_cleanup` function when a new simulation day is inserted that matches a scheduled restock date.

6. current_day_tracker:
   - Automatically tracks and inserts the simulation day into `starmart_current_date` whenever a new order is placed.
*/

-- =============================================================================
-- 1. Checks whether a given date is a holiday  -- Removed to increase efficiency
-- =============================================================================
-- CREATE OR REPLACE FUNCTION is_holiday(p_date DATE)
-- RETURNS BOOLEAN AS $$
-- BEGIN
    -- Return TRUE if the given date exists in starmart_holiday_dates
--     RETURN EXISTS (
--         SELECT 1 FROM starmart_holiday_dates WHERE holiday_dates = p_date
--     );
-- END;
-- $$ LANGUAGE plpgsql;

-- =============================================================================
-- 2. Handles product restocking and expired product cleanup
--    Called at the start of the day if it's a restock day.
-- =============================================================================
CREATE OR REPLACE FUNCTION restock_and_cleanup(f_curr_date DATE)
RETURNS VOID AS $$
DECLARE
    curr_date           DATE := f_curr_date;
    rec_lookup          RECORD;
    rec_expired         RECORD;
    chosen_vendor_id    VARCHAR(25);
BEGIN
    -- 1) INSERT "Scheduled Restock" into starmart_inventory only if not already present
    INSERT INTO starmart_inventory (
        product_id,
        on_hand_qty,
        restock_date,
        expiry_date
    )
    SELECT
        lkp.product_id,
        lkp.prod_lookup_qty,
        lkp.restock_date,
        (lkp.restock_date + p.shelf_life) AS expiry_date
    FROM starmart_inventory_lookup AS lkp
    JOIN starmart_products AS p
      ON lkp.product_id = p.product_id
    WHERE lkp.restock_date = curr_date
      AND NOT EXISTS (
        SELECT 1
        FROM starmart_inventory si
        WHERE si.product_id = lkp.product_id
          AND si.expiry_date = (lkp.restock_date + p.shelf_life)
      );

    -- 2) LOG each restock operation in starmart_inventory_log only if not already logged
    FOR rec_lookup IN
        SELECT
            lkp.product_id,
            lkp.prod_lookup_qty
        FROM starmart_inventory_lookup AS lkp
        WHERE lkp.restock_date = curr_date
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM starmart_inventory_log log
            WHERE log.product_id = rec_lookup.product_id
              AND log.restocked_date = curr_date
              AND log.reason = 'Restock'
        ) THEN
            -- Pick a random vendor who supplies this product
            SELECT vendor_unique_id
              INTO chosen_vendor_id
            FROM starmart_vendors
            WHERE product_id = rec_lookup.product_id
            ORDER BY RANDOM()
            LIMIT 1;

            INSERT INTO starmart_inventory_log (
                product_id,
                restocked_date,
                log_quantity,
                vendor_unique_id,
                reason
            ) VALUES (
                rec_lookup.product_id,
                curr_date,
                rec_lookup.prod_lookup_qty,
                chosen_vendor_id,
                'Restock'
            );
        END IF;
    END LOOP;

    -- 3) REMOVE any inventory rows with on_hand_qty <= 0
    DELETE FROM starmart_inventory
     WHERE on_hand_qty <= 0;

    -- 4) IDENTIFY & LOG expired items (expiry_date < curr_date)
    FOR rec_expired IN
        SELECT
            product_id,
            on_hand_qty
        FROM starmart_inventory
        WHERE expiry_date < curr_date
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM starmart_inventory_log log
            WHERE log.product_id = rec_expired.product_id
              AND log.discarded_date = curr_date
              AND log.reason = 'Expired'
        ) THEN
            -- Pick a random vendor who supplies this product
            SELECT vendor_unique_id
              INTO chosen_vendor_id
            FROM starmart_vendors
            WHERE product_id = rec_expired.product_id
            ORDER BY RANDOM()
            LIMIT 1;

            INSERT INTO starmart_inventory_log (
                product_id,
                discarded_date,
                log_quantity,
                vendor_unique_id,
                reason
            ) VALUES (
                rec_expired.product_id,
                curr_date,
                rec_expired.on_hand_qty,
                chosen_vendor_id,
                'Expired'
            );
        END IF;
    END LOOP;

    -- 5) DELETE all expired items from inventory
    DELETE FROM starmart_inventory
     WHERE expiry_date < curr_date;
END;
$$ LANGUAGE plpgsql;


-- =============================================================================
-- 3. Deducts product quantity (FIFO-style) when an order is placed
-- =============================================================================
CREATE OR REPLACE FUNCTION inventory_updater()
  RETURNS TRIGGER
AS $$
DECLARE
    qty_to_deduct  INTEGER := NEW.quantity;
    rec            RECORD;
    deduct_amount  INTEGER;
BEGIN
    FOR rec IN
      SELECT product_id, on_hand_qty
      FROM starmart_inventory
      WHERE product_id = NEW.product_id
        AND on_hand_qty > 0
      ORDER BY expiry_date
      FOR UPDATE
    LOOP
        EXIT WHEN qty_to_deduct <= 0;

        IF rec.on_hand_qty >= qty_to_deduct THEN
            -- This batch can cover the rest of the order
            deduct_amount := qty_to_deduct;
        ELSE
            -- Only part of this batch—use up entire rec.on_hand_qty
            deduct_amount := rec.on_hand_qty;
        END IF;

        UPDATE starmart_inventory
        SET on_hand_qty = on_hand_qty - deduct_amount
        WHERE product_id = rec.product_id;

        qty_to_deduct := qty_to_deduct - deduct_amount;
    END LOOP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER trg_deduct_inventory
  AFTER INSERT
  ON starmart_orders
  FOR EACH ROW
  EXECUTE FUNCTION inventory_updater();

-- =============================================================================
-- 4. Applies discounts (holiday, normal, membership) to each order line -- Removed to increase efficiency, discounts has been applied in python already
-- =============================================================================
-- CREATE OR REPLACE FUNCTION apply_order_item_discount()
-- RETURNS TRIGGER AS $$
-- DECLARE
--     t_hol_disc   NUMERIC := 0;
--     t_norm_disc  NUMERIC := 0;
--     mem_disc     NUMERIC := 0;
--     total_disc   NUMERIC := 0;
--     final_pr     NUMERIC := 0;
-- BEGIN
    -- Check for holiday discount
--     IF is_holiday(NEW.order_datetime::DATE) THEN
--         SELECT COALESCE(holiday_discount, 0)
--         INTO t_hol_disc
--         FROM starmart_markup_discount
--         WHERE product_id = NEW.product_id;
-- 
    -- Check for normal discount day
--     ELSIF EXISTS (
--         SELECT 1 FROM starmart_discount_dates
--         WHERE discount_dates = NEW.order_datetime::DATE
--     ) THEN
--         SELECT COALESCE(normal_day_discount, 0)
--         INTO t_norm_disc
--         FROM starmart_markup_discount
--         WHERE product_id = NEW.product_id;
--     END IF;
-- 
    -- Membership discount (20% per membership point)
--     SELECT COALESCE(membership, 0) * 0.20
--     INTO mem_disc
--     FROM starmart_customers
--     WHERE customer_id = NEW.customer_id;
-- 
    -- Combine discounts and calculate final price
--     total_disc := t_hol_disc + t_norm_disc + mem_disc;
--     final_pr := NEW.selling_price * (1 - total_disc);
-- 
    -- Save results into row
--     NEW.applied_discount := total_disc;
--     NEW.final_price := final_pr;
-- 
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;
-- 
-- CREATE TRIGGER apply_order_item_discount_trigger
-- BEFORE INSERT ON starmart_orders
-- FOR EACH ROW
-- EXECUTE FUNCTION apply_order_item_discount();

-- =============================================================================
-- 5. Executes restock logic if the inserted date is a scheduled restock day
-- =============================================================================
CREATE OR REPLACE FUNCTION scheduled_restock_and_cleanup()
RETURNS TRIGGER AS $$
DECLARE
    should_restock_and_cleanup BOOLEAN;
BEGIN
    -- Check if the current date matches a scheduled restock date
    SELECT EXISTS (
        SELECT 1
        FROM starmart_restock_dates
        WHERE restock_date = NEW.current_sim_date
    ) INTO should_restock_and_cleanup;

    -- If yes, run the restock and cleanup routine
    IF should_restock_and_cleanup THEN
        PERFORM restock_and_cleanup(NEW.current_sim_date);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_restock_before_day_start
AFTER INSERT ON starmart_current_date
FOR EACH ROW
EXECUTE FUNCTION scheduled_restock_and_cleanup();

-- =============================================================================
-- 6. Tracks the current simulation day whenever an order is placed
--    Ensures inventory operations can use the correct simulation date.
-- =============================================================================
CREATE OR REPLACE FUNCTION current_day_tracker()
RETURNS TRIGGER AS $$
DECLARE
    new_order_date DATE := NEW.order_datetime::DATE;
BEGIN
    -- Insert the order date into current date tracker if not already present
    INSERT INTO starmart_current_date (current_sim_date)
    VALUES (new_order_date)
    ON CONFLICT (current_sim_date) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER current_day_tracker_trigger
BEFORE INSERT ON starmart_orders
FOR EACH ROW
EXECUTE FUNCTION current_day_tracker();
