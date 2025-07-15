import pandas as pd
from datetime import datetime
from pathlib import Path
from employee_generator import generate_employee_df
from products import generate_product_df, product_markup_and_discount
from stores import generate_stores_df
from customer_generator import return_complete_df
from orders_generator import generate_orders_file
from raw_data import holiday_lookup_dates, holiday_restock_dates, holiday_lookup
from stocks_and_vendors import generate_stocks_table, generate_fake_vendors
from custom_functions import discount_list

base_dir = Path(
    "C:/Users/shrav/Data_Analysis_Projects/Big Projects/Project StarMart/Datasets"
)


def csv_writer(file_name, df):
    file_path = base_dir / file_name
    df.to_csv(file_path, index=False)
    print(f"{file_name} done!")


# Customers Table
start_dt = datetime(2024, 1, 1)
end_dt = datetime(2025, 1, 1)
customer_df = return_complete_df(40_000, 50_000, 90_000)
csv_writer("StarMart_Customers.csv", customer_df)

# Employee Table
employee_df = generate_employee_df()
csv_writer("StarMart_Employees.csv", employee_df)
del employee_df

# Products Table
products_df = generate_product_df()
csv_writer("StarMart_Products.csv", products_df)
del products_df

# Stores Table
stores_df = generate_stores_df()
# removing category as it is not useful anymore
stores_df = stores_df.drop(columns=["category"])
csv_writer("StarMart_Stores.csv", stores_df)
del stores_df

# Orders and Orders Summary Table
orders_file_path = base_dir / "StarMart_Orders.csv"
generate_orders_file(orders_file_path, start_date=start_dt, end_date=end_dt)
print("Orders and Orders Summary Done")

orders_df = pd.read_csv(orders_file_path)
all_customers = list(orders_df['customer_id'].unique())
customer_df = customer_df[customer_df['customer_id'].isin(all_customers)]
csv_writer("StarMart_Customers.csv", customer_df)
del customer_df, orders_df

# Holiday Dates
dates_df = pd.DataFrame(holiday_lookup_dates, columns=["holiday_dates"])
csv_writer("StarMart_Holiday_Dates.csv", dates_df)

# Discount Dates
dates_df = pd.DataFrame(list(discount_list), columns=["discount_dates"])
csv_writer("StarMart_Discount_Dates.csv", dates_df)

# Stocks
stocks, restock_dates = generate_stocks_table()
csv_writer("StarMart_Inventory_Lookup.csv", stocks)
csv_writer("StarMart_Restock_Dates.csv", restock_dates)

# Vendors
vendors_df = generate_fake_vendors()
csv_writer("StarMart_Vendors.csv", vendors_df)

# Markup And Discount
markup_discount = product_markup_and_discount()
csv_writer("StarMart_Markup_Discount.csv", markup_discount)

# Holiday Restock Days
dates_df = pd.DataFrame(list(holiday_restock_dates), columns=["restock_dates"])
csv_writer("StarMart_Holiday_Restock.csv", dates_df)

# Holiday Lookup
holiday_lookup_df = pd.DataFrame.from_dict(holiday_lookup, orient='index', columns=['Holiday_Name'])
holiday_lookup_df = holiday_lookup_df.reset_index().rename(columns={'index': 'Date'})
csv_writer("StarMart_Holiday_Lookup.csv", holiday_lookup_df)
