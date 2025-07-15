import csv
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from basket_size_script import basket_size_calculator, get_discount_flag
from products import generate_product_df, product_markup_and_discount
from purchased_item import predict_categories
from raw_data import high_traffic_periods, holiday_lookup
from stores import generate_stores_df
from employee_generator import generate_employee_df
from custom_functions import discount_list

# Customer df should already be created
customer_df = pd.read_csv(
    "C:/Users/shrav/Data_Analysis_Projects/Big Projects/Project StarMart/Datasets/StarMart_Customers.csv"
).loc[:, ["customer_id", "age", "membership", "recurring"]]

# Split the customer_df into recurring and non-recurring
recurring_ids = customer_df[customer_df["recurring"] == "Recurring"]['customer_id']
non_recurring_ids = customer_df[customer_df["recurring"] == "Non-Recurring"]['customer_id']
one_time_ids = customer_df[customer_df["recurring"] == "One Time Customer"]['customer_id']
customer_pool = []

for idx in recurring_ids:
    customer_pool.extend([idx] * np.random.randint(12, 18))  # Loyal: 8–14 orders
for idx in non_recurring_ids:
    customer_pool.extend([idx] * np.random.randint(3, 6))  # Mid: 2–5 orders
for idx in one_time_ids:
    customer_pool.append(idx)  # Just once

np.random.shuffle(customer_pool)

customer_dict = customer_df.set_index("customer_id").to_dict("index")
del customer_df


def random_split(n: int, min_val: int = 1) -> list[int]:
    """
    Creates a random split for a given number, this will be taken as quantity for individual product purchase
    basket_size = 34
    return value = [10, 5, 4, 7, 8] -> each element will be the quantity bought per order
    :param n: Number to create the split for.
    :param min_val: The Minimum value for each split must be greater than or equal to 1.
    :return: List of splits where the sum of elements equals n.
    """
    result = []
    total = 0  # when this == n returns the result
    cap_percentage = np.random.rand()
    if cap_percentage < 0.70:  # 70% of the time the cap value will be half of the basket size
        cap_val = n // 2
    elif cap_percentage < 0.90:  # if the random value is between 70 and 90, take 1/3rd the basket size as cap
        cap_val = n // 3
    else:
        cap_val = n

    cap = max(min_val, cap_val)

    while total < n:
        # cap the max_vak to our calculated "cap"
        max_val = min(cap, n - total)

        # If the remaining value is less than min_val, append and exit
        if max_val <= min_val:
            result.append(max_val)
            break

        # Get a random value between the min_val and max_val and append and repeat untile total == n
        val = np.random.randint(min_val, max_val + 1)
        result.append(val)
        total += val

    return result


def get_customer_count(curr_year: int,
                       curr_month: int,
                       curr_day: int,
                       category: str,
                       avail_parking: str,
                       is_discounted: int) -> int:
    """
    Simulates customer traffic with noise centered around key variable means.
    Optimized to reduce unnecessary random draws and improve performance.
    """
    curr_date = datetime(curr_year, curr_month, curr_day)

    # Base customer count with slight noise
    base_customers = 70 * np.random.normal(1.0, 0.1)

    # Store category multiplier with noise factor
    store_multipliers = {"High": np.random.choice([1.10, 1.15, 1.20]),
                         "Medium": np.random.choice([0.90, 1.00, 1.10]),
                         "Low": np.random.choice([0.90, 0.85, 1.10])}

    store_multiplier = np.random.normal(store_multipliers[category], 0.1)

    # Parking availability multiplier
    parking_multipliers = {
        "Very Limited": 0.95,
        "Limited": 0.97,
        "Moderate": 1.0,
        "Adequate": 1.03,
        "Spacious": 1.07,
    }
    parking_multiplier = parking_multipliers[avail_parking] * np.random.normal(
        1.0, 0.02
    )

    # Month multiplier with slight variation
    month_multipliers = {
        1: 0.95,
        2: 0.75,
        3: 0.83,
        4: 0.95,
        5: 0.92,
        6: 1.05,
        7: 1.10,
        8: 1.12,
        9: 1.12,
        10: 1.20,
        11: 1.35,
        12: 1.50,
    }
    month_multiplier = month_multipliers[curr_month] * np.random.normal(1.0, 0.01)

    # Weekday multiplier
    weekday_multipliers = {0: 1.0, 1: 0.85, 2: 0.90, 3: 1.05, 4: 1.1, 5: 1.2, 6: 1.15}
    weekday_multiplier = weekday_multipliers[curr_date.weekday()] * np.random.normal(
        1.0, 0.02
    )

    # Holiday bonus
    holiday_bonus = 1.0
    if curr_date in high_traffic_periods:
        holiday_name = holiday_lookup.get(curr_date)
        holiday_weights = {
            "Labor Day": 1.02,
            "Father's Day": 1.03,
            "Veterans Day": 1.08,
            "Back to School": 1.10,
            "Memorial Day": 1.10,
            "Valentine's Day": 1.12,
            "Mother's Day": 1.13,
            "St. Patrick's Day": 1.15,
            "Independence Day": 1.15,
            "Superbowl": 1.17,
            "Cinco de Mayo": 1.22,
            "Easter": 1.27,
            "New Year": 1.60,
            "Halloween": 1.70,
            "Thanksgiving & Black Friday": 1.75,
            "Christmas": 1.90,
        }
        base_bonus = holiday_weights.get(holiday_name, 0.80)
        holiday_bonus = base_bonus * np.random.normal(
            1.0, 0.2
        )  # Lower variance for performance

    # Discount impact
    discount_multiplier = 1.2 if is_discounted == 1 else 0.85
    discount_boost = discount_multiplier * np.random.normal(1.0, 0.2)

    # Final customer count
    final_count = (
            base_customers
            * store_multiplier
            * parking_multiplier
            * month_multiplier
            * weekday_multiplier
            * holiday_bonus
            * discount_boost
    )

    return max(int(final_count), 0)


def get_season(curr_date):
    """Return the current season based on the month."""
    curr_month = curr_date.month

    if 3 <= curr_month <= 5:
        return "Spring"
    elif 6 <= curr_month <= 8:
        return "Summer"
    elif 9 <= curr_month <= 11:
        return "Fall"
    else:
        return "Winter"


def generate_sorted_order_times(n, base_date):
    """Generates a sorted list of time-stamps from 7am to 10pm"""
    start_seconds = 7 * 3600  # 7 AM = 25,200 seconds
    end_seconds = 22 * 3600  # 10 PM = 79,200 seconds

    times = np.array(
        [
            base_date + timedelta(seconds=np.random.randint(start_seconds, end_seconds))
            for _ in range(n)
        ]
    )

    return sorted(times)


def generate_orders_file(
        orders_file_path, start_date: datetime, end_date: datetime
) -> None:
    """Generates orders and orders_summary csv file from start date to end date"""
    customer_pointer = 0
    order_id = 1
    line_order_id = 1
    curr_date = start_date

    products_df = generate_product_df(stats=False).loc[
                  :, ["product_id", "store_id", "category", "cost_price"]
                  ]

    stores_df = generate_stores_df()
    employee_df = generate_employee_df().loc[:, ["emp_id", "store_id", "role"]]

    category_df_dict = {}
    cashier_df_dict = {}

    for store_id in stores_df["store_id"]:
        # Get cashiers at store
        emp_df = employee_df[
            (employee_df["store_id"] == store_id)
            & (employee_df["role"] == "Front-end Checkout Staff")
            ]
        cashier_df_dict[store_id] = emp_df

        # Only consider categories that exist in this store
        store_products = products_df[products_df["store_id"] == store_id]
        for category in store_products["category"].unique():
            mask = store_products["category"] == category
            category_df_dict[(store_id, category)] = store_products[mask]

    markup_df = product_markup_and_discount()
    markup_dict = markup_df.set_index('product_id')['markup'].to_dict()

    holiday_discount_dict = markup_df.set_index('product_id')['holiday_discount'].to_dict()
    normal_discount_dict = markup_df.set_index('product_id')['normal_day_discount'].to_dict()
    del markup_df, employee_df

    with open(orders_file_path, "w", newline="", buffering=1024 * 1024) as orders_file:
        order_writer = csv.writer(orders_file)
        # headers
        order_writer.writerow(
            [
                "line_order_id",
                "order_id",
                "customer_id",
                "product_id",
                "store_id",
                "cashier_id",
                "order_datetime",
                "quantity",
                "final_price"
            ]
        )

        while curr_date < end_date:
            day = curr_date.day
            month = curr_date.month
            year = curr_date.year

            discount, curr_holiday = get_discount_flag(curr_date, discount_list)
            curr_season = get_season(curr_date)

            for _, store in stores_df.iterrows():
                store_id = store["store_id"]
                parking = store["parking_space"]
                store_category = store["category"]

                cashier_df = cashier_df_dict[store_id]

                # customer for a day
                curr_customer_count = get_customer_count(
                    year, month, day, store_category, parking, discount
                )

                # order times for the current day
                order_times = generate_sorted_order_times(
                    curr_customer_count, curr_date
                )

                for customer in range(curr_customer_count):
                    # get cashier info
                    line_cashier = cashier_df.iloc[np.random.randint(len(cashier_df))]
                    line_cashier_id = line_cashier["emp_id"]

                    # get customer info
                    c_id = customer_pool[customer_pointer]
                    age = customer_dict[c_id]["age"]
                    membership = customer_dict[c_id]["membership"]

                    basket_size = basket_size_calculator(
                        curr_date, store_category, discount, curr_holiday, membership
                    )

                    cart_size_split = random_split(basket_size)
                    num_of_categories = len(cart_size_split)
                    purchase_list = predict_categories(
                        num_of_categories, age, curr_holiday, curr_season
                    )

                    curr_time = order_times[customer]
                    for i, category in enumerate(purchase_list):
                        # sort the product dataframe based on the current category
                        category_df = category_df_dict[(store_id, category)]
                        item_row = category_df.iloc[np.random.randint(len(category_df))]

                        # get item info
                        p_id = item_row["product_id"]
                        cost_price = item_row['cost_price']
                        if discount == 1 and curr_holiday == "Normal day":
                            curr_discount = normal_discount_dict[p_id]
                        elif discount == 1:
                            curr_discount = holiday_discount_dict[p_id]
                        else:
                            curr_discount = 0

                        # Base markup before any discount
                        base_markup = markup_dict[p_id]

                        # Apply product discount on a markup portion only
                        effective_markup = base_markup * (1 - curr_discount)

                        # Price after markup (before membership discount)
                        price_after_markup = cost_price * (1 + effective_markup)

                        # The Membership discount is applied on the final price
                        membership_discount = 0.15 * membership
                        final_price = np.round(price_after_markup * (1 - membership_discount), 2)

                        quantity = cart_size_split[i]

                        # Log the values, discount and line total will be applied in SQL
                        order_row = [
                            f"STRMRT_LINE_ID_{line_order_id}",
                            f"STRMRT_ORDR_{order_id}",
                            c_id,
                            p_id,
                            store_id,
                            line_cashier_id,
                            curr_time,
                            quantity,
                            final_price
                        ]
                        order_writer.writerow(order_row)

                        line_order_id += 1

                    order_id += 1
                    customer_pointer += 1

                    if customer_pointer >= len(customer_pool):
                        customer_pointer = 0

            print(curr_date, end=", ")
            curr_date += timedelta(days=1)
