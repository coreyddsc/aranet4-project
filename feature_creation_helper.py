import pandas as pd
# import numpy as np
import json
import os
import re

aranetExp_path = "./datasets/aranetExp.csv"
aranet4_path = "./datasets/aranet4.csv"

aranetExp = pd.read_csv(aranetExp_path)
aranet4 = pd.read_csv(aranet4_path)

# Function to categorize CO2 quality
def categorize_co2(co2_value):
    if co2_value < 1000:
        return 'Optimal'
    elif 1000 <= co2_value <= 1400:
        return 'Average'
    else:
        return 'Unhealthy'

# Apply the function to the 'Carbon dioxide(ppm)' column to create a new 'CO2Quality' feature
aranet4['CO2Quality'] = aranet4['Carbon dioxide(ppm)'].apply(categorize_co2)

def categorize_rhumidity(rh_value):
    if rh_value < 30.0:
        return 'Low'
    elif 30.0 <= rh_value <= 50.0:
        return 'Ideal'
    elif rh_value > 50.0:
        return 'High'

aranet4['RHQuality'] = aranet4['Relative humidity(%)'].apply(categorize_rhumidity)

# Dew Point calculation
def dew_point(temp, rh):
    """
    Calculate dew point in °F given temperature in °F and relative humidity in %.
    """
    temp_c = (temp - 32) * 5 / 9  # Convert temperature to °C
    rh_decimal = rh / 100  # Convert relative humidity to decimal
    dew_point_c = temp_c - ((100 - rh_decimal) / 5)
    dew_point_f = (dew_point_c * 9 / 5) + 32  # Convert dew point back to °F
    return dew_point_f

# Heat Index calculation
def heat_index(temp, rh):
    """
    Calculate heat index in °F given temperature in °F and relative humidity in %.
    """
    temp_c = (temp - 32) * 5 / 9  # Convert temperature to °C
    rh_decimal = rh / 100  # Convert relative humidity to decimal

    heat_index_f = (
        -42.379
        + 2.04901523 * temp
        + 10.14333127 * rh
        - 0.22475541 * temp * rh
        - 6.83783e-03 * temp ** 2
        - 5.481717e-02 * rh ** 2
        + 1.22874e-03 * temp ** 2 * rh
        + 8.5282e-04 * temp * rh ** 2
        - 1.99e-06 * temp ** 2 * rh ** 2
    )

    return heat_index_f



# Create new columns for dew point, heat index, and AQI
aranet4['Dew Point(°F)'] = dew_point(aranet4['Temperature(°F)'], aranet4['Relative humidity(%)'])
aranet4['Heat Index(°F)'] = heat_index(aranet4['Temperature(°F)'], aranet4['Relative humidity(%)'])

# Define a function to calculate the 5-minute moving average for CO2 levels
def calculate_moving_average(dataframe, column_name, window_size=5):
    return dataframe[column_name].rolling(window=window_size, min_periods=1).mean()

# Apply the function to the 'Carbon dioxide(ppm)' column to create a new 'CO2_5min_avg' feature
aranet4['CO2_3min_avg'] = calculate_moving_average(aranet4, 'Carbon dioxide(ppm)', window_size=3)
aranet4['CO2_5min_avg'] = calculate_moving_average(aranet4, 'Carbon dioxide(ppm)', window_size=5)
aranet4['CO2_10min_avg'] = calculate_moving_average(aranet4, 'Carbon dioxide(ppm)', window_size=10)
aranet4['CO2_15min_avg'] = calculate_moving_average(aranet4, 'Carbon dioxide(ppm)', window_size=15)
aranet4['CO2_30min_avg'] = calculate_moving_average(aranet4, 'Carbon dioxide(ppm)', window_size=30)


# Convert the 'Date' column to datetime type
aranet4['Date'] = pd.to_datetime(aranet4['Date'])
# Extract day of the week from the Date column
aranet4['DayOfWeek'] = aranet4['Date'].dt.dayofweek

# Map day of the week to a feature class
day_of_week_mapping = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday'
}
aranet4['DayOfWeekClass'] = aranet4['DayOfWeek'].map(day_of_week_mapping)

# Extract period of the day from the Datetime column
aranet4['PeriodOfDay'] = pd.cut(
    aranet4['Datetime'].dt.hour,
    bins=[0, 6, 12, 18, 24],
    labels=['Night', 'Morning', 'Afternoon', 'Evening'],
    right=False
)

# Define the main features
main_features = ['Carbon dioxide(ppm)', 'Temperature(°F)', 'Relative humidity(%)', 'Atmospheric pressure(hPa)']

# Calculate the minute-to-minute difference for each main feature
for feature in main_features:
    aranet4[f'{feature}_diff'] = aranet4[feature].diff().fillna(0)
    
# Add lagged variables for CO2 with 1, 3, 5, and 10-minute lag
aranet4['CO2_1min_lag'] = aranet4['Carbon dioxide(ppm)'].shift(1)
aranet4['CO2_3min_lag'] = aranet4['Carbon dioxide(ppm)'].shift(3)
aranet4['CO2_5min_lag'] = aranet4['Carbon dioxide(ppm)'].shift(5)
aranet4['CO2_10min_lag'] = aranet4['Carbon dioxide(ppm)'].shift(10)
aranet4['CO2_15min_lag'] = aranet4['Carbon dioxide(ppm)'].shift(15)
aranet4['CO2_30min_lag'] = aranet4['Carbon dioxide(ppm)'].shift(30)
aranet4['CO2_60min_lag'] = aranet4['Carbon dioxide(ppm)'].shift(60)

# Define a function to calculate the rolling average and sign tracking
def calculate_rolling_average(df, column_name, window_sizes):
    for window_size in window_sizes:
        # Calculate the rolling average
        df[f'{column_name}_{window_size}min_avg'] = df[column_name].rolling(window=window_size).mean()
        # Calculate the sign tracking feature
        df[f'{column_name}_{window_size}min_sign'] = df[f'{column_name}_{window_size}min_avg'].diff().apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
    return df

# Specify the window sizes for rolling average
window_sizes = [5, 10, 15]

# Apply the function to calculate rolling averages and sign tracking features
aranet4 = calculate_rolling_average(aranet4, 'Carbon dioxide(ppm)_diff', window_sizes)

# %%
# Define the main features
main_features = ['Carbon dioxide(ppm)', 'Temperature(°F)', 'Relative humidity(%)', 'Atmospheric pressure(hPa)']

# Define a function to calculate the sign column
def calculate_sign(df, column_name):
    df[f'{column_name}_sign'] = df[column_name].apply(lambda x: 1 if x > 0 else -1 if x < 0 else 0)
    return df

# Apply the function to calculate the sign column for each feature
for feature in main_features:
    aranet4 = calculate_sign(aranet4, f'{feature}_diff')

aranet4.info()