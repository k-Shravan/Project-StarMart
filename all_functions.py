import pandas as pd
import numpy as np
import math
import calendar
import re
from collections import defaultdict
from faker import Faker
from stores import generate_stores_df
import csv
import random
from collections import Counter
from pathlib import Path

from project_data import *


base_dir = Path(
    "C:/Users/shrav/Data_Analysis_Projects/Big Projects/Project StarMart/Datasets"
)

fake = Faker()


# ---- Custom Functions ----
def get_random_date_group(day_group: int, year: int = 2024) -> list[datetime] | None:
    """
    Generate a list of consecutive dates in chronological order, avoiding high-traffic periods.
    Dates are selected such that none of them fall within predefined high-traffic periods (e.g., holidays),
    which already have active discounts.
    :param day_group: Number of consecutive dates to return.
    :param year: Year to generate dates for. Default is 2024.
    :return: List[datetime]: List of consecutive dates in datetime format.
    """
    random.seed(42)

    while True:
        month = random.randint(1, 13)
        day = random.randint(1, calendar.monthrange(year, month)[1])
        start_date = datetime(year, month, day)

        # Check the full range for overlap
        if any(
                (start_date + timedelta(days=i)) in high_traffic_periods
                for i in range(day_group)
        ):
            continue

        return [(start_date + timedelta(days=i)) for i in range(day_group)]


def create_discount_periods(n: int, day_groups: tuple = (1, 3, 7)) -> list[list[datetime]]:
    """
    Create multiple date groups for discount periods using get_random_date_group.
    Each group is a list of consecutive dates of length randomly selected from the day_groups tuple.

    :param n: Number of discount date groups to generate.
    :param day_groups: Tuple of possible group lengths (e.g., 1-day, 3-day, 7-day discounts). Default is (1, 3, 7).
    :return list[list[datetime]]: A 2D list where each inner list is a group of dates.
    """
    random.seed(42)
    final_list = []

    for _ in range(n):
        day_group = random.choice(day_groups)
        date_list = get_random_date_group(day_group)
        final_list.append(date_list)

    return final_list


discount_group = create_discount_periods(15)
discount_list = set()

for grp in discount_group:
    for date in grp:
        discount_list.add(date)


def apply_markup_and_round(price: float) -> float:
    """
    Apply a random markup to a base cost price and round it to a psychological price ending.
    The markup is sampled from a normal distribution centered around 25% with bounds between 15% and 75%.
    The final price is then adjusted to end with a commonly used psychological price ending (e.g., 0.29, 0.49, 0.99).

    :param price: The base cost price of the product.
    :return: The final marked-up and psychologically rounded price.
    """
    random.seed(42)
    # Apply markup (clipped normal between 15% and 75%)
    price_markup = np.clip(random.normalvariate(0.25, 0.1), 0.15, 0.75)
    new_price = price + (price_markup * price)

    # Choose a psychological ending randomly
    endings = [0.29, 0.49, 0.99]
    ending = random.choice(endings)

    # Round up to that ending
    base = math.floor(new_price)
    rounded_price = base + ending
    if new_price > rounded_price:
        rounded_price = base + 1 + ending  # move to next integer base with ending

    return round(rounded_price, 2)


def generate_rating():
    """Rating generator (0 to 5) with skew toward 3 to 5"""
    ratings = [0, 1, 2, 3, 4, 5]
    weights = [0.02, 0.03, 0.10, 0.30, 0.35, 0.20]  # Most ratings are 3–5
    return np.random.choice(ratings, p=weights)


def abbreviate(name):
    # Normalize and remove special characters
    name = name.lower()
    name = re.sub(r"[^a-z\s]", "", name)

    # Handle plurals like cookies → CKS, candies → CNDS
    if name.endswith("ies"):
        name = name[:-3] + "ys"
    elif name.endswith("s") and not name.endswith("ss"):
        name = name[:-1]

    # Drop vowels (except first letter if vowel)
    chars = [c for c in name if c.isalpha()]
    if not chars:
        return ""

    result = [chars[0]]
    vowels = {"a", "e", "i", "o", "u"}
    for c in chars[1:]:
        if c not in vowels:
            result.append(c)

    # Return up to 4 characters
    return "".join(result[:4]).upper()


def generate_unique_skus(f_categories):
    used = defaultdict(int)
    skus = {}

    for name in f_categories:
        abbr = abbreviate(name)
        # Ensure uniqueness
        count = used[abbr]
        used[abbr] += 1
        final = abbr if count == 0 else f"{abbr}{count + 1}"
        skus[name] = final

    return skus


# Right-skewed sampling for key drivers
def sample_right_skewed(base_mean, sigma):
    """
    Generates a right-skewed random variable using a log-normal distribution.

    This function is used to simulate major drivers of increased basket size
    such as holidays and discounts, where higher-than-average values occur
    more frequently. It shifts the distribution such that the majority of
    the samples are above the provided base_mean, mimicking real-world
    behavior where spending spikes during certain events.

    :param base_mean: Mean, which is log transformed.
    :param sigma: Standard deviation, higher values increase the skew and variability.
    :return: A right-skewed value greater than or around the base_mean.
    """
    np.random.seed(42)
    mu = math.log(max(base_mean, 0.01))
    return np.random.lognormal(mean=mu, sigma=sigma)


# Utility functions
def get_discount_flag(f_date, discount_dt_lst=()) -> tuple:
    """
    Checks the `holiday_lookup` dict keys to get the holiday name. If the holiday name is not present in the dict then
    `Normal Day` is returned with the respective discount flag, discount flag is 1 if the current date is in holiday
    lookup dict or is present in the `discount_dt_lst`

    In the orders' generator, there will be another check, as some products are not eligible for a discount, the split
    of basket size will favor more towards the discounted item

    :param f_date: Date to be checked
    :param discount_dt_lst: List of dates other than holidays when discounts will be provided
    :return: A tuple containing a discount flag and the holiday name
    """
    curr_holiday = holiday_lookup.get(f_date, "Normal Day")
    if curr_holiday != "Normal Day":
        return 1, curr_holiday
    if discount_dt_lst and f_date in discount_dt_lst:
        return 1, "Normal Day"
    return 0, "Normal Day"


def generate_age_grp_and_prob(group,
                              age_groups=((18, 22), (23, 30), (31, 40), (41, 50), (51, 60), (61, 70)),
                              emp_prob=(0.25, 0.30, 0.20, 0.10, 0.10, 0.05),
                              customer_prob=(0.22, 0.20, 0.14, 0.16, 0.12, 0.14)):
    """
    Generates a list of ages with certain given probability.
    :param age_groups: [(18, 22), (23, 30), (31, 40), (41, 50), (51, 60), (61, 70)]
    :param emp_prob:
    :param customer_prob:
    :param group: The probability of age groups.
    :return: Tuple of age list and their probability list
    """

    group_prob = emp_prob if group.lower() == "emp" else customer_prob

    ages = []
    probs = []

    for (start, end), grp_prob in zip(age_groups, group_prob):
        count = end - start + 1
        prob_per_age = grp_prob / count
        ages.extend(range(start, end + 1))
        probs.extend([prob_per_age] * count)

    # total probability to 1.0
    probs = np.array(probs)
    probs /= probs.sum()

    return ages, probs


def generate_unique_phone_numbers(size, area_codes=(312, 872), area_code_probs=(0.8, 0.2)):
    """
    Generates a list of unique phone numbers in the format +1(area_code)-prefix-line_number.
    """
    np.random.seed(42)
    phone_numbers = set()

    while len(phone_numbers) < size:
        area_code = np.random.choice(area_codes, p=area_code_probs)
        prefix = np.random.randint(100, 1000)
        line_number = np.random.randint(1000, 10000)
        phone = f"+1({area_code})-{prefix}-{line_number}"
        phone_numbers.add(phone)

    return list(phone_numbers)


def generate_unique_emails(size, names: list[str], phone_num: list[str],
                           email_domain=("gmail.com", "yahoo.com", "hotmail.com"),
                           email_domain_prob=(0.7, 0.2, 0.1)):
    """
    Generates a list of unique emails using full phone numbers for better uniqueness.
    """
    np.random.seed(42)
    email_set = set()
    email_list = []

    for i in range(size):
        name = names[i].lower().replace(" ", "")
        digits_only = ''.join(filter(lambda p: p.isdigit(), phone_num[i]))
        domain = np.random.choice(email_domain, p=email_domain_prob)

        email = f"{name}{digits_only}@{domain}"

        # Ensure uniqueness
        counter = 1
        while email in email_set:
            email = f"{name}{digits_only}_{counter}@{domain}"
            counter += 1

        email_set.add(email)
        email_list.append(email)

    return email_list


def generate_unique_addresses(n, region_neighborhoods, weights, f_chicago_streets):
    np.random.seed(42)
    addresses = set()
    region_neighborhoods = np.array(region_neighborhoods)

    while len(addresses) < n:
        # Choose a region-neighborhood pair based on population weight
        idx = np.random.choice(len(region_neighborhoods), p=weights)
        region, neighborhood = region_neighborhoods[idx]

        # Choose a random street in that neighborhood
        street = np.random.choice(f_chicago_streets[(region, neighborhood)])

        # Generate building and floor numbers
        building_number = np.random.randint(1, 10000)

        # Construct full address
        full_address = f"#{building_number}, {street}, {neighborhood}, {region}, Chicago"

        addresses.add(full_address)

    return list(addresses)


# ---- Basket Size Script ----
def basket_size_calculator(dt: datetime,
                           store_category,
                           discount_flag,
                           curr_holiday,
                           membership,
                           base_mean=15,
                           holiday_weight=1.5,
                           discount_weight=1.25,
                           seed=42) -> int:
    """
    Calculates the basket size for a customer purchase based on the given context.
    :param dt: Current Date(Datetime)
    :param store_category: List[str] values are ["High", "Medium", "Low"] these are the store category, which are
        nothing but a stores' popularity.
    :param discount_flag: Does the current product have a discount? Values = [1, 0] *In this script the discount flag
    is based on dates but in the actual orders generator discount will be based on products*.
    :param curr_holiday: American holiday names.
    :param membership: "Yes" or "No".
    :param base_mean: Base-mean for the basket size, middle point for further calculation.
    :param holiday_weight: Weightage for holidays, more will lead to holidays having higher basket sizes
    :param discount_weight: Same as `holiday_weight`
    :param seed: np random seed.
    :return:
    """
    np.random.seed(seed)

    # Draw base basket size
    base = np.random.normal(base_mean, 0.5)

    # Impact factors with std
    weekday_impact = np.random.normal(day_of_week_impact_dict[dt.weekday()], 0.10)
    store_impact = np.random.normal(store_cat_impact_dict[store_category], 0.10)
    member_impact = np.random.normal(customer_member_impact_dict[membership], 0.10)

    # Discount and holiday impacts
    discount_impact = (
        sample_right_skewed(discount_impact_dict[1], 0.15) if discount_flag else 1.0
    )

    is_holiday = curr_holiday != "Normal Day"
    holiday_base = holiday_impact_dict.get(curr_holiday, 1.0)
    holiday_impact = sample_right_skewed(holiday_base, 0.20) if is_holiday else 1.0

    # Final calculation
    core_value = base * weekday_impact * store_impact * member_impact
    holiday_bonus = holiday_weight * base * (holiday_impact - 1)
    discount_bonus = discount_weight * base * (discount_impact - 1)

    return max(1, int(core_value + holiday_bonus + discount_bonus))

def generate_customers9_df(n: int) -> pd.DataFrame:
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

    ages, probs = generate_age_grp_and_prob("cust")

    df = pd.DataFrame({
        "name": names,
        "age": np.random.choice(ages, size=n, p=probs),
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
    base_df["customer_id"] = [f"STRMRT_CSTMR_{i}" for i in range(1, total + 1)]

    # Reorder columns
    cols = ["customer_id"] + [col for col in base_df.columns if col != "customer_id"]
    return base_df[cols]


stores_df = generate_stores_df()
# Generate ages and probabilities
e_ages, e_probs = generate_age_grp_and_prob("emp")


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

            for i, role in enumerate(roles_list):
                for _ in range(emp_count):
                    curr_emp_id = f"STRMRT_EMP_{str_num}_{emp_id}"
                    curr_role = role
                    curr_salary = hourly_rate[i]
                    curr_store = store_id
                    gender_probability = gender_roles.get(role, [0.50, 0.50])
                    gender = np.random.choice(["Male", "Female"], p=gender_probability)

                    name = fake.name_male() if gender == "Male" else fake.name_female()

                    ph_number = (
                        f"+1({np.random.choice(area_codes, p=area_code_probs)})-"
                        + f"{np.random.randint(100, 999)}-"
                        + f"{np.random.randint(1000, 9999)}"
                    )

                    email = (
                        name.lower().replace(" ", "")
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

                    age = np.random.choice(e_ages, p=e_probs)

                    curr_emp_row = [
                        curr_emp_id,
                        curr_store,
                        name,
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
    f_stores_df = generate_stores_df()
    products = []
    for store_num, (_, store) in enumerate(f_stores_df.iterrows(), start=1):
        # Get the store details
        store_id = store["store_id"]
        store_size = store["store_size"]

        # get the product categories
        f_categories = category_and_products.keys()

        product_id = 1
        # loop through the categories
        for category in f_categories:
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
                    random.randint(1, 2)
                    if store_size == "Large"
                    else random.randint(3, 4)
                    if store_size == "Medium"
                    else random.randint(4, 5)
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
    # Get base product info
    prod_price_df = pd.read_csv(
        r"C:\Users\shrav\Data_Analysis_Projects\Big Projects\Project StarMart\Datasets\StarMart_Products.csv").loc[:,
                    ["product_id", "subcategory"]]

    # Assign markup based on subcategory mapping
    prod_price_df['markup'] = prod_price_df.apply(
        lambda row: multiplication_factor * product_markup.get(row['subcategory'], 1),
        axis=1
    ).round(2)

    # Convert flags to integers (1 or 0)
    prod_price_df["discount_flag_normal_day"] = prod_price_df["subcategory"].isin(normal_day_discount_items).astype(int)
    prod_price_df["discount_flag_holiday"] = prod_price_df["subcategory"].isin(holiday_discount_items).astype(int)

    # Define discount logic
    def apply_discount(row, day):
        discount_percentages = (
            np.arange(0.05, 0.20, 0.05) if day == "normal day"
            else np.arange(0.2, 0.50, 0.1)
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


# Define category filtering logic
def filter_categories(curr_holiday, curr_season):
    valid = set(categories)
    # seasonal pruning
    for s, cat in season_map.items():
        if s != curr_season:
            valid.discard(cat)
    # chilled snacks bias
    if curr_season == "Winter" and np.random.random() < 0.8:
        valid.discard("Chilled Snacks")
    # gifts logic
    if curr_holiday == "Normal Day" or np.random.random() < 0.1:
        valid.discard("Gifts")

    return tuple(valid)


def assign_weights(valid_categories, curr_holiday, curr_season):
    weights = {cat: 1.0 for cat in valid_categories}

    # Season-based
    for season_cat, factor in season_weights.get(curr_season, {}).items():
        if season_cat in weights:
            weights[season_cat] *= factor
    # Holiday-based
    for cat in holiday_weights.get(curr_holiday, []):
        if cat in weights:
            weights[cat] *= 1.4
    total = sum(weights.values())
    return {c: w / total for c, w in weights.items()} if total else weights


def predict_categories(n, curr_holiday, curr_season):
    valid = filter_categories(curr_holiday, curr_season)
    wts = assign_weights(valid, curr_holiday, curr_season)

    cats = list(valid)
    probs = [wts[c] for c in cats]
    k = min(n, len(cats))
    selected = list(np.random.choice(cats, size=k, replace=False, p=probs))

    counts = Counter(selected)
    while len(selected) < n:
        avail = [c for c in wts if counts[c] < 3]
        if not avail:
            break
        rem_w = [wts[c] for c in avail]
        p = np.array(rem_w) / sum(rem_w)
        c = np.random.choice(avail, p=p)
        selected.append(c)
        counts[c] += 1

    return selected

def generate_stocks_table():
    orders = pd.read_csv(base_dir / "StarMart_Orders.csv").loc[:, ["order_datetime", "quantity", "product_id"]]
    products = pd.read_csv(base_dir / "StarMart_Products.csv").loc[:, ["product_id", "shelf_life"]]

    # Shelf life groups
    products_grp_3 = products[products['shelf_life'] < 6]
    products_grp_6_12 = products[(products['shelf_life'] >= 6) & (products['shelf_life'] <= 12)]
    products_grp_15_30 = products[(products['shelf_life'] > 12) & (products['shelf_life'] <= 30)]
    products_grp_30_90 = products[(products['shelf_life'] > 30) & (products['shelf_life'] <= 90)]
    products_grp_90 = products[products['shelf_life'] > 90]

    # Merge orders with products by group
    orders_3 = orders.merge(products_grp_3, on=['product_id'])
    orders_6_12 = orders.merge(products_grp_6_12, on=['product_id'])
    orders_15_30 = orders.merge(products_grp_15_30, on=['product_id'])
    orders_30_90 = orders.merge(products_grp_30_90, on=['product_id'])
    orders_90 = orders.merge(products_grp_90, on=['product_id'])

    # Function to compute grouped sales
    def products_sold_grp(days, merged_df):
        merged_df['order_datetime'] = pd.to_datetime(merged_df['order_datetime'])
        merged_df = merged_df.sort_values('order_datetime')
        min_date = merged_df['order_datetime'].min()

        merged_df['period_start'] = (
                ((merged_df['order_datetime'] - min_date).dt.days // days) * days
        ).apply(lambda x: min_date + pd.Timedelta(days=x))

        grouped = (
            merged_df.groupby(['product_id', 'period_start'], as_index=False)
            .agg({'quantity': 'sum', 'shelf_life': 'min'})
            .rename(columns={'quantity': 'total_sold'})
            .sort_values(['product_id', 'period_start'])
        )
        return grouped

    # Apply grouping per shelf-life bucket
    sales_3 = products_sold_grp(3, orders_3)
    sales_6_12 = products_sold_grp(6, orders_6_12)
    sales_15_30 = products_sold_grp(15, orders_15_30)
    sales_30_90 = products_sold_grp(30, orders_30_90)
    sales_90 = products_sold_grp(90, orders_90)

    # Apply adjustments
    def add_extra(df, p):
        df['total_sold'] *= (1 + p / 100)
        df['total_sold'] = np.ceil(df['total_sold'])
        df['period_start'] = df['period_start'].dt.date
        return df

    # 15, 20, 22, 25, 30
    sales_3 = add_extra(sales_3, 10)
    sales_6_12 = add_extra(sales_6_12, 8)
    sales_15_30 = add_extra(sales_15_30, 10)
    sales_30_90 = add_extra(sales_30_90, 12)
    sales_90 = add_extra(sales_90, 15)

    # Combine all sales
    final_df = pd.concat(
        [sales_3, sales_6_12, sales_15_30, sales_30_90, sales_90],
        ignore_index=True
    )

    final_df = final_df.rename(columns={
        'period_start': 'restock_date',
        'total_sold': 'prod_lookup_qty'
    }).drop(columns='shelf_life')

    final_df['prod_lookup_qty'] = final_df['prod_lookup_qty'].astype(int)

    restock_dates = final_df[['restock_date']].drop_duplicates().sort_values(by='restock_date')

    return final_df, restock_dates


# -----------Vendors---------------
fake = Faker()


def fake_ein():
    np.random.seed(42)
    return f"{np.random.randint(10, 99)}-{np.random.randint(1000000, 9999999)}"


def generate_fake_vendors():
    np.random.seed(42)
    products_df = pd.read_csv(base_dir / "StarMart_Products.csv").loc[:, ["product_id", "subcategory", "cost_price"]]
    sub_categories = products_df["subcategory"].unique()

    cat_sku = generate_unique_skus(sub_categories)
    vendors = []
    used_names = set()
    v_id = 1

    for cat in sub_categories:
        num_vendors = 1

        for i in range(num_vendors):
            vendor_id = f"STRMRT_VNDR_{cat_sku[cat]}_{v_id}"

            # Ensure unique vendor names
            while True:
                vendor_name = fake.company()
                if vendor_name not in used_names:
                    used_names.add(vendor_name)
                    break

            delivery_fee = random.choice([20, 25, 35, 30])

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


# Create a DataFrame using list comprehension
def generate_stores_df():
    """
    Attributes: store_id, region, neighborhood, pop_density, store_size, parking_space, category
    :return:
    """
    f_stores_df = pd.DataFrame(
        [
            [region, *neighborhood_info,]  # Unpack neighborhood details into separate columns
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
            "zip_codes"
        ],
    )
    # store id
    f_stores_df["store_id"] = [f"STRMRT_STR_{i + 1:02d}" for i in range(len(f_stores_df))]

    # moving store_id to the start
    cols = f_stores_df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("store_id")))
    f_stores_df = f_stores_df[cols]

    return f_stores_df


# ------------------------------------------------------------------------------------------------------------------
np.random.seed(2025)
random.seed(2025)

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


#----------------------------------------------------------------------------------------------------------------------
# Customer df should already be created
customer_df = pd.read_csv(
    "C:/Users/shrav/Data_Analysis_Projects/Big Projects/Project StarMart/Datasets/StarMart_Customers.csv"
).loc[:, ["customer_id", "age", "membership", "recurring"]]

# Split the customer_df into recurring and non-recurring
recurring_ids = customer_df[customer_df["recurring"] == "Recurring"]['customer_id']
non_recurring_ids = customer_df[customer_df["recurring"] == "Non-Recurring"]['customer_id']
one_time_ids = customer_df[customer_df["recurring"] == "One Time Customer"]['customer_id']
customer_pool = []

for c_idx in recurring_ids:
    customer_pool.extend([c_idx] * random.randint(12, 18))  # Loyal: 8–14 orders
for c_idx in non_recurring_ids:
    customer_pool.extend([c_idx] * random.randint(3, 6))  # Mid: 2–5 orders
for c_idx in one_time_ids:
    customer_pool.append(c_idx)  # Just once

random.shuffle(customer_pool)

customer_dict = customer_df.set_index("customer_id").to_dict("index")
del customer_df


def expected_splits(n, k_min=1, k_max=15, s=0.1, c=30):
    """Sigmoid function mapping basket size to expected split count."""
    return k_min + (k_max - k_min) / (1 + np.exp(-s * (n - c)))


def random_split(n, k_max=20):
    """
    Generate a realistic split for basket of size n using a sigmoid-based number of splits.
    """
    if n <= 2:
        return [n]

    # determine expected number of splits (can have some randomness)
    expected = expected_splits(n, k_max=k_max)
    num_parts = max(1, int(np.random.normal(expected, expected * 0.2)))  # 20% randomness

    # ensure num_parts ≤ n
    num_parts = min(num_parts, n)

    # generate splits using Dirichlet distribution (smooth fractional randoms that sum to 1)
    weights = np.random.dirichlet(np.ones(num_parts))
    parts = np.round(weights * n).astype(int)

    # fix rounding
    diff = n - parts.sum()
    while diff != 0:
        fix_idx = random.randint(0, len(parts) - 1)
        parts[fix_idx] += 1 if diff > 0 else -1
        diff = n - parts.sum()

    parts = np.clip(parts, 1, None)
    return parts.tolist()


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
    base_customers = random.normalvariate(50, 5)

    # Store category multiplier with noise factor
    store_multipliers = {"High": 1.20,
                         "Medium": 0.85,
                         "Low": 0.65}

    store_multiplier = random.normalvariate(store_multipliers[category], 0.15)

    # Parking availability multiplier
    parking_multipliers = {
        "Very Limited": 0.95,
        "Limited": 0.97,
        "Moderate": 1.0,
        "Adequate": 1.03,
        "Spacious": 1.07,
    }
    parking_multiplier = random.normalvariate(parking_multipliers[avail_parking], 0.02)

    # Month multiplier with slight variation
    month_multipliers = {
        1: 0.70,
        2: 0.68,
        3: 0.72,
        4: 0.75,
        5: 0.70,
        6: 0.80,
        7: 0.82,
        8: 0.88,
        9: 0.93,
        10: 1.00,
        11: 1.05,
        12: 1.10,
    }
    month_multiplier = random.normalvariate(month_multipliers[curr_month], 0.10)

    # Weekday multiplier
    weekday_multipliers = {0: 1.0, 1: 0.85, 2: 0.90, 3: 1.05, 4: 1.1, 5: 1.2, 6: 1.15}
    weekday_multiplier = weekday_multipliers[curr_date.weekday()] * random.normalvariate(
        1.0, 0.02
    )

    # Holiday bonus
    holiday_bonus = 1.0
    if curr_date in high_traffic_periods:
        holiday_name = holiday_lookup.get(curr_date)
        f_holiday_weights = {
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
            "New Year": 1.48,
            "Halloween": 1.52,
            "Thanksgiving & Black Friday": 1.60,
            "Christmas": 1.75,
        }
        base_bonus = f_holiday_weights.get(holiday_name, 0.80)
        holiday_bonus = random.normalvariate(base_bonus, 0.2)

    # Discount impact
    discount_multiplier = 1.2 if is_discounted == 1 else 0.85
    discount_boost = random.normalvariate(discount_multiplier, 0.15)

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


def dicts_with_hierarchy_skew(
        df,
        sub_skew: float = 1.5,  # Light skew for subcategories
        prod_skew: float = 4.5,  # Stronger skew for products
        var_skew: float = 3.5,  # Moderate skew for variants
        seed: int | None = 42
):
    """
    Build three flat probability dictionaries:
    - (store, category) → subcategory probabilities
    - (store, category, subcategory) → product probabilities
    - (store, category, subcategory, product) → variant probabilities
    """

    rng = np.random.default_rng(seed)

    def skewed_probs(n: int, skew: float):
        if n <= 0:
            return []
        weights = rng.random(n) ** skew
        weights /= weights.sum()
        return weights.tolist()

    subcategory_probs = {}
    product_probs = {}
    variant_probs = {}

    for (store_id, category), cat_df in df.groupby(["store_id", "category"]):
        # --- Level 1: Subcategory ---
        subcats = cat_df["subcategory"].unique().tolist()
        subcategory_probs[(store_id, category)] = {
            "items": subcats,
            "probs": skewed_probs(len(subcats), sub_skew)
        }

        for subcat, sub_df in cat_df.groupby("subcategory"):
            # --- Level 2: Product ---
            products = sub_df["product_name"].unique().tolist()
            product_probs[(store_id, category, subcat)] = {
                "items": products,
                "probs": skewed_probs(len(products), prod_skew)
            }

            for product, prod_df in sub_df.groupby("product_name"):
                # --- Level 3: Variant ---
                variants = prod_df["variant"].tolist()
                variant_probs[(store_id, category, subcat, product)] = {
                    "items": variants,
                    "probs": skewed_probs(len(variants), var_skew)
                }

    return subcategory_probs, product_probs, variant_probs


def choose_item(
        store_id,
        category: str,
        category_df: pd.DataFrame,
        subcategory_probs_d: dict,
        product_probs_d: dict,
        variant_probs_d: dict
):
    """
    Select one product row from a given category using precomputed hierarchical probabilities.
    Assumes category_df_dict[category] contains only items from a single store.
    """

    # --- Step 1: Choose subcategory ---
    subcategory_items_probs = subcategory_probs_d[(store_id, category)]
    sub_category_items, sub_category_probs = subcategory_items_probs['items'], subcategory_items_probs['probs']
    sub_category = random.choices(sub_category_items, weights=sub_category_probs, k=1)[0]

    # --- Step 2: Choose product within subcategory ---
    product_items_probs = product_probs_d[(store_id, category, sub_category)]
    product_items, product_probs = product_items_probs['items'], product_items_probs['probs']
    product = random.choices(product_items, weights=product_probs, k=1)[0]

    # --- Step 3: Choose variant within product ---
    variant_items_probs = variant_probs_d[(store_id, category, sub_category, product)]
    variant_items, variant_probs = variant_items_probs['items'], variant_items_probs['probs']
    variant = random.choices(variant_items, weights=variant_probs, k=1)[0]

    # --- Step 4: Retrieve item row ---
    mask = (
            (category_df["subcategory"] == sub_category)
            & (category_df["product_name"] == product)
            & (category_df["variant"] == variant)
    )
    item_row = category_df.loc[mask].iloc[0]

    return item_row


def generate_orders_file(
        orders_file_path, start_date: datetime, end_date: datetime
) -> None:
    """Generates orders and orders_summary csv file from start date to end date"""

    customer_pointer = 0
    order_id = 1
    line_order_id = 1
    curr_date = start_date

    products_df = pd.read_csv(
        r"C:\Users\shrav\Data_Analysis_Projects\Big Projects\Project StarMart\Datasets\StarMart_Products.csv").loc[
                  :, ["product_id", "store_id", "category", "subcategory", "cost_price", "variant", "product_name"]
                  ]

    subcategory_probs_d, product_probs_d, variant_probs_d = dicts_with_hierarchy_skew(products_df)

    f_stores_df = generate_stores_df()
    employee_df = generate_employee_df().loc[:, ["emp_id", "store_id", "role"]]

    category_df_dict = {}
    cashier_df_dict = {}

    for store_id in f_stores_df["store_id"]:
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
                "final_price",
                "return_time",
                "money_return"
            ]
        )

        while curr_date < end_date:
            day = curr_date.day
            month = curr_date.month
            year = curr_date.year

            discount, curr_holiday = get_discount_flag(curr_date, discount_list)
            curr_season = get_season(curr_date)

            for _, store in f_stores_df.iterrows():
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
                    line_cashier = cashier_df.iloc[random.randint(0, len(cashier_df) - 1)]
                    line_cashier_id = line_cashier["emp_id"]

                    # get customer info
                    c_id = customer_pool[customer_pointer]
                    membership = customer_dict[c_id]["membership"]

                    basket_size = basket_size_calculator(
                        curr_date, store_category, discount, curr_holiday, membership
                    )

                    cart_size_split = random_split(basket_size)
                    num_of_categories = len(cart_size_split)
                    purchase_list = predict_categories(
                        num_of_categories, curr_holiday, curr_season
                    )

                    curr_time = order_times[customer]
                    for i, category in enumerate(purchase_list):
                        # sort the product dataframe based on the current category
                        category_df = category_df_dict[(store_id, category)]

                        item_row = choose_item(
                            store_id,
                            category,
                            category_df,
                            subcategory_probs_d,
                            product_probs_d,
                            variant_probs_d)

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
                        final_price = round(price_after_markup * (1 - membership_discount), 2)

                        # cap orders to 70 per product
                        quantity = cart_size_split[i]

                        if quantity > 70:
                            continue

                        # cancellations check
                        if random.random() < 0.04:
                            return_time_sec = random.randint(10_800, 1_209_600)
                            if return_time_sec < 604_800:
                                return_time = curr_time + timedelta(seconds=return_time_sec)
                                if random.random() < 0.40:
                                    money_return = True
                        else:
                            return_time = datetime(year=1900, month=1, day=1)
                            money_return = False

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
                            final_price,
                            return_time,
                            money_return
                        ]
                        order_writer.writerow(order_row)

                        line_order_id += 1

                    order_id += 1
                    customer_pointer += 1

                    if customer_pointer >= len(customer_pool):
                        customer_pointer = 0
            curr_date += timedelta(days=1)
            print(curr_date)


def generate_orders_dataframe_test(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Generates a Pandas DataFrame of simulated orders between start_date and end_date.

    Returns:
        pd.DataFrame: Columns include line_order_id, order_id, customer_id, product_id,
                      store_id, cashier_id, order_datetime, quantity, final_price,
                      return_time, money_return.
    """
    customer_pointer = 0
    order_id = 1
    line_order_id = 1
    curr_date = start_date

    products_df = generate_product_df(stats=False).loc[
                  :, ["product_id", "store_id", "category", "cost_price"]
                  ]

    f_stores_df = generate_stores_df()
    employee_df = generate_employee_df().loc[:, ["emp_id", "store_id", "role"]]

    category_df_dict = {}
    cashier_df_dict = {}

    for store_id in f_stores_df["store_id"]:
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
    markup_dict = markup_df.set_index("product_id")["markup"].to_dict()

    holiday_discount_dict = markup_df.set_index("product_id")["holiday_discount"].to_dict()
    normal_discount_dict = markup_df.set_index("product_id")["normal_day_discount"].to_dict()
    del markup_df, employee_df

    # Store all generated orders here
    all_orders = []

    while curr_date < end_date:
        day = curr_date.day
        month = curr_date.month
        year = curr_date.year

        discount, curr_holiday = get_discount_flag(curr_date, discount_list)
        curr_season = get_season(curr_date)

        for _, store in f_stores_df.iterrows():
            store_id = store["store_id"]
            parking = store["parking_space"]
            store_category = store["category"]

            cashier_df = cashier_df_dict[store_id]

            # customer for a day
            curr_customer_count = get_customer_count(
                year, month, day, store_category, parking, discount
            )

            # order times for the current day
            order_times = generate_sorted_order_times(curr_customer_count, curr_date)

            for customer in range(curr_customer_count):
                # get cashier info
                line_cashier = cashier_df.iloc[random.randint(0, len(cashier_df) - 1)]
                line_cashier_id = line_cashier["emp_id"]

                # get customer info
                c_id = customer_pool[customer_pointer]
                membership = customer_dict[c_id]["membership"]

                basket_size = basket_size_calculator(
                    curr_date, store_category, discount, curr_holiday, membership
                )

                cart_size_split = random_split(basket_size)
                num_of_categories = len(cart_size_split)
                purchase_list = predict_categories(
                    num_of_categories, curr_holiday, curr_season
                )

                curr_time = order_times[customer]
                for i, category in enumerate(purchase_list):
                    # sort the product dataframe based on the current category
                    category_df = category_df_dict[(store_id, category)]
                    item_row = category_df.iloc[random.randint(0, len(category_df) - 1)]

                    # get item info
                    p_id = item_row["product_id"]
                    cost_price = item_row["cost_price"]

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

                    if quantity > 70:
                        continue

                    # Returns check (4% chance)
                    if random.random() < 0.04:
                        return_time_sec = random.randint(10_800, 1_209_600)
                        if return_time_sec < 604_800:  # within 7 days
                            return_time = curr_time + timedelta(seconds=return_time_sec)
                            money_return = random.random() < 0.40
                        else:
                            return_time = datetime(1900, 1, 1)
                            money_return = False
                    else:
                        return_time = datetime(1900, 1, 1)
                        money_return = False

                    # Append the order row
                    all_orders.append([
                        f"STRMRT_LINE_ID_{line_order_id}",
                        f"STRMRT_ORDR_{order_id}",
                        c_id,
                        p_id,
                        store_id,
                        line_cashier_id,
                        curr_time,
                        quantity,
                        final_price,
                        return_time,
                        money_return,
                    ])

                    line_order_id += 1

                order_id += 1
                customer_pointer += 1

                if customer_pointer >= len(customer_pool):
                    customer_pointer = 0
        curr_date += timedelta(days=1)

    # Convert to DataFrame
    orders_df = pd.DataFrame(
        all_orders,
        columns=[
            "line_order_id",
            "order_id",
            "customer_id",
            "product_id",
            "store_id",
            "cashier_id",
            "order_datetime",
            "quantity",
            "final_price",
            "return_time",
            "money_return",
        ],
    )

    # Convert datetime
    orders_df["order_datetime"] = pd.to_datetime(orders_df["order_datetime"])
    orders_df["return_time"] = pd.to_datetime(orders_df["return_time"])

    print(start_date.year, "Done!")

    return orders_df
