import os
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# Read data.csv from the same folder as this script, so it runs on any clone
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data.csv')

if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(
        f"No CSV found at {DATA_PATH}. "
        "Make sure data.csv sits in the same folder as this script."
    )

data = pd.read_csv(DATA_PATH)

# 1. Standardize periodicity to match years
data.insert(0, 'Periodicity', data['Tenor (Maturity)'])
data['Periodicity'] = data['Periodicity'].str.split('-').str[0].astype(float)
data.loc[data.index[0:3], 'Periodicity'] = data.loc[data.index[0:3], 'Periodicity'] / 12
data = data.drop(columns=['Tenor (Maturity)'])

# 2. Convert percentage strings to decimal floats
for col in ['Baseline Yield (Spot Rate)', '2-Year Shock Curve', '5-Year Shock Curve', '10-Year Shock Curve']:
    data[col] = data[col].str.rstrip('%').astype(float) / 100

# 3. Define Bond Pricing Function with Odd-Period Logic
def calculate_bond_price(bond_tenor, bond_coupon, bond_face_value, coupon_frequency, yield_column='Baseline Yield (Spot Rate)'):
    """
    Calculates bond price handling annual, semi-annual, or quarterly frequencies
    by dynamically interpolating missing spot curve rates and factoring in odd periods.
    """

    # Create an interpolation function from CSV data
    interpolate_curve = interp1d(data['Periodicity'], data[yield_column], kind='linear', fill_value="extrapolate")

    # Calculate the remaining fraction (time from today to the first coupon payment)
    # Examples: 10.6 returns 0.6 | 10.5 returns 0.5 | 5.25 (quarterly) returns 0.25
    period_length = 1.0 / coupon_frequency
    stub = bond_tenor % period_length
    if np.isclose(stub, 0):
        stub = period_length  # Clean integer maturities start exactly one full period out

    # Generate the precise timeline array of cash flow dates (e.g., [0.6, 1.6, ..., 10.6])
    cash_flow_times = np.arange(stub, bond_tenor + 0.01, period_length)

    coupon_payment = (bond_coupon / coupon_frequency) * bond_face_value
    total_price = 0.0

    # Loop sequentially through the actual chronological payment times
    for t_years in cash_flow_times:
        # Determine cash flow (Regular coupon vs. terminal payment)
        if np.isclose(t_years, bond_tenor):
            cash_flow = bond_face_value + coupon_payment
        else:
            cash_flow = coupon_payment

        # Get the interpolated annualized rate matching this specific decimal time
        annual_spot_rate = float(interpolate_curve(t_years))

        # Discount to Present Value using the fractional year as the true exponent
        present_value = cash_flow / ((1 + annual_spot_rate) ** t_years)
        total_price += present_value

    return round(total_price, 2)

# 4. Define your bond portfolio
bonds = [
    {
        'name': 'Bond_1',
        'bond_tenor': 5,
        'bond_coupon': 0.08,
        'bond_face_value': 1000.0,
        'coupon_frequency': 1
    },
    {
        'name': 'Bond_2',
        'bond_tenor': 10,
        'bond_coupon': 0.05,
        'bond_face_value': 1000.0,
        'coupon_frequency': 1
    },
    {
        'name': 'Bond_3',
        'bond_tenor': 15,
        'bond_coupon': 0.08,
        'bond_face_value': 1000.0,
        'coupon_frequency': 1
    }
]

# 5. Define yield curves to test
yield_curves = ['Baseline Yield (Spot Rate)', '5-Year Shock Curve', '10-Year Shock Curve']

# 6. Loop through bonds and calculate prices
results = []

for bond in bonds:
    bond_results = {'Bond_ID': bond['name']}

    for curve in yield_curves:
        price = calculate_bond_price(
            bond['bond_tenor'],
            bond['bond_coupon'],
            bond['bond_face_value'],
            bond['coupon_frequency'],
            curve
        )
        bond_results[curve] = price

    results.append(bond_results)

# 7. Print bond portfolio prices based on selected curves
bond_results = pd.DataFrame(results)
print("\n\nPortfolio Summary:")
print(bond_results.to_string(index=False))

# 8. Calculate bond portfolio statistics
# # 8.1 Calculate each bond's KRD


# # 8.2 Calculate each bond's total duration
# # 8.3 Calculate each bond's convexity
