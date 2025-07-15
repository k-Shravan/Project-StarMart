from raw_data import *
from custom_functions import *
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

base_dir = Path("C:/users/shrav/Data_Analysis_Projects/Big Projects/Project Starmart/Datasets")
fake = Faker()


def generate_stores_df():
    """
    Attributes: store_id, region, neighborhood, pop_density, store_size, parking_space, category
    :return:
    """
    df = pd.DataFrame(
        [
            [region, *neighborhood_info, ]  # Unpack neighborhood details into separate columns
            for s_id, (region, neighborhoods) in enumerate(chicago_regions.items(), start=1)  # Assign unique store_id
            for neighborhood_info in neighborhoods  # Iterate through each neighborhood in a region
        ],
        columns=[
            "region",
            "neighbourhood",
            "pop_density",
            "store_size",
            "parking_space",
            "category",
        ],
    )
    # store id
    df["store_id"] = [f"STRMRT_STR_{str_idx + 1:02d}" for str_idx in range(len(stores_df))]

    # moving store_id to the start
    cols = df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("store_id")))
    df = df[cols]

    return df


def generate_product_df(stats=False) -> pd.DataFrame:
    """
    Generates a product lookup table.
    :param stats: If true, prints number of products per store.
    :return: Products DataFrame
    """
    np.random.seed(42)
    f_df = generate_stores_df()
    products = []
    for store_num, (_, store) in enumerate(f_df.iterrows(), start=1):
        # Get the store details
        store_id = store["store_id"]
        store_size = store["store_size"]

        # get the product categories
        categories = category_and_products.keys()

        product_id = 1
        # loop through the categories
        for category in categories:
            # get the subcategory for the current product category
            sub_category_list = category_and_products[category].keys()

            # get the product and its shelf life
            for item in sub_category_list:
                product_list = category_and_products[category][item]
                item_shelf_life = return_shelf_life(item)

                # return [['N/A', 1]] to loop through a nested list
                variant_list = variant_and_multiplier.get(item, [["N/A", 1]])

                # get the number of products in the current category and remove as per store size
                n_products = len(product_list)

                # removing products based on store size (smaller the store size more product removal)
                n_remove_products = (
                    np.random.randint(1, 3)
                    if store_size == "Large"
                    else np.random.randint(2, 4)
                    if store_size == "Medium"
                    else np.random.randint(4, 5)
                )

                n_keep = max(0, n_products - n_remove_products)

                for idx in range(n_keep):
                    (product,
                     prod_cost_price,
                     prod_selling_price,
                     base_rating) = product_list[idx]

                    num_variants = len(variant_list)
                    variant_ratings = generate_balanced_ratings(
                        base_rating, num_variants
                    )

                    for (variant, variant_rating) in zip(variant_list, variant_ratings):
                        variant_name, price_multiplier = variant

                        cost_price = round(prod_cost_price * price_multiplier, 2)
                        curr_product_id = f"STRMRT_PRD_{store_num:02d}_{product_id:04d}"

                        product_row = [
                            curr_product_id,
                            store_id,
                            category,
                            item,
                            product,
                            variant_name,
                            cost_price,
                            item_shelf_life,
                            round(variant_rating, 2),
                        ]

                        products.append(product_row)
                        product_id += 1

    products_df = pd.DataFrame(
        products,
        columns=[
            "product_id",
            "store_id",
            "category",
            "subcategory",
            "product_name",
            "variant",
            "cost_price",
            "shelf_life",
            "rating",
        ],
    )

    if stats:
        num_of_stores = products_df["store_id"].nunique()
        store_product_counts = products_df.groupby("store_id")["product_id"].count()
        print(f"Number of stores: {num_of_stores}")
        print(f"Products Per Store: {store_product_counts}")

    return products_df


def product_markup_and_discount():
    """
    Generates a table for markup values, normal day and holiday day.
    :return: DataFrame with discount percentages
    """
    # Set random seed once, for reproducibility
    np.random.seed(42)

    # Get base product info
    prod_price_df = generate_product_df().loc[:, ["product_id", "subcategory"]]

    # Assign markup based on subcategory mapping
    prod_price_df['markup'] = prod_price_df.apply(
        lambda row: 2 * product_markup.get(row['subcategory'], 1),
        axis=1
    ).round(2)

    # Convert flags to integers (1 or 0)
    prod_price_df["discount_flag_normal_day"] = prod_price_df["subcategory"].isin(normal_day_discount_items).astype(int)
    prod_price_df["discount_flag_holiday"] = prod_price_df["subcategory"].isin(holiday_discount_items).astype(int)

    # Define discount logic
    def apply_discount(row, day):
        discount_percentages = (
            np.arange(0.05, 0.20, 0.05) if day == "normal day"
            else np.arange(0.2, 0.70, 0.1)
        )
        flag = row["discount_flag_normal_day"] if day == "normal day" else row["discount_flag_holiday"]

        if flag == 1:
            return np.random.choice(discount_percentages)
        else:
            return 0

    # Apply discount logic
    prod_price_df["normal_day_discount"] = prod_price_df.apply(
        apply_discount, axis=1, args=("normal day",)
    ).round(2)

    prod_price_df["holiday_discount"] = prod_price_df.apply(
        apply_discount, axis=1, args=("holiday",)
    ).round(2)

    return prod_price_df.drop(columns=['subcategory', 'discount_flag_normal_day', 'discount_flag_holiday'])


def generate_stocks_table():
    np.random.seed(42)
    df = pd.read_csv(base_dir / "StarMart_Orders.csv").loc[:, ["order_datetime", "product_id", "quantity"]]
    df['order_datetime'] = pd.to_datetime(df['order_datetime'])
    df['date'] = df['order_datetime'].dt.date
    df['date'] = pd.to_datetime(df['date'])

    prod_dict = {prod: [] for prod in df.product_id.unique()}
    curr_date = datetime(2024, 1, 1)

    for dt_grp in range(0, 366, 3):
        curr_date_range = [curr_date + timedelta(days=j) for j in range(3)]
        curr_df = df[df['date'].isin(curr_date_range)].drop(columns='date')

        curr_df = curr_df.groupby('product_id')['quantity'].sum().reset_index()

        for _, row in curr_df.iterrows():
            pid = row['product_id']
            qty = row['quantity']
            prod_dict[pid].append((dt_grp, qty))

        curr_date += timedelta(days=3)

    start_dt = datetime(2024, 1, 1)
    restock_list = []
    for p_id, restock_val in prod_dict.items():
        for val in restock_val:
            restock_wave, qty = val
            restock_date = start_dt + timedelta(days=restock_wave)

            restock_list.append([p_id, restock_date, qty])

    stocks_3_day = pd.DataFrame(restock_list, columns=["product_id", "restock_date", "prod_lookup_qty"])

    stocks_3_day['restock_date'] = pd.to_datetime(stocks_3_day['restock_date'])
    stocks_3_day = stocks_3_day.sort_values(by='restock_date')

    ranges = [(0, 26), (26, 51), (51, 76), (76, 101)]
    stock_probs = [0.50, 0.25, 0.15, 0.10]

    range_indices = np.random.choice(len(ranges), p=stock_probs, size=len(stocks_3_day))

    # Step 2: For each selected range, sample an integer
    increments = [np.random.randint(ranges[idx][0], ranges[idx][1]) for idx in range_indices]

    # Step 3: Add to the column
    stocks_3_day['prod_lookup_qty'] += increments

    restock_dates = stocks_3_day['restock_date'].drop_duplicates().sort_values()

    return stocks_3_day, restock_dates


# -----------Vendors---------------
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

        for idx in range(num_vendors):
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

    vendors_df['vendor_unique_id'] = [f"STRMRT_VNDR_{idx}" for idx in range(1, len(vendors_df) + 1)]

    return vendors_df.drop(columns='subcategory')


stores_df = generate_stores_df()
ages, probs = generate_age_grp_and_prob("emp")  # Generate ages and probabilities


def generate_employee_df() -> pd.DataFrame:
    """
    Generates a dataframe of employee information using the store_roles dict in this function
    attributes:
    emp_id, store_id, f_name, l_name, age, gender, ph_no, email, address, department, role, hourly_rate, customer_rating
    """
    np.random.seed(42)

    area_codes = [312, 872]
    area_code_probs = [0.8, 0.2]
    email_domains = ["gmail.com", "yahoo.com", "hotmail.com"]
    email_probs = [0.7, 0.2, 0.1]

    emp_list = []
    # loop through the stores
    for idx, store_row in stores_df.iterrows():
        store_id = store_row["store_id"]
        str_num = int(store_id.split("_")[-1])
        store_size = store_row["store_size"]
        store_region = store_row["region"]

        neighbourhood_list = np.array(chicago_regions[store_region])
        neighbourhoods = neighbourhood_list[:, 0]
        population = neighbourhood_list[:, 1].astype(int)
        population_weights = population / population.sum()

        emp_id = 1

        for dept, roles_dict in store_roles_and_hourly_rates.items():
            roles_list = roles_dict["roles"]
            emp_count = roles_dict["count"]

            emp_count = (
                max(1, emp_count - 1)
                if store_size == "Medium"
                else max(1, emp_count - 2)
                if store_size == "Small"
                else emp_count
            )

            hourly_rate = roles_dict["hourly_rate"]

            for e_idx, role in enumerate(roles_list):
                for _ in range(emp_count):
                    curr_emp_id = f"STRMRT_EMP_{str_num}_{emp_id}"
                    curr_role = role
                    curr_salary = hourly_rate[e_idx]
                    curr_store = store_id
                    gender_probability = gender_roles.get(role, [0.50, 0.50])
                    gender = np.random.choice(["Male", "Female"], p=gender_probability)

                    emp_name = fake.name_male() if gender == "Male" else fake.name_female()

                    ph_number = (
                            f"+1({np.random.choice(area_codes, p=area_code_probs)})-"
                            + f"{np.random.randint(100, 999)}-"
                            + f"{np.random.randint(1000, 9999)}"
                    )

                    email = (
                            emp_name.lower().replace(" ", "")
                            + "@"
                            + np.random.choice(email_domains, p=email_probs)
                    )

                    building_number = fake.building_number()
                    emp_neighbourhood = np.random.choice(
                        neighbourhoods, p=population_weights
                    )
                    emp_street = np.random.choice(
                        chicago_streets.get((store_region, emp_neighbourhood))
                    )
                    full_address = f"{building_number} {emp_street}, {emp_neighbourhood}, {store_region} Chicago"

                    age = np.random.choice(ages, p=probs)

                    curr_emp_row = [
                        curr_emp_id,
                        curr_store,
                        emp_name,
                        age,
                        gender,
                        ph_number,
                        email,
                        full_address,
                        dept,
                        curr_role,
                        curr_salary,
                    ]

                    emp_list.append(curr_emp_row)
                    emp_id += 1

    emp_df = pd.DataFrame(
        emp_list,
        columns=[
            "emp_id",
            "store_id",
            "name",
            "age",
            "gender",
            "ph_num",
            "email",
            "address",
            "department",
            "role",
            "hourly_rate",
        ],
    )

    return emp_df


def generate_customers_df(n: int) -> pd.DataFrame:
    """Generates base customer info including address, name, age, phone, email, gender."""
    region_neighborhoods = []
    weights = []

    for region, neighborhoods in chicago_regions.items():
        for entry in neighborhoods:
            neighborhood, population, *_ = entry
            region_neighborhoods.append((region, neighborhood))
            weights.append(population)

    weights = np.array(weights)
    weights = weights / weights.sum()

    addresses = generate_unique_addresses(n, region_neighborhoods, weights, chicago_streets)
    phone_numbers = generate_unique_phone_numbers(size=n)
    gender = np.random.choice(["Male", "Female"], size=n, p=[0.4854, 0.5146])
    names = [fake.name_male() if g == "Male" else fake.name_female() for g in gender]
    emails = generate_unique_emails(size=n, names=names, phone_num=phone_numbers)

    c_ages, c_probs = generate_age_grp_and_prob("cust")

    df = pd.DataFrame({
        "name": names,
        "age": np.random.choice(c_ages, size=n, p=c_probs),
        "gender": gender,
        "phone_number": phone_numbers,
        "email": emails,
        "address": addresses
    })

    return df


def return_complete_df(recurring_count: int, non_recurring_count: int, one_time_customer_count: int) -> pd.DataFrame:
    """
    Returns a full customer dataframe with demographic info, customer type, and membership flags.
    """
    total = recurring_count + non_recurring_count + one_time_customer_count
    base_df = generate_customers_df(total)

    # Assign customer type labels
    recurring_flags = (
            ["Recurring"] * recurring_count +
            ["Non-Recurring"] * non_recurring_count +
            ["One Time Customer"] * one_time_customer_count
    )

    membership_flags = np.concatenate([
        np.random.choice([1, 0], size=recurring_count, p=[0.55, 0.45]),
        np.random.choice([1, 0], size=non_recurring_count, p=[0.05, 0.95]),
        np.zeros(one_time_customer_count, dtype=int)
    ])

    # Shuffle everything in the same order
    shuffle_indices = np.random.permutation(total)
    base_df = base_df.iloc[shuffle_indices].reset_index(drop=True)
    base_df["recurring"] = np.array(recurring_flags)[shuffle_indices]
    base_df["membership"] = membership_flags[shuffle_indices]

    # Add unique customer ID
    base_df["customer_id"] = [f"STRMRT_CSTMR_{idx}" for idx in range(1, total + 1)]

    # Reorder columns
    cols = ["customer_id"] + [col for col in base_df.columns if col != "customer_id"]
    return base_df[cols]
