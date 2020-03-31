# dash libs
# import collections
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import json
import time

# dash interactive states
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# dash components
import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt

# Plotting graphics
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from utils_no_live import parse_search
## FOR LIVE
# from viz.app import app
## FOR LIVE: IMPORT DATABASE
#from viz.app import engine
##

#styling
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css',
'https://codepen.io/chriddyp/pen/brPBPO.css']

# set connection string. REMOVE FOR LIVE
user = 'viz'
password = 'Zc2D63rSbIko6d'
DATABASE_URI = 'postgres+psycopg2://{}:{}@aws1.mint.isi.edu:5432/publicingestion'.format(user,password)
con = create_engine(DATABASE_URI)

## threadid.  Change to get this from url when avilable.
thread_id = 'b2oR7iGkFEzVgimbNZFO'

options_list=['end_planting_day','fertilizer_rate','start_planting_day', 'weed_fraction', 'total_biomass', 'root_biomass',
   'grain_yield', 'forage_yield', 'ag_residue', 'harvest_index', 'potential_tr', 'actual_tr', 'soil_evap', 'total_n', 'root_n',
   'grain_n', 'forage_n', '"cum._n_stress"', 'n_in_harvest', 'n_in_residue', 'n_concn_forage','north','east'
]
selected_options=['fertilizer_rate','start_planting_day', 'weed_fraction','grain_yield','north','east']

def get_numeric_columns(dataframe):
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    numeric_cols =  dataframe.select_dtypes(include=numerics).columns
    return numeric_cols

## LOCAL ONLY
##Config elements
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config.suppress_callback_exceptions = True
##

# Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.H3('Parallel Coordinates Graph'),
    dcc.Store(id='s-settings'),
    dcc.Store(id='s-sqldata'),
    html.Div([
        html.Div([
            html.P('CROP'),
            dcc.Dropdown(id='dd_crop'),
            # dcc.Dropdown(id='dd_crop',multi=True),
            html.P('PLANTING START DATE'),
            dcc.Dropdown(id='dd_planting',multi=True),
        ],className="four columns"),
        html.Div([
            html.P('LOCATIONS'),
            dcc.Dropdown(id='dd_locations',multi=True),
            html.P('YEAR'),
            html.Div(id='rs_year'),
        ],className="eight columns"),
    ],className="row"),
    html.Div([
        html.Div([
            html.P('AXES:'),
            dcc.Dropdown(id='dd_pcoptions',
                        options=[dict(label=x, value=x) for x in sorted(options_list)],
                        value=selected_options,
                        multi=True),
        ],className="six columns"),
        html.Div([
            html.P('SCALE:'),
            dcc.Dropdown(id='dd_pcscale',
                        options=[dict(label=x, value=x) for x in sorted(options_list)],
                        value=selected_options[0]
                        ),
        ],className="three columns"),
        html.Div([
            html.Div([html.Button('Build Parallel Coordinates', id='btn-pc')],style={"margin-top":'30px'})
        ],className="two columns"),
    ],className="row"),
    html.Div([
            html.Div(id='div_pcoptions')
    ],className="row"),
    html.Div([
        dcc.Loading(id='l-graph',children=[
            html.Div(id='graph')
        ],type="circle"),
    ],className="row"),
    html.Div(id='testdiv'),
])


# Callbacks
#Set Dropdown Values
@app.callback(
    [Output('dd_crop','options'),Output('dd_crop','value'),
    Output('dd_locations','options'),Output('dd_locations','value'),
    Output('dd_planting','options'), Output('dd_planting','value')
    ,Output('rs_year','children')
    ],
    [
        Input('s-settings','data'),
        Input('url', component_property='search')
     ]
    )
def set_dropdowns(settings,search):
    thread_id = parse_search(search, "thread_id")
    if thread_id is None or thread_id == '':
        raise PreventUpdate
    tablename = 'public."cycles-0.9.4-alpha-advanced-pongo-weather"'
    query = """select crop_name, fertilizer_rate, start_planting_day, start_year, end_year, weed_fraction, location
                from {} WHERE threadid = '{}';""".format(tablename,thread_id)
    df = pd.DataFrame(pd.read_sql(query,con))
    #dropdown options
    crops = df.crop_name.unique()
    crop_options = [dict(label=x, value=x) for x in sorted(crops)]
    planting_starts = df.start_planting_day.unique()
    planting_options =[dict(label=x, value=x) for x in sorted(planting_starts)]
    locations = df.location.unique()
    location_options = [dict(label=x, value=x) for x in sorted(locations)]
    #year range slider options
    start_year = df.start_year.min()
    end_year = df.end_year.max()
    year_options = [dict(label=x, value=x) for x in range(start_year, end_year)]
    testdiv = 'years: {} - {}'.format(start_year, end_year)
    yearslider =dcc.RangeSlider(
                id='rs_year',
                min=start_year,
                max=end_year,
                marks={i: '{}'.format(i) for i in range(start_year,end_year+1)},
                step=None,
                value=[(end_year-3),(end_year-1)],
                allowCross=False
            ),
    return [crop_options,crops[0],
            location_options,locations[0:5],
            planting_options,planting_starts,
            yearslider]

@app.callback(
    Output('testdiv','children'),
    # Output('sqldata','data')
    [Input('btn-pc', 'n_clicks')],
    [State('dd_crop','value'),State('dd_locations','value'), State('dd_planting','value'), State('rs_year','value'),
    State('dd_locations','options'),State('rs_year','min'),State('rs_year','max'),State('dd_pcoptions','value'),State('dd_pcscale','value')]
     )
def update_figure(n_clicks,crop,locations,planting,year,locationoptions,yearmin,yearmax,selectlist,scale):
    if n_clicks is None:
        raise PreventUpdate
    for item in (crop,locations,planting,year):
        if item is None or item == '':
            # raise PreventUpdate
            return "Please ensure all variables are selected"
    ins = 'public."cycles-0.9.4-alpha-advanced-pongo-weather"'
    outs = 'public."cycles-0.9.4-alpha-advanced-pongo-weather_cycles_season"'
    thread = "'" + thread_id + "'"
    #build lists for strings
    select_cols = 'crop'
    selectlist.append(scale)
    selectlist = list(sorted(set(selectlist)))
    if isinstance(selectlist, list):
        scols = "::numeric,".join(list(selectlist))
    if len(selectlist) > 0:
        select_cols = select_cols + ', ' + scols + '::numeric'

    # crop_list=[]
    # if isinstance(crop, list):
    #     crop_list = "','".join(list(crop))
    # crop_list = "'" + crop_list + "'"

    #build lists for ints
    planting_list = ",".join(str(x) for x in list(planting))
    #if locations selected < total locations, add locations clause
    # locationclause = ''
    # if len(locations) != len(locationoptions):
    locations_list=[]
    if isinstance(locations, list):
        locations_list = "','".join(list(locations))
    locations_list = "'" + locations_list + "'"
        # locationclause = ' AND location IN  ({}) '.format(locations_list)
    query="""SELECT {}
             FROM
            (SELECT *
            ,(split_part(location, 'Nx', 1))::numeric AS north ,(split_part(split_part(location, 'Nx', 2),'E',1))::numeric AS east
            FROM {}
            WHERE threadid = {}
            AND crop_name LIKE '{}'
            AND start_planting_day IN ({})
            AND location in ({})
            ) ins
            INNER JOIN
            (Select * from
            (SELECT *, EXTRACT(year FROM TO_DATE(date, 'YYYY-MM-DD')) as year
            FROM {}) o
            WHERE year >= {} and year <= {}
            ) outs
            ON ins."mint-runid" = outs."mint-runid" """.format(select_cols,ins,thread,crop,planting_list,locations_list,outs,year[0],year[1])
    pcdata = pd.DataFrame(pd.read_sql(query,con))
    # contents=[]
    # for c in crop:
    # graphid = 'graph-' + c
    # c = crop[0]
    figdata = pcdata
    fig = px.parallel_coordinates(figdata, color=scale,
                            # color_continuous_midpoint = figdata.loc[:,scale].median(),
                            #  color_continuous_scale=px.colors.diverging.Tealrose
                             )
    pc = dcc.Graph(id='graphid',figure=fig)
    # contents.append(pc)
    return pc
    # return contents
    # return "{}".format(contents)
    # pcols = figdata.columns.values.tolist()
    # return "{}".format(query)
    # return "{},{}".format(c,figdata.head(5))


## LOCAL ONLY
if __name__ == '__main__':
    app.run_server(debug=True,port=8040)
##
