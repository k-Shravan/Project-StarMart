from faker import Faker
import numpy as np
import pandas as pd
from stores import generate_stores_df
from raw_data import (
    store_roles_and_hourly_rates,
    gender_roles,
    chicago_regions,
    chicago_streets,
)
from custom_functions import generate_age_grp_and_prob

stores_df = generate_stores_df()

fake = Faker()

# Generate ages and probabilities
ages, probs = generate_age_grp_and_prob("emp")


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

                    age = np.random.choice(ages, p=probs)

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
