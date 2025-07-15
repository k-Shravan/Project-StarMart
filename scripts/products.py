from raw_data import (
    shelf_life,
    category_and_products,
    variant_and_multiplier,
    product_markup,
    normal_day_discount_items,
    holiday_discount_items,
)
import numpy as np
import pandas as pd
from stores import generate_stores_df


def return_shelf_life(f_item):
    """
    returns the shelf life(days) of an item based on the shelf_life dict

    :param f_item: chosen item
    :return: shelf life in days
    """

    shelf_life_value = shelf_life.get(f_item)
    if shelf_life_value == "Indefinite":
        return 1000

    n, period = shelf_life_value.split()

    period_multipliers = {"days": 1, "weeks": 7, "months": 30, "years": 365}
    period_multiplier = period_multipliers.get(
        period, 1
    )  # Default to 1 if unit is unknown

    return int(n) * period_multiplier


def generate_balanced_ratings(f_base_rating, f_num_variants):
    if f_num_variants == 1:
        return [round(f_base_rating, 2)]  # If only one variant, return the base rating

    ratings = [
        round(
            np.random.uniform(
                max(1.0, f_base_rating - 0.3), min(5.0, f_base_rating + 0.3)
            ),
            2,
        )
        for _ in range(f_num_variants - 1)
    ]
    last_rating = round(
        (f_base_rating * f_num_variants) - sum(ratings), 2
    )  # Adjust last value to keep mean
    ratings.append(
        max(0.0, min(5.0, last_rating))
    )  # Ensure the rating is between 0 and 5
    return ratings


def generate_product_df(stats=False) -> pd.DataFrame:
    """
    Generates a product lookup table.
    :param stats: If true, prints number of products per store.
    :return: Products DataFrame
    """
    np.random.seed(42)
    stores_df = generate_stores_df()
    products = []
    for store_num, (_, store) in enumerate(stores_df.iterrows(), start=1):
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
