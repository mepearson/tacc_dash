import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from viz.utils import  parse_search
from viz.app import app


# Models to take Thread ID
from viz.models.upload import render as render_upload
from viz.models.map_points import render as render_map_points
from viz.models.images import render as render_images
from viz.models.leaflet import render as render_leaflet
from viz.models.leaflet_demo import render as render_leaflet_demo # DEMO page for leaflet elements

# from viz.models.test_render import render as render_test_render
THREAD_ID = "thread_id"

#Render format: pass in threadid
UPLOAD = "upload"
MAP_POINTS = "map_points"
IMAGES = "images"
LEAFLET = "leaflet"
LEAFLET_DEMO = "leaflet_demo"  # Use for demoing dash leaflet mapping elements
# TEST_RENDER = "test_render"

# Hard Coded Data
# TEST_LAYOUT = "test_layout"

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              inputs=[
                  Input('url', component_property='pathname'),
                  Input('url', component_property='search'),

              ])
def display_page(pathname, search):
    if pathname:
        model_name = str(pathname).replace('/', '')
        thread_id = parse_search(search, "%s" % THREAD_ID)
        if model_name == UPLOAD:
            return render_upload.generate_layout(thread_id)
        elif model_name == MAP_POINTS:
            return render_map_points.generate_layout(thread_id)
        elif model_name == IMAGES:
            return render_images.generate_layout(thread_id)
        elif model_name == LEAFLET:
            return render_leaflet.generate_layout(thread_id)
        elif model_name == LEAFLET_DEMO: # Test page: use for testing out new elements
            return render_leaflet_demo.generate_layout(thread_id)

#         elif model_name == TEST_RENDER:
#             return render_test_render.generate_layout(thread_id)
#         elif model_name == TEST_LAYOUT:
#             return layout_test_layout
    return '404'
