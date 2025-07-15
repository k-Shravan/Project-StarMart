import numpy as np
from collections import Counter

# Define product categories
categories = {
    "Bakery & Desserts",
    "Beverages & Water",
    "Breakfast",
    "Candy",
    "Cleaning Supplies",
    "Gifts",
    "Household Items",
    "Grocery",
    "Meat and Seafood",
    "Pantry and Dry Goods",
    "Paper & Plastic Products",
    "Snacks",
    "Winter Seasonal",
    "Spring Seasonal",
    "Summer Seasonal",
    "Fall Seasonal",
    "Chilled Snacks",
}

season_map = {
    "Winter": "Winter Seasonal",
    "Spring": "Spring Seasonal",
    "Summer": "Summer Seasonal",
    "Fall": "Fall Seasonal",
}

season_weights = {
    "Winter": {"Winter Seasonal": 1.75, "Summer Seasonal": 0},
    "Spring": {"Spring Seasonal": 1.5},
    "Summer": {"Summer Seasonal": 1.75, "Winter Seasonal": 0},
    "Fall": {"Fall Seasonal": 1.5},
}

holiday_weights = {
    "Thanksgiving & Black Friday": [
        "Grocery",
        "Pantry and Dry Goods",
        "Bakery & Desserts",
        "Meat and Seafood",
        "Gifts"
    ],
    "Christmas/New Year": [
        "Gifts",
        "Bakery & Desserts",
        "Meat and Seafood"
    ],
    "Easter": [
        "Grocery",
        "Candy",
        "Bakery & Desserts"],
    "Halloween": ["Candy", "Snacks"],
    "Independence Day": [
        "Meat and Seafood",
        "Snacks",
        "Beverages & Water"
    ],
    "Valentine's Day": [
        "Gifts",
        "Bakery & Desserts",
        "Candy"
    ],
}


# Define category filtering logic
def filter_categories(customer_age, curr_holiday, curr_season):
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
    # age pruning
    if customer_age < 25:
        valid.discard("Cleaning Supplies")
    elif customer_age > 55:
        valid.discard("Candy")
    return tuple(valid)


def assign_weights(valid_categories, customer_age, curr_holiday, curr_season):
    weights = {cat: 1.0 for cat in valid_categories}
    # Age-based boosts
    if 18 <= customer_age <= 25:
        for cat in ["Snacks", "Beverages & Water", "Breakfast", "Candy"]:
            weights[cat] = weights.get(cat, 0) * 1.2
        for cat in ["Household Items", "Cleaning Supplies"]:
            weights[cat] = weights.get(cat, 0) * 0.85
    elif 26 <= customer_age <= 50:
        for cat in ["Grocery", "Meat and Seafood", "Cleaning Supplies", "Pantry and Dry Goods"]:
            weights[cat] = weights.get(cat, 0) * 1.3
    elif customer_age > 50:
        for cat in ["Pantry and Dry Goods", "Grocery", "Household Items"]:
            weights[cat] = weights.get(cat, 0) * 1.4
        for cat in ["Candy", "Snacks", "Beverages & Water"]:
            weights[cat] = weights.get(cat, 0) * 0.6
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


def predict_categories(n, customer_age, curr_holiday, curr_season):
    valid = filter_categories(customer_age, curr_holiday, curr_season)
    wts = assign_weights(valid, customer_age, curr_holiday, curr_season)

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

