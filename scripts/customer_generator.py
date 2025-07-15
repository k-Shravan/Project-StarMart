from faker import Faker
import numpy as np
import pandas as pd
from raw_data import (chicago_streets,
                      chicago_regions)
from custom_functions import (generate_age_grp_and_prob,
                              generate_unique_emails,
                              generate_unique_phone_numbers,
                              generate_unique_addresses)

fake = Faker()


# Function to generate customers
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
