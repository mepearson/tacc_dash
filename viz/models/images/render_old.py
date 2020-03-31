from viz.utils import *
import re

def generate_layout(thread_id=None):
    return html.Div([
        html.Div([
            html.H3(['Visualisations']),
            html.Label(['for MINT modeling thread: '],style={'float':'left'}),
            dcc.Input(id='images_thread_id', value=thread_id,style={'float':'left'}),
                html.Div(id='dd-output-container'),
        ],className='row'),

        dcc.Dropdown(
            id='images_dropdown',
        ),

        html.Div(id="images")
    ])

@app.callback(
    dash.dependencies.Output('dd-output-container', 'children'),
    [dash.dependencies.Input('demo-dropdown', 'value')])
def update_output(value):
    return 'You have selected "{}"'.format(value)

@app.callback(
    [
        Output('images_dropdown','options'),
        Output('images_dropdown','value')
    ],
    [
        Input(component_id='images_thread_id', component_property='value')
    ]
    )
def set_dropdowns(thread_id):
    if thread_id is None:
        raise PreventUpdate
    items = []
    df = obtain_params(thread_id)

    for index, row in df.iterrows():
        #print("insert {}".format(row))
        items.append({"label": "Config {}".format(index), "value": row["mint_runid"]})

    return [
        items,
        items[0]["value"]
    ]

def fix_dbname(name):
    return name.strip().lower().replace(' ', '_').replace('(',
        '').replace(')', '').replace('%', 'percentage').replace('/',
        '_per_').replace('.', '_').replace('-', '_')


def obtain_params(thread_id):
    if thread_id != None and thread_id != None:
        meta_query = "SELECT metadata FROM threads WHERE threadid='{}'".format(thread_id)
        meta_df = pd.DataFrame(pd.read_sql(meta_query, con))
        if meta_df.empty:
            print("Thread doesn't exist")
            return None
        meta = json.loads(meta_df.metadata[0])
        models = meta["thread"]["models"]
        for modelid in models:
            model = models[modelid]
            model_config = model["model_configuration"]
            runs_table_name = fix_dbname("{}_runs".format(model_config))

            query = """SELECT * from {} WHERE threadid='{}';""".format(runs_table_name, thread_id)
            df = pd.DataFrame(pd.read_sql(query, con))
            df = df.drop(["threadid"], axis=1)
            return df

def obtain_output_tables(threadid):
    query = """SELECT DISTINCT output_table_name from threads_output_table where threadid='{}';""".format(threadid)
    df = pd.DataFrame(pd.read_sql(query, con))
    return df

def obtain_images(tablename, mint_runid):
    query = """SELECT url from {} where mint_runid='{}' order by url asc;""".format(tablename, mint_runid)

    df = pd.DataFrame(pd.read_sql(query, con))
    if df.empty:
        empty_data_options = [{'label':'Waiting on Data Ingestion','value':'waiting'}]
        emptymsg = 'Please Wait for Data Ingestion'
    return df


# @app.callback(
#         Output('image', 'src'),
#     [
#         Input('images_dropdown', 'value')
#     ]
#     )
@app.callback(
    Output('images', 'children'),
    [
        Input('images_thread_id', 'value'),
        Input('images_dropdown', 'value')
    ]
)
def update_image_src(threadid, mint_runid):
    op_tables_df = obtain_output_tables(threadid)
    images = []
    for op_table_row in op_tables_df.values:
        op_table_name = op_table_row[0]
        images.append(
            html.H2(children=op_table_name)
        )
        images_df = obtain_images(op_table_name, mint_runid)

        for image_row in images_df.values:
            image_url = image_row[0]
            if re.search(r"(\.png|\.gif|\.jpg|\.jpeg)", image_url, re.IGNORECASE):
                images.append(
                    html.Img(
                        src=image_url,
                        width="500px"
                    )
                )
            else:
                images.append(
                    html.Div(
                        children=[
                            html.A(
                                href=image_url,
                                children=image_url
                            )
                        ]
                    )
                )
    return images


if __name__ == '__main__':
    app.run_server(debug=True, port=8053, host='0.0.0.0')
