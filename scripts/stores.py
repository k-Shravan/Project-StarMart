from raw_data import chicago_regions
import pandas as pd


# Create a DataFrame using list comprehension
def generate_stores_df():
    """
    Attributes: store_id, region, neighborhood, pop_density, store_size, parking_space, category
    :return:
    """
    stores_df = pd.DataFrame(
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
    stores_df["store_id"] = [f"STRMRT_STR_{i + 1:02d}" for i in range(len(stores_df))]

    # moving store_id to the start
    cols = stores_df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("store_id")))
    stores_df = stores_df[cols]

    return stores_df
