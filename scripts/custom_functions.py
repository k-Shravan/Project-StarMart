import math
from datetime import datetime, timedelta
from raw_data import (
    high_traffic_periods,
    holiday_lookup
)
import numpy as np
import calendar
import re
from collections import defaultdict


def get_random_date_group(day_group: int, year: int = 2024) -> list[datetime]:
    """
    Generate a list of consecutive dates in chronological order, avoiding high-traffic periods.
    Dates are selected such that none of them fall within predefined high-traffic periods (e.g., holidays),
    which already have active discounts.
    :param day_group: Number of consecutive dates to return.
    :param year: Year to generate dates for. Default is 2024.
    :return: List[datetime]: List of consecutive dates in datetime format.
    """
    np.random.seed(42)

    while True:
        month = np.random.randint(1, 13)
        day = np.random.randint(1, calendar.monthrange(year, month)[1] + 1)
        start_date = datetime(year, month, day)

        # Check the full range for overlap
        if any(
                (start_date + timedelta(days=i)) in high_traffic_periods
                for i in range(day_group)
        ):
            continue

        return [(start_date + timedelta(days=i)) for i in range(day_group)]


def create_discount_periods(
        n: int, day_groups: tuple = (1, 3, 7)
) -> list[list[datetime]]:
    """
    Create multiple date groups for discount periods using get_random_date_group.
    Each group is a list of consecutive dates of length randomly selected from the day_groups tuple.

    :param n: Number of discount date groups to generate.
    :param day_groups: Tuple of possible group lengths (e.g., 1-day, 3-day, 7-day discounts). Default is (1, 3, 7).
    :return list[list[datetime]]: A 2D list where each inner list is a group of dates.
    """
    np.random.seed(42)
    final_list = []

    for _ in range(n):
        day_group = np.random.choice(day_groups)
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

    Parameters:
        price (float): The base cost price of the product.

    Returns:
        float: The final marked-up and psychologically rounded price.
    """
    np.random.seed(42)
    # Apply markup (clipped normal between 15% and 75%)
    price_markup = np.clip(np.random.normal(0.25, 0.1), 0.15, 0.75)
    new_price = price + (price_markup * price)

    # Choose a psychological ending randomly
    endings = [0.29, 0.49, 0.99]
    ending = np.random.choice(endings)

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


def generate_unique_skus(categories):
    used = defaultdict(int)
    skus = {}

    for name in categories:
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
        prob_per_age = grp_prob / count  # Distribute group prob equally among ages
        ages.extend(range(start, end + 1))
        probs.extend([prob_per_age] * count)

    # Normalize to ensure that the total probability is 1.0
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
        prefix = np.random.randint(100, 1000)  # 100 to 999 inclusive
        line_number = np.random.randint(1000, 10000)  # 1000 to 9999 inclusive
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
        digits_only = ''.join(filter(lambda p: p.isdigit(), phone_num[i]))  # Full phone number digits
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


def generate_unique_addresses(n, region_neighborhoods, weights, chicago_streets):
    np.random.seed(42)
    addresses = set()
    region_neighborhoods = np.array(region_neighborhoods)

    while len(addresses) < n:
        # Choose a region-neighborhood pair based on population weight
        idx = np.random.choice(len(region_neighborhoods), p=weights)
        region, neighborhood = region_neighborhoods[idx]

        # Choose a random street in that neighborhood
        street = np.random.choice(chicago_streets[(region, neighborhood)])

        # Generate building and floor numbers
        building_number = np.random.randint(1, 10000)

        # Construct full address
        full_address = f"#{building_number}, {street}, {neighborhood}, {region}, Chicago"

        addresses.add(full_address)

    return list(addresses)
