import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from raw_data import (
    holiday_impact,
    family_impact,
    income_impact,
    store_impact,
    discount_impact,
    month_impact,
    daily_impact,
    high_traffic_periods,
    holiday_lookup,
)


def get_discount_flag(date, discount_dt_lst=None) -> tuple:
    """
    Check whether the given date is a holiday or in the discount date list.
    Returns (1, holiday_name) if it's a holiday or discounted, else (0, "Normal Day").
    """
    curr_holiday = holiday_lookup.get(date, "Normal Day")

    if curr_holiday != "Normal Day":
        return 1, curr_holiday

    if discount_dt_lst is not None and date in discount_dt_lst:
        return 1, "Normal Day"

    return 0, "Normal Day"


# Main Data Generation
def generate_cart_dataset(
        samples: int,
        start_dt: str,
        end_dt: str,
        multiplier=1,
        p_stats=True,
        p_graphs=True,
        seed=42,
        holiday_probability=0.2,
        base_mean=8,
        base_std=1.5,
) -> pd.DataFrame:
    """
    Generate a semi realistic dataset to show trends in cart size based on factors such as holidays, income of a person,
    number of family_members, purchase month, purchase day, and store effect.

    :param samples: Number of rows in the dataset
    :param start_dt: Starting date of the dataset(curr yr 2024, to change go to raw_data.py -> holiday_discounts)
    :param end_dt: Ending date of the dataset(curr yr 2024, to change go to raw_data.py -> holiday_discounts)
    :param multiplier: Multiplier for the base mean
    :param p_stats: prints the statistics for the current dataset
    :param p_graphs: plots the distribution for the current dataset
    :param seed: np seed
    :param holiday_probability: Percentage of dates to be holidays in the dataset
    :param base_mean: mean of the baseline value increase it to increase cart_size
    :param base_std: standard deviation of baseline
    :return: DataFrame containing the dataset
    """

    np.random.seed(seed)

    # creating lists to iterate through during data generation

    # Date range
    start_date = datetime.strptime(start_dt, "%Y-%m-%d")
    end_date = datetime.strptime(end_dt, "%Y-%m-%d")
    date_range = (end_date - start_date).days

    dates = []
    for _ in range(samples):
        if np.random.rand() < holiday_probability:
            date = np.random.choice(list(high_traffic_periods))
            dates.append(date)
        else:
            # pick a random normal date
            date = start_date + timedelta(days=np.random.randint(0, date_range + 1))
            dates.append(date)

    np.random.shuffle(dates)

    # random 10% of the samples will be discount, a list of datetime can also be provided in raw data
    discount_sample = int(samples * 0.1)
    discount_dates = dates[:discount_sample]

    # Convert the date ranges to datetime
    dates = pd.to_datetime(dates)
    discount_dates = pd.to_datetime(discount_dates)

    # Generate income
    # this will get an income range which is skewed towards low income
    income = np.random.lognormal(mean=4.2, sigma=0.35, size=samples) * 1000
    income = np.round(np.clip(income, 35000, 150000)).astype(int)

    # Family size
    family_size: np.ndarray[int] = np.random.choice(
        [1, 2, 3, 4, 5, 6], size=samples, p=[0.15, 0.25, 0.24, 0.2, 0.1, 0.06]
    )

    # Store location
    store_locations: np.ndarray[str] = np.random.choice(
        ["High", "Medium", "Low"], size=samples
    )

    # Prepare columns
    discount_flags = []
    holiday_names = []
    cart_sizes = []

    for i in range(samples):
        curr_date, curr_income, cur_family_size, curr_store_size = (
            dates[i],
            int(income[i]),
            family_size[i],
            store_locations[i],
        )

        # get the cart size
        curr_cart_size = cart_size_calculator(
            curr_date,
            curr_income,
            cur_family_size,
            curr_store_size,
            discount_dt_lst=discount_dates,
            multiplier=multiplier,
            base_mean=base_mean,
            base_std=base_std,
        )

        discount_flag, curr_holiday = get_discount_flag(curr_date, discount_dates)
        discount_flags.append(discount_flag)
        holiday_names.append(curr_holiday)
        cart_sizes.append(curr_cart_size)

    # Build DataFrame
    df = pd.DataFrame(
        {
            "date": dates,
            "income": income,
            "family_size": family_size,
            "store_location": store_locations,
            "discount_flag": discount_flags,
            "holiday": holiday_names,
            "cart_size": cart_sizes,
        }
    )

    # print optional stats or graphs to visualize, or to tweak the data
    if p_stats:
        mean_all = df["cart_size"].mean()
        mean_holiday = df.loc[df["discount_flag"] == 1, "cart_size"].mean()
        mean_normal = df.loc[df["discount_flag"] == 0, "cart_size"].mean()
        print(f"Overall Mean Cart Size: {mean_all:.2f}")
        print(f"Median Cart Size: {df['cart_size'].median()}")
        print(f"Std Dev of Cart Size: {df['cart_size'].std():.2f}")

        print(f"Mean Cart Size (Holiday): {mean_holiday:.2f}")
        print(f"Mean Cart Size (Normal): {mean_normal:.2f}")

    if p_graphs:
        # plot the density plot for the overall cart size
        plt.figure(figsize=(10, 6))
        sns.kdeplot(df["cart_size"], fill=True)

        # Add mean and median lines
        plt.axvline(df["cart_size"].mean(), linestyle="--", color="blue", label="Mean")
        plt.axvline(
            df["cart_size"].median(), linestyle="-.", color="red", label="Median"
        )

        # Labels and title
        plt.xlabel("Cart Size")
        plt.ylabel("Density")
        plt.title("Cart Size Distribution")
        plt.legend()
        plt.show()

        # plot the density plot for normal days and holidays

        # holiday group
        holiday_grp = df[df["holiday"] != "Normal Day"]
        normal_grp = df[df["holiday"] == "Normal Day"]

        # Plot
        plt.figure(figsize=(10, 6))
        sns.kdeplot(holiday_grp["cart_size"], label="Holiday", fill=True, color="blue")
        sns.kdeplot(normal_grp["cart_size"], label="No Holiday", fill=True, color="red")

        # Labels and title
        plt.xlabel("Cart Size")
        plt.ylabel("Density")
        plt.title(
            "Cart Size Distribution during Holiday vs No Holiday (Discounts may be present)"
        )
        plt.legend()
        plt.tight_layout()
        plt.show()

    return df


def cart_size_calculator(
        dt: str | datetime,
        income: int,
        family_size: int,
        store_size: str,
        multiplier: float = 1,
        base_mean: float = 8,
        base_std: float = 1.5,
        discount_dt_lst=None,
) -> int:
    """
    Calculates cart size(how many items a customer purchases) based on the date, customer income, family size, store -
    size, discounts(based on holidays, extra discounts can be provided by the list) and holidays(different holidays have
    different impacts).

    :param dt: Date for which the cart size needs to be determined
    :param income: Income of the customer
    :param family_size: Number of members in the customers family
    :param store_size: Size of the store
    :param multiplier: Percentage tweaker for the other features(current 100%)
    :param base_mean: starting point for the cart, although there are features that decrease the cart size the overall
                      effect is positive, so start with lower mean or test it with cart_size_script and find what the
                      final value should be.
    :param base_std: Standard deviation for the base mean
    :param discount_dt_lst: Holidays are considered as discounts by default, if additional holidays dates need to be
                     considered as discounts provide a list of date strings **Must Be Datetime Elements**
    :return: Cart size for the features provided
    """

    # prerequisites
    # given date can be string or datetime
    if isinstance(dt, str):
        curr_date = datetime.strptime(dt, "%Y-%m-%d")
    else:
        curr_date = dt

    discount_flag, curr_holiday = get_discount_flag(curr_date, discount_dt_lst)

    curr_month = curr_date.month
    curr_day = curr_date.weekday()

    # effects
    # 1) Baseline
    baseline = np.random.normal(base_mean, base_std)  # mean=3.5, std=1.5

    # additional noice
    a = 0.1  # mean
    b = 0.2  # std

    # 2) Family effect
    fam_effect = family_impact.get(family_size) + np.random.normal(a, b)

    # 3) Income effect
    if income < 50000:
        income_effect = income_impact.get("Low") - np.random.normal(a, b)
    elif income < 100000:
        income_effect = income_impact.get("Medium") - np.random.normal(a, b)
    else:
        income_effect = income_impact.get("High") - np.random.normal(a, b)

    # 4) Month effect
    month_eff = month_impact.get(curr_month) + np.random.normal(a, b)

    # 5) Weekend effect
    wkd_eff = daily_impact.get(curr_day) - np.random.normal(a, b)

    # 6) Store location effect
    store_effect = store_impact.get(store_size) + np.random.normal(a, b)

    # 7) Holiday effect
    no_holiday_effect = np.random.normal(-0.5, 0.20)
    holiday_effect = holiday_impact.get(
        curr_holiday, no_holiday_effect
    ) + np.random.normal(a, b)

    # 8) Discount effect
    discount_effect = discount_impact.get(discount_flag) + np.random.normal(a, b)

    # 9) Sum all effects
    total_items = baseline * (
            multiplier
            + fam_effect
            + income_effect
            + month_eff
            + wkd_eff
            + store_effect
            + holiday_effect
            + discount_effect
    )

    return max(1, int(total_items))
