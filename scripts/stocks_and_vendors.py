import pandas as pd
from products import generate_product_df
from custom_functions import generate_unique_skus
from pathlib import Path
from faker import Faker
from datetime import datetime, timedelta
import numpy as np

base_dir = Path("C:/users/shrav/Data_Analysis_Projects/Big Projects/Project Starmart/Datasets")


def generate_stocks_table():
    np.random.seed(42)
    df = pd.read_csv(base_dir / "StarMart_Orders.csv").loc[:, ["order_datetime", "product_id", "quantity"]]
    df['order_datetime'] = pd.to_datetime(df['order_datetime'])
    df['date'] = df['order_datetime'].dt.date
    df['date'] = pd.to_datetime(df['date'])

    prod_dict = {prod: [] for prod in df.product_id.unique()}
    curr_date = datetime(2024, 1, 1)

    for i in range(0, 366, 3):
        date_range = [curr_date + timedelta(days=j) for j in range(3)]
        curr_df = df[df['date'].isin(date_range)].drop(columns='date')

        curr_df = curr_df.groupby('product_id')['quantity'].sum().reset_index()

        for _, row in curr_df.iterrows():
            pid = row['product_id']
            qty = row['quantity']
            prod_dict[pid].append((i, qty))

        curr_date += timedelta(days=3)

    start_date = datetime(2024, 1, 1)
    restock_list = []
    for p_id, restock_val in prod_dict.items():
        for val in restock_val:
            restock_wave, qty = val
            restock_date = start_date + timedelta(days=restock_wave)

            restock_list.append([p_id, restock_date, qty])

    stocks_3_day = pd.DataFrame(restock_list, columns=["product_id", "restock_date", "prod_lookup_qty"])

    stocks_3_day['restock_date'] = pd.to_datetime(stocks_3_day['restock_date'])
    stocks_3_day = stocks_3_day.sort_values(by='restock_date')

    ranges = [(0, 26), (26, 51), (51, 76), (76, 101)]
    probs = [0.50, 0.25, 0.15, 0.10]

    range_indices = np.random.choice(len(ranges), p=probs, size=len(stocks_3_day))

    # Step 2: For each selected range, sample an integer
    increments = [np.random.randint(ranges[i][0], ranges[i][1]) for i in range_indices]

    # Step 3: Add to the column
    stocks_3_day['prod_lookup_qty'] += increments

    restock_dates = stocks_3_day['restock_date'].drop_duplicates().sort_values()

    return stocks_3_day, restock_dates


# -----------Vendors---------------
fake = Faker()


def fake_ein():
    np.random.seed(42)
    return f"{np.random.randint(10, 99)}-{np.random.randint(1000000, 9999999)}"


def generate_fake_vendors():
    np.random.seed(42)
    products_df = generate_product_df().loc[:, ["product_id", "subcategory", "cost_price"]]
    sub_categories = products_df["subcategory"].unique()

    cat_sku = generate_unique_skus(sub_categories)
    vendors = []
    used_names = set()
    v_id = 1

    for cat in sub_categories:
        num_vendors = np.random.randint(3, 6)

        for i in range(num_vendors):
            vendor_id = f"STRMRT_VNDR_{cat_sku[cat]}_{v_id}"

            # Ensure unique vendor names
            while True:
                vendor_name = fake.company()
                if vendor_name not in used_names:
                    used_names.add(vendor_name)
                    break

            delivery_fee = np.random.choice([20, 30, 40, 50])

            vendors.append([
                vendor_id,
                vendor_name,
                cat,
                delivery_fee
            ])

            v_id += 1

    vendors_df = pd.DataFrame(vendors, columns=["vendor_id", "vendor_name", "subcategory", "delivery_fee"])

    vendors_df = (
        vendors_df
        .merge(products_df, how="inner", on="subcategory")
        .rename(columns={"cost_price": "per_item_cost"})
    )

    vendors_df['per_item_cost'] = (
            vendors_df['per_item_cost'] - np.random.uniform(0.1, 0.3, size=len(vendors_df))
    ).round(2)

    vendors_df['vendor_unique_id'] = [f"STRMRT_VNDR_{i}" for i in range(1, len(vendors_df) + 1)]

    return vendors_df.drop(columns='subcategory')
