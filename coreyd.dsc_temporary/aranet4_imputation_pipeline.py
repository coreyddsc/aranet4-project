# %% IMPORTS
import pandas as pd
# import numpy as np
import json
import os
import re


aranetExp_path = "../datasets/aranetExp.csv"
aranet4_path = "../datasets/aranet4.csv"

aranetExp = pd.read_csv(aranetExp_path)
aranet4 = pd.read_csv(aranet4_path)

# Create a dictionary for renaming the columns
rename_dict = {
    'Carbon dioxide(ppm)': 'CO2',
    'Temperature(°F)': 'Temperature',
    'Relative humidity(%)': 'Humidity',
    'Atmospheric pressure(hPa)': 'Pressure'
}

# Rename the columns
aranet4.rename(columns=rename_dict, inplace=True)
# Convert 'Date' and 'Datetime' columns to datetime objects
aranet4['Date'] = pd.to_datetime(aranet4['Date'])
aranet4['Datetime'] = pd.to_datetime(aranet4['Datetime'])

# Extract features from 'Date' and 'Datetime'
aranet4['Year'] = aranet4['Date'].dt.year
aranet4['Month'] = aranet4['Date'].dt.month
aranet4['Day'] = aranet4['Date'].dt.day
aranet4['Hour'] = aranet4['Datetime'].dt.hour
aranet4['Minute'] = aranet4['Datetime'].dt.minute
aranet4['Second'] = aranet4['Datetime'].dt.second

# Calculate the 5-minute moving average of 'Humidity'
aranet4['Humidity_MA_5'] = aranet4['Humidity'].rolling(window=5, min_periods=1).mean()

# Replace missing 'Humidity' values with the moving average
aranet4['Humidity'].fillna(aranet4['Humidity_MA_5'], inplace=True)

# Replace any remaining NaN values with the overall mean
aranet4['Humidity'].fillna(aranet4['Humidity'].mean(), inplace=True)

# Drop the moving average column
aranet4.drop('Humidity_MA_5', axis=1, inplace=True)

def report_nan(df):
    return df.isnull().sum()

# Use the function on your DataFrame
print(report_nan(aranet4))
aranet4.info()
#%% IMPUTATION BY LINEAR REGRESSION

from sklearn.linear_model import LinearRegression

# Assuming 'aranet4' is your original DataFrame
numeric_columns = ['CO2', 'Temperature', 'Humidity', 'Pressure', 'Month', 'Day', 'Hour', 'Minute']
aranet4_numeric = aranet4[numeric_columns].copy()
# Split the data into sets with and without missing 'Pressure' values
train_data = aranet4_numeric[aranet4_numeric['Pressure'].notna()]
test_data = aranet4_numeric[aranet4_numeric['Pressure'].isna()]

# Define the predictors and target
predictors = ['CO2', 'Temperature', 'Humidity', 'Month', 'Day', 'Hour', 'Minute']
target = 'Pressure'

# Train the model
model = LinearRegression()
model.fit(train_data[predictors], train_data[target])

# Predict the missing 'Pressure' values and assign them directly in the DataFrame
test_data.loc[:, 'Pressure'] = model.predict(test_data[predictors])

# Combine the data back together
aranet4_numeric = pd.concat([train_data, test_data])

# Sort the DataFrame by the index
aranet4_numeric.sort_index(inplace=True)

# Check the number of NaN values again
print(report_nan(aranet4_numeric))

# Merge the dataframes
merged_df = aranet4.merge(aranet4_numeric[['Pressure']], left_index=True, right_index=True, how='left', suffixes=('', '_y'))

# Drop the original 'Pressure' column
merged_df.drop('Pressure', axis=1, inplace=True)

# Rename the 'Pressure_y' column to 'Pressure'
merged_df.rename(columns={'Pressure_y': 'Pressure'}, inplace=True)

# Check the result
print(merged_df.info())
print(report_nan(merged_df))

#%% TRANSFORM AND IMPUTE FUNCTION
import pandas as pd
from sklearn.linear_model import LinearRegression

def transform_and_impute_aranet4(df):
    # Convert 'Date' and 'Datetime' columns to datetime objects
    df['Date'] = pd.to_datetime(df['Date'])
    df['Datetime'] = pd.to_datetime(df['Datetime'])

    # Extract features from 'Date' and 'Datetime'
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Day'] = df['Date'].dt.day
    df['Hour'] = df['Datetime'].dt.hour
    df['Minute'] = df['Datetime'].dt.minute
    df['Second'] = df['Datetime'].dt.second

    # Calculate the 5-minute moving average of 'Humidity'
    df['Humidity_MA_5'] = df['Humidity'].rolling(window=5, min_periods=1).mean()

    # Replace missing 'Humidity' values with the moving average
    df['Humidity'].fillna(df['Humidity_MA_5'], inplace=True)

    # Replace any remaining NaN values with the overall mean
    df['Humidity'].fillna(df['Humidity'].mean(), inplace=True)

    # Drop the moving average column
    df.drop('Humidity_MA_5', axis=1, inplace=True)

    # Select numeric columns for imputation
    numeric_columns = ['CO2', 'Temperature', 'Humidity', 'Pressure', 'Month', 'Day', 'Hour', 'Minute']
    df_numeric = df[numeric_columns].copy()

    # Split the data into sets with and without missing 'Pressure' values
    train_data = df_numeric[df_numeric['Pressure'].notna()]
    test_data = df_numeric[df_numeric['Pressure'].isna()].copy()


    # Define the predictors and target
    predictors = ['CO2', 'Temperature', 'Humidity', 'Month', 'Day', 'Hour', 'Minute']
    target = 'Pressure'

    # Train the model
    model = LinearRegression()
    model.fit(train_data[predictors], train_data[target])

    # Predict the missing 'Pressure' values and assign them directly in the DataFrame
    test_data.loc[:, 'Pressure'] = model.predict(test_data[predictors])

    # Combine the data back together
    df_numeric = pd.concat([train_data, test_data])

    # Sort the DataFrame by the index
    df_numeric.sort_index(inplace=True)

    # Merge the imputed 'Pressure' values back to the original DataFrame
    df = df.merge(df_numeric[['Pressure']], left_index=True, right_index=True, how='left', suffixes=('', '_y'))

    # Drop the original 'Pressure' column and rename the imputed one
    df.drop('Pressure', axis=1, inplace=True)
    # df.drop('Time', axis=1, inplace=True)
    df.rename(columns={'Pressure_y': 'Pressure'}, inplace=True)

    return df

#%% TESTING THE FUNCTION
aranet4 = pd.read_csv('../datasets/aranet4.csv')

# Create a dictionary for renaming the columns
rename_dict = {
    'Carbon dioxide(ppm)': 'CO2',
    'Temperature(°F)': 'Temperature',
    'Relative humidity(%)': 'Humidity',
    'Atmospheric pressure(hPa)': 'Pressure'
}

# Rename the columns
aranet4.rename(columns=rename_dict, inplace=True)
transformed_aranet4 = transform_and_impute_aranet4(aranet4)
transformed_aranet4.drop(columns=['Time'], inplace=True)
print(transformed_aranet4.info())


# %%
