import pandas as pd
# import numpy as np
import json
import os
import re

import sqlalchemy as sql
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, delete, insert, DateTime, Float, Boolean, select, distinct, inspect, Time
from datetime import datetime

# Set the DATABASE_URL environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the database engine
engine = sql.create_engine(DATABASE_URL)

metadata = MetaData()

# Query
def query(sql_query):
    data = pd.read_sql_query(sql_query, engine)
    data.index += 1
    return data

# q = """
# SELECT *
# FROM aranet_lecture_data
# """

# aranetExp = query(q)

q = """
SELECT *
FROM aranet4
"""

aranet4 = query(q)

# Ensure the Date and Time columns are of type string
aranet4['Date'] = aranet4['Date'].astype(str)
aranet4['Time'] = aranet4['Time'].astype(str)

# Combine Date and Time into a single datetime column
aranet4['Datetime'] = pd.to_datetime(aranet4['Date'] + ' ' + aranet4['Time'])


def calculate_moving_averages(dataframe, column_names, window_sizes):
    for column_name in column_names:
        for window_size in window_sizes:
            dataframe[f'{column_name}_rolling_mean_{window_size}'] = dataframe[column_name].rolling(window=window_size, min_periods=1).mean()
    return dataframe

main_features = ['Carbon dioxide(ppm)', 'Temperature(°F)', 'Relative humidity(%)', 'Atmospheric pressure(hPa)']
window_sizes = [3, 5, 10, 15, 30, 60]
aranet4 = calculate_moving_averages(aranet4, main_features, window_sizes)

aranet4.info()