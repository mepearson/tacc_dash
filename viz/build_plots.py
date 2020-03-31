# Centralized repository of reusable functions to generate dash components using page inputs

# Import Libraries from viz.utils
from viz.utils import *

# FUNCTIONS
# DATA TABLE
# Build dash data table from dataframe
def create_datatable(dataframe):
    dtable = dt.DataTable(
        # Table Data
                    id='dtable',
                    data=dataframe.to_dict('records'),
                    columns=[{'name': i, 'id': i, "selectable": True, "hideable": True} for i in dataframe.columns],
        # Table Controls
                    filter_action='custom',
                    filter_query='',
                    sort_action="native",
                    sort_mode="multi",
                    column_selectable="multi",
                    # row_selectable="multi",
                    # row_deletable=True,
                    selected_columns=[],
                    selected_rows=[],
                    page_action="native",
                    page_current= 0,
                    page_size= 10,
                    export_format='csv',
                    export_headers='display',
                )
    return dtable

# DATA TABLE: Filtering
operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]

def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3

## Generate Map from user selections
def generate_map(spatial_data,lat,lon,hover,color):
    fig = px.scatter_mapbox(spatial_data, lat=lat, lon=lon, hover_name=hover, color=color, zoom=6,height=300)
    fig.update_layout(mapbox_style="stamen-terrain")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig
