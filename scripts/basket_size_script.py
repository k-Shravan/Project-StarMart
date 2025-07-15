import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from custom_functions import sample_right_skewed, get_discount_flag, discount_list
from raw_data import (
    high_traffic_periods,
    holiday_impact_dict,
    day_of_week_impact_dict,
    store_cat_impact_dict,
    customer_member_impact_dict,
    discount_impact_dict,
)


def basket_size_calculator(dt: datetime,
                           store_category,
                           discount_flag,
                           curr_holiday,
                           membership,
                           base_mean=15,
                           holiday_weight=1.5,
                           discount_weight=1.25) -> int:
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
    :return:
    """
    np.random.seed(42)

    # Draw base basket size
    base = np.random.normal(base_mean, 0.5)

    # Impact factors
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


def basket_size_simulation(start_dt, end_dt, samples=10000, base_mean=7):
    """
    Creates a dataframe of containing `samples` amount of records with attributes:
    date, holiday, discount, store_category, membership, basket_size.
    :param start_dt: Starting date (year 2024)
    :param end_dt: Ending date (year 2024)
    :param samples: Number of records needed
    :param base_mean: Starting value for the base value
    :return: pd.DataFrame
    """
    np.random.seed(42)
    days = (end_dt - start_dt).days
    dates = []
    for _ in range(samples):
        if np.random.rand() < 0.3:
            dates.append(np.random.choice(list(high_traffic_periods)))
        else:
            dates.append(start_dt + timedelta(days=np.random.randint(days + 1)))
    np.random.shuffle(dates)

    flags, hols = zip(*[get_discount_flag(d, discount_list) for d in dates])
    stores = np.random.choice(list(store_cat_impact_dict.keys()), size=samples)
    members = np.random.choice(list(customer_member_impact_dict.keys()), size=samples)

    basket_sizes = [
        basket_size_calculator(
            dt=dates[i],
            store_category=stores[i],
            discount_flag=flags[i],
            curr_holiday=hols[i],
            membership=members[i],
            base_mean=base_mean,
        )
        for i in range(samples)
    ]

    return pd.DataFrame(
        {
            "date": dates,
            "holiday": hols,
            "discount": flags,
            "store_category": stores,
            "membership": members,
            "basket_size": basket_sizes,
        }
    )
