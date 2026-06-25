import os
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# Read data.csv from the same folder as this script, so it runs on any clone
DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'data.csv')

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
for col in ['Baseline Yield (Spot Rate)', '2-Year Shock +', '2-Year Shock -',
            '5-Year Shock +', '5-Year Shock -', '10-Year Shock +', '10-Year Shock -']:
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

    if bond_face_value == 0:
        coupon_payment = bond_coupon / coupon_frequency
    else:
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
        'bond_face_value': 100000.0,
        'coupon_frequency': 1
    },
    {
        'name': 'Bond_2',
        'bond_tenor': 10,
        'bond_coupon': 0.07,
        'bond_face_value': 100000.0,
        'coupon_frequency': 1
    },
    {
        'name': 'Bond_3',
        'bond_tenor': 15,
        'bond_coupon': 0.08,
        'bond_face_value': 100000.0,
        'coupon_frequency': 1
    },
    {
        'name': 'Bond_4',
        'bond_tenor': 15,
        'bond_coupon': 0.06,
        'bond_face_value': 100000.0,
        'coupon_frequency': 2
    }


]

# 5. Define yield curves to test
yield_curves = ['Baseline Yield (Spot Rate)', '2-Year Shock +', '2-Year Shock -', 
                '5-Year Shock +', '5-Year Shock -', '10-Year Shock +', '10-Year Shock -']

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
## 8.1 Calculate each bond's KRD
### Convert bond_results to a DataFrame for easier manipulation
bonds_results = bond_results[['Bond_ID', 'Baseline Yield (Spot Rate)', '2-Year Shock +', '2-Year Shock -',
                            '5-Year Shock +', '5-Year Shock -', '10-Year Shock +', '10-Year Shock -']]

### Calculate KRD's for each shock
krd_2_year = (bonds_results['2-Year Shock -'] - bonds_results['2-Year Shock +'])/(2 * 0.01 * bonds_results['Baseline Yield (Spot Rate)'])
krd_5_year = (bonds_results['5-Year Shock -'] - bonds_results['5-Year Shock +'])/(2 * 0.01 * bonds_results['Baseline Yield (Spot Rate)'])
krd_10_year = (bonds_results['10-Year Shock -'] - bonds_results['10-Year Shock +'])/(2 * 0.01 * bonds_results['Baseline Yield (Spot Rate)'])
bond_krds = pd.DataFrame({ 'Bond_ID': bonds_results['Bond_ID'], 'KRD_2_Year': krd_2_year, 'KRD_5_Year': krd_5_year, 'KRD_10_Year': krd_10_year})

print(bond_krds)

# # 8.2 Calculate each bond's convexity
convexity_2_year = (bonds_results['2-Year Shock +'] + bonds_results['2-Year Shock -'] - 2 * bonds_results['Baseline Yield (Spot Rate)'])/(0.01**2 * bonds_results['Baseline Yield (Spot Rate)'])
convexity_5_year = (bonds_results['5-Year Shock +'] + bonds_results['5-Year Shock -'] - 2 * bonds_results['Baseline Yield (Spot Rate)'])/(0.01**2 * bonds_results['Baseline Yield (Spot Rate)'])
convexity_10_year = (bonds_results['10-Year Shock +'] + bonds_results['10-Year Shock -'] - 2 * bonds_results['Baseline Yield (Spot Rate)'])/(0.01**2 * bonds_results['Baseline Yield (Spot Rate)'])
bond_convexities = pd.DataFrame({ 'Bond_ID': bonds_results['Bond_ID'], 'Convexity_2_Year': convexity_2_year, 'Convexity_5_Year': convexity_5_year, 'Convexity_10_Year': convexity_10_year})  

print(bond_convexities)

# 9. Define static liability stream - Flat annuity
# Assuming a flat annuity of $100,000 per year for 10 years 
liabilities = [
    {
        'name': 'Liability_1',
        'tenor': 20,
        'coupon': 100000.0,
        'face_value': 0.0,
        'coupon_frequency': 1
    }]

# 10. Loop through liabilities and calculate liability PVs
results = []

for liability in liabilities:
    liability_results = {'Liability_ID': liability['name']}

    for curve in yield_curves:
        price = calculate_bond_price(
            liability['tenor'],
            liability['coupon'],
            liability['face_value'],
            liability['coupon_frequency'],
            curve
        )
        liability_results[curve] = price

    results.append(liability_results)
print("\n\nLiability Summary:")
liability_results = pd.DataFrame(results)
print(liability_results.to_string(index=False))
# 10. Calculate liability statistics
## 10.1 Calculate each liability's KRD
### Convert liability_results to a DataFrame for easier manipulation
liabilities_results = liability_results[['Liability_ID', 'Baseline Yield (Spot Rate)', '2-Year Shock +', '2-Year Shock -',
                            '5-Year Shock +', '5-Year Shock -', '10-Year Shock +', '10-Year Shock -']]

### Calculate KRD's for each shock
krd_2_year = (liabilities_results['2-Year Shock -'] - liabilities_results['2-Year Shock +'])/(2 * 0.01 * liabilities_results['Baseline Yield (Spot Rate)'])
krd_5_year = (liabilities_results['5-Year Shock -'] - liabilities_results['5-Year Shock +'])/(2 * 0.01 * liabilities_results['Baseline Yield (Spot Rate)'])
krd_10_year = (liabilities_results['10-Year Shock -'] - liabilities_results['10-Year Shock +'])/(2 * 0.01 * liabilities_results['Baseline Yield (Spot Rate)'])
bond_krds = pd.DataFrame({ 'Bond_ID': liabilities_results['Liability_ID'], 'KRD_2_Year': krd_2_year, 'KRD_5_Year': krd_5_year, 'KRD_10_Year': krd_10_year})

print(bond_krds)

# # 10.2 Calculate each liability's convexity
convexity_2_year = (liabilities_results['2-Year Shock +'] + liabilities_results['2-Year Shock -'] - 2 * liabilities_results['Baseline Yield (Spot Rate)'])/(0.01**2 * liabilities_results['Baseline Yield (Spot Rate)'])
convexity_5_year = (liabilities_results['5-Year Shock +'] + liabilities_results['5-Year Shock -'] - 2 * liabilities_results['Baseline Yield (Spot Rate)'])/(0.01**2 * liabilities_results['Baseline Yield (Spot Rate)'])
convexity_10_year = (liabilities_results['10-Year Shock +'] + liabilities_results['10-Year Shock -'] - 2 * liabilities_results['Baseline Yield (Spot Rate)'])/(0.01**2 * liabilities_results['Baseline Yield (Spot Rate)'])
bond_convexities = pd.DataFrame({ 'Bond_ID': liabilities_results['Liability_ID'], 'Convexity_2_Year': convexity_2_year, 'Convexity_5_Year': convexity_5_year, 'Convexity_10_Year': convexity_10_year})  

print(bond_convexities)

# 11. Calculate all key tenor shock rate curves for the portfolio and liability streams

# 12. Calculate all key tenor shock scenarios for the portfolio and liability streams

# 13. Calculate surplus/deficit for each shock scenario