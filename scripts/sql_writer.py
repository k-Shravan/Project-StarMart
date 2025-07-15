# import pandas as pd
import psycopg2
import csv
from pathlib import Path

base_dir = Path(
    "C:/Users/shrav/Data_Analysis_Projects/Big Projects/Project StarMart/Datasets"
)


def load_csv_batched(connection_params, table_name, csv_filepath, batch_size=50000):
    """Load csv file to postgres with batches"""
    conn = psycopg2.connect(**connection_params)
    cursor = conn.cursor()
    print("Current Table:", table_name)

    total_records = 0  # Record tracker

    try:
        with open(csv_filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            data = []
            for row in reader:
                row = [val for val in row]
                data.append(tuple(row))

                if len(data) == batch_size:
                    sql = f"INSERT INTO {table_name} ({', '.join(header)}) VALUES ({', '.join(['%s'] * len(header))})"
                    cursor.executemany(sql, data)
                    conn.commit()
                    total_records += len(data)

                    if total_records % batch_size == 0:
                        print(f"Inserted {total_records} records...")

                    data = []  # Clear the list after every dump

            if data:  # If anything is remaining
                sql = f"INSERT INTO {table_name} ({', '.join(header)}) VALUES ({', '.join(['%s'] * len(header))})"
                cursor.executemany(sql, data)
                conn.commit()
                total_records += len(data)

                if total_records % batch_size == 0:
                    print(f"Inserted {total_records} records...")

            print(f"\nSuccessfully loaded {total_records} records into {table_name}\n")

    except psycopg2.DatabaseError as error:
        print(f"Error while loading data: {error}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


# DB connection settings
conn_params = {
    "dbname": "StarMart",
    "user": "postgres",
    "password": "123456",
    "host": "localhost",
    "port": 5432,
}

# Files to be inserted in this order
small_csv = [
    "StarMart_Stores.csv",
    "StarMart_Employees.csv",
    "StarMart_Products.csv",
    "StarMart_Vendors.csv",
    "StarMart_Markup_Discount.csv",
    "StarMart_Inventory_Lookup.csv",
    "StarMart_Customers.csv",
    "StarMart_Discount_Dates.csv",
    "StarMart_Holiday_Dates.csv",
    "StarMart_Markup_Discount.csv",
    "StarMart_Restock_Dates.csv",
    "StarMart_Holiday_Lookup.csv"
]

for csv_file in small_csv:
    curr_path = base_dir / csv_file
    sql_table_name = csv_file.replace(".csv", "").lower()
    load_csv_batched(conn_params, sql_table_name, curr_path, 100000)

csv_file = "StarMart_Orders.csv"
curr_path = base_dir / csv_file

# # Load the CSV
# df = pd.read_csv(curr_path)
#
# # Extract numeric ID from STRMRT_LINE_ID_* column
# df['numeric_id'] = df['line_order_id'].str.extract(r'_(\d+)$').astype(int)
#
# # Sort by the numeric ID
# df = df.sort_values('numeric_id')
#
# # Remove the first 1,100,000 rows
# n_remove_rows = 1100000
# df = df[df['numeric_id'] > n_remove_rows]
#
# # Drop the helper column
# df = df.drop(columns=['numeric_id'])
#
# # Save back to CSV
# df.to_csv(curr_path, index=False)

# Prepare table name and load to SQL
sql_table_name = csv_file.replace(".csv", "").lower()
load_csv_batched(conn_params, sql_table_name, curr_path, 50000)
