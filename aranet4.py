"""
Created on Sat Dec 23 14:20:31 2023

@author: Corey Dearing
"""

#%% DEPLOYMENT NOTES
"""
- When creating the virtual environment for deployment on Heroku we need to do a pip install for dash-auth and psycopg2. Sqlalchemy is dependent on
psycopyg2, and dash-auth is necessary for login credentials.
"""


#%% IMPORTS
import pandas as pd
# import numpy as np
import json
import os
import re

import sqlalchemy as sql
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, delete, insert, DateTime, Float, Boolean, select, distinct, inspect, Time
from datetime import datetime

# import plotly.express as px
# import plotly.graph_objects as go

# Dash Modules from Plotly Dash
from dash import Dash, dcc, html, Input, Output, State, callback, dash_table, callback_context, no_update
from dash.dependencies import ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# statsmodels api
# import statsmodels.api as sm
# from statsmodels.formula.api import ols
#%% web browser
import webbrowser
from webbrowser import BackgroundBrowser

# Define the path to Microsoft Edge executable
# Note: Update the path to the actual location of your Microsoft Edge executable
edge_path = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"

# Register Microsoft Edge as a browser type
# The 'BackgroundBrowser' class is used to pass the path of the browser executable
class Edge(BackgroundBrowser):
    def __init__(self, path):
        super().__init__(path)


# Register Microsoft Edge as a browser type
webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
#%% HEROKU POSTGRESQL
# Now, retrieve it using os.environ.get
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the database engine
engine = sql.create_engine(DATABASE_URL)

metadata = MetaData()


# aranet_lecture_data = Table('aranet_lecture_data', metadata,
#                             Column('id', Integer, primary_key=True),
#                             Column('date', DateTime),
#                             Column('time', Time),
#                             Column('door1', String),
#                             Column('door2', String),
#                             Column('hvac', String),
#                             Column('subject_count', Integer)
#                             ) 
# %% CREATE TABLE
# from sqlalchemy import inspect
# inspector = inspect(engine)
# if inspector.has_table('aranet_lecture_data'):
#     aranet_lecture_data.drop(checkfirst=True)

# metadata.create_all()

# %%
# Reflect the existing table
aranet_lecture_data = Table('aranet_lecture_data', metadata, autoload_with=engine)

# Function to query database
def query(sql_query):
    data = pd.read_sql_query(sql_query, engine)
    data.index += 1
    return data

#%% PANEL STYLES
panel_style = {
    'border': '1px solid #ddd',
    'borderRadius': '15px',
    'padding': '20px',
    'marginBottom': '15px',
    'backgroundColor': '#f8f9fa'
}


#%% INPUT FIELD PANELS
def create_input_field(id, placeholder, type='text', className=None, style=None):
    return dbc.Input(id=id, type=type, placeholder=placeholder, className=className, style=style)


#%% ARANET EXPERIMENTS
def aranet_inputs_container():
    return dbc.Card(
        dbc.CardBody([
            html.H4("Lecture Air Quality Aranet Experiment", className="card-title"),
            html.Div([
                html.Div([
                    dbc.Label("Door One State"),
                    dbc.Row([
                        dbc.Col(html.Div("Open", className="switch-label-open"), width="auto"),
                        dbc.Col(dbc.Switch(
                            id='door-one-switch',
                            label='',  # Remove the label here
                            value=False,  # Initially set to False indicating 'Closed'
                            className='mb-3',
                        ), width="auto"),
                        dbc.Col(html.Div("Closed", className="switch-label-close"), width="auto"),
                    ], justify="center"),
                ]),
                html.Div([
                    dbc.Label("Door Two State"),
                    dbc.Row([
                        dbc.Col(html.Div("Open", className="switch-label-open"), width="auto"),
                        dbc.Col(dbc.Switch(
                            id='door-two-switch',
                            label='',  # Remove the label here
                            value=False,  # Initially set to False indicating 'Closed'
                            className='mb-3',
                        ), width="auto"),
                        dbc.Col(html.Div("Closed", className="switch-label-close"), width="auto"),
                    ], justify="center"),
                ]),
                html.Div([
                    dbc.Label("HVAC State"),
                    dbc.Row([
                        dbc.Col(html.Div("On", className="switch-label-open"), width="auto"),
                        dbc.Col(dbc.Switch(
                            id='hvac-switch',
                            label='',  # Remove the label here
                            value=False,  # Initially set to False indicating 'Closed'
                            className='mb-3',
                        ), width="auto"),
                        dbc.Col(html.Div("Off", className="switch-label-close"), width="auto"),
                    ], justify="center"),
                ]),
            ]),
            html.Div([
                dbc.Label("Attendance Count"),
                dbc.Input(id='subject-count', type='number', className='mb-3', style={'display': 'block'}),
            ]),
            dbc.Button("Submit", id="submit-button-aranet", color="primary", className="mt-3"),
        ])
    )

def aranet_display_container():
    return dbc.Card(
            dbc.CardBody([
                html.H4("Aranet Lecture Data", className="card-title"),
                dash_table.DataTable(
                    id='aranet-lecture-table',
                    columns=[
                        {"name": "ID", "id": "id"},
                        {"name": "Date", "id": "date"},
                        {"name": "Time", "id": "time"},
                        {"name": "Door 1", "id": "door1"},
                        {"name": "Door 2", "id": "door2"},
                        {"name": "HVAC", "id": "hvac"},
                        {"name": "Subject Count", "id": "subject_count"},
                    ],
                    # data=initial_data.to_dict('records'),
                    editable=True,
                    row_deletable=True,
                    page_size=15,  # Set the number of rows per page
                    sort_action='native',
                    sort_by=[{"column_id": "date", "direction": "desc"}, {"column_id": "time", "direction": "desc"}],  # Sort by Date and Time in descending order
                    style_table={'overflowX': 'auto'},
                    style_data_conditional=[
                        {'if': {'column_id': 'id'},
                        'display': 'none'}  # Hide the ID column
                    ],
                    style_header_conditional=[
                        {'if': {'column_id': 'id'},
                        'display': 'none'}  # Hide the header of the ID column
                    ]
                )
            ])
        )


#%% APP
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

server = app.server

#%% MAIN ARANET DISPLAY CONTAINER
aranet_container = dbc.Container([
    dbc.Row([
        dbc.Col(aranet_inputs_container(), width=12, lg=3), #full width on small screens, 1/4 width on large screens
        dcc.Store(id='aranet-lecture-store'),
        html.Div(id='aranet-load-trigger', style={'display': 'none'}), # hidden element
        dbc.Col(aranet_display_container(), width=12, lg=9, className="d-none d-lg-block")
    ], justify="center")
], fluid=True)
app.layout = aranet_container
#%% ARANET EXPERIMENTS CALLBACKS
def aranet_callbacks(app):
    # Load Initial Data
    @app.callback(
        Output('aranet-lecture-store', 'data'),
        Input('aranet-load-trigger', 'n_clicks'), # This is a hidden div or similar component
        allow_duplicate=True,  
        prevent_initial_call=False  # Allow this callback to run on initial load
    )
    def load_initial_data(n_clicks):
        initial_data = query("""
        SELECT *
        FROM aranet_lecture_data
        """)
        updated_data = initial_data.to_dict('records')
        return updated_data
    
    # Update Aranet Table Store
    @app.callback(
        Output('aranet-lecture-table', 'data'),
        [Input('aranet-lecture-store', 'data')]
    )
    def update_table_from_store(stored_data):
        return stored_data

    @app.callback(
        Output('aranet-lecture-store', 'data', allow_duplicate=True),
        [Input('submit-button-aranet', 'n_clicks')],
        [State('door-one-switch', 'value'),
         State('door-two-switch', 'value'),
         State('hvac-switch', 'value'),
         State('subject-count', 'value')],
         prevent_initial_call=True
    )
    def handle_data_updates(submit_trigger, door1, door2, hvac, subject_count):
        if submit_trigger is None:
            PreventUpdate
        # Ensure subject_count is not None before converting to int
        subject_count = int(subject_count) if subject_count is not None else 0
        new_entry = {
            'date': datetime.now().strftime("%m-%d-%Y %H:%M:%S"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'door1': 'closed' if door1 else 'open',
            'door2': 'closed' if door2 else 'open',
            'hvac': 'off' if hvac else 'on',
            'subject_count': int(subject_count)
        }
        # Insert new entry into the database and return updated data
        # (Implementation depends on your database setup)
        # Create an insert statement for the new_entry
        stmt = insert(aranet_lecture_data).values(new_entry)

        try:
            print("Attempting to insert data into the database...")
            with engine.connect() as connection:
                with connection.begin() as transaction:
                    try:
                        connection.execute(stmt)
                        transaction.commit()
                        print("Data inserted successfully.")
                    except Exception as e:
                        print(f"Error during insertion: {e}")
                        transaction.rollback()
                        raise
        except Exception as e:
            print(f"An error occurred: {e}")

    # Code to return updated data
        updated_data = query("""
        SELECT *
        FROM aranet_lecture_data
        """)
        return updated_data.to_dict('records')


    #%% DELETE RECORDS FROM DATABASE
    @app.callback(
        Output('aranet-lecture-store', 'data', allow_duplicate=True),
        Input('aranet-lecture-table', 'data'),
        State('aranet-lecture-store', 'data'),
        prevent_initial_call='initial_duplicate'
    )
    def on_row_delete(new_data, old_data):
        try:
            if old_data is None or new_data is None:
                return new_data  # Handle the case where data is None
    
            old_ids = {row['id'] for row in old_data}
            new_ids = {row['id'] for row in new_data}
            deleted_ids = old_ids - new_ids
    
            # Connect to the database and start a transaction
            with engine.connect() as connection:
                with connection.begin() as transaction:
                    try:
                        for deleted_id in deleted_ids:
                            stmt = delete(aranet_lecture_data).where(aranet_lecture_data.c.id == deleted_id)
                            connection.execute(stmt)
                        transaction.commit()
                        print(f"Deleted rows with IDs: {deleted_ids}")
                    except Exception as e:
                        print(f"Error during row deletion: {e}")
                        transaction.rollback()
                        raise
    
            return new_data
    
        except Exception as e:
            print(f"Error in on_row_delete callback: {e}")
            # Handle the error or re-raise
            raise


aranet_callbacks(app)

#%% LAUNCH
# launch application
if __name__ == '__main__':
    import webbrowser
    url = "http://127.0.0.1:50777/"
    webbrowser.get('edge').open_new(url)
    app.run_server(debug=True, port=50777)