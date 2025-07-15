# Project StarMart - Retail Management & Analytics System

**Overview:**  
StarMart is a retail chain with over 25 stores across Chicago, USA. This project simulates the operations of a retail
chain by modeling store operations, inventory, customer data, and billing. The goal is to practice using different data
analysis and visualization tools in a cohesive project environment.

Python Script: Done
SQL Database Creation: Done
SQL Data Analysis: In Progress
Power BI Dashboard: In Progress
---

## Tech Stack & Tools

### Python

Python is used primarily for:

- Creating **synthetic datasets** that simulate realistic retail operations.
- Writing scripts to populate a PostgresSQL database.
- Building a **regression model** to **predict customer cart size** based on:
    - Customer income
    - Family size
    - Holidays
    - Discounts

### SQL (PostgresSQL)

SQL is used to:

- Design and manage relational database schemas covering:
    - Stores
    - Items
    - Customers
    - Billing and transactions
- Write queries to analyze sales, inventory levels, and customer behavior.
- Implement **triggers** to:
    - Refill stock when levels fall below the threshold.
    - Apply relevant discounts.
    - Generate supplier order requests.

### Power BI

Power BI is used to create interactive dashboards and visualizations, including:

- Sales by item category and store.
- Inventory trends.
- Customer purchase patterns.
- Cart size predictions based on model output.

### Excel (VBA & What-If Analysis)

Excel is used for:

- Running **What-If analyses** on pricing, discounts, and seasonal changes.
- Prototyping retail strategies.
- Using VBA to streamline data handling and generate reports.

---

## Modules in the System

1. **Store Management**
    - Stores with details like location and type.

2. **Inventory & Item Management**
    - Item master with SKUs, categories, and stock levels.
    - Triggers to manage restocking and supplier coordination.

3. **Customer Management**
    - Customer profiles including demographics.
    - Basis for segmentation and targeted analysis.

4. **Billing System**
    - Transaction-level sales records.
    - Billing includes taxes, discounts, and payment methods.
    - Input to cart-size prediction model.

5. **Predictive Analytics**
    - Regression model to estimate cart size.
    - Uses income, family size, holidays, and discounts as features.

6. **Business Intelligence**
    - Dashboards for exploring trends in sales and customer behavior.
    - Visualizations support data-driven insights and decision exploration.

---

## Purpose

This project is a hands-on exercise to build familiarity with multiple data analysis tools, databases, and reporting
platforms in the context of a simulated retail environment.

---

# Script Generation

## Stores

StarMart consists of **25 supermarket stores across Chicago**, divided into three regions:

- **Chicago North**
- **Chicago South**
- **Chicago Central**

The stores will be distributed evenly across these regions. Within each region, store placement will vary in terms of 
**population density**, which will directly influence **customer footfall** - stores in denser areas will experience
higher customer flow.

Each store will also have a `store_size` attribute. This will affect:

- The number of products per store (larger stores will offer a wider variety)
- Stock allocation strategies

A temporary column `store_category` will be used in the generation process to assist in script logic but will be removed
before writing to SQL.

---

## Employees

Each store will have employees with various **roles** (e.g., cashier, floor staff, manager). Key features:

- Employees will be either **full-time** or **part-time**
- All employees in the same role will have the **same hourly wage**
- **Full-time** employees will receive additional **benefits**
- An **employee rating system** will be implemented (1-5 stars), rated by customers

---


## Products

The number and variety of products will vary **based on store size**:

- Larger stores -> more products, more categories
- Products will include `cost_price` and `selling_price`
- **Markup** and **discounts** will be maintained in a separate **lookup table**

Some products (e.g., chips, candy bars) will be sold strictly at **MRP** - no discounts like BOGO will apply.

**Membership discounts**:

- **10% off**
  These discounts will stack with normal discounts (up to a capped limit in the lookup table).

---

## Stocks

Initial **stock levels** will be assigned arbitrarily. After the dataset is created, stock analysis will determine
optimal stock quantities for:

- **Regular days**
- **Holidays**
- **High-traffic periods**

The `stock` table will include:

- Product ID (foreign key)
- Stock threshold values
- Current stock level

**Triggers** will be implemented on the `orders` table to automatically do these processes:
- Decrease stock when an order is placed
- Restock products based on certain conditions

---

## Vendors

Vendors are linked to **subcategories** (not individual products). Each subcategory:

- Will have a **random set of vendors**
- Vendors will offer **dynamic pricing** based on order quantity  
  (smaller quantity orders = higher cost per unit)

Restocking will occur on a **weekly schedule**.

---

## Customers

The `customers` table will include:

- `name`, `birthdate`, `gender`, `phone_number`, `email`, `address`
- `membership` (None, Gold, Platinum)

Membership benefits:

- Gold: **5% off**
- Platinum: **10% off**

Discounts apply to all purchases and can stack with product discounts (up to a max).

---

## Orders

The `orders` table is the **main fact table** of the project.

### 1. Basket Size

- Will be predicted using either:
    - A basic **custom logic**
    - Or an **algorithm** (e.g., regression, rules-based)
- Choice depends on performance and flexibility

### 2. Purchased Items

- Once the **basket size** is known, the script will:
    - Select items a customer is likely to buy
    - Use either a **custom algorithm** or the **Apriori algorithm** to determine item combinations

### 3. Holiday Purchase Behavior

- Customers will buy more during holidays, more people will show up during these periods, discounts are provided as well.

---

## Expenses 

Expenses such as products discard due to expiry, insurance, electricity and such are included


