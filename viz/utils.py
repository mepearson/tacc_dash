from urllib.parse import urlparse, parse_qs
import os

# Database Querying
from sqlalchemy import create_engine

# DASH libraries
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_table as dt
import dash_leaflet as dl

# Managing Data
import pandas as pd
import numpy as np
import json
import time
#import rasterio as rio

#Plotting Libraries
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# For File Upload
import base64
import io

## FOR LIVE
from viz.app import app
from viz.app import engine



def parse_search(search, key):
    query = urlparse(search).query
    query_dict = parse_qs(query)
    if key in query_dict:
        print("loading {}".format(query_dict[key][0]))
        return query_dict[key][0]
    return None

# ACCESS TOKENS FOR OTHER PRODUCTS
# Mapbox setup
mapbox_url = "https://api.mapbox.com/styles/v1/mapbox/{id}/tiles/{{z}}/{{x}}/{{y}}{{r}}?access_token={access_token}"
mapbox_token = os.environ['MAPBOX_TOKEN']
mapbox_ids = ["light-v9", "dark-v9", "streets-v9", "outdoors-v9", "satellite-streets-v9"]


# DATABASE CONNECTION INFORMATION
# DATABASES = {
#     'production':{
#         'NAME': os.environ['DATABASE_NAME'],
#         'USER': os.environ['DATABASE_USER'],
#         'PASSWORD': os.environ['DATABASE_PASSWORD'],
#         'HOST': os.environ['DATABASE_HOSTNAME'],
#         'PORT': 5432,
#     },
# }

DATABASES = {
    'production':{
        'NAME': 'devingestion',
        'USER': 'ingestion',
        'PASSWORD': 'pVC1PmHo',
        'HOST': 'aws1.mint.isi.edu',
        'PORT': 5432,
    },
}


# choose the database to use
db = DATABASES['production']

# construct an engine connection string
engine_string = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}".format(
    user = db['USER'],
    password = db['PASSWORD'],
    host = db['HOST'],
    port = db['PORT'],
    database = db['NAME'],
)

con = create_engine(engine_string)

# LOADING DATA
# Load thread data if threadid is supplied
def fix_dbname(name):
    return name.strip().lower().replace(' ', '_').replace('(',
        '').replace(')', '').replace('%', 'percentage').replace('/',
        '_per_').replace('.', '_').replace('-', '_')

def load_thread_data(thread_id):
    if thread_id != None and thread_id != None:
        meta_query = "SELECT metadata FROM threads WHERE threadid='{}'".format(thread_id)
        meta_df = pd.DataFrame(pd.read_sql(meta_query, con))
        if meta_df.empty:
            print("Thread doesn't exist")
            return meta_df
        models = meta_df.metadata[0]["thread"]["models"]
        for modelid in models:
            model = models[modelid]
            model_config = model["model_configuration"]

            runs_table_name = fix_dbname("{}_runs".format(model_config))

            op_table_query = "SELECT output_table_name from threads_output_table WHERE threadid='{}'".format(thread_id)
            op_table_df = pd.DataFrame(pd.read_sql(op_table_query, con))
            output_table_name = op_table_df.output_table_name[0]

            #identify cycles runs:
            if 'cycles' in model_config:
                data_query = """SELECT runs.*, outputs.*, ti.x as lon, ti.y as lat FROM
                    {}	runs
                    LEFT JOIN threads_inputs ti ON ti.id = runs.cycles_weather and ti.threadid = runs.threadid and ti.spatial_type = 'Point'
                    LEFT JOIN {} outputs
                        ON runs.mint_runid = outputs.mint_runid AND runs.threadid = outputs.threadid
                        WHERE runs.threadid='{}'  """.format(runs_table_name, output_table_name, thread_id)
            else:
                data_query = """SELECT * from {} runs LEFT JOIN {} outputs
                    ON runs.mint_runid = outputs.mint_runid AND runs.threadid = outputs.threadid
                    WHERE runs.threadid='{}' """.format(runs_table_name, output_table_name, thread_id)
            df = pd.DataFrame(pd.read_sql(data_query, con))
            df = df.drop(["threadid"], axis=1)
            return df

def store_data(dataframe):
    scols = dataframe.columns.values.tolist()
    sdata = dataframe.to_dict('records')
    return scols, sdata

# Read in the data from an uploaded file
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return df
